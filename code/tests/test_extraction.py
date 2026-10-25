import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from extract import Extractor,observed_state
from inputs import timestamp
from transport import RuntimeFailure


class ExtractionScopeTests(unittest.TestCase):
    def test_missing_retained_readback_and_boolean_counts(self):
        self.assertEqual(observed_state("SECURITY_AUDIT_LOG",{"rows":0}),"ABSENT")
        for key in ["rows","total_hits","direct_identifiers","http_status","status_code"]:
            with self.subTest(key=key),self.assertRaises(ValueError):observed_state("USER_PROFILE",{key:False})

    def test_empty_model_business_scan_is_not_absence(self):
        class EmptyJobs:
            def request(self,prompt,stage,context,validate,attachment=None):return validate(dict(records=[],uncertainties=[]))
        extractor=Extractor(".",{"deletion_rules.csv":[]},EmptyJobs())
        with patch("extract.subprocess.check_output",return_value="Stored business records are visible."):
            with self.assertRaises(RuntimeFailure):
                extractor.business(dict(file_id="fixture",file_path="fixture.pdf",captured_at="2026-04-10T11:00:00Z"),Path("fixture.pdf"))

    def test_reused_trace_does_not_carry_another_lookup_subject(self):
        text=("2026-04-10T10:00:00Z service=account_service trace_id=one event=profile_lookup_started subject_key=old@example.test\n"
              "2026-04-10T10:00:01Z service=account_service trace_id=one event=profile_lookup_completed resource_id=old rows=1\n"
              "2026-04-10T10:00:02Z service=account_service trace_id=one event=profile_lookup_started lookup_key=new@example.test\n"
              "2026-04-10T10:00:03Z service=account_service trace_id=one event=profile_lookup_completed resource_id=new rows=1\n")
        with tempfile.TemporaryDirectory(dir="/tmp/opencode" if Path("/tmp/opencode").is_dir() else None) as directory:
            path=Path(directory)/"fixture.log";path.write_text(text)
            extractor=Extractor(directory,{})
            extractor.log(dict(file_id="fixture",file_path="fixture.log",captured_at="2026-04-10T11:00:00Z"),path)
            self.assertNotIn(("email","old@example.test"),extractor.facts[-1].subject_keys)
            self.assertIn(("email","new@example.test"),extractor.facts[-1].subject_keys)
    def test_observed_control_labels_not_workflow_health(self):
        self.assertEqual(observed_state("DATA_FLOW",{"enabled":"Enabled"}),"ACTIVE")
        self.assertEqual(observed_state("DATA_FLOW",{"status":"Paused"}),"DISABLED")
        self.assertEqual(observed_state("DATA_FLOW",{"status":"Healthy"}),"UNKNOWN")
        self.assertEqual(observed_state("BACKUP_ARCHIVE",{"restore_allowed":"No"}),"BLOCKED")
        self.assertEqual(observed_state("BACKUP_ARCHIVE",{"status":"Healthy"}),"UNKNOWN")
    def test_embedded_future_observation_is_not_eligible(self):
        with tempfile.TemporaryDirectory(dir="/tmp/opencode" if Path("/tmp/opencode").is_dir() else None) as directory:
            path=Path(directory)/"readback.json"
            path.write_text(json.dumps(dict(exported_at="2026-04-10T11:00:00Z",records=[dict(
                recorded_at="2026-04-10T13:00:00Z",system="account_service",resource_id="fixture",
                record_type="USER_PROFILE",result="NOT_FOUND",subject_reference="user_fixture")])) )
            extractor=Extractor(directory,{})
            extractor.json(dict(file_id="fixture",file_path="readback.json",captured_at="2026-04-10T11:00:00Z"),path)
            self.assertEqual(len(extractor.facts),1)
            self.assertFalse(extractor.facts[0].eligible(timestamp("2026-04-10T12:00:00Z")))

    def test_empty_declared_sql_scope_proves_no_collection_absence(self):
        with tempfile.TemporaryDirectory(dir="/tmp/opencode" if Path("/tmp/opencode").is_dir() else None) as directory:
            path=Path(directory)/"empty.sql"
            path.write_text("CREATE TABLE snapshot_scope(origin_system TEXT,captured_at TEXT);\n"
                            "CREATE TABLE customer_profiles(resource_id TEXT,email TEXT,updated_at TEXT);\n")
            extractor=Extractor(directory,{})
            extractor.sql(dict(file_id="fixture",file_path="empty.sql",captured_at="2026-04-10T11:00:00Z"),path)
            self.assertEqual(extractor.facts,[])
