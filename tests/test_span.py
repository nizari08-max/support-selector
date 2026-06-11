"""
Tests for the support span calculator (span_calculator.py).

Coverage:
  - Table 13 (CS, LT, SS): bare-empty, bare-water, insulated-vapor,
    insulated-liquid; schedules sch40, sch80, 10s; all temperature bands
  - Table 14 (DS, AL, CN, FRP): representative sizes
  - Nearest-key interpolation for non-standard NPS values
  - LT warning behavior (uses CS values)
  - FRP cap and warning (≤ 20 ft)
  - Unknown material handling
  - Chart data structure
"""

import pytest
from span_calculator import calculate_span, FT_TO_M, TABLE_13, TABLE_14


# ── helpers ──────────────────────────────────────────────────────────────────

def ft_to_m(ft):
    """Replicate the _ft_to_m helper: round(ft * 0.3048, 1)."""
    return round(ft * FT_TO_M, 1)


# =============================================================================
# TABLE 13 — CS / LT / SS
# =============================================================================

class TestTable13CS:

    def test_cs_sch40_bare_empty_nps2(self):
        r = calculate_span(2.0, "CS", "bare_empty", "sch40")
        assert r["span_ft"]  == 20.0
        assert r["span_m"]   == ft_to_m(20)        # 6.1
        assert r["nps_used"] == 2.0
        assert r["warning"]  is None

    def test_cs_sch40_bare_empty_nps6(self):
        r = calculate_span(6.0, "CS", "bare_empty", "sch40")
        assert r["span_ft"] == 34.0
        assert r["span_m"]  == ft_to_m(34)         # 10.4

    def test_cs_sch40_bare_empty_nps12(self):
        r = calculate_span(12.0, "CS", "bare_empty", "sch40")
        assert r["span_ft"] == 49.0
        assert r["span_m"]  == ft_to_m(49)         # 14.9

    def test_cs_sch40_bare_empty_nps24(self):
        r = calculate_span(24.0, "CS", "bare_empty", "sch40")
        assert r["span_ft"] == 67.0
        assert r["span_m"]  == ft_to_m(67)         # 20.4

    def test_cs_sch80_bare_empty_nps6(self):
        r = calculate_span(6.0, "CS", "bare_empty", "sch80")
        assert r["span_ft"] == 34.0
        assert r["schedule_used"] == "sch80"

    def test_cs_sch40_bare_water_nps6(self):
        r = calculate_span(6.0, "CS", "bare_water", "sch40")
        # TABLE_13[(6.0,'sch40')][2] = 29
        assert r["span_ft"] == 29.0
        assert r["span_m"]  == ft_to_m(29)         # 8.8

    def test_cs_sch40_ins_vapor_t1_nps6(self):
        r = calculate_span(6.0, "CS", "ins_vapor", "sch40", "t1")
        # TABLE_13[(6.0,'sch40')][4] = 33
        assert r["span_ft"] == 33.0

    def test_cs_sch40_ins_vapor_t2_nps6(self):
        r = calculate_span(6.0, "CS", "ins_vapor", "sch40", "t2")
        # TABLE_13[(6.0,'sch40')][5] = 26
        assert r["span_ft"] == 26.0
        assert r["span_m"]  == ft_to_m(26)         # 7.9

    def test_cs_sch40_ins_vapor_t3_nps6(self):
        r = calculate_span(6.0, "CS", "ins_vapor", "sch40", "t3")
        # TABLE_13[(6.0,'sch40')][6] = 24
        assert r["span_ft"] == 24.0
        assert r["span_m"]  == ft_to_m(24)         # 7.3

    def test_cs_sch40_ins_liquid_t3_nps8(self):
        r = calculate_span(8.0, "CS", "ins_liquid", "sch40", "t3")
        # TABLE_13[(8.0,'sch40')][9] = 26
        assert r["span_ft"] == 26.0
        assert r["span_m"]  == ft_to_m(26)         # 7.9

    def test_cs_weight_populated_for_bare_pipe(self):
        r = calculate_span(6.0, "CS", "bare_empty", "sch40")
        assert r["weight_lb_ft"] == 19.0
        assert r["weight_kg_m"]  == round(19.0 * 1.4882, 1)  # 28.3

    def test_cs_weight_none_for_insulated(self):
        r = calculate_span(6.0, "CS", "ins_vapor", "sch40", "t1")
        assert r["weight_lb_ft"] is None
        assert r["weight_kg_m"]  is None

    def test_cs_reference_string_contains_table13(self):
        r = calculate_span(6.0, "CS", "bare_empty", "sch40")
        # Reference may use non-breaking spaces (\xa0), so check component words
        assert "Table" in r["reference"] and "13" in r["reference"]

    def test_cs_chart_data_is_list_of_nps_span_pairs(self):
        r = calculate_span(6.0, "CS", "bare_empty", "sch40")
        assert isinstance(r["chart_data"], list)
        assert len(r["chart_data"]) > 0
        for entry in r["chart_data"]:
            assert len(entry) == 2
            nps_val, span_m = entry
            assert span_m > 0

    def test_cs_10s_schedule(self):
        r = calculate_span(4.0, "CS", "bare_empty", "10s")
        # TABLE_13[(4.0,'10s')][0] = 26
        assert r["span_ft"] == 26.0
        assert r["schedule_used"] == "10s"


