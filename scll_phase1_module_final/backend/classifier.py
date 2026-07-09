"""Public Phase 1 API for SCLL line-list classification.

This orchestrator runs the SAME pipeline as the final standalone SCLL tool
(detect_format -> read_linelist -> filter_scope -> classify_dataframe) using the
standalone engine and configuration files verbatim. It then writes a clean
2-sheet Phase 1 workbook.

Intentionally excluded (Phase 2+): CN assignment / grouping / proposal / review,
P&ID markup, PDF highlighting, candidate matching, equipment-list workflows.
"""

from __future__ import annotations

import re
import warnings as warnings_module
from pathlib import Path
from typing import Any

import pandas as pd

from .excel_exporter import LEVEL_TO_ROMAN, PHASE1_HEADERS, write_phase1_output
from .format_detector import apply_detection_to_rules, detect_format, load_mapping
from .parser import filter_scope, load_material_map, load_rules, read_linelist
from .rules_engine import classify_dataframe

MODULE_DIR = Path(__file__).resolve().parent
CONFIG_DIR = MODULE_DIR / "config"
RULES_PATH = CONFIG_DIR / "rules.yaml"
MAPPING_PATH = CONFIG_DIR / "mapping.yaml"
MATERIAL_MAP_PATH = CONFIG_DIR / "material_mapping.yaml"

_MAX_WARNINGS = 25


