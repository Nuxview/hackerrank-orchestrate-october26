import copy
from dataclasses import FrozenInstanceError, replace
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

CODE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE))
from facts import Fact, normalize, resolve_identity
from inputs import InputError, evidence_path, load_inputs, read_csv, timestamp
from sql_snapshot import read_snapshot
from steps import canonical_steps, render_rows, validate_steps, write_atomic
from transport import CONFIG, MODEL, ROOT, RUN_ID, RuntimeFailure, invoke, validate_intents

TEMP = "/tmp/opencode" if Path("/tmp/opencode").is_dir() else None


def step(phase="VERIFICATION", operation="VERIFY_RECORD_ABSENT", state="ABSENT", evidence="e1", resource="profile"):
    return dict(step_no=1, phase=phase, system_id="accounts", resource_id=resource,
                operation=operation, state=state, evidence_id=evidence)


class InputsTests(unittest.TestCase):
    def test_activity_original_rows_survive_time_sort(self):
        from audit import activity_facts
        from inputs import SCHEMAS
        tables,_=load_inputs(ROOT/"dataset")
        original=read_csv(ROOT/"dataset/system_activity.csv",SCHEMAS["system_activity.csv"])
        locations={row["activity_id"]:number for number,row in enumerate(original,2)}
        for fact in activity_facts(tables["system_activity.csv"]):
            self.assertEqual(fact.location,"row "+str(locations[fact.evidence_id]))
    def test_real_inputs_and_historical_resolution(self):
        tables, hashes = load_inputs(ROOT / "dataset")
        self.assertEqual(len(tables["deletion_requests.csv"]), 518)
        self.assertEqual(len(tables["evidence_files.csv"]), 94)
        self.assertEqual(len(hashes), 100)
        self.assertNotIn("sample_output.csv", hashes)
        self.assertNotIn("output.csv", hashes)
        times = [timestamp(r["event_time"]) for r in tables["system_activity.csv"]]
        self.assertEqual(times, sorted(times))
        for r in tables["deletion_requests.csv"]:
            user, aliases = resolve_identity(r["email"], timestamp(r["audit_at"]),
                                            tables["user_identities.csv"], tables["user_audit_log.csv"])
            self.assertTrue(user)
            self.assertTrue(aliases)

    def test_csv_boundary(self):
        with tempfile.TemporaryDirectory(dir=TEMP) as directory:
            path = Path(directory) / "input.csv"
            for text in ["wrong\nx\n", "id,value\nx,a\nx,b\n", "id,value\nx\n", "id,value\nx,a,extra\n"]:
                path.write_text(text)
                with self.subTest(text=text), self.assertRaises(InputError):
                    read_csv(path, "id,value")

    def test_timestamps_require_zone(self):
        for value in ["tomorrow", "2026-01-01", "2026-01-01T01:00:00"]:
            with self.subTest(value=value), self.assertRaises(InputError):
                timestamp(value)
        self.assertEqual(timestamp("2026-01-01T02:00:00+02:00"), timestamp("2026-01-01T00:00:00Z"))

    def test_manifest_escape_and_symlink(self):
        with tempfile.TemporaryDirectory(dir=TEMP) as directory:
            base = Path(directory)
            dataset = base / "dataset"
            (dataset / "evidence").mkdir(parents=True)
            (base / "outside.txt").write_text("not evidence")
            (dataset / "evidence" / "link").symlink_to(base / "outside.txt")
            for name in ["../outside.txt", "evidence/link", str(base / "outside.txt")]:
                with self.subTest(name=name), self.assertRaises(InputError):
                    evidence_path(dataset, name)


