# Actual evaluation — ghost-c125c273-c4d9-4fbb-a9b8-bb80a8d06056

Plan revision 3. Findings remain auditor-owned; no acceptance is claimed.

## Public samples: 32 attempted, 2 defensible, 30 unresolved
All public cases are included in the metric denominators. Unresolved rows count as incorrect/missing predictions; no answer is fabricated to fill them.
- Status accuracy: 2/32.
- Exact ordered sequence accuracy: 1/32.
- Whole-row exact accuracy: 1/32.
- Unordered six-field step TP/FP/FN: 5/0/188; precision 1.0, recall 0.025906735751295335, F1 0.050505050505050504.
- Field accuracy: 35/1351 (7 × 193 union slots).
- Per-field matches: `{"evidence_id": 5, "operation": 5, "phase": 5, "resource_id": 5, "state": 5, "step_no": 5, "system_id": 5}`.
- Status confusion counts: `[{"count": 1, "expected": "COMPLETE", "predicted": "COMPLETE"}, {"count": 9, "expected": "COMPLETE", "predicted": "UNRESOLVED"}, {"count": 1, "expected": "INCOMPLETE", "predicted": "INCOMPLETE"}, {"count": 21, "expected": "INCOMPLETE", "predicted": "UNRESOLVED"}]`.
- Evaluator SHA-256: `9c277c24ab508a79da0a5f851f043fc05e52bc06ac546f50fb9763ff5328cfee`.

