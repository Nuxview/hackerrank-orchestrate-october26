# Independent audit — Ghost Data Still Exists

## Run control and verdict

| Field | Reviewed value |
| --- | --- |
| run_id | `ghost-c125c273-c4d9-4fbb-a9b8-bb80a8d06056` |
| cycle / plan_revision / audit pass | 1 / 1 / 1 |
| verdict | **NEEDS_MANAGER — partial implementation, not accepted or submission-ready** |
| auditor / harness / actual development model | auditor / OpenCode / `openai/gpt-6.1-sol` (authoritative runtime metadata) |
| auditor native session | `ses_e8e0402ccffe4K5xN1SV5l8LFH` |
| baseline | `0eddbbd33f682eae0a2770d67412af8a3cf4af20`, detached HEAD |
| implementation | 14 files, including untracked source/config/prompts/tests/reports; SHA-256 `159acb3685167e766e7b5e606f5f5d8b2ff6e8d0450b0e2b355dfef71ba69cd4` |
| implementation manifest | `artifacts/<run_id>/snapshot.json`, SHA-256 `29f9b2980435c59e802b9422bd9b1b4dd8761ee31a2f99d4510f0c6add5086d8` |
| recorded runtime/check artifact aggregate | `8d4e02684b444b2093489d5a0160f0e360eb801a2e22a86e5ed5d37776590ad5`; all listed artifact bytes rechecked |
| output run / output hash / code.zip hash | none / absent / absent; no final inference run exists |
| next role | **manager**, then implementer; auditor rechecks changed snapshot afterward |

What this change does: The implementation provides input validation, eligible identity aliases, immutable fact records, restricted SQL reading, serialization helpers, a sample comparator, and synthetic AI transport checks. It does **not** yet perform deletion auditing or produce the required submission.

The user requested an audit now, despite the implementer explicitly recording **NEEDS_MANAGER / not READY_FOR_AUDIT**. This pass audits the available foundation and missing prerequisites; it does not assume a finished implementation or waive any final acceptance gate. No product, dataset, role profile, manager memory, implementer memory, report, or recorded runtime response was edited. Only this memory, required root log entries, and disposable audit artifacts were written.

## Independence, provenance, and scope

1. Read all of AGENTS.md first and appended SESSION START. Read the auditor profile, original problem statement, README, trace instructions, policy/manifest/sample data, tracked diff, and **all product source/config/prompts/tests before either role memory**.
2. Recorded the source-first acceptance checklist at `/tmp/opencode/ghost-audit-source-first/acceptance-checklist.md` before opening `memories/manager/manager-memory.md` or `memories/implementer/implementer-memory.md`. The checklist is reproduced below with results and manager ID mapping.
3. Then read both current-run memories and both evaluation Markdown reports. Their run IDs, plan revision, baseline, implementation manifest, and current implementation match. The actual implementation file set equals the manifest, including untracked files; no missing or additional non-cache code files were excluded.
4. Recomputed the original 103-file dataset aggregate: `9fe321bd9167a5f6b831eff96b5d211c7b9c69ab4811fd88a636c4a5e31ca497`, 3,978,506 bytes. Three role profiles still aggregate to `0928195088cb55b2b5037412cf8f70a8785e32bc98045031f823efb7cd6886ad`. Original four-document aggregate is `8966e1c0582270586cd0b16b0d7f2b7a90349503ad8b62d1eb4a4455a96a9c6e`, using starter README from `git show HEAD:README.md`; the current README is intentionally changed and covered by the implementation fingerprint.
5. Source inspection found no organizer-data reads, sample-answer prediction lookup, numeric case/resource inference, or prior-run cache import in the implemented path. `load_inputs` excludes public answers and the blank output template; only the evaluator reads labels. There is not yet a prediction path to certify. The manager's historical clean-start observation is consistent with the starter commit and preserved fingerprints, but current files alone cannot independently prove every historical action.

