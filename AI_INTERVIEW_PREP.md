# AI Judge Interview Prep — Ghost Data Still Exists

Use this as a speaking outline, not a script. Be explicit about what is proven,
what is partial, and what you would do next.

## 1. 30-second pitch

> I built a fail-closed deletion-audit pipeline. It first decides whether the
> request actually authorizes deletion, then reconstructs the person's current
> and historical identities, extracts all 94 evidence artifacts into immutable
> time-scoped facts, links those facts to resources through identifiers and
> business keys, and applies the 15 supplied policy rules at `audit_at`.
> The model only interprets multilingual requests and business documents; a
> deterministic engine makes the deletion decision and emits findings, ordered
> remediation, and verification. Missing or conflicting proof stays unresolved
> instead of becoming a guessed COMPLETE. Under the deadline I submitted 407
> evidence-backed rows and deliberately omitted 111 I could not defend.

## 2. Architecture in one picture

```text
CSV inputs
  -> strict validation (headers, timestamps, IDs, SQL safety)
  -> intent gate: LLM returns {authorizes_deletion, quote, ambiguity}
  -> identity reconstruction: current snapshot + audit history, <= audit_at
  -> 94 evidence artifacts -> adapters
       JSON / SQL / logs / text / PDF / images
  -> immutable facts: provenance, timestamps, scope, copy, subject keys
  -> eligible-fact linking: aliases -> resource IDs -> business keys
  -> per-copy state reduction (latest valid observation at/before audit_at)
  -> 15 policy rules -> expected final state per resource
  -> findings + risk-first remediation + verification checks
  -> strict serializer + evidence/proof gate -> output.csv
```

Key files:

| Area | File |
|---|---|
| Orchestration | `code/main.py` |
| Intent / evidence model calls | `code/ai.py`, `code/transport.py`, `code/runtime/*.md` |
| Extraction | `code/extract.py`, `code/facts.py`, `code/sql_snapshot.py` |
| Identity / policy / planning | `code/audit.py` |
| Output contract | `code/steps.py` |
| Evaluation | `code/evaluation/main.py`, `code/evaluation/custom.py` |
| Reports | `code/evaluation/evaluation_report.md`, `usage_report.md` |

## 3. The design decisions that matter

### Model output is interpretation, never a verdict

- The intent model returns a boolean, a literal supporting quote, and an
  ambiguity field. It never sees or assigns a deletion status.
- The evidence model extracts visible records and uncertainty, not policy
  conclusions. It cannot say “deletion is complete.”
- The deterministic engine applies `deletion_rules.csv`. That separation is the
  main defense against hallucinated compliance.

### Claims are not proof

- `reported_status` and `system_activity.csv` results are treated as claims.
- A workflow saying SUCCESS does not prove a record is absent.
- A real state needs an eligible readback, snapshot, scoped inventory, or other
  direct observation. Missing data is unknown, not absence.

### Everything is scoped by time

Every fact carries `observed_at`, `captured_at`, and `snapshot_at`. A fact is
eligible only if all three are at or before the case's `audit_at`. This prevents
later evidence from changing an earlier answer.

### Identity is reconstructed, not looked up once

- Current identity snapshot plus `user_audit_log.csv`.
- Normalize email/hash case-insensitively, phones by formatting, exact user IDs.
- Only aliases observable at or before `audit_at` are eligible.
- Shared phone/email/hash matches require independent ownership corroboration.
- Ambiguous request identity fails that case instead of assigning the wrong person.
- Names are not used as matching keys because they collide.

### Linking is a fixed point, not a guess

Starting from the subject's exact aliases:

1. Link explicit resource IDs.
2. Link business keys only when an eligible catalog/link proves the mapping.
3. For a business record with a unique business key, bind it to that resource.
4. Propagate through resource references until no new links appear.

If a business document has only a filename and no canonical resource ID, it
stays unbound. That is deliberate: do not invent `object_19` or an account ID
from a filename or a case number.

### State reduction is per copy

- Group observations by resource and copy (`primary`, regional, failover,
  service, archive, etc.).
- In each copy, take the latest eligible observation.
- Conflicting observations at the same time are unresolved, not “latest wins.”
- A closed SQL scope can prove absence only for the copies it actually covers;
  it is not global proof.
- Extraction failure is unknown, never absence.

### Policy: 15 categories, expected final states

Examples:

| Category | Required treatment |
|---|---|
| User profile, search entry, export, cache, marketing profile | Delete |
| Support message with shared context | Redact |
| Support attachment exclusive to subject | Delete |
| Analytics/telemetry still attributable | Anonymize |
| Security audit log within retention | Retain |
| Active legal hold | Retain |
| Backup with restorable data | Keep but block restore |
| Deleted-account tombstone | Redact direct identifiers, preserve stable `user_id` |

