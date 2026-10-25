# Implementer handoff — revision 3

## Run control / outcome

- run_id: `ghost-c125c273-c4d9-4fbb-a9b8-bb80a8d06056`
- role / harness / model: implementer / OpenCode / `openai/gpt-6.1-sol`
- cycle / manager plan_revision: **1 / 3**
- status: **BLOCKED — NOT READY_FOR_AUDIT or submission**
- baseline: `0eddbbd33f682eae0a2770d67412af8a3cf4af20`, detached HEAD
- implementer native session: `ses_e8e282347ffeMXNtaG4X3niYEz`
- latest target execution: `final-fc426d06-e5d3-4d84-bf9e-0a3710a82c65`
- root output.csv: **absent**, deliberately withheld; 443 unresolved requests
- code.zip: **candidate only**, 28 members, extracted/replayed checks performed
- next role: **auditor for explicitly partial, finding-specific verification**;
  manager/source clarification and further implementation remain necessary.

All AUD-001–AUD-004 remain auditor-owned. Nothing is closed or waived here.
The runnable pipeline now exists, but it does not yet satisfy the all-518 output
or full sample-acceptance gates. “Defensible” in artifacts means passed current
engine guards, not independently established correctness.

## Instructions / boundaries verified

Read manager revision 3 and the latest complete auditor memory before editing.
Preserved this run_id and original participant data; no earlier-run source,
memories, predictions, caches or traces were imported. Current-run validated
responses were reused only with matching source/prompt/config/model/media and
fresh validation. Manager/auditor memories and profiles were not edited. DEC-005
already records the user's development subscription clarification; its concrete
reporting instructions were implemented, not replaced by a new manager decision.
No billing-clarification guard was placed on extraction, testing or evaluation.

Original 103-file dataset aggregate remains
`9fe321bd9167a5f6b831eff96b5d211c7b9c69ab4811fd88a636c4a5e31ca497`.
No source data or public label was hand-edited; no ID-number arithmetic or sample
exception was introduced. All original SQL executes only in disposable memory;
no production deletion, redaction, flow-disable or restore action is implemented.

## Implementation / changed surfaces