Assumed load: one terminal invocation over the supplied 518 requests and 94 evidence artifacts, not a production service. No real deletion/redaction/restore/network integration was executed. Public labels were used only for audit/evaluator fixtures. No private truth, old-attempt histories, credentials, or credential stores were inspected. No subagents were launched.

## Source-backed acceptance checklist and independent results

PS = `problem_statement.md`; AG = `AGENTS.md`. AC IDs were assigned before reading role memories; REQ/TASK mappings were added afterward.

| AC | Original source and required acceptance | Related manager IDs | Independently established result |
| --- | --- | --- | --- |
| AC-01 | AG §4, §6.1, §6.7; auditor profile 12–25,98: fresh run, immutable participant inputs, matching run/snapshot including untracked implementation | REQ-001,023; TASK-003,010 | Current baseline, dataset/profile/document hashes, implementation and artifact aggregates match; run_id agrees. Historical clean-start limitation above. |
| AC-02 | PS 17–29,91; AG §6.5: semantic multilingual authorization first; non-deletion => [] and no plan; same sample/target solver | REQ-002,016; TASK-005,006 | Recorded five-intent response independently revalidated against explicit expected booleans; negative serializer boundary checked. **No end-to-end authorization/planner bypass exists.** |
| AC-03 | PS 9,123; AG §6.1,§6.5–6: exact current/historical identifiers, provenance, decoy isolation | REQ-003; TASK-003,006 | All 550 target+sample request emails resolve uniquely with eligible aliases; unit tests cover collisions, name/substring rejection, historical provenance. Resource expansion and post-anonymization ownership missing. |
| AC-04 | PS 57,124,127; AG §6.2,§6.6: event/capture/snapshot cutoffs, eligible identities, workflow not proof | REQ-004,005; TASK-003,004,006 | Independently tested all three Fact time fields with a future value; each is ineligible. Future identity/history tests pass. No integrated reducer or claim-versus-observation decision exists. |
| AC-05 | PS 24–29,47; AG §6.6: content-grounded SQL/replica, log, JSON/text, PDF/image extraction; errors not absence | REQ-005,006; TASK-004,005 | Restricted SQL reads all 24 originals, preserves copies/scope, and rejects unsafe SQL. **55 other non-PDF/PNG adapters and 15 business PDF/PNG extractions are absent.** Auditor diagnostic extraction of all 94 files is not a product coverage ledger. |
| AC-06 | `dataset/deletion_rules.csv:2–16`; PS 13,24–29,125: conditional policy, retention, tombstones, flow/restore risk | REQ-007–009; TASK-006 | CSV action/schema gate only. No policy evaluator, 15-rule suite, retention/tombstone planner, or active-risk reconstruction. CUST-003 remains unexecuted. |
| AC-07 | AG §6.3–6.5; PS 91,103–127: complete findings/repairs/full final-state verification, ranked order, grounded eligible citations | REQ-010,011,013–015; TASK-006,007 | Helper schema/order/finding-repair-check tests pass; all public label arrays pass helper structural/source-ID/capture-time checks. Semantic `supports` callback and complete resource/check coverage are not implemented. This is not proof of citation content or all embedded timestamps. |
| AC-08 | PS 61–99; AG §6.3,§6.7: root CSV, exact header, 518 unique sorted IDs, enums/numbering, safe deterministic write | REQ-012,013,017; TASK-007,009 | Serializer/atomic-write components pass. Default CLI exits 2. **No root output.csv exists**, so final schema/count/evidence validation cannot be executed. |
| AC-09 | PS 129–139; AG §6.8; original README evaluation section: actual sample status/step/field/sequence metrics and ≥3 custom cases | REQ-018; TASK-008 | Reports correctly mark actual solver metrics N/A. Missing-slot and changed-citation metric perturbations work; new boolean-numbering false-perfect result found (AUD-004). No real sample predictions or full mandatory custom outcomes. |
| AC-10 | PS 150–160; AG §6.8: final-run provider/model/calls/tokens/cost, averages and dated pricing, cache/preprocessing separation | REQ-019; TASK-001,009 | Export totals independently reconcile: 2 synthetic generations, input 2,258/output 352/reasoning 30 separately. Final usage unavailable; live model catalog still gives `cost: []` (AUD-003). |
| AC-11 | AG §6.7,§6.9; original README packaging section: documented runnable package and reports; no forbidden contents; clean extracted run | REQ-017,022; TASK-009,010 | README accurately describes partial commands and warns not to submit. **code.zip absent**; package membership/secret exclusions/clean-package execution not testable. |
| AC-12 | AG §2–5; trace instructions 3–13,72–98: exact logging and separate complete native traces | REQ-020,021,023; TASK-011 | Existing 3 SESSION START entries and 2 prior-turn entries each have exactly one OpenCode/model context. Four allowlisted runtime exports exist; developer exports and separate trace ZIP pending human closeout. Auditor turn entry appended before handoff. |

