"""Build/check an allowlisted candidate; packaging never grants audit acceptance."""

import hashlib
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import zipfile

from prepare import BASE
from steps import write_atomic
from transport import ROOT,RUN_ID


def build():
    files=[ROOT/"README.md"]+[p for p in (ROOT/"code").rglob("*") if p.is_file()
        and "__pycache__" not in p.parts and (p.suffix==".py"
        or p.parent.name=="runtime" and p.suffix in {".md",".json"}
        or p.parent.name=="evaluation" and p.suffix==".md")]
    output=io.BytesIO()
    with zipfile.ZipFile(output,"w",compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(files):
            name=path.relative_to(ROOT).as_posix()
            if path.is_symlink():raise ValueError("Do not package symlink sources")
            info=zipfile.ZipInfo(name,date_time=(2026,10,25,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED
            archive.writestr(info,path.read_bytes())
    data=output.getvalue()
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        names=archive.namelist()
        assert len(names)==len(set(names))
        assert all(not set(Path(name).parts).intersection({"dataset","artifacts","memories",".git",".opencode","__pycache__"}) for name in names)
        assert all(Path(n).suffix not in {".zip",".gz",".tar",".pyc"} for n in names)
        assert {"README.md","code/evaluation/evaluation_report.md","code/evaluation/usage_report.md"}.issubset(names)
        with tempfile.TemporaryDirectory(prefix="ghost-package-",dir="/tmp/opencode" if Path("/tmp/opencode").is_dir() else None) as directory:
            extracted=Path(directory);archive.extractall(extracted)
            (extracted/"dataset").symlink_to(ROOT/"dataset",target_is_directory=True)
            checks=[]
            for args in [[sys.executable,"-B","-m","unittest","discover","-s","code/tests","-v"],
                         [sys.executable,"-B","code/main.py","--check-inputs"]]:
                result=subprocess.run(args,cwd=extracted,text=True,capture_output=True,timeout=180)
                checks.append(dict(command=args,exit=result.returncode,stdout=result.stdout,stderr=result.stderr))
                if result.returncode:raise RuntimeError("Extracted candidate component check failed: "+result.stderr)
            if (BASE/"latest-final.json").exists():
                # Replay in an independent cache copy: never mutate the user's run or spend credits.
                prior=json.loads((BASE/json.loads((BASE/"latest-final.json").read_text())["path"]).read_text())
                replay=extracted/"artifacts"/RUN_ID
                replay.mkdir(parents=True)
                shutil.copytree(BASE/"jobs",replay/"jobs")
                for name in ["preprocessing-current.json",prior["preprocessing_snapshot"]]:
                    shutil.copy2(BASE/name,replay/name)
                command=[sys.executable,"-B","code/main.py","--offline"]
                result=subprocess.run(command,cwd=extracted,text=True,capture_output=True,timeout=180)
                checks.append(dict(command=command,exit=result.returncode,stdout=result.stdout,stderr=result.stderr))
                now=json.loads((replay/json.loads((replay/"latest-final.json").read_text())["path"]).read_text())
                assert prior["defensible_output_sha256"]==now["defensible_output_sha256"]
                assert prior["unresolved"]==now["unresolved"]
                assert result.returncode==(0 if prior["finalized"] else 2)
    write_atomic(ROOT/"code.zip",data)
    report=dict(run_id=RUN_ID,candidate_only=True,archive_sha256=hashlib.sha256(data).hexdigest(),members=names,
                checks=checks,cache_scope="Only current-run validated external cache; not a cold-provider reproducibility claim")
    write_atomic(BASE/"candidate-package-check.json",(json.dumps(report,indent=2)+"\n").encode())
    print(json.dumps(dict(archive="code.zip",sha256=report["archive_sha256"],members=len(names),candidate_only=True)))


if __name__=="__main__":build()
