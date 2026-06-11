"""
Tests for the support selector (selector.py + support_rules.py + note_refinement.py).

Coverage:
  - Input normalizers (get_size_range, normalize_material, normalize_insulation,
    normalize_function)
  - REST selections: complete cases, refinement-triggering cases, full refinement
    resolution
  - GUIDE, LINE STOP, HOLD DOWN selections
  - FRP special-case handling (all four functions)
  - Edge / validation cases
  - Removed obsolete codes (SC09, CF04) confirmed absent
"""

import pytest
from selector import (
    select_support,
    get_size_range,
    normalize_material,
    normalize_insulation,
    normalize_function,
)


# =============================================================================
# SIZE-RANGE HELPER
# =============================================================================

class TestGetSizeRange:

    # ── TABLE 15 (REST) ──────────────────────────────────────────────────────

    @pytest.mark.parametrize("nps,expected", [
        (0.5,  "0.5_to_1"),
        (0.75, "0.5_to_1"),
        (1.0,  "0.5_to_1"),
        (1.5,  "1.5"),
        (2.0,  "2_to_16"),
        (10.0, "2_to_16"),
        (16.0, "2_to_16"),
        (18.0, "18_to_24"),
        (24.0, "18_to_24"),
        (26.0, "26_to_30"),
        (30.0, "26_to_30"),
        (32.0, "32_to_48"),
        (48.0, "32_to_48"),
    ])
    def test_rest_ranges(self, nps, expected):
        assert get_size_range(nps, "rest") == expected

    # ── TABLE 16 (GUIDE / LINE STOP / HOLD DOWN) ─────────────────────────────

    @pytest.mark.parametrize("nps,expected", [
        (0.5,  "0.5_to_1"),
        (1.0,  "0.5_to_1"),
        (1.5,  "1.5_to_6"),
        (6.0,  "1.5_to_6"),
        (8.0,  "8_to_10"),
        (10.0, "8_to_10"),
        (12.0, "12_to_48"),
        (48.0, "12_to_48"),
    ])
    def test_guide_ranges(self, nps, expected):
        assert get_size_range(nps, "guide") == expected

    def test_below_minimum_raises(self):
        with pytest.raises(ValueError, match="minimum"):
            get_size_range(0.4, "rest")

    def test_above_maximum_raises(self):
        with pytest.raises(ValueError, match="maximum"):
            get_size_range(49.0, "rest")


# =============================================================================
# NORMALIZERS
# =============================================================================

class TestNormalizeMaterial:

    @pytest.mark.parametrize("raw,expected", [
        ("cs",         "cs_lt"),
        ("CS",         "cs_lt"),
        ("LT",         "cs_lt"),
        ("lt",         "cs_lt"),
        ("SS",         "ss_ds_sd_sa"),
        ("DS",         "ss_ds_sd_sa"),
        ("sd",         "ss_ds_sd_sa"),
        ("SA",         "ss_ds_sd_sa"),
        ("AL",         "al_ay_cn"),
        ("ay",         "al_ay_cn"),
        ("CN",         "al_ay_cn"),
        ("aluminum",   "al_ay_cn"),
        ("FRP",        "frp"),
        ("frp",        "frp"),
        ("fiberglass", "frp"),
    ])
    def test_known_aliases(self, raw, expected):
        assert normalize_material(raw) == expected

    def test_unknown_material_raises(self):
        with pytest.raises(ValueError, match="Unknown material"):
            normalize_material("XX")


class TestNormalizeInsulation:

    @pytest.mark.parametrize("raw,expected", [
        ("uninsulated",   "uninsulated"),
        ("bare",          "uninsulated"),
        ("none",          "uninsulated"),
        ("hot_insulated", "hot_insulated"),
        ("insulated",     "hot_insulated"),
        ("hot",           "hot_insulated"),
    ])
    def test_known_values(self, raw, expected):
        assert normalize_insulation(raw) == expected

    def test_unknown_raises(self):
        with pytest.raises(ValueError, match="Unknown insulation"):
            normalize_insulation("warm")


class TestNormalizeFunction:

    @pytest.mark.parametrize("raw,expected", [
        ("rest",      "rest"),
        ("GUIDE",     "guide"),
        ("line_stop", "line_stop"),
        ("LINE STOP", "line_stop"),
        ("hold_down", "hold_down"),
        ("HOLD DOWN", "hold_down"),
    ])
    def test_known_values(self, raw, expected):
        assert normalize_function(raw) == expected

    def test_unknown_raises(self):
        with pytest.raises(ValueError, match="Unknown support function"):
            normalize_function("anchor")


# =============================================================================
# REST — COMPLETE CASES (no refinement questions)
# =============================================================================

class TestRestComplete:
    """
    Cases where select_support returns status='complete' with no refinement questions.
    These are the simplest, most deterministic paths through the rules table.
    """

    def test_cs_small_bore_uninsulated(self):
        r = select_support(1.0, "CS", False, "uninsulated", "rest")
        assert r.support_code == "DIRECT REST"
        assert r.status == "complete"
        assert r.notes == []

    def test_cs_half_inch_uninsulated(self):
        r = select_support(0.5, "CS", False, "uninsulated", "rest")
        assert r.support_code == "DIRECT REST"
        assert r.status == "complete"

    def test_ss_half_inch_uninsulated(self):
        r = select_support(1.0, "SS", False, "uninsulated", "rest")
        assert r.support_code == "BEARING PLATE (BP02)"
        assert r.status == "complete"
        assert r.notes == []

    def test_al_half_inch_uninsulated(self):
        r = select_support(0.75, "AL", False, "uninsulated", "rest")
        assert r.support_code == "BEARING PLATE (BP02)"
        assert r.status == "complete"

    def test_cs_large_bore_uninsulated_has_wear_pad(self):
        # NPS 18–24: CS no PWHT uninsulated → WEAR PAD (WA01)
        r = select_support(18.0, "CS", False, "uninsulated", "rest")
        assert r.support_code == "WEAR PAD (WA01)"
        assert r.status == "complete"
        assert 1 in r.notes
        assert 2 in r.notes

    def test_cs_24_inch_uninsulated(self):
        r = select_support(24.0, "CS", False, "uninsulated", "rest")
        assert r.support_code == "WEAR PAD (WA01)"
        assert r.status == "complete"

    def test_cs_hot_insulated_straight_small_bore(self):
        r = select_support(2.0, "CS", False, "hot_insulated", "rest",
                           {"pipe_orientation": "straight"})
        assert r.support_code == "WELDED SHOE (SH01)"
        assert r.status == "complete"

    def test_cs_hot_insulated_sloping_small_bore(self):
        # NPS ≤ 4 sloping → SH04
        r = select_support(2.0, "CS", False, "hot_insulated", "rest",
                           {"pipe_orientation": "sloping"})
        assert r.support_code == "WELDED SHOE (SH04)"
        assert r.status == "complete"

    def test_cs_hot_insulated_sloping_large_bore(self):
        # NPS > 4 sloping → SH05
        r = select_support(6.0, "CS", False, "hot_insulated", "rest",
                           {"pipe_orientation": "sloping"})
        assert r.support_code == "WELDED SHOE (SH05)"
        assert r.status == "complete"

    def test_cs_pwht_axial_stop_straight(self):
        # Axial stop location → must use welded shoe
        r = select_support(4.0, "CS", True, "hot_insulated", "rest",
                           {"is_axial_stop_location": "true",
                            "pipe_orientation": "straight"})
        assert "SH01" in r.support_code
        assert "WA01" in r.support_code
        assert r.status == "complete"

    def test_cs_pwht_no_axial_stop_straight(self):
        # Non-axial-stop → clamped shoe SC01
        r = select_support(4.0, "CS", True, "hot_insulated", "rest",
                           {"is_axial_stop_location": "false",
                            "pipe_orientation": "straight"})
        assert "SC01" in r.support_code
        assert r.status == "complete"

    def test_cs_pwht_no_axial_stop_sloping(self):
        # Non-axial-stop sloping → SC05
        r = select_support(4.0, "CS", True, "hot_insulated", "rest",
                           {"is_axial_stop_location": "false",
                            "pipe_orientation": "sloping"})
        assert "SC05" in r.support_code
        assert r.status == "complete"