## Independently executed checks

On 2026-10-25, Python 3.14.8; tests invoked with `-B` / `PYTHONDONTWRITEBYTECODE=1` to avoid changing product caches:

| Command/check | Actual result |
| --- | --- |
| `python3 -B -m unittest discover -s code/tests -v` | Exit 0, **22/22 pass**, 8.790 s. Inspected test assertions; these are component tests, not 22 solved deletion cases. |
| `python3 -B code/main.py --check-inputs` | Exit 0; 518 requests, 94 manifest artifacts, 100 hashed prediction files, 24 SQL snapshots, `full_solver_ready=false`. |
| Absolute `code/main.py --check-inputs` from disposable directory | Exit 0; stdout byte-identical to root invocation. |
| `python3 -B code/main.py` | Exit **2**, explicitly blocked; no output written. This end-to-end command does **not** meet the challenge. |
| `python3 -B code/evaluation/main.py` | Exit **2**, no real sample predictions; no invented accuracy. |
| `git diff --check` | Exit 0. |
| `python3 -B /tmp/opencode/ghost-audit-source-first/audit_checks.py "$PWD"` | Exit 0; rechecks fingerprints/file set, 550 eligible identity resolutions, sample structural/source-time validity, three fact cutoff gates, unauthorized serialization, metric counterexamples, cached smoke, runtime export totals. |
| Cached smoke through `smoke.main()`, with `smoke.invoke` patched to raise on any attempted provider call | Five intent expectations, exact image identifiers and OCR-grounded quote pass; **no new inference**, no paid access assumed. |
| Evaluator CLI on disposable copy of all 32 public labels, first `step_no` changed from integer `1` to JSON `true` in each row | Exit **0**, status/sequence/whole-row 32/32, fields 1,351/1,351, F1 1.0. Deliberately invalid evaluator fixture, **not solver accuracy**. |
| Independent diagnostic text reads, `pdftotext -layout` for all 4 PDFs and Tesseract for all 11 PNGs | 94 files readable/extracted; targeted object/source search confirms AMB-004 remains unreconciled. OCR/search is not a semantic completeness proof. Visually inspected evidence_46 and both evidence_58 PDF pages. |
| Available-model catalog, provider openai, query gpt-6.1-sol | Active exact ID `openai/gpt-6.1-sol`, **empty cost list**. Read-only catalog check; not a model call. |

Temporary evidence: `/tmp/opencode/ghost-audit-source-first/commands.json`, individual command records, `independent-results.json`, `invalid-boolean-evaluator-cli.json`, `source-discrepancy.json`, and `log-context-summary.json`. These are disposable audit artifacts, not submission content; findings below include standalone reproductions/source locations so closure does not depend on temporary files surviving.

## Findings — must fix / resolve before final acceptance

### AUD-001 — No deletion-audit pipeline or submission artifacts

