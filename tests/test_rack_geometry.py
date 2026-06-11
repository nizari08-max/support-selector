"""
Tests for the rack schematic geometry model (rack_geometry.py).

These tests verify the geometry layer that sits between calculate_rack()
and the SVG renderer:
  - real CL-to-CL coordinates (column CL -> pipe1 CL, pipe-to-pipe CL-CL)
  - non-overlapping spare-space zones for both 'right' and 'center'
  - gap-insertion semantics for 'center' (pipe shift, single-pipe fallback)
  - geometry coverage across a range of pipe counts / sizes / ratings
"""

import pytest

from rack_calculator import calculate_rack
from rack_geometry import build_geometry_model
from rack_diagram import generate_diagram


def _pipe(dn, rating=150, insulation=0):
    return {"dn": dn, "rating": rating, "insulation": insulation}


# =============================================================================
# Coordinate model: column CL -> pipe1 CL, pipe-to-pipe CL-CL
# =============================================================================

class TestCoordinateModel:

    def test_first_dimension_is_column_cl_to_pipe1_cl(self):
        pipes = [_pipe(100)]
        result = calculate_rack(pipes)
        geo = build_geometry_model(pipes, result)

        first_dim = geo.top_dimensions[0]
        assert first_dim.x1 == geo.column_cl_left
        assert first_dim.x2 == geo.pipes[0].cl_x
        assert first_dim.label == f"{result['first_gap']} CL-CL"

    def test_pipe1_cl_minus_column_cl_equals_first_gap(self):
        pipes = [_pipe(300, rating=600)]
        result = calculate_rack(pipes)
        geo = build_geometry_model(pipes, result)

        assert geo.pipes[0].cl_x - geo.column_cl_left == result['first_gap']

    def test_pipe_to_pipe_dimensions_are_cl_to_cl(self):
        pipes = [_pipe(100), _pipe(200, rating=300), _pipe(50)]
        result = calculate_rack(pipes)
        geo = build_geometry_model(pipes, result, spare_space_location='right')

        # No spare inserted (location='right'), so calc_cl_x == cl_x for all pipes
        for i, s in enumerate(result['spacings']):
            p_a, p_b = geo.pipes[i], geo.pipes[i + 1]
            assert p_b.cl_x - p_a.cl_x == s

    def test_column_cl_to_column_cl_equals_rack_width(self):
        pipes = [_pipe(100), _pipe(200)]
        result = calculate_rack(pipes)
        geo = build_geometry_model(pipes, result)

        # x=0 is the left column CL; x=rack_width is the right column CL.
        assert geo.column_cl_left == 0
        assert geo.column_cl_right == result['rack_width']
        assert geo.column_cl_right - geo.column_cl_left == result['rack_width']

    def test_pipe_cls_match_calc_cl_when_no_spare(self):
        pipes = [_pipe(100), _pipe(200)]
        result = calculate_rack(pipes, expansion_pct=0)
        geo = build_geometry_model(pipes, result, spare_space_location='right')

        for p in geo.pipes:
            assert p.cl_x == p.calc_cl_x


# =============================================================================
# Spare space: 'right' placement
# =============================================================================

class TestSpareSpaceRight:

    def test_right_zone_spans_inner_total_to_right_column_cl(self):
        pipes = [_pipe(100), _pipe(200)]
        result = calculate_rack(pipes, expansion_pct=20)
        geo = build_geometry_model(pipes, result, spare_space_location='right')

        assert len(geo.spare_zones) == 1
        zone = geo.spare_zones[0]
        assert zone.x1 == result['inner_total']
        # Spare zone ends at the right column's near (left) edge, i.e.
        # one column-half-width before the right column centerline.
        assert zone.x2 == geo.column_cl_right - geo.column_width / 2
        assert zone.width == result['expansion']

    def test_right_zone_does_not_overlap_any_pipe(self):
        pipes = [_pipe(100), _pipe(200), _pipe(50)]
        result = calculate_rack(pipes, expansion_pct=20)
        geo = build_geometry_model(pipes, result, spare_space_location='right')

        zone = geo.spare_zones[0]
        for p in geo.pipes:
            assert not (zone.x1 < p.cl_x < zone.x2)

    def test_no_spare_zone_when_expansion_zero(self):
        pipes = [_pipe(100)]
        result = calculate_rack(pipes, expansion_pct=0)
        geo = build_geometry_model(pipes, result, spare_space_location='right')

        assert geo.spare_zones == []
        assert geo.expansion == 0


# =============================================================================
# Spare space: 'center' gap-insertion placement
# =============================================================================