class FactsTests(unittest.TestCase):
    def setUp(self):
        self.cutoff = timestamp("2026-04-10T12:00:00Z")
        self.identity = dict(user_id="subject", name="Fixture Person", email="new@example.test",
                             phone="+1 555-0100", email_hash="ab12", updated_at="2026-04-01T00:00:00Z")
        self.history = dict(audit_id="audit-old", user_id="subject", field_name="email",
                            old_value="old@example.test", new_value="new@example.test",
                            event_time="2026-04-02T00:00:00Z")

    def test_old_alias_retains_raw_provenance(self):
        user, aliases = resolve_identity("OLD@example.test", self.cutoff, [self.identity], [self.history])
        self.assertEqual(user, "subject")
        self.assertTrue(any(a.raw == "old@example.test" and a.source_id == "audit-old" for a in aliases))

    def test_no_substring_or_name_join(self):
        for email in ["old@example.test.evil", "Fixture Person", "nobody@example.test"]:
            with self.subTest(email=email), self.assertRaises(InputError):
                resolve_identity(email, self.cutoff, [self.identity], [self.history])

    def test_email_collision_blocks(self):
        other = dict(self.identity, user_id="other")
        with self.assertRaises(InputError):
            resolve_identity(self.identity["email"], self.cutoff, [self.identity, other], [])

    def test_future_identity_and_history_excluded(self):
        future = dict(self.identity, updated_at="2026-04-11T00:00:00Z")
        with self.assertRaises(InputError):
            resolve_identity(future["email"], self.cutoff, [future], [])
        future_history = dict(self.history, event_time="2026-04-11T00:00:00Z")
        with self.assertRaises(InputError):
            resolve_identity("old@example.test", self.cutoff, [self.identity], [future_history])

    def test_normalization_does_not_invent_aliases(self):
        self.assertNotEqual(normalize("email", "a+b@example.test"), normalize("email", "ab@example.test"))
        self.assertNotEqual(normalize("email", "a.b@example.test"), normalize("email", "ab@example.test"))
        self.assertEqual(normalize("phone", "+1 (555) 0100"), "+15550100")
        self.assertNotEqual(normalize("phone", "5550100"), normalize("phone", "+15550100"))

    def test_two_time_cutoff_and_missing_null(self):
        early = timestamp("2026-04-10T10:00:00Z")
        fact = Fact("fact", "e1", "fixture.json", "records[0]", "observation", "accounts",
                    "profile", "USER_PROFILE", (("user_id", "subject"),), '{"email":null}',
                    early, timestamp("2026-04-10T11:00:00Z"), early, "primary")
        self.assertTrue(fact.eligible(self.cutoff))
        future = replace(fact, observed_at=timestamp("2026-04-10T13:00:00Z"))
        self.assertFalse(future.eligible(self.cutoff))
        self.assertTrue(future.eligible(timestamp("2026-04-10T14:00:00Z")))
        self.assertFalse(replace(fact, captured_at=timestamp("2026-04-11T00:00:00Z")).eligible(self.cutoff))
        self.assertIn("email", json.loads(fact.payload_json))
        self.assertNotIn("phone", json.loads(fact.payload_json))
        with self.assertRaises(FrozenInstanceError):
            fact.scope = "replica"


class SQLTests(unittest.TestCase):
    def test_all_original_sql_and_replica_drift(self):
        paths = sorted((ROOT / "dataset/evidence/databases").glob("*.sql"))
        self.assertEqual(len(paths), 24)
        tables = {p.name: read_snapshot(p.read_text()) for p in paths}
        replica = tables["customer_accounts_failover_replica_20260902.sql"]
        copies = {name: any(row.get("resource_id") == "account_005" for row in table["rows"])
                  for name,table in replica.items()}
        self.assertTrue(any(copies.values()))
        self.assertTrue(any(not present for present in copies.values()))
        scope = tables["customer_data_inventory_20260905.sql"]["snapshot_scope"]["rows"]
        self.assertEqual([r["origin_system"] for r in scope], ["account_service"])

    def test_sql_filesystem_and_extension_operations_denied(self):
        with tempfile.TemporaryDirectory(dir=TEMP) as directory:
            target = Path(directory) / "should-not-exist.db"
            statements = [f"ATTACH DATABASE '{target}' AS outside;", f"VACUUM INTO '{target}';",
                          "SELECT load_extension('anything');", "PRAGMA writable_schema=ON;",
                          "CREATE VIRTUAL TABLE bad USING fts5(text);", "PRAGMA journal_mode=WAL;"]
            for sql in statements:
                with self.subTest(sql=sql), self.assertRaises(InputError):
                    read_snapshot(sql)
                self.assertFalse(target.exists())

    def test_invalid_or_open_transaction_is_not_absence(self):
        for sql in ["not SQL", "BEGIN; CREATE TABLE x(id TEXT);"]:
            with self.subTest(sql=sql), self.assertRaises(InputError):
                read_snapshot(sql)


