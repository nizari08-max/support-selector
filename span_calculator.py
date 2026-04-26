"""
span_calculator.py — Support Span Lookup Engine
Source: KS-PE-SPC-0073 Rev 0, 01 December 2019, Appendix A, Tables 13 & 14.
All internal span values are in feet (imperial); metre conversion happens at
the display layer only.  Do NOT change table values to metric.
"""

FT_TO_M       = 0.3048    # exact
LB_FT_TO_KG_M = 1.4882    # 1 lb/ft → kg/m
FRP_MAX_FT    = 20.0      # spec hard cap for FRP

# ── Table 13: CS, LT and SS Pipe Span ──────────────────────────────────────
# Key  : (nps_float, schedule_str)   schedule in {'sch40', 'sch80', '10s'}
# Value: 10-tuple
#   [0] empty_span_ft   [1] empty_wt_lb_ft
#   [2] water_span_ft   [3] water_wt_lb_ft
#   [4] ins_vap_t1      [5] ins_vap_t2      [6] ins_vap_t3
#   [7] ins_liq_t1      [8] ins_liq_t2      [9] ins_liq_t3
#
# Temperature bands (from spec, converted to °C for display only):
#   t1 = up to 347 °F  (≤ 175 °C)
#   t2 = 348–599 °F    (176–315 °C)
#   t3 = 600–752 °F    (316–400 °C)
#
# LT (Low Temperature CS) shares identical values with CS — handled in logic.

