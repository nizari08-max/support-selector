"""
Tests for the pipe rack width calculator (rack_calculator.py + pipe_flange_data.py).

Coverage:
  - mround() Excel-compatible rounding
  - Single-pipe edge-offset formula
  - Pair-spacing staggered-flange formula
  - Full rack-width calculation: totals, expansion, final width
  - Insulation effects
  - Flange-rating effects (B16.5 and B16.47 Series A/B)
  - Custom expansion % and steel column width
  - Multiple-pipe racks (3 pipes)
  - Error cases: empty list, too many pipes, non-standard flange combo
  - Eurocode steel profile database (structural_profiles.py)
  - Future Spare Space rename does not change calculation
"""

import pytest
from rack_calculator import (
    calculate_rack,
    calculate_pair_spacing,
    calculate_edge_offset,
    mround,
    PAIR_CLEARANCE_MM,
    EDGE_CLEARANCE_MM,
    PER_PIPE_BUFFER_MM,
    DEFAULT_EXPANSION_PCT,
    DEFAULT_STEEL_COLUMN_MM,
    MAX_PIPES_PER_TIER,
)
from pipe_flange_data import get_pipe_od, get_flange_od
from structural_profiles import get_profile_width, PROFILES, profiles_for_js
from rack_diagram import generate_diagram


# =============================================================================
# mround — Excel MROUND compatibility
# =============================================================================

class TestMround:

    def test_exact_multiple_unchanged(self):
        assert mround(320, 5) == 320

    def test_rounds_down(self):
        assert mround(322, 5) == 320

    def test_rounds_up(self):
        assert mround(347, 5) == 345

    def test_round_half_away_from_zero_not_bankers(self):
        # Python built-in round(2.5) = 2 (banker's), but Excel MROUND(2.5,5) = 5
        assert mround(2.5, 5) == 5

    def test_round_half_up_7point5(self):
        assert mround(7.5, 5) == 10

    def test_zero_value(self):
        assert mround(0, 5) == 0

    def test_multiple_of_one(self):
        assert mround(163.0, 1) == 163

    def test_fractional_multiple(self):
        # Used for expansion: MROUND(inner * pct, 1)
        assert mround(84.0, 1) == 84
        assert mround(94.0, 1) == 94

    def test_large_value(self):
        assert mround(595, 5) == 595


# =============================================================================
# Pipe and flange data access
# =============================================================================

class TestPipeFlangeData:

    def test_dn100_pipe_od(self):
        assert get_pipe_od(100) == 114

    def test_dn200_pipe_od(self):
        assert get_pipe_od(200) == 219

    def test_dn650_pipe_od(self):
        assert get_pipe_od(650) == 660

    def test_dn100_class150_flange(self):
        assert get_flange_od(100, 150) == 230

    def test_dn200_class300_flange(self):
        assert get_flange_od(200, 300) == 380

    def test_dn650_series_a_class150_flange(self):
        assert get_flange_od(650, "150A") == 870

    def test_dn650_series_b_class150_flange(self):
        assert get_flange_od(650, "150B") == 785

    def test_nonstandard_combination_returns_none(self):
        # DN 350 has no 2500 rating in B16.5
        assert get_flange_od(350, 2500) is None


# =============================================================================
# Edge-offset formula
# =============================================================================