class TestSpareSpaceCenterGapInsertion:

    def test_single_pipe_falls_back_to_right(self):
        pipes = [_pipe(100)]
        result = calculate_rack(pipes, expansion_pct=20)
        geo_center = build_geometry_model(pipes, result, spare_space_location='center')
        geo_right = build_geometry_model(pipes, result, spare_space_location='right')

        assert geo_center.spare_zones[0].x1 == geo_right.spare_zones[0].x1
        assert geo_center.spare_zones[0].x2 == geo_right.spare_zones[0].x2
        assert geo_center.spare_zones[0].gap_index == -1
        assert geo_center.pipes[0].cl_x == geo_center.pipes[0].calc_cl_x

    def test_two_pipes_inserts_into_only_gap(self):
        pipes = [_pipe(100), _pipe(200, rating=300)]
        result = calculate_rack(pipes, expansion_pct=20)
        geo = build_geometry_model(pipes, result, spare_space_location='center')

        zone = geo.spare_zones[0]
        assert zone.gap_index == 0
        # Pipe 0 is unshifted; pipe 1 shifts right by `expansion`.
        assert geo.pipes[0].cl_x == geo.pipes[0].calc_cl_x
        assert geo.pipes[1].cl_x == geo.pipes[1].calc_cl_x + result['expansion']
        # Spare zone sits strictly between pipe0 and shifted pipe1.
        assert zone.width == result['expansion']
        assert geo.pipes[0].cl_x <= zone.x1
        assert zone.x2 <= geo.pipes[1].cl_x

    def test_center_zone_does_not_overlap_any_pipe(self):
        pipes = [_pipe(100), _pipe(200, rating=300), _pipe(50), _pipe(80, insulation=25)]
        result = calculate_rack(pipes, expansion_pct=20)
        geo = build_geometry_model(pipes, result, spare_space_location='center')

        zone = geo.spare_zones[0]
        for p in geo.pipes:
            assert not (zone.x1 < p.cl_x < zone.x2)

    def test_center_zone_keeps_rack_width_unchanged(self):
        pipes = [_pipe(100), _pipe(200), _pipe(300, rating=600)]
        result = calculate_rack(pipes, expansion_pct=20)
        geo = build_geometry_model(pipes, result, spare_space_location='center')

        assert geo.rack_width == result['rack_width']
        assert geo.column_cl_left == 0
        assert geo.column_cl_right == result['rack_width']

    def test_center_zone_keeps_last_pipe_clear_of_right_column(self):
        pipes = [_pipe(100), _pipe(200), _pipe(300, rating=600)]
        result = calculate_rack(pipes, expansion_pct=20)
        geo = build_geometry_model(pipes, result, spare_space_location='center')

        assert geo.pipes[-1].cl_x < geo.column_cl_right

    @pytest.mark.parametrize("n,expected_gap", [(4, 1), (5, 2), (6, 2)])
    def test_center_picks_middle_gap_by_index(self, n, expected_gap):
        # Spare zone is inserted into the gap nearest the middle of the pipe
        # list, by index (not by geometric position).
        pipes = [_pipe(50 + (i % 5) * 50, rating=150) for i in range(n)]
        result = calculate_rack(pipes, expansion_pct=20)
        geo = build_geometry_model(pipes, result, spare_space_location='center')

        zone = geo.spare_zones[0]
        assert zone.gap_index == expected_gap

    @pytest.mark.parametrize("n", [3, 4, 8])
    def test_center_bay_between_envelopes_and_non_overlapping(self, n):
        from rack_geometry import _envelope_radius
        pipes = [_pipe(50 + (i % 5) * 50, rating=150) for i in range(n)]
        result = calculate_rack(pipes, expansion_pct=20)
        geo = build_geometry_model(pipes, result, spare_space_location='center')

        zone = geo.spare_zones[0]
        assert zone.width == result['expansion']
        assert zone.gap_index == (n - 1) // 2

        # Bay does not overlap any pipe centerline, and the rack stays the
        # same overall width.
        for p in geo.pipes:
            assert not (zone.x1 < p.cl_x < zone.x2)
        assert geo.column_cl_right - geo.column_cl_left == result['rack_width']

        # Bay sits strictly between the flanking pipes' CLs.
        gap = zone.gap_index
        assert geo.pipes[gap].cl_x <= zone.x1
        assert zone.x2 <= geo.pipes[gap + 1].cl_x

        # Bay does not overlap either flanking pipe's outer envelope, and
        # clearance to each envelope is balanced (unless a warning was
        # raised because there isn't enough room).
        r_left = _envelope_radius(pipes[gap])
        r_right = _envelope_radius(pipes[gap + 1])
        left_clearance = zone.x1 - (geo.pipes[gap].cl_x + r_left)
        right_clearance = (geo.pipes[gap + 1].cl_x - r_right) - zone.x2
        if not geo.warnings:
            assert left_clearance >= -1e-6
            assert right_clearance >= -1e-6
            assert left_clearance == pytest.approx(right_clearance, abs=1e-6)

        # Pipes split cleanly into a left group (unshifted) and a right
        # group (shifted right by `expansion`).
        for i, p in enumerate(geo.pipes):
            if i <= gap:
                assert p.cl_x == p.calc_cl_x
            else:
                assert p.cl_x == p.calc_cl_x + result['expansion']

    def test_center_bottom_dimensions(self):
        pipes = [_pipe(100), _pipe(200, rating=300), _pipe(50)]
        result = calculate_rack(pipes, expansion_pct=20)
        geo = build_geometry_model(pipes, result, spare_space_location='center')

        zone = geo.spare_zones[0]
        occ_dim, rack_dim, spare_dim = geo.bottom_dimensions

        assert occ_dim.label == f"Occupied Width = {result['occupied_width']} mm"
        assert occ_dim.style == "annotation"

        assert rack_dim.x1 == geo.column_cl_left
        assert rack_dim.x2 == geo.column_cl_right
        assert str(result['rack_width']) in rack_dim.label
        assert rack_dim.style == "total"

        assert spare_dim.x1 == zone.x1
        assert spare_dim.x2 == zone.x2
        assert spare_dim.style == "spare"

    def test_top_dimension_for_inserted_gap_splits_calculated_spacing(self):
        pipes = [_pipe(100), _pipe(200, rating=300)]
        result = calculate_rack(pipes, expansion_pct=20)
        geo = build_geometry_model(pipes, result, spare_space_location='center')

        # top_dimensions[0] = column->pipe1; the remaining dims flank the
        # spare bay and together cover the original CL-CL spacing.
        remaining = geo.top_dimensions[1:]
        assert 1 <= len(remaining) <= 2
        total = sum(d.x2 - d.x1 for d in remaining)
        assert total == result['spacings'][0]
        for d in remaining:
            assert int(d.label) == d.x2 - d.x1


