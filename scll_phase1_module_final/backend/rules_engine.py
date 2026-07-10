"""
classifier.py — 5-step deterministic classification engine.

Waterfall (strict priority; first match wins, no later step overrides an earlier one):

  STEP 1 — FRP / non-metallic material            → Level 1
  STEP 2 — Exception flags (relief line, jacketed, vibration, …)  → Level 1
  STEP 3 — Equipment chart lookup (Chart 3 pumps / Chart 3 strain / Chart 4)
  STEP 4 — Material chart lookup (Chart 1 / 2)
  STEP 5 — Missing data → Level "?" + Data_Quality_Flag = "MISSING: …"

Graceful handling of missing columns:
  - Exception flag rules whose 'flag' column is absent from the file are silently skipped.
  - Missing size / temperature / material → row marked NEEDS REVIEW, not rejected.
  - Missing FROM/TO → Step 3 short-circuits, classification proceeds with Step 4.

This module performs no I/O. All thresholds come from the rules dict.
"""

from __future__ import annotations

import re

import pandas as pd


# ─────────────────────────────────────────────────────────────────────────────
# Material group resolution
# ─────────────────────────────────────────────────────────────────────────────

def resolve_material_group(pipe_class: str, material_map: dict[str, str]) -> str:
    if not pipe_class or pd.isna(pipe_class):
        return "UNKNOWN"
    return material_map.get(str(pipe_class).strip().upper(), "UNKNOWN")


def _material_code_candidates(value) -> list[str]:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return []
    raw = str(value).strip().upper()
    if not raw:
        return []
    candidates: list[str] = []
    for part in re.split(r"[/-]", raw):
        code = re.sub(r"[^A-Z0-9]", "", part)
        if code and code not in candidates:
            candidates.append(code)
    return candidates


def _first_known_material_code(value, material_map: dict[str, str]) -> tuple[str, str]:
    for code in _material_code_candidates(value):
        group = material_map.get(code)
        if group:
            return code, group
    return "", "UNKNOWN"


def _select_material_code(row: pd.Series, material_map: dict[str, str]) -> tuple[str, str]:
    raw_spec = row.get("piping_spec") if "piping_spec" in row.index else None
    raw_material = row.get("material")

    for raw in (raw_spec, raw_material):
        code, group = _first_known_material_code(raw, material_map)
        if code:
            return code, group

    for raw in (raw_spec, raw_material):
        candidates = _material_code_candidates(raw)
        if candidates:
            return candidates[0], "UNKNOWN"

    return "", "UNKNOWN"


# ─────────────────────────────────────────────────────────────────────────────
# Equipment tag parsing
# ─────────────────────────────────────────────────────────────────────────────

EQUIPMENT_STRUCTURED_TAG_RE = re.compile(r"\b\d{3}-\d[A-Z]\d{2}-([A-Z]{2,4})-(\d{3})(?!\d)\b")
EQUIPMENT_TAG_RE = re.compile(r"\b([A-Z]{2,4})-(\d{3})(?!\d)\b")
EQUIPMENT_IGNORE_CODES = {"PSV", "PRV", "BDV", "SDV", "MOV", "XV", "HV", "FV", "CV", "RV"}


def _equipment_code_categories(rules: dict) -> dict[str, dict[str, str]]:
    categories: dict[str, dict[str, str]] = {}
    for category, cfg in (rules.get("equipment_tag_codes", {}) or {}).items():
        for code in cfg.get("codes", []):
            categories[str(code).upper()] = {
                "category": category,
                "description": cfg.get("description", category),
            }
    return categories


def _build_line_prefix_blocklist(df: pd.DataFrame) -> set[str]:
    blocklist: set[str] = set()
    if df is None or "line_number" not in df.columns:
        return blocklist
    for tag in df["line_number"].dropna():
        tag_str = str(tag).strip().upper()
        match = re.search(r"(?:^|[-\s])([A-Z]{2,4})(?=-?\d)", tag_str)
        if match:
            blocklist.add(match.group(1))
    return blocklist


def _equipment_ignore_codes(rules: dict) -> set[str]:
    codes = set(EQUIPMENT_IGNORE_CODES)
    for category, cfg in (rules.get("equipment_tag_codes", {}) or {}).items():
        if category == "ignore_not_equipment":
            codes.update(str(code).upper() for code in cfg.get("codes", []))
    return codes


def extract_equipment_tags(
    tag_value,
    rules: dict,
    line_prefix_blocklist: set[str] | None = None,
) -> list[dict[str, str]]:
    """
    Extract project equipment tags such as 522-8J20-PMP-011 from FROM/TO text.
    Returns ordered dicts with tag, code, number, category, and description.
    """
    if not tag_value or (isinstance(tag_value, float) and pd.isna(tag_value)):
        return []

    categories = _equipment_code_categories(rules)
    blocklist = {str(code).upper() for code in (line_prefix_blocklist or rules.get("_line_prefix_blocklist", set()))}
    ignore_codes = _equipment_ignore_codes(rules)
    found: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()

    def add_tag(code: str, number: str, raw_tag: str = "") -> None:
        code = code.upper()
        if code in ignore_codes or code in blocklist:
            return
        key = (code, number)
        if key in seen:
            return
        info = categories.get(code, {})
        found.append({
            "tag": raw_tag or f"{code}-{number}",
            "short_tag": f"{code}-{number}",
            "code": code,
            "number": number,
            "category": info.get("category", "unknown"),
            "description": info.get("description", "Unknown equipment code"),
        })
        seen.add(key)

    for fragment in _parse_tag_fragments(tag_value):
        text = fragment.strip().upper()
        structured_matches = list(EQUIPMENT_STRUCTURED_TAG_RE.finditer(text))
        for match in structured_matches:
            add_tag(match.group(1), match.group(2), f"{match.group(1).upper()}-{match.group(2)}")
        if structured_matches:
            continue
        for match in EQUIPMENT_TAG_RE.finditer(text):
            code = match.group(1).upper()
            number = match.group(2)
            key = (code, number)
            if key in seen:
                continue
            add_tag(code, number, f"{code}-{number}")
    return found


