"""Recover missing usage only for session IDs already recorded by this run's jobs."""

from datetime import datetime,timezone
import json
from pathlib import Path
import subprocess
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from prepare import BASE
from transport import RUN_ID
from usage import normalize_usage


def collect():
    supplements={}
    for path in (BASE/"jobs").glob("job-*.json"):
        record=json.loads(path.read_text())
        if record.get("run_id")!=RUN_ID:raise ValueError("Foreign run job record")
        sid=record.get("session_id")
        if not sid or record.get("tokens") is not None and record.get("model_calls") is not None and not record.get("usage_pending"):continue
        item=dict(session_id=sid,tokens=None,model_calls=None)
        result=subprocess.run(["opencode","api","get","/api/session/"+sid],text=True,capture_output=True,timeout=30)
        if result.returncode==0:
            data=json.loads(result.stdout)["data"]
            item["raw_session_usage"]={k:data.get(k) for k in ["id","model","tokens","cost","outcome"]}
            item["tokens"]=data.get("tokens")
            item["usage_pending"]=data.get("outcome") not in {"succeeded","failed","interrupted","cancelled"}
            item["normalized_usage"]=normalize_usage(item["tokens"])
        exported=subprocess.run(["opencode","session","export",sid,"--sanitize"],text=True,capture_output=True,timeout=30)
        if exported.returncode==0:
            messages=json.loads(exported.stdout).get("messages",[])
            assistants=[m for m in messages if m.get("type")=="assistant"]
            item["model_calls"]=len(assistants)
            item["raw_generation_usage"]=[{k:m.get(k) for k in ["id","model","tokens","cost","finish"]} for m in assistants]
        supplements[sid]=item
    report=dict(run_id=RUN_ID,captured_at=datetime.now(timezone.utc).isoformat(),sessions=supplements,
                scope="Missing telemetry recovery from exact current-run session IDs, no history enumeration; original records unchanged")
    (BASE/"usage-supplements.json").write_text(json.dumps(report,indent=2)+"\n")
    print("Recovered usage metadata for",len(supplements),"recorded runtime sessions")


if __name__=="__main__":collect()
