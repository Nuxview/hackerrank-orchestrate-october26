"""Three independent AI-intent -> JSON extraction -> planner -> serializer cases."""

from dataclasses import replace
import json
from pathlib import Path
import sys
import tempfile

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from ai import AIJobs
from audit import AuditEngine
from extract import Extractor
from inputs import SCHEMAS,read_csv,timestamp
from prepare import BASE
from steps import validate_steps
from transport import ROOT,RUN_ID


def main():
    requests=[dict(case_id="CUST-001",email="a@example.test",request_text="Remove promotional emails only. Keep my account and invoices."),
              dict(case_id="CUST-002",email="b@example.test",request_text="Please delete my account and personal data."),
              dict(case_id="CUST-003",email="c@example.test",request_text="Delete my account, but preserve records lawfully required.")]
    for request in requests:request.update(requested_at="2026-04-10T09:00:00Z",audit_at="2026-04-10T12:00:00Z")
    identities=[dict(user_id="user_custom_"+letter,name="Fixture "+letter,email=letter+"@example.test",phone="",email_hash="hash-"+letter,updated_at="2026-04-01T00:00:00Z") for letter in "abc"]
    tables={"deletion_rules.csv":read_csv(ROOT/"dataset/deletion_rules.csv",SCHEMAS["deletion_rules.csv"]),
            "user_identities.csv":identities,"user_audit_log.csv":[],"system_activity.csv":[]}
    records=[]
    def row(user,resource,system,category,result,**fields):
        return dict(recorded_at="2026-04-10T10:00:00Z",system=system,resource_id=resource,
                    record_type=category,result=result,subject_reference="user_custom_"+user,**fields)
    records += [row("a","profile-a","account_service","USER_PROFILE","FOUND"),
                row("a","connector-a","integration_service","DATA_FLOW","ACTIVE"),
                row("b","profile-b","account_service","USER_PROFILE","FOUND"),
                dict(row("b","profile-b","account_service","USER_PROFILE","NOT_FOUND"),recorded_at="2026-04-10T13:00:00Z"),
                row("c","profile-c","account_service","USER_PROFILE","NOT_FOUND"),
                row("c","journal-c","security_service","SECURITY_AUDIT_LOG","FOUND",retention_until="2030-01-01T00:00:00Z"),
                row("c","stable-c","identity_service","ACCOUNT_TOMBSTONE","IDENTIFIABLE",account_status="DELETED",name=None,email=None,phone=None,email_hash="hash-c")]
    jobs=AIJobs(BASE/"jobs","custom-r3")
    intents=jobs.intents(requests,"custom")
    with tempfile.TemporaryDirectory(prefix="ghost-custom-",dir="/tmp/opencode" if Path("/tmp/opencode").is_dir() else None) as directory:
        source=Path(directory)/"custom.json"
        source.write_text(json.dumps(dict(exported_at="2026-04-10T11:00:00Z",records=records)))
        extractor=Extractor(directory,tables)
        manifest=dict(file_id="custom-source",file_path="custom.json",captured_at="2026-04-10T11:00:00Z")
        extractor.json(manifest,source)
        future=replace(extractor.facts[3],evidence_id="future-file",observed_at=timestamp("2026-04-10T10:30:00Z"),
                       captured_at=timestamp("2026-04-11T00:00:00Z"))
        engine=AuditEngine(tables,extractor.facts+[future])
        expected=[("NOT_APPLICABLE",[]),("INCOMPLETE",["REPORT_REMAINING_RECORD","DELETE_RECORD","VERIFY_RECORD_ABSENT"]),
                  ("INCOMPLETE",["REPORT_EXPOSED_PII","REDACT_RECORD","VERIFY_RECORD_ABSENT","VERIFY_RECORD_PRESENT","VERIFY_RECORD_REDACTED"])]
        results=[]
        for request,(status,operations) in zip(requests,expected):
            decision=engine.decide(request,intents[request["case_id"]])
            assert decision["status"]==status,decision
            assert [s["operation"] for s in decision["steps"]]==operations,decision
            validate_steps(status,decision["steps"],lambda s:s["evidence_id"]=="custom-source")
            results.append(dict(case_id=request["case_id"],request_text=request["request_text"],expected_status=status,
                                actual_status=decision["status"],expected_operations=operations,actual_steps=decision["steps"],passed=True))
    report=dict(run_id=RUN_ID,stage="custom",cases=results,attribution=jobs.events,passed=True)
    (BASE/"custom-evaluation.json").write_text(json.dumps(report,indent=2)+"\n")
    print("PASS: 3 AI-intent/JSON-extraction/audit/serialization custom cases")


if __name__=="__main__":main()