class TestEdgeOffset:

    def test_dn100_no_insulation_default_column(self):
        pipe = {"dn": 100, "rating": 150, "insulation": 0}
        # MROUND(114/2 + 0 + 330/2 + 100, 5) = MROUND(322, 5) = 320
        assert calculate_edge_offset(pipe, DEFAULT_STEEL_COLUMN_MM) == 320

    def test_dn100_with_insulation(self):
        pipe = {"dn": 100, "rating": 150, "insulation": 50}
        # MROUND(57 + 50 + 165 + 100, 5) = MROUND(372, 5) = 370
        assert calculate_edge_offset(pipe, DEFAULT_STEEL_COLUMN_MM) == 370

    def test_dn200_no_insulation(self):
        pipe = {"dn": 200, "rating": 150, "insulation": 0}
        # MROUND(219/2 + 0 + 165 + 100, 5) = MROUND(374.5, 5)
        # 374.5/5 = 74.9 → int(74.9+0.5)=int(75.4)=75 → 75*5=375
        assert calculate_edge_offset(pipe, DEFAULT_STEEL_COLUMN_MM) == 375

    def test_custom_steel_column(self):
        pipe = {"dn": 100, "rating": 150, "insulation": 0}
        # MROUND(57 + 0 + 125 + 100, 5) = MROUND(282, 5) = 280
        assert calculate_edge_offset(pipe, 250) == 280


# =============================================================================
# Pair-spacing formula
# =============================================================================

class TestPairSpacing:

    def test_two_identical_pipes_no_insulation(self):
        pipe = {"dn": 100, "rating": 150, "insulation": 0}
        # flange=230, OD=114
        # case_1 = case_2 = (230+114)/2 + 0+0+50 = 172+50 = 222
        # MROUND(222, 5) = 220
        assert calculate_pair_spacing(pipe, pipe) == 220

    def test_symmetric_pipes_with_insulation(self):
        pipe = {"dn": 200, "rating": 300, "insulation": 75}
        # flange=380, OD=219, ins=75
        # case_1=case_2 = (380+219)/2 + 75+75+50 = 299.5+200 = 499.5
        # MROUND(499.5, 5) = 500
        assert calculate_pair_spacing(pipe, pipe) == 500

    def test_asymmetric_pipes_takes_worst_case(self):
        pipe_a = {"dn": 100, "rating": 150, "insulation": 0}
        pipe_b = {"dn": 200, "rating": 300, "insulation": 50}
        # flange_a=230, OD_a=114, ins_a=0
        # flange_b=380, OD_b=219, ins_b=50
        # case_1 = (230+219)/2 + 0+50+50 = 224.5+100 = 324.5
        # case_2 = (380+114)/2 + 0+50+50 = 247+100 = 347
        # max = 347 → MROUND(347,5) = 345
        assert calculate_pair_spacing(pipe_a, pipe_b) == 345

    def test_asymmetric_spacing_is_order_independent(self):
        # Swapping A and B should give the same result since we take max of both cases
        pipe_a = {"dn": 100, "rating": 150, "insulation": 0}
        pipe_b = {"dn": 200, "rating": 300, "insulation": 50}
        assert calculate_pair_spacing(pipe_a, pipe_b) == calculate_pair_spacing(pipe_b, pipe_a)

    def test_high_pressure_flange_increases_spacing(self):
        pipe_std = {"dn": 100, "rating": 150,  "insulation": 0}
        pipe_hp  = {"dn": 100, "rating": 1500, "insulation": 0}
        pipe_nb  = {"dn": 100, "rating": 150,  "insulation": 0}
        spacing_std = calculate_pair_spacing(pipe_std, pipe_nb)
        spacing_hp  = calculate_pair_spacing(pipe_hp,  pipe_nb)
        assert spacing_hp >= spacing_std


# =============================================================================
# Per-pipe flange presence (Has Flange @ Section)
# =============================================================================

