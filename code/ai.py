"""Run-local, hash-keyed validated interpretation jobs and stage attribution."""

import hashlib
import json
from pathlib import Path
from datetime import datetime, timezone

from transport import CONFIG, MODEL, RUN_ID, RuntimeFailure, invoke, validate_intents


class AIJobs:
    def __init__(self, directory, execution_id, offline=False):
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)
        self.execution_id = execution_id
        self.events = []
        self.provider_unavailable = False
        self.offline = offline

    def request(self, prompt, stage, context, validate, attachment=None):
        parser_bytes = b"".join(Path(__file__).with_name(name).read_bytes() for name in ["ai.py","extract.py","transport.py"])
        digest = hashlib.sha256(prompt.encode() + CONFIG.read_bytes() + MODEL.encode() + parser_bytes
                 + (Path(attachment).read_bytes() if attachment else b"")).hexdigest()
        cached = self.directory / ("validated-" + digest + ".json")
        event = dict(run_id=RUN_ID, execution_id=self.execution_id, stage=stage,
                     context=context, key=digest, at=datetime.now(timezone.utc).isoformat())
        # A control-code revision need not spend again on an identical, still-valid source job.
        # Only this run's validated responses with matching original prompt/config/model/media qualify.
        if not cached.exists():
            for previous in self.directory.glob("validated-*.json"):
                data=json.loads(previous.read_text(encoding="utf-8"))
                if data.get("run_id")!=RUN_ID or not data.get("attempt_records"):continue
                if any(Path(n).name!=n or not n.startswith("job-") or not n.endswith(".json") for n in data["attempt_records"]):
                    raise RuntimeFailure("Invalid run-local cache record reference")
                first=json.loads((self.directory/data["attempt_records"][0]).read_text())
                if (first.get("run_id")==RUN_ID
                        and first.get("prompt_sha256")==hashlib.sha256(prompt.encode()).hexdigest()
                        and first.get("config_sha256")==hashlib.sha256(CONFIG.read_bytes()).hexdigest()
                        and first.get("attachment_sha256")== (hashlib.sha256(Path(attachment).read_bytes()).hexdigest() if attachment else None)
                        and first.get("model")==MODEL):
                    try:validate(data["response"])
                    except (RuntimeFailure,ValueError,KeyError,TypeError):continue
                    data=dict(data,key=digest)
                    cached.write_text(json.dumps(data,ensure_ascii=False)+"\n",encoding="utf-8")
                    break
        if cached.exists():
            data = json.loads(cached.read_text(encoding="utf-8"))
            if data["run_id"] != RUN_ID or data["key"] != digest:
                raise RuntimeFailure("Cache identity mismatch")
            result = validate(data["response"])
            event.update(cache_hit=True, attempt_records=data["attempt_records"])
        else:
            if self.offline:
                event.update(error="Offline mode: no matching validated model response",cache_hit=False,attempt_records=[])
                self._record(event)
                raise RuntimeFailure(event["error"])
            if self.provider_unavailable:
                event.update(error="Provider usage limit already observed in this execution",cache_hit=False,attempt_records=[])
                self._record(event)
                raise RuntimeFailure(event["error"])
            attempts = []
            corrective = ""
            for attempt in range(3):
                job = "job-" + digest[:24] + "-" + hashlib.sha256(self.execution_id.encode()).hexdigest()[:8] + "-" + str(attempt)
                record_path = self.directory / (job + ".json")
                attempts.append(record_path.name)
                try:
                    if record_path.exists():
                        record = json.loads(record_path.read_text(encoding="utf-8"))
                        if record.get("run_id") != RUN_ID or record.get("error"):
                            raise RuntimeFailure("Previous current-run attempt failed")
                    else:
                        record = invoke(prompt + corrective, job, self.directory,
                            stage=stage, context=dict(execution_id=self.execution_id, **context),
                            attachment=attachment, timeout=180)
                    result = validate(record["response"])
                    cached.write_text(json.dumps(dict(run_id=RUN_ID,key=digest,
                        response=record["response"],attempt_records=attempts),ensure_ascii=False)+"\n",encoding="utf-8")
                    event.update(cache_hit=False, attempt_records=attempts)
                    break
                except (RuntimeFailure, ValueError, KeyError, TypeError) as exc:
                    if record_path.exists():
                        failed=json.loads(record_path.read_text())
                        if failed.get("provider_usage_limit"):
                            self.provider_unavailable=True
                            event.update(cache_hit=False,attempt_records=attempts,error="Provider usage limit")
                            self._record(event)
                            raise RuntimeFailure("Provider usage limit; remaining model jobs stop for this execution") from exc
                    corrective = "\nCorrection: previous attempt was invalid: " + str(exc)[:600] + ". Return the requested JSON only."
                    if attempt == 2:
                        event.update(cache_hit=False, attempt_records=attempts,error=str(exc))
                        self._record(event)
                        raise RuntimeFailure("Interpretation failed after three attempts: " + str(exc)) from exc
        self._record(event)
        return result

    def _record(self,event):
        self.events.append(event)
        with (self.directory / "attribution.jsonl").open("a",encoding="utf-8") as file:
            file.write(json.dumps(event,ensure_ascii=False)+"\n")

    def intents(self, requests, stage):
        prompt_source = Path(__file__).with_name("runtime").joinpath("intent.md").read_text(encoding="utf-8")
        results = {}
        for start in range(0,len(requests),24):
            batch = [{"case_id":r["case_id"],"request_text":r["request_text"]} for r in requests[start:start+24]]
            prompt = prompt_source + "\n<untrusted-source-json>\n" + json.dumps(batch,ensure_ascii=False) + "\n</untrusted-source-json>"
            try:
                results.update(self.request(prompt,stage,dict(case_ids=[r["case_id"] for r in batch]),
                                            lambda response: validate_intents(response,batch,allow_ambiguity=True)))
            except RuntimeFailure as exc:
                for row in batch:results[row["case_id"]] = str(exc)
        return results
