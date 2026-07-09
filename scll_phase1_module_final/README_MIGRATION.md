# SCLL Phase 1 Module Migration

This folder is a clean, copyable Phase 1 module that reproduces the **final
standalone SCLL tool** behavior exactly.

## What Was Extracted (rebuilt 2026-07 to match standalone byte-for-byte)

The detection, reading, and classification logic are **verbatim copies** of the
final standalone tool's source, so results match the standalone exactly:

- `backend/format_detector.py` — verbatim `format_detector.py` (dynamic sheet /
  header / units-row / column / scope / size-unit detection).
- `backend/parser.py` — verbatim `parser.py` (reading, column normalization,
  scope filtering, mm→NPS conversion).
- `backend/rules_engine.py` — verbatim `classifier.py` (deterministic 5-step
  Level I / II / III waterfall + reasons + data-quality flags).
- `backend/config/rules.yaml`, `mapping.yaml`, `material_mapping.yaml` — verbatim
  standalone config (the three separate files the standalone loads).
- `backend/column_mapper.py` — thin backward-compat shim re-exporting
  `format_detector`.
- `backend/classifier.py` — Phase 1 orchestrator (`process_scll_phase1`).
- `backend/excel_exporter.py` — clean self-contained 2-sheet Phase 1 output.
- A portable Flask Blueprint named `scll_bp`.

Verified against the standalone on the Q37027 line list (907 rows): identical
Level I / II / III on every row (475 / 123 / 274, 35 unclassified).

The public backend entry point is:

```python
from scll_phase1_module_final.backend import process_scll_phase1

summary = process_scll_phase1(input_excel_path, output_folder)
```

Return shape:

```python
{
    "total_lines": 0,
    "in_scope_lines": 0,
    "excluded_lines": 0,
    "level_1_count": 0,
    "level_2_count": 0,
    "level_3_count": 0,
    "missing_data_count": 0,
    "ambiguous_count": 0,
    "output_excel_path": "...",
    "warnings": [],
    "detection_summary": "...",
}
```

## Excel Output (2 sheets, self-contained)

- **Sheet 1 "Classified Line List"** — the original line-list rows (original
  headers + original values) with three appended columns: `CRITICALITY LEVEL`
  (I / II / III), `CLASSIFICATION REASON`, `DATA QUALITY FLAG`. Rows are colored
  by criticality. The source workbook is **not** copied, so coversheets, notes,
  and merged-cell blocks are never dragged along.
- **Sheet 2 "Classification Report"** — totals, criticality counts, data-detection
  assumptions, columns not detected, warnings, and the classification criteria
  summary.

## What Was Intentionally Excluded

- CN assignment, grouping, proposal, numbering, and review workflow.
- P&ID upload, viewing, markup, PDF highlighting, and review.
- Candidate matching logic.
- Equipment-list assisted CN workflows.
- Any Phase 2 or advanced workflow routes.

The generated Excel appends only:

- `CRITICALITY LEVEL`
- `CLASSIFICATION REASON`
- `DATA QUALITY FLAG`

## Copy Into Main Platform

Copy the full folder into the main Flask platform, keeping this structure intact:

```text
scll_phase1_module_final/
  backend/
  routes/
  templates/scll/
  static/scll/
```

The module uses relative imports and reads its own `backend/config/` YAML files
(`rules.yaml`, `mapping.yaml`, `material_mapping.yaml`), so it does not depend on
the old full SCLL app root.

## Register The Blueprint

```python
from scll_phase1_module_final.routes import scll_bp

app.register_blueprint(scll_bp)

app.config["SCLL_UPLOAD_FOLDER"] = "uploads"
app.config["SCLL_OUTPUT_FOLDER"] = "outputs"
```

Routes provided:

- `GET /scll`
- `POST /scll/upload`
- `GET /scll/results/<job_id>`
- `GET /scll/download/<job_id>`

## Required Dependencies

Install these in the target platform environment:

```text
flask>=3.0.0
openpyxl>=3.1.0
pandas>=2.0.0
pyyaml>=6.0
```

No PDF libraries are required for Phase 1.

## Manual Test Steps

1. Compile/import the module:

```bash
python -m compileall scll_phase1_module_final
```

2. Register the Blueprint in a small Flask app and confirm the `/scll` routes exist.

3. Run the public backend function:

```python
from scll_phase1_module_final.backend import process_scll_phase1
summary = process_scll_phase1("test_linelist.xlsx", "outputs")
print(summary)
```

4. Open the generated Excel file and confirm the added headers are only:

```text
CRITICALITY LEVEL
CLASSIFICATION REASON
DATA QUALITY FLAG
```

5. Confirm no generated CN columns exist.

6. Confirm no P&ID, PDF, or candidate matching logic is needed to run Phase 1.

## Phase 2 Integration Note

Future CN logic should be added after `process_scll_phase1` returns and should consume the Phase 1 classified output as a separate workflow. Keep it outside this module unless intentionally creating a Phase 2 package.
