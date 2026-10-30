# HackerRank Orchestrate - October 2026

## Ghost Data Still Exists

Build an AI agent that audits whether a user's personal data was actually deleted.

A deletion workflow may report **Complete** while data still exists in databases, logs, support attachments, exports, search indexes, archives, or backups. Sync and restore processes may also bring deleted data back.

For each request, the agent must first determine whether deletion was actually requested. It then returns `COMPLETE`, `INCOMPLETE`, or `NOT_APPLICABLE`, reports any remaining data or recreation risk, and produces the ordered remediation and verification steps required to finish an authorized deletion safely.

Read [`problem_statement.md`](./problem_statement.md) for the complete challenge contract.

## Current implementation: audit candidate, not submission-ready

### Post-submission completion work

The submitted source, reports, memories, output and package were preserved in a
timestamped `artifacts/<run_id>/submitted-baseline-*.zip` before changes. Root
`output.csv` is the historical 407-row submission and is not the result of the
latest guarded run. An incomplete new run now explicitly warns when it preserves
this older file and records its hash in execution metadata.

Use `--offline` on the main program, sample evaluator, preprocessing, or custom
evaluation to permit only validated matching responses from this run. A missing
response produces an explicit diagnostic without starting a provider session.
The original response provenance and usage remain attributable; cached replay
does not make the earlier model work free.

```bash
python3 -B code/main.py --offline
python3 -B code/evaluation/main.py --offline
python3 -B code/evaluation/custom.py --offline
```

The evaluator includes every public sample in its metric denominators, including
unresolved cases as missing predictions. JSON record update times and snapshot
timestamps are checked as timezone-aware instants. Explicit human-readable
retention deadlines are parsed without filling in missing retention policies.
Serialized citations are rechecked against their source fact, resource, state,
scope and cutoff. Package replay uses an independent cache copy and offline mode,
so testing an archive cannot change the original run pointers or start model jobs.

The pipeline remains blocked on unresolved evidence and policy prerequisites;
passing component tests is not a claim of all-518 completion. See the current
evaluation report and implementer handoff for exact results and blocker examples.

Run: `ghost-c125c273-c4d9-4fbb-a9b8-bb80a8d06056`, manager revision 3. The
application validates inputs, interprets intent/business documents with AI,
extracts JSON/SQL/log/text observations, reconstructs eligible resource states,
applies policy and emits ordered audit plans. It never changes supplied records
or connects to production. Essential unknowns remain diagnostics, not fabricated
COMPLETE/absence. The normal run writes root output.csv atomically **only if
all 518 rows are defensible**; otherwise exit 2 writes only a run-local subset.
For the 2026-10-25 deadline, `code/deadline_export.py` produced a **partial,
non-compliant** root output.csv: 407 of 518 rows (the 75 guarded rows plus 332
INCOMPLETE rows each backed by an eligible policy violation). The remaining 111
cases are omitted rather than guessed; see artifacts/.../deadline-export.json.
AUD-002's historical object/source conflict remains unresolved; no sample exception,
old-evidence TTL, source edit or label override is permitted. Current reports and
implementer memory state the measured results and remaining acceptance gaps.

### Implemented checks

Prerequisites: Python 3.11+ with SQLite JSON support, authorized OpenCode V2
access to `openai/gpt-6.1-sol`, pdftotext, Tesseract (English), and ImageMagick with
the DejaVu-Sans font only to reproduce the historical synthetic image. Python uses only the standard
library. No API credentials belong in this repository; configure authorized
OpenCode access separately. Original data belongs in `dataset/`.

```bash
python3 -m unittest discover -s code/tests -v
python3 code/main.py --check-inputs
python3 code/evaluation/custom.py
python3 code/evaluation/main.py
python3 code/main.py
python3 code/evaluation/report.py
python3 code/package.py
```

