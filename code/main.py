"""Evidence-backed deletion auditing; unknown essential states block finalization."""

import argparse
import json
from datetime import datetime, timezone
import hashlib
from pathlib import Path
import sys
import uuid

from ai import AIJobs
from audit import AuditEngine
from inputs import InputError, evidence_path, load_inputs
from prepare import BASE, load_prepared, restore_facts
from sql_snapshot import read_snapshot
from steps import render_rows, write_atomic
from transport import MODEL, RUN_ID

ROOT = Path(__file__).resolve().parent.parent


def code_fingerprint():
    paths=[p for p in (ROOT/"code").rglob("*") if p.is_file() and "__pycache__" not in p.parts
           and (p.suffix==".py" or p.parent.name=="runtime" and p.suffix in {".json",".md"})]
    return {p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(paths)}


def run(sample=False, offline=False):
    request_file="sample_deletion_requests.csv" if sample else "deletion_requests.csv"
    tables,hashes=load_inputs(ROOT/"dataset",request_file)
    execution_id=("sample-" if sample else "final-")+str(uuid.uuid4())
    metadata=dict(run_id=RUN_ID,execution_id=execution_id,stage="sample" if sample else "final",
        started_at=datetime.now(timezone.utc).isoformat(),inputs=hashes,code=code_fingerprint(),model=MODEL,
        model_config_sha256=hashlib.sha256((ROOT/"code/runtime/opencode.json").read_bytes()).hexdigest(),
        prompts={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/"code/runtime").glob("*.md")},
        output_sha256=None,finalized=False,offline=offline)
    prepared,source=load_prepared(tables,hashes,offline=offline)
    metadata.update(preprocessing_snapshot=source.name,preprocessing_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                    preprocessing_execution_id=prepared["execution_id"])
    jobs=AIJobs(BASE/"jobs",execution_id,offline=offline)
    requests=sorted(tables[request_file],key=lambda r:r["case_id"])
    intents=jobs.intents(requests,metadata["stage"])
    engine=AuditEngine(tables,restore_facts(prepared),prepared["coverage"])
    decisions=[]
    for request in requests:
        try:result=engine.decide(request,intents[request["case_id"]])
        except (InputError,ValueError,KeyError,TypeError) as exc:
            result=dict(case_id=request["case_id"],status=None,steps=[],diagnostics=["Decision failed: "+str(exc)])
        decisions.append(result)
    valid=[d for d in decisions if d["status"] is not None]
    unresolved=[d for d in decisions if d["status"] is None]
    rows=[dict(case_id=d["case_id"],deletion_status=d["status"],steps_json=json.dumps(d["steps"],ensure_ascii=False)) for d in valid]
    by_case={d["case_id"]:d for d in valid}
    by_request={r["case_id"]:r for r in requests}
    def supports(case,step):
        decision=by_case[case]
        return step in decision["steps"] and engine.supports(by_request[case],decision,step)
    content=render_rows(rows,[r["case_id"] for r in valid],supports)
    directory=BASE/execution_id
    directory.mkdir(parents=True,exist_ok=False)
    write_atomic(directory/"defensible-output.csv",content)
    metadata.update(requests=len(requests),defensible=len(valid),unresolved=len(unresolved),decisions=decisions,
                    attribution=jobs.events,coverage=prepared["coverage"],completed_at=datetime.now(timezone.utc).isoformat(),
                    defensible_output_sha256=hashlib.sha256(content).hexdigest())
    if not unresolved:
        output=BASE/"sample-output.csv" if sample else ROOT/"output.csv"
        write_atomic(output,content)
        metadata.update(finalized=True,output_sha256=hashlib.sha256(content).hexdigest(),output=str(output.relative_to(ROOT)))
    elif not sample and (ROOT/"output.csv").exists():
        metadata["preserved_output_sha256"]=hashlib.sha256((ROOT/"output.csv").read_bytes()).hexdigest()
        print("WARNING: output.csv is from an earlier run and was preserved; this run did not finalize it.",file=sys.stderr)
    write_atomic(directory/"run.json",(json.dumps(metadata,ensure_ascii=False,sort_keys=True,indent=2)+"\n").encode())
    write_atomic(BASE/("latest-sample.json" if sample else "latest-final.json"),
                 (json.dumps(dict(run_id=RUN_ID,path=execution_id+"/run.json"))+"\n").encode())
    print(json.dumps(dict(run_id=RUN_ID,execution_id=execution_id,attempted=len(requests),defensible=len(valid),
                         unresolved=len(unresolved),finalized=metadata["finalized"],metadata=str(directory/"run.json"))))
    return metadata,directory


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-inputs", action="store_true", help="Validate inputs and all SQL snapshots; no model calls")
    parser.add_argument("--offline",action="store_true",help="Use validated model responses only; never invoke a provider")
    args = parser.parse_args()
    if not args.check_inputs:
        metadata,_=run(offline=args.offline)
        return 0 if metadata["finalized"] else 2
    try:
        tables, hashes = load_inputs(ROOT / "dataset")
        snapshots = []
        for row in tables["evidence_files.csv"]:
            path = evidence_path(ROOT / "dataset", row["file_path"])
            if path.suffix == ".sql":
                data = read_snapshot(path.read_text(encoding="utf-8"))
                snapshots.append({"file_id": row["file_id"], "tables": len(data),
                                  "rows": sum(len(t["rows"]) for t in data.values())})
        print(json.dumps({"run_id": RUN_ID, "requests": len(tables["deletion_requests.csv"]),
                          "manifest_artifacts": len(tables["evidence_files.csv"]),
                          "hashed_prediction_inputs": len(hashes),
                          "sql_snapshots": snapshots, "input_gate_only": True}, indent=2))
        return 0
    except (InputError, OSError, ValueError) as exc:
        print("Input gate failed: " + str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