# =============================================================================
# Bottom dimensions: occupied width / rack width
# =============================================================================

class TestBottomDimensions:

    def test_occupied_width_dimension(self):
        pipes = [_pipe(100), _pipe(200)]
        result = calculate_rack(pipes, expansion_pct=20)
        geo = build_geometry_model(pipes, result)

        occ = geo.bottom_dimensions[0]
        assert occ.x1 == geo.column_cl_left
        assert occ.x2 == geo.column_cl_right
        assert occ.style == "annotation"
        assert occ.label == f"Occupied Width = {result['occupied_width']} mm"

    def test_rack_width_dimension(self):
        pipes = [_pipe(100)]
        result = calculate_rack(pipes, expansion_pct=20)
        geo = build_geometry_model(pipes, result)

        rw = geo.bottom_dimensions[1]
        assert rw.x1 == geo.column_cl_left
        assert rw.x2 == geo.column_cl_right
        assert str(result['rack_width']) in rw.label


# =============================================================================
# Edge cases / size matrix
# =============================================================================

class TestGeometryEdgeCases:

    def test_one_pipe(self):
        pipes = [_pipe(50)]
        result = calculate_rack(pipes)
        geo = build_geometry_model(pipes, result)
        assert len(geo.pipes) == 1
        assert len(geo.top_dimensions) == 1  # only the column->pipe1 dim

    def test_two_pipes(self):
        pipes = [_pipe(50), _pipe(100)]
        result = calculate_rack(pipes)
        geo = build_geometry_model(pipes, result)
        assert len(geo.pipes) == 2
        assert len(geo.top_dimensions) == 2

    def test_six_pipes(self):
        pipes = [_pipe(50 + 50 * i) for i in range(6)]
        result = calculate_rack(pipes)
        geo = build_geometry_model(pipes, result)
        assert len(geo.pipes) == 6
        assert len(geo.top_dimensions) == 6

    def test_sixteen_pipes_max(self):
        pipes = [_pipe(50) for _ in range(16)]
        result = calculate_rack(pipes)
        geo = build_geometry_model(pipes, result)
        assert len(geo.pipes) == 16
        assert len(geo.top_dimensions) == 16
        # Sequential CL-CL dimensions never overlap in mm-space by construction.
        for i, s in enumerate(result['spacings']):
            assert geo.pipes[i + 1].cl_x - geo.pipes[i].cl_x == s

    def test_dn50_bare(self):
        pipes = [_pipe(15), _pipe(15)]  # smallest DN available
        result = calculate_rack(pipes)
        geo = build_geometry_model(pipes, result)
        assert geo.pipes[0].pipe_od == 21
        assert geo.pipes[0].ins_od == geo.pipes[0].pipe_od

    def test_dn1000_bare(self):
        pipes = [_pipe(1000, rating='150A')]
        result = calculate_rack(pipes)
        geo = build_geometry_model(pipes, result)
        assert geo.pipes[0].pipe_od == 1016
        assert geo.pipes[0].flange_od == 1290

    def test_mixed_dn50_dn1000(self):
        pipes = [_pipe(15), _pipe(1000, rating='150A')]
        result = calculate_rack(pipes)
        geo = build_geometry_model(pipes, result)
        assert geo.pipes[0].pipe_od < geo.pipes[1].pipe_od
        assert geo.pipes[1].cl_x - geo.pipes[0].cl_x == result['spacings'][0]

    def test_insulated_pipe_ins_od(self):
        pipes = [_pipe(100, insulation=50)]
        result = calculate_rack(pipes)
        geo = build_geometry_model(pipes, result)
        p = geo.pipes[0]
        assert p.ins_od == p.pipe_od + 100
        assert p.label_ins == "Ins 50 mm"

    def test_class_150_vs_class_2500_flange_od(self):
        p150 = _pipe(100, rating=150)
        p2500 = _pipe(100, rating=2500)
        r150 = calculate_rack([p150])
        r2500 = calculate_rack([p2500])
        geo150 = build_geometry_model([p150], r150)
        geo2500 = build_geometry_model([p2500], r2500)
        assert geo2500.pipes[0].flange_od > geo150.pipes[0].flange_od

    def test_future_spare_zero_percent(self):
        pipes = [_pipe(100)]
        result = calculate_rack(pipes, expansion_pct=0)
        geo = build_geometry_model(pipes, result, spare_space_location='right')
        assert geo.spare_zones == []

    def test_future_spare_twenty_percent(self):
        pipes = [_pipe(100)]
        result = calculate_rack(pipes, expansion_pct=20)
        geo = build_geometry_model(pipes, result, spare_space_location='right')
        assert geo.spare_zones[0].width == result['expansion']

    def test_future_spare_fifty_percent(self):
        pipes = [_pipe(100)]
        result = calculate_rack(pipes, expansion_pct=50)
        geo = build_geometry_model(pipes, result, spare_space_location='right')
        assert geo.spare_zones[0].width == result['expansion']
        assert geo.spare_zones[0].x2 == geo.column_cl_right - geo.column_width / 2

    def test_custom_column_width(self):
        pipes = [_pipe(100)]
        result = calculate_rack(pipes, steel_column_mm=400)
        geo = build_geometry_model(pipes, result)
        assert geo.column_width == 400
        assert geo.column_cl_left == 0
        assert geo.column_cl_right == result['rack_width']

    def test_calculation_results_unchanged_by_geometry(self):
        pipes = [_pipe(100), _pipe(200, rating=600, insulation=50)]
        result = calculate_rack(pipes, expansion_pct=20)
        before = dict(result)
        build_geometry_model(pipes, result, spare_space_location='center')
        build_geometry_model(pipes, result, spare_space_location='right')
        assert result == before