class TestPerPipeFlange:

    def test_default_includes_flange(self):
        # Absent has_flange == flange included (backward compatible).
        with_key = {"dn": 100, "rating": 150, "insulation": 0, "has_flange": True}
        without_key = {"dn": 100, "rating": 150, "insulation": 0}
        assert calculate_pair_spacing(with_key, with_key) \
            == calculate_pair_spacing(without_key, without_key)

    def test_no_flange_uses_bare_pipe_od(self):
        # Both pipes flangeless => bare-pipe staggered model.
        # DN100 OD=114, DN200 OD=219
        # case = (114+219)/2 + 0+0+50 = 166.5+50 = 216.5 -> MROUND(216.5,5)=215
        a = {"dn": 100, "rating": 150, "insulation": 0, "has_flange": False}
        b = {"dn": 200, "rating": 300, "insulation": 0, "has_flange": False}
        assert calculate_pair_spacing(a, b) == 215

    def test_no_flange_spacing_not_greater_than_flanged(self):
        a_f = {"dn": 100, "rating": 150, "insulation": 0, "has_flange": True}
        b_f = {"dn": 200, "rating": 300, "insulation": 0, "has_flange": True}
        a_n = {"dn": 100, "rating": 150, "insulation": 0, "has_flange": False}
        b_n = {"dn": 200, "rating": 300, "insulation": 0, "has_flange": False}
        assert calculate_pair_spacing(a_n, b_n) <= calculate_pair_spacing(a_f, b_f)

    def test_mixed_flange_is_between_all_and_none(self):
        a_f = {"dn": 100, "rating": 150, "insulation": 0, "has_flange": True}
        b_f = {"dn": 200, "rating": 300, "insulation": 0, "has_flange": True}
        a_n = {"dn": 100, "rating": 150, "insulation": 0, "has_flange": False}
        b_n = {"dn": 200, "rating": 300, "insulation": 0, "has_flange": False}
        # Only the larger-flange pipe (B) keeps its flange.
        b_only = {"dn": 200, "rating": 300, "insulation": 0, "has_flange": True}
        mixed = calculate_pair_spacing(a_n, b_only)
        assert calculate_pair_spacing(a_n, b_n) <= mixed <= calculate_pair_spacing(a_f, b_f)

    def test_no_flange_skips_nonstandard_flange_error(self):
        # DN90 has no CL900 flange; with has_flange=False it must not raise.
        a = {"dn": 90, "rating": 900, "insulation": 0, "has_flange": False}
        b = {"dn": 100, "rating": 150, "insulation": 0, "has_flange": False}
        spacing = calculate_pair_spacing(a, b)
        assert spacing > 0

    def test_flanged_nonstandard_still_raises(self):
        a = {"dn": 90, "rating": 900, "insulation": 0, "has_flange": True}
        b = {"dn": 100, "rating": 150, "insulation": 0, "has_flange": True}
        with pytest.raises(ValueError, match="not standardized"):
            calculate_pair_spacing(a, b)

    def test_full_rack_no_flange_reduces_or_equals_width(self):
        flanged = [
            {"dn": 200, "rating": 600, "insulation": 0, "has_flange": True},
            {"dn": 300, "rating": 600, "insulation": 0, "has_flange": True},
        ]
        bare = [
            {"dn": 200, "rating": 600, "insulation": 0, "has_flange": False},
            {"dn": 300, "rating": 600, "insulation": 0, "has_flange": False},
        ]
        assert calculate_rack(bare)["rack_width"] <= calculate_rack(flanged)["rack_width"]


# =============================================================================
# Full rack calculation — single pipe
# =============================================================================

