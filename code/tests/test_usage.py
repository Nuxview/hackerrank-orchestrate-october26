import sys
from pathlib import Path
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from inputs import InputError
from usage import normalize_usage, totals, reference_scenarios
from transport import validate_intents


class UsageTests(unittest.TestCase):
    def test_ambiguous_case_does_not_discard_other_valid_intents(self):
        requests=[dict(case_id="a",request_text="Delete my account."),dict(case_id="b",request_text="Change something.")]
        response=[dict(case_id="a",authorizes_deletion=True,supporting_quote="Delete my account.",ambiguity=None),
                  dict(case_id="b",authorizes_deletion=False,supporting_quote="Change something.",ambiguity="Scope unclear")]
        result=validate_intents(response,requests,allow_ambiguity=True)
        self.assertIs(result["a"],True)
        self.assertIsInstance(result["b"],str)
    def test_missing_is_not_zero_and_counts_are_strict(self):
        self.assertIsNone(normalize_usage(None)["input"])
        self.assertIsNone(normalize_usage({"input":0})["output"])
        for value in [True,False,1.0,-1,"4"]:
            with self.subTest(value=value), self.assertRaises(InputError):normalize_usage({"input":value})
            with self.subTest(cache=value), self.assertRaises(InputError):normalize_usage({"cache":{"read":value}})

    def test_cumulative_and_cached_records_not_double_counted(self):
        record=dict(session_id="fresh",model_calls=1,tokens=dict(input=100,output=20,reasoning=5,cache=dict(read=10,write=0)))
        result=totals([record,record,dict(cache_hit=True)])
        self.assertEqual((result["input"],result["output"],result["model_calls"]),(100,20,1))
        self.assertIsNone(normalize_usage(record["tokens"])["billable_total"])
        self.assertEqual(len(reference_scenarios(result)),4)
        self.assertEqual(reference_scenarios(dict(input=2258,output=352,reasoning=30,cache_read=0,cache_write=0))[0]["usd"],"0.008036")
        self.assertIsNone(totals([dict(record,usage_pending=True)])["input"])