# =============================================================================
# SVG smoke tests across the matrix (rendering must not raise)
# =============================================================================

class TestSvgRendersForMatrix:

    @pytest.mark.parametrize("n", [1, 2, 6, 16])
    def test_pipe_counts(self, n):
        pipes = [_pipe(50 + (i % 5) * 50, rating=150) for i in range(n)]
        result = calculate_rack(pipes, expansion_pct=20)
        for loc in ('right', 'center'):
            svg = generate_diagram(pipes, result, spare_space_location=loc)
            assert svg.startswith('<svg')
            assert svg.endswith('</svg>')

    @pytest.mark.parametrize("expansion_pct", [0, 20, 50])
    def test_expansion_levels(self, expansion_pct):
        pipes = [_pipe(100), _pipe(200, rating=300)]
        result = calculate_rack(pipes, expansion_pct=expansion_pct)
        for loc in ('right', 'center'):
            svg = generate_diagram(pipes, result, spare_space_location=loc)
            assert svg.startswith('<svg')

    def test_dn50_and_dn1000_mixed_renders(self):
        # A small DN15 pipe alongside several DN1000 pipes drives the scale
        # low enough that DN15's true-scale radius falls below the
        # minimum-visual-size floor.
        pipes = [_pipe(15)] + [_pipe(1000, rating='150A')] * 3
        result = calculate_rack(pipes, expansion_pct=20)
        svg = generate_diagram(pipes, result)
        assert "Note: small-diameter pipes shown enlarged" in svg

    def test_high_rating_large_flange_renders(self):
        pipes = [_pipe(600, rating=1500), _pipe(600, rating=1500)]
        result = calculate_rack(pipes, expansion_pct=20)
        svg = generate_diagram(pipes, result)
        assert svg.startswith('<svg')

    def test_eurocode_profiles_render(self):
        from structural_profiles import get_profile_width
        pipes = [_pipe(100), _pipe(200)]
        for family, size in (("HEA", "300"), ("HEB", "300"), ("HEM", "300"), ("IPE", "300")):
            col = get_profile_width(family, size)
            result = calculate_rack(pipes, steel_column_mm=col)
            svg = generate_diagram(pipes, result)
            assert svg.startswith('<svg')


# =============================================================================
# SVG envelope-overlap prevention (rack_diagram radius capping)
# =============================================================================

