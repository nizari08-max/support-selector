"""
span_calculator.py — Support Span Lookup Engine
Maximum recommended pipe support spacing per ASME B31.1, B31.3 / Shell DEP, ISO 14692.
All span values in metres. For reference/preliminary use only.
"""

# ── TABLE A — ASME B31.1 Table 121.5 ────────────────────────────────────────
# (water/liquid m, steam/gas/air m)
TABLE_A = {
     1.0:  (2.1,  2.7),
     2.0:  (3.0,  4.0),
     3.0:  (3.7,  4.6),
     4.0:  (4.3,  5.2),
     6.0:  (5.2,  6.4),
     8.0:  (5.8,  7.3),
    12.0:  (7.0,  9.1),
    16.0:  (8.2, 10.7),
    20.0:  (9.1, 11.9),
    24.0:  (9.8, 12.8),
}

# ── TABLE B — ASME B31.3 / Shell DEP — Carbon Steel ─────────────────────────
# (vapor_bare, vapor_ins, liquid_bare, liquid_ins)  all metres
TABLE_B = {
     0.5:  ( 0.90,  0.80,  0.90,  0.80),
     0.75: ( 1.40,  1.20,  1.40,  1.20),
     1.0:  ( 3.60,  2.30,  3.45,  2.25),
     1.5:  ( 3.60,  3.00,  3.45,  2.80),
     2.0:  ( 3.60,  3.45,  3.45,  3.30),
     3.0:  ( 6.55,  4.60,  5.45,  4.20),
     4.0:  ( 7.50,  5.55,  6.10,  4.90),
     6.0:  ( 9.15,  6.80,  7.10,  5.80),
     8.0:  (10.50,  8.05,  7.95,  6.70),
    10.0:  (11.80,  9.05,  8.70,  7.40),
    12.0:  (12.90,  9.80,  9.15,  7.80),
    14.0:  (15.15, 11.85, 10.85,  9.30),
    16.0:  (16.25, 12.85, 11.20,  9.75),
    18.0:  (17.25, 13.75, 11.50, 10.15),
    20.0:  (18.20, 14.45, 11.75, 10.40),
    24.0:  (18.95, 16.05, 12.15, 10.95),
    30.0:  (21.00, 17.50, 13.10, 11.50),
    36.0:  (22.70, 18.50, 13.70, 12.50),
    42.0:  (23.40, 19.50, 14.30, 13.00),
    48.0:  (25.00, 20.50, 14.60, 13.40),
}

# ── TABLE C — ASME B31.3 — Stainless Steel Schedule 10S ─────────────────────
# (vapor_bare, vapor_ins, liquid_bare, liquid_ins)  all metres
TABLE_C = {
     1.0:  ( 2.20,  1.80,  2.10,  1.80),
     1.5:  ( 2.80,  2.50,  2.40,  2.50),
     2.0:  ( 2.80,  2.60,  2.70,  2.60),
     3.0:  ( 6.40,  4.05,  4.95,  3.50),
     4.0:  ( 6.40,  4.80,  5.30,  4.00),
     6.0:  ( 9.40,  5.75,  5.95,  4.60),
     8.0:  (10.75,  6.80,  6.45,  5.20),
    10.0:  (10.75,  7.60,  6.95,  5.65),
    12.0:  (10.75,  8.25,  7.35,  6.05),
    14.0:  (10.75,  8.70,  7.60,  6.30),
    16.0:  (11.00,  9.45,  7.75,  6.55),
    18.0:  (11.00,  9.70,  7.85,  6.75),
    20.0:  (11.50, 10.50,  8.40,  7.30),
    24.0:  (12.00, 11.00,  9.05,  8.05),
    30.0:  (14.00, 13.00, 10.50,  9.50),
    36.0:  (16.00, 15.00, 11.50, 10.50),
    42.0:  (18.00, 16.50, 12.50, 11.50),
    48.0:  (20.00, 17.30, 13.50, 12.50),
}

# ── TABLE D — FRP/GRE  ISO 14692 (simplified) ────────────────────────────────
TABLE_D = {
     1.0: 0.6,
     2.0: 1.2,
     3.0: 1.8,
     4.0: 2.1,
     6.0: 2.4,
     8.0: 3.0,
    10.0: 3.6,
    12.0: 4.3,
}
FRP_MAX_NPS = 12.0

# ── Column selector helpers ───────────────────────────────────────────────────
_COLS_B_C = {
    ("vapor",  "bare"):      0,
    ("vapor",  "insulated"): 1,
    ("liquid", "bare"):      2,
    ("liquid", "insulated"): 3,
}