# =============================================================================
# REST — NEEDS REFINEMENT (triggers questions without answers)
# =============================================================================

class TestRestNeedsRefinement:

    def test_cs_hot_insulated_asks_orientation(self):
        r = select_support(2.0, "CS", False, "hot_insulated", "rest")
        assert r.status == "needs_refinement"
        question_ids = [q["id"] for q in r.refinement_questions]
        assert "pipe_orientation" in question_ids

    def test_cs_pwht_hot_insulated_asks_axial_stop(self):
        r = select_support(4.0, "CS", True, "hot_insulated", "rest")
        assert r.status == "needs_refinement"
        question_ids = [q["id"] for q in r.refinement_questions]
        assert "is_axial_stop_location" in question_ids

    def test_ss_uninsulated_small_bore_asks_wall_schedule(self):
        # NPS 1.5–24 SS uninsulated → needs wall schedule
        r = select_support(4.0, "SS", False, "uninsulated", "rest")
        assert r.status == "needs_refinement"
        question_ids = [q["id"] for q in r.refinement_questions]
        assert "wall_schedule" in question_ids

    def test_ss_hot_insulated_asks_orientation_first(self):
        r = select_support(6.0, "SS", False, "hot_insulated", "rest")
        assert r.status == "needs_refinement"
        question_ids = [q["id"] for q in r.refinement_questions]
        assert "pipe_orientation" in question_ids

    def test_cs_uninsulated_small_bore_asks_wall_schedule(self):
        # NPS 2–16 CS uninsulated → notes [1,2] → wall schedule for DIRECT REST
        r = select_support(4.0, "CS", False, "uninsulated", "rest")
        assert r.status == "needs_refinement"
        question_ids = [q["id"] for q in r.refinement_questions]
        assert "wall_schedule" in question_ids

    def test_ss_large_bore_asks_orientation(self):
        r = select_support(30.0, "SS", False, "uninsulated", "rest")
        assert r.status == "needs_refinement"
        question_ids = [q["id"] for q in r.refinement_questions]
        assert "pipe_orientation" in question_ids


# =============================================================================
# REST — FULL REFINEMENT RESOLUTION
# =============================================================================

class TestRestRefinementResolution:

    def test_ss_uninsulated_thin_wall_gets_welded_shoe(self):
        r = select_support(4.0, "SS", False, "uninsulated", "rest",
                           {"wall_schedule": "lt_sch10s"})
        assert "SH01" in r.support_code
        assert "WA01" in r.support_code

    def test_ss_uninsulated_normal_wall_gets_wear_pad(self):
        r = select_support(4.0, "SS", False, "uninsulated", "rest",
                           {"wall_schedule": "ge_sch10s"})
        assert r.support_code == "WEAR PAD (WA01)"
        assert r.status == "complete"

    def test_cs_uninsulated_thin_wall_small_bore_gets_shoe(self):
        r = select_support(4.0, "CS", False, "uninsulated", "rest",
                           {"wall_schedule": "lt_sch20", "pipe_orientation": "straight"})
        assert "SH01" in r.support_code
        assert r.status == "complete"

    def test_cs_uninsulated_normal_wall_stays_direct_rest(self):
        r = select_support(4.0, "CS", False, "uninsulated", "rest",
                           {"wall_schedule": "ge_sch20"})
        assert r.support_code == "DIRECT REST"
        assert r.status == "complete"

    def test_ss_hot_insulated_straight_low_temp(self):
        r = select_support(6.0, "SS", False, "hot_insulated", "rest",
                           {"pipe_orientation": "straight",
                            "is_limit_stop_location": "false",
                            "design_temperature_c": "300"})
        assert "SC02" in r.support_code or "SC03" in r.support_code
        assert r.status == "complete"

    def test_ss_hot_insulated_straight_high_temp(self):
        r = select_support(6.0, "SS", False, "hot_insulated", "rest",
                           {"pipe_orientation": "straight",
                            "is_limit_stop_location": "false",
                            "design_temperature_c": "400"})
        assert "SC04" in r.support_code
        assert r.status == "complete"

    def test_ss_hot_insulated_sloping_low_temp(self):
        r = select_support(6.0, "SS", False, "hot_insulated", "rest",
                           {"pipe_orientation": "sloping",
                            "is_limit_stop_location": "false",
                            "design_temperature_c": "300"})
        assert "SC06" in r.support_code or "SC07" in r.support_code
        assert r.status == "complete"

    def test_ss_hot_insulated_sloping_limit_stop_below_400c(self):
        r = select_support(6.0, "SS", False, "hot_insulated", "rest",
                           {"pipe_orientation": "sloping",
                            "is_limit_stop_location": "true",
                            "design_temperature_c": "380"})
        assert "SH05" in r.support_code
        assert "WA01" in r.support_code
        assert r.status == "complete"

    def test_ss_hot_insulated_sloping_limit_stop_above_400c(self):
        r = select_support(6.0, "SS", False, "hot_insulated", "rest",
                           {"pipe_orientation": "sloping",
                            "is_limit_stop_location": "true",
                            "design_temperature_c": "410"})
        assert "SH03" in r.support_code
        assert "WA01" in r.support_code
        assert r.status == "complete"

    def test_ss_large_bore_straight(self):
        r = select_support(30.0, "SS", False, "uninsulated", "rest",
                           {"pipe_orientation": "straight"})
        assert "SH02" in r.support_code
        assert "WA01" in r.support_code
        assert r.status == "complete"

    def test_ss_large_bore_sloping_below_400c(self):
        r = select_support(30.0, "SS", False, "uninsulated", "rest",
                           {"pipe_orientation": "sloping",
                            "design_temperature_c": "300"})
        assert "SH05" in r.support_code
        assert "WA01" in r.support_code
        assert r.status == "complete"

    def test_ss_hot_insulated_straight_limit_stop(self):
        # Straight + limit stop → SH01 + WA01 (skips temperature check)
        r = select_support(6.0, "SS", False, "hot_insulated", "rest",
                           {"pipe_orientation": "straight",
                            "is_limit_stop_location": "true"})
        assert "SH01" in r.support_code
        assert "WA01" in r.support_code
        assert r.status == "complete"