class TestSvgEnvelopeOverlap:
    """
    Reproduces rack_diagram.render_svg's pipe-circle radius capping and
    confirms adjacent envelopes (and end pipes vs. columns) never overlap,
    for the scenarios called out in the schematic-fix request.
    """

    def _capped_radii(self, pipes, result, spare_space_location='right'):
        from rack_diagram import MIN_PIPE_R_PX, ENVELOPE_CLEARANCE_PX
        geo = build_geometry_model(pipes, result, spare_space_location=spare_space_location)

        rack_width = geo.rack_width
        steel_column = geo.column_width
        margin_left = margin_right = 112
        scale_max_width = 1100
        drawable = scale_max_width - margin_left - margin_right
        rack_left_edge = -steel_column / 2
        rack_right_edge = rack_width + steel_column / 2
        total_span = rack_right_edge - rack_left_edge
        scale = drawable / total_span

        def mx(mm):
            return margin_left + (mm - rack_left_edge) * scale

        rack_left_x = mx(rack_left_edge)
        rack_right_x = mx(rack_right_edge)
        col_w_px = max(steel_column * scale, 8)
        col_inner_left_x = rack_left_x + col_w_px
        col_inner_right_x = rack_right_x - col_w_px

        cx_list = [mx(p.cl_x) for p in geo.pipes]
        n = len(geo.pipes)
        radii = []
        for i, p in enumerate(geo.pipes):
            pipe_r_px = max(p.pipe_od * scale / 2, MIN_PIPE_R_PX)
            ins_r_px = max(p.ins_od * scale / 2, pipe_r_px)
            flange_r_px = max(p.flange_od * scale / 2, pipe_r_px + 3)

            cx = cx_list[i]
            if i > 0:
                left_avail = (cx - cx_list[i - 1]) / 2 - ENVELOPE_CLEARANCE_PX / 2
            else:
                left_avail = (cx - col_inner_left_x) - ENVELOPE_CLEARANCE_PX
            if i < n - 1:
                right_avail = (cx_list[i + 1] - cx) / 2 - ENVELOPE_CLEARANCE_PX / 2
            else:
                right_avail = (col_inner_right_x - cx) - ENVELOPE_CLEARANCE_PX

            max_r = max(min(left_avail, right_avail), MIN_PIPE_R_PX)
            pipe_r_px = min(pipe_r_px, max_r)
            ins_r_px = min(max(ins_r_px, pipe_r_px), max_r)
            flange_r_px = min(max(flange_r_px, pipe_r_px), max_r)
            radii.append((cx, max(ins_r_px, flange_r_px)))
        return radii, rack_left_x, rack_right_x, col_w_px

    @pytest.mark.parametrize("n", [3, 4, 8])
    def test_no_envelope_overlap_center(self, n):
        pipes = [_pipe(50 + (i % 5) * 50, rating=150) for i in range(n)]
        result = calculate_rack(pipes, expansion_pct=20)
        radii, *_ = self._capped_radii(pipes, result, spare_space_location='center')
        for (cx_a, r_a), (cx_b, r_b) in zip(radii, radii[1:]):
            assert r_a + r_b <= (cx_b - cx_a) + 1e-6

    def test_no_envelope_overlap_right_spare(self):
        pipes = [_pipe(100), _pipe(200, rating=300), _pipe(50)]
        result = calculate_rack(pipes, expansion_pct=20)
        radii, *_ = self._capped_radii(pipes, result, spare_space_location='right')
        for (cx_a, r_a), (cx_b, r_b) in zip(radii, radii[1:]):
            assert r_a + r_b <= (cx_b - cx_a) + 1e-6

    def test_no_pipe_column_overlap(self):
        pipes = [_pipe(15), _pipe(900, rating='600A')]
        result = calculate_rack(pipes, expansion_pct=20)
        radii, rack_left_x, rack_right_x, col_w_px = self._capped_radii(pipes, result)
        col_inner_left_x = rack_left_x + col_w_px
        col_inner_right_x = rack_right_x - col_w_px
        first_cx, first_r = radii[0]
        last_cx, last_r = radii[-1]
        assert first_cx - first_r >= col_inner_left_x - 1e-6
        assert last_cx + last_r <= col_inner_right_x + 1e-6


# =============================================================================
# SVG smoke tests for the schematic-fix request matrix
# =============================================================================