def equipment_tags_from_row(row: pd.Series, rules: dict) -> list[dict[str, str]]:
    tags: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for value, _ in _equipment_sources(row):
        for tag in extract_equipment_tags(value, rules):
            key = (tag["code"], tag["number"])
            if key not in seen:
                tags.append(tag)
                seen.add(key)
    return tags


def _select_equipment_chart(row: pd.Series, rules: dict) -> tuple[str | None, dict | None, str]:
    priority = {
        "centrifugal_pump": 3,
        "strain_sensitive_other": 2,
        "non_strain_sensitive": 1,
        "ignore_not_equipment": 0,
        "unknown": 0,
    }
    selected: dict | None = None
    unknown_codes: list[str] = []

    for tag in equipment_tags_from_row(row, rules):
        category = tag["category"]
        if category == "unknown":
            unknown_codes.append(tag["code"])
            continue
        if category == "ignore_not_equipment":
            continue
        if selected is None or priority.get(category, 0) > priority.get(selected["category"], 0):
            selected = tag

    if not selected:
        quality = ""
        if unknown_codes:
            codes = ", ".join(dict.fromkeys(unknown_codes))
            quality = f"Unknown equipment code {codes} in FROM/TO - verify equipment type manually"
        return None, None, quality

    chart_name = {
        "centrifugal_pump": "chart_3_pumps",
        "strain_sensitive_other": "chart_3_strain",
        "non_strain_sensitive": "chart_4",
    }[selected["category"]]
    return chart_name, selected, ""


def _parse_tag_fragments(tag_value) -> list[str]:
    if not tag_value or (isinstance(tag_value, float) and pd.isna(tag_value)):
        return []
    raw = str(tag_value).strip()
    for sep in ("/", "&", ";", ",", "\n"):
        raw = raw.replace(sep, "|")
    return [t.strip() for t in raw.split("|") if t.strip()]


def _match_tag_prefix(tag: str, tag_patterns: list[dict]) -> tuple[bool, str]:
    tag_upper = tag.strip().upper()
    for p in tag_patterns:
        if tag_upper.startswith(str(p["prefix"]).upper()):
            return True, p["type"]
    return False, ""


def _strain_sensitive_prefix(tag_value, rules: dict) -> tuple[bool, str]:
    patterns = rules["strain_sensitive_equipment"].get("tag_patterns", [])
    priority = ["centrifugal_pump", "reciprocating_pump", "compressor",
                "turbine", "heater", "air_cooler"]
    found: list[str] = []
    for t in _parse_tag_fragments(tag_value):
        matched, equip_type = _match_tag_prefix(t, patterns)
        if matched:
            found.append(equip_type)
    if not found:
        return False, ""
    for p in priority:
        if p in found:
            return True, p
    return True, found[0]


def _strain_sensitive_keyword(tag_value, rules: dict) -> tuple[bool, str]:
    if not tag_value or (isinstance(tag_value, float) and pd.isna(tag_value)):
        return False, ""
    tag_upper = str(tag_value).strip().upper()
    for entry in rules["strain_sensitive_equipment"].get("keyword_patterns", []):
        for kw in entry.get("keywords", []):
            if str(kw).upper() in tag_upper:
                return True, entry["type"]
    return False, ""


def is_strain_sensitive_equipment(tag_value, rules: dict) -> tuple[bool, str]:
    keyword_match = _strain_sensitive_keyword(tag_value, rules)
    if keyword_match[0]:
        return keyword_match
    mode = rules["strain_sensitive_equipment"].get("detection_mode", "tag_prefix")
    if mode == "keyword":
        return False, ""
    return _strain_sensitive_prefix(tag_value, rules)


def _non_strain_sensitive_keyword(tag_value, rules: dict) -> bool:
    if not tag_value or (isinstance(tag_value, float) and pd.isna(tag_value)):
        return False
    tag_upper = str(tag_value).strip().upper()
    kws = rules["strain_sensitive_equipment"].get("non_strain_sensitive_keywords", [])
    return any(str(k).upper() in tag_upper for k in kws)


def _matches_known_equipment_prefix(tag_value, rules: dict) -> bool:
    prefixes_by_type = rules.get("cn_settings", {}).get("equipment_type_prefixes", {}) or {}
    known_prefixes = []
    for prefixes in prefixes_by_type.values():
        known_prefixes.extend(str(p).upper() for p in prefixes)
    known_prefixes.extend(
        str(p.get("prefix", "")).upper()
        for p in rules["strain_sensitive_equipment"].get("tag_patterns", [])
    )
    for part in _parse_tag_fragments(tag_value):
        part_upper = part.strip().upper()
        if any(part_upper.startswith(prefix) for prefix in known_prefixes if prefix):
            return True
    return False


def _has_equipment_connection(tag_value, rules: dict, explicit: bool = False) -> bool:
    if not tag_value or (isinstance(tag_value, float) and pd.isna(tag_value)):
        return False
    s = str(tag_value).strip()
    if not s or s.lower() in ("nan", "none", "-", "n/a", "na", "tbd"):
        return False
    if explicit:
        return True
    mode = rules["strain_sensitive_equipment"].get("detection_mode", "tag_prefix")
    if mode == "keyword":
        sensitive, _ = _strain_sensitive_keyword(tag_value, rules)
        return sensitive or _non_strain_sensitive_keyword(tag_value, rules)
    return (_strain_sensitive_keyword(tag_value, rules)[0]
            or _non_strain_sensitive_keyword(tag_value, rules)
            or _matches_known_equipment_prefix(tag_value, rules))


def _equipment_sources(row: pd.Series) -> list[tuple[object, bool]]:
    explicit = []
    for col in ("from_equipment_tag", "to_equipment_tag", "equipment_tag"):
        if col in row.index:
            val = row.get(col)
            if (val is not None and not (isinstance(val, float) and pd.isna(val))
                    and str(val).strip().lower() not in ("", "nan", "none", "-", "n/a", "na", "tbd")):
                explicit.append((val, True))
    if explicit:
        return explicit

    sources = []
    for col in ("from_equipment", "to_equipment"):
        if col in row.index:
            sources.append((row.get(col), False))
    return sources


# ─────────────────────────────────────────────────────────────────────────────
# Numeric parsing (tolerates "60/-20", "150°C")
# ─────────────────────────────────────────────────────────────────────────────

