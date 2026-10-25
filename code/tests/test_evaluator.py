import csv
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from inputs import InputError
from steps import HEADER
from transport import ROOT

spec = importlib.util.spec_from_file_location("metrics", ROOT / "code/evaluation/main.py")
metrics = importlib.util.module_from_spec(spec)
spec.loader.exec_module(metrics)


def rows(numbers):
    return [dict(case_id="fixture", deletion_status="COMPLETE", steps_json=json.dumps([
        dict(step_no=n, phase="VERIFICATION", system_id="fixture", resource_id=f"r{i}",
             operation="VERIFY_RECORD_ABSENT", state="ABSENT", evidence_id="fixture_evidence")
        for i,n in enumerate(numbers)]))]


class EvaluatorBoundaryTests(unittest.TestCase):
    def test_integer_matrix_comparator_and_cli(self):
        bad = [[True], [False], [1.0], ["1"], [0], [-1], [2], [1,1], [1,3],
               [1,True,3], [1,False,3], [1,2,True], [1,2,False], [1,2.0,3], [1,"2",3]]
        for numbers in [[1], [1,2,3]]:
            self.assertEqual(metrics.compare(rows(numbers), rows(numbers))["sequence_correct"], 1)
        with (ROOT / "dataset/sample_output.csv").open() as file:
            original = list(csv.DictReader(file))
        with tempfile.TemporaryDirectory(dir="/tmp/opencode" if Path("/tmp/opencode").is_dir() else None) as directory:
            path = Path(directory) / "predictions.csv"
            for numbers, invalid in [([1],False),([1,2,3],False),*((n,True) for n in bad)]:
                modified = [dict(r) for r in original]
                modified[0]["steps_json"] = rows(numbers)[0]["steps_json"]
                with path.open("w",newline="") as file:
                    writer=csv.DictWriter(file,fieldnames=HEADER); writer.writeheader(); writer.writerows(modified)
                result = subprocess.run([sys.executable, str(ROOT/"code/evaluation/main.py"),
                                         "--predictions",str(path)],capture_output=True,text=True)
                with self.subTest(numbers=numbers):
                    if invalid:
                        self.assertNotEqual(result.returncode,0)
                        with self.assertRaises(InputError):metrics.compare(rows([1]),rows(numbers))
                        with self.assertRaises(InputError):metrics.compare(rows(numbers),rows([1]))
                    else:self.assertEqual(result.returncode,0,result.stderr)

    def test_missing_spurious_and_citation_penalties(self):
        r=metrics.compare(rows([1]),rows([]))
        self.assertEqual((r["field_correct"],r["field_denominator"],r["step_fn"]),(0,7,1))
        r=metrics.compare(rows([]),rows([1]))
        self.assertEqual((r["field_correct"],r["field_denominator"],r["step_fp"]),(0,7,1))
        changed=rows([1]); s=json.loads(changed[0]["steps_json"]);s[0]["evidence_id"]="other"
        changed[0]["steps_json"]=json.dumps(s)
        r=metrics.compare(rows([1]),changed)
        self.assertEqual((r["field_correct"],r["field_denominator"],r["sequence_correct"]),(6,7,0))