def _interp(table: dict, nps: float):
    """
    Return interpolated (key, value) for the requested NPS.
    Value is a tuple or float depending on the table structure.
    Returns (None, None) when nps is outside the table range by >50% of the
    smallest table key or the nps is negative.
    """
    if not table or nps <= 0:
        return None, None

    keys = sorted(table.keys())

    if nps in table:
        return nps, table[nps]

    # Below minimum
    if nps < keys[0]:
        # Only accept if within 50% of smallest entry
        if nps >= keys[0] * 0.5:
            return keys[0], table[keys[0]]
        return None, None

    # Above maximum
    if nps > keys[-1]:
        return None, None

    # Interpolate between two bracketing entries
    for i in range(len(keys) - 1):
        k1, k2 = keys[i], keys[i + 1]
        if k1 <= nps <= k2:
            v1, v2 = table[k1], table[k2]
            frac = (nps - k1) / (k2 - k1)
            if isinstance(v1, tuple):
                val = tuple(round(v1[j] + frac * (v2[j] - v1[j]), 2) for j in range(len(v1)))
            else:
                val = round(v1 + frac * (v2 - v1), 2)
            return nps, val

    return None, None


def _m_to_ft(metres: float) -> float:
    return round(metres * 3.28084, 1)


def get_thumb_rule(nps: float):
    """Department thumb rule for metallic pipes only. Returns metres or None."""
    if 1.0 <= nps <= 6.0:
        return round(3.5 + (nps - 1.0) * 0.5, 2)
    if 6.0 < nps <= 18.0:
        return round(6.5 + (nps - 8.0) * 0.25, 2)
    return None


