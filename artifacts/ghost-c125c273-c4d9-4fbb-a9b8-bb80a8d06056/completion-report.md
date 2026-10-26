# Implementation completion pass

Date: 2026-10-25T20:22:40.631790+00:00

Checkout: `/home/pierce/Documents/Projects/Challenges/ghost-data-sol-fresh`
Run ID: `ghost-c125c273-c4d9-4fbb-a9b8-bb80a8d06056`

**Status: not complete.** The code changes and reproducibility checks below are finished, but a conforming 518-row prediction file is still blocked. No evidence, prediction, or test success was invented to remove that blocker.

## Changes made

- Added explicit offline execution to the main pipeline, preprocessing, public-sample evaluation, and custom evaluation. It accepts only matching, revalidated current-run model responses; cache misses remain errors and never invoke a provider.
- Fixed JSON updated_at handling so a future-dated treatment cannot leak into an earlier audit. Nested snapshot timestamps now compare timezone-aware instants rather than raw strings.
- Added parsing for explicitly supplied human-readable retention deadlines. Missing periods remain missing; date-only deadlines are treated conservatively without inventing a time or extending retention.
- Fixed PDF document-container reconciliation: a sole body and sole attachment metadata record are joined only when their support-ticket keys match and the document explicitly identifies attachment properties/upload history. The actual support_001 document is now an attachment with its body identity and cross-page provenance. Different tickets stay separate.
- Rechecked serialized evidence citations against source fact IDs, resource/state, closed scope and cutoff, instead of checking only that the generated decision contains a proof key.
- Fixed sample evaluation coverage: unresolved cases now count as missing predictions in all-32 denominators instead of being omitted from accuracy. Existing strict integer validation is retained.
- Incomplete runs explicitly warn if they preserve an older root output.csv and record that file's hash. The historical submission remains unchanged.
- Package replay now uses an independent cache copy and offline mode. It no longer shares mutable original run pointers or starts model jobs during archive validation.
- Updated README, evaluation/usage reports and the implementer handoff. Manager/auditor memory and the original participant dataset were not edited.

## Verification actually completed

| Check | Result |
| --- | --- |
| Unit/regression tests | 56/56 passed; original baseline was 49/49 |
| Input/SQL gate | Passed |
| Integrated custom cases | 3/3 passed using validated earlier AI responses, synthetic extraction and the actual audit/serialization pipeline |
| Evidence preprocessing | 94/94 artifacts processed; 3322 facts; no parser failures; interpretation uncertainties are still explicit |
| Public samples | 32 attempted; 2 passed the current decision guards; 30 unresolved |
| Status accuracy, all public samples | 2/32 |
| Exact whole-row/sequence accuracy | 1/32 |
| Step TP / FP / FN | 5 / 0 / 188 |
| Field matches | 35/1351 |
| Target pipeline | 518 attempted; 75 passed current guards; 443 unresolved; exit 2 |
| Archive | 29 members; extracted tests/input gate passed and cached target replay reproduced the guarded subset |
| Original run pointers | Unchanged by package replay, independently checked |
| Participant input hashes | Match the original full-run inputs |
| Original submitted output.csv | Preserved byte-for-byte; historical 407-row file, not a finalized result from this pass |
| New application model jobs | 0; job-record count stayed at 111 |

Test logs and exact command results: `artifacts/ghost-c125c273-c4d9-4fbb-a9b8-bb80a8d06056/completion-checks.json`.
Final checked execution: `final-ca71ebf0-cc3d-4d91-9a69-c6feeb7b0b35`.
Archive SHA-256: `e22fb8d29b170127ced43866673c9a6b998501337d37bd9b7f037f0c53868050`.

Exit 2 is an explicit unresolved-case result, not a passing full-dataset run. Cached replay does not establish cold-provider behavior, actual billing, hidden-grader accuracy or an independent audit. The model work used to create these caches still has its original usage; zero new jobs is not a claim that development cost was zero.

## What prevents completion

The main overlapping target diagnostics include 343 cases without grounded account resource/state proof and 208 without an established required retention/hold period. They are diagnostics, not proof that all these cases are dataset defects. Some remaining failures may still be extraction/linking limitations.

Concrete unresolved examples:

1. **Deleted account linkage:** the current graph has no subject-to-resource link for sample case_01's expected account_001. The deletion activity mentions that resource but does not identify its subject; the closed SQL snapshot can establish absence of a known resource but does not supply the missing ownership mapping. Numeric user/account suffixes or the sample label must not become inference rules.
2. **Anonymous analytics ownership:** sample case_03 expects a check for analytics_9406, but its eligible readback has null identity fields and the current graph has no ownership link. An anonymization activity claiming success does not itself supply the missing subject identity.
3. **Retention prerequisites:** many security readbacks identify a retained-type record but omit a retention deadline or an eligible source establishing the supplied condition. The new date parser fixes explicit document dates; it cannot supply a period that is absent.
4. **Object-scope dispute:** object_19 has an eligible ownership link and an older presence observation; the sample omits it without an established later removal, alias or general scope explanation. The historical continuity diagnostic remains open. The support PDF container fix does not settle this separate dispute.

The user confirmed that no additional organizer information was provided for the mapping and retention questions. A fully conforming result still needs source-backed mappings/conditions or an explicitly established general interpretation of those requirements. This pass does not authorize case exceptions, implicit deletion, guessed ownership, arbitrary retention defaults or fabricated completion.

## Reproduce without new model calls

```text
python3 -B -m unittest discover -s code/tests -v
python3 -B code/main.py --check-inputs
python3 -B code/evaluation/custom.py --offline
python3 -B code/evaluation/main.py --offline
python3 -B code/main.py --offline
python3 -B code/evaluation/report.py
python3 -B code/package.py
```

The sample and target commands currently return 2 because required cases are unresolved. Offline inference needs the existing validated run-local responses; they are intentionally not bundled into code.zip. A cold run requires the documented external tools and authorized model connection. Pricing/authentication uncertainty remains disclosed separately from the technical evidence blockers.

The updated archive is a tested **candidate**, not a completed or auditor-approved submission. No auditor finding was closed by this implementation pass. Earlier submitted source/reports/output/archive and memory are preserved in `artifacts/ghost-c125c273-c4d9-4fbb-a9b8-bb80a8d06056/submitted-baseline-20261025T195754Z.zip`.