The account tombstone is a key nuance: preserve the stable internal reference
needed by retained records, but remove name, email, phone, email hash, and other
direct identifiers. Verify both the absent account profile and the redacted
tombstone.

### Remediation is risk-first

Order:

1. Disable an active sync/export/indexing flow.
2. Block an unsafe backup restore.
3. Delete, redact, or anonymize dependent records.
4. Verify the final state of every repaired resource or process.

This prevents a repair from being undone by an active copy path. Future work
has an empty `evidence_id`; findings cite real eligible evidence.

### Fail-closed output gate

`steps.py` validates the exact seven fields, genuine consecutive integers,
allowed phase/operation/state combinations, phase order, evidence support, and
repair-to-check coverage. `main.py` writes root `output.csv` atomically only if
there are no unresolved cases. Otherwise it exits 2 and keeps a non-submission
subset plus diagnostics.

## 4. Actual numbers to remember

| Metric | Result |
|---|---|
| Evaluation requests | 518 |
| Evidence artifacts | 94 |
| Extracted facts | 3,323 |
| Parser/extraction entries with errors | 0 |
| Public samples attempted | 32 |
| Sample rows passing engine guards | 2 |
| Sample status accuracy on that subset | 2/2 |
| Sample exact sequence / whole row | 1/2 |
| Sample step F1 on that subset | 0.909 |
| Target cases attempted | 518 |
| Target rows passing full engine guards | 75 |
| Target unresolved at engine gate | 443 |
| Deadline root output rows | **407 / 518** |
| Omitted, unsupported | **111** |
| Output status mix | 361 INCOMPLETE, 36 COMPLETE, 10 NOT_APPLICABLE |
| Unit tests | 49/49 pass |
| Custom end-to-end cases | 3/3 pass |
| Final model dependency records | 37 |
| Input / output tokens (attempt workload) | 96,519 / 28,210 |
| Reasoning counter (separate) | 1,367 |
| Hypothetical API-reference cost | $0.475–$0.489, not billed |

Sample metrics are only for the 2 defensible rows, not all 32. Do not present
them as full-sample accuracy.

## 5. Why the submission is partial — answer this directly

> The normal pipeline is fail-closed. It produced 75 rows that passed every
> guard, but 443 cases still had essential unknowns. With the deadline, I added
> a separate exporter, not a looser engine. It kept the 75 guarded decisions and
> added 332 INCOMPLETE rows only where an eligible, uncontested observation
> proved at least one policy violation. That gives a certain status even when
> the full plan is not exhaustive. I omitted the other 111 because I could not
> establish a supported status without guessing.

Exact omission reasons (overlapping, not additive):

- 343 engine diagnostics: no grounded account resource/state proof.
- 208 retention/hold period not established as active.
- 33 no complete required final-state checks.
- 19 shared-support-context or exclusive-attachment conditions.
- 12 extraction uncertainties.
- 8 conflicting same-copy observations.
- 8 tombstones without a grounded deleted-account readback.
- 2 historical obligations without as-of continuity.
- 2 uncorroborated visual keys.
- 2 unknown observed treatments.

Do not say “the dataset was wrong.” Say: “These were unresolved source/linkage
or proof gaps in my implementation; they may also reflect genuinely incomplete
evidence, but I did not declare either.”

## 6. Evaluation story

### What was measured

- Public sample labels compared only after the actual pipeline ran.
- Status, exact ordered sequence, whole-row, unordered step TP/FP/FN, field-level
  accuracy, confusion matrix.
- Three custom cases through real intent -> extraction -> same audit engine ->
  serialization:
  - marketing-only request -> NOT_APPLICABLE;
  - mixed evidence with a future observation -> ignore it, INCOMPLETE;
  - tombstone plus retained journal -> redact tombstone, preserve journal.
- Additional unit cases for all 15 rules, replicas/decoys, missing retained
  records, shared identifiers, temporal cutoffs, and tombstones.

### Evaluator bug worth telling

> The first comparator used Python equality, so `True == 1` let a boolean
> `step_no` pass as integer 1. I fixed it by requiring `type(step_no) is int`,
> validating present steps on both expected and predicted sides, and adding a
> matrix for booleans, floats, numeric strings, negatives, gaps, and duplicates.
> This was a correctness bug in evaluation, not in the policy engine.

This is a good “found a failure and improved it” answer.

## 7. Likely questions and strong answers