# =============================================================================
# GUIDE
# =============================================================================

class TestGuideSelection:

    def test_cs_uninsulated_small_bore_gl01(self):
        r = select_support(1.0, "CS", False, "uninsulated", "guide")
        assert r.support_code == "GL01"
        assert r.status == "complete"

    def test_cs_hot_insulated_small_bore_not_applicable(self):
        # NPS ≤ 1" hot insulated guide → not applicable
        r = select_support(1.0, "CS", False, "hot_insulated", "guide")
        assert r.support_code is None
        assert r.status == "complete"

    def test_cs_uninsulated_mid_bore_gl01(self):
        r = select_support(4.0, "CS", False, "uninsulated", "guide")
        assert r.support_code == "GL01"
        assert r.status == "complete"

    def test_cs_hot_insulated_mid_bore_gl02(self):
        r = select_support(4.0, "CS", False, "hot_insulated", "guide")
        assert r.support_code == "GL02"
        assert r.status == "complete"

    def test_cs_large_bore_hot_gl02(self):
        r = select_support(12.0, "CS", False, "hot_insulated", "guide")
        assert r.support_code == "GL02"
        assert r.status == "complete"

    def test_ss_uninsulated_mid_bore_gl01_with_isolation(self):
        r = select_support(6.0, "SS", False, "uninsulated", "guide")
        assert "GL01" in r.support_code
        assert r.status == "complete"

    def test_ss_hot_insulated_mid_bore_gl02(self):
        r = select_support(6.0, "SS", False, "hot_insulated", "guide")
        assert r.support_code == "GL02"
        assert r.status == "complete"

    def test_frp_guide_mid_bore_sc73(self):
        r = select_support(4.0, "FRP", False, "uninsulated", "guide")
        assert "SC73" in r.support_code
        assert r.status == "complete"

    def test_frp_guide_nps26_not_applicable(self):
        r = select_support(26.0, "FRP", False, "uninsulated", "guide")
        assert r.support_code is None
        assert r.status == "complete"


# =============================================================================
# LINE STOP
# =============================================================================

class TestLineStopSelection:

    def test_cs_small_bore_uninsulated_ls01(self):
        r = select_support(0.75, "CS", False, "uninsulated", "line_stop")
        assert r.support_code == "LS01"
        assert r.status == "complete"

    def test_cs_small_bore_hot_insulated_not_applicable(self):
        r = select_support(1.0, "CS", False, "hot_insulated", "line_stop")
        assert r.support_code is None
        assert r.status == "complete"

    def test_cs_mid_bore_uninsulated_ls01_wa01(self):
        r = select_support(4.0, "CS", False, "uninsulated", "line_stop")
        assert "LS01" in r.support_code
        assert "WA01" in r.support_code
        assert r.status == "complete"

    def test_cs_mid_bore_hot_insulated_ls02(self):
        r = select_support(4.0, "CS", False, "hot_insulated", "line_stop")
        assert r.support_code == "LS02"
        assert r.status == "complete"

    def test_cs_large_bore_hot_insulated_ls03(self):
        r = select_support(12.0, "CS", False, "hot_insulated", "line_stop")
        assert r.support_code == "LS03"
        assert r.status == "complete"

    def test_ss_uninsulated_ls01_wa01(self):
        r = select_support(4.0, "SS", False, "uninsulated", "line_stop")
        assert "LS01" in r.support_code
        assert "WA01" in r.support_code
        assert r.status == "complete"

    def test_ss_hot_insulated_asks_temperature(self):
        r = select_support(4.0, "SS", False, "hot_insulated", "line_stop")
        assert r.status == "needs_refinement"
        question_ids = [q["id"] for q in r.refinement_questions]
        assert "design_temperature_c" in question_ids

    def test_ss_hot_insulated_high_temp_ls02_sh03(self):
        r = select_support(4.0, "SS", False, "hot_insulated", "line_stop",
                           {"design_temperature_c": "450"})
        assert "LS02" in r.support_code
        assert "SH03" in r.support_code
        assert r.status == "complete"

    def test_ss_hot_insulated_low_temp_ls02_straight(self):
        r = select_support(4.0, "SS", False, "hot_insulated", "line_stop",
                           {"design_temperature_c": "200",
                            "pipe_orientation": "straight"})
        assert "LS02" in r.support_code
        assert "SH01" in r.support_code
        assert r.status == "complete"

    def test_ss_hot_insulated_low_temp_sloping_nps4(self):
        # NPS ≤ 4 sloping → SH04
        r = select_support(4.0, "SS", False, "hot_insulated", "line_stop",
                           {"design_temperature_c": "200",
                            "pipe_orientation": "sloping"})
        assert "LS02" in r.support_code
        assert "SH04" in r.support_code
        assert r.status == "complete"

    def test_ss_hot_insulated_low_temp_sloping_nps6(self):
        # NPS 6 > 4 sloping → SH05
        r = select_support(6.0, "SS", False, "hot_insulated", "line_stop",
                           {"design_temperature_c": "200",
                            "pipe_orientation": "sloping"})
        assert "LS02" in r.support_code
        assert "SH05" in r.support_code
        assert r.status == "complete"

    def test_frp_line_stop_returns_cf03_with_note6(self):
        r = select_support(4.0, "FRP", False, "uninsulated", "line_stop")
        assert r.support_code == "CF03"
        assert 6 in r.notes
        assert len(r.refinement_warnings) > 0
        assert r.status == "complete"


# =============================================================================
# HOLD DOWN
# =============================================================================