def _to_float(val):
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None
    s = str(val).strip().rstrip("°C").rstrip("°").rstrip("C").strip()
    if not s:
        return None
    if "/" in s:  # compound max/min temp like "60/-20"
        nums = []
        for p in s.split("/"):
            p = p.strip().rstrip("°C").rstrip("°").rstrip("C").strip()
            try:
                nums.append(float(p))
            except (ValueError, TypeError):
                pass
        return max(nums) if nums else None
    try:
        return float(s)
    except (ValueError, TypeError):
        return None


def _to_size_float(val):
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None
    s = str(val).strip()
    if not s or s.upper() in ("XX", "TBD", "N/A", "-"):
        return None
    nums = [float(n) for n in re.findall(r"\d+(?:\.\d+)?", s)]
    return max(nums) if nums else None


# ─────────────────────────────────────────────────────────────────────────────
# Step 2 — Exception flags
# ─────────────────────────────────────────────────────────────────────────────

def _eval_extra(row_val, condition: dict | None) -> bool:
    if condition is None:
        return True
    parser = _to_size_float if condition.get("field") == "size" else _to_float
    v = parser(row_val)
    if v is None:
        return False
    threshold = float(condition["value"])
    op = condition["operator"]
    return {">": v > threshold, ">=": v >= threshold,
            "<": v < threshold, "<=": v <= threshold}.get(op, False)


def _is_true_flag(value, rules: dict) -> bool:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return False
    true_vals = {str(v).strip().lower() for v in rules.get("true_values", [])}
    return str(value).strip().lower() in true_vals


def _level_rank(level: str) -> int:
    return {"Level 1": 1, "Level 2": 2, "Level 3": 3}.get(level, 99)


def _more_critical_level(current: str, candidate: str) -> str:
    return candidate if _level_rank(candidate) < _level_rank(current) else current


def _check_exception_flags(
    row: pd.Series,
    rules: dict,
    material_group: str = "",
    material_code: str = "",
    temp: float | None = None,
) -> tuple[bool, str]:
    for exc in rules.get("exception_flags", []):
        if "flag" not in exc:
            continue
        flag_col = exc["flag"]
        # If the flag column doesn't exist in this file, skip the rule silently
        if flag_col not in row.index:
            continue
        if not _is_true_flag(row.get(flag_col), rules):
            continue
        if exc.get("name") == "vacuum":
            vacuum_rule = rules.get("vacuum_rule", {})
            if not vacuum_rule.get("enabled", True):
                continue
            # Reference document: "lines with vacuum condition (stiffening rings)"
            # -> Level I unconditionally, with NO size limit.
            size = _to_size_float(row.get("size"))
            return True, (
                f"{_base_reason_prefix(material_group, material_code, size, temp)} | "
                "Exception: vacuum service detected (JESA §3.3 item 12) -> Level I unconditional"
            )
        extra = exc.get("extra_condition")
        if extra is not None:
            if extra["field"] not in row.index:
                continue
            if not _eval_extra(row.get(extra["field"]), extra):
                continue
        return True, _short_exception_reason(exc, row, material_group, material_code, temp)
    return False, ""


def _condition_rule(rules: dict, rule_name: str) -> dict | None:
    for exc in rules.get("exception_flags", []):
        if exc.get("name") == rule_name:
            return exc
    return None


def _old_short_exception_reason(
    exc: dict,
    row: pd.Series,
    material_group: str = "",
    material_code: str = "",
    temp: float | None = None,
) -> str:
    name = exc.get("name", "")
    size = _to_size_float(row.get("size"))
    size_txt = f", D={_fmt_size(size)}\"" if size is not None else ""
    labels = {
        "relief_line_high_pressure": "Relief P>10 barg",
        "cement_lined": "Lined pipe",
        "vertical_tower_large": "Tower connection",
        "jacketed": "Jacketed pipe",
        "expansion_joint": "Expansion joint",
        "vibration": "Vibration/slug flow",
        "settlement": "Settlement",
        "ped_category_3_large": "PED Cat III",
        "underground_high_temp": "Underground high T",
        "nozzle_load_limit": "Nozzle load limit",
        "heavy_wall_large": "Heavy wall",
        "cyclic_service": "Cyclic service",
        "category_m": "Category M",
        "schedule_160": "Schedule 160",
        "client_request": "Client request",
    }
    return f"{labels.get(name, exc.get('description', name) or 'Exception')}{size_txt} → L1"


def _short_exception_reason(
    exc: dict,
    row: pd.Series,
    material_group: str = "",
    material_code: str = "",
    temp: float | None = None,
) -> str:
    name = exc.get("name", "")
    size = _to_size_float(row.get("size"))
    labels = {
        "relief_line_high_pressure": "relief line high pressure",
        "cement_lined": "lined pipe",
        "vertical_tower_large": "vertical tower connection",
        "jacketed": "jacketed piping",
        "expansion_joint": "expansion joint",
        "vibration": "vibration/slug flow",
        "large_deflection": "external moment / large deflection",
        "settlement": "settlement",
        "ped_category_3_large": "PED Category III",
        "underground_high_temp": "underground high temperature",
        "nozzle_load_limit": "nozzle load limit",
        "heavy_wall_large": "heavy wall",
        "cyclic_service": "cyclic service",
        "category_m": "Category M",
        "schedule_160": "Schedule 160",
        "client_request": "client request",
    }
    items = {
        "relief_line_high_pressure": 1,
        "cement_lined": 2,
        "vertical_tower_large": 3,
        "jacketed": 4,
        "expansion_joint": 5,
        "vibration": 6,
        "large_deflection": 7,
        "settlement": 7,
        "ped_category_3_large": 8,
        "underground_high_temp": 9,
        "nozzle_load_limit": 10,
        "heavy_wall_large": 11,
        "cyclic_service": 13,
        "category_m": 14,
        "schedule_160": 15,
        "client_request": 16,
    }
    label = labels.get(name, exc.get("description", name) or "exception")
    item = items.get(name, "?")
    return (
        f"{_base_reason_prefix(material_group, material_code, size, temp)} | "
        f"Exception: {label} (JESA §3.3 item {item}) -> Level I unconditional"
    )


def _render_reason(template: str, **values) -> str:
    try:
        return template.format(**values)
    except Exception:
        return template


