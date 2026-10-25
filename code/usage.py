"""Stage-separated telemetry. Unknown accounting semantics are not invented costs."""

from decimal import Decimal
from inputs import InputError

STAGES = {"development", "synthetic_smoke", "preprocessing", "sample", "custom", "final"}


def normalize_usage(raw):
    """OpenCode session counters counted once, never also summed from stream events."""
    result = {}
    for key in ["input", "output", "reasoning"]:
        value = raw.get(key) if isinstance(raw, dict) else None
        if value is not None and (type(value) is not int or value < 0):
            raise InputError("Usage counters must be genuine nonnegative integers")
        result[key] = value
    cache = raw.get("cache") if isinstance(raw, dict) else None
    for key in ["read", "write"]:
        value = cache.get(key) if isinstance(cache, dict) else None
        if value is not None and (type(value) is not int or value < 0):
            raise InputError("Cache counters must be genuine nonnegative integers")
        result["cache_" + key] = value
    result["input_plus_output"] = (result["input"] + result["output"]
        if result["input"] is not None and result["output"] is not None else None)
    result["billable_total"] = None
    result["mapping"] = "OpenCode counters; cache/input and reasoning/output overlap unverified"
    return result


def totals(records):
    """Deduplicate sessions; cache references never create another charge/counter."""
    seen = set()
    counters = []
    calls = 0
    calls_known = True
    for record in records:
        sid = record.get("session_id")
        if sid is None or sid in seen:
            continue
        seen.add(sid)
        counters.append(normalize_usage(None if record.get("usage_pending") else record.get("tokens")))
        count = None if record.get("usage_pending") else record.get("model_calls")
        if count is None:
            calls_known = False
        elif type(count) is not int or count < 0:
            raise InputError("Invalid model call count")
        else:
            calls += count
    result = {key: (sum(c[key] for c in counters) if counters and all(c[key] is not None for c in counters) else None)
              for key in ["input", "output", "reasoning", "cache_read", "cache_write", "input_plus_output"]}
    result.update(sessions=len(seen), model_calls=calls if calls_known and counters else None)
    return result


def reference_scenarios(summary):
    """Conditional short-context Standard API USD valuation, NEVER measured billing."""
    if any(summary.get(k) is None for k in ["input", "output", "reasoning", "cache_read", "cache_write"]):
        return []
    results = []
    for input_includes_cache in [True, False]:
        uncached = summary["input"] - (summary["cache_read"] + summary["cache_write"] if input_includes_cache else 0)
        if uncached < 0:
            continue
        for output_includes_reasoning in [True, False]:
            output = summary["output"] + (0 if output_includes_reasoning else summary["reasoning"])
            cost = (Decimal(2)*uncached + Decimal("0.10")*summary["cache_read"]
                    + Decimal("2.50")*summary["cache_write"] + Decimal(10)*output)/1_000_000
            scenario = dict(input_includes_cache=input_includes_cache,
                            output_includes_reasoning=output_includes_reasoning, usd=str(cost))
            results.append(scenario)
    return results