class TestSchematicFixMatrix:

    @pytest.mark.parametrize("n", [3, 4, 8])
    def test_center_spare_pipe_counts(self, n):
        pipes = [_pipe(50 + (i % 5) * 50, rating=150) for i in range(n)]
        result = calculate_rack(pipes, expansion_pct=20)
        svg = generate_diagram(pipes, result, spare_space_location='center')
        assert svg.startswith('<svg') and svg.endswith('</svg>')
        assert "Future spare space" in svg

    def test_spare_at_right(self):
        pipes = [_pipe(100), _pipe(200, rating=300), _pipe(50)]
        result = calculate_rack(pipes, expansion_pct=20)
        svg = generate_diagram(pipes, result, spare_space_location='right')
        assert "Future spare space" in svg

    def test_dn50_dn900_mixed(self):
        pipes = [_pipe(50), _pipe(900, rating='600A')]
        result = calculate_rack(pipes, expansion_pct=20)
        for loc in ('right', 'center'):
            svg = generate_diagram(pipes, result, spare_space_location=loc)
            assert svg.startswith('<svg')

    def test_insulated_pipes_center(self):
        pipes = [_pipe(100, insulation=50), _pipe(200, rating=300, insulation=75), _pipe(50, insulation=25)]
        result = calculate_rack(pipes, expansion_pct=20)
        svg = generate_diagram(pipes, result, spare_space_location='center')
        assert svg.startswith('<svg')

    def test_high_flange_rating_center(self):
        pipes = [_pipe(300, rating=2500), _pipe(300, rating=2500)]
        result = calculate_rack(pipes, expansion_pct=20)
        svg = generate_diagram(pipes, result, spare_space_location='center')
        assert svg.startswith('<svg')

    def test_custom_column_width_center(self):
        pipes = [_pipe(100), _pipe(200), _pipe(150)]
        result = calculate_rack(pipes, expansion_pct=20, steel_column_mm=400)
        svg = generate_diagram(pipes, result, spare_space_location='center')
        assert svg.startswith('<svg')

    def test_eurocode_profiles_center(self):
        from structural_profiles import get_profile_width
        pipes = [_pipe(100), _pipe(200), _pipe(150)]
        for family, size in (("HEA", "300"), ("HEB", "300"), ("HEM", "300"), ("IPE", "300")):
            col = get_profile_width(family, size)
            result = calculate_rack(pipes, expansion_pct=20, steel_column_mm=col)
            svg = generate_diagram(pipes, result, spare_space_location='center')
            assert svg.startswith('<svg')


# =============================================================================
# Phase 2.3 schematic refinement: centering, occupied-width annotation,
# two-scale symbol sizing, label format, dimension arrow markers
# =============================================================================

class TestCenterSpareBetweenEnvelopes:
    """
    "Center" spare space means: reserve the future bay between two adjacent
    pipe groups, near the middle of the pipe list, with balanced clearance
    to each flanking pipe's outer envelope (flange/insulation OD) - not
    forced onto the rack's geometric centerline.
    """

    @pytest.mark.parametrize("n,expected_gap", [(4, 1), (5, 2), (6, 2)])
    def test_gap_index_near_middle_of_pipe_list(self, n, expected_gap):
        pipes = [_pipe(50 + (i % 5) * 50, rating=150) for i in range(n)]
        result = calculate_rack(pipes, expansion_pct=20)
        geo = build_geometry_model(pipes, result, spare_space_location='center')
        assert geo.spare_zones[0].gap_index == expected_gap

    def test_two_pipes_inserts_into_only_gap(self):
        pipes = [_pipe(100), _pipe(200, rating=300)]
        result = calculate_rack(pipes, expansion_pct=20)
        geo = build_geometry_model(pipes, result, spare_space_location='center')
        assert geo.spare_zones[0].gap_index == 0

    def test_mixed_dn500_dn350_balanced_clearance(self):
        from rack_geometry import _envelope_radius
        pipes = [_pipe(100), _pipe(500, rating=300), _pipe(350, rating=300), _pipe(100)]
        result = calculate_rack(pipes, expansion_pct=20)
        geo = build_geometry_model(pipes, result, spare_space_location='center')

        zone = geo.spare_zones[0]
        gap = zone.gap_index
        r_left = _envelope_radius(pipes[gap])
        r_right = _envelope_radius(pipes[gap + 1])
        left_clearance = zone.x1 - (geo.pipes[gap].cl_x + r_left)
        right_clearance = (geo.pipes[gap + 1].cl_x - r_right) - zone.x2
        if not geo.warnings:
            assert left_clearance == pytest.approx(right_clearance, abs=1e-6)
            assert left_clearance >= -1e-6

    def test_large_flange_near_spare(self):
        from rack_geometry import _envelope_radius
        pipes = [_pipe(100), _pipe(300, rating=2500), _pipe(300, rating=2500), _pipe(100)]
        result = calculate_rack(pipes, expansion_pct=20)
        geo = build_geometry_model(pipes, result, spare_space_location='center')

        zone = geo.spare_zones[0]
        for p in geo.pipes:
            assert not (zone.x1 < p.cl_x < zone.x2)
        gap = zone.gap_index
        r_left = _envelope_radius(pipes[gap])
        r_right = _envelope_radius(pipes[gap + 1])
        # Spare zone must not overlap either flanking envelope, unless doing
        # so is mathematically unavoidable (flagged via geo.warnings).
        if not geo.warnings:
            assert zone.x1 >= geo.pipes[gap].cl_x + r_left - 1e-6
            assert zone.x2 <= geo.pipes[gap + 1].cl_x - r_right + 1e-6

    def test_insulated_pipe_near_spare(self):
        from rack_geometry import _envelope_radius
        pipes = [_pipe(100), _pipe(200, insulation=75), _pipe(200, insulation=75), _pipe(100)]
        result = calculate_rack(pipes, expansion_pct=20)
        geo = build_geometry_model(pipes, result, spare_space_location='center')

        zone = geo.spare_zones[0]
        gap = zone.gap_index
        r_left = _envelope_radius(pipes[gap])
        r_right = _envelope_radius(pipes[gap + 1])
        assert zone.x1 >= geo.pipes[gap].cl_x + r_left - 1e-6
        assert zone.x2 <= geo.pipes[gap + 1].cl_x - r_right + 1e-6

    def test_spare_never_overlaps_pipe_centerlines(self):
        pipes = [_pipe(15), _pipe(1000, rating='600A')]
        result = calculate_rack(pipes, expansion_pct=20)
        geo = build_geometry_model(pipes, result, spare_space_location='center')

        zone = geo.spare_zones[0]
        for p in geo.pipes:
            assert not (zone.x1 < p.cl_x < zone.x2)