def _match_keyword(value, keywords: list[str]) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    text = str(value)
    text_upper = text.upper()
    for keyword in keywords:
        kw = str(keyword).strip()
        if kw and kw.upper() in text_upper:
            return kw
    return ""


def _append_quality(existing: str, addition: str) -> str:
    existing = str(existing or "").strip()
    addition = str(addition or "").strip()
    if not addition:
        return existing
    if not existing:
        return addition
    if addition in existing:
        return existing
    return f"{existing}; {addition}"


def _pipe_spec_matches(material_code: str, row: pd.Series, specs: list) -> str:
    wanted = {str(spec).strip().upper() for spec in specs}
    for raw in (material_code, row.get("piping_spec"), row.get("material")):
        for code in _material_code_candidates(raw):
            if code in wanted:
                return code
    return ""


def _format_num(value: float) -> str:
    return f"{value:g}"


def _level_short(level: str) -> str:
    return {"Level 1": "L1", "Level 2": "L2", "Level 3": "L3"}.get(level, level)


def _level_roman(level: str) -> str:
    return {"Level 1": "Level I", "Level 2": "Level II", "Level 3": "Level III"}.get(level, level)


def _fmt_size(size: float) -> str:
    return _format_num(size)


def _fmt_temp(temp: float) -> str:
    return _format_num(temp)


def _row_context(row: pd.Series) -> tuple[str, str, float | None, float | None]:
    material_code = str(row.get("Material_Lookup_Code", "") or "").strip()
    material_group = str(row.get("Material_Group", "") or "").strip()
    if not material_code or not material_group:
        material_code, material_group = _select_material_code(row, {})
    size = _to_size_float(row.get("size"))
    temp = _to_float(row.get("design_temperature"))
    return material_group, material_code, size, temp


def _base_reason_prefix(material_group: str, material_code: str, size: float | None, temp: float | None) -> str:
    size_txt = _fmt_size(size) if size is not None else "?"
    temp_txt = _fmt_temp(temp) if temp is not None else "?"
    return f"{_material_label(material_group or '?', material_code)}, D={size_txt}\", T={temp_txt}°C"


def _chart_label(chart_name: str) -> str:
    return {
        "chart_1": "Chart 1",
        "chart_2": "Chart 2",
        "chart_3_pumps": "Chart 3a",
        "chart_3_strain": "Chart 3b",
        "chart_4": "Chart 4",
    }.get(chart_name, chart_name)


def _chart_reason_label(chart_name: str, material_group: str = "") -> str:
    labels = {
        "chart_1": "Chart 1 (CS)",
        "chart_2": "Chart 2 (SS)",
        "chart_3_pumps": "Chart 3a (pump)",
        "chart_3_strain": "Chart 3b (strain)",
        "chart_4": "Chart 4",
    }
    return labels.get(chart_name, _chart_label(chart_name))


def _material_label(material_group: str, material_code: str = "") -> str:
    return f"{material_group} ({material_code})" if material_code else material_group


def _equipment_short_label(category: str, tag: str = "") -> str:
    if category == "centrifugal_pump":
        return "centrifugal pump"
    if category == "strain_sensitive_other":
        code = str(tag or "").split("-", 1)[0].upper()
        if code == "HEX":
            return "heat exchanger, strain"
        if code in {"ACE", "AIR", "FAN"}:
            return "air cooler, strain"
        return "strain"
    if category == "non_strain_sensitive":
        code = str(tag or "").split("-", 1)[0].upper()
        names = {
            "REA": "reactor",
            "SCB": "scrubber",
            "TNK": "tank",
            "VSL": "vessel",
            "VES": "vessel",
            "SEP": "separator",
            "COL": "column",
            "FIL": "filter",
            "DRM": "drum",
        }
        return f"{names.get(code, 'vessel')}, non-strain"
    return category


def _old_chart_reason(material_group: str, size: float, temp: float, chart_name: str, level: str) -> str:
    return (
        f"{material_group} {_fmt_size(size)}\" | T={_fmt_temp(temp)}°C | "
        f"{_chart_label(chart_name)} → {_level_short(level)}"
    )


def _chart_band(chart_name: str, size: float, rules: dict) -> dict:
    for band in rules[chart_name]["size_bands"]:
        if size <= float(band["max_size"]):
            return band
    return rules[chart_name]["size_bands"][-1]


def _threshold_summary(chart_name: str, size: float, rules: dict) -> str:
    band = _chart_band(chart_name, size, rules)
    l1 = float(band["l1_threshold"])
    l2 = float(band["l2_threshold"])
    max_size = float(band["max_size"])
    if l1 == 0:
        limit = f"D<={_fmt_size(max_size)}\"" if max_size < 9999 else "largest band"
        return f"{limit} -> always L1"
    if _chart_is_exclusive(chart_name, rules):
        # Exact reference-table band: L3 T<=A, L2 A<T<=B, L1 T>B.
        if l1 == l2:
            return f"L1 T>{_fmt_temp(l1)}°C, no L2, L3 T<={_fmt_temp(l1)}°C"
        return (
            f"L1 T>{_fmt_temp(l1)}°C, "
            f"L2 {_fmt_temp(l2)}<T<={_fmt_temp(l1)}°C, "
            f"L3 T<={_fmt_temp(l2)}°C"
        )
    if l1 == l2:
        return f"L1>={_fmt_temp(l1)}°C, no L2"
    return f"L1>={_fmt_temp(l1)}°C, L2>={_fmt_temp(l2)}°C"


def _temperature_band_text(chart_name: str, size: float, temp: float, level: str, rules: dict) -> str:
    band = _chart_band(chart_name, size, rules)
    if float(band["l1_threshold"]) == 0:
        previous = 0.0
        for candidate in rules[chart_name]["size_bands"]:
            if candidate is band:
                break
            previous = float(candidate["max_size"])
        return f"D>{_fmt_size(previous)}\" -> always L1"
    return f"T in {_level_short(level)} band"


def _chart_reason(
    material_group: str,
    material_code: str,
    size: float,
    temp: float,
    chart_name: str,
    level: str,
    rules: dict,
) -> str:
    return (
        f"{_material_label(material_group, material_code)}, D={_fmt_size(size)}\", T={_fmt_temp(temp)}°C | "
        f"No equip. detected -> {_chart_reason_label(chart_name, material_group)}: "
        f"{_threshold_summary(chart_name, size, rules)} | "
        f"{_temperature_band_text(chart_name, size, temp, level, rules)} -> {_level_roman(level)}"
    )