TABLE_13 = {
    # ── SCH 40 ─────────────────────────────────────────────────────────────
    (0.75, 'sch40'): (13, 1.1,  11, 1.3,   10, 8,  8,  10, 8,  8),
    (1.0,  'sch40'): (15, 1.7,  13, 2.0,   11, 10, 10, 11, 10, 8),
    (1.5,  'sch40'): (18, 2.7,  16, 3.6,   15, 11, 11, 15, 11, 11),
    (2.0,  'sch40'): (20, 3.7,  18, 5.1,   18, 15, 13, 16, 13, 11),
    (2.5,  'sch40'): (21, 5.8,  20, 7.9,   20, 16, 15, 18, 15, 15),
    (3.0,  'sch40'): (24, 7.6,  21, 10.8,  23, 18, 18, 21, 16, 16),
    (4.0,  'sch40'): (28, 10.8, 24, 16.4,  26, 21, 20, 23, 20, 18),
    (6.0,  'sch40'): (34, 19.0, 29, 31.3,  33, 26, 24, 29, 23, 23),
    (8.0,  'sch40'): (39, 28.7, 33, 50.5,  38, 29, 29, 33, 26, 26),
    (10.0, 'sch40'): (44, 40.8, 38, 75.1,  42, 34, 33, 36, 29, 29),
    (12.0, 'sch40'): (49, 50.0, 39, 99.1,  46, 38, 36, 39, 31, 31),
    (14.0, 'sch40'): (51, 55.4, 41, 115.6, 47, 39, 38, 39, 33, 33),
    (16.0, 'sch40'): (54, 63.5, 42, 143.2, 52, 42, 41, 42, 34, 34),
    (18.0, 'sch40'): (57, 71.5, 44, 173.5, 56, 44, 44, 44, 36, 36),
    (20.0, 'sch40'): (60, 79.6, 46, 206.6, 57, 47, 46, 46, 38, 36),
    (24.0, 'sch40'): (67, 95.7, 49, 281.0, 64, 52, 51, 47, 41, 39),
    # ── SCH 80 ─────────────────────────────────────────────────────────────
    (0.75, 'sch80'): (13, 1.4,  11, 1.6,   10, 8,  8,  10, 8,  8),
    (1.0,  'sch80'): (15, 2.2,  13, 2.4,   11, 10, 10, 11, 10, 10),
    (1.5,  'sch80'): (18, 3.7,  16, 4.4,   15, 11, 11, 15, 11, 11),
    (2.0,  'sch80'): (20, 5.0,  18, 6.3,   18, 15, 13, 16, 13, 13),
    (2.5,  'sch80'): (21, 7.7,  21, 9.6,   20, 16, 16, 20, 15, 15),
    (3.0,  'sch80'): (24, 10.3, 23, 13.2,  23, 18, 18, 21, 16, 16),
    (4.0,  'sch80'): (28, 15.1, 26, 20.0,  26, 21, 20, 24, 20, 20),
    (6.0,  'sch80'): (34, 28.8, 31, 40.2,  33, 26, 26, 29, 24, 23),
    (8.0,  'sch80'): (39, 43.7, 36, 63.7,  38, 29, 29, 34, 28, 26),
    (10.0, 'sch80'): (44, 55.2, 39, 87.8,  42, 34, 33, 38, 31, 29),
    (12.0, 'sch80'): (47, 65.9, 42, 113.2, 46, 38, 36, 41, 33, 33),
    (14.0, 'sch80'): (51, 72.7, 44, 130.6, 49, 39, 38, 42, 34, 33),
    (16.0, 'sch80'): (54, 83.4, 46, 161.2, 52, 42, 41, 44, 36, 34),
    (18.0, 'sch80'): (57, 94.2, 47, 192.5, 56, 44, 44, 46, 38, 36),
    (20.0, 'sch80'): (60, 105.8, 49, 229.6, 59, 47, 46, 49, 39, 38),
    (24.0, 'sch80'): (67, 126.5, 52, 308.0, 64, 52, 51, 52, 42, 41),
    # ── 10S ────────────────────────────────────────────────────────────────
    (0.75, '10s'): (13, 0.8,  11, 1.1,   8,  8,  8,  8,  8,  8),
    (1.0,  '10s'): (15, 1.4,  13, 1.8,   11, 10, 10, 11, 10, 8),
    (1.5,  '10s'): (18, 2.0,  16, 3.0,   15, 15, 11, 13, 13, 10),
    (2.0,  '10s'): (20, 2.6,  18, 4.2,   16, 15, 11, 15, 13, 10),
    (2.5,  '10s'): (23, 3.5,  20, 5.9,   20, 18, 15, 18, 16, 15),
    (3.0,  '10s'): (24, 4.3,  21, 8.0,   21, 20, 16, 20, 18, 16),
    (4.0,  '10s'): (26, 5.5,  23, 11.8,  24, 23, 20, 21, 20, 20),
    (6.0,  '10s'): (33, 9.2,  28, 23.1,  31, 29, 26, 24, 23, 23),
    (8.0,  '10s'): (38, 13.3, 29, 37.2,  36, 34, 33, 28, 24, 24),
    (10.0, '10s'): (42, 18.6, 31, 56.0,  41, 39, 36, 29, 28, 26),
    (12.0, '10s'): (47, 24.1, 34, 77.0,  44, 42, 39, 33, 29, 29),
    (14.0, '10s'): (51, 27.6, 34, 89.1,  47, 46, 42, 33, 31, 29),
    (16.0, '10s'): (54, 31.7, 36, 115.7, 51, 47, 46, 34, 31, 31),
    (18.0, '10s'): (57, 35.7, 36, 142.5, 54, 51, 47, 34, 33, 31),
    (20.0, '10s'): (60, 46.0, 39, 177.7, 57, 54, 51, 38, 34, 33),
    (24.0, '10s'): (67, 63.4, 42, 253.2, 62, 59, 56, 41, 38, 36),
}

# ── Table 14: DS / SD / AS / AL / AY / TI / CN / FRP Pipe Span ─────────────
# Single span value (ft) for both vapor and liquid.  No temperature bands.
# Key  : nps_float
# Value: (ds_sd_ft, as_ay_al_ft, ti_ft, cn_ft, frp_ft)
# None  = not applicable for that size (shown as "–" in spec).

TABLE_14 = {
    0.75: (11,   10,   8,    6,    None),
    1.0:  (13,   12,   10,   7,    10),
    1.5:  (16,   16,   13,   10,   11),
    2.0:  (18,   18,   15,   11,   12),
    2.5:  (19,   19,   19,   13,   None),
    3.0:  (19,   19,   19,   14,   13),
    4.0:  (19,   19,   19,   16,   14),
    6.0:  (19,   19,   19,   19,   16),
    8.0:  (19,   19,   19,   19,   18),
    10.0: (19,   19,   19,   19,   19),
    12.0: (19,   19,   19,   19,   19),
    14.0: (26,   26,   26,   19,   19),
    16.0: (26,   26,   26,   26,   19),
    18.0: (26,   26,   26,   26,   19),
    20.0: (26,   26,   26,   26,   19),
    22.0: (26,   26,   26,   26,   19),
    24.0: (26,   26,   26,   26,   19),
}

