"""Extract participant artifacts once, preserving coverage, locations and raw fields."""

import argparse
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import uuid

from ai import AIJobs
from extract import Extractor
from facts import Fact
from inputs import load_inputs, timestamp
from steps import write_atomic
from transport import ROOT, RUN_ID

BASE = ROOT / "artifacts" / RUN_ID


def parser_fingerprint():
    paths=[Path(__file__).with_name(name) for name in ["extract.py","facts.py","sql_snapshot.py","inputs.py"]]
    paths += [Path(__file__).with_name("runtime")/name for name in ["evidence.md","opencode.json"]]
    return hashlib.sha256(b"".join(p.read_bytes() for p in paths)).hexdigest()


def extract_all(tables, hashes, structured_only=False):
    execution_id="preprocessing-"+str(uuid.uuid4())
    jobs=AIJobs(BASE/"jobs",execution_id)
    extractor=Extractor(ROOT/"dataset",tables,jobs)
    facts,coverage=extractor.run(structured_only=structured_only)
    serialized=[]
    for fact in facts:
        row=asdict(fact)
        for key in ["observed_at","captured_at","snapshot_at"]:row[key]=row[key].isoformat()
        serialized.append(row)
    snapshot=dict(run_id=RUN_ID,execution_id=execution_id,created_at=datetime.now(timezone.utc).isoformat(),
        inputs=hashes,parser_sha256=parser_fingerprint(),facts=serialized,coverage=coverage,attribution=jobs.events)
    path=BASE/(execution_id+".json")
    path.parent.mkdir(parents=True,exist_ok=True)
    write_atomic(path,(json.dumps(snapshot,ensure_ascii=False,sort_keys=True)+"\n").encode())
    write_atomic(BASE/"preprocessing-current.json",(json.dumps(dict(run_id=RUN_ID,path=path.name))+"\n").encode())
    return snapshot,path


def load_prepared(tables, hashes):
    pointer=BASE/"preprocessing-current.json"
    if pointer.exists():
        ref=json.loads(pointer.read_text())
        path=BASE/ref["path"]
        data=json.loads(path.read_text())
        shared=lambda values:{k:v for k,v in values.items() if k not in {"deletion_requests.csv","sample_deletion_requests.csv"}}
        if (ref["run_id"]==RUN_ID and data["run_id"]==RUN_ID and shared(data["inputs"])==shared(hashes)
                and data["parser_sha256"]==parser_fingerprint()
                and not any(r.get("skipped") for r in data["coverage"])):
            return data,path
    return extract_all(tables,hashes)


def restore_facts(data):
    facts=[]
    for raw in data["facts"]:
        row=dict(raw)
        for key in ["observed_at","captured_at","snapshot_at"]:row[key]=timestamp(row[key])
        row["subject_keys"]=tuple(tuple(pair) for pair in row["subject_keys"])
        facts.append(Fact(**row))
    return facts


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--structured-only",action="store_true")
    args=parser.parse_args()
    tables,hashes=load_inputs(ROOT/"dataset")
    data,path=extract_all(tables,hashes,args.structured_only)
    print(path)
    print("facts",len(data["facts"]),"artifacts",len(data["coverage"]),
          "errors",sum(bool(r.get("error")) for r in data["coverage"]))