class TestHoldDownSelection:

    def test_cs_small_bore_uninsulated_gh02(self):
        r = select_support(1.0, "CS", False, "uninsulated", "hold_down")
        assert r.support_code == "GH02"
        assert r.status == "complete"

    def test_cs_small_bore_hot_insulated_not_applicable(self):
        r = select_support(1.0, "CS", False, "hot_insulated", "hold_down")
        assert r.support_code is None
        assert r.status == "complete"

    def test_cs_mid_bore_hot_insulated_gh01(self):
        r = select_support(4.0, "CS", False, "hot_insulated", "hold_down")
        assert r.support_code == "GH01"
        assert r.status == "complete"

    def test_cs_large_bore_uninsulated_not_applicable(self):
        # NPS ≥ 12 uninsulated hold_down → not applicable
        r = select_support(12.0, "CS", False, "uninsulated", "hold_down")
        assert r.support_code is None
        assert r.status == "complete"

    def test_cs_large_bore_hot_insulated_gh01(self):
        r = select_support(12.0, "CS", False, "hot_insulated", "hold_down")
        assert r.support_code == "GH01"
        assert r.status == "complete"

    def test_ss_mid_bore_uninsulated_gh02_with_pad(self):
        r = select_support(4.0, "SS", False, "uninsulated", "hold_down")
        assert "GH02" in r.support_code
        assert r.status == "complete"

    def test_frp_hold_down_not_applicable(self):
        r = select_support(4.0, "FRP", False, "uninsulated", "hold_down")
        assert r.support_code is None
        assert r.status == "complete"


# =============================================================================
# FRP SPECIAL CASES
# =============================================================================

class TestFrpSpecialCases:

    # ── REST ─────────────────────────────────────────────────────────────────

    def test_frp_half_inch_rest_not_applicable(self):
        # NPS 1/2" is below the FRP minimum (3/4")
        r = select_support(0.5, "FRP", False, "uninsulated", "rest")
        assert r.support_code is None
        assert r.status == "complete"

    def test_frp_three_quarter_inch_rest_sc71_primary(self):
        r = select_support(0.75, "FRP", False, "uninsulated", "rest")
        assert "SC71" in r.support_code
        assert r.status == "complete"

    def test_frp_1_inch_rest_includes_sc72_alternative(self):
        r = select_support(1.0, "FRP", False, "uninsulated", "rest")
        assert "SC71" in r.support_code
        assert "SC72" in r.support_code
        assert r.status == "complete"

    def test_frp_mid_bore_rest_sc71_and_sc72(self):
        r = select_support(6.0, "FRP", False, "uninsulated", "rest")
        assert "SC71" in r.support_code
        assert "SC72" in r.support_code
        assert r.status == "complete"

    def test_frp_nps26_rest_sc71_only(self):
        # NPS 26" falls between SC72 sub-ranges → SC71 only
        r = select_support(26.0, "FRP", False, "uninsulated", "rest")
        assert r.support_code == "SADDLE SUPPORT (SC71)"
        assert "SC72" not in r.support_code
        assert r.status == "complete"

    def test_frp_hot_insulated_rest_same_as_uninsulated(self):
        # FRP special-case path ignores insulation for REST
        r_bare = select_support(4.0, "FRP", False, "uninsulated", "rest")
        r_hot  = select_support(4.0, "FRP", False, "hot_insulated", "rest")
        assert r_bare.support_code == r_hot.support_code

    # ── GUIDE ────────────────────────────────────────────────────────────────

    def test_frp_guide_small_bore_not_applicable(self):
        # FRP NPS < 3/4" guide → not applicable (handled by frp nps<0.75 check)
        r = select_support(0.5, "FRP", False, "uninsulated", "guide")
        assert r.support_code is None

    def test_frp_guide_mid_bore_sc73(self):
        r = select_support(8.0, "FRP", False, "uninsulated", "guide")
        assert "SC73" in r.support_code
        assert r.status == "complete"

    def test_frp_guide_nps26_not_applicable(self):
        r = select_support(26.0, "FRP", False, "uninsulated", "guide")
        assert r.support_code is None
        assert r.status == "complete"

    # ── LINE STOP ────────────────────────────────────────────────────────────

    def test_frp_line_stop_cf03_is_deviation(self):
        r = select_support(8.0, "FRP", False, "uninsulated", "line_stop")
        assert r.support_code == "CF03"
        assert 6 in r.notes
        assert any("deviation" in w.lower() or "approval" in w.lower()
                   for w in r.refinement_warnings)

    # ── HOLD DOWN ────────────────────────────────────────────────────────────

    def test_frp_hold_down_all_sizes_not_applicable(self):
        for nps in (0.75, 2.0, 6.0, 12.0, 24.0):
            r = select_support(nps, "FRP", False, "uninsulated", "hold_down")
            assert r.support_code is None, f"Expected None for FRP NPS {nps} hold_down"


# =============================================================================
# DRAWING REFERENCES
# =============================================================================

class TestDrawingReferences:

    def test_complete_result_includes_drawings(self):
        r = select_support(1.0, "CS", False, "uninsulated", "rest")
        # DIRECT REST has no drawing in the index
        # (direct rest support is just structural steel)
        assert isinstance(r.drawings, list)

    def test_frp_saddle_drawings_populated(self):
        r = select_support(4.0, "FRP", False, "uninsulated", "rest")
        # SC71 has drawings in the index
        assert len(r.drawings) > 0

    def test_drawings_labeled(self):
        r = select_support(4.0, "FRP", False, "uninsulated", "rest")
        for item in r.drawings_labeled:
            assert "ref" in item
            assert "code" in item

    def test_gl01_has_drawings(self):
        r = select_support(4.0, "CS", False, "uninsulated", "guide")
        assert r.support_code == "GL01"
        assert len(r.drawings) > 0

    def test_ff01_drawing_resolves_to_0417(self):
        r = select_support(4.0, "CS", False, "uninsulated", "rest",
                           is_flange=True, flange_class=150)
        assert "JS-PE-DPS-0417" in r.drawings

    def test_ff06_drawing_resolves_to_0422(self):
        r = select_support(4.0, "CS", False, "uninsulated", "rest",
                           is_flange=True, flange_class=2500)
        assert "JS-PE-DPS-0422" in r.drawings

    def test_ff71_drawing_resolves_to_0705(self):
        r = select_support(4.0, "FRP", False, "uninsulated", "rest",
                           is_flange=True)
        assert "JS-PE-DPS-0705" in r.drawings


# =============================================================================
# FLANGE SUPPORT — IMAGE KEY TESTS
# =============================================================================


class TestFlangeImageKeys:
    """
    Confirm that FF01–FF06 and FF71 are mapped to their dedicated SVG keys
    and are no longer routed to the generic bearing_plate placeholder.
    """

    def _image_key(self, support_code: str) -> str:
        import sys, os
        sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
        from app import get_image_key
        return get_image_key(support_code)

    def test_ff01_image_key_is_flange_frame(self):
        assert self._image_key("FLANGE FRAME (FF01)") == "flange_frame"

    def test_ff06_image_key_is_flange_frame(self):
        assert self._image_key("FLANGE FRAME (FF06)") == "flange_frame"

    def test_ff71_image_key_is_frp_flange_holder(self):
        assert self._image_key("FLANGED VALVE HOLDER (FF71)") == "frp_flange_holder"

    def test_ff_codes_not_mapped_to_bearing_plate(self):
        for code in ["FF01", "FF02", "FF03", "FF04", "FF05", "FF06"]:
            result = self._image_key(f"FLANGE FRAME ({code})")
            assert result != "bearing_plate", f"{code} still routes to bearing_plate"

    def test_ff71_not_mapped_to_bearing_plate(self):
        result = self._image_key("FLANGED VALVE HOLDER (FF71)")
        assert result != "bearing_plate"