class TestTable13LT:

    def test_lt_same_span_as_cs(self):
        """LT uses the same Table 13 values as CS."""
        r_cs = calculate_span(6.0, "CS", "bare_empty", "sch40")
        r_lt = calculate_span(6.0, "LT", "bare_empty", "sch40")
        assert r_lt["span_ft"] == r_cs["span_ft"]
        assert r_lt["span_m"]  == r_cs["span_m"]

    def test_lt_has_warning(self):
        r = calculate_span(6.0, "LT", "bare_empty", "sch40")
        assert r["warning"] is not None
        assert "Low Temperature" in r["warning"] or "LT" in r["warning"]


class TestTable13SS:

    def test_ss_10s_bare_empty_nps4(self):
        r = calculate_span(4.0, "SS", "bare_empty", "10s")
        # TABLE_13[(4.0,'10s')][0] = 26
        assert r["span_ft"] == 26.0
        assert r["span_m"]  == ft_to_m(26)         # 7.9

    def test_ss_10s_bare_empty_nps12(self):
        r = calculate_span(12.0, "SS", "bare_empty", "10s")
        # TABLE_13[(12.0,'10s')][0] = 47
        assert r["span_ft"] == 47.0

    def test_ss_sch40_bare_empty_nps8(self):
        r = calculate_span(8.0, "SS", "bare_empty", "sch40")
        # TABLE_13[(8.0,'sch40')][0] = 39
        assert r["span_ft"] == 39.0

    def test_ss_no_warning(self):
        r = calculate_span(6.0, "SS", "bare_empty", "10s")
        assert r["warning"] is None


# =============================================================================
# TABLE 14 — DS / SD / AL / AY / CN / FRP
# =============================================================================

class TestTable14DS:

    def test_ds_nps8(self):
        r = calculate_span(8.0, "DS")
        # TABLE_14[8.0][0] = 19
        assert r["span_ft"] == 19.0
        assert r["span_m"]  == ft_to_m(19)         # 5.8

    def test_ds_nps14_large(self):
        r = calculate_span(14.0, "DS")
        # TABLE_14[14.0][0] = 26
        assert r["span_ft"] == 26.0
        assert r["span_m"]  == ft_to_m(26)         # 7.9

    def test_sd_same_column_as_ds(self):
        r_ds = calculate_span(8.0, "DS")
        r_sd = calculate_span(8.0, "SD")
        assert r_ds["span_ft"] == r_sd["span_ft"]

    def test_ds_reference_string_contains_table14(self):
        r = calculate_span(8.0, "DS")
        # Reference may use non-breaking spaces (\xa0), so check component words
        assert "Table" in r["reference"] and "14" in r["reference"]


class TestTable14AL:

    def test_al_nps4(self):
        r = calculate_span(4.0, "AL")
        # TABLE_14[4.0][1] = 19
        assert r["span_ft"] == 19.0
        assert r["span_m"]  == ft_to_m(19)

    def test_al_nps1(self):
        r = calculate_span(1.0, "AL")
        # TABLE_14[1.0][1] = 12
        assert r["span_ft"] == 12.0

    def test_ay_same_as_al(self):
        r_al = calculate_span(4.0, "AL")
        r_ay = calculate_span(4.0, "AY")
        assert r_al["span_ft"] == r_ay["span_ft"]


class TestTable14CN:

    def test_cn_nps4(self):
        r = calculate_span(4.0, "CN")
        # TABLE_14[4.0][3] = 16
        assert r["span_ft"] == 16.0
        assert r["span_m"]  == ft_to_m(16)         # 4.9

    def test_cn_nps6(self):
        r = calculate_span(6.0, "CN")
        # TABLE_14[6.0][3] = 19
        assert r["span_ft"] == 19.0


