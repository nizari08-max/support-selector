"""Tests for the rack DXF export renderer (Pipe Rack Spacing Arrangement)."""

from io import StringIO

import ezdxf

from app import app
from rack_calculator import calculate_rack
from rack_dxf import LAYER_SPECS, generate_dxf


def _pipe(dn, rating=150, insulation=0, has_flange=True, support_condition="direct_rest"):
    return {
        "dn": dn,
        "rating": rating,
        "insulation": insulation,
        "has_flange": has_flange,
        "support_condition": support_condition,
    }


def _doc_from_bytes(dxf_bytes):
    return ezdxf.read(StringIO(dxf_bytes.decode("utf-8")))


def _lwpolyline_size(entity):
    points = list(entity.get_points("xy"))
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    return max(xs) - min(xs), max(ys) - min(ys)


def _texts(doc):
    return [entity.dxf.text for entity in doc.modelspace().query("TEXT")]


def _notes_blob(doc):
    """All note text joined and whitespace-normalised, so assertions are
    robust to word-wrapping a long note across multiple TEXT entities."""
    import re
    return re.sub(r"\s+", " ", " ".join(_texts(doc)))


class TestRackDxfExport:

    def test_dxf_file_is_generated(self):
        pipes = [_pipe(100), _pipe(200, rating=300)]
        result = calculate_rack(pipes)

        dxf_bytes = generate_dxf(pipes, result)

        assert dxf_bytes.startswith(b"  0")
        assert b"SECTION" in dxf_bytes
        assert b"EOF" in dxf_bytes

    def test_units_are_mm(self):
        pipes = [_pipe(100)]
        result = calculate_rack(pipes)

        doc = _doc_from_bytes(generate_dxf(pipes, result))

        assert doc.header["$INSUNITS"] == 4

    def test_ltscale_is_set_so_linetypes_render(self):
        pipes = [_pipe(100), _pipe(200, rating=300)]
        result = calculate_rack(pipes)

        doc = _doc_from_bytes(generate_dxf(pipes, result))

        assert doc.header["$LTSCALE"] > 1

    def test_required_layers_exist(self):
        pipes = [_pipe(100)]
        result = calculate_rack(pipes)

        doc = _doc_from_bytes(generate_dxf(pipes, result))

        for layer_name in LAYER_SPECS:
            assert layer_name in doc.layers

    def test_flange_layer_is_removed(self):
        # Option A: a spacing arrangement does not draw flange envelopes.
        assert "FLANGE_OD" not in LAYER_SPECS
        assert "CALLOUTS" not in LAYER_SPECS

        pipes = [_pipe(100, rating=300)]
        result = calculate_rack(pipes)
        doc = _doc_from_bytes(generate_dxf(pipes, result))

        assert "FLANGE_OD" not in doc.layers

    def test_pipe_and_insulation_circles_only(self):
        pipes = [
            _pipe(100, rating=150, insulation=0),
            _pipe(200, rating=300, insulation=50),
        ]
        result = calculate_rack(pipes)

        doc = _doc_from_bytes(generate_dxf(pipes, result))
        circles = list(doc.modelspace().query("CIRCLE"))
        layers = {c.dxf.layer for c in circles}

        pipe_od_circles = [c for c in circles if c.dxf.layer == "PIPE_OD"]
        insulation_circles = [c for c in circles if c.dxf.layer == "INSULATION_OD"]

        assert len(pipe_od_circles) == 2
        assert len(insulation_circles) == 1
        # No flange (or any other) circles in the section graphic.
        assert layers <= {"PIPE_OD", "INSULATION_OD"}

    def test_flange_envelope_note_present(self):
        pipes = [_pipe(100, rating=300)]
        result = calculate_rack(pipes)

        doc = _doc_from_bytes(generate_dxf(pipes, result))

        # The notes must explain that flange envelopes are conditional and
        # that flange circles are not drawn in this arrangement. Notes may be
        # word-wrapped across multiple TEXT entities, so match the joined blob.
        blob = _notes_blob(doc)
        assert "FLANGE ENVELOPES ARE INCLUDED" in blob
        assert "HAVING A FLANGE AT THE RACK SECTION" in blob

    def test_support_representation_note_present(self):
        pipes = [_pipe(100), _pipe(200, rating=300)]
        result = calculate_rack(pipes)

        doc = _doc_from_bytes(generate_dxf(pipes, result))
        blob = _notes_blob(doc)

        assert "DIRECT REST = PIPE SHOWN ON" in blob
        assert "PIPE SHOE = NOMINAL SCHEMATIC SHOE" in blob

    def test_centerlines_use_pipe_cl_layer(self):
        pipes = [_pipe(100), _pipe(200, rating=300)]
        result = calculate_rack(pipes)

        doc = _doc_from_bytes(generate_dxf(pipes, result))
        center_entities = [e for e in doc.modelspace() if e.dxf.layer == "PIPE_CL"]

        assert center_entities
        assert doc.layers.get("PIPE_CL").dxf.linetype == "CENTER"

    def test_real_dimension_entities_are_used(self):
        pipes = [_pipe(100), _pipe(200, rating=300)]
        result = calculate_rack(pipes)

        doc = _doc_from_bytes(generate_dxf(pipes, result))
        dimensions = list(doc.modelspace().query("DIMENSION"))

        assert dimensions
        assert "RACK" in doc.dimstyles

    def test_single_rack_width_readout(self):
        pipes = [_pipe(100), _pipe(200, rating=300)]
        result = calculate_rack(pipes)

        doc = _doc_from_bytes(generate_dxf(pipes, result))
        dim_texts = [d.dxf.text for d in doc.modelspace().query("DIMENSION")]
        rack_width_hits = [t for t in dim_texts if "rack width" in t]
        text_hits = [t for t in _texts(doc) if "rack width" in t]

        assert len(rack_width_hits) == 1
        assert text_hits == []

    def test_direct_rest_draws_no_support_geometry(self):
        # Direct Rest = pipe shown on the beam, no fabricated support symbol.
        pipes = [_pipe(100), _pipe(200, rating=300), _pipe(400, rating=300)]
        result = calculate_rack(pipes)

        doc = _doc_from_bytes(generate_dxf(pipes, result))
        support_entities = list(doc.modelspace().query('LWPOLYLINE[layer=="SUPPORT"]'))

        assert support_entities == []

    def test_no_triangular_support_symbols(self):
        # The old triangular rest symbol (a 3-corner polyline) must be gone,
        # for both direct-rest and pipe-shoe pipes.
        pipes = [
            _pipe(100, support_condition="direct_rest"),
            _pipe(200, rating=300, support_condition="pipe_shoe"),
            _pipe(400, rating=300, support_condition="pipe_shoe"),
        ]
        result = calculate_rack(pipes)

        doc = _doc_from_bytes(generate_dxf(pipes, result))
        for poly in doc.modelspace().query('LWPOLYLINE[layer=="SUPPORT"]'):
            distinct_corners = {tuple(round(c, 3) for c in p) for p in poly.get_points("xy")}
            # Rectangles have 4 distinct corners; triangles would have 3.
            assert len(distinct_corners) == 4

    def test_pipe_shoe_drawn_as_rectangles(self):
        # Pipe Shoe = inverted-T (base plate + web) => rectangle polylines.
        pipes = [
            _pipe(100, support_condition="pipe_shoe"),
            _pipe(200, rating=300, support_condition="pipe_shoe"),
        ]
        result = calculate_rack(pipes)

        doc = _doc_from_bytes(generate_dxf(pipes, result))
        shoes = list(doc.modelspace().query('LWPOLYLINE[layer=="SUPPORT"]'))

        # Two pipes => two shoes, each made of a base plate + a web (2 rects).
        assert len(shoes) == 4
        for shoe in shoes:
            w, h = _lwpolyline_size(shoe)
            assert w <= 250
            assert h <= 350

    def test_mixed_support_conditions(self):
        pipes = [
            _pipe(100, support_condition="direct_rest"),
            _pipe(200, rating=300, support_condition="pipe_shoe"),
        ]
        result = calculate_rack(pipes)

        doc = _doc_from_bytes(generate_dxf(pipes, result))
        shoes = list(doc.modelspace().query('LWPOLYLINE[layer=="SUPPORT"]'))

        # Only the pipe-shoe pipe contributes support geometry (2 rects).
        assert len(shoes) == 2

    def test_spare_zone_appears_when_requested(self):
        pipes = [_pipe(100), _pipe(200, rating=300)]
        result = calculate_rack(pipes, expansion_pct=20)

        doc = _doc_from_bytes(generate_dxf(pipes, result, spare_space_location="center"))
        spare_entities = [
            e for e in doc.modelspace()
            if e.dxf.layer in ("SPARE_ZONE", "HATCH")
        ]

        assert spare_entities
        assert any(e.dxftype() == "LWPOLYLINE" for e in spare_entities)

    def test_export_does_not_change_calculation_result(self):
        pipes = [_pipe(100), _pipe(200, rating=300, insulation=50)]
        result = calculate_rack(pipes, expansion_pct=20)
        before = dict(result)

        generate_dxf(pipes, result, spare_space_location="center")

        assert result == before

    def test_title_schedule_legend_and_tags_present(self):
        pipes = [_pipe(100), _pipe(200, rating=300, insulation=50)]
        result = calculate_rack(pipes)

        doc = _doc_from_bytes(generate_dxf(
            pipes,
            result,
            metadata={"profile_label": "HEA 300", "column_label": "HEA 300"},
        ))
        texts = _texts(doc)

        assert "PIPE RACK" in texts
        assert any("SPACING ARRANGEMENT" in t for t in texts)
        assert "PIPE SCHEDULE" in texts
        assert "LEGEND" in texts
        assert "HEA 300" in texts
        assert "P1" in texts
        assert "DN100" in texts
        assert "P2" in texts
        assert "DN200" in texts
        # The retired section title must be gone.
        assert "PIPE RACK SECTION" not in texts
        assert "DRAWING INFORMATION" not in texts

    def test_composition_zone_layers_present(self):
        pipes = [_pipe(100), _pipe(200, rating=300, insulation=50)]
        result = calculate_rack(pipes)

        doc = _doc_from_bytes(generate_dxf(pipes, result))
        layers = {entity.dxf.layer for entity in doc.modelspace()}

        for expected in ("TITLE_BLOCK", "SCHEDULE", "NOTES", "LEGEND",
                         "DIMENSIONS", "PIPE_OD", "RACK_BEAM", "RACK_COLUMN"):
            assert expected in layers
        assert "CALLOUTS" not in layers
        assert "FLANGE_OD" not in layers

    def test_title_block_is_bottom_right(self):
        pipes = [_pipe(100), _pipe(200, rating=300)]
        result = calculate_rack(pipes)

        doc = _doc_from_bytes(generate_dxf(pipes, result))
        title_texts = [
            e for e in doc.modelspace().query("TEXT")
            if e.dxf.layer == "TITLE_BLOCK"
        ]
        schedule_texts = [
            e for e in doc.modelspace().query("TEXT")
            if e.dxf.layer == "SCHEDULE"
        ]

        assert title_texts
        # Bottom: title block sits below the schematic pipe centerline (y = 0).
        assert max(e.dxf.insert.y for e in title_texts) < 0
        # Right: title block is to the right of the schedule.
        assert min(e.dxf.insert.x for e in title_texts) > max(e.dxf.insert.x for e in schedule_texts)

    def test_pipe_schedule_is_below_bottom_dimensions(self):
        pipes = [_pipe(100), _pipe(200, rating=300)]
        result = calculate_rack(pipes)

        doc = _doc_from_bytes(generate_dxf(pipes, result))
        dimension_y = [d.dxf.defpoint.y for d in doc.modelspace().query("DIMENSION")]
        schedule_text_y = [
            entity.dxf.insert.y for entity in doc.modelspace().query('TEXT[layer=="SCHEDULE"]')
        ]

        assert dimension_y
        assert schedule_text_y
        assert max(schedule_text_y) < min(dimension_y)


class TestRackDxfRoute:

    def test_download_route_returns_dxf(self):
        client = app.test_client()

        response = client.post(
            "/rack-calculator/dxf",
            data={
                "dn": ["100", "200"],
                "rating": ["150", "300"],
                "insulation": ["0", "50"],
                "expansion_pct": "20",
                "profile_family": "custom",
                "profile_size": "300",
                "steel_column_mm": "330",
                "spare_space_location": "right",
            },
        )

        assert response.status_code == 200
        assert response.mimetype == "application/dxf"
        assert response.data.startswith(b"  0")
        assert "attachment;" in response.headers["Content-Disposition"]