# =============================================================================
# DRAWING PAGE COVERAGE — FF SERIES
# =============================================================================


class TestFFDrawingPages:
    """
    Confirm that all FF drawing references have been added to DRAWING_PAGES
    in pdf_service.py so the /api/drawing/ endpoint does not return 404.
    """

    def _drawing_pages(self):
        import sys, os
        sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
        from pdf_service import DRAWING_PAGES
        return DRAWING_PAGES

    @pytest.mark.parametrize("ref,expected_key", [
        ("JS-PE-DPS-0417", "JS-PE-DPS-0417"),  # FF01
        ("JS-PE-DPS-0418", "JS-PE-DPS-0418"),  # FF02
        ("JS-PE-DPS-0419", "JS-PE-DPS-0419"),  # FF03
        ("JS-PE-DPS-0420", "JS-PE-DPS-0420"),  # FF04
        ("JS-PE-DPS-0421", "JS-PE-DPS-0421"),  # FF05
        ("JS-PE-DPS-0422", "JS-PE-DPS-0422"),  # FF06
        ("JS-PE-DPS-0705", "JS-PE-DPS-0705"),  # FF71
    ])
    def test_ff_drawing_ref_in_drawing_pages(self, ref, expected_key):
        pages = self._drawing_pages()
        assert expected_key in pages, f"{expected_key} missing from DRAWING_PAGES"
        assert len(pages[expected_key]) > 0, f"{expected_key} has empty page list"

    def test_ff01_page_number_is_correct(self):
        pages = self._drawing_pages()
        assert pages["JS-PE-DPS-0417"] == [111]

    def test_ff06_page_number_is_correct(self):
        pages = self._drawing_pages()
        assert pages["JS-PE-DPS-0422"] == [116]

    def test_ff71_page_number_is_correct(self):
        pages = self._drawing_pages()
        assert pages["JS-PE-DPS-0705"] == [179]


class TestFFPdfHighlighting:
    """Focused checks for FF drawing NPS row detection."""

    def _page(self, page_index):
        fitz = pytest.importorskip("fitz")
        from pdf_service import get_pdf_path

        pdf_path = get_pdf_path()
        if not pdf_path:
            pytest.skip("Standard PDF not available")

        return fitz.open(pdf_path)[page_index]

    @pytest.mark.parametrize("nps", [10.0, 18.0])
    def test_ff71_special_case_finds_bare_nps_rows(self, nps):
        from pdf_service import _find_ff71_row_rect

        rect = _find_ff71_row_rect(self._page(179), nps)

        assert rect is not None
        assert rect.width > 0
        assert rect.height > 30

    @pytest.mark.parametrize("page_index,nps", [
        (111, 10.0),  # FF01 / JS-PE-DPS-0417
        (112, 10.0),  # FF02 / JS-PE-DPS-0418
        (113, 10.0),  # FF03 / JS-PE-DPS-0419
        (114, 10.0),  # FF04 / JS-PE-DPS-0420
        (115, 10.0),  # FF05 / JS-PE-DPS-0421
        (116, 10.0),  # FF06 / JS-PE-DPS-0422
    ])
    def test_ff01_to_ff06_generic_finder_still_finds_rows(self, page_index, nps):
        from pdf_service import _find_row_rect

        rect = _find_row_rect(self._page(page_index), nps)

        assert rect is not None
        assert rect.width > 0
        assert rect.height > 30


class TestWLPdfHighlighting:
    """Focused checks for WL drawing NPS column detection."""

    WL_REFS = [
        "JS-PE-DPS-0386",
        "JS-PE-DPS-0387",
        "JS-PE-DPS-0388",
        "JS-PE-DPS-0389",
    ]

    def _page(self, page_index):
        fitz = pytest.importorskip("fitz")
        from pdf_service import get_pdf_path

        pdf_path = get_pdf_path()
        if not pdf_path:
            pytest.skip("Standard PDF not available")

        return fitz.open(pdf_path)[page_index]

    @pytest.mark.parametrize("ref", WL_REFS)
    def test_wl03_to_wl06_use_column_highlighting_mode(self, ref):
        from pdf_service import _highlight_mode_for_ref

        assert _highlight_mode_for_ref(ref) == "column"

    @pytest.mark.parametrize("page_index,nps", [
        (85, 12.0),  # WL04 / JS-PE-DPS-0387
        (85, 24.0),  # WL04 / JS-PE-DPS-0387
        (86, 12.0),  # WL05 / JS-PE-DPS-0388
        (86, 24.0),  # WL05 / JS-PE-DPS-0388
    ])
    def test_wl_table_finder_returns_vertical_column_rect(self, page_index, nps):
        from pdf_service import _find_wl_column_rect

        rect = _find_wl_column_rect(self._page(page_index), nps)

        assert rect is not None
        assert rect.width > 50
        assert 10 < rect.height < 40

    def test_standard_supports_still_use_row_highlighting_mode(self):
        from pdf_service import _highlight_mode_for_ref

        assert _highlight_mode_for_ref("JS-PE-DPS-0327") == "row"
        assert _highlight_mode_for_ref("JS-PE-DPS-0417") == "row"
        assert _highlight_mode_for_ref("JS-PE-DPS-0705") == "ff71_row"


class TestRCPdfHighlighting:
    """Focused checks for RC drawing NPS row detection."""

    def _page(self, page_index):
        fitz = pytest.importorskip("fitz")
        from pdf_service import get_pdf_path

        pdf_path = get_pdf_path()
        if not pdf_path:
            pytest.skip("Standard PDF not available")

        return fitz.open(pdf_path)[page_index]

    @pytest.mark.parametrize("page_index,nps", [
        (181, 4.0),    # RC71 / 0707-01
        (184, 4.0),    # RC72 / 0708-01
        (187, 4.0),    # RC73 / 0709-01
        (183, 80.0),   # RC71 / 0707-03
    ])
    def test_rc_generic_row_finder_finds_nps_rows(self, page_index, nps):
        from pdf_service import _find_row_rect

        rect = _find_row_rect(self._page(page_index), nps)

        assert rect is not None
        assert rect.width > 0
        assert rect.height > 20


# =============================================================================
# KNOWN LIMITATIONS
# =============================================================================