| Files | Implemented behavior |
| --- | --- |
| code/steps.py; code/evaluation/main.py | Shared strict present-step structure/types, especially genuine consecutive integer step_no, before comparison; no renumbering imported predictions. Incomplete/missing semantic content still gets documented union-slot penalties. Default evaluator runs the actual shared sample pipeline before reading labels and reports unresolved/subset denominators. |
| code/inputs.py; code/facts.py; code/sql_snapshot.py | Existing input, aliases, immutable facts and SQL safety retained. Original activity row numbers now survive chronological sorting. Closed SQL scope distinguishes an explicitly empty scope from unspecified scope. |
| code/extract.py | All 28 JSON, 26 logs, 1 text and 24 SQL files mapped into provenance facts. Handles nested service readbacks, record histories, scoped inventories, embedded JSON/copies, trace correlation and reused-trace reset. Preserves separate capture/export/observation times, null/missing, state/control flags and count types. Empty business interpretation cannot prove absence. PDFs use pdftotext; images use explicit attachment plus two OCR passes. Business keys without canonical IDs stay unbound unless eligible content links resolve them. |
| code/runtime/evidence.md; intent.md; opencode.json | Readable untrusted-source interpretation contracts and isolated tool-denied primary runtime. Intent now distinguishes non-destructive audit/continuation of a prior deletion from merely access/export/opt-out/hypothetical questions. Does not turn audit consent into production mutation. Generic service naming conventions and attachment/business facts are interpreted, not case labels. |
| code/ai.py | Bounded jobs, current-run hash-keyed validated responses, per-case ambiguity quarantine, at most three attempts, fresh execution-qualified session jobs after failures, explicit cache attribution. Quota circuit breaker stops further provider calls in that execution. Current-run identical prompts/config/media can be revalidated after control-code changes without needless model spending. |
| code/audit.py | Eligible alias/resource/business-link fixed point, copy-scoped latest-state reduction, closed-scope negative checks, claims not readbacks, all policy actions/conditions, stable tombstones, retained records, risk-first repairs and whole known final-state checks. Shared phone/hash/email-only links need independent ownership corroboration. Conflicts, missing periods/IDs, uncertain interpretation and historical continuity remain diagnostics and block finalization. |
| code/transport.py; code/usage.py | Actual source-stage/context, selected model/session/location checks, same-subprocess safe auth summaries, raw session and assistant usage alongside normalized counters. Null for missing/unknown counters, strict nonnegative integer validation, session deduplication, timeout session/usage recovery, pending usage not silently treated as final. API-reference scenarios never become actual billed cost. |
| code/main.py; code/prepare.py | Actual shared target/sample pipeline, 94-artifact snapshot, input/code/config/prompt/run bindings, sorted structural/proof validation and atomic final-output gate. All cases attempted; unresolved cases preserve existing root output and write only a clearly non-submission subset plus diagnostics. |
| code/evaluation/custom.py; report.py; usage_collect.py | Three actual AI-intent/JSON/planner/serializer custom evaluations; readable measured partial metrics and failures; stage-separated usage and narrowly allowlisted missing-usage recovery. |
| code/tests/*.py | **49 passing tests**, including evaluator comparator/CLI number matrix; scope, future observations, trace reuse, missing retained rows, tombstones, replicas/decoys, identifier collision corroboration, quota/cache behavior and raw-counter normalization. |
| code/package.py; README.md | Explicit source/report allowlist, no dataset/secrets/caches/nested archives, clean extracted tests/input gate and actual cached target replay. Candidate only, not an accepted submission. Historical one-off smoke source/records preserved under artifacts, not a second stale runnable transport. |

## Actual executed results

Evidence root: `artifacts/<run_id>/`.

| Check | Actual result / evidence |
| --- | --- |
| python3 -B -m unittest discover -s code/tests -v | **49/49 pass**, final root execution 16.292 s; revision3-final-checks.json. |
| python3 -B code/evaluation/custom.py | **3/3 pass** through real AI intent -> synthetic JSON-file extraction -> same AuditEngine -> strict serialization; custom-evaluation.json. Subsequent matching replays make no new call. |
| Structured extraction | All **79** structured/text artifacts accounted for by production adapters; independent real-data coverage test passes. |
| Complete preprocessing | **94/94 extraction entries, 0 parser failures, 3,323 facts**; preprocessing-1a398b9a-df45-4768-a3b7-a52e5060ac0e.json. Some model interpretation uncertainties remain per-record blockers; successful parsing does not establish all states. |
| Actual 32-sample pipeline | **32 attempted, 2 internally defensible, 30 unresolved**, exit 2. On the 2-row subset: status 2/2; exact sequence/whole-row 1/2; steps TP/FP/FN 5/0/1, F1 0.90909; fields 35/42. These are NOT full-32 scores. Latest sample pointer and metrics.json identify exact execution. |
| Actual 518-target pipeline | **518 attempted, 75 internally defensible, 443 unresolved**, exit 2. Subset statuses: 36 COMPLETE, 29 INCOMPLETE, 10 NOT_APPLICABLE. No hidden accuracy claim. All 518 intents were processed, not copied from sample labels. |
| Subset schema/proof checks | 75 unique string-sorted target IDs, exact header/seven step fields/enums/order/numbering, future citation rules, eligible file/event times and stored proof references checked; verifications cover each engine-resolved resource. Not an independent semantic audit. |
| Final output gate | Root output.csv remains absent; no invented UNKNOWN status, empty fabricated completion or copied missing row. Full-518 CSV validation cannot pass while 443 rows are unresolved. |
| Candidate package | **28 members**, byte-match current source/reports. Extracted 49-test suite and input gate exit 0; actual cached 518-target replay exits expected 2 with identical subset hash/unresolved count. External current-run validated cache used; not a cold-provider reproduction. |
| Other checks | Input gate/24 original SQL files pass; external-cwd behavior previously verified and extracted pipeline rerun; git diff --check passes; original dataset hash unchanged. Allowlist and limited key/private-key literal scan performed, not a comprehensive security certification. |

Final command records: `revision3-final-checks.json`,
`revision3-finalization-checks.json`, `candidate-package-check.json`.
Final proof/source binding is snapshot-r3.json; revision3-validation-final.json
records the prior frozen validation and the current snapshot independently binds
the latest source/run. All historical first-pass check/snapshot files are retained.

## AUD finding responses — proposed, never closed

### AUD-004 — FIXED_PENDING_REVIEW

The comparator and CLI now validate both expected/predicted present steps before
Python equality. Genuine integers/consecutive positions required; booleans,
floats, numeric strings, zero/negative/non-1 start, duplicates and skipped numbers
reject. Valid one/three-step fixtures score exactly; missing/spurious slots keep
7-field union penalties and citation change gives 6/7, nonexact sequence.
Matrix tests also cover booleans in later positions. Other counters/pages/row
counts use genuine nonnegative integer checks. Auditor must rerun the original
counterexample and full matrix before recording closure.

### AUD-003 — FIXED_PENDING_REVIEW for treatment/instrumentation; prerequisites OPEN

- Development access: user-confirmed ChatGPT subscription/sign-in, not measured
  per-call dollars. Partial cumulative counters for the two known development
  sessions are separately timestamped; no subscription allocation/API-charge/$0
  claim. Development totals/call counts are not falsely called complete.
- Actual application path: code/transport.py launches installed OpenCode CLI,
  explicit `openai/gpt-6.1-sol`, fresh tool-denied deletion-runtime, isolated
  config workspace, cwd/PWD set, OPENCODE_SESSION_ID removed, remaining ambient
  environment/service inherited. No direct OpenAI SDK client/separate credential.
- Safe auth summaries queried **inside that same subprocess context** show an
  available openai OAuth connection and no child OPENAI_API_KEY/BASE_URL override.
  Provider errors for actual runtime session ses_e8db50257ffea5FoR2yOHrdHre report
  a ChatGPT usage limit. This independently establishes a ChatGPT quota context,
  NOT the selected account, applicable per-call rate or attributable charge.
- Exact selected credential/account and OpenCode input/cache/output/reasoning
  overlap remain unexposed/unverified. Null/unknown is preserved. No coding or
  evaluation was delayed for monetary clarification.
- Stage totals in readable usage_report.md: preprocessing 81 session/assistant
  records (including failures), samples 6, custom 2, target intent 22; synthetic
  legacy smoke and development counters separately labeled. Counts describe
  observed OpenCode records, not certified underlying HTTP retries/generations.
- Latest target-attempt dependency set is **37 unique records** (15 selected
  preprocessing + 22 target intent), input **96,519**, output **28,210**, reasoning
  separately **1,367**, cache read/write **0/0**. Raw I+O arithmetic **124,729**;
  overlap/billable total unknown. Shared preprocessing deduplicated once; all
  selected attempt references retained. Superseded development/preprocessing
  calls remain visible in stage totals, not hidden as free cache.
- Official exact-model rates, retrieved 2026-10-25, are used ONLY in labeled
  Standard short-context **API-equivalent reference estimates, not actual billed
  cost**. Alternative output-includes/excludes-reasoning scenarios give
  **$0.475138 / $0.488808**, or **$0.000917255 / $0.000943645 per attempted target**,
  with explicit overlap/context/tier/region assumptions. These are conditional
  alternatives, not an invoice, verified range or finalized-output cost. Actual
  attributable subscription cost remains unmeasured; no final output hash exists.

**Auditor requested:** verify revised treatment against PS 150–158/AG §6.8,
actual raw metadata, counter deduplication/missing/pending values, exact-model
dated rates/arithmetic and the distinction between actual charges, reference
scenarios and attempt averages. Decide whether this disclosure satisfies the
estimate requirement; final output-linked accounting remains unmet. Do not close
AUD-003 from manager/user agreement alone.

### AUD-002 — BLOCKED, unchanged manager decision

object_19 was not excluded. Eligible catalog ownership and actual object-browser
evidence are preserved; September support_001 is a different filename. General
historical-object uncertainty, distinct resources, wrong-subject filename collision,
account-only scope and later eligible readback tests exist. Current case_07
remains unresolved; there is no TTL, case exception, altered label or invented
supersession. The conservative request-boundary continuity diagnostic itself
needs independent review against DEC-002, not automatic approval as a general rule.

### AUD-001 — BLOCKED / PARTIAL_IMPLEMENTATION

Production adapters, genuine AI jobs, shared pipeline, custom evaluation, all
32/518 attempts, reports and a checked candidate now exist. The original
“no pipeline” observation is superseded, but the finding is **not fixed**:
443 unresolved requests, incomplete public metrics and no full root CSV remain.

Dominant diagnostics include 343 cases without grounded account resource/state
proof and 208 retention/hold-period diagnostics (overlapping counts). Other
blockers include shared-support/exclusive-attachment conditions, business-key
binding, conflicting scopes, model uncertainties and historical continuity.
These may reflect remaining implementation/retrieval shortcomings or missing
source support; they are **not declared dataset defects**.

Concrete further review: current evidence_58 interpretation splits a document
body into support_001 SUPPORT_MESSAGE and separate attachment metadata; container
classification/linking remains unreconciled. Sample case_03's expected anonymous
analytics_9406 check is missing from the current graph: visible text hits establish
an anonymous readback and an anonymization operation claim, but no subject link
was established. Do not assign every anonymous resource to each person or embed
the expected row. Auditor should distinguish source gaps from parser/linking bugs.
Only two sample rows passing guards cannot establish full semantic correctness.

## Snapshot / reproducibility / trace

- 28-file implementation aggregate:
  `8cd2042af6fce47d4294fd66c83230a8b7f7ec7f3d56612a3c34a6cdc7befc9c`
- snapshot-r3.json SHA-256:
  `7be67c5a343ae9c6800e1fa8c34446d2ba26313963e0d149fd23d92214ce626f`
- candidate code.zip SHA-256:
  `3b5d54a5cd29ac549972af5b7a7bbafe89cb6ec2aad002a8479f366d41de9a87`
- 75-row NON-SUBMISSION subset SHA-256:
  `083c6180972e1e47531f28cb43ea695828e03c6446e31f36684a836edb88325f`
- No full output hash exists. Snapshot enumerates tracked/untracked source,
  prompts/config/tests/reports/README, latest target/input/preprocessing bindings,
  and separately 422 run artifacts. Mutable memories/logs/role controls/caches are
  excluded from the implementation fingerprint. Later edits require a new snapshot.
- session-allowlist-r3.json contains **115 exact known runtime session IDs**;
  all 115 sanitized native exports saved in native-runtime/. No history listing,
  auth-file export, credential contents or prior-run sessions were read. Sanitized
  titles do not preserve literal run titles; exact creation-record IDs were checked.
  Manager session IDs remain unavailable. Developer post-exit exports, redaction/
  completeness review and separate agent-trace.zip remain human closeout tasks.

## Reproduce / next role

```bash
python3 -B -m unittest discover -s code/tests -v
python3 -B code/main.py --check-inputs
python3 -B code/evaluation/custom.py
python3 -B code/evaluation/main.py       # partial metrics; expected exit 2 now
python3 -B code/main.py                  # 518 attempted; expected exit 2 now
python3 -B code/evaluation/usage_collect.py
python3 -B code/evaluation/report.py
python3 -B code/package.py               # candidate only
```

Auditor should inspect source first and independently rerun AUD-004/AUD-003
checks on this exact snapshot; verify all changed source, 49 tests, 94 entries,
the actual custom/sample/target results and candidate replay. Keep AUD-001/002
open and identify precise residual implementation versus source prerequisites.
Do not treat expected fail-closed exit 2 as successful submission execution.
No auditor was launched and no finding was closed. Not checked: cold extracted
provider run, cross-platform execution, invoice billing, verified counter overlap,
hidden target accuracy, or complete post-exit native trace/upload/interview.

## Short revision history

- Pass 1 / manager revision 1: fresh starter verified, 22-test foundation and
  two synthetic runtime calls; no pipeline/output/archive. Original 14-file
  snapshot `159acb3685167e766e7b5e606f5f5d8b2ff6e8d0450b0e2b355dfef71ba69cd4` retained as history.
- Revision 3 continuation: evaluator correction, full-format extraction and
  actual pipeline/usage/report/package work; recovered from provider quota without
  discarding attempts. 49 tests/custom cases pass; actual partial sample/target
  attempts and candidate replay recorded. BLOCKED, no acceptance claim.