- **Severity/category/status:** high / IMPLEMENTATION / **OPEN**.
- **Affected:** AC-02–11; REQ-002–019,022; TASK-004–010 (component work only).
- **Source/locations:** PS 15–29,61–99,129–160; AG §6.7–6.9; `code/main.py:15–35`; `code/evaluation/evaluation_report.md:88–95`; root `output.csv` and `code.zip` absent.
- **What this is / expected:** The terminal program must decide all 518 cases from source evidence and emit an evaluable output, measured reports, and runnable package.
- **Observed / impact:** Normal main always returns 2 before reading inputs or invoking auditing. `--check-inputs` only validates/reads SQL. There are no production JSON/log/text/business-document adapters, integrated intent/resource/as-of/policy/risk planner, semantic citation validator, real sample predictions, final usage, or package. Passing foundation tests cannot support deletion assurance or a submission. This is openly disclosed, not evidence of fabricated success.
- **Reproduce:** `python3 -B code/main.py` => exit 2, “full inference is not implemented”; `python3 -B code/evaluation/main.py` => exit 2. `python3 -c "from pathlib import Path; print({p:Path(p).exists() for p in ['output.csv','code.zip']})"` => both false.
- **Smallest correction:** Finish the planned source adapters and shared sample/target decision path; connect existing helpers rather than add another framework. Execute full policy/custom/sample/target checks and build the promised reports/package. Source/sample and pricing decisions do not prevent unaffected implementation work.
- **Closure:** Auditor reruns actual pipeline on ≥3 custom cases including unauthorized intent, temporal leakage, and retained tombstone; checks all 94 artifact coverage and rule conditions; recomputes 32-sample metrics with explained/dispositioned differences; validates the 518-row root CSV and real final usage; inspects and executes the clean extracted archive. New fingerprint/output/archive hashes required.
- **Owner/next role:** implementer, after manager handoff. No product fix made here.

### AUD-002 — Public-label coverage conflict has no source-backed disposition

- **Severity/category/status:** high / PLAN / **OPEN** (acceptance interpretation gate, not a proven canonical-label error or measured solver mismatch).
- **Affected:** AC-05–07,09; REQ-005,006,010,018; TASK-002,006,008; AMB-004 / IMP-B001.
- **Source/locations:** AG §6.5 “every relevant copy” and §6.6; `dataset/deletion_rules.csv:7` (rule_06); `dataset/system_activity.csv:4008` (activity_4007); `dataset/evidence_files.csv:47` (evidence_46); actual `dataset/evidence/images/object_storage_browser_20260213.png`; public `case_07` in sample requests/output; evidence_58 PDF pages 1–2.
- **What this is / expected:** Ownership, attachment treatment, and any supersession/alias must be justified without dropping old evidence or copying the public answer.
- **Observed / impact:** Screenshot proves the listed object filename; eligible catalog activity connects `object_19` / `delivery_confirmation_19.pdf` exclusively to `user_07`. Public case_07's audit is 2026-09-12 08:00Z, but its answer only covers `support_001` and `account_007`. Evidence_58 names **delivery_address_correction.pdf**, not the object filename. No later object_19 readback, deletion, or object_storage scoped snapshot was found in independent targeted extraction/search. Evidence_38 SQL's same basename belongs to a different subject/resource, not a safe alias. Old presence alone is not automatically current presence; equally, the label's omission is not proof of deletion. The obligation/as-of state remains unreconciled.
- **Reproduce:** `rg -n 'object_19|delivery_confirmation_19|object_storage' dataset -g '*.csv' -g '*.sql' -g '*.json' -g '*.log' -g '*.txt'`; inspect evidence_46; `pdftotext -layout dataset/evidence/documents/delivery_correction_attachment.pdf -`; compare the public case_07 array. Search finds the one ownership activity and unrelated SQL filename collision, not a source-backed removal. All 94-artifact OCR/text diagnostic search is recorded separately; OCR can miss content, so absence of a text hit is not claimed exhaustive proof of a dataset defect.
- **Smallest correction:** Manager must document a grounded scope/alias/supersession interpretation, obtain source clarification, or explicitly disposition an honestly reported sample disagreement/uncertainty without claiming perfect sample agreement. Do not alter supplied labels, discard pre-request evidence globally, invent an alias, or special-case case_07. A manager preference cannot itself prove the required state.
- **Closure:** Written source-referenced disposition; implemented general rule tested against both the source conflict and decoys; real sample metrics/rationale reflect the result; auditor independently rechecks it. If no defensible state can be established, preserve an explicit blocker rather than fabricate COMPLETE/absence.
- **Owner/next role:** manager; implementer follows the decision, auditor owns verification.

