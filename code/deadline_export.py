"""Deadline-only partial export: never invent a status to fill an unresolved row."""

from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path

from inputs import load_inputs,timestamp
from prepare import BASE,restore_facts
from steps import canonical_steps,render_rows,validate_steps,write_atomic
from transport import ROOT,RUN_ID


def main():
    ref=json.loads((BASE/"latest-final.json").read_text())
    source=BASE/ref["path"];meta=json.loads(source.read_text())
    tables,hashes=load_inputs(ROOT/"dataset")
    assert meta["run_id"]==RUN_ID and meta["inputs"]==hashes
    for name,digest in meta["code"].items():
        assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest,"Original audited-attempt source changed: "+name
    prepared=json.loads((BASE/meta["preprocessing_snapshot"]).read_text())
    facts={f.fact_id:f for f in restore_facts(prepared)}
    requests={r["case_id"]:r for r in tables["deletion_requests.csv"]}
    resolved={};proof={};omitted=[];expanded=[]
    verify={"ABSENT":"VERIFY_RECORD_ABSENT","PRESENT":"VERIFY_RECORD_PRESENT","REDACTED":"VERIFY_RECORD_REDACTED",
            "ANONYMIZED":"VERIFY_RECORD_ANONYMIZED","DISABLED":"VERIFY_DATA_FLOW_DISABLED","BLOCKED":"VERIFY_RESTORE_BLOCKED"}
    for decision in meta["decisions"]:
        case=decision["case_id"]
        if decision["status"] is not None:
            resolved[case]=(decision["status"],decision["steps"])
            continue
        request=requests[case];cutoff=timestamp(request["audit_at"]);requested=timestamp(request["requested_at"])
        findings=[];repairs=[];checks=[]
        for resource in decision.get("resources",[]):
            system,rid=resource["system_id"],resource["resource_id"]
            ids=resource["fact_ids"]
            if any((rid in message or any(fid in message for fid in ids)) and any(word in message.lower()
                   for word in ["conflict","uncertain","historical","corroborat","unknown","missing","shared identifier"])
                   for message in decision.get("diagnostics",[])):continue
            candidates=[facts[fid] for fid in ids if fid in facts and facts[fid].claim_kind=="observation"
                        and facts[fid].eligible(cutoff) and facts[fid].observed_at>=requested]
            clean=[]
            for fact in candidates:
                payload=json.loads(fact.payload_json)
                if payload.get("_extraction_uncertainties") or payload.get("_corroboration_required"):continue
                clean.append((fact,payload["_state"]))
            expected=resource["expected"]
            bad=[(f,s) for f,s in clean if (expected=="ABSENT" and s in {"PRESENT","IDENTIFIABLE","ANONYMIZED","REDACTED"})
                 or (expected in {"REDACTED","ANONYMIZED"} and s=="IDENTIFIABLE")
                 or (expected in {"DISABLED","BLOCKED"} and s=="ACTIVE")]
            if not clean:continue
            def step(phase,operation,state,evidence=""):
                return dict(step_no=0,phase=phase,system_id=system,resource_id=rid,operation=operation,state=state,evidence_id=evidence)
            checks.append(step("VERIFICATION",verify[expected],expected))
            if not bad:continue
            fact,_=sorted(bad,key=lambda p:(-p[0].observed_at.timestamp(),p[0].evidence_id,p[0].location))[0]
            finding,repair,state={"ABSENT":("REPORT_REMAINING_RECORD","DELETE_RECORD","PRESENT"),
                "REDACTED":("REPORT_EXPOSED_PII","REDACT_RECORD","PRESENT"),
                "ANONYMIZED":("REPORT_EXPOSED_PII","ANONYMIZE_RECORD","PRESENT"),
                "DISABLED":("REPORT_ACTIVE_DATA_FLOW","DISABLE_DATA_FLOW","ACTIVE"),
                "BLOCKED":("REPORT_RESTORE_RISK","BLOCK_RESTORE","ACTIVE")}[expected]
            findings.append(step("FINDING",finding,state,fact.evidence_id))
            repairs.append(step("REMEDIATION",repair,expected))
            proof[(case,system,rid,fact.evidence_id)]=fact
        if findings:
            steps=canonical_steps(findings+repairs+checks)
            validate_steps("INCOMPLETE",steps,lambda s:(case,s["system_id"],s["resource_id"],s["evidence_id"]) in proof)
            resolved[case]=("INCOMPLETE",steps);expanded.append(case)
        else:omitted.append(dict(case_id=case,diagnostics=decision.get("diagnostics",[])))
    known_ids={r["file_id"] for r in tables["evidence_files.csv"]}|{r["activity_id"] for r in tables["system_activity.csv"]}
    rows=[dict(case_id=case,deletion_status=status,steps_json=json.dumps(steps,ensure_ascii=False))
          for case,(status,steps) in sorted(resolved.items())]
    content=render_rows(rows,list(resolved),lambda case,s:s["evidence_id"] in known_ids)
    write_atomic(ROOT/"output.csv",content)
    report=dict(run_id=RUN_ID,at=datetime.now(timezone.utc).isoformat(),source_execution=meta["execution_id"],
        source_metadata_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),rows=len(rows),required_rows=518,
        complete=False,output_sha256=hashlib.sha256(content).hexdigest(),expanded_positive_violation_cases=expanded,
        omitted=omitted,limitations="PARTIAL NON-COMPLIANT SUBMISSION: omitted unresolved cases; added INCOMPLETE rows contain supported violations and only known safe plans/checks, not guaranteed exhaustive remediation. No guessed statuses or invented IDs/evidence.",
        skipped=["No new model calls","No manager/auditor cycle","No broad test rerun","No cold-provider package replay","No further pricing investigation"])
    write_atomic(BASE/"deadline-export.json",(json.dumps(report,indent=2)+"\n").encode())
    print(json.dumps(dict(rows=len(rows),required=518,omitted=len(omitted),complete=False,sha256=report["output_sha256"])))


if __name__=="__main__":main()
