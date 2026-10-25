"""One fresh, tool-denied OpenCode session per bounded interpretation job."""

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import time
from usage import STAGES, normalize_usage

RUN_ID = "ghost-c125c273-c4d9-4fbb-a9b8-bb80a8d06056"
MODEL = "openai/gpt-6.1-sol"
ROOT = Path(__file__).resolve().parent.parent
CONFIG = Path(__file__).with_name("runtime") / "opencode.json"


class RuntimeFailure(RuntimeError):
    pass


def invoke(prompt, job, artifacts, attachment=None, timeout=120, stage="synthetic_smoke", context=None):
    """Record even failed attempts; never continue a session or claim missing usage is 0."""
    if not isinstance(prompt, str) or not prompt or len(prompt.encode()) > 60_000:
        raise RuntimeFailure("Empty or oversized model payload")
    if not job or any(c not in "abcdefghijklmnopqrstuvwxyz0123456789-_" for c in job):
        raise RuntimeFailure("Invalid job name")
    if stage not in STAGES:
        raise RuntimeFailure("Unknown usage stage")
    artifacts = Path(artifacts)
    artifacts.mkdir(parents=True, exist_ok=True)
    record_path = artifacts / (job + ".json")
    if record_path.exists():
        raise RuntimeFailure("Job already recorded; use an explicit new attempt ID")
    # PWD, not just subprocess cwd, determines the CLI's session location.
    temp_base = "/tmp/opencode" if Path("/tmp/opencode").is_dir() else None
    workspace = Path(tempfile.mkdtemp(prefix=RUN_ID + "-", dir=temp_base))
    config = CONFIG.read_bytes()
    (workspace / "opencode.json").write_bytes(config)
    env = os.environ.copy()
    env.pop("OPENCODE_SESSION_ID", None)
    env["PWD"] = str(workspace)
    command = ["opencode", "run", "--model", MODEL, "--agent", "deletion-runtime",
               "--format", "json", "--title", RUN_ID + ":" + job]
    attachment_hash = None
    if attachment is not None:
        attachment = Path(attachment).resolve(strict=True)
        attachment_hash = hashlib.sha256(attachment.read_bytes()).hexdigest()
        command += ["--file", str(attachment)]
    command.append(prompt)
    record = dict(run_id=RUN_ID, job=job, stage=stage, model=MODEL, context=context,
                  executable=shutil.which("opencode"), model_calls=None,
                  prompt_sha256=hashlib.sha256(prompt.encode()).hexdigest(),
                  config_sha256=hashlib.sha256(config).hexdigest(),
                  attachment_sha256=attachment_hash, workspace=str(workspace),
                  session_id=None, tokens=None, error=None)
    started = time.monotonic()
    try:
        def api(path):
            result = subprocess.run(["opencode", "api", "get", path], cwd=workspace,
                                    env=env, capture_output=True, text=True,
                                    timeout=30, check=True)
            return json.loads(result.stdout)

        location = "?location[directory]=" + str(workspace)
        # Discover configuration before resolving agents on a brand-new location.
        sources = api("/api/config" + location)
        agent = api("/api/agent/deletion-runtime" + location)["data"]
        expected = json.loads(config)["agents"]["deletion-runtime"]
        rules = agent["permissions"]
        last_deny = max(i for i, r in enumerate(rules) if r == {
            "action": "*", "resource": "*", "effect": "deny"})
        if (agent["system"] != expected["system"] or agent["steps"] != 1
                or any(r["effect"] != "deny" for r in rules[last_deny:])):
            raise RuntimeFailure("Effective runtime agent isolation differs from config")
        if isinstance(sources, dict):
            sources = sources["data"]
        for source in sources:
            info = source.get("info", {})
            if any(info.get(key) for key in ["instructions", "references"]):
                raise RuntimeFailure("Ambient instructions/references prevent isolation")
            if Path(source["path"]).resolve() != workspace / "opencode.json" and info.get("policies"):
                raise RuntimeFailure("Unreviewed ambient policy overrides")
            if source["type"] == "directory" and (Path(source["path"]) / "AGENTS.md").exists():
                raise RuntimeFailure("Ambient global AGENTS.md prevents isolation")
        if any((parent / "AGENTS.md").exists() for parent in [workspace, *workspace.parents]):
            raise RuntimeFailure("Ambient workspace AGENTS.md prevents isolation")
        plugins = api("/api/plugin" + location)["data"]
        if any(p.get("source", {}).get("type") != "builtin" for p in plugins):
            raise RuntimeFailure("Non-built-in runtime plugin prevents isolation")
        if api("/api/mcp" + location)["data"] or api("/api/skill" + location)["data"]:
            raise RuntimeFailure("Runtime MCP or skill integration unexpectedly active")
        record["containment"] = dict(agent=agent, source_paths=[s["path"] for s in sources])
        # Supported credential SUMMARY, never auth export or credential-file reads.
        auth = subprocess.run(["opencode", "auth", "list", "--format", "json"],
                              cwd=workspace, env=env, capture_output=True, text=True, timeout=30)
        methods = None
        if auth.returncode == 0:
            connections = json.loads(auth.stdout)
            methods = [c.get("method") if c.get("method") in {"oauth", "api", "api-key"} else "unknown"
                       for integration in connections if integration.get("id") == "openai"
                       for c in integration.get("connections", [])]
        record["runtime_connection"] = dict(provider="openai", model=MODEL,
            available_connection_methods=methods, selected_auth_kind=None, billing_context=None,
            evidence="Same cwd/PWD/environment/service as run; available credentials do not prove selected credential or billing",
            provider_environment_present={name: name in env for name in ["OPENAI_API_KEY", "OPENAI_BASE_URL"]})
        result = subprocess.run(command, cwd=workspace, env=env, capture_output=True,
                                text=True, timeout=timeout)
        record.update(returncode=result.returncode, stdout=result.stdout,
                      stderr=result.stderr)
        events = [json.loads(line) for line in result.stdout.splitlines() if line.strip()]
        sessions = {e["sessionID"] for e in events if "sessionID" in e}
        if len(sessions) != 1:
            raise RuntimeFailure("Missing or multiple runtime session IDs")
        record["session_id"] = sessions.pop()
        if result.returncode or any(e.get("type") == "error" for e in events):
            messages=[str(e.get("error",{}).get("message","")).lower() for e in events if e.get("type")=="error"]
            record["provider_usage_limit"]=any("usage limit" in m for m in messages)
            record["provider_reported_chatgpt_limit"]=any("chatgpt" in m and "usage limit" in m for m in messages)
            raise RuntimeFailure("OpenCode job failed")
        if any(e.get("type") not in {"step_start", "step_finish", "text", "reasoning"}
               for e in events):
            raise RuntimeFailure("Unexpected event or runtime tool execution")
        text = "".join(e["part"]["text"] for e in events if e.get("type") == "text")
        record["response"] = json.loads(text)
        data = api("/api/session/" + record["session_id"])["data"]
        record["session"] = data
        if (data["model"]["providerID"] + "/" + data["model"]["id"] != MODEL
                or data["agent"] != "deletion-runtime"
                or data["location"]["directory"] != str(workspace)
                or data.get("outcome") != "succeeded"):
            raise RuntimeFailure("Runtime model, agent, location or outcome mismatch")
        record["tokens"] = data.get("tokens")
        record["normalized_usage"] = normalize_usage(record["tokens"])
        export = subprocess.run(["opencode", "session", "export", record["session_id"], "--sanitize"],
                                cwd=workspace, env=env, capture_output=True, text=True, timeout=30)
        if export.returncode == 0:
            messages = json.loads(export.stdout).get("messages", [])
            assistants = [m for m in messages if m.get("type") == "assistant"]
            record["model_calls"] = len(assistants)
            record["raw_generation_usage"] = [{k:m.get(k) for k in ["id", "model", "tokens", "cost", "finish"]}
                                               for m in assistants]
    except (RuntimeFailure, OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as exc:
        record["error"] = str(exc)
        if isinstance(exc, subprocess.CalledProcessError):
            record["preflight_stdout"] = exc.stdout
            record["preflight_stderr"] = exc.stderr
        if isinstance(exc, subprocess.TimeoutExpired):
            partial=exc.stdout or b""
            record["stdout"] = partial.decode() if isinstance(partial,bytes) else partial
            sessions=set()
            for line in record["stdout"].splitlines():
                try:
                    event=json.loads(line)
                    if isinstance(event.get("sessionID"),str):sessions.add(event["sessionID"])
                except ValueError:continue
            if len(sessions)==1:record["session_id"]=sessions.pop()
    finally:
        if record["session_id"] and not record.get("session"):
            try:
                data=api("/api/session/"+record["session_id"])["data"]
                record["session"]=data
                record["usage_pending"]=data.get("outcome") not in {"succeeded","failed","interrupted","cancelled"}
                record["tokens"]=data.get("tokens")
                record["normalized_usage"]=normalize_usage(record["tokens"])
                exported=subprocess.run(["opencode","session","export",record["session_id"],"--sanitize"],
                    cwd=workspace,env=env,capture_output=True,text=True,timeout=30)
                if exported.returncode==0:
                    assistants=[m for m in json.loads(exported.stdout).get("messages",[]) if m.get("type")=="assistant"]
                    record["model_calls"]=len(assistants)
                    record["raw_generation_usage"]=[{k:m.get(k) for k in ["id","model","tokens","cost","finish"]} for m in assistants]
            except (OSError,ValueError,KeyError,subprocess.SubprocessError):
                record["usage_recovery_error"]="Terminal usage metadata unavailable; counters remain unknown"
        record["elapsed_seconds"] = time.monotonic() - started
        with record_path.open("x", encoding="utf-8") as file:
            json.dump(record, file, indent=2)
            file.write("\n")
    if record["error"]:
        raise RuntimeFailure(f"{record['error']}; see {record_path}")
    return record


def validate_intents(response, requests, allow_ambiguity=False):
    inputs = {r["case_id"]: r["request_text"] for r in requests}
    if len(inputs) != len(requests) or not isinstance(response, list):
        raise RuntimeFailure("Invalid intent input or response collection")
    seen = set()
    for item in response:
        if not isinstance(item, dict) or set(item) != {
                "case_id", "authorizes_deletion", "supporting_quote", "ambiguity"}:
            raise RuntimeFailure("Invalid intent fields")
        case = item["case_id"]
        if not isinstance(case, str) or case not in inputs or case in seen:
            raise RuntimeFailure("Invented or duplicate intent case")
        seen.add(case)
        quote = item["supporting_quote"]
        if (type(item["authorizes_deletion"]) is not bool
                or not isinstance(quote, str) or not quote.strip()
                or quote not in inputs[case]):
            raise RuntimeFailure("Invalid intent boolean or ungrounded quote")
        if item["ambiguity"] is not None:
            if not isinstance(item["ambiguity"],str) or not item["ambiguity"].strip():
                raise RuntimeFailure("Invalid intent ambiguity")
            if not allow_ambiguity:raise RuntimeFailure("Ambiguous intent requires review")
    if seen != set(inputs):
        raise RuntimeFailure("Missing intent results")
    return {item["case_id"]: ("Ambiguous intent: "+item["ambiguity"] if item["ambiguity"] is not None
                              else item["authorizes_deletion"]) for item in response}