def _equipment_reason(
    material_group: str,
    size: float,
    temp: float,
    tag: str,
    category: str,
    level: str,
    capped: bool = False,
) -> str:
    base = (
        f"{material_group} {_fmt_size(size)}\" | T={_fmt_temp(temp)}°C | "
        f"{tag} ({_equipment_short_label(category, tag)})"
    )
    if capped:
        return f"{base} → capped L2 (D<2\" small bore)"
    return f"{base} → {_level_short(level)}"


def _equipment_reason(
    material_group: str,
    material_code: str,
    size: float,
    temp: float,
    tag: str,
    category: str,
    chart_name: str,
    raw_level: str,
    level: str,
    rules: dict,
    capped: bool = False,
) -> str:
    base = (
        f"{_material_label(material_group, material_code)}, D={_fmt_size(size)}\", T={_fmt_temp(temp)}°C | "
        f"{tag} ({_equipment_short_label(category, tag)})"
    )
    if capped:
        return (
            f"{base} -> {_chart_reason_label(chart_name, material_group)} -> {_level_short(raw_level)} | "
            f"capped: D<2\" small bore on vessel -> {_level_roman(level)}"
        )
    return (
        f"{base} -> {_chart_reason_label(chart_name, material_group)}: "
        f"{_threshold_summary(chart_name, size, rules)} | "
        f"{_temperature_band_text(chart_name, size, temp, level, rules)} -> {_level_roman(level)}"
    )


def _old_missing_reason(missing: list[str]) -> str:
    names = []
    for item in missing:
        names.append({
            "Size": "size",
            "Design Temperature": "temp",
            "Material": "material",
        }.get(item, item.lower()))
    return f"Missing: {', '.join(names)} → review"


def _missing_reason(missing: list[str]) -> str:
    names = []
    for item in missing:
        names.append({
            "Size": "size",
            "Design Temperature": "design temperature",
            "Material": "material",
        }.get(item, item.lower()))
    return (
        f"Classification incomplete: {', '.join(names)} missing. "
        "Cannot apply chart classification. Engineer review required."
    )


def _combined_risk_reason(material_code: str, equipment_tag: dict | None, material_group: str) -> str:
    spec = material_code or material_group
    tag = "equip"
    equip_label = "vessel"
    if equipment_tag:
        tag = equipment_tag.get("short_tag") or equipment_tag.get("tag") or tag
        equip_label = _equipment_short_label(equipment_tag.get("category", ""), tag)
    if spec in {"BG1", "BG2", "CG1", "CG2"}:
        mat = f"{spec} (904L)"
    else:
        mat = f"{spec} (SS)"
    return f"{mat} + {tag} ({equip_label}) | both L2 → L1"


def _combined_risk_reason(
    material_code: str,
    equipment_tag: dict | None,
    material_group: str,
    size: float,
    temp: float,
) -> str:
    spec = material_code or material_group
    tag = "equip"
    equip_label = "vessel, non-strain"
    if equipment_tag:
        tag = equipment_tag.get("short_tag") or equipment_tag.get("tag") or tag
        equip_label = _equipment_short_label(equipment_tag.get("category", ""), tag)
    mat = f"{spec} (904L)" if spec in {"BG1", "BG2", "CG1", "CG2"} else f"{spec} alloy"
    return (
        f"{_material_label(material_group, spec)}, D={_fmt_size(size)}\", T={_fmt_temp(temp)}°C | "
        f"{tag} ({equip_label}) -> Chart 4 -> L2 | + {mat} on vessel nozzle: "
        "combined risk -> upgraded to Level I"
    )


def _pressure_value(row: pd.Series):
    for field in ("design_pressure", "inlet_pressure"):
        if field in row.index:
            pressure = _to_float(row.get(field))
            if pressure is not None:
                return pressure
    return None


def _psv_sources(row: pd.Series) -> list:
    values = []
    for col in (
        "from_equipment",
        "to_equipment",
        "from_equipment_tag",
        "to_equipment_tag",
        "equipment_tag",
    ):
        if col in row.index:
            values.append(row.get(col))
    return values


def _match_psv_keyword(value, keywords: list[str]) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    text = str(value).strip()
    if not text:
        return ""
    text_upper = text.upper()
    for keyword in keywords:
        kw = str(keyword).strip().upper()
        if not kw:
            continue
        if kw.endswith("-"):
            if kw in text_upper:
                return _matched_tag_text(text, kw.rstrip("-"))
            continue
        if " " in kw or len(kw) > 3:
            if kw in text_upper:
                return _matched_tag_text(text, kw)
            continue
        if re.search(rf"(?<![A-Z0-9]){re.escape(kw)}(?:-\w+)?(?![A-Z0-9])", text_upper):
            return _matched_tag_text(text, kw)
    return ""


def _matched_tag_text(text: str, keyword: str) -> str:
    token_re = re.compile(
        rf"[A-Z0-9]*{re.escape(keyword)}[A-Z0-9-]*",
        re.IGNORECASE,
    )
    match = token_re.search(text)
    return match.group(0).strip(" ,;/&") if match else text


def _detect_psv_connection(row: pd.Series, rules: dict) -> str:
    for value in _psv_sources(row):
        match = _match_psv_keyword(value, rules.get("psv_keywords", []))
        if match:
            return match
    return ""