- Difference case_01, first differing step 1: expected `{"evidence_id": "evidence_54", "operation": "VERIFY_RECORD_ABSENT", "phase": "VERIFICATION", "resource_id": "account_001", "state": "ABSENT", "step_no": 1, "system_id": "account_service"}`, predicted `null`.
- Difference case_02, first differing step 1: expected `{"evidence_id": "evidence_54", "operation": "VERIFY_RECORD_ABSENT", "phase": "VERIFICATION", "resource_id": "account_002", "state": "ABSENT", "step_no": 1, "system_id": "account_service"}`, predicted `null`.
- Difference case_03, first differing step 3: expected `{"step_no": 3, "phase": "VERIFICATION", "system_id": "analytics_platform", "resource_id": "analytics_9406", "operation": "VERIFY_RECORD_ANONYMIZED", "state": "ANONYMIZED", "evidence_id": "evidence_94"}`, predicted `null`.
- Difference case_04, first differing step 1: expected `{"evidence_id": "evidence_54", "operation": "VERIFY_RECORD_ABSENT", "phase": "VERIFICATION", "resource_id": "account_004", "state": "ABSENT", "step_no": 1, "system_id": "account_service"}`, predicted `null`.
- Difference case_06, first differing step 1: expected `{"evidence_id": "evidence_57", "operation": "REPORT_REMAINING_RECORD", "phase": "FINDING", "resource_id": "search_001", "state": "PRESENT", "step_no": 1, "system_id": "search_service"}`, predicted `null`.
- Difference case_07, first differing step 1: expected `{"evidence_id": "evidence_58", "operation": "REPORT_REMAINING_RECORD", "phase": "FINDING", "resource_id": "support_001", "state": "PRESENT", "step_no": 1, "system_id": "support_platform"}`, predicted `null`.
- Difference case_08, first differing step 1: expected `{"evidence_id": "evidence_59", "operation": "REPORT_REMAINING_RECORD", "phase": "FINDING", "resource_id": "export_001", "state": "PRESENT", "step_no": 1, "system_id": "export_service"}`, predicted `null`.
- Difference case_09, first differing step 1: expected `{"step_no": 1, "phase": "FINDING", "system_id": "backup_service", "resource_id": "backup_4978", "operation": "REPORT_RESTORE_RISK", "state": "ACTIVE", "evidence_id": "evidence_93"}`, predicted `null`.
- Difference case_10, first differing step 1: expected `{"evidence_id": "evidence_61", "operation": "REPORT_REMAINING_RECORD", "phase": "FINDING", "resource_id": "support_002", "state": "PRESENT", "step_no": 1, "system_id": "support_platform"}`, predicted `null`.
- Difference case_11, first differing step 1: expected `{"step_no": 1, "phase": "FINDING", "system_id": "search_service", "resource_id": "search_052", "operation": "REPORT_REMAINING_RECORD", "state": "PRESENT", "evidence_id": "evidence_03"}`, predicted `null`.
- Difference case_12, first differing step 1: expected `{"step_no": 1, "phase": "FINDING", "system_id": "analytics_platform", "resource_id": "analytics_9914", "operation": "REPORT_REMAINING_RECORD", "state": "PRESENT", "evidence_id": "evidence_01"}`, predicted `null`.
- Difference case_13, first differing step 1: expected `{"step_no": 1, "phase": "FINDING", "system_id": "search_service", "resource_id": "search_1308", "operation": "REPORT_REMAINING_RECORD", "state": "PRESENT", "evidence_id": "evidence_03"}`, predicted `null`.
- Difference case_14, first differing step 1: expected `{"step_no": 1, "phase": "FINDING", "system_id": "backup_service", "resource_id": "backup_3870", "operation": "REPORT_RESTORE_RISK", "state": "ACTIVE", "evidence_id": "evidence_03"}`, predicted `null`.
- Difference case_15, first differing step 1: expected `{"step_no": 1, "phase": "FINDING", "system_id": "integration_service", "resource_id": "data_flow_9846", "operation": "REPORT_ACTIVE_DATA_FLOW", "state": "ACTIVE", "evidence_id": "evidence_01"}`, predicted `null`.
- Difference case_16, first differing step 1: expected `{"step_no": 1, "phase": "FINDING", "system_id": "account_service", "resource_id": "account_994", "operation": "REPORT_REMAINING_RECORD", "state": "PRESENT", "evidence_id": "evidence_05"}`, predicted `null`.
- Difference case_17, first differing step 1: expected `{"step_no": 1, "phase": "FINDING", "system_id": "backup_service", "resource_id": "backup_3245", "operation": "REPORT_RESTORE_RISK", "state": "ACTIVE", "evidence_id": "evidence_01"}`, predicted `null`.
- Difference case_18, first differing step 1: expected `{"step_no": 1, "phase": "FINDING", "system_id": "search_service", "resource_id": "search_4013", "operation": "REPORT_REMAINING_RECORD", "state": "PRESENT", "evidence_id": "evidence_94"}`, predicted `null`.
- Difference case_19, first differing step 1: expected `{"step_no": 1, "phase": "FINDING", "system_id": "search_service", "resource_id": "search_6083", "operation": "REPORT_REMAINING_RECORD", "state": "PRESENT", "evidence_id": "evidence_01"}`, predicted `null`.
- Difference case_20, first differing step 1: expected `{"step_no": 1, "phase": "FINDING", "system_id": "search_service", "resource_id": "search_4262", "operation": "REPORT_REMAINING_RECORD", "state": "PRESENT", "evidence_id": "evidence_94"}`, predicted `null`.
- Difference case_21, first differing step 1: expected `{"step_no": 1, "phase": "VERIFICATION", "system_id": "account_service", "resource_id": "account_6440", "operation": "VERIFY_RECORD_ABSENT", "state": "ABSENT", "evidence_id": "evidence_92"}`, predicted `null`.
- Difference case_22, first differing step 1: expected `{"step_no": 1, "phase": "FINDING", "system_id": "search_service", "resource_id": "search_8911", "operation": "REPORT_REMAINING_RECORD", "state": "PRESENT", "evidence_id": "evidence_05"}`, predicted `null`.
- Difference case_23, first differing step 1: expected `{"step_no": 1, "phase": "FINDING", "system_id": "export_service", "resource_id": "export_7364", "operation": "REPORT_REMAINING_RECORD", "state": "PRESENT", "evidence_id": "evidence_92"}`, predicted `null`.
- Difference case_24, first differing step 1: expected `{"step_no": 1, "phase": "FINDING", "system_id": "account_service", "resource_id": "account_5334", "operation": "REPORT_REMAINING_RECORD", "state": "PRESENT", "evidence_id": "evidence_92"}`, predicted `null`.
- Difference case_25, first differing step 1: expected `{"step_no": 1, "phase": "VERIFICATION", "system_id": "account_service", "resource_id": "account_3136", "operation": "VERIFY_RECORD_ABSENT", "state": "ABSENT", "evidence_id": "evidence_92"}`, predicted `null`.
- Difference case_26, first differing step 1: expected `{"step_no": 1, "phase": "VERIFICATION", "system_id": "account_service", "resource_id": "account_5684", "operation": "VERIFY_RECORD_ABSENT", "state": "ABSENT", "evidence_id": "evidence_92"}`, predicted `null`.
- Difference case_27, first differing step 1: expected `{"step_no": 1, "phase": "VERIFICATION", "system_id": "account_service", "resource_id": "account_3866", "operation": "VERIFY_RECORD_ABSENT", "state": "ABSENT", "evidence_id": "evidence_92"}`, predicted `null`.
- Difference case_28, first differing step 1: expected `{"step_no": 1, "phase": "VERIFICATION", "system_id": "account_service", "resource_id": "account_5482", "operation": "VERIFY_RECORD_ABSENT", "state": "ABSENT", "evidence_id": "evidence_92"}`, predicted `null`.
- Difference case_29, first differing step 1: expected `{"step_no": 1, "phase": "FINDING", "system_id": "search_service", "resource_id": "search_1993", "operation": "REPORT_REMAINING_RECORD", "state": "PRESENT", "evidence_id": "evidence_92"}`, predicted `null`.
- Difference case_30, first differing step 1: expected `{"step_no": 1, "phase": "FINDING", "system_id": "search_service", "resource_id": "search_9359", "operation": "REPORT_REMAINING_RECORD", "state": "PRESENT", "evidence_id": "evidence_92"}`, predicted `null`.
- Difference case_31, first differing step 1: expected `{"step_no": 1, "phase": "VERIFICATION", "system_id": "account_service", "resource_id": "account_4857", "operation": "VERIFY_RECORD_ABSENT", "state": "ABSENT", "evidence_id": "evidence_51"}`, predicted `null`.
- Difference case_32, first differing step 1: expected `{"step_no": 1, "phase": "FINDING", "system_id": "identity_service", "resource_id": "tombstone_9178", "operation": "REPORT_EXPOSED_PII", "state": "PRESENT", "evidence_id": "evidence_51"}`, predicted `null`.

