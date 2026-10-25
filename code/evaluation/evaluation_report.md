# Actual evaluation — ghost-c125c273-c4d9-4fbb-a9b8-bb80a8d06056

Plan revision 3. Findings remain auditor-owned; no acceptance is claimed.

## Public samples: 32 attempted, 2 defensible, 30 unresolved
Unresolved rows are NOT silently counted as correct or fabricated. The metrics below apply only to the stated defensible subset, not all 32 samples.
- Status accuracy: 2/2.
- Exact ordered sequence accuracy: 1/2.
- Whole-row exact accuracy: 1/2.
- Unordered six-field step TP/FP/FN: 5/0/1; precision 1.0, recall 0.8333333333333334, F1 0.9090909090909091.
- Field accuracy: 35/42 (7 × 6 union slots).
- Per-field matches: `{"evidence_id": 5, "operation": 5, "phase": 5, "resource_id": 5, "state": 5, "step_no": 5, "system_id": 5}`.
- Status confusion counts: `[{"count": 1, "expected": "COMPLETE", "predicted": "COMPLETE"}, {"count": 1, "expected": "INCOMPLETE", "predicted": "INCOMPLETE"}]`.
- Evaluator SHA-256: `b82f59576112ec0163d88525630ce7885e278eb36922d52f5e907ef273b0e0f3`.

- Difference case_03, first differing step 3: expected `{"step_no": 3, "phase": "VERIFICATION", "system_id": "analytics_platform", "resource_id": "analytics_9406", "operation": "VERIFY_RECORD_ANONYMIZED", "state": "ANONYMIZED", "evidence_id": "evidence_94"}`, predicted `null`.

### Unresolved sample diagnostics
- case_01: No grounded account resource/state proof; No complete required final-state checks
- case_02: No grounded account resource/state proof; No complete required final-state checks
- case_04: No grounded account resource/state proof; No complete required final-state checks
- case_06: Unresolved resource category/state: account_service/account_006; No grounded account resource/state proof
- case_07: Historical obligation lacks as-of continuity: object_storage/object_19; support_platform/support_001: Shared support-context condition not established; No grounded account resource/state proof
- case_08: Owned business record has no grounded canonical resource: evidence_27:1015; No grounded account resource/state proof
- case_09: No grounded account resource/state proof
- case_10: No grounded account resource/state proof
- case_11: security_service/audit_record_9394: Supplied retention/hold period is not established as active; support_platform/support_864: Shared support-context condition not established
- case_12: Owned business record has no grounded canonical resource: evidence_27:1016; security_service/audit_record_2945: Supplied retention/hold period is not established as active
- case_13: security_service/audit_record_4816: Supplied retention/hold period is not established as active; support_platform/support_4218: Exclusive attachment ownership not established
- case_14: security_service/audit_record_987: Supplied retention/hold period is not established as active
- case_15: security_service/audit_record_1596: Supplied retention/hold period is not established as active
- case_16: security_service/audit_record_9528: Supplied retention/hold period is not established as active
- case_17: Owned evidence has extraction uncertainties: evidence_42:1735; Owned business record has no grounded canonical resource: evidence_27:1017; Historical obligation lacks as-of continuity: identity_service/tombstone_17; security_service/audit_record_1797: Supplied retention/hold period is not established as active
- case_18: No grounded account resource/state proof
- case_19: security_service/audit_record_6793: Supplied retention/hold period is not established as active
- case_20: No grounded account resource/state proof
- case_21: Owned business record has no grounded canonical resource: evidence_27:1018; Required retained record missing; no safe allowed repair: security_service/audit_record_3737; No grounded account resource/state proof; No complete required final-state checks
- case_22: security_service/audit_record_3482: Supplied retention/hold period is not established as active; No grounded account resource/state proof
- case_23: No grounded account resource/state proof
- case_24: Owned business record has no grounded canonical resource: evidence_27:1019
- case_25: Required retained record missing; no safe allowed repair: security_service/audit_record_451; No grounded account resource/state proof; No complete required final-state checks
- case_26: Required retained record missing; no safe allowed repair: security_service/audit_record_5416; No grounded account resource/state proof
- case_27: Required retained record missing; no safe allowed repair: security_service/audit_record_3830; No grounded account resource/state proof
- case_28: Required retained record missing; no safe allowed repair: security_service/audit_record_9265; No grounded account resource/state proof
- case_29: Owned business record has no grounded canonical resource: evidence_27:1020; No grounded account resource/state proof
- case_30: No grounded account resource/state proof
- case_31: Tombstone lacks grounded deleted-account readback: tombstone_440; security_service/audit_record_6909: Supplied retention/hold period is not established as active; No grounded account resource/state proof
- case_32: Tombstone lacks grounded deleted-account readback: tombstone_9178; security_service/audit_record_7068: Supplied retention/hold period is not established as active; No grounded account resource/state proof

