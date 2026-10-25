# Usage and billing treatment — ghost-c125c273-c4d9-4fbb-a9b8-bb80a8d06056

Generated 2026-10-25T12:55:39.622577+00:00; plan revision 3; AUD-003 remains OPEN pending auditor verification.

## Development coding sessions
The user confirmed on 2026-10-25 that development GPT 6.1 Sol access through OpenCode uses ChatGPT subscription/sign-in. Actual attributable subscription cost is unmeasured: no $0 claim, API-charge claim or arbitrary subscription allocation is made. Coding-session telemetry, if captured in current-run development-usage.json, is cumulative per known session at its timestamp, not an additional runtime ledger or complete coverage of every development session.

## Synthetic smoke tests
Historical two synthetic application-transport generations: input 2,258; output 352; separately reported reasoning 30; cache read/write 0. They are not developer-agent totals, preprocessing or final-target usage. Two early agent-not-found sessions have zero observed token counters. Revalidation reused the same recorded model response, not another generation. Historical authentication/billing of these smoke sessions was not verified.

## Actual application invocation / authentication evidence
Python launches the installed OpenCode CLI with explicit openai/gpt-6.1-sol and deletion-runtime, in a fresh temporary workspace containing the checked runtime config. cwd and PWD are set; OPENCODE_SESSION_ID is removed; other environment/service/provider selection is inherited. The config does not establish a separate billing account. Supported `opencode auth list --format json` summaries were queried through the same subprocess cwd/PWD/environment. Actual new-job records show an available openai OAuth connection; no OPENAI_API_KEY or OPENAI_BASE_URL environment override was present in those observed invocations. The runtime provider also explicitly returned ChatGPT usage-limit errors in recorded preprocessing sessions (for example ses_e8db50257ffea5FoR2yOHrdHre), independently establishing a ChatGPT quota context for those subprocess calls. Selected credential/account and attributable billing charges are still not exposed. Available OAuth plus a quota error is not proof of which account/subscription paid for a session. Development sign-in is not substituted as runtime proof. No credential contents, labels, authentication tokens, headers or secret values were printed or saved.

## Stage-separated observed application telemetry
Provider openai; exact model gpt-6.1-sol. Table covers actual current-run job records, including invalid/retried generations. Cache references are not new calls. Superseded preprocessing attempts remain included here as development/preprocessing work; the final execution attribution below selects its own dependency records.
Raw reasoning is a separate reported counter, not automatically added to output.

### Available development counters (cumulative snapshot 2026-10-25T08:49:20.991779+00:00, not complete development coverage)
| Role/session | Input | Output | Reasoning | Cache read | Cache write | Calls |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| implementer / ses_e8e282347ffeMXNtaG4X3niYEz | 202305 | 64432 | 37139 | 13685760 | 0 | unknown |
| auditor / ses_e8e0402ccffe4K5xN1SV5l8LFH | 91815 | 14650 | 3527 | 1337088 | 0 | unknown |
These development counters are not added to runtime or reference-cost totals. Actual attributable subscription cost remains unmeasured.

### Application stages
| Stage | Unique sessions | Observed assistant records | Input | Output | Reasoning | Cache read | Cache write |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| preprocessing | 81 | 81 | 176576 | 44838 | 5806 | 0 | 0 |
| sample | 6 | 6 | 9540 | 6062 | 354 | 0 | 0 |
| custom | 2 | 2 | 1565 | 304 | 28 | 0 | 0 |
| final | 22 | 22 | 44013 | 20521 | 340 | 0 | 0 |