class TestSinglePipe:

    def _pipe(self, dn=100, rating=150, insulation=0):
        return {"dn": dn, "rating": rating, "insulation": insulation}

    def test_basic_output_keys(self):
        r = calculate_rack([self._pipe()])
        for key in ("edge_offset", "spacings", "pipe_run", "pipe_buffer",
                    "inner_total", "expansion", "rack_width",
                    "steel_column", "expansion_pct", "warnings"):
            assert key in r, f"Missing key: {key}"

    def test_single_pipe_no_insulation(self):
        r = calculate_rack([self._pipe()])
        assert r["edge_offset"]  == 320
        assert r["spacings"]     == []
        assert r["pipe_run"]     == 0
        assert r["pipe_buffer"]  == 100   # (1+1)*50
        assert r["inner_total"]  == 420
        assert r["expansion"]    == 84    # MROUND(420*0.2, 1)
        assert r["rack_width"]   == 669   # 420+84+165

    def test_single_pipe_with_insulation(self):
        r = calculate_rack([self._pipe(insulation=50)])
        assert r["edge_offset"]  == 370
        assert r["inner_total"]  == 470
        assert r["expansion"]    == 94    # MROUND(470*0.2, 1)
        assert r["rack_width"]   == 729   # 470+94+165

    def test_single_large_bore_dn650_series_a(self):
        r = calculate_rack([self._pipe(dn=650, rating="150A")])
        assert r["edge_offset"]  == 595
        assert r["inner_total"]  == 695
        assert r["rack_width"]   == 999

    def test_single_pipe_custom_expansion(self):
        r = calculate_rack([self._pipe()], expansion_pct=10)
        assert r["expansion_pct"] == 10
        # inner_total = 420 (default column 330), expansion = MROUND(420*0.1, 1) = 42
        assert r["expansion"]     == 42
        assert r["rack_width"]    == 627   # 420 + 42 + 165

    def test_single_pipe_custom_steel_column(self):
        r = calculate_rack([self._pipe()], steel_column_mm=250)
        assert r["steel_column"]  == 250
        assert r["edge_offset"]   == 280   # MROUND(57+0+125+100,5)
        assert r["inner_total"]   == 380   # 280+0+100
        assert r["expansion"]     == 76    # MROUND(380*0.2,1)
        assert r["rack_width"]    == 581   # 380+76+125


# =============================================================================
# Full rack calculation — multiple pipes
# =============================================================================

class TestMultiplePipes:

    def _pipe(self, dn=100, rating=150, insulation=0):
        return {"dn": dn, "rating": rating, "insulation": insulation}

    def test_two_pipe_spacing_in_spacings_list(self):
        r = calculate_rack([self._pipe(), self._pipe(dn=200, rating=300, insulation=50)])
        assert len(r["spacings"]) == 1
        assert r["spacings"][0] == 345

    def test_two_pipe_totals(self):
        r = calculate_rack([self._pipe(), self._pipe(dn=200, rating=300, insulation=50)])
        assert r["edge_offset"]  == 320
        assert r["pipe_run"]     == 345
        assert r["pipe_buffer"]  == 150   # (2+1)*50
        assert r["inner_total"]  == 815
        assert r["expansion"]    == 163
        assert r["rack_width"]   == 1143

    def test_three_identical_pipes(self):
        r = calculate_rack([self._pipe()] * 3)
        assert len(r["spacings"]) == 2
        assert r["spacings"] == [220, 220]
        assert r["pipe_buffer"]  == 200   # (3+1)*50
        assert r["inner_total"]  == 960   # 320+220+220+200
        assert r["expansion"]    == 192
        assert r["rack_width"]   == 1317

    def test_three_mixed_pipes_with_insulation(self):
        pipes = [
            self._pipe(dn=100, rating=150, insulation=50),
            self._pipe(dn=200, rating=300, insulation=0),
            self._pipe(dn=100, rating=150, insulation=50),
        ]
        r = calculate_rack(pipes)
        assert r["edge_offset"]  == 370
        assert len(r["spacings"]) == 2
        assert r["spacings"][0] == r["spacings"][1]  # symmetric layout

    def test_symmetric_layout_gives_equal_spacings(self):
        pipes = [
            self._pipe(dn=200, rating=300, insulation=75),
            self._pipe(dn=200, rating=300, insulation=75),
        ]
        r = calculate_rack(pipes)
        assert r["edge_offset"]  == 450
        assert r["spacings"]     == [500]
        assert r["inner_total"]  == 1100
        assert r["expansion"]    == 220
        assert r["rack_width"]   == 1485


# =============================================================================
# Insulation effects on width
# =============================================================================