class TestObsoleteCodesRemoved:
    """
    SC09 and CF04 belong to an obsolete revision of the JESA support standard.
    These tests confirm they have been fully removed from the codebase.
    """

    def test_sc09_absent_from_all_rule_strings(self):
        """SC09 must not appear in any support rule string."""
        from support_rules import SUPPORT_RULES
        import json
        rules_text = json.dumps(SUPPORT_RULES)
        assert "SC09" not in rules_text, (
            "SC09 found in SUPPORT_RULES — this obsolete code must be removed."
        )

    def test_sc09_absent_from_drawing_index(self):
        """SC09 must not be present as a key in DRAWING_INDEX."""
        from drawing_index import DRAWING_INDEX
        assert "SC09" not in DRAWING_INDEX

    def test_ss_al_hot_insulated_rule_uses_sc06_to_sc08(self):
        """
        The current rule for hot-insulated SS/AL REST (NPS 1.5"–24") must
        reference SC06-SC08 (not SC06-SC09).
        """
        from support_rules import SUPPORT_RULES
        rule = SUPPORT_RULES["rest"]["1.5"]["ss_ds_sd_sa"]["hot_insulated"]["support"]
        assert "SC06-SC08" in rule
        assert "SC09" not in rule

    def test_ss_al_hot_insulated_refinement_resolves_correctly(self):
        """
        End-to-end: SS hot-insulated REST, straight orientation, low temp
        must complete successfully and return SC02-SC04 drawings.
        """
        r = select_support(
            1.5, "SS", False, "hot_insulated", "rest",
            {"pipe_orientation": "straight",
             "is_limit_stop_location": "false",
             "design_temperature_c": "200"},
        )
        assert r.status == "complete"
        assert r.support_code is not None
        assert "SC09" not in (r.support_code or "")

    def test_cf04_absent_from_all_rule_strings(self):
        """CF04 must not appear in any support rule string."""
        from support_rules import SUPPORT_RULES
        import json
        rules_text = json.dumps(SUPPORT_RULES)
        assert "CF04" not in rules_text, (
            "CF04 found in SUPPORT_RULES — this obsolete code must be removed."
        )

    def test_cf04_absent_from_drawing_index(self):
        """CF04 must not be present as a key in DRAWING_INDEX."""
        from drawing_index import DRAWING_INDEX
        assert "CF04" not in DRAWING_INDEX


# =============================================================================
# EDGE / VALIDATION CASES
# =============================================================================

class TestEdgeCases:

    def test_nps_below_minimum_raises(self):
        with pytest.raises(ValueError):
            select_support(0.3, "CS", False, "uninsulated", "rest")

    def test_nps_above_maximum_raises(self):
        with pytest.raises(ValueError):
            select_support(50.0, "CS", False, "uninsulated", "rest")

    def test_unknown_material_raises(self):
        with pytest.raises(ValueError, match="Unknown material"):
            select_support(4.0, "XX", False, "uninsulated", "rest")

    def test_unknown_function_raises(self):
        with pytest.raises(ValueError, match="Unknown support function"):
            select_support(4.0, "CS", False, "uninsulated", "anchor")

    def test_unknown_insulation_raises(self):
        with pytest.raises(ValueError, match="Unknown insulation"):
            select_support(4.0, "CS", False, "warm", "rest")

    def test_result_is_not_applicable_returns_false(self):
        r = select_support(0.5, "FRP", False, "uninsulated", "rest")
        assert r.is_applicable() is False

    def test_result_is_applicable_returns_true(self):
        r = select_support(1.0, "CS", False, "uninsulated", "rest")
        assert r.is_applicable() is True

    def test_pwht_ignored_for_non_cs_materials(self):
        # SS does not have PWHT sub-keys — PWHT flag must not affect the result
        r_no_pwht = select_support(4.0, "SS", False, "uninsulated", "rest")
        r_pwht    = select_support(4.0, "SS", True,  "uninsulated", "rest")
        assert r_no_pwht.support_code == r_pwht.support_code

    def test_size_range_boundary_18_is_table15_range(self):
        # NPS 18.0 is exactly at the 18_to_24 boundary
        r = select_support(18.0, "CS", False, "uninsulated", "rest")
        assert r.size_range == "18_to_24"

    def test_note_texts_populated_when_notes_present(self):
        r = select_support(18.0, "CS", False, "uninsulated", "rest")
        assert len(r.note_texts) == len(r.notes)
        for text in r.note_texts:
            assert len(text) > 10  # each note has real content


# =============================================================================
# VERTICAL PIPE LUG SUPPORTS (WL03-WL06)
# =============================================================================

