"""Readable reports from actual current-run artifacts; no invented final accuracy/cost."""

from collections import Counter
from datetime import datetime,timezone
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from prepare import BASE
from transport import ROOT,RUN_ID
from usage import normalize_usage,totals,reference_scenarios


def latest(kind):
    path=BASE/("latest-"+kind+".json")
    if not path.exists():return None,None
    ref=json.loads(path.read_text())
    source=BASE/ref["path"]
    if ref["run_id"]!=RUN_ID or not source.resolve().is_relative_to(BASE.resolve()):raise ValueError("Wrong run metadata reference")
    data=json.loads(source.read_text())
    if data["run_id"]!=RUN_ID:raise ValueError("Wrong run metadata")
    return data,source


def generate():
    sample,sample_path=latest("sample")
    final,final_path=latest("final")
    evaluation=[f"# Actual evaluation — {RUN_ID}","", "Plan revision 3. Findings remain auditor-owned; no acceptance is claimed.",""]
    if sample:
        metrics=json.loads(sample_path.with_name("metrics.json").read_text())
        n=metrics["cases"]
        evaluation += [f"## Public samples: {sample['requests']} attempted, {n} defensible, {sample['unresolved']} unresolved",
            "Unresolved rows are NOT silently counted as correct or fabricated. The metrics below apply only to the stated defensible subset, not all 32 samples.",
            f"- Status accuracy: {metrics['status_correct']}/{n}.",
            f"- Exact ordered sequence accuracy: {metrics['sequence_correct']}/{n}.",
            f"- Whole-row exact accuracy: {metrics['whole_row_correct']}/{n}.",
            f"- Unordered six-field step TP/FP/FN: {metrics['step_tp']}/{metrics['step_fp']}/{metrics['step_fn']}; precision {metrics['step_precision']}, recall {metrics['step_recall']}, F1 {metrics['step_f1']}.",
            f"- Field accuracy: {metrics['field_correct']}/{metrics['field_denominator']} (7 × {metrics['union_slots']} union slots).",
            f"- Per-field matches: `{json.dumps(metrics['field_correct_by_name'],sort_keys=True)}`.",
            f"- Status confusion counts: `{json.dumps(metrics['confusion'],sort_keys=True)}`.",
            f"- Evaluator SHA-256: `{hashlib.sha256(Path(__file__).with_name('main.py').read_bytes()).hexdigest()}`.",""]
        for diff in metrics["differences"]:evaluation.append(f"- Difference {diff['case_id']}, first differing step {diff['first_differing_step']}: expected `{json.dumps(diff['expected'])}`, predicted `{json.dumps(diff['predicted'])}`.")
        evaluation += ["","### Unresolved sample diagnostics"]
        for d in sample["decisions"]:
            if d["status"] is None:evaluation.append(f"- {d['case_id']}: "+"; ".join(d["diagnostics"]))
    else:evaluation += ["Public metrics N/A: no sample attempt metadata exists."]
    evaluation += ["","## Metric definitions and evaluator repair",
        "Status and exact-sequence denominators are the defensible subset explicitly stated above. Step matching ignores step_no only; all other six fields including evidence must match. Fields align by phase/system/resource/local occurrence, with seven errors for each missing/spurious slot. Sequence and whole-row checks preserve array order and integer types. AUD-004 boolean, float, string, negative, duplicate and gap numbering fixtures now fail through comparator and CLI; valid fixtures, missing/spurious penalties and changed-citation 6/7 penalty pass. Auditor verification remains requested.",
        "","## Independent integrated custom cases (source fixtures, not sample labels)",
        "Executed with `python3 -B -m unittest discover -s code/tests -v`; see code/tests/test_audit.py.",
        "Additionally `python3 -B code/evaluation/custom.py` executes CUST-001–003 through real AI intent interpretation, synthetic JSON-file extraction, the same AuditEngine, and strict serialization checks. Its run-local custom-evaluation.json records actual versus expected tuples: three cases passed. Requests are respectively ‘Remove promotional emails only. Keep my account and invoices.’, ‘Please delete my account and personal data.’, and ‘Delete my account, but preserve records lawfully required.’. This is not a public/hidden accuracy claim.",
        "- CUST-001: marketing-only opt-out, with deliberately corrupt deletion evidence. Expected and actual NOT_APPLICABLE/[]; identity/evidence/planning is bypassed. Five real synthetic multilingual/negation intent decisions were also tested separately; these are not hidden-case accuracy.",
        "- CUST-002: present readback at 10:00, file capture 11:00, audit 12:00; ignore embedded 13:00 absence and next-day file despite SUCCESS claim. Expected and actual INCOMPLETE with finding/delete/check. At 14:00 the eligible actual absence gives COMPLETE.",
        "- CUST-003: absent account, required security journal with retention through 2030, stable-reference tombstone with exposed hash. Expected and actual only tombstone redaction repair, then all three verification checks. Clearing direct identifiers yields COMPLETE with stable reference preserved.",
        "- CUST-004: primary absent, failover copy present, wrong-subject decoy. Actual finding cites failover; decoy excluded.",
        "- CUST-005: absent account, present search entry, active connector and restorable retained archive. Actual repairs disable flow, block restore, then delete search; all four final checks remain, no archive deletion.",
        "- Additional: all 15 rule actions/conditional rejection paths, missing retained record, secondary identifier on analytics, 79-artifact structured coverage, and historical object uncertainty/eligible later readback regression pass.",
        "","## AUD-002 remains unresolved",
        "The eligible catalog link activity_4007 plus screenshot evidence_46 establish object_19 / delivery_confirmation_19.pdf ownership at February observation. September support_001 in evidence_58 has a distinct filename delivery_address_correction.pdf. Account-only scopes do not erase object obligations; a same-basename record for another subject is not an alias. No expiry, sample exception or automatic perpetual old-state assertion was introduced. Historical obligations without as-of continuity remain explicit diagnostics. This general conservative rule itself still needs auditor review against DEC-002; it does not close the source clarification."]
    if final:
        evaluation += ["",f"## Target attempt: {final['requests']} processed; {final['defensible']} defensible; {final['unresolved']} unresolved",
            f"Execution `{final['execution_id']}`; output hash `{final['output_sha256']}`; finalized={final['finalized']}.",
            "Hidden target accuracy is unavailable. Root output is written only if every row is defensible; a run-local defensible subset is NOT a submission."]
    coverage=(final or sample or {}).get("coverage",[])
    if coverage:
        evaluation += ["","## Artifact coverage",f"{len(coverage)} manifest entries; {sum(not r.get('error') for r in coverage)} extraction successes; {sum(bool(r.get('error')) for r in coverage)} explicit failures."]
        for r in coverage:
            if r.get("error"):evaluation.append(f"- {r['file_id']}: {r['error']}")
    evaluation += ["","## Failures and improvements",
        "Fixed type-insensitive evaluator equality; preserved strict input, SQL and atomic-write gates. Added actual adapters, scoped facts, trace correlation, deterministic policies/plans, model interpretation and per-case diagnostics. Business interpretation and resource-link completeness remain audit concerns: for example support_001 currently yields separate message/attachment interpretations rather than a fully reconciled container record, and analytics_9406 has no established subject link in the current graph. These are not declared dataset defects or accepted label exceptions. ‘Defensible’ means passed the current engine guards, not independently verified. Business OCR/model uncertainties and missing retention/canonical-resource/as-of support remain blockers instead of fabricated absent/COMPLETE states. Passing fixtures does not resolve every real source ambiguity. Candidate packaging is not final acceptance."]
    Path(__file__).with_name("evaluation_report.md").write_text("\n".join(evaluation)+"\n",encoding="utf-8")

    records=[json.loads(p.read_text()) for p in (BASE/"jobs").glob("job-*.json")]
    supplements_path=BASE/"usage-supplements.json"
    extra=json.loads(supplements_path.read_text()) if supplements_path.exists() else dict(run_id=RUN_ID,sessions={})
    if extra["run_id"]!=RUN_ID:raise ValueError("Foreign usage supplement")
    supplements=extra["sessions"]
    def enrich(record):
        result=dict(record)
        extra=supplements.get(result.get("session_id"),{})
        for key in ["tokens","model_calls","usage_pending"]:
            if (result.get(key) is None or result.get("usage_pending")) and extra.get(key) is not None:result[key]=extra[key]
        return result
    records=[enrich(r) for r in records]
    lines=[f"# Usage and billing treatment — {RUN_ID}","",f"Generated {datetime.now(timezone.utc).isoformat()}; plan revision 3; AUD-003 remains OPEN pending auditor verification.",
        "","## Development coding sessions",
        "The user confirmed on 2026-10-25 that development GPT 6.1 Sol access through OpenCode uses ChatGPT subscription/sign-in. Actual attributable subscription cost is unmeasured: no $0 claim, API-charge claim or arbitrary subscription allocation is made. Coding-session telemetry, if captured in current-run development-usage.json, is cumulative per known session at its timestamp, not an additional runtime ledger or complete coverage of every development session.",
        "","## Synthetic smoke tests",
        "Historical two synthetic application-transport generations: input 2,258; output 352; separately reported reasoning 30; cache read/write 0. They are not developer-agent totals, preprocessing or final-target usage. Two early agent-not-found sessions have zero observed token counters. Revalidation reused the same recorded model response, not another generation. Historical authentication/billing of these smoke sessions was not verified.",
        "","## Actual application invocation / authentication evidence",
        "Python launches the installed OpenCode CLI with explicit openai/gpt-6.1-sol and deletion-runtime, in a fresh temporary workspace containing the checked runtime config. cwd and PWD are set; OPENCODE_SESSION_ID is removed; other environment/service/provider selection is inherited. The config does not establish a separate billing account. Supported `opencode auth list --format json` summaries were queried through the same subprocess cwd/PWD/environment. Actual new-job records show an available openai OAuth connection; no OPENAI_API_KEY or OPENAI_BASE_URL environment override was present in those observed invocations. The runtime provider also explicitly returned ChatGPT usage-limit errors in recorded preprocessing sessions (for example ses_e8db50257ffea5FoR2yOHrdHre), independently establishing a ChatGPT quota context for those subprocess calls. Selected credential/account and attributable billing charges are still not exposed. Available OAuth plus a quota error is not proof of which account/subscription paid for a session. Development sign-in is not substituted as runtime proof. No credential contents, labels, authentication tokens, headers or secret values were printed or saved.",
        "","## Stage-separated observed application telemetry",
        "Provider openai; exact model gpt-6.1-sol. Table covers actual current-run job records, including invalid/retried generations. Cache references are not new calls. Superseded preprocessing attempts remain included here as development/preprocessing work; the final execution attribution below selects its own dependency records.",
        "Raw reasoning is a separate reported counter, not automatically added to output."]
    development=BASE/"development-usage.json"
    if development.exists():
        data=json.loads(development.read_text())
        if data["run_id"]!=RUN_ID:raise ValueError("Foreign development usage")
        lines += ["",f"### Available development counters (cumulative snapshot {data['at']}, not complete development coverage)",
                  "| Role/session | Input | Output | Reasoning | Cache read | Cache write | Calls |",
                  "| --- | ---: | ---: | ---: | ---: | ---: | --- |"]
        for session in data["sessions"]:
            counters=normalize_usage(session.get("tokens"))
            lines.append("| "+session["role"]+" / "+session["session_id"]+" | "+" | ".join(str(counters[k]) for k in ["input","output","reasoning","cache_read","cache_write"])+" | unknown |")
        lines += ["These development counters are not added to runtime or reference-cost totals. Actual attributable subscription cost remains unmeasured."]
    lines += ["", "### Application stages", "| Stage | Unique sessions | Observed assistant records | Input | Output | Reasoning | Cache read | Cache write |", "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |"]
    for stage in ["preprocessing","sample","custom","final"]:
        stage_records=[r for r in records if r.get("stage")==stage]
        t=totals(stage_records)
        lines.append("| "+stage+" | "+" | ".join(str(t.get(k)) for k in ["sessions","model_calls","input","output","reasoning","cache_read","cache_write"])+" |")
    if final:
        prepared=json.loads((BASE/final["preprocessing_snapshot"]).read_text())
        references={name for e in prepared["attribution"]+final["attribution"] for name in e.get("attempt_records",[])}
        selected=[enrich(json.loads((BASE/"jobs"/name).read_text())) for name in sorted(references)]
        summary=totals(selected)
        lines += ["", "## Latest target-attempt attribution (not a finalized-output cost)",
            f"Execution `{final['execution_id']}`; {final['requests']} attempted requests; output_sha256=`{final['output_sha256']}`; finalized={final['finalized']}.",
            f"Run metadata `{final_path.relative_to(ROOT)}` records exact input/code/config/prompt hashes, preprocessing snapshot/hash and call/cache dependencies.",
            f"Observed unique dependency records: {len(selected)}; normalized counters `{json.dumps(summary,sort_keys=True)}`.",
            "These dependencies count shared preprocessing once, including failed corrections, plus all target intent attempts. Raw session counters and per-assistant generation token metadata are retained side by side, but are NOT added to one another. Stream step counters are not also summed. Cached response references deduplicate by fresh session ID. Missing categories are null/unknown, never manufactured zeros. Model generation counts come from current-session assistant records; failed/unavailable metadata remains unknown.",
            "Session attempt counts include failed quota-rejected invocations. Observed generations are OpenCode assistant-record counts, not independently measured underlying HTTP retries. Transport-internal retry/maintenance overhead is not exposed and is not silently certified absent. Missing counters recovered through exact-ID session metadata are stored in usage-supplements.json; original raw job records are preserved unchanged.",
            "","### API-equivalent reference estimate — not actual billed cost",
            "Exact-model official reference https://developers.openai.com/api/docs/models/gpt-6.1-sol retrieved 2026-10-25: Standard USD/million input $2, cache read $0.10, cache write $2.50, output $10. These are hypothetical API valuations, not actual subscription charges. Assume short-context Standard, no speed/region/tool premiums or unobserved overhead. Actual applicability and token overlap mapping remain unverified.",
            "OpenCode input/output/reasoning/cache fields are preserved as reported. We have not verified whether input includes caches or output includes reasoning. Therefore billable_total is unknown. Input-plus-output is only arithmetic on two counters, not certified billable tokens. Alternative scenarios below explicitly vary overlap; they are not a measured charge or a verified cost range."]
        lines.append("For disjoint hypothetical quantities the reference formula is USD = (2 × uncached input + 0.10 × cache read + 2.50 × cache write + 10 × billable output) / 1,000,000. Reasoning is added only in the explicitly exclusive-output scenario, never silently twice.")
        for scenario in reference_scenarios(summary):
            shown=dict(scenario)
            if final["requests"]==518:shown["usd_per_attempted_target_request"]=str((Decimal(scenario["usd"])/518).quantize(Decimal("0.000000001")))
            lines.append("- Conditional reference: "+json.dumps(shown,sort_keys=True))
        if final["requests"]==518 and summary["input_plus_output"] is not None:
            lines.append(f"Attempt-workload arithmetic: input-plus-output counters {summary['input_plus_output']}/518 = {summary['input_plus_output']/518:.3f} tokens per attempted request, including selected shared preprocessing once. This is not a verified billable-token average or a finalized-output figure; reference USD/request above is rounded to nine decimals under each separate assumption.")
        lines.append("No final output exists unless finalized=true. Required finalized-output figures remain pending while rows are unresolved; only the actual 518-target attempt, never smoke totals, supplies the explicitly labeled attempt denominator above.")
    lines += ["","## Auditor request / remaining uncertainty",
        "Please independently verify AUD-003 against PS 150–158 / AG §6.8: exact run/output linkage, stage attribution, cumulative/session and generation counter mapping, retries/caches/missing telemetry, official reference assumptions and arithmetic, and whether the final reference estimate plus explicit unmeasured actual billing satisfies the required estimated-cost report. Selected runtime authentication/billing and OpenCode counter overlap remain precise unknowns; they do not gate unrelated implementation/evaluation. No finding is closed here."]
    Path(__file__).with_name("usage_report.md").write_text("\n".join(lines)+"\n",encoding="utf-8")


if __name__=="__main__":generate()
