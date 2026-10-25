"""Compare independently generated sample predictions; never import into inference."""

import argparse
from collections import Counter
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from inputs import InputError, read_csv
from steps import FIELDS, HEADER, validate_structure
from transport import ROOT, RUN_ID


def compare(expected, predicted):
    truth = {r["case_id"]: r for r in expected}
    actual = {r["case_id"]: r for r in predicted}
    if len(truth) != len(expected) or len(actual) != len(predicted) or set(truth) != set(actual):
        raise InputError("Sample prediction IDs must match exactly once")
    confusion = Counter()
    fields = Counter()
    status = sequence = whole_row = tp = fp = fn = union_slots = 0
    differences = []

    def slots(steps):
        counts = Counter()
        result = {}
        for step in steps:
            key = (step["phase"], step["system_id"], step["resource_id"])
            counts[key] += 1
            result[key + (counts[key],)] = step
        return result

    for case in sorted(truth):
        a, b = truth[case], actual[case]
        left, right = json.loads(a["steps_json"]), json.loads(b["steps_json"])
        validate_structure(left)
        validate_structure(right)
        if any(r["deletion_status"] not in {"COMPLETE", "INCOMPLETE", "NOT_APPLICABLE"} for r in [a,b]):
            raise InputError("Invalid evaluation status")
        same_status = a["deletion_status"] == b["deletion_status"]
        same_sequence = left == right
        status += same_status
        sequence += same_sequence
        whole_row += same_status and same_sequence
        confusion[(a["deletion_status"], b["deletion_status"])] += 1
        lc = Counter(json.dumps({k:v for k,v in s.items() if k != "step_no"}, sort_keys=True) for s in left)
        rc = Counter(json.dumps({k:v for k,v in s.items() if k != "step_no"}, sort_keys=True) for s in right)
        tp += sum((lc & rc).values())
        fn += sum((lc - rc).values())
        fp += sum((rc - lc).values())
        lslots, rslots = slots(left), slots(right)
        for key in lslots.keys() | rslots.keys():
            union_slots += 1
            for field in FIELDS:
                if key in lslots and key in rslots and lslots[key].get(field) == rslots[key].get(field):
                    fields[field] += 1
        if not (same_status and same_sequence):
            index = next((i for i in range(max(len(left),len(right)))
                          if (left[i] if i < len(left) else None) != (right[i] if i < len(right) else None)), None)
            differences.append({"case_id": case, "status_matches": same_status,
                                "first_differing_step": None if index is None else index + 1,
                                "expected": None if index is None or index >= len(left) else left[index],
                                "predicted": None if index is None or index >= len(right) else right[index]})
    precision = tp / (tp+fp) if tp+fp else None
    recall = tp / (tp+fn) if tp+fn else None
    return dict(run_id=RUN_ID, cases=len(truth), status_correct=status,
                sequence_correct=sequence, whole_row_correct=whole_row,
                step_tp=tp, step_fp=fp, step_fn=fn, step_precision=precision,
                step_recall=recall, step_f1=2*tp/(2*tp+fp+fn) if 2*tp+fp+fn else None,
                field_correct=sum(fields.values()), field_denominator=7*union_slots,
                field_correct_by_name=dict(sorted(fields.items())), union_slots=union_slots,
                confusion=[dict(expected=a,predicted=b,count=n) for (a,b),n in sorted(confusion.items())],
                differences=differences)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--predictions", type=Path)
    args = parser.parse_args()
    run_metadata=None
    if args.predictions is None:
        from main import run
        run_metadata,directory=run(sample=True)
        args.predictions=directory/"defensible-output.csv"
    if not args.predictions.is_file():
        print("BLOCKED: no real sample-pipeline predictions exist; no accuracy is claimed.", file=sys.stderr)
        return 2
    predicted = read_csv(args.predictions, ",".join(HEADER))
    expected = read_csv(ROOT / "dataset" / "sample_output.csv", ",".join(HEADER))
    if run_metadata is not None:
        selected={r["case_id"] for r in predicted}
        expected=[r for r in expected if r["case_id"] in selected]
    try:
        measured=compare(expected,predicted)
        if run_metadata is not None:
            measured.update(attempted=run_metadata["requests"],unresolved=run_metadata["unresolved"],
                            full_sample_finalized=run_metadata["finalized"])
            (directory/"metrics.json").write_text(json.dumps(measured,indent=2)+"\n")
        print(json.dumps(measured, indent=2))
    except (InputError, ValueError, TypeError) as exc:
        print("Invalid evaluation input: " + str(exc), file=sys.stderr)
        return 1
    return 2 if run_metadata is not None and not run_metadata["finalized"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