class TestOccupiedWidthAnnotation:

    def test_no_sum_formula_in_center_mode(self):
        pipes = [_pipe(100), _pipe(200, rating=300), _pipe(50)]
        result = calculate_rack(pipes, expansion_pct=20)
        geo = build_geometry_model(pipes, result, spare_space_location='center')

        labels = [d.label for d in geo.bottom_dimensions]
        assert not any("+" in lbl and "=" in lbl and "occupied" in lbl for lbl in labels)
        assert any(lbl.startswith("Occupied Width = ") for lbl in labels)

    def test_occupied_width_label_right_mode(self):
        pipes = [_pipe(100), _pipe(200)]
        result = calculate_rack(pipes, expansion_pct=20)
        geo = build_geometry_model(pipes, result, spare_space_location='right')
        assert geo.bottom_dimensions[0].label == "Occupied Width = " + str(result['occupied_width']) + " mm"


class TestUniformLabelFormat:

    def test_label_ins_format(self):
        pipes = [_pipe(250, insulation=20)]
        result = calculate_rack(pipes, expansion_pct=20)
        geo = build_geometry_model(pipes, result)
        assert geo.pipes[0].label_ins == "Ins 20 mm"

    def test_label_ins_empty_when_bare(self):
        pipes = [_pipe(250)]
        result = calculate_rack(pipes, expansion_pct=20)
        geo = build_geometry_model(pipes, result)
        assert geo.pipes[0].label_ins == ""


class TestDimensionArrowMarkers:

    def test_start_and_end_markers_defined_and_used(self):
        pipes = [_pipe(100), _pipe(200, rating=300), _pipe(50)]
        result = calculate_rack(pipes, expansion_pct=20)
        svg = generate_diagram(pipes, result, spare_space_location='center')

        for marker_id in (
            "dimArrowEnd", "dimArrowStart",
            "dimArrowRedEnd", "dimArrowRedStart",
            "dimArrowAmberEnd", "dimArrowAmberStart",
        ):
            assert ('id="' + marker_id + '"') in svg
            assert ('url(#' + marker_id + ')') in svg


