"""Exact submission serialization, independent of inference and policy decisions."""

import csv
import io
import json
import os
from pathlib import Path
import tempfile

from inputs import InputError

OPERATIONS = {
    "FINDING": {
        "REPORT_REMAINING_RECORD": "PRESENT", "REPORT_EXPOSED_PII": "PRESENT",
        "REPORT_ACTIVE_DATA_FLOW": "ACTIVE", "REPORT_RESTORE_RISK": "ACTIVE"},
    "REMEDIATION": {
        "DISABLE_DATA_FLOW": "DISABLED", "BLOCK_RESTORE": "BLOCKED",
        "DELETE_RECORD": "ABSENT", "REDACT_RECORD": "REDACTED",
        "ANONYMIZE_RECORD": "ANONYMIZED"},
    "VERIFICATION": {
        "VERIFY_RECORD_ABSENT": "ABSENT", "VERIFY_RECORD_PRESENT": "PRESENT",
        "VERIFY_RECORD_REDACTED": "REDACTED", "VERIFY_RECORD_ANONYMIZED": "ANONYMIZED",
        "VERIFY_DATA_FLOW_DISABLED": "DISABLED", "VERIFY_RESTORE_BLOCKED": "BLOCKED"},
}
FIELDS = {"step_no", "phase", "system_id", "resource_id", "operation", "state", "evidence_id"}
HEADER = ["case_id", "deletion_status", "steps_json"]


def order(step):
    phase = step["phase"]
    return (list(OPERATIONS).index(phase), list(OPERATIONS[phase]).index(step["operation"]),
            step["system_id"], step["resource_id"])


def validate_structure(steps):
    """External evaluator input may be incomplete, but present steps must be valid."""
    if not isinstance(steps, list):
        raise InputError("steps_json must contain an array")
    for number, step in enumerate(steps, 1):
        if not isinstance(step, dict) or set(step) != FIELDS:
            raise InputError("Incorrect step fields")
        if type(step["step_no"]) is not int or step["step_no"] != number:
            raise InputError("Invalid consecutive integer step_no")
        if any(not isinstance(step[f], str) for f in FIELDS - {"step_no"}):
            raise InputError("Step fields must be strings")
        if (step["phase"] not in OPERATIONS
                or OPERATIONS[step["phase"]].get(step["operation"]) != step["state"]):
            raise InputError("Invalid phase/operation/state combination")
        if not step["system_id"].strip() or not step["resource_id"].strip():
            raise InputError("Missing system or resource")


def validate_steps(status, steps, supports):
    """supports(step) must check grounded identity, resource, state, scope and cutoff."""
    if status not in {"NOT_APPLICABLE", "COMPLETE", "INCOMPLETE"} or not isinstance(steps, list):
        raise InputError("Invalid status or steps array")
    validate_structure(steps)
    if status == "NOT_APPLICABLE":
        if steps:
            raise InputError("Unauthorized request has steps")
        return
    if not steps:
        raise InputError("Authorized case has no state proof")
    seen = set()
    phases = set()
    for number, step in enumerate(steps, 1):
        if not isinstance(step, dict) or set(step) != FIELDS:
            raise InputError("Incorrect step fields")
        if type(step["step_no"]) is not int or step["step_no"] != number:
            raise InputError("Invalid consecutive step number")
        if any(not isinstance(step[f], str) for f in FIELDS - {"step_no"}):
            raise InputError("Step fields must be strings")
        phase, operation = step["phase"], step["operation"]
        if phase not in OPERATIONS or OPERATIONS[phase].get(operation) != step["state"]:
            raise InputError("Invalid phase/operation/state combination")
        if not step["system_id"].strip() or not step["resource_id"].strip():
            raise InputError("Missing system or resource")
        phases.add(phase)
        if status == "COMPLETE" and phase != "VERIFICATION":
            raise InputError("COMPLETE contains non-verification steps")
        needs_evidence = phase == "FINDING" or status == "COMPLETE"
        if needs_evidence:
            if not step["evidence_id"] or not supports(step):
                raise InputError("Unsupported or ineligible evidence citation")
        elif step["evidence_id"] != "":
            raise InputError("Future work must not cite past evidence")
        logical = (phase, operation, step["system_id"], step["resource_id"])
        if logical in seen:
            raise InputError("Duplicate logical step")
        seen.add(logical)
    if steps != sorted(steps, key=order):
        raise InputError("Noncanonical step order")
    if status == "INCOMPLETE" and phases != set(OPERATIONS):
        raise InputError("INCOMPLETE must contain findings, repairs and checks")
    repairs = {
        "DELETE_RECORD": ("REPORT_REMAINING_RECORD", "VERIFY_RECORD_ABSENT"),
        "REDACT_RECORD": ("REPORT_EXPOSED_PII", "VERIFY_RECORD_REDACTED"),
        "ANONYMIZE_RECORD": ("REPORT_EXPOSED_PII", "VERIFY_RECORD_ANONYMIZED"),
        "DISABLE_DATA_FLOW": ("REPORT_ACTIVE_DATA_FLOW", "VERIFY_DATA_FLOW_DISABLED"),
        "BLOCK_RESTORE": ("REPORT_RESTORE_RISK", "VERIFY_RESTORE_BLOCKED"),
    }
    if status == "INCOMPLETE":
        covered = set()
        for step in steps:
            if step["phase"] == "REMEDIATION":
                finding, check = repairs[step["operation"]]
                system, resource = step["system_id"], step["resource_id"]
                if (("FINDING", finding, system, resource) not in seen
                        or ("VERIFICATION", check, system, resource) not in seen):
                    raise InputError("Repair lacks corresponding finding or final check")
                covered.add(("FINDING", finding, system, resource))
        if {s for s in seen if s[0] == "FINDING"} != covered:
            raise InputError("Finding lacks a repair")


def canonical_steps(steps):
    result = sorted((dict(s) for s in steps), key=order)
    for number, step in enumerate(result, 1):
        step["step_no"] = number
    return result


def render_rows(rows, case_ids, supports):
    """Render only a fully validated set; supports receives (case_id, step)."""
    if len(case_ids) != len(set(case_ids)) or len(rows) != len(case_ids):
        raise InputError("Case count or uniqueness mismatch")
    if any(set(row) != set(HEADER) for row in rows):
        raise InputError("Invalid output row fields")
    ids = [r["case_id"] for r in rows]
    if ids != sorted(case_ids):
        raise InputError("Output cases must match and be string-sorted")
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=HEADER, lineterminator="\n")
    writer.writeheader()
    for row in rows:
        if not isinstance(row["steps_json"], str):
            raise InputError("steps_json must be serialized JSON")
        steps = json.loads(row["steps_json"])
        validate_steps(row["deletion_status"], steps, lambda s: supports(row["case_id"], s))
        writer.writerow(dict(row, steps_json=json.dumps(steps, ensure_ascii=False, separators=(",", ":"))))
    return buffer.getvalue().encode("utf-8")


def write_atomic(path, content):
    path = Path(path)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, prefix=".output-", delete=False) as file:
            temporary = Path(file.name)
            file.write(content)
            file.flush()
            os.fsync(file.fileno())
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