## Findings — should fix / prerequisite gap

### AUD-003 — Authorized model prices remain unavailable

- **Severity/category/status:** medium / USAGE / **OPEN**.
- **Affected:** AC-10; REQ-019; TASK-001,009; AMB-005 / IMP-B002.
- **Source/locations:** PS 150–158; AG §6.8; `code/evaluation/usage_report.md:34–48`; independently queried current model catalog for `openai/gpt-6.1-sol`.
- **What this is / expected:** Final output's actual attributable model usage needs an estimated total/per-request monetary cost using dated, authorized rates and a stated billing method.
- **Observed / impact:** Catalog still returns `cost: []`. Report honestly says pricing and final-run usage are N/A; session `cost:0` is not billing proof. Smoke totals are correct but cannot replace final-run cost. Mandatory cost reporting remains unmet; missing rates are not an excuse to delay parsers/planner.
- **Reproduce:** Available-model tool query `{provider:'openai', query:'gpt-6.1-sol'}` returns an active model with empty cost entries; inspect usage_report pricing section. Auditor did not inspect billing or credential stores.
- **Smallest correction:** Manager obtains dated applicable billing rates/source or authorizes an available runtime with known rates and valid access. An exception must be supported by the challenge owner, not an internal agreement to call unavailable cost zero or complete.
- **Closure:** Final run ledger plus output hash; exact providers/models/calls/token categories/cache/retry accounting; dated pricing and explicit total/518 averages, reconciled independently. Development usage remains separately labeled.
- **Owner/next role:** manager for access/rates/authorized configuration; implementer for final telemetry/report, auditor verifies.

### AUD-004 — Evaluator counts boolean step numbers as exact integer matches

- **Severity/category/status:** medium / EVALUATION / **OPEN**; independently discovered in this pass.
- **Affected:** AC-08,09; REQ-013,018; TASK-008.
- **Source/locations:** PS 75–99; `code/evaluation/main.py:34–38,49–53,80–82`; contrasting strict check in `code/steps.py:50–51`; current tests only cover metric missing slots (`code/tests/test_core.py:267–279`).
- **What this is / expected:** Imported predictions are an untrusted evaluator input. A malformed `step_no:true` must be rejected or fail exact field/sequence comparison, not score as the required integer `1`.
- **Observed / impact:** Python compares `True == 1`. The comparator performs normal dictionary/list equality and never validates step schemas on its CLI input. A synthetic one-step prediction with true instead of 1 receives perfect whole-row/sequence/F1 and 7/7 fields; mutating all 32 public first-step numbers similarly yields 32/32 and 1,351/1,351 with exit 0. The product serializer does reject it, but the external prediction-file evaluator bypasses that gate. No existing reported solver score is fabricated—none exists yet—but future claimed exact accuracy can be wrong.
- **Standalone reproduction (repository root):**

```bash
python3 -B - <<'PY'
import importlib.util, json
spec = importlib.util.spec_from_file_location('metrics', 'code/evaluation/main.py')
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
s = dict(step_no=1, phase='VERIFICATION', system_id='fixture', resource_id='account',
         operation='VERIFY_RECORD_ABSENT', state='ABSENT', evidence_id='fixture_evidence')
a = dict(case_id='fixture', deletion_status='COMPLETE', steps_json=json.dumps([s]))
b = dict(a, steps_json=json.dumps([dict(s, step_no=True)]))
r = m.compare([a], [b])
print(r['whole_row_correct'], r['sequence_correct'], r['field_correct'], r['field_denominator'])
PY
```