### “Walk me through the pipeline.”

Use the 30-second pitch, then expand in this order: intent -> identity -> facts ->
linking -> state reduction -> policy -> planning -> output gate. Keep each part
to one sentence unless asked for detail.

### “Why use an LLM at all?”

> The request text is multilingual and free-form, and business evidence includes
> PDFs and screenshots. An LLM is useful for semantic interpretation. But it is
> constrained to structured extraction with literal quotes and uncertainty, and
> it never decides deletion status. The deterministic policy engine does that.

### “How do you prevent hallucination?”

> Four layers: strict JSON schemas and literal-quote support; an empty
> interpretation is not proof of absence; evidence content is marked untrusted
> and the runtime has no tools; and the model never emits the final status.
> The policy engine only uses eligible observations with provenance and fails
> closed on conflicts or missing proof.

### “How do you stop prompt injection from a PDF or log?”

> The evidence prompt says the attachment and text are untrusted sources, not
> instructions. The model has no tools and one step. Its output must match a
> fixed record schema. Injected text can at most become an extracted record; it
> cannot call anything or set a deletion verdict. I also validate the effective
> agent configuration and reject ambient AGENTS.md, plugins, MCP, skills, or
> tools before the call.

### “How do you resolve historical emails and phones?”

> I build aliases from the current identity snapshot and from audit-log
> old/new values, but only rows at or before `audit_at`. Emails and hashes are
> case-folded, phones are formatting-normalized, user IDs are exact. The request
> email must resolve to exactly one user. Historical aliases then link older
> evidence. Names are excluded because they are not unique.

### “How do you know a record is absent?”

> Only from an eligible observation that explicitly establishes absence: a
> readback with NOT_FOUND/404/zero rows, or a closed scope that explicitly
> covers the resource and copy. Missing rows, a failed parse, an empty search,
> or a healthy UI badge are not absence. Those stay unknown.

### “How do you handle replicas and conflicts?”

> State is reduced per copy, so a primary being absent does not hide a regional
> or failover copy. Each copy uses its latest eligible observation. Two
> conflicting observations at the same timestamp are an unresolved diagnostic,
> not a coin flip. Any copy still present becomes a finding.

### “How do you handle account tombstones?”

> The rule is REDACT, not DELETE. The tombstone must show the account is deleted
> and retain a stable `user_id`/subject reference. I require a grounded deleted-
> account readback, then verify direct identifiers are removed and the stable
> reference remains. Deleting the tombstone would break retained-record
> references, so that would be wrong.

### “How do you handle backups and sync?”

> A backup is retained, not deleted; the required state is restore-blocked.
> An active connector or sync is a finding and must be disabled before dependent
> records are changed. Verification checks the flow is disabled or the restore
> is blocked. That ordering prevents remediation from being undone.

### “What about support conversations and attachments?”

> A conversation containing shared customer/agent/order context is redacted,
> not deleted. An attachment is deleted only when it belongs exclusively to the
> subject. If ownership is shared or unproven, it is a diagnostic rather than a
> destructive action. This is a policy distinction, not a model guess.

### “How do you handle retention and legal holds?”

> Security audit records within a supplied retention period and active legal
> holds are retained. If the period or hold is not established, I do not delete
> and I do not claim complete; the case stays unresolved. Verification checks the
> required record is present.

### “Why did only 2 of 32 samples pass?”

> The sample subset is tiny and the engine is intentionally conservative. Thirty
> cases were unresolved, not scored as wrong. The main gaps were grounded account
> readbacks, retention evidence, support container reconciliation, and one
> anonymous analytics resource with no established subject link. I chose not to
> loosen the gate just to raise the sample score.

### “Why not fill the 111 missing rows with the reported status?”

> Because `reported_status` is exactly the claim the challenge asks me to audit.
> Copying COMPLETE would recreate the failure mode the task is about: a workflow
> says complete while data remains. I would rather submit a visibly partial file
> than a fabricated complete one.

### “Isn't a partial file worse for scoring?”

> It may be worse for row coverage, but it is the honest engineering choice for
> a deletion audit. A false COMPLETE can hide retained personal data and unsafe
> restore paths. I documented the exact gap and the 407 rows I could support.
> With more time I would close the linkage/coverage gaps, not guess statuses.

### “Did you hardcode sample answers?”

> No. The sample labels are read only by the evaluator after predictions are
> generated. The audit engine never reads `sample_output.csv`. I preserved the
> original dataset hash and added only synthetic custom fixtures in tests.

### “How did you evaluate without hidden labels?”