## Metric definitions and evaluator repair
Status and exact-sequence denominators are the defensible subset explicitly stated above. Step matching ignores step_no only; all other six fields including evidence must match. Fields align by phase/system/resource/local occurrence, with seven errors for each missing/spurious slot. Sequence and whole-row checks preserve array order and integer types. AUD-004 boolean, float, string, negative, duplicate and gap numbering fixtures now fail through comparator and CLI; valid fixtures, missing/spurious penalties and changed-citation 6/7 penalty pass. Auditor verification remains requested.

## Independent integrated custom cases (source fixtures, not sample labels)
Executed with `python3 -B -m unittest discover -s code/tests -v`; see code/tests/test_audit.py.
Additionally `python3 -B code/evaluation/custom.py` executes CUST-001–003 through real AI intent interpretation, synthetic JSON-file extraction, the same AuditEngine, and strict serialization checks. Its run-local custom-evaluation.json records actual versus expected tuples: three cases passed. Requests are respectively ‘Remove promotional emails only. Keep my account and invoices.’, ‘Please delete my account and personal data.’, and ‘Delete my account, but preserve records lawfully required.’. This is not a public/hidden accuracy claim.
- CUST-001: marketing-only opt-out, with deliberately corrupt deletion evidence. Expected and actual NOT_APPLICABLE/[]; identity/evidence/planning is bypassed. Five real synthetic multilingual/negation intent decisions were also tested separately; these are not hidden-case accuracy.
- CUST-002: present readback at 10:00, file capture 11:00, audit 12:00; ignore embedded 13:00 absence and next-day file despite SUCCESS claim. Expected and actual INCOMPLETE with finding/delete/check. At 14:00 the eligible actual absence gives COMPLETE.
- CUST-003: absent account, required security journal with retention through 2030, stable-reference tombstone with exposed hash. Expected and actual only tombstone redaction repair, then all three verification checks. Clearing direct identifiers yields COMPLETE with stable reference preserved.
- CUST-004: primary absent, failover copy present, wrong-subject decoy. Actual finding cites failover; decoy excluded.
- CUST-005: absent account, present search entry, active connector and restorable retained archive. Actual repairs disable flow, block restore, then delete search; all four final checks remain, no archive deletion.
- Additional: all 15 rule actions/conditional rejection paths, missing retained record, secondary identifier on analytics, 79-artifact structured coverage, and historical object uncertainty/eligible later readback regression pass.

## AUD-002 remains unresolved
The eligible catalog link activity_4007 plus screenshot evidence_46 establish object_19 / delivery_confirmation_19.pdf ownership at February observation. September support_001 in evidence_58 has a distinct filename delivery_address_correction.pdf. Account-only scopes do not erase object obligations; a same-basename record for another subject is not an alias. No expiry, sample exception or automatic perpetual old-state assertion was introduced. Historical obligations without as-of continuity remain explicit diagnostics. This general conservative rule itself still needs auditor review against DEC-002; it does not close the source clarification.

## Target attempt: 518 processed; partial deadline output 407/518
Execution `final-fc426d06-e5d3-4d84-bf9e-0a3710a82c65`; engine-defensible 75; unresolved 443.
Deadline export `code/deadline_export.py` produced root `output.csv` with **407 unique, string-sorted rows**: the 75 guarded decisions plus 332 INCOMPLETE rows where at least one eligible observation violates the resource's required final state. Status counts: 361 INCOMPLETE, 36 COMPLETE, 10 NOT_APPLICABLE. SHA-256 `7a5ee2341d9c6341ccde64f6a28a1f5cae30a080a5d8962f7bb186a8196cebf7`.
The other **111 case IDs are omitted** because no honestly supported status could be established (94 lack grounded account resource/state proof; others have retention, extraction, tombstone, continuity or conflict diagnostics). No status, finding, evidence ID or cost is fabricated. This is a **PARTIAL NON-COMPLIANT submission**, not full 518-row coverage.
Structural validation of all 407 rows passed locally: exact header, unique sorted IDs within the 518 requests, genuine consecutive integer step numbers, allowed phase/operation/state combinations, canonical phase order, valid JSON, finding evidence IDs present and captured at or before each case's `audit_at`, and empty future-work evidence. Rediscovered violation findings were independently serialized; they were not scored against hidden labels.
Hidden target accuracy is unavailable. The normal guarded run still exits 2 and does not write root output; the partial deadline export is a separate, explicitly documented action.

## Artifact coverage
94 manifest entries; 94 extraction successes; 0 explicit failures.

## Failures and improvements
Fixed type-insensitive evaluator equality; preserved strict input, SQL and atomic-write gates. Added actual adapters, scoped facts, trace correlation, deterministic policies/plans, model interpretation and per-case diagnostics. Business interpretation and resource-link completeness remain audit concerns: for example support_001 currently yields separate message/attachment interpretations rather than a fully reconciled container record, and analytics_9406 has no established subject link in the current graph. These are not declared dataset defects or accepted label exceptions. ‘Defensible’ means passed the current engine guards, not independently verified. Business OCR/model uncertainties and missing retention/canonical-resource/as-of support remain blockers instead of fabricated absent/COMPLETE states. Passing fixtures does not resolve every real source ambiguity. Candidate packaging is not final acceptance.