def _check_psv_high_pressure_rule(row: pd.Series, size: float, rules: dict) -> dict | None:
    psv_tag = _detect_psv_connection(row, rules)
    if not psv_tag:
        return None

    pressure = _pressure_value(row)
    if pressure is None:
        return {
            "level": None,
            "data_quality": (
                f"{psv_tag} | P unknown → review"
            ),
        }

    large_rule = _condition_rule(rules, "psv_high_pressure_large") or {}
    small_rule = _condition_rule(rules, "psv_high_pressure_small") or {}
    pressure_threshold = float(
        large_rule.get("pressure_threshold", small_rule.get("pressure_threshold", 10))
    )
    size_threshold = float(
        large_rule.get("size_threshold", small_rule.get("size_threshold", 4))
    )

    if pressure <= pressure_threshold:
        return {
            "level": None,
            "data_quality": (
                f"{psv_tag} | P={_format_num(pressure)} barg <= "
                f"{_format_num(pressure_threshold)} barg → no upgrade"
            ),
        }

    if size > size_threshold:
        return {
            "level": "Level 1",
            "reason": (
                f"{_base_reason_prefix(str(row.get('Material_Group', '') or ''), str(row.get('Material_Lookup_Code', '') or ''), size, _to_float(row.get('design_temperature')))} | "
                f"Exception: {psv_tag} in FROM/TO, P={_format_num(pressure)} barg > "
                f"{_format_num(pressure_threshold)} barg, D>4\" (JESA §3.3 item 1) -> Level I"
            ),
        }

    return {
        "level": "Level 2",
        "reason": (
            f"{_base_reason_prefix(str(row.get('Material_Group', '') or ''), str(row.get('Material_Lookup_Code', '') or ''), size, _to_float(row.get('design_temperature')))} | "
            f"Exception: {psv_tag} in FROM/TO, P={_format_num(pressure)} barg > "
            f"{_format_num(pressure_threshold)} barg, D<=4\" (JESA §3.3 item 1) -> Level II minimum"
        ),
    }


def _check_upgrade_rules(
    row: pd.Series,
    size: float,
    temp: float,
    material_group: str,
    rules: dict,
) -> list[dict]:
    upgrades: list[dict] = []
    fluid_service = row.get("fluid_service")

    psv_upgrade = _check_psv_high_pressure_rule(row, size, rules)
    if psv_upgrade:
        upgrades.append(psv_upgrade)

    raw_min_temp = row.get("min_design_temperature")
    min_temp = None
    if raw_min_temp is not None and not (isinstance(raw_min_temp, float) and pd.isna(raw_min_temp)):
        raw_min_temp_str = str(raw_min_temp).strip()
        if raw_min_temp_str and "AMB" not in raw_min_temp_str.upper():
            min_temp = _to_float(raw_min_temp)

    if min_temp is not None and min_temp < 0:
        cold_rules = rules.get("cold_service", {})
        operating_temp = _to_float(row.get("operating_temperature"))
        if operating_temp is not None and operating_temp <= 0:
            upgrades.append({
                "level": None,
                "data_quality": cold_rules.get(
                    "review_flag",
                    "REVIEW: operating at sub-zero temperature — verify cold case thermal analysis required",
                ),
            })
        level1_rule = cold_rules.get("level1", {})
        level2_rule = cold_rules.get("level2", {})
        level1_temp = float(level1_rule.get("operating_temp_max", -29))
        level2_temp = float(level2_rule.get("operating_temp_max", -10))
        if operating_temp is not None and operating_temp <= level1_temp:
            upgrades.append({
                "level": "Level 1",
                "reason": f"Oper. T={_fmt_temp(operating_temp)}°C (cryogenic) → L1",
            })
        elif operating_temp is not None and operating_temp <= level2_temp:
            upgrades.append({
                "level": "Level 2",
                "reason": f"Oper. T={_fmt_temp(operating_temp)}°C (cryogenic) → L2 min",
            })

    service_rules = rules.get("fluid_service_rules", {})

    matched_corrosive = _match_keyword(fluid_service, rules.get("corrosive_keywords", []))
    if matched_corrosive and material_group == "CS":
        corrosive = service_rules.get("corrosive", {})
        l1_size = float(corrosive.get("level_1_min_size", 4))
        l2_size = float(corrosive.get("level_2_min_size", 2))
        if size >= l1_size:
            upgrades.append({
                "level": "Level 1",
                "reason": f"Corrosive ({matched_corrosive}) | D={_fmt_size(size)}\" → L1",
            })
        elif size >= l2_size:
            upgrades.append({
                "level": "Level 2",
                "reason": f"Corrosive ({matched_corrosive}) | D={_fmt_size(size)}\" → L2 min",
            })

    material_code = str(row.get("Material_Lookup_Code", "") or "")
    for alloy in rules.get("alloy_rules", []):
        if alloy.get("specs") == "ALL_SS":
            continue
        spec = _pipe_spec_matches(material_code, row, alloy.get("specs", []))
        if not spec:
            continue
        corrosive_kw = _match_keyword(fluid_service, alloy.get("corrosive_keywords", []))
        level1_size = float(alloy.get("min_size_for_level1_corrosive", 9999))
        level2_size = float(alloy.get("min_size_for_level2_corrosive", 9999))
        if corrosive_kw and size >= level1_size:
            upgrades.append({
                "level": "Level 1",
                "reason": f"{spec} (904L) | {corrosive_kw} | D>=6\" → L1",
            })
        elif corrosive_kw and size >= level2_size:
            upgrades.append({
                "level": "Level 2",
                "reason": f"{spec} (904L) | {corrosive_kw} | L2 min",
            })
        elif alloy.get("flag_if_mild", False):
            mild_level2_size = float(alloy.get("min_size_for_level2_mild", 9999))
            upgrades.append({
                "level": "Level 2" if size >= mild_level2_size else None,
                "data_quality": _render_reason(
                    alloy.get(
                        "mild_review_flag",
                        "NOTE: 904L alloy ({spec}) — verify if service requires higher criticality",
                    ),
                    spec=spec,
                ),
            })

    steam_condensate = rules.get("steam_condensate_rule", {})
    if (
        steam_condensate.get("enabled", True)
        and _match_keyword(fluid_service, steam_condensate.get("fluid_keywords", []))
        and temp >= float(steam_condensate.get("min_temp", 150))
        and size >= float(steam_condensate.get("min_size_nps", 4))
    ):
        upgrades.append({
            "level": "Level 1",
            "reason": f"Steam condensate | T={_fmt_temp(temp)}°C | D>=4\" → L1",
        })

    return upgrades