class TestInsulationEffects:

    def test_insulation_increases_edge_offset(self):
        r0 = calculate_rack([{"dn": 100, "rating": 150, "insulation": 0}])
        r1 = calculate_rack([{"dn": 100, "rating": 150, "insulation": 100}])
        assert r1["edge_offset"] > r0["edge_offset"]

    def test_insulation_increases_pair_spacing(self):
        pipe_bare = {"dn": 100, "rating": 150, "insulation": 0}
        pipe_ins  = {"dn": 100, "rating": 150, "insulation": 100}
        s_bare = calculate_pair_spacing(pipe_bare, pipe_bare)
        s_ins  = calculate_pair_spacing(pipe_ins,  pipe_ins)
        assert s_ins > s_bare

    def test_insulation_increases_final_rack_width(self):
        r0 = calculate_rack([{"dn": 200, "rating": 300, "insulation": 0}] * 2)
        r1 = calculate_rack([{"dn": 200, "rating": 300, "insulation": 50}] * 2)
        assert r1["rack_width"] > r0["rack_width"]


# =============================================================================
# Flange-rating effects
# =============================================================================

class TestFlangeRatingEffects:

    def test_higher_flange_class_increases_spacing(self):
        pipe_150 = {"dn": 100, "rating": 150,  "insulation": 0}
        pipe_600 = {"dn": 100, "rating": 600,  "insulation": 0}
        filler   = {"dn": 100, "rating": 150,  "insulation": 0}
        s150 = calculate_pair_spacing(pipe_150, filler)
        s600 = calculate_pair_spacing(pipe_600, filler)
        assert s600 >= s150

    def test_b1647_series_b_larger_pipe_calculates(self):
        pipe = {"dn": 700, "rating": "150B", "insulation": 0}
        r = calculate_rack([pipe])
        assert r["rack_width"] > 0
        assert r["edge_offset"] > 0


# =============================================================================
# Error / edge cases
# =============================================================================

class TestErrorCases:

    def test_empty_pipe_list_raises(self):
        with pytest.raises(ValueError, match="At least one pipe"):
            calculate_rack([])

    def test_too_many_pipes_raises(self):
        pipes = [{"dn": 100, "rating": 150, "insulation": 0}] * (MAX_PIPES_PER_TIER + 1)
        with pytest.raises(ValueError, match="Maximum"):
            calculate_rack(pipes)

    def test_exactly_max_pipes_no_exception(self):
        pipes = [{"dn": 100, "rating": 150, "insulation": 0}] * MAX_PIPES_PER_TIER
        r = calculate_rack(pipes)
        assert r["rack_width"] > 0
        assert len(r["warnings"]) > 0  # capacity warning expected

    def test_non_standard_flange_combination_raises(self):
        # DN 90 has no 900 rating in the B16.5 table
        pipe_a = {"dn": 90, "rating": 900, "insulation": 0}
        pipe_b = {"dn": 100, "rating": 150, "insulation": 0}
        with pytest.raises(ValueError, match="not standardized"):
            calculate_pair_spacing(pipe_a, pipe_b)

    def test_warnings_empty_for_normal_rack(self):
        r = calculate_rack([{"dn": 100, "rating": 150, "insulation": 0}] * 2)
        assert r["warnings"] == []

    def test_rack_width_is_integer(self):
        r = calculate_rack([{"dn": 100, "rating": 150, "insulation": 0}])
        assert isinstance(r["rack_width"], int)

    def test_expansion_is_integer(self):
        r = calculate_rack([{"dn": 100, "rating": 150, "insulation": 0}])
        assert isinstance(r["expansion"], int)


# =============================================================================
# Formula consistency check
# =============================================================================

