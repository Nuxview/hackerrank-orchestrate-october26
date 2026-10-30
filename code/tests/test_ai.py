import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from ai import AIJobs
from transport import CONFIG,MODEL,RUN_ID,RuntimeFailure


class InterpretationCacheTests(unittest.TestCase):
    def test_offline_cache_miss_never_invokes_provider(self):
        with tempfile.TemporaryDirectory() as directory:
            jobs=AIJobs(directory,"offline-fixture",offline=True)
            with patch("ai.invoke",side_effect=AssertionError("No external calls permitted")):
                with self.assertRaisesRegex(RuntimeFailure,"Offline mode"):
                    jobs.request("uncached source","custom",{},lambda response:response)
            self.assertEqual(jobs.events[0]["attempt_records"],[])
            self.assertFalse(jobs.events[0]["cache_hit"])

    def test_same_run_identical_source_revalidated_without_new_call(self):
        with tempfile.TemporaryDirectory(dir="/tmp/opencode" if Path("/tmp/opencode").is_dir() else None) as directory:
            base=Path(directory)
            (base/"job-old.json").write_text(json.dumps(dict(run_id=RUN_ID,model=MODEL,
                prompt_sha256=hashlib.sha256(b"fixture prompt").hexdigest(),
                config_sha256=hashlib.sha256(CONFIG.read_bytes()).hexdigest(),attachment_sha256=None)))
            (base/"validated-old.json").write_text(json.dumps(dict(run_id=RUN_ID,key="old-version",response={"value":7},attempt_records=["job-old.json"])))
            def validate(response):
                if response!={"value":7}:raise RuntimeFailure("wrong fixture")
                return response
            jobs=AIJobs(base,"new-execution",offline=True)
            with patch("ai.invoke",side_effect=AssertionError("Must not call provider")):
                self.assertEqual(jobs.request("fixture prompt","custom",{},validate),{"value":7})
            self.assertTrue(jobs.events[0]["cache_hit"])

    def test_quota_failure_stops_additional_calls_until_new_execution(self):
        with tempfile.TemporaryDirectory(dir="/tmp/opencode" if Path("/tmp/opencode").is_dir() else None) as directory:
            def fail(prompt,job,artifacts,**kwargs):
                (Path(artifacts)/(job+".json")).write_text(json.dumps(dict(provider_usage_limit=True)))
                raise RuntimeFailure("provider quota")
            jobs=AIJobs(directory,"first-execution")
            with patch("ai.invoke",side_effect=fail) as invoke:
                for prompt in ["fixture one","fixture two"]:
                    with self.assertRaises(RuntimeFailure):jobs.request(prompt,"custom",{},lambda r:r)
                self.assertEqual(invoke.call_count,1)