class TestTable14FRP:

    def test_frp_nps4(self):
        r = calculate_span(4.0, "FRP")
        # TABLE_14[4.0][4] = 14
        assert r["span_ft"] == 14.0
        assert r["span_m"]  == ft_to_m(14)         # 4.3

    def test_frp_nps8(self):
        r = calculate_span(8.0, "FRP")
        # TABLE_14[8.0][4] = 18 — below 20ft cap
        assert r["span_ft"] == 18.0

    def test_frp_nps10_approaches_cap(self):
        r = calculate_span(10.0, "FRP")
        # TABLE_14[10.0][4] = 19 — below 20ft cap
        assert r["span_ft"] == 19.0

    def test_frp_always_has_warning(self):
        r = calculate_span(4.0, "FRP")
        assert r["warning"] is not None
        assert "20" in r["warning"] or "FRP" in r["warning"]

    def test_frp_nps075_not_applicable_returns_message(self):
        r = calculate_span(0.75, "FRP")
        assert r["span_ft"]  is None
        assert r["message"]  is not None
        assert "0.75" in r["message"]

    def test_frp_nps25_not_applicable(self):
        # TABLE_14[2.5][4] = None
        r = calculate_span(2.5, "FRP")
        assert r["span_ft"] is None
        assert r["message"] is not None

    def test_frp_chart_data_excludes_none_entries(self):
        r = calculate_span(4.0, "FRP")
        for entry in r["chart_data"]:
            assert entry[1] is not None


# =============================================================================
# NEAREST-KEY INTERPOLATION
# =============================================================================

class TestNearestKey:

    def test_cs_nps5_uses_nps4_data(self):
        # NPS 5" is equidistant from 4" and 6"; Python's min() picks 4.0
        r = calculate_span(5.0, "CS", "bare_empty", "sch40")
        assert r["nps_used"] == 4.0
        assert r["span_ft"]  == TABLE_13[(4.0, "sch40")][0]

    def test_cs_nps3point5_uses_nps3_or_nps4(self):
        # |3.5-3.0|=0.5, |3.5-4.0|=0.5 → tie, min picks 3.0 (first in sorted list)
        r = calculate_span(3.5, "CS", "bare_empty", "sch40")
        assert r["nps_used"] in (3.0, 4.0)

    def test_ds_nps5_uses_nps4_or_nps6(self):
        r = calculate_span(5.0, "DS")
        assert r["nps_used"] in (4.0, 6.0)

    def test_nps_exactly_in_table_uses_exact_key(self):
        r = calculate_span(12.0, "CS", "bare_empty", "sch40")
        assert r["nps_used"] == 12.0


# =============================================================================
# UNKNOWN / UNSUPPORTED MATERIALS
# =============================================================================

class TestUnknownMaterial:

    def test_unrecognised_material_returns_message(self):
        r = calculate_span(4.0, "XX")
        assert r["span_ft"] is None
        assert r["span_m"]  is None
        assert r["message"] is not None

    def test_unrecognised_material_no_exception(self):
        # Must return gracefully without raising
        r = calculate_span(4.0, "TITANIUM")
        assert r["span_ft"] is None

    def test_unknown_condition_returns_message(self):
        r = calculate_span(6.0, "CS", "hot_vapor", "sch40")
        assert r["span_ft"] is None
        assert r["message"] is not None


# =============================================================================
# RESULT STRUCTURE
# =============================================================================

class TestResultStructure:

    def test_all_keys_present_for_table13(self):
        r = calculate_span(6.0, "CS", "bare_empty", "sch40")
        for key in ("span_m", "span_ft", "weight_kg_m", "weight_lb_ft",
                    "reference", "warning", "message",
                    "nps_used", "schedule_used", "chart_data"):
            assert key in r, f"Missing key: {key}"

    def test_all_keys_present_for_table14(self):
        r = calculate_span(6.0, "DS")
        for key in ("span_m", "span_ft", "weight_kg_m", "weight_lb_ft",
                    "reference", "warning", "message",
                    "nps_used", "schedule_used", "chart_data"):
            assert key in r, f"Missing key: {key}"

    def test_reference_always_populated(self):
        for mat in ("CS", "DS", "FRP", "AL"):
            r = calculate_span(4.0, mat, "bare_empty", "sch40")
            assert r["reference"] is not None and len(r["reference"]) > 5