class TestFormulaConsistency:

    def test_inner_total_equals_edge_plus_run_plus_buffer(self):
        pipes = [
            {"dn": 100, "rating": 150, "insulation": 0},
            {"dn": 200, "rating": 300, "insulation": 50},
            {"dn": 150, "rating": 150, "insulation": 25},
        ]
        r = calculate_rack(pipes)
        expected = r["edge_offset"] + r["pipe_run"] + r["pipe_buffer"]
        assert r["inner_total"] == expected

    def test_pipe_run_equals_sum_of_spacings(self):
        pipes = [{"dn": 100, "rating": 150, "insulation": 0}] * 4
        r = calculate_rack(pipes)
        assert r["pipe_run"] == sum(r["spacings"])

    def test_pipe_buffer_equals_n_plus_1_times_50(self):
        for n in (1, 2, 4, 8):
            pipes = [{"dn": 100, "rating": 150, "insulation": 0}] * n
            r = calculate_rack(pipes)
            assert r["pipe_buffer"] == (n + 1) * PER_PIPE_BUFFER_MM

    def test_rack_width_formula(self):
        pipes = [{"dn": 100, "rating": 150, "insulation": 0}]
        r = calculate_rack(pipes)
        expected = int(round(r["inner_total"] + r["expansion"] + r["steel_column"] / 2))
        assert r["rack_width"] == expected


# =============================================================================
# Eurocode steel profile database
# =============================================================================

class TestSteelProfiles:

    # ── Profile width lookups ─────────────────────────────────────────────────

    def test_hea_300_width(self):
        assert get_profile_width("HEA", "300") == 300

    def test_heb_300_width(self):
        assert get_profile_width("HEB", "300") == 300

    def test_ipe_300_width(self):
        assert get_profile_width("IPE", "300") == 150

    def test_hem_300_width(self):
        assert get_profile_width("HEM", "300") == 310

    def test_hea_200_width(self):
        # HEA 200: b = 200 mm (matches size designation)
        assert get_profile_width("HEA", "200") == 200

    def test_heb_200_width(self):
        assert get_profile_width("HEB", "200") == 200

    def test_ipe_200_width(self):
        # IPE 200: b = 100 mm (narrow flange)
        assert get_profile_width("IPE", "200") == 100

    def test_hem_100_width(self):
        # HEM 100 is heavier: b = 106 mm (wider than designation)
        assert get_profile_width("HEM", "100") == 106

    def test_hea_large_size_b_capped_at_300(self):
        # HEA 320 and above: b stays at 300 mm
        assert get_profile_width("HEA", "320") == 300
        assert get_profile_width("HEA", "1000") == 300

    def test_heb_large_size_b_capped_at_300(self):
        assert get_profile_width("HEB", "320") == 300
        assert get_profile_width("HEB", "1000") == 300

    def test_case_insensitive_family(self):
        assert get_profile_width("hea", "300") == 300
        assert get_profile_width("Heb", "300") == 300
        assert get_profile_width("ipe", "300") == 150

    def test_unknown_size_raises(self):
        with pytest.raises(ValueError, match="not found"):
            get_profile_width("HEA", "999")

    def test_unknown_family_raises(self):
        with pytest.raises(ValueError, match="Unknown profile family"):
            get_profile_width("XYZ", "300")

    # ── Profile data completeness ─────────────────────────────────────────────

    def test_all_families_present(self):
        for family in ("IPE", "HEA", "HEB", "HEM"):
            assert family in PROFILES, f"Missing family {family}"

    def test_ipe_has_18_sizes(self):
        assert len(PROFILES["IPE"]) == 18  # IPE 80 through IPE 600

    def test_hea_has_24_sizes(self):
        assert len(PROFILES["HEA"]) == 24  # HEA 100 through HEA 1000

    def test_heb_has_24_sizes(self):
        assert len(PROFILES["HEB"]) == 24

    def test_hem_has_24_sizes(self):
        assert len(PROFILES["HEM"]) == 24

    def test_all_entries_have_required_keys(self):
        for family, entries in PROFILES.items():
            for p in entries:
                for key in ("size", "h", "b", "tw", "tf"):
                    assert key in p, f"{family} entry missing key '{key}': {p}"

    def test_flange_width_b_is_positive_int(self):
        for family, entries in PROFILES.items():
            for p in entries:
                assert isinstance(p["b"], int) and p["b"] > 0

    # ── profiles_for_js helper ────────────────────────────────────────────────

    def test_profiles_for_js_returns_all_families(self):
        js = profiles_for_js()
        for family in ("IPE", "HEA", "HEB", "HEM"):
            assert family in js

    def test_profiles_for_js_entry_has_size_and_b(self):
        js = profiles_for_js()
        for family, entries in js.items():
            for entry in entries:
                assert "size" in entry and "b" in entry

    def test_profiles_for_js_has_no_tw_tf(self):
        # JS payload should be lightweight — no thickness data needed in frontend
        js = profiles_for_js()
        for entries in js.values():
            for e in entries:
                assert "tw" not in e and "tf" not in e

    # ── Integration: profile width used in rack formula ───────────────────────

    def test_hea_300_width_in_calculate_rack(self):
        b = get_profile_width("HEA", "300")
        assert b == 300
        r = calculate_rack([{"dn": 100, "rating": 150, "insulation": 0}], steel_column_mm=b)
        assert r["steel_column"] == 300
        assert r["rack_width"] > 0

    def test_ipe_300_width_in_calculate_rack(self):
        b = get_profile_width("IPE", "300")
        assert b == 150
        r = calculate_rack([{"dn": 100, "rating": 150, "insulation": 0}], steel_column_mm=b)
        assert r["steel_column"] == 150

    def test_custom_column_width_bypasses_profile_lookup(self):
        # Custom path: pass steel_column_mm directly — no profile database involved
        r = calculate_rack([{"dn": 100, "rating": 150, "insulation": 0}], steel_column_mm=250)
        assert r["steel_column"] == 250
        assert r["edge_offset"] == 280   # MROUND(57+0+125+100, 5)

    # ── Future Spare Space rename does not change calculation ─────────────────

    def test_future_spare_space_25_pct(self):
        # "Future Spare Space 25%" is just expansion_pct=25 — formula unchanged
        r = calculate_rack([{"dn": 100, "rating": 150, "insulation": 0}], expansion_pct=25)
        # inner_total = 420, expansion = MROUND(420 * 0.25, 1) = 105
        assert r["expansion"] == 105
        assert r["expansion_pct"] == 25

    def test_future_spare_space_0_pct(self):
        r = calculate_rack([{"dn": 100, "rating": 150, "insulation": 0}], expansion_pct=0)
        assert r["expansion"] == 0

    def test_future_spare_space_same_result_as_old_expansion_pct(self):
        # Renaming the label must not change the numeric result
        r1 = calculate_rack([{"dn": 100, "rating": 150, "insulation": 0}], expansion_pct=20)
        r2 = calculate_rack([{"dn": 100, "rating": 150, "insulation": 0}], expansion_pct=20)
        assert r1["rack_width"] == r2["rack_width"]
        assert r1["expansion"] == r2["expansion"]