### Unresolved sample diagnostics
- case_01: No grounded account resource/state proof; No complete required final-state checks
- case_02: No grounded account resource/state proof; No complete required final-state checks
- case_04: No grounded account resource/state proof; No complete required final-state checks
- case_06: Unresolved resource category/state: account_service/account_006; No grounded account resource/state proof
- case_07: Historical obligation lacks as-of continuity: object_storage/object_19; No grounded account resource/state proof
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
Status and exact-sequence denominators include every public sample, including unresolved cases. Step matching ignores step_no only; all other six fields including evidence must match. Fields align by phase/system/resource/local occurrence, with seven errors for each missing/spurious slot. Missing cases have no predicted steps and their expected steps contribute false negatives. Sequence and whole-row checks preserve array order and integer types. AUD-004 boolean, float, string, negative, duplicate and gap numbering fixtures now fail through comparator and CLI; valid fixtures, missing/spurious penalties and changed-citation 6/7 penalty pass. Auditor verification remains requested.

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

## Target attempt: 518 processed; 75 defensible; 443 unresolved
Execution `final-ca71ebf0-cc3d-4d91-9a69-c6feeb7b0b35`; output hash `None`; finalized=False.
Hidden target accuracy is unavailable. Root output is written only if every row is defensible; a run-local defensible subset is NOT a submission.
An older root output.csv was preserved with SHA-256 `7a5ee2341d9c6341ccde64f6a28a1f5cae30a080a5d8962f7bb186a8196cebf7`. It is NOT this execution's finalized output.

## Artifact coverage
94 manifest entries; 94 extraction successes; 0 explicit failures.

## Failures and improvements
Fixed type-insensitive evaluator equality; preserved strict input, SQL and atomic-write gates. Added actual adapters, scoped facts, trace correlation, deterministic policies/plans, model interpretation and per-case diagnostics. Post-submission repairs include JSON updated_at cutoffs, timezone-aware snapshot comparison, explicit human-readable retention deadlines, source-backed serialization proof checks, full-sample metric denominators and no-provider offline replay. PDF attachment properties now reconcile a sole document body and sole upload record only when their support ticket keys match; differing tickets remain distinct. Resource-link completeness remains an audit concern: analytics_9406 has no established subject link in the current graph. These are not declared dataset defects or accepted label exceptions. ‘Defensible’ means passed the current engine guards, not independently verified. Business OCR/model uncertainties and missing retention/canonical-resource/as-of support remain blockers instead of fabricated absent/COMPLETE states. Passing fixtures does not resolve every real source ambiguity. Candidate packaging is not final acceptance.