def calculate_span(
    nps: float,
    material: str,
    service: str,
    insulation: str,
    code_preference: str = "b31_3",
    ss_schedule: str = "schedule_10s",
) -> dict:
    """
    Return max recommended support span for the given parameters.

    Parameters
    ----------
    nps            : Nominal pipe size (inches, float)
    material       : 'CS','LT','SA','SS','DS','SD','AL','AY','CN','FRP'
    service        : 'liquid' or 'vapor'
    insulation     : 'bare' or 'insulated'
    code_preference: 'b31_3' (default) or 'b31_1'
    ss_schedule    : 'schedule_10s' (default) or 'standard'

    Returns dict with keys:
        span_m, span_ft, reference, warning, message,
        thumb_rule_m, thumb_rule_ft, nps_used, table_used,
        chart_data  (list of [nps, span_m] for all table entries)
    """
    mat = material.upper().strip()
    svc = service.lower().strip()
    ins = insulation.lower().strip()

    out = {
        "span_m":        None,
        "span_ft":       None,
        "reference":     None,
        "warning":       None,
        "message":       None,
        "thumb_rule_m":  None,
        "thumb_rule_ft": None,
        "nps_used":      nps,
        "table_used":    None,
        "chart_data":    [],
    }

    # Thumb rule (metallic only)
    tr = get_thumb_rule(nps)
    if tr is not None and mat != "FRP":
        out["thumb_rule_m"]  = tr
        out["thumb_rule_ft"] = _m_to_ft(tr)

    # ── Non-metallic (not FRP) ────────────────────────────────────────────────
    if mat in ("HDPE", "PVC", "GRP", "PE", "PP", "PVDF"):
        out["message"] = (
            "Support span for non-metallic pipes must follow the pipe "
            "manufacturer's guidelines. This tool does not cover these materials."
        )
        return out

    # ── FRP / GRE — Table D ───────────────────────────────────────────────────
    if mat == "FRP":
        if nps > FRP_MAX_NPS:
            out["message"] = (
                f"FRP/GRE pipe NPS {nps}\u2033 is above NPS {int(FRP_MAX_NPS)}\u2033. "
                "Support span must be calculated case by case per ISO\u202014692 "
                "and manufacturer data."
            )
            return out
        key, val = _interp(TABLE_D, nps)
        if val is None:
            out["message"] = f"No standard span value for NPS\u00a0{nps}\u2033 FRP pipe."
            return out
        out["span_m"]     = val
        out["span_ft"]    = _m_to_ft(val)
        out["reference"]  = "ISO\u202014692 \u2014 FRP/GRE Piping (simplified)"
        out["warning"]    = (
            "FRP spans depend heavily on temperature, pressure, and "
            "manufacturer specification. Always verify with the pipe manufacturer."
        )
        out["table_used"] = "D"
        out["nps_used"]   = key
        out["chart_data"] = [[k, v] for k, v in sorted(TABLE_D.items())]
        return out

    # ── CS / LT / SA ─────────────────────────────────────────────────────────
    if mat in ("CS", "LT", "SA"):
        if code_preference == "b31_1":
            key, val = _interp(TABLE_A, nps)
            if val is None:
                out["message"] = (
                    f"No ASME\u00a0B31.1 span value for NPS\u00a0{nps}\u2033. "
                    "Use B31.3\u00a0/\u00a0Shell\u00a0DEP reference instead."
                )
                return out
            span_m = val[0] if svc == "liquid" else val[1]
            out["span_m"]     = span_m
            out["span_ft"]    = _m_to_ft(span_m)
            svc_lbl = "Water\u00a0/\u00a0Liquid" if svc == "liquid" else "Steam\u00a0/\u00a0Gas\u00a0/\u00a0Air"
            out["reference"]  = f"ASME\u00a0B31.1 Table\u00a0121.5 \u2014 {mat}, {svc_lbl}"
            out["warning"]    = (
                "ASME\u00a0B31.1 values do not distinguish insulation status. "
                "Apply engineering judgement for insulated lines."
            )
            out["table_used"] = "A"
            out["nps_used"]   = key
            col = 0 if svc == "liquid" else 1
            out["chart_data"] = [[k, v[col]] for k, v in sorted(TABLE_A.items())]
        else:
            key, val = _interp(TABLE_B, nps)
            if val is None:
                out["message"] = (
                    f"No standard span value for NPS\u00a0{nps}\u2033. "
                    "Stress analysis required."
                )
                return out
            col      = _COLS_B_C.get((svc, ins), 2)
            span_m   = val[col]
            out["span_m"]     = span_m
            out["span_ft"]    = _m_to_ft(span_m)
            svc_lbl  = "Liquid" if svc == "liquid" else "Vapor\u00a0/\u00a0Gas"
            ins_lbl  = "Insulated" if ins == "insulated" else "Bare"
            out["reference"]  = (
                f"ASME\u00a0B31.3\u00a0/\u00a0Shell\u00a0DEP \u2014 {mat}, "
                f"{svc_lbl}, {ins_lbl}"
            )
            out["table_used"] = "B"
            out["nps_used"]   = key
            out["chart_data"] = [[k, v[col]] for k, v in sorted(TABLE_B.items())]
        return out

    # ── SS / DS / SD ──────────────────────────────────────────────────────────
    if mat in ("SS", "DS", "SD"):
        table    = TABLE_C if ss_schedule == "schedule_10s" else TABLE_B
        sch_lbl  = "Schedule\u00a010S" if ss_schedule == "schedule_10s" else "Standard\u00a0/\u00a0Heavy\u00a0Wall"
        key, val = _interp(table, nps)
        if val is None:
            out["message"] = (
                f"No standard span value for NPS\u00a0{nps}\u2033 SS pipe."
            )
            return out
        col      = _COLS_B_C.get((svc, ins), 2)
        span_m   = val[col]
        out["span_m"]     = span_m
        out["span_ft"]    = _m_to_ft(span_m)
        svc_lbl  = "Liquid" if svc == "liquid" else "Vapor\u00a0/\u00a0Gas"
        ins_lbl  = "Insulated" if ins == "insulated" else "Bare"
        out["reference"]  = (
            f"ASME\u00a0B31.3 \u2014 {mat} {sch_lbl}, {svc_lbl}, {ins_lbl}"
        )
        out["table_used"] = "C" if ss_schedule == "schedule_10s" else "B"
        out["nps_used"]   = key
        out["chart_data"] = [[k, v[col]] for k, v in sorted(table.items())]
        return out

    # ── AL / AY / CN — approximate via SS Sch 10S × 0.85 ────────────────────
    if mat in ("AL", "AY", "CN"):
        key, val = _interp(TABLE_C, nps)
        if val is None:
            out["message"] = (
                f"No approximate span for NPS\u00a0{nps}\u2033 {mat}. "
                "Consult manufacturer or perform stress analysis."
            )
            return out
        col    = _COLS_B_C.get((svc, ins), 2)
        span_m = round(val[col] * 0.85, 2)
        out["span_m"]     = span_m
        out["span_ft"]    = _m_to_ft(span_m)
        svc_lbl = "Liquid" if svc == "liquid" else "Vapor\u00a0/\u00a0Gas"
        ins_lbl = "Insulated" if ins == "insulated" else "Bare"
        out["reference"]  = (
            f"Approximate \u2014 SS\u00a0basis \u00d7\u00a00.85 ({mat}), "
            f"{svc_lbl}, {ins_lbl}"
        )
        out["warning"]    = (
            f"{mat} span values are approximate. "
            "Verify with material-specific data or stress analysis."
        )
        out["table_used"] = "C-approx"
        out["nps_used"]   = key
        out["chart_data"] = [
            [k, round(v[col] * 0.85, 2)] for k, v in sorted(TABLE_C.items())
        ]
        return out

    # ── Unrecognised material ─────────────────────────────────────────────────
    out["message"] = (
        f"Material '{material}' is not covered by this calculator. "
        "Consult the stress engineer for applicable span values."
    )
    return out