def _check_review_flags(row: pd.Series, size: float, level: str, rules: dict) -> str:
    data_quality = ""
    fluid_service = row.get("fluid_service")
    temp = _to_float(row.get("design_temperature"))

    # Vacuum lines are now handled unconditionally as a Level 1 exception (Step 2,
    # no size limit), so there is no longer a "vacuum below min-size" review case.

    hp_rule = rules.get("high_pressure_review", {})
    pressure = _to_float(row.get("design_pressure", row.get("inlet_pressure")))
    hp_levels = set(hp_rule.get("levels", ["Level 2", "Level 3"]))
    if (
        hp_rule.get("enabled", True)
        and pressure is not None
        and size >= float(hp_rule.get("min_size_nps", 0))
        and pressure >= float(hp_rule.get("min_pressure_barg", 0))
        and level in hp_levels
    ):
        data_quality = _append_quality(data_quality, hp_rule.get("review_flag", ""))

    for flag_rule in rules.get("process_review_flags", []):
        if not _match_keyword(fluid_service, flag_rule.get("fluid_keywords", [])):
            continue
        max_size = flag_rule.get("max_size_nps")
        if max_size is not None and not (size < float(max_size)):
            continue
        max_temp = flag_rule.get("max_temp")
        if max_temp is not None:
            if temp is None or temp > float(max_temp):
                continue
        data_quality = _append_quality(data_quality, flag_rule.get("review_flag", ""))

    return data_quality