class StepsTests(unittest.TestCase):
    def test_complete_and_unauthorized_contracts(self):
        validate_steps("NOT_APPLICABLE", [], lambda s: False)
        validate_steps("COMPLETE", [step()], lambda s: s["evidence_id"] == "e1")
        for status, values in [("NOT_APPLICABLE", [step()]), ("COMPLETE", []), ("UNKNOWN", [])]:
            with self.subTest(status=status), self.assertRaises(InputError):
                validate_steps(status, values, lambda s: True)

    def test_malformed_fields_types_operations_and_citations_rejected(self):
        variants = [dict(step(), extra="bad"), dict(step(), step_no=True), dict(step(), step_no=2),
                    dict(step(), operation="DELETE_RECORD"), dict(step(), state="PRESENT"),
                    dict(step(), evidence_id=""), dict(step(), system_id="")]
        missing = step(); del missing["resource_id"]; variants.append(missing)
        for invalid in variants:
            with self.subTest(invalid=invalid), self.assertRaises(InputError):
                validate_steps("COMPLETE", [invalid], lambda s: True)
        with self.assertRaises(InputError):
            validate_steps("COMPLETE", [step()], lambda s: False)

    def test_canonical_risk_before_record_order_and_blank_future_citations(self):
        steps = [step("VERIFICATION", "VERIFY_RECORD_ABSENT", "ABSENT", ""),
                 step("REMEDIATION", "DELETE_RECORD", "ABSENT", ""),
                 step("FINDING", "REPORT_REMAINING_RECORD", "PRESENT", "e1"),
                 step("REMEDIATION", "BLOCK_RESTORE", "BLOCKED", "", "archive"),
                 step("FINDING", "REPORT_RESTORE_RISK", "ACTIVE", "e2", "archive"),
                 step("VERIFICATION", "VERIFY_RESTORE_BLOCKED", "BLOCKED", "", "archive")]
        ordered = canonical_steps(steps)
        validate_steps("INCOMPLETE", ordered, lambda s: True)
        self.assertEqual([s["operation"] for s in ordered if s["phase"] == "REMEDIATION"],
                         ["BLOCK_RESTORE", "DELETE_RECORD"])
        bad = copy.deepcopy(ordered); bad[-1]["evidence_id"] = "e2"
        with self.assertRaises(InputError):
            validate_steps("INCOMPLETE", bad, lambda s: True)
        bad = canonical_steps([s for s in ordered if s["operation"] != "DELETE_RECORD"])
        with self.assertRaises(InputError):
            validate_steps("INCOMPLETE", bad, lambda s: True)

    def test_string_order_and_byte_determinism(self):
        rows = [dict(case_id=c, deletion_status="NOT_APPLICABLE", steps_json="[]")
                for c in ["case_100", "case_33"]]
        result = render_rows(rows, ["case_33", "case_100"], lambda c,s: False)
        self.assertEqual(result, render_rows(rows, ["case_100", "case_33"], lambda c,s: False))
        with self.assertRaises(InputError):
            render_rows(list(reversed(rows)), ["case_33", "case_100"], lambda c,s: False)

    def test_atomic_failure_preserves_existing_output(self):
        with tempfile.TemporaryDirectory(dir=TEMP) as directory:
            path = Path(directory) / "output.csv"; path.write_bytes(b"existing")
            with patch("steps.os.replace", side_effect=OSError("synthetic interruption")):
                with self.assertRaises(OSError):
                    write_atomic(path, b"new")
            self.assertEqual(path.read_bytes(), b"existing")
            self.assertEqual(list(Path(directory).iterdir()), [path])


