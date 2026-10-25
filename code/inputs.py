"""Validated participant inputs; public answers are not prediction inputs."""

import csv
from datetime import datetime, timezone
import hashlib
from pathlib import Path

SCHEMAS = {
    "deletion_requests.csv": "case_id,email,requested_at,reported_status,reported_at,audit_at,request_text",
    "sample_deletion_requests.csv": "case_id,email,requested_at,reported_status,reported_at,audit_at,request_text",
    "user_identities.csv": "user_id,name,email,phone,email_hash,updated_at",
    "user_audit_log.csv": "audit_id,user_id,event_time,field_name,old_value,new_value",
    "system_activity.csv": "activity_id,event_time,event_type,source_system,target_system,resource_id,reported_result,details",
    "deletion_rules.csv": "rule_id,data_category,condition,required_action",
    "evidence_files.csv": "file_id,file_path,origin,captured_at",
}


class InputError(ValueError):
    pass


def timestamp(value):
    try:
        parsed = datetime.fromisoformat(value)
    except (TypeError, ValueError) as exc:
        raise InputError(f"Invalid timestamp: {value!r}") from exc
    if parsed.tzinfo is None:
        raise InputError("Timestamp must include a timezone")
    return parsed.astimezone(timezone.utc)


def read_csv(path, schema):
    with Path(path).open(encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)
        if reader.fieldnames != schema.split(","):
            raise InputError(f"Unexpected CSV header: {Path(path).name}")
        rows = list(reader)
    key = schema.split(",")[0]
    seen = set()
    for row in rows:
        if None in row or any(v is None for v in row.values()):
            raise InputError(f"Malformed CSV row: {Path(path).name}")
        if not row[key] or row[key] in seen:
            raise InputError(f"Missing or duplicate {key}")
        seen.add(row[key])
        for field, value in row.items():
            if field.endswith("_at") or field == "event_time":
                timestamp(value)
    return rows


def evidence_path(dataset, relative):
    dataset = Path(dataset).resolve(strict=True)
    path = (dataset / relative).resolve(strict=True)
    if Path(relative).is_absolute() or not path.is_relative_to(dataset / "evidence"):
        raise InputError("Manifest path escapes dataset/evidence")
    if not path.is_file():
        raise InputError("Manifest path is not a file")
    return path


def load_inputs(dataset, request_file="deletion_requests.csv"):
    dataset = Path(dataset).resolve(strict=True)
    if request_file not in {"deletion_requests.csv", "sample_deletion_requests.csv"}:
        raise InputError("Unknown request file")
    names = [request_file, "user_identities.csv", "user_audit_log.csv",
             "system_activity.csv", "deletion_rules.csv", "evidence_files.csv"]
    tables = {name: read_csv(dataset / name, SCHEMAS[name]) for name in names}
    expected = 518 if request_file == "deletion_requests.csv" else 32
    if len(tables[request_file]) != expected:
        raise InputError(f"Expected {expected} requests")
    for row in tables[request_file]:
        if (row["reported_status"] not in {"COMPLETE", "PARTIALLY_COMPLETE", "NOT_STARTED"}
                or timestamp(row["audit_at"]) < timestamp(row["requested_at"])
                or not row["request_text"].strip()):
            raise InputError("Invalid request fields")
    for row in tables["deletion_rules.csv"]:
        if row["required_action"] not in {"DELETE", "REDACT", "ANONYMIZE", "RETAIN"}:
            raise InputError("Unknown policy action")
        if not row["condition"] or not row["data_category"]:
            raise InputError("Missing policy category or condition")
    categories = [r["data_category"] for r in tables["deletion_rules.csv"]]
    if len(categories) != len(set(categories)):
        raise InputError("Ambiguous duplicate policy category")
    ids = {r["user_id"] for r in tables["user_identities.csv"]}
    for row in tables["user_audit_log.csv"]:
        if row["user_id"] not in ids or row["field_name"] not in {"name", "email", "phone", "email_hash"}:
            raise InputError("Invalid identity history reference")
    for number,row in enumerate(tables["system_activity.csv"],2):row["_source_row"]=number
    tables["system_activity.csv"].sort(key=lambda r: (timestamp(r["event_time"]), r["activity_id"]))
    paths = [dataset / name for name in names]
    paths += [evidence_path(dataset, row["file_path"]) for row in tables["evidence_files.csv"]]
    if len(paths) != len(set(paths)):
        raise InputError("Duplicate manifest path")
    hashes = {p.relative_to(dataset).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
              for p in sorted(paths)}
    return tables, hashes