# Map material code → column index in TABLE_14 tuple
_T14_COL = {
    'DS': 0, 'SD': 0,
    'AS': 1, 'AL': 1, 'AY': 1,
    'TI': 2,
    'CN': 3,
    'FRP': 4,
}

# Tuple-index → condition meaning for TABLE_13
_T13_IDX = {
    'bare_empty':  0,
    'bare_water':  2,
    'ins_vapor':   {'t1': 4, 't2': 5, 't3': 6},
    'ins_liquid':  {'t1': 7, 't2': 8, 't3': 9},
}


# ── Conversion helpers ───────────────────────────────────────────────────────

def _ft_to_m(ft: float) -> float:
    return round(ft * FT_TO_M, 1)


def _kg_m(lb_ft: float) -> float:
    return round(lb_ft * LB_FT_TO_KG_M, 1)


def _nearest_key(keys: list, nps: float) -> float:
    """Return the nearest key to *nps* from a sorted list."""
    return min(keys, key=lambda k: abs(k - nps))


# ── Public API ───────────────────────────────────────────────────────────────

def calculate_span(
    nps: float,
    material: str,
    condition: str = 'bare_empty',
    schedule: str  = 'sch40',
    temp_range: str = 't1',
) -> dict:
    """
    Return maximum recommended support span from KS-PE-SPC-0073 Appendix A.

    Parameters
    ----------
    nps        : Nominal pipe size in inches (float).
    material   : Material code — one of:
                   Table 13: 'CS', 'LT', 'SS'
                   Table 14: 'DS', 'SD', 'AS', 'AL', 'AY', 'TI', 'CN', 'FRP'
    condition  : 'bare_empty' | 'bare_water' | 'ins_vapor' | 'ins_liquid'
                 (Table 14 materials use a single span; condition is informational.)
    schedule   : 'sch40' | 'sch80' | '10s'
                 Only used for Table 13 materials (CS / LT / SS).
    temp_range : 't1' | 't2' | 't3'
                 t1 = ≤175 °C (≤347 °F)
                 t2 = 176–315 °C (348–599 °F)
                 t3 = 316–400 °C (600–752 °F)
                 Only used for insulated conditions with Table 13 materials.

    Returns
    -------
    dict with keys:
        span_m, span_ft,
        weight_kg_m, weight_lb_ft   (bare pipe only; None for insulated)
        reference, warning, message,
        nps_used, schedule_used,
        chart_data                  (list of [nps, span_m])
    """
    mat  = material.upper().strip()
    cond = condition.lower().strip()
    sch  = schedule.lower().strip()
    tr   = temp_range.lower().strip()

    out = {
        'span_m':        None,
        'span_ft':       None,
        'weight_kg_m':   None,
        'weight_lb_ft':  None,
        'reference':     'KS-PE-SPC-0073 Rev 0, Appendix A',
        'warning':       None,
        'message':       None,
        'nps_used':      nps,
        'schedule_used': sch,
        'chart_data':    [],
    }

    # ── TABLE 14 materials ───────────────────────────────────────────────────
    if mat in _T14_COL:
        col    = _T14_COL[mat]
        keys14 = sorted(TABLE_14.keys())
        nps_k  = _nearest_key(keys14, nps)
        row    = TABLE_14[nps_k]
        val    = row[col]

        if val is None:
            out['message'] = (
                f'NPS {nps}" is not listed for {mat} in Table 14 '
                f'(KS-PE-SPC-0073). Consult the stress engineer.'
            )
            return out

        span_ft = min(float(val), FRP_MAX_FT) if mat == 'FRP' else float(val)
        out['span_ft']  = span_ft
        out['span_m']   = _ft_to_m(span_ft)
        out['nps_used'] = nps_k

        grp_label = {
            'DS': 'DS / SD', 'SD': 'DS / SD',
            'AS': 'AS / AY / AL', 'AL': 'AS / AY / AL', 'AY': 'AS / AY / AL',
            'TI': 'TI', 'CN': 'CN', 'FRP': 'FRP',
        }[mat]
        out['reference'] = (
            f'KS-PE-SPC-0073 Table 14 — {grp_label}, '
            f'Vapor / Liquid (single span), NPS {nps_k}"'
        )

        if mat == 'FRP':
            out['warning'] = (
                'FRP spans are capped at 6.1 m (20 ft) per spec. '
                'Verify with manufacturer data — Fiberbond 20FR16 basis, '
                '1000 psi allowable stress.'
            )

        out['chart_data'] = [
            [k, _ft_to_m(v[col])]
            for k, v in sorted(TABLE_14.items())
            if v[col] is not None
        ]
        return out

    # ── TABLE 13 materials: CS / LT / SS ────────────────────────────────────
    if mat in ('CS', 'LT', 'SS'):
        keys13 = sorted({k[0] for k in TABLE_13 if k[1] == sch})
        if not keys13:
            out['message'] = f"Schedule '{schedule}' not found in Table 13."
            return out

        nps_k = _nearest_key(keys13, nps)
        row   = TABLE_13.get((nps_k, sch))
        if row is None:
            out['message'] = (
                f'No data for NPS {nps}" {mat} {schedule} in Table 13.'
            )
            return out

        (empty_span, empty_wt, water_span, water_wt,
         vap_t1, vap_t2, vap_t3,
         liq_t1, liq_t2, liq_t3) = row

        if cond == 'bare_empty':
            span_ft = empty_span
            wt_lb   = empty_wt
        elif cond == 'bare_water':
            span_ft = water_span
            wt_lb   = water_wt
        elif cond == 'ins_vapor':
            span_ft = {'t1': vap_t1, 't2': vap_t2, 't3': vap_t3}.get(tr, vap_t1)
            wt_lb   = None
        elif cond == 'ins_liquid':
            span_ft = {'t1': liq_t1, 't2': liq_t2, 't3': liq_t3}.get(tr, liq_t1)
            wt_lb   = None
        else:
            out['message'] = f"Unknown condition '{condition}'."
            return out

        out['span_ft']      = float(span_ft)
        out['span_m']       = _ft_to_m(float(span_ft))
        out['weight_lb_ft'] = wt_lb
        out['weight_kg_m']  = _kg_m(wt_lb) if wt_lb is not None else None
        out['nps_used']     = nps_k
        out['schedule_used'] = sch

        cond_lbl = {
            'bare_empty':  'Bare Pipe — Empty',
            'bare_water':  'Bare Pipe — Water Filled',
            'ins_vapor':   'Insulated — Vapor Filled',
            'ins_liquid':  'Insulated — Liquid Filled',
        }.get(cond, cond)

        temp_lbl = ''
        if cond in ('ins_vapor', 'ins_liquid'):
            temp_lbl = {
                't1': ', ≤175°C (≤347°F)',
                't2': ', 176–315°C (348–599°F)',
                't3': ', 316–400°C (600–752°F)',
            }.get(tr, '')

        sch_lbl = {'sch40': 'SCH 40', 'sch80': 'SCH 80', '10s': '10S'}.get(sch, sch)
        out['reference'] = (
            f'KS-PE-SPC-0073 Table 13 — {mat}, {sch_lbl}, '
            f'{cond_lbl}{temp_lbl}, NPS {nps_k}"'
        )

        if mat == 'LT':
            out['warning'] = (
                'Low Temperature Carbon Steel (LT) uses the same span values '
                'as Carbon Steel (CS) per KS-PE-SPC-0073.'
            )

        # Chart: same schedule, same condition/temp, all NPS sizes
        col_idx = _T13_IDX.get(cond)
        if isinstance(col_idx, dict):
            col_idx = col_idx.get(tr, list(col_idx.values())[0])

        out['chart_data'] = [
            [k[0], _ft_to_m(TABLE_13[k][col_idx])]
            for k in sorted(TABLE_13.keys())
            if k[1] == sch
        ]
        return out

    # ── Unrecognised material ────────────────────────────────────────────────
    out['message'] = (
        f"Material '{material}' is not covered by KS-PE-SPC-0073 Tables 13–14. "
        'Consult the stress engineer.'
    )
    return out