def process_scll_phase1(input_excel_path: str, output_folder: str) -> dict[str, Any]:
    """Run Phase 1 only: detect columns, classify, flag data quality, export Excel."""
    input_path = Path(input_excel_path).resolve()
    output_dir = Path(output_folder).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    if not input_path.is_file():
        raise FileNotFoundError(f"Input Excel file not found: {input_path}")

    # ── Load standalone configuration (verbatim files) ──────────────────────
    rules = load_rules(str(RULES_PATH))
    mapping = load_mapping(str(MAPPING_PATH))
    material_map = load_material_map(str(MATERIAL_MAP_PATH))

    # ── Detect format ───────────────────────────────────────────────────────
    detected_config, detection_summary = detect_format(str(input_path), mapping)
    rules = apply_detection_to_rules(rules, detected_config, mapping)

    # ── Read line list (renamed internal columns) for classification ────────
    with warnings_module.catch_warnings(record=True) as caught:
        warnings_module.simplefilter("always")
        raw_df = read_linelist(str(input_path), detected_config, rules)
    read_warnings = [str(item.message) for item in caught]

    in_scope_df, excluded_df, exclusion_labels = filter_scope(raw_df, detected_config)

    if not in_scope_df.empty:
        classified_df = classify_dataframe(in_scope_df, material_map, rules)
    else:
        classified_df = in_scope_df.copy()
        for col in ("Level", "Classification_Reason", "Data_Quality_Flag"):
            classified_df[col] = ""

    # ── Build per-row Phase 1 result columns aligned to raw_df index ────────
    results = _assemble_results(raw_df, classified_df, excluded_df, exclusion_labels)

    # ── Display frame: original headers + original values + 3 result cols ───
    display_df = _read_display_frame(str(input_path), detected_config)
    display_df = _attach_results(display_df, results)

    # ── Counts ──────────────────────────────────────────────────────────────
    level_series = results["Level"].astype(str)
    dq_series = results["Data_Quality_Flag"].astype(str)
    l1 = int((level_series == "Level 1").sum())
    l2 = int((level_series == "Level 2").sum())
    l3 = int((level_series == "Level 3").sum())
    missing = int(dq_series.str.startswith("MISSING").sum())
    ambiguous = int((dq_series == "AMBIGUOUS").sum())
    total = int(len(display_df))
    excluded = int(len(excluded_df))
    in_scope = total - excluded

    # ── Warnings (deduped, bounded) ─────────────────────────────────────────
    warnings = _collect_warnings(read_warnings, detection_summary, dq_series)

    # ── Report for Sheet 2 ──────────────────────────────────────────────────
    report = _build_report(
        detected_config, detection_summary, rules,
        total=total, in_scope=in_scope, excluded=excluded,
        l1=l1, l2=l2, l3=l3, missing=missing, ambiguous=ambiguous,
        warnings=warnings,
    )

    # ── Write output ────────────────────────────────────────────────────────
    output_filename = f"{_project_stem(input_path)}_SCLL.xlsx"
    output_path = output_dir / output_filename
    write_phase1_output(str(output_path), display_df, report)

    return {
        "total_lines": total,
        "in_scope_lines": in_scope,
        "excluded_lines": excluded,
        "level_1_count": l1,
        "level_2_count": l2,
        "level_3_count": l3,
        "missing_data_count": missing,
        "ambiguous_count": ambiguous,
        "output_excel_path": str(output_path),
        "warnings": warnings,
        "detection_summary": detection_summary,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _project_stem(input_path: Path) -> str:
    """Derive a clean output filename stem from the uploaded file's own name
    (its project/document number), e.g. 'Q37027-02-A00-PE-LST-00010 (1).xlsx'
    -> 'Q37027-02-A00-PE-LST-00010'."""
    stem = input_path.stem
    stem = re.sub(r"(\s*\(\d+\))+$", "", stem).strip()  # strip "(1)" dup-download markers
    stem = re.sub(r"[^A-Za-z0-9._-]+", "_", stem)
    stem = re.sub(r"_+", "_", stem).strip("_.")
    return stem or "line_list"


def _assemble_results(
    raw_df: pd.DataFrame,
    classified_df: pd.DataFrame,
    excluded_df: pd.DataFrame,
    exclusion_labels: pd.Series,
) -> pd.DataFrame:
    """Per-row Level / Classification_Reason / Data_Quality_Flag, indexed like raw_df."""
    results = pd.DataFrame(
        {"Level": "", "Classification_Reason": "", "Data_Quality_Flag": ""},
        index=raw_df.index,
    )
    for col in ("Level", "Classification_Reason", "Data_Quality_Flag"):
        if col in classified_df.columns:
            results.loc[classified_df.index, col] = classified_df[col].astype(str)

    for idx in excluded_df.index:
        label = exclusion_labels.at[idx] if idx in exclusion_labels.index else ""
        if label:
            results.at[idx, "Data_Quality_Flag"] = f"SCOPE: {label}"

    return results


def _read_display_frame(input_path: str, detected_config: dict) -> pd.DataFrame:
    """Re-read the original data region with ORIGINAL headers/values (no rename,
    no mm->NPS conversion). Row selection mirrors read_linelist exactly so the
    index aligns 1:1 with the classification results."""
    sheet_name = detected_config.get("sheet_name", 0)
    header_row = int(detected_config.get("header_row", 0))
    skip_rows = detected_config.get("skip_rows", [])

    df = pd.read_excel(
        input_path,
        sheet_name=sheet_name,
        header=header_row,
        skiprows=skip_rows if skip_rows else None,
        dtype=str,
    )
    df.columns = [str(c).strip() for c in df.columns]
    df = df.map(lambda x: x.strip() if isinstance(x, str) else x)
    df = df.dropna(how="all").reset_index(drop=True)
    return df


def _attach_results(display_df: pd.DataFrame, results: pd.DataFrame) -> pd.DataFrame:
    """Append the three Phase 1 columns to the original-headed display frame.
    Alignment is positional (both frames share the reset 0..N-1 index)."""
    out = display_df.copy()
    n = min(len(out), len(results))
    level = results["Level"].astype(str).tolist()
    reason = results["Classification_Reason"].astype(str).tolist()
    dq = results["Data_Quality_Flag"].astype(str).tolist()

    roman = [LEVEL_TO_ROMAN.get(level[i], "") for i in range(n)]
    # pad if display frame somehow longer
    while len(roman) < len(out):
        roman.append("")
        reason.append("")
        dq.append("")

    # Avoid clobbering an existing original column of the same name
    labels = _unique_labels(list(out.columns), PHASE1_HEADERS)
    out[labels[0]] = roman[: len(out)]
    out[labels[1]] = reason[: len(out)]
    out[labels[2]] = dq[: len(out)]
    # Ensure the exporter can find the columns by their canonical names
    rename = {labels[i]: PHASE1_HEADERS[i] for i in range(3) if labels[i] != PHASE1_HEADERS[i]}
    if rename:
        out = out.rename(columns=rename)
    return out


def _unique_labels(existing: list[str], desired: list[str]) -> list[str]:
    taken = set(str(c) for c in existing)
    out = []
    for name in desired:
        candidate = name
        n = 2
        while candidate in taken:
            candidate = f"{name} ({n})"
            n += 1
        taken.add(candidate)
        out.append(candidate)
    return out


def _collect_warnings(read_warnings, detection_summary: str, dq_series: pd.Series) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()

    def add(msg: str) -> None:
        text = str(msg).strip()
        if text and text not in seen:
            seen.add(text)
            out.append(text)

    for line in str(detection_summary or "").splitlines():
        line = line.strip()
        if line.startswith("!"):
            add(line.lstrip("! ").strip())
    for w in read_warnings:
        add(w)

    distinct_dq = [d for d in dict.fromkeys(dq_series.tolist()) if str(d).strip()]
    shown = 0
    for d in distinct_dq:
        if shown >= _MAX_WARNINGS:
            add(f"...and {len(distinct_dq) - shown} more distinct data-quality flag(s) in the Excel output.")
            break
        add(d)
        shown += 1
    return out


def _build_report(
    detected_config: dict,
    detection_summary: str,
    rules: dict,
    *,
    total: int, in_scope: int, excluded: int,
    l1: int, l2: int, l3: int, missing: int, ambiguous: int,
    warnings: list[str],
) -> dict:
    header_row = int(detected_config.get("header_row", 0))
    skip_rows = detected_config.get("skip_rows", []) or []
    size_unit = detected_config.get("size_unit", "inches")
    scope_mode = detected_config.get("scope_mode", "assume_all_in_scope")
    equipment_mode = (
        rules.get("strain_sensitive_equipment", {}).get("detection_mode", "tag_prefix")
    )

    scope_labels = {
        "assume_all_in_scope": "No scope column — all lines treated as in scope",
        "include_values": "Dedicated scope column (keep listed in-scope values)",
        "text_keywords": "Scope by keyword exclusion (vendor / client / licensor)",
        "column_exclude_values": "Scope column (exclude listed values)",
    }

    return {
        "total_lines": total,
        "in_scope_lines": in_scope,
        "excluded_lines": excluded,
        "level_1_count": l1,
        "level_2_count": l2,
        "level_3_count": l3,
        "missing_data_count": missing,
        "ambiguous_count": ambiguous,
        "sheet_name": detected_config.get("sheet_name", ""),
        "header_excel_row": header_row + 1,
        "units_row_skipped": ", ".join(str(int(r) + 1) for r in skip_rows) if skip_rows else "none",
        "size_unit_label": "mm → converted to NPS inches" if size_unit == "mm" else "inches (as provided)",
        "scope_label": scope_labels.get(scope_mode, scope_mode),
        "equipment_mode": "keyword" if equipment_mode == "keyword" else "tag-prefix",
        "columns_mapped": len(detected_config.get("column_mappings", {})),
        "columns_not_detected": list(detected_config.get("not_found_columns", []) or []),
        "warnings": warnings,
    }
