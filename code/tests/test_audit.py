from dataclasses import replace
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from audit import AuditEngine, policy_action
from extract import Extractor, keys_from
from facts import Fact
from inputs import InputError, SCHEMAS, load_inputs, read_csv, timestamp
from transport import ROOT

RULES=read_csv(ROOT/"dataset/deletion_rules.csv",SCHEMAS["deletion_rules.csv"])
REQUEST=dict(case_id="custom",email="new@example.test",requested_at="2026-04-10T09:00:00Z",audit_at="2026-04-10T12:00:00Z")
TABLES={"deletion_rules.csv":RULES,"user_identities.csv":[dict(user_id="user_fixture",name="Fixture Person",email="new@example.test",phone="+1 5550100",email_hash="newhash",updated_at="2026-04-01T00:00:00Z")],"user_audit_log.csv":[],"system_activity.csv":[]}


def fact(resource="account-fixture",system="account_service",category="USER_PROFILE",state="ABSENT",fields=None,
         time="2026-04-10T10:00:00Z",capture="2026-04-10T11:00:00Z",copy="service",evidence="fixture-proof"):
    payload=dict(subject_reference="user_fixture",_copy=copy,_state=state)
    payload.update(fields or {})
    return Fact(evidence+":"+resource+":"+time+":"+copy,evidence,"synthetic.json","records[0]","observation",system,resource,category,
                keys_from(payload),json.dumps(payload),timestamp(time),timestamp(capture),timestamp(capture),system+":"+copy)