# =============================================================================
# Spare space location — diagram only, no formula change
# =============================================================================

_SINGLE_PIPE = [{"dn": 100, "rating": 150, "insulation": 0}]
_TWO_PIPES   = [{"dn": 100, "rating": 150, "insulation": 0},
                {"dn": 200, "rating": 300, "insulation": 50}]


class TestSpareSpaceLocation:

    # ── Custom column width ────────────────────────────────────────────────────

    def test_custom_column_250_used_in_formula(self):
        r = calculate_rack(_SINGLE_PIPE, steel_column_mm=250)
        assert r["steel_column"] == 250

    def test_custom_column_produces_different_rack_width_than_default(self):
        r_default = calculate_rack(_SINGLE_PIPE)
        r_custom  = calculate_rack(_SINGLE_PIPE, steel_column_mm=250)
        assert r_default["rack_width"] != r_custom["rack_width"]

    def test_custom_column_hea_profile_still_works(self):
        b = get_profile_width("HEA", "300")
        r = calculate_rack(_SINGLE_PIPE, steel_column_mm=b)
        assert r["steel_column"] == b
        assert r["rack_width"] > 0

    # ── spare_space_location does not change rack width ────────────────────────

    def test_right_location_does_not_change_rack_width(self):
        r = calculate_rack(_SINGLE_PIPE, expansion_pct=20)
        rw = r["rack_width"]
        _ = generate_diagram(_SINGLE_PIPE, r, spare_space_location='right')
        assert r["rack_width"] == rw  # result dict not mutated

    def test_center_location_does_not_change_rack_width(self):
        r = calculate_rack(_SINGLE_PIPE, expansion_pct=20)
        rw = r["rack_width"]
        _ = generate_diagram(_SINGLE_PIPE, r, spare_space_location='center')
        assert r["rack_width"] == rw

    def test_right_and_center_give_same_rack_width(self):
        r1 = calculate_rack(_TWO_PIPES, expansion_pct=20)
        r2 = calculate_rack(_TWO_PIPES, expansion_pct=20)
        assert r1["rack_width"] == r2["rack_width"]

    # ── SVG output correctness ────────────────────────────────────────────────

    def test_svg_contains_future_spare_space_label_right(self):
        r = calculate_rack(_SINGLE_PIPE, expansion_pct=20)
        svg = generate_diagram(_SINGLE_PIPE, r, spare_space_location='right')
        assert "Future spare space" in svg

    def test_svg_contains_future_spare_space_label_center(self):
        r = calculate_rack(_SINGLE_PIPE, expansion_pct=20)
        svg = generate_diagram(_SINGLE_PIPE, r, spare_space_location='center')
        assert "Future spare space" in svg

    def test_svg_right_and_center_are_different(self):
        # With >=2 pipes, 'center' inserts the spare zone into an internal
        # gap, which differs from the 'right' (after-last-pipe) placement.
        r = calculate_rack(_TWO_PIPES, expansion_pct=20)
        svg_r = generate_diagram(_TWO_PIPES, r, spare_space_location='right')
        svg_c = generate_diagram(_TWO_PIPES, r, spare_space_location='center')
        assert svg_r != svg_c

    def test_svg_single_pipe_center_falls_back_to_right(self):
        # A single pipe has no internal gap to insert a center spare zone
        # into, so 'center' falls back to the 'right' placement.
        r = calculate_rack(_SINGLE_PIPE, expansion_pct=20)
        svg_r = generate_diagram(_SINGLE_PIPE, r, spare_space_location='right')
        svg_c = generate_diagram(_SINGLE_PIPE, r, spare_space_location='center')
        assert svg_r == svg_c

    def test_svg_no_spare_zone_when_expansion_zero(self):
        r = calculate_rack(_SINGLE_PIPE, expansion_pct=0)
        svg = generate_diagram(_SINGLE_PIPE, r, spare_space_location='right')
        assert "Future spare space" not in svg
        # The zone rect (fill="url(#spareHatch)") must not be rendered
        assert 'fill="url(#spareHatch)"' not in svg

    def test_svg_default_location_is_right(self):
        r = calculate_rack(_SINGLE_PIPE, expansion_pct=20)
        svg_default = generate_diagram(_SINGLE_PIPE, r)
        svg_right   = generate_diagram(_SINGLE_PIPE, r, spare_space_location='right')
        assert svg_default == svg_right

    def test_svg_is_valid_svg_element(self):
        r = calculate_rack(_TWO_PIPES, expansion_pct=20)
        svg = generate_diagram(_TWO_PIPES, r, spare_space_location='right')
        assert svg.startswith('<svg')
        assert svg.endswith('</svg>')

    def test_svg_center_contains_center_zone(self):
        r = calculate_rack(_TWO_PIPES, expansion_pct=20)
        svg = generate_diagram(_TWO_PIPES, r, spare_space_location='center')
        # Center: spare zone is inserted into the gap between the two pipes;
        # right: spare zone sits after the last pipe. They differ.
        svg_r = generate_diagram(_TWO_PIPES, r, spare_space_location='right')
        assert svg != svg_r
