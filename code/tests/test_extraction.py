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
    def test_pdf_container_metadata_keeps_attachment_policy_and_body_identity(self):
        source="support-fixture ticket-fixture contact@example.test\fAttachment properties and upload history document.pdf ticket-fixture"
        body=dict(system_id="support_platform",resource_id="support-fixture",business_key="ticket-fixture",
                  category="SUPPORT_MESSAGE",fields=dict(email="contact@example.test"),quote="support-fixture",page=1)
        upload=dict(system_id="support_platform",resource_id=None,business_key="document.pdf",category="SUPPORT_ATTACHMENT",
                    fields=dict(file_name="document.pdf",ticket="ticket-fixture"),quote="document.pdf",page=2)
        class Jobs:
            def request(self,prompt,stage,context,validate,attachment=None):
                return validate(dict(records=[body,upload],uncertainties=[]))
        tables={"deletion_rules.csv":[dict(data_category=c) for c in ["SUPPORT_MESSAGE","SUPPORT_ATTACHMENT"]],"user_identities.csv":[]}
        manifest=dict(file_id="document",file_path="fixture.pdf",captured_at="2026-04-10T11:00:00Z")
        extractor=Extractor(".",tables,Jobs())
        with patch("extract.subprocess.check_output",return_value=source):extractor.business(manifest,Path("fixture.pdf"))
        self.assertEqual(len(extractor.facts),1)
        fact=extractor.facts[0]
        self.assertEqual((fact.resource_id,fact.category),("support-fixture","SUPPORT_ATTACHMENT"))
        self.assertIn(("email","contact@example.test"),fact.subject_keys)
        self.assertIn("identifier on page 1",fact.location)
        upload["fields"]["ticket"]="another-ticket"
        extractor=Extractor(".",tables,Jobs())
        with patch("extract.subprocess.check_output",return_value=source):extractor.business(manifest,Path("fixture.pdf"))
        self.assertEqual(len(extractor.facts),2)

    def test_snapshot_cutoffs_compare_instants_not_timestamp_strings(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/"snapshots.json"
            path.write_text(json.dumps(dict(exported_at="2026-04-10T09:00:00Z",snapshots=[dict(
                data_store="account_service",collection="customer_profiles",captured_at="2026-04-10T10:00:00+02:00",
                records=[dict(resource_id="fixture",email="fixture@example.test")]) ])))
            extractor=Extractor(directory,{})
            extractor.json(dict(file_id="fixture",file_path="snapshots.json",captured_at="2026-04-10T09:00:00Z"),path)
            self.assertEqual(extractor.facts[0].observed_at,timestamp("2026-04-10T09:00:00Z"))

    def test_json_updated_at_cannot_leak_a_future_treatment(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/"future.json"
            path.write_text(json.dumps(dict(exported_at="2026-04-10T11:00:00Z",collection="customer_profiles",records=[
                dict(resource_id="profile-fixture",email="fixture@example.test",updated_at="2026-04-11T10:00:00Z") ])))
            extractor=Extractor(directory,{})
            extractor.json(dict(file_id="future",file_path="future.json",captured_at="2026-04-10T11:00:00Z"),path)
            self.assertFalse(extractor.facts[0].eligible(timestamp("2026-04-10T12:00:00Z")))

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