class TestVerticalPipeLugSupports:

    WL_WARNING = (
        "Use only when specified on stress isometrics or approved by stress engineer. "
        "Local stress checks may be required."
    )

    def test_horizontal_behavior_unchanged_when_orientation_horizontal(self):
        base = select_support(4.0, "CS", False, "uninsulated", "rest")
        horizontal = select_support(
            4.0, "CS", False, "uninsulated", "rest",
            pipe_orientation="horizontal",
            vertical_restraint="fixed",
        )
        assert horizontal.support_code == base.support_code
        assert horizontal.drawings == base.drawings
        assert horizontal.refinement_warnings == base.refinement_warnings

    @pytest.mark.parametrize("fn", ["rest", "guide", "line_stop", "hold_down"])
    def test_vertical_branch_bypasses_horizontal_function_rules(self, fn):
        r = select_support(
            4.0, "CS", False, "uninsulated", fn,
            pipe_orientation="vertical",
            vertical_restraint="sliding",
        )
        assert r.support_code == "SHEAR LUG - SLIDING FOR VERTICAL BARE PIPE (WL03)"
        assert r.drawings == ["JS-PE-DPS-0386"]

    @pytest.mark.parametrize("insulation,restraint,code,drawing", [
        ("uninsulated", "sliding", "WL03", "JS-PE-DPS-0386"),
        ("uninsulated", "fixed", "WL04", "JS-PE-DPS-0387"),
        ("hot_insulated", "sliding", "WL05", "JS-PE-DPS-0388"),
        ("hot_insulated", "fixed", "WL06", "JS-PE-DPS-0389"),
    ])
    def test_wl03_to_wl06_selection_logic(self, insulation, restraint, code, drawing):
        r = select_support(
            6.0, "CS", False, insulation, "rest",
            pipe_orientation="vertical",
            vertical_restraint=restraint,
        )
        assert code in r.support_code
        assert r.drawings == [drawing]
        assert self.WL_WARNING in r.refinement_warnings

    @pytest.mark.parametrize("nps", [0.5, 0.75, 26.0, 48.0])
    def test_vertical_wl_outside_one_to_twenty_four_is_not_applicable(self, nps):
        r = select_support(
            nps, "CS", False, "uninsulated", "rest",
            pipe_orientation="vertical",
            vertical_restraint="sliding",
        )
        assert r.support_code is None
        assert any("NPS 1" in warning and "NPS 24" in warning for warning in r.refinement_warnings)

    def test_frp_vertical_bypasses_wl_and_returns_rc71(self):
        r = select_support(
            4.0, "FRP", False, "uninsulated", "rest",
            pipe_orientation="vertical",
            vertical_restraint="fixed",
        )
        assert "RC71" in r.support_code
        assert "WL" not in r.support_code
        assert r.drawings == ["JS-PE-DPS-0707-01"]

    def test_unknown_vertical_restraint_raises(self):
        with pytest.raises(ValueError, match="vertical restraint"):
            select_support(
                4.0, "CS", False, "uninsulated", "rest",
                pipe_orientation="vertical",
                vertical_restraint="anchored",
            )

    def test_wl03_to_wl06_drawing_references_resolve(self):
        from drawing_index import DRAWING_INDEX

        assert DRAWING_INDEX["WL03"] == ["JS-PE-DPS-0386"]
        assert DRAWING_INDEX["WL04"] == ["JS-PE-DPS-0387"]
        assert DRAWING_INDEX["WL05"] == ["JS-PE-DPS-0388"]
        assert DRAWING_INDEX["WL06"] == ["JS-PE-DPS-0389"]

    def test_deferred_wl01_wl02_not_in_drawing_index(self):
        from drawing_index import DRAWING_INDEX

        assert "WL01" not in DRAWING_INDEX
        assert "WL02" not in DRAWING_INDEX

    def test_wl03_to_wl06_pdf_pages_resolve(self):
        from pdf_service import DRAWING_PAGES

        assert DRAWING_PAGES["JS-PE-DPS-0386"] == [84]
        assert DRAWING_PAGES["JS-PE-DPS-0387"] == [85]
        assert DRAWING_PAGES["JS-PE-DPS-0388"] == [86]
        assert DRAWING_PAGES["JS-PE-DPS-0389"] == [87]

    def test_wl06_related_drawings_include_notes_and_load_table_refs(self):
        from drawing_index import get_related_drawings

        related = get_related_drawings(["JS-PE-DPS-0389"])

        assert related == ["JS-PE-DPS-0386", "JS-PE-DPS-0388"]

    def test_wl_related_drawings_resolve_to_valid_pdf_pages(self):
        from drawing_index import get_related_drawings
        from pdf_service import DRAWING_PAGES

        for ref in ["JS-PE-DPS-0386", "JS-PE-DPS-0387", "JS-PE-DPS-0388", "JS-PE-DPS-0389"]:
            for related_ref in get_related_drawings([ref]):
                assert related_ref in DRAWING_PAGES
                assert DRAWING_PAGES[related_ref]

    def test_wl06_api_includes_related_drawings(self):
        from app import app

        with app.test_client() as client:
            response = client.post("/api/select", json={
                "nps": 12.0,
                "material": "CS",
                "pwht": False,
                "insulation": "hot_insulated",
                "function": "rest",
                "pipe_orientation": "vertical",
                "vertical_restraint": "fixed",
            })

        data = response.get_json()
        assert response.status_code == 200
        assert data["drawings"] == ["JS-PE-DPS-0389"]
        assert data["related_drawings"] == ["JS-PE-DPS-0386", "JS-PE-DPS-0388"]
        assert {item["code"] for item in data["related_drawings_labeled"]} == {"WL03", "WL05"}

    def test_vertical_lug_uses_own_illustration_key(self):
        from app import get_image_key

        assert get_image_key("SHEAR LUG - SLIDING FOR VERTICAL BARE PIPE (WL03)") == "vertical_lug"


# =============================================================================
# FRP VERTICAL RISER CLAMP SUPPORTS (RC71-RC73)
# =============================================================================

class TestFrpVerticalRiserClampSupports:

    @pytest.mark.parametrize("support_type,code", [
        ("rest", "RC71"),
        ("rest_guide_hold_down", "RC72"),
        ("all_around_guide", "RC73"),
    ])
    def test_frp_vertical_support_type_selection(self, support_type, code):
        r = select_support(
            4.0, "FRP", False, "uninsulated", "rest",
            pipe_orientation="vertical",
            frp_vertical_support=support_type,
        )
        assert code in r.support_code
        assert r.is_applicable()

    @pytest.mark.parametrize("nps,expected_suffix", [
        (4.0, "-01"),
        (8.0, "-02"),
        (12.0, "-03"),
        (80.0, "-03"),
    ])
    def test_rc71_nps_routes_to_correct_drawing_suffix(self, nps, expected_suffix):
        r = select_support(
            nps, "FRP", False, "uninsulated", "rest",
            pipe_orientation="vertical",
            frp_vertical_support="rest",
        )
        assert r.drawings == [f"JS-PE-DPS-0707{expected_suffix}"]

    @pytest.mark.parametrize("support_type,expected_ref", [
        ("rest", "JS-PE-DPS-0707-02"),
        ("rest_guide_hold_down", "JS-PE-DPS-0708-02"),
        ("all_around_guide", "JS-PE-DPS-0709-02"),
    ])
    def test_rc71_to_rc73_drawing_references_resolve(self, support_type, expected_ref):
        r = select_support(
            8.0, "FRP", False, "uninsulated", "rest",
            pipe_orientation="vertical",
            frp_vertical_support=support_type,
        )
        assert r.drawings == [expected_ref]

    def test_frp_vertical_no_longer_returns_not_applicable(self):
        r = select_support(
            6.0, "FRP", False, "uninsulated", "rest",
            pipe_orientation="vertical",
            frp_vertical_support="rest",
        )
        assert r.support_code is not None
        assert "RC71" in r.support_code

    def test_rc_drawing_index_entries(self):
        from drawing_index import DRAWING_INDEX

        assert DRAWING_INDEX["RC71"] == [
            "JS-PE-DPS-0707-01",
            "JS-PE-DPS-0707-02",
            "JS-PE-DPS-0707-03",
        ]
        assert DRAWING_INDEX["RC72"] == [
            "JS-PE-DPS-0708-01",
            "JS-PE-DPS-0708-02",
            "JS-PE-DPS-0708-03",
        ]
        assert DRAWING_INDEX["RC73"] == [
            "JS-PE-DPS-0709-01",
            "JS-PE-DPS-0709-02",
            "JS-PE-DPS-0709-03",
        ]

    def test_rc_pdf_page_mappings(self):
        from pdf_service import DRAWING_PAGES

        assert DRAWING_PAGES["JS-PE-DPS-0707-01"] == [181]
        assert DRAWING_PAGES["JS-PE-DPS-0707-02"] == [182]
        assert DRAWING_PAGES["JS-PE-DPS-0707-03"] == [183]
        assert DRAWING_PAGES["JS-PE-DPS-0708-01"] == [184]
        assert DRAWING_PAGES["JS-PE-DPS-0708-02"] == [185]
        assert DRAWING_PAGES["JS-PE-DPS-0708-03"] == [186]
        assert DRAWING_PAGES["JS-PE-DPS-0709-01"] == [187]
        assert DRAWING_PAGES["JS-PE-DPS-0709-02"] == [188]
        assert DRAWING_PAGES["JS-PE-DPS-0709-03"] == [189]

    @pytest.mark.parametrize("code,image_key", [
        ("RC71", "rc71"),
        ("RC72", "rc72"),
        ("RC73", "rc73"),
    ])
    def test_rc_image_keys(self, code, image_key):
        from app import get_image_key

        assert get_image_key(f"PIPE SUPPORT RISER CLAMP ({code})") == image_key

    def test_metallic_vertical_still_routes_to_wl03_to_wl06(self):
        r = select_support(
            6.0, "CS", False, "hot_insulated", "rest",
            pipe_orientation="vertical",
            vertical_restraint="fixed",
        )
        assert "WL06" in r.support_code