class AuditCases(unittest.TestCase):
    def test_business_retention_dates_are_parsed_without_guessing_missing_periods(self):
        rules={r["data_category"]:r for r in RULES}
        cutoff=timestamp(REQUEST["audit_at"])
        for date in ["25 Aug 2027 04 03 UTC","25 Aug 2027 04:03 UTC","04 May 2033"]:
            with self.subTest(date=date):
                self.assertEqual(policy_action("SECURITY_AUDIT_LOG",dict(retention_until=date),cutoff,rules),"RETAIN")
        for date in [None,"tomorrow","04 May 2020"]:
            with self.subTest(date=date),self.assertRaises(InputError):
                policy_action("SECURITY_AUDIT_LOG",dict(retention_until=date),cutoff,rules)

    def test_output_proof_rechecks_source_state_resource_and_time(self):
        source=fact()
        engine=AuditEngine(TABLES,[source])
        decision=engine.decide(REQUEST,True)
        step=decision["steps"][0]
        self.assertTrue(engine.supports(REQUEST,decision,step))
        self.assertFalse(engine.supports(REQUEST,decision,dict(step,evidence_id="invented")))
        self.assertFalse(engine.supports(REQUEST,decision,dict(step,resource_id="different-resource")))
        payload=json.loads(source.payload_json);payload["_state"]="PRESENT"
        self.assertFalse(AuditEngine(TABLES,[replace(source,payload_json=json.dumps(payload))]).supports(REQUEST,decision,step))
        self.assertFalse(AuditEngine(TABLES,[replace(source,captured_at=timestamp("2026-04-11T00:00:00Z"))]).supports(REQUEST,decision,step))

    def test_shared_phone_without_independent_identity_does_not_establish_ownership(self):
        tables=dict(TABLES,**{"user_identities.csv":TABLES["user_identities.csv"]+[
            dict(TABLES["user_identities.csv"][0],user_id="user_other",email="other@example.test",email_hash="otherhash")]})
        uncertain=fact("phone-only","support_platform","SECONDARY_IDENTIFIER","PRESENT",
                       dict(subject_reference=None,phone="+1 5550100"))
        result=AuditEngine(tables,[fact(),uncertain]).decide(REQUEST,True)
        self.assertIsNone(result["status"])
        self.assertTrue(any("Shared identifier" in d for d in result["diagnostics"]))
        corroboration=fact("phone-only","support_platform","SECONDARY_IDENTIFIER","PRESENT")
        result=AuditEngine(tables,[fact(),uncertain,corroboration]).decide(REQUEST,True)
        self.assertEqual(result["status"],"INCOMPLETE",result["diagnostics"])
    def test_cust001_no_authorization_bypasses_everything(self):
        engine=AuditEngine({"deletion_rules.csv":RULES},[],[dict(error="corrupt",captured_at="2026-01-01T00:00:00Z",file_id="bad")])
        result=engine.decide(REQUEST,False)
        self.assertEqual((result["status"],result["steps"]),("NOT_APPLICABLE",[]))

    def test_cust002_two_time_cutoff_and_success_claim(self):
        facts=[fact(state="PRESENT"),fact(state="ABSENT",time="2026-04-10T13:00:00Z"),
               fact(state="ABSENT",time="2026-04-10T10:30:00Z",capture="2026-04-11T00:00:00Z")]
        tables=dict(TABLES,**{"system_activity.csv":[dict(activity_id="claim",event_time="2026-04-10T11:30:00Z",event_type="DELETE_RECORD",
            source_system="worker",target_system="account_service",resource_id="account-fixture",reported_result="SUCCESS",details="Deleted account-fixture.")]})
        engine=AuditEngine(tables,facts)
        result=engine.decide(REQUEST,True)
        self.assertEqual(result["status"],"INCOMPLETE",result["diagnostics"])
        self.assertEqual([s["operation"] for s in result["steps"]],["REPORT_REMAINING_RECORD","DELETE_RECORD","VERIFY_RECORD_ABSENT"])
        later=engine.decide(dict(REQUEST,audit_at="2026-04-10T14:00:00Z"),True)
        self.assertEqual(later["status"],"COMPLETE",later["diagnostics"])

    def test_cust003_tombstone_retained_and_full_verification(self):
        tomb=fact("stable-reference","identity_service","ACCOUNT_TOMBSTONE","IDENTIFIABLE",
                  dict(account_status="DELETED",name=None,email=None,phone=None,email_hash="oldhash"))
        security=fact("retained-journal","security_service","SECURITY_AUDIT_LOG","PRESENT",dict(retention_until="2030-01-01T00:00:00Z"))
        engine=AuditEngine(TABLES,[fact(),tomb,security])
        result=engine.decide(REQUEST,True)
        self.assertEqual(result["status"],"INCOMPLETE",result["diagnostics"])
        self.assertEqual([s["operation"] for s in result["steps"]],
            ["REPORT_EXPOSED_PII","REDACT_RECORD","VERIFY_RECORD_ABSENT","VERIFY_RECORD_PRESENT","VERIFY_RECORD_REDACTED"])
        self.assertTrue(all(s["evidence_id"]=="" for s in result["steps"][1:]))
        clean=json.loads(tomb.payload_json);clean.update(_state="REDACTED",email_hash=None)
        result=AuditEngine(TABLES,[fact(),replace(tomb,payload_json=json.dumps(clean)),security]).decide(REQUEST,True)
        self.assertEqual(result["status"],"COMPLETE",result["diagnostics"])
        self.assertTrue(all(s["phase"]=="VERIFICATION" and s["evidence_id"] for s in result["steps"]))

    def test_cust004_replica_and_decoy(self):
        facts=[fact(copy="primary"),fact(copy="failover",state="PRESENT",evidence="surviving-copy"),
               fact(resource="decoy",state="PRESENT",fields=dict(subject_reference="other-user",email="new@example.test.evil"))]
        result=AuditEngine(TABLES,facts).decide(REQUEST,True)
        self.assertEqual(result["status"],"INCOMPLETE",result["diagnostics"])
        self.assertEqual(result["steps"][0]["evidence_id"],"surviving-copy")
        self.assertFalse(any(s["resource_id"]=="decoy" for s in result["steps"]))

    def test_cust005_stop_flows_block_restore_before_records(self):
        facts=[fact(),fact("search-fixture","search_service","SEARCH_INDEX_ENTRY","PRESENT"),
               fact("connector-fixture","integration_service","DATA_FLOW","ACTIVE",dict(enabled=True)),
               fact("archive-fixture","backup_service","BACKUP_ARCHIVE","ACTIVE",dict(restore_allowed=True))]
        result=AuditEngine(TABLES,facts).decide(REQUEST,True)
        self.assertEqual(result["status"],"INCOMPLETE",result["diagnostics"])
        repairs=[s["operation"] for s in result["steps"] if s["phase"]=="REMEDIATION"]
        self.assertEqual(repairs,["DISABLE_DATA_FLOW","BLOCK_RESTORE","DELETE_RECORD"])
        self.assertEqual(len([s for s in result["steps"] if s["phase"]=="VERIFICATION"]),4)

    def test_retained_missing_and_unknown_period_block(self):
        for state,fields in [("ABSENT",dict(retention_until="2030-01-01T00:00:00Z")),("PRESENT",{})]:
            result=AuditEngine(TABLES,[fact(),fact("journal","security_service","SECURITY_AUDIT_LOG",state,fields)]).decide(REQUEST,True)
            self.assertIsNone(result["status"])
            self.assertTrue(result["diagnostics"])

    def test_all_fifteen_policy_actions_and_conditions(self):
        cutoff=timestamp(REQUEST["audit_at"])
        rules={r["data_category"]:r for r in RULES}
        payload=dict(_state="IDENTIFIABLE",_shared_context=True,_subject_only=True,email="fixture@example.test",
                     retention_until="2030-01-01T00:00:00Z",legal_hold_active=True,account_status="DELETED",subject_reference="user_fixture")
        for category,rule in rules.items():
            data=dict(payload)
            if category=="BACKUP_ARCHIVE":data["_state"]="ACTIVE"
            with self.subTest(category=category):self.assertEqual(policy_action(category,data,cutoff,rules),rule["required_action"])
        for category in ["SUPPORT_MESSAGE","SUPPORT_ATTACHMENT","ANALYTICS_PROFILE","PRODUCT_TELEMETRY",
                         "EMAIL_DELIVERY_LOG","SECURITY_AUDIT_LOG","LEGAL_HOLD_RECORD","BACKUP_ARCHIVE","ACCOUNT_TOMBSTONE"]:
            with self.subTest(category=category),self.assertRaises(InputError):policy_action(category,{},cutoff,rules)

    def test_secondary_identifier_category_not_service_prefix(self):
        result=AuditEngine(TABLES,[fact(),fact("contact","analytics_platform","SECONDARY_IDENTIFIER","PRESENT")]).decide(REQUEST,True)
        self.assertEqual(result["status"],"INCOMPLETE",result["diagnostics"])
        self.assertIn("DELETE_RECORD",[s["operation"] for s in result["steps"]])
        self.assertNotIn("ANONYMIZE_RECORD",[s["operation"] for s in result["steps"]])

    def test_aud002_historical_object_kept_unresolved_until_eligible_readback(self):
        old=fact("object-fixture","object_storage","SUPPORT_ATTACHMENT","PRESENT",dict(_subject_only=True),
                 time="2026-02-01T10:00:00Z",capture="2026-02-01T11:00:00Z")
        scope=replace(fact(),resource_id="",claim_kind="scope",payload_json=json.dumps(dict(_closed=True,members=[],_copy="service")))
        result=AuditEngine(TABLES,[fact(),old,scope]).decide(REQUEST,True)
        self.assertIsNone(result["status"])
        self.assertTrue(any("Historical obligation" in d for d in result["diagnostics"]))
        absent=fact("object-fixture","object_storage","SUPPORT_ATTACHMENT","ABSENT",dict(_subject_only=True))
        result=AuditEngine(TABLES,[fact(),old,scope,absent]).decide(REQUEST,True)
        self.assertEqual(result["status"],"COMPLETE",result["diagnostics"])

    def test_real_structured_79_coverage(self):
        tables,_=load_inputs(ROOT/"dataset")
        facts,ledger=Extractor(ROOT/"dataset",tables).run(structured_only=True)
        self.assertEqual(sum(not r.get("skipped") for r in ledger),79)
        self.assertFalse([r for r in ledger if r.get("error")])
        self.assertGreater(len(facts),3000)
        self.assertTrue(any("lines" in f.location for f in facts))

    def test_reused_resource_with_foreign_subject_is_not_merged(self):
        other=fact(state="PRESENT",fields=dict(subject_reference="user_other"),time="2026-04-10T10:30:00Z")
        result=AuditEngine(TABLES,[fact(),other]).decide(REQUEST,True)
        self.assertIsNone(result["status"])
        self.assertTrue(any("conflicting subject ownership" in d for d in result["diagnostics"]))