Default dataset paths resolve from source, not the working directory. Unit tests
require no provider credentials. Custom, sample and target runs use bounded fresh
tool-denied OpenCode sessions; validated responses cache only inside this run,
keyed by source/prompt/model/config/parser bytes. Changed versions invalidate
cache entries. `python3 code/prepare.py` explicitly rebuilds the 94-artifact
preprocessing snapshot; normal runs reuse a matching snapshot. The original
one-off smoke script and records are preserved as historical evidence under
artifacts/; current verification uses the integrated custom cases and business
artifact pipeline above. Artifacts/telemetry/caches are outside code.zip. The CLI needs both
cwd and PWD set to the isolated runtime workspace; no development role is invoked.
Runtime auth is delegated to OpenCode; available OAuth metadata does not prove
the selected credential or billing. Development ChatGPT sign-in is user-confirmed,
but actual attributable subscription cost is unmeasured. Published API-equivalent
reference scenarios are separate from actual charges; missing telemetry stays unknown.

The sample evaluator runs the same prediction pipeline before reading labels.
If some samples are unresolved, it counts them as missing in full-sample metrics
and exits 2. To compare an existing complete sample file only, use
`python3 code/evaluation/main.py --predictions <sample-output.csv>`; malformed
present steps (including boolean/float numbering) fail, without renumbering them.
The package command creates an allowlisted **candidate** code.zip, tests it in a
temporary extraction with external dataset, and, when available, reproduces the
latest target attempt using an independent copy of this run's validated cache in
offline mode. That is not a
cold-provider reproducibility claim or acceptance of unresolved decisions. No
dataset, credentials, caches, raw artifacts, role memories or nested archive is bundled.

Do **not** submit the candidate as a completed solution while acceptance gaps remain.

---

## Quick Start

Clone the repository and move into the project directory:

```bash
git clone https://github.com/interviewstreet/hackerrank-orchestrate-october26.git
cd hackerrank-orchestrate-october26
```

Start your AI coding tool from the **repository root** so it automatically reads [`AGENTS.md`](./AGENTS.md) and logs your session turns to `log.txt` in the root directory.

Build your solution in `code/main.py`, or use another language and document its setup and run command clearly in your README.

Your solution must:

- Read the input files from `dataset/`
- Generate one prediction row for every request in `dataset/deletion_requests.csv`
- Write the final predictions to `output.csv` in the repository root

Run the starter Python entry point with:

```bash
python3 code/main.py
```

The blank template at `dataset/output.csv` is provided as a reference. Your final generated file for submission must be the root-level `output.csv`.


## Dataset

All participant-facing files are in `dataset/`:

| File | Contents |
| --- | --- |
| `deletion_requests.csv` | 518 requests |
| `sample_deletion_requests.csv` | 32 sample requests |
| `sample_output.csv` | Correct sample answers |
| `user_identities.csv` | Current user identities |
| `user_audit_log.csv` | Historical identity changes |
| `system_activity.csv` | Activity across services and data processes |
| `deletion_rules.csv` | Required treatment for each data category |
| `evidence_files.csv` | Manifest of supplied evidence files |
| `output.csv` | Blank output template |

Evidence is stored under `dataset/evidence/` and may include PDFs, images, logs, JSON, plain text, or SQL snapshot exports. SQL captures may contain a primary database, regional replicas, a reporting replica, or a failover replica so replication drift can be investigated directly. The `.sql` files are readable as text and executable with SQLite.

Only `deletion_requests.csv` requires answers. The other files provide evidence and context.

---

## Output

Create `output.csv` with these columns in this exact order:

```text
case_id,deletion_status,steps_json
```

Produce exactly one row per request. `deletion_status` is `COMPLETE`, `INCOMPLETE`, or `NOT_APPLICABLE`. `steps_json` is an ordered JSON array containing findings, remediation actions, and verification checks. Use an empty array (`[]`) for `NOT_APPLICABLE`. Evidence references may be a `file_id`, `activity_id`, or `audit_id`. Determine the resource state at `audit_at` from the available evidence; reported workflow statuses and operation results are claims. Use `dataset/sample_output.csv` as the format reference.

The final file must contain 518 data rows sorted by `case_id` (plus the header row). The grader parses `steps_json` as JSON, so object-key order and whitespace do not matter; array order does. Order findings, remediation, and verification in that phase order. Within a phase, follow the operation order in the problem statement, then sort by `system_id` and `resource_id`.

---

## Evaluation

`output.csv` will be compared with hidden canonical answers. Scoring considers:

- deletion assessment accuracy;
- current and historical identity resolution;
- discovery of remaining data and recreation risks;
- correct policy application and evidence references; and
- completeness and ordering of remediation and verification steps.

Your `code.zip` must include:

```text
code/evaluation/evaluation_report.md
code/evaluation/usage_report.md
```

- `evaluation_report.md` must cover case, row, field, and sequence accuracy, at least three additional evaluation cases created by you, failures found, and improvements made.
- `usage_report.md` must cover the final full-dataset run, including model providers and names, model calls, input and output tokens, total and average tokens per request, and estimated total and per-request cost. Include per-model and overall totals when using multiple models.

**Important:** Place `evaluation_report.md` and `usage_report.md` inside `code/evaluation/` (matching `code/evaluation/main.py` in this starter layout), write your complete evaluation metrics, custom evaluation test cases, and token/cost breakdowns directly inside those Markdown files, and keep prompts in source code or Markdown files. Automated code evaluation ignores raw data files (`.csv`, `.tsv`, `.json`, `.jsonl`, `.sql`, `.log`), so content stored only in those formats will not be visible to the code judge or AI interviewer.

---

## Chat Transcript

This repository includes [`AGENTS.md`](./AGENTS.md), which instructs compatible AI coding tools to append conversation summaries to `log.txt` in the repository root:

| Platform | Path |
| --- | --- |
| macOS / Linux | `<repo root>/log.txt` |
| Windows | `<repo root>\log.txt` |

- Always launch your AI coding agent from the repository root (or explicitly ask it to read `./AGENTS.md` first) so every turn is logged to `log.txt` with the required `User Prompt`, `Agent Response Summary`, `Actions`, and `Context` sections.
- Upload `log.txt` directly as your `chat_transcript` submission on HackerRank.
- Do not include API keys, tokens, credentials, or secrets in prompts, code, configuration, or `log.txt`.

---

## Packaging `code.zip` and Submission

| Item | Description |
| --- | --- |
| `code.zip` | Runnable solution, prompts, configuration, `README.md`, and `evaluation/` reports |
| `output.csv` | One answer row for each of the 518 requests in `dataset/deletion_requests.csv` |
| `chat_transcript` | The root `log.txt` file generated by your coding agent |
| AI interview | Live explanation of your architecture, approach, and evaluation |

You may use any programming language, model, framework, or retrieval approach. Include clear setup and execution instructions in `README.md` inside `code.zip`.

To package `code.zip` from the repository root without bundling the dataset:

**macOS / Linux:**

```bash
zip -r code.zip README.md code -x "*/__pycache__/*" "*/.venv/*" "*/venv/*" "*/node_modules/*" "*/.git/*" "*/.DS_Store"
```

**Windows (PowerShell):**

```powershell
Compress-Archive -Path README.md, code -DestinationPath code.zip -Force
```

When packaging `code.zip`:

- Keep your evaluation reports in `code/evaluation/` so they are bundled automatically with `code` (or add `evaluation` to the archive command above if you placed them in a top-level `evaluation/` directory).
- Do **not** include `dataset/`, virtual environments (`.venv`, `venv`, `node_modules`), or build caches (`__pycache__`). On Windows, keep `.venv` at the repository root (outside `code/`) and remove any `code/__pycache__` folders before running `Compress-Archive`.
- Do **not** include nested archives (`.zip`, `.tar`, `.gz`, `.tgz`, `.7z`, `.rar`) inside `code.zip` — submissions containing nested archive files will be rejected.

Before submitting, confirm that:

- `output.csv` has the exact header `case_id,deletion_status,steps_json` and contains all 518 data rows sorted by `case_id`;
- every `steps_json` value is a valid JSON array with consecutive step numbers starting at `1`;
- findings cite valid evidence IDs, and `COMPLETE` verification steps cite evidence proving the current state;
- proposed remediation and future verification steps use an empty `evidence_id` (`""`);
- `code.zip` includes your runnable code, `README.md`, `code/evaluation/evaluation_report.md`, and `code/evaluation/usage_report.md`;
- `log.txt` follows the `AGENTS.md` turn format and is uploaded to the `chat_transcript` slot; and
- no API keys, credentials, real personal data, or sensitive configuration values are included.