class TestTwoScaleSymbolSizing:

    def _envelope_radii_px(self, pipes, result, loc='right'):
        from rack_diagram import ENVELOPE_CLEARANCE_PX, MIN_PIPE_R_PX
        geo = build_geometry_model(pipes, result, spare_space_location=loc)
        rack_width = geo.rack_width
        steel_column = geo.column_width
        margin = 112
        scale_max_width = 1100
        drawable = scale_max_width - 2 * margin
        rack_left_edge = -steel_column / 2
        rack_right_edge = rack_width + steel_column / 2
        scale = drawable / (rack_right_edge - rack_left_edge)

        def mx(mm):
            return margin + (mm - rack_left_edge) * scale

        col_w_px = max(steel_column * scale, 8)
        col_inner_left_x = mx(rack_left_edge) + col_w_px
        col_inner_right_x = mx(rack_right_edge) - col_w_px
        cx_list = [mx(p.cl_x) for p in geo.pipes]
        n = len(geo.pipes)

        available_px = []
        for i in range(n):
            cx = cx_list[i]
            if i > 0:
                left_avail = (cx - cx_list[i - 1]) / 2 - ENVELOPE_CLEARANCE_PX / 2
            else:
                left_avail = (cx - col_inner_left_x) - ENVELOPE_CLEARANCE_PX
            if i < n - 1:
                right_avail = (cx_list[i + 1] - cx) / 2 - ENVELOPE_CLEARANCE_PX / 2
            else:
                right_avail = (col_inner_right_x - cx) - ENVELOPE_CLEARANCE_PX
            available_px.append(max(min(left_avail, right_avail), 1))

        sym_scale_factor = 1.0
        for i, p in enumerate(geo.pipes):
            envelope_od = max(p.pipe_od, p.ins_od, p.flange_od)
            ideal_r_px = envelope_od * scale / 2
            if ideal_r_px > 0:
                sym_scale_factor = min(sym_scale_factor, available_px[i] / ideal_r_px)

        radii = []
        for p in geo.pipes:
            pipe_r_px = p.pipe_od * scale / 2 * sym_scale_factor
            radii.append(max(pipe_r_px, MIN_PIPE_R_PX))
        return radii

    def test_dn900_larger_than_dn200(self):
        pipes = [_pipe(200, rating=150), _pipe(900, rating='600A')]
        result = calculate_rack(pipes, expansion_pct=20)
        radii = self._envelope_radii_px(pipes, result)
        assert radii[1] > radii[0]

    def test_dn50_dn50_equal_radii(self):
        pipes = [_pipe(50), _pipe(50)]
        result = calculate_rack(pipes, expansion_pct=20)
        radii = self._envelope_radii_px(pipes, result)
        assert radii[0] == pytest.approx(radii[1])

    def test_dn200_dn300_dn400_increasing(self):
        pipes = [_pipe(200), _pipe(300, rating=300), _pipe(400, rating=300)]
        result = calculate_rack(pipes, expansion_pct=20)
        radii = self._envelope_radii_px(pipes, result)
        assert radii[0] <= radii[1] <= radii[2]
        assert radii[0] < radii[2]

    def test_high_flange_class_renders(self):
        pipes_low = [_pipe(300, rating=150), _pipe(300, rating=150)]
        pipes_high = [_pipe(300, rating=2500), _pipe(300, rating=2500)]
        result_low = calculate_rack(pipes_low, expansion_pct=20)
        result_high = calculate_rack(pipes_high, expansion_pct=20)
        radii_low = self._envelope_radii_px(pipes_low, result_low)
        radii_high = self._envelope_radii_px(pipes_high, result_high)
        assert all(r > 0 for r in radii_low + radii_high)


# =============================================================================
# Validation matrix (requirement H)
# =============================================================================

class TestValidationMatrixH:

    def test_dn50_plus_dn50(self):
        pipes = [_pipe(50), _pipe(50)]
        result = calculate_rack(pipes, expansion_pct=20)
        for loc in ('right', 'center'):
            svg = generate_diagram(pipes, result, spare_space_location=loc)
            assert svg.startswith('<svg') and svg.endswith('</svg>')

    def test_dn200_dn300_dn400(self):
        pipes = [_pipe(200), _pipe(300, rating=300), _pipe(400, rating=300)]
        result = calculate_rack(pipes, expansion_pct=20)
        for loc in ('right', 'center'):
            svg = generate_diagram(pipes, result, spare_space_location=loc)
            assert svg.startswith('<svg') and svg.endswith('</svg>')

    def test_dn900_plus_dn150(self):
        pipes = [_pipe(900, rating='600A'), _pipe(150)]
        result = calculate_rack(pipes, expansion_pct=20)
        for loc in ('right', 'center'):
            svg = generate_diagram(pipes, result, spare_space_location=loc)
            assert svg.startswith('<svg') and svg.endswith('</svg>')

    def test_mixed_insulation(self):
        pipes = [_pipe(100, insulation=10), _pipe(300, rating=300, insulation=50), _pipe(150, insulation=0)]
        result = calculate_rack(pipes, expansion_pct=20)
        for loc in ('right', 'center'):
            svg = generate_diagram(pipes, result, spare_space_location=loc)
            assert svg.startswith('<svg') and svg.endswith('</svg>')

    def test_center_spare_mode(self):
        pipes = [_pipe(150), _pipe(250, rating=300), _pipe(100)]
        result = calculate_rack(pipes, expansion_pct=20)
        geo = build_geometry_model(pipes, result, spare_space_location='center')
        assert geo.spare_zones
        zone = geo.spare_zones[0]
        for p in geo.pipes:
            assert not (zone.x1 < p.cl_x < zone.x2)

    def test_end_spare_mode(self):
        pipes = [_pipe(150), _pipe(250, rating=300), _pipe(100)]
        result = calculate_rack(pipes, expansion_pct=20)
        geo = build_geometry_model(pipes, result, spare_space_location='right')
        zone = geo.spare_zones[0]
        last_pipe = geo.pipes[-1]
        assert zone.x1 >= last_pipe.cl_x
        assert zone.x2 <= geo.column_cl_right + 1e-6

    def test_max_pipe_count(self):
        pipes = [_pipe(50 + (i % 5) * 50, rating=150) for i in range(16)]
        result = calculate_rack(pipes, expansion_pct=20)
        for loc in ('right', 'center'):
            svg = generate_diagram(pipes, result, spare_space_location=loc)
            assert svg.startswith('<svg') and svg.endswith('</svg>')