def _apply_upgrades(
    base_level: str,
    base_reason: str,
    upgrades: list[dict],
    row: pd.Series,
    size: float,
    rules: dict,
) -> dict:
    level = base_level
    reasons = [r for r in [base_reason] if r]
    for upgrade in upgrades:
        if upgrade.get("level"):
            current_level = level
            level = _more_critical_level(level, upgrade["level"])
            if upgrade.get("reason") and _level_rank(upgrade["level"]) <= _level_rank(current_level):
                reasons.append(upgrade["reason"])
                continue
        if upgrade.get("reason") and not upgrade.get("level"):
            reasons.append(upgrade["reason"])
    data_quality = _check_review_flags(row, size, level, rules)
    for upgrade in upgrades:
        if upgrade.get("data_quality"):
            data_quality = _append_quality(data_quality, upgrade["data_quality"])
    return {
        "level": level,
        "reason": " | ".join(dict.fromkeys(reasons)),
        "data_quality": data_quality,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Chart lookups
# ─────────────────────────────────────────────────────────────────────────────

def _apply_combined_risk_upgrade(
    classification: dict,
    equipment_chart: str,
    equipment_chart_level: str,
    material_group: str,
    material_code: str,
    equipment_tag: dict | None,
    size: float,
    temp: float,
    rules: dict,
) -> dict:
    combined_rule = rules.get("combined_risk_rule", {})
    if not combined_rule.get("enabled", False):
        return classification
    if equipment_chart != "chart_4" or equipment_chart_level != "Level 2":
        return classification
    if material_group != "SS":
        return classification
    if classification.get("level") != "Level 2":
        return classification

    upgraded = classification.copy()
    upgraded["level"] = "Level 1"
    upgraded["reason"] = _combined_risk_reason(material_code, equipment_tag, material_group, size, temp)
    return upgraded


def _chart_is_exclusive(chart_name: str, rules: dict) -> bool:
    """Charts 1 & 2 use exclusive boundaries (L1 = T > l1, L2 = l2 < T <= l1)
    to exactly match the reference criticality tables; charts 3 & 4 keep the
    original inclusive (>=) semantics."""
    return str(rules[chart_name].get("threshold_boundary", "inclusive")).lower() == "exclusive"


def _lookup_chart(chart_name: str, size: float, temp: float, rules: dict) -> str:
    exclusive = _chart_is_exclusive(chart_name, rules)
    for band in rules[chart_name]["size_bands"]:
        if size <= float(band["max_size"]):
            l1_threshold = float(band["l1_threshold"])
            l2_threshold = float(band["l2_threshold"])
            if l1_threshold == 0:
                return "Level 1"
            l1_hit = temp > l1_threshold if exclusive else temp >= l1_threshold
            if l1_hit:
                return "Level 1"
            if l1_threshold == l2_threshold:
                return "Level 3"
            l2_hit = temp > l2_threshold if exclusive else temp >= l2_threshold
            if l2_hit:
                return "Level 2"
            return "Level 3"
    return "Level 3"


def _apply_chart_4_small_bore_cap(level: str, size: float) -> tuple[str, bool]:
    if level == "Level 1" and size < 2:
        return "Level 2", True
    return level, False


def _apply_chart_3(
    size: float,
    temp: float,
    equip_type: str,
    material_group: str,
    material_code: str,
    rules: dict,
) -> tuple[str, str]:
    chart_name = "chart_3_pumps" if equip_type == "centrifugal_pump" else "chart_3_strain"
    level = _lookup_chart(chart_name, size, temp, rules)
    category = "centrifugal_pump" if equip_type == "centrifugal_pump" else "strain_sensitive_other"
    tag = equip_type.replace("_", " ")
    return level, _equipment_reason(
        material_group, material_code, size, temp, tag, category, chart_name, level, level, rules
    )

# ─────────────────────────────────────────────────────────────────────────────
# Row classifier
# ─────────────────────────────────────────────────────────────────────────────

def classify_row(row: pd.Series, material_map: dict, rules: dict) -> dict:
    """
    Returns {level, reason, data_quality}.
    level         — "Level 1" | "Level 2" | "Level 3" | "" (unclassifiable)
    reason        — human-readable explanation of which rule fired
    data_quality  — "" | "MISSING: <fields>" | "AMBIGUOUS"
    """

    # ── Check required fields present ────────────────────────────────────────
    raw_size     = row.get("size")
    raw_temp     = row.get("design_temperature")
    raw_material = row.get("material")

    size     = _to_size_float(raw_size)
    temp     = _to_float(raw_temp)
    material_str, material_group = _select_material_code(row, material_map)
    row = row.copy()
    row["Material_Lookup_Code"] = material_str
    row["Material_Group"] = material_group

    missing = []
    if size is None:
        missing.append("Size")
    if temp is None:
        missing.append("Design Temperature")
    if not material_str:
        missing.append("Material")

    if missing:
        # Vacuum is an unconditional Level 1 exception with no size/temp/material
        # dependency (reference document), so it must win even when those cells are
        # blank — otherwise a vacuum line would slip through as "MISSING".
        vacuum_rule = rules.get("vacuum_rule", {})
        if (
            vacuum_rule.get("enabled", True)
            and "vacuum" in row.index
            and _is_true_flag(row.get("vacuum"), rules)
        ):
            return {
                "level":        "Level 1",
                "reason":       (
                    f"{_base_reason_prefix(material_group, material_str, size, temp)} | "
                    "Exception: vacuum service detected (JESA §3.3 item 12) -> Level I unconditional"
                ),
                "data_quality": f"MISSING: {', '.join(missing)}",
            }
        return {
            "level":        "",
            "reason":       _missing_reason(missing),
            "data_quality": f"MISSING: {', '.join(missing)}",
        }

    # ── STEP 1: FRP / non-metallic → Level 1 ─────────────────────────────────
    if material_group == "FRP":
        return {
            "level":        "Level 1",
            "reason":       (
                f"{_material_label(material_group, material_str)}, D={_fmt_size(size)}\", T={_fmt_temp(temp)}°C | "
                "Non-metallic material -> Level I unconditional (all FRP/GRE/HDPE regardless of T or D)"
            ),
            "data_quality": "",
        }
    if material_group == "UNKNOWN":
        return {
            "level":        "",
            "reason":       f"Material code '{material_str}' not in material_mapping.yaml — cannot classify",
            "data_quality": "AMBIGUOUS",
            "material_key":  material_str,
        }

    # ── STEP 2: Exception flags ──────────────────────────────────────────────
    triggered, reason = _check_exception_flags(row, rules, material_group, material_str, temp)
    if triggered:
        upgrades = _check_upgrade_rules(row, size, temp, material_group, rules)
        return _apply_upgrades("Level 1", reason, upgrades, row, size, rules)

    upgrades = _check_upgrade_rules(row, size, temp, material_group, rules)

    equipment_sources = _equipment_sources(row)
    equipment_chart, equipment_tag, equipment_quality = _select_equipment_chart(row, rules)
    if equipment_quality:
        upgrades.append({"level": None, "data_quality": equipment_quality})

    # ── STEP 3: Project equipment tags (Chart 3 / Chart 4) ───────────────────
    if equipment_chart and equipment_tag:
        raw_level = _lookup_chart(equipment_chart, size, temp, rules)
        level = raw_level
        capped = False
        if equipment_chart == "chart_4":
            level, capped = _apply_chart_4_small_bore_cap(raw_level, size)
        reason = _equipment_reason(
            material_group,
            material_str,
            size,
            temp,
            equipment_tag["short_tag"],
            equipment_tag["category"],
            equipment_chart,
            raw_level,
            level,
            rules,
            capped,
        )
        classification = _apply_upgrades(level, reason, upgrades, row, size, rules)
        return _apply_combined_risk_upgrade(
            classification,
            equipment_chart,
            raw_level,
            material_group,
            material_str,
            equipment_tag,
            size,
            temp,
            rules,
        )

    # ── STEP 3: Legacy strain-sensitive equipment names/prefixes (Chart 3) ───
    sens_types = []
    for source_value, _ in equipment_sources:
        sensitive, equip_type = is_strain_sensitive_equipment(source_value, rules)
        if sensitive:
            sens_types.append(equip_type)

    if sens_types:
        priority = ["centrifugal_pump", "reciprocating_pump", "compressor",
                    "turbine", "heater", "air_cooler"]
        equip_type = sens_types[0]
        for p in priority:
            if p in sens_types:
                equip_type = p
                break
        level, step3_reason = _apply_chart_3(size, temp, equip_type, material_group, material_str, rules)
        return _apply_upgrades(level, step3_reason, upgrades, row, size, rules)

    # ── STEP 4: Material chart lookup ────────────────────────────────────────
    chart_name = rules["material_chart_map"].get(material_group)
    if not chart_name:
        return {
            "level":        "",
            "reason":       f"No chart defined for material group '{material_group}'",
            "data_quality": "AMBIGUOUS",
        }

    mat_level = _lookup_chart(chart_name, size, temp, rules)

    has_equip = any(
        _has_equipment_connection(source_value, rules, explicit=explicit)
        for source_value, explicit in equipment_sources
    )

    if has_equip:
        raw_c4_level = _lookup_chart("chart_4", size, temp, rules)
        c4_level, c4_capped = _apply_chart_4_small_bore_cap(raw_c4_level, size)
        if _level_rank(c4_level) <= _level_rank(mat_level):
            classification = _apply_upgrades(
                c4_level,
                _equipment_reason(
                    material_group,
                    material_str,
                    size,
                    temp,
                    "equip",
                    "non_strain_sensitive",
                    "chart_4",
                    raw_c4_level,
                    c4_level,
                    rules,
                    c4_capped,
                ),
                upgrades,
                row,
                size,
                rules,
            )
            return _apply_combined_risk_upgrade(
                classification,
                "chart_4",
                raw_c4_level,
                material_group,
                material_str,
                None,
                size,
                temp,
                rules,
            )
        return _apply_upgrades(
            mat_level,
            _chart_reason(material_group, material_str, size, temp, chart_name, mat_level, rules),
            upgrades,
            row,
            size,
            rules,
        )

    return _apply_upgrades(
        mat_level,
        _chart_reason(material_group, material_str, size, temp, chart_name, mat_level, rules),
        upgrades,
        row,
        size,
        rules,
    )


def classify_dataframe(df: pd.DataFrame, material_map: dict, rules: dict) -> pd.DataFrame:
    """Apply classify_row to every row; returns a copy with 3 new columns."""
    if df.empty:
        out = df.copy()
        for col in ("Level", "Classification_Reason", "Data_Quality_Flag"):
            out[col] = ""
        out["Material_Lookup_Code"] = ""
        return out

    rules_with_prefixes = dict(rules)
    rules_with_prefixes["_line_prefix_blocklist"] = _build_line_prefix_blocklist(df)

    results = df.apply(
        lambda row: classify_row(row, material_map, rules_with_prefixes),
        axis=1,
        result_type="expand",
    )
    out = df.copy()
    out["Level"]                 = results["level"]
    out["Classification_Reason"] = results["reason"]
    out["Data_Quality_Flag"]     = results["data_quality"]
    out["Material_Lookup_Code"]  = df.apply(
        lambda row: _select_material_code(row, material_map)[0],
        axis=1,
    )
    return out