> Public samples for exact schema/sequence metrics, custom cases for known
> behaviors, unit tests for policy branches, and internal consistency checks for
> all 407 output rows. I did not claim hidden-target accuracy.

### “What was the hardest technical problem?”

> Evidence linkage. The manifest does not say which case a file belongs to, so
> the same email or phone can appear in decoys, shared support contexts, or
> historical records. The hard part was building a conservative link graph:
> exact aliases, explicit resource pointers, unique business keys, and no
> over-linking from a filename or a shared identifier. That is also where most
> of the unresolved cases came from.

### “What went wrong?”

> Three things: the evaluator's boolean/integer bug; provider quota failures
> during preprocessing, which I handled with a circuit breaker and validated
> response cache; and insufficient evidence-link coverage, especially account
> readbacks and support/analytics containers. The deadline forced me to stop
> improving coverage and ship only supported rows.

### “How did you handle model failures and cost?”

> Each interpretation is a fresh, tool-denied session with a bounded timeout and
> at most three attempts. Validated responses are cached by prompt/config/model/
> media hashes. A quota error opens a circuit breaker for that execution instead
> of burning more calls. I recorded 37 dependency records for the final attempt:
> 96,519 input and 28,210 output tokens. The $0.475–$0.489 figure is explicitly a
> hypothetical API-equivalent estimate; the actual subscription charge was not
> measurable.

### “How would you scale this?”

> Preprocess each artifact once, cache by content hash, batch intent calls, and
> parallelize independent evidence extraction with a strict concurrency and cost
> budget. The policy engine is deterministic and cheap. The expensive part is
> document interpretation, so incremental extraction and content-addressed
> caching are the main levers.

### “What would you do with another week?”

> In order: (1) improve grounded account readback and SQL copy coverage;
> (2) reconcile support documents at the container level instead of separate
> message/attachment facts; (3) establish anonymous analytics subject links;
> (4) make retention/hold evidence corroborated; (5) rerun all 32 samples and
> require full acceptance before claiming 518-row readiness. I would not relax
> the fail-closed gate.

### “What is the business value?”

> It turns a deletion workflow's claim into an evidence-backed audit: what
> remains, which copy or process can recreate it, what order to fix it in, and
> what must be verified afterward. That is directly useful for privacy
> compliance, incident response, and avoiding false “deletion complete” reports.

## 8. Honest limitations to state before being asked

- Root output is **407/518**, not complete; 111 IDs omitted.
- Only 2 of 32 public samples passed the full gate; metrics are subset-only.
- 332 deadline rows are status-defensible INCOMPLETE, not guaranteed exhaustive
  remediation plans.
- AUD-002 historical `object_19` conflict remains unresolved; no sample-specific
  exception or TTL was added.
- Model interpretation still has per-record uncertainties; parsing success is
  not state correctness.
- Actual ChatGPT subscription cost is unmeasured; API figures are hypothetical.
- No cold-provider replay or independent semantic audit was completed.

## 9. Things not to say

- “The output is complete.” It is not.
- “The model decides deletion status.” It does not.
- “The sample accuracy is 2/32 correct.” Thirty were unresolved, not scored wrong;
  and the two metrics are subset-only.
- “The dataset was wrong.” Say “my pipeline could not establish the link/state.”
- “I used the reported status to fill gaps.” You did not, and should not.
- “The API cost was $0.48.” It is a hypothetical reference, not a charge.
- “The sample answers are used by the engine.” They are evaluator-only.

## 10. 60-second closing

> The strongest part of this solution is the separation of concerns: AI for
> language and document interpretation, deterministic code for identity, policy,
> ordering, and proof. The weakest part is evidence coverage: I could not ground
> enough account, retention, and container links to defend all 518 cases, so I
> submitted 407 supported rows and documented the 111 omissions. Given more time,
> I would improve linkage and rerun the full sample gate before claiming
> completeness. I would keep the fail-closed behavior, because a false COMPLETE
> in a deletion audit is worse than an explicit unknown.

## 11. Quick file map for follow-up questions

- Architecture / setup: `README.md`
- Actual evaluation and failure analysis: `code/evaluation/evaluation_report.md`
- Usage and billing treatment: `code/evaluation/usage_report.md`
- Evidence and audit rules: `code/audit.py`, `code/extract.py`, `code/facts.py`
- Prompts: `code/runtime/intent.md`, `code/runtime/evidence.md`
- Runtime isolation: `code/transport.py`, `code/runtime/opencode.json`
- Tests: `code/tests/`
- Deadline export and diagnostics:
  `artifacts/ghost-c125c273-c4d9-4fbb-a9b8-bb80a8d06056/deadline-export.json`