Actual result: `1 1 7 7`; expected rejection or non-exact score.

- **Smallest correction:** Apply strict structural/type validation before comparison (separate from unavailable semantic evidence validation), or use JSON-type-sensitive field/sequence comparisons. Reuse existing schema rules where practical. Add the boolean-numbering regression through both comparator and CLI, without suppressing legitimate missing-step penalties.
- **Closure:** Reproduction no longer reports exact equality; malformed CLI input exits nonzero or is explicitly scored invalid; valid exact fixtures remain perfect and missing/citation perturbations retain the documented denominators. Recompute actual metrics after implementation exists.
- **Owner/next role:** implementer; auditor alone closes after executing regression.

## Claim comparison, reports, and finding history

- Manager says READY_FOR_IMPLEMENTATION only, not acceptance. Its original input counts/hashes and deterministic operation-rank ordering agree with current sources. No evidence supports overriding the exact PS operation order; no genuine dependency contradiction was established in this pass.
- Implementer says foundation only, no final output/archive, 22 component tests, pending policy/extractors/custom/sample/target/package checks. All verified claims are consistent with source and reruns. NEEDS_MANAGER is accurate; do not reinterpret this as NEEDS_AUDIT/PASS.
- Evaluation report contains readable custom specifications and honestly marks CUST-003 unexecuted and actual sample accuracy N/A. Specifications and component checks are not three completed end-to-end deletion evaluations. Comparator missing-step and changed-evidence penalties work; AUD-004 narrows the evaluator claim.
- Usage report accurately separates two synthetic runtime calls from development-agent totals and nonexistent final-target usage. Four allowlisted exported sessions contain two assistant generations and no tool content; token totals match their metadata. Sanitized exports redact message text, so these alone do not prove full source prompts or replace human-reviewed complete native traces. Cached smoke matches prompt/config/image hashes and explicit expected outputs; fresh provider invocation/containment was not independently rerun.
- No prior auditor findings existed in this run. **AUD-001–004 are newly OPEN; none is CLOSED_VERIFIED or waived.** The report does not fix product code or propose that agreement between roles closes findings.

## Limitations, human closeout, and next handoff

Not checked: a fresh paid inference, live runtime containment at new inference time, full end-to-end authorization/evidence/policy decisions, actual sample/hidden-target accuracy, all business-artifact semantic extraction, final-output citations, final-run costs, package execution, or post-exit trace exports. These are missing/unapproved prerequisites, not successful checks. Hidden 518-case accuracy is unavailable to participants. No production operations, external credential use, dependency installation, or old-history enumeration was needed.

Human must later identify the manager session from their actual session metadata (allowlist currently has null), preserve/export the implementer session `ses_e8e282347ffeMXNtaG4X3niYEz`, this auditor session, all later development sessions, and four recorded runtime sessions. After quitting each session, use verified OpenCode export functionality, review useful prompt/response coverage and sensitive-content redaction, then build **separate** agent-trace.zip. No whole database/auth files, prior attempts, or nested trace archive in code.zip. Upload and AI interview remain human actions, not completed software checks.

**Next: manager** disposes AUD-002 and obtains rates/authorized runtime decision for AUD-003, while keeping the mandatory contract intact; then hands AUD-001 and AUD-004 to implementer for continued work. Auditor receives a new fingerprinted implementation/output/archive and reruns closure checks. This snapshot is **not approved for submission**. No repair round has been consumed by this first partial audit.

### Revision history

| Pass | Cycle / revision | Outcome |
| --- | --- | --- |
| 1 — 2026-10-25 | 1 / 1 | Source-first checklist, full implementation inspection, matching run/snapshot/input fingerprints, 22 rerun tests, fail-closed E2E confirmed, recorded smoke/usage checked, source discrepancy independently investigated, boolean evaluator counterexample reproduced. NEEDS_MANAGER; product unchanged. |