# =============================================================================
# FLANGE FRAME SUPPORTS (FF01–FF06)  —  pipe flange, all materials
# =============================================================================

class TestFlangeFrameSupports:

    # ── Each pressure class returns the correct code ──────────────────────────

    @pytest.mark.parametrize("cls,expected_code", [
        (150,  "FF01"),
        (300,  "FF02"),
        (600,  "FF03"),
        (900,  "FF04"),
        (1500, "FF05"),
        (2500, "FF06"),
    ])
    def test_correct_code_per_class(self, cls, expected_code):
        r = select_support(4.0, "CS", False, "uninsulated", "rest",
                           is_flange=True, flange_class=cls)
        assert expected_code in r.support_code
        assert r.status == "complete"

    # ── Drawings wired up ─────────────────────────────────────────────────────

    @pytest.mark.parametrize("cls,expected_dwg", [
        (150,  "JS-PE-DPS-0417"),
        (300,  "JS-PE-DPS-0418"),
        (600,  "JS-PE-DPS-0419"),
        (900,  "JS-PE-DPS-0420"),
        (1500, "JS-PE-DPS-0421"),
        (2500, "JS-PE-DPS-0422"),
    ])
    def test_drawing_reference(self, cls, expected_dwg):
        r = select_support(4.0, "CS", False, "uninsulated", "rest",
                           is_flange=True, flange_class=cls)
        assert expected_dwg in r.drawings

    # ── NPS boundary: CL150/300 max is 24" ───────────────────────────────────

    def test_cl150_nps24_applicable(self):
        r = select_support(24.0, "CS", False, "uninsulated", "rest",
                           is_flange=True, flange_class=150)
        assert "FF01" in r.support_code

    def test_cl150_nps26_not_applicable(self):
        r = select_support(26.0, "CS", False, "uninsulated", "rest",
                           is_flange=True, flange_class=150)
        assert r.support_code is None

    # ── NPS boundary: CL600–1500 min is 2", max is 16" ───────────────────────

    def test_cl600_nps1_not_applicable(self):
        r = select_support(1.0, "CS", False, "uninsulated", "rest",
                           is_flange=True, flange_class=600)
        assert r.support_code is None

    def test_cl600_nps2_applicable(self):
        r = select_support(2.0, "CS", False, "uninsulated", "rest",
                           is_flange=True, flange_class=600)
        assert "FF03" in r.support_code

    def test_cl600_nps16_applicable(self):
        r = select_support(16.0, "CS", False, "uninsulated", "rest",
                           is_flange=True, flange_class=600)
        assert "FF03" in r.support_code

    def test_cl600_nps18_not_applicable(self):
        r = select_support(18.0, "CS", False, "uninsulated", "rest",
                           is_flange=True, flange_class=600)
        assert r.support_code is None

    # ── NPS boundary: CL2500 max is 12" ──────────────────────────────────────

    def test_cl2500_nps12_applicable(self):
        r = select_support(12.0, "CS", False, "uninsulated", "rest",
                           is_flange=True, flange_class=2500)
        assert "FF06" in r.support_code

    def test_cl2500_nps14_not_applicable(self):
        r = select_support(14.0, "CS", False, "uninsulated", "rest",
                           is_flange=True, flange_class=2500)
        assert r.support_code is None

    # ── Metallic materials route to FFxx (FRP routes to FF71, tested separately) ─

    @pytest.mark.parametrize("material", ["CS", "SS", "DS", "AL"])
    def test_metallic_materials_get_ffxx(self, material):
        r = select_support(4.0, material, False, "uninsulated", "rest",
                           is_flange=True, flange_class=150)
        assert "FF01" in (r.support_code or "")

    # ── Flange flag ignored for non-REST functions ────────────────────────────

    @pytest.mark.parametrize("fn", ["guide", "line_stop", "hold_down"])
    def test_flange_flag_ignored_for_non_rest(self, fn):
        r = select_support(4.0, "CS", False, "uninsulated", fn,
                           is_flange=True, flange_class=150)
        assert r.support_code is None or "FF" not in (r.support_code or "")

    # ── Unknown / missing pressure class raises ValueError ───────────────────

    def test_unknown_pressure_class_raises(self):
        with pytest.raises(ValueError, match="pressure class"):
            select_support(4.0, "CS", False, "uninsulated", "rest",
                           is_flange=True, flange_class=400)

    def test_missing_pressure_class_raises(self):
        with pytest.raises(ValueError, match="required"):
            select_support(4.0, "CS", False, "uninsulated", "rest",
                           is_flange=True, flange_class=None)


# =============================================================================
# FRP FLANGED HOLDER (FF71) — used for both pipe and valve flanges on FRP lines
# =============================================================================

class TestFF71FrpFlangeHolder:

    def test_frp_flange_nps1_returns_ff71(self):
        r = select_support(1.0, "FRP", False, "uninsulated", "rest",
                           is_flange=True)
        assert "FF71" in r.support_code
        assert r.status == "complete"

    def test_frp_flange_nps6_returns_ff71(self):
        r = select_support(6.0, "FRP", False, "uninsulated", "rest",
                           is_flange=True)
        assert "FF71" in r.support_code

    def test_frp_flange_nps18_returns_ff71(self):
        # NPS 18" is the maximum for FF71
        r = select_support(18.0, "FRP", False, "uninsulated", "rest",
                           is_flange=True)
        assert "FF71" in r.support_code

    def test_frp_flange_nps20_not_applicable(self):
        # NPS 20" exceeds FF71 range (max 18")
        r = select_support(20.0, "FRP", False, "uninsulated", "rest",
                           is_flange=True)
        assert r.support_code is None

    def test_frp_flange_below_min_nps_not_applicable(self):
        # NPS 0.75" is below FF71 minimum (1")
        r = select_support(0.75, "FRP", False, "uninsulated", "rest",
                           is_flange=True)
        assert r.support_code is None

    def test_ff71_drawing_is_0705(self):
        r = select_support(4.0, "FRP", False, "uninsulated", "rest",
                           is_flange=True)
        assert "JS-PE-DPS-0705" in r.drawings

    def test_frp_flange_no_class_required(self):
        # FRP + is_flange must not raise even when flange_class is omitted
        r = select_support(4.0, "FRP", False, "uninsulated", "rest",
                           is_flange=True)
        assert "FF71" in r.support_code