class RuntimeTests(unittest.TestCase):
    def test_timed_out_client_preserves_session_and_recovers_usage(self):
        def fake(command,**kwargs):
            workspace=kwargs["env"]["PWD"]
            if command[1]=="run":
                raise subprocess.TimeoutExpired(command,1,output=(json.dumps(dict(type="step_start",sessionID="ses_timeout_fixture"))+"\n").encode())
            if command[1]=="auth":data=[]
            elif command[1]=="session":data=dict(messages=[dict(type="assistant",tokens=dict(input=7,output=2))])
            elif "/api/config" in command[-1]:data=[dict(type="document",path=workspace+"/opencode.json",info={})]
            elif "/api/agent/" in command[-1]:data=dict(data=json.loads(CONFIG.read_text())["agents"]["deletion-runtime"])
            elif any(path in command[-1] for path in ["/api/plugin","/api/mcp","/api/skill"]):data=dict(data=[])
            else:data=dict(data=dict(outcome="succeeded",tokens=dict(input=7,output=2)))
            return subprocess.CompletedProcess(command,0,stdout=json.dumps(data),stderr="")
        with tempfile.TemporaryDirectory(dir=TEMP) as directory,patch("transport.subprocess.run",side_effect=fake):
            with self.assertRaises(RuntimeFailure):invoke("fixture","timeout-fixture",directory)
            record=json.loads((Path(directory)/"timeout-fixture.json").read_text())
            self.assertEqual(record["session_id"],"ses_timeout_fixture")
            self.assertEqual(record["tokens"],dict(input=7,output=2))
            self.assertEqual(record["model_calls"],1)
    def test_structured_intent_validation(self):
        requests = [{"case_id": "fixture", "request_text": "Do not delete my account."}]
        response = [dict(case_id="fixture", authorizes_deletion=False,
                         supporting_quote="Do not delete my account.", ambiguity=None)]
        self.assertEqual(validate_intents(response, requests), {"fixture": False})
        variants = [dict(response[0], authorizes_deletion="false"), dict(response[0], case_id="invented"),
                    dict(response[0], supporting_quote="Delete it"), dict(response[0], ambiguity="unsure"),
                    dict(response[0], extra=1)]
        for item in variants:
            with self.subTest(item=item), self.assertRaises(RuntimeFailure):
                validate_intents([item], requests)
        with self.assertRaises(RuntimeFailure):
            validate_intents(response * 2, requests)
        with self.assertRaises(RuntimeFailure):
            validate_intents([], requests)

    def test_fresh_location_denied_tools_and_recorded_usage(self):
        calls = []
        def fake(command, **kwargs):
            calls.append((command, kwargs))
            workspace = kwargs["env"]["PWD"]
            self.assertEqual(str(kwargs["cwd"]), workspace)
            self.assertNotIn("OPENCODE_SESSION_ID", kwargs["env"])
            if command[1] == "run":
                self.assertNotIn("--session", command)
                self.assertNotIn("--continue", command)
                self.assertNotIn("--fork", command)
                output = json.dumps({"type": "text", "sessionID": "ses_new_fixture",
                                     "part": {"text": "[]"}}) + "\n"
            elif command[1] == "auth":
                output = json.dumps([dict(id="openai",connections=[dict(method="oauth")])])
            elif command[1] == "session":
                output = json.dumps(dict(messages=[dict(type="assistant",tokens=dict(input=10,output=2))]))
            elif "/api/config" in command[-1]:
                output = json.dumps([dict(type="document", path=workspace + "/opencode.json", info={})])
            elif "/api/agent/" in command[-1]:
                output = json.dumps({"data": json.loads(CONFIG.read_text())["agents"]["deletion-runtime"]})
            elif any(path in command[-1] for path in ["/api/plugin", "/api/mcp", "/api/skill"]):
                output = json.dumps({"data": []})
            else:
                output = json.dumps({"data": dict(model=dict(providerID="openai", id="gpt-6.1-sol"),
                    agent="deletion-runtime", location=dict(directory=workspace), outcome="succeeded",
                    tokens=dict(input=10, output=2))})
            return subprocess.CompletedProcess(command, 0, stdout=output, stderr="")
        with tempfile.TemporaryDirectory(dir=TEMP) as directory, patch("transport.subprocess.run", side_effect=fake):
            record = invoke("synthetic", "fixture-job", directory)
            self.assertEqual(record["tokens"], dict(input=10, output=2))
            self.assertEqual(record["run_id"], RUN_ID)
            self.assertTrue((Path(directory) / "fixture-job.json").is_file())
            with self.assertRaises(RuntimeFailure):
                invoke("synthetic", "fixture-job", directory)
        self.assertEqual(sum(command[1] == "run" for command, _ in calls), 1)

    def test_oversized_or_invalid_jobs_fail_before_calls(self):
        with tempfile.TemporaryDirectory(dir=TEMP) as directory, patch("transport.subprocess.run") as call:
            for prompt, job in [("", "fixture"), ("x" * 60001, "fixture"), ("fixture", "../escape")]:
                with self.subTest(job=job), self.assertRaises(RuntimeFailure):
                    invoke(prompt, job, directory)
            call.assert_not_called()


class EvaluationTests(unittest.TestCase):
    def test_missing_slots_penalize_every_field(self):
        spec = importlib.util.spec_from_file_location("sample_comparator", CODE / "evaluation/main.py")
        module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
        expected = [dict(case_id="fixture", deletion_status="COMPLETE", steps_json=json.dumps([step()]))]
        actual = [dict(case_id="fixture", deletion_status="NOT_APPLICABLE", steps_json="[]")]
        result = module.compare(expected, actual)
        self.assertEqual(result["field_denominator"], 7)
        self.assertEqual(result["field_correct"], 0)
        self.assertEqual(result["step_fn"], 1)
        exact = module.compare(expected, expected)
        self.assertEqual(exact["whole_row_correct"], 1)
        self.assertEqual(exact["step_f1"], 1)


if __name__ == "__main__":
    unittest.main()