## Latest target-attempt attribution (not a finalized-output cost)
Execution `final-fc426d06-e5d3-4d84-bf9e-0a3710a82c65`; 518 attempted requests. Deadline partial output (`output.csv`, 407/518 rows) SHA-256 `7a5ee2341d9c6341ccde64f6a28a1f5cae30a080a5d8962f7bb186a8196cebf7`; finalized=False, complete=False.
Run metadata `artifacts/ghost-c125c273-c4d9-4fbb-a9b8-bb80a8d06056/final-fc426d06-e5d3-4d84-bf9e-0a3710a82c65/run.json` records exact input/code/config/prompt hashes, preprocessing snapshot/hash and call/cache dependencies.
Observed unique dependency records: 37; normalized counters `{"cache_read": 0, "cache_write": 0, "input": 96519, "input_plus_output": 124729, "model_calls": 37, "output": 28210, "reasoning": 1367, "sessions": 37}`.
These dependencies count shared preprocessing once, including failed corrections, plus all target intent attempts. Raw session counters and per-assistant generation token metadata are retained side by side, but are NOT added to one another. Stream step counters are not also summed. Cached response references deduplicate by fresh session ID. Missing categories are null/unknown, never manufactured zeros. Model generation counts come from current-session assistant records; failed/unavailable metadata remains unknown.
Session attempt counts include failed quota-rejected invocations. Observed generations are OpenCode assistant-record counts, not independently measured underlying HTTP retries. Transport-internal retry/maintenance overhead is not exposed and is not silently certified absent. Missing counters recovered through exact-ID session metadata are stored in usage-supplements.json; original raw job records are preserved unchanged.

### API-equivalent reference estimate — not actual billed cost
Exact-model official reference https://developers.openai.com/api/docs/models/gpt-6.1-sol retrieved 2026-10-25: Standard USD/million input $2, cache read $0.10, cache write $2.50, output $10. These are hypothetical API valuations, not actual subscription charges. Assume short-context Standard, no speed/region/tool premiums or unobserved overhead. Actual applicability and token overlap mapping remain unverified.
OpenCode input/output/reasoning/cache fields are preserved as reported. We have not verified whether input includes caches or output includes reasoning. Therefore billable_total is unknown. Input-plus-output is only arithmetic on two counters, not certified billable tokens. Alternative scenarios below explicitly vary overlap; they are not a measured charge or a verified cost range.
For disjoint hypothetical quantities the reference formula is USD = (2 × uncached input + 0.10 × cache read + 2.50 × cache write + 10 × billable output) / 1,000,000. Reasoning is added only in the explicitly exclusive-output scenario, never silently twice.
- Conditional reference: {"input_includes_cache": true, "output_includes_reasoning": true, "usd": "0.475138", "usd_per_attempted_target_request": "0.000917255"}
- Conditional reference: {"input_includes_cache": true, "output_includes_reasoning": false, "usd": "0.488808", "usd_per_attempted_target_request": "0.000943645"}
- Conditional reference: {"input_includes_cache": false, "output_includes_reasoning": true, "usd": "0.475138", "usd_per_attempted_target_request": "0.000917255"}
- Conditional reference: {"input_includes_cache": false, "output_includes_reasoning": false, "usd": "0.488808", "usd_per_attempted_target_request": "0.000943645"}
Attempt-workload arithmetic: input-plus-output counters 124729/518 = 240.790 tokens per attempted request, including selected shared preprocessing once. This is not a verified billable-token average or a finalized-output figure; reference USD/request above is rounded to nine decimals under each separate assumption.
No complete/finalized 518-row output was produced; the root output is explicitly partial (407 rows, 111 omitted). Required finalized-output figures remain pending. Only the actual 518-target attempt, never smoke totals, supplies the explicitly labeled attempt denominator above. Deadline export made no additional model calls, so the attribution remains the same run's attempt workload.

## Auditor request / remaining uncertainty
Please independently verify AUD-003 against PS 150–158 / AG §6.8: exact run/output linkage, stage attribution, cumulative/session and generation counter mapping, retries/caches/missing telemetry, official reference assumptions and arithmetic, and whether the final reference estimate plus explicit unmeasured actual billing satisfies the required estimated-cost report. Selected runtime authentication/billing and OpenCode counter overlap remain precise unknowns; they do not gate unrelated implementation/evaluation. No finding is closed here.
