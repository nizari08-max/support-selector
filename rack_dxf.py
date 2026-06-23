"""DXF renderer for the rack calculator — Pipe Rack Spacing Arrangement.

Pipeline: calculate_rack() -> build_geometry_model() -> render_dxf()

This drawing is officially a **Pipe Rack Spacing Arrangement** (schematic),
NOT a true structural rack section:

  * Horizontal geometry is true-scale millimetre engineering geometry
    (pipe centerlines, spacings, rack width, spare) straight from the
    approved geometry model.
  * Vertical representation is schematic (single tier, aligned pipe
    centerlines). No vertical elevation is implied or scaled.

It deliberately uses the true-scale millimetre geometry from
``rack_geometry.py``. It does not derive anything from the SVG renderer and
does not apply SVG readability scaling to CAD entities. It performs no
engineering calculations of its own.
"""

from io import StringIO

import ezdxf
from ezdxf.enums import TextEntityAlignment

from rack_geometry import build_geometry_model


# ── Layer table (Option A) ────────────────────────────────────────────────
# Pen hierarchy by lineweight: primary 0.50, secondary 0.18, tertiary 0.13.
LAYER_SPECS = {
    "PIPE_OD": {"color": 1, "lineweight": 50},
    "RACK_BEAM": {"color": 7, "lineweight": 50},
    "RACK_COLUMN": {"color": 7, "lineweight": 50},
    "INSULATION_OD": {"color": 3, "linetype": "DASHED", "lineweight": 13},
    "PIPE_CL": {"color": 4, "linetype": "CENTER", "lineweight": 13},
    "SUPPORT": {"color": 7, "lineweight": 13},
    "SPARE_ZONE": {"color": 6, "lineweight": 25},
    "HATCH": {"color": 8, "lineweight": 9},
    "DIMENSIONS": {"color": 2, "lineweight": 18},
    "TEXT": {"color": 7, "lineweight": 13},
    "NOTES": {"color": 7, "lineweight": 13},
    "SCHEDULE": {"color": 7, "lineweight": 13},
    "LEGEND": {"color": 7, "lineweight": 13},
    "TITLE_BLOCK": {"color": 7, "lineweight": 25},
    "SCALE_BAR": {"color": 7, "lineweight": 18},
}

# ── Text heights (mm) ──────────────────────────────────────────────────────
TITLE_TEXT_HEIGHT = 130
SUBTITLE_TEXT_HEIGHT = 62
TAG_TEXT_HEIGHT = 85
NOTE_TEXT_HEIGHT = 55
DIM_TEXT_HEIGHT = 62
SCHEDULE_TEXT_HEIGHT = 55

# ── Schematic vertical layout constants (mm) ───────────────────────────────
PIPE_Y = 0.0              # beam-top datum: direct-rest pipe bottoms rest on this line
# Standard schematic shoe height (mm), identical for every pipe regardless of
# DN. A pipe on a shoe has its bottom raised by this fixed amount above the
# beam top, so the elevation difference between shoe and direct-rest pipes is
# unambiguous and the shoe height never varies. Schematic only -- not a
# fabrication dimension (nominal 100 mm; acceptable up to 130 mm).
SHOE_NOMINAL_HEIGHT = 100
BEAM_HEIGHT = 320         # strong tier beam
COL_RISE = 320            # column top above the tallest pipe envelope
COL_DROP = 240            # column bottom below the beam
TOP_DIM_GAP = 280         # first top dimension row above column top
BOTTOM_DIM_GAP = 320      # first bottom dimension row below column bottom
DIM_ROW_STEP = 230        # vertical step between stacked dimension rows
TAG_GAP = 150             # pipe tag above the tallest pipe envelope

NOTE_STEP = 90
SCHEDULE_ROW_H = 150
LEGEND_GAP = 320
LEGEND_HEADER_H = 200      # title row of the legend box
LEGEND_ROW_H = 165         # per-entry row height
LEGEND_PAD = 120           # bottom padding inside the legend box
LEGEND_SAMPLE_W = 360      # length of each colour sample line
LOWER_ZONE_GAP = 640
TITLE_BLOCK_W = 2500
TITLE_BLOCK_H = 1180

SHEET_SIDE_MARGIN = 1100
SHEET_TOP_MARGIN = 280
SHEET_BOTTOM_MARGIN = 280
MIN_SHEET_WIDTH = 5400

# Real DIMENSION style overrides applied to every linear dim.
DIM_OVERRIDE = {
    "dimtxt": DIM_TEXT_HEIGHT,
    "dimasz": 70,
    "dimexe": 35,
    "dimexo": 45,
    "dimgap": 20,
    "dimtad": 1,
    "dimdec": 0,
    "dimlunit": 2,
}

TEXT_ALIGN = {
    "LEFT": TextEntityAlignment.LEFT,
    "CENTER": TextEntityAlignment.CENTER,
    "RIGHT": TextEntityAlignment.RIGHT,
}


def generate_dxf(pipes, result, spare_space_location="right", metadata=None):
    """Build rack geometry and return a DXF document as UTF-8 bytes."""
    geometry = build_geometry_model(
        pipes,
        result,
        spare_space_location=spare_space_location,
    )
    return render_dxf(geometry, metadata=metadata)


def render_dxf(geometry, metadata=None):
    """Render a RackGeometry object to a Pipe Rack Spacing Arrangement DXF."""
    doc = ezdxf.new("R2010", setup=True)
    doc.header["$INSUNITS"] = 4  # millimetres
    doc.units = ezdxf.units.MM
    _setup_layers(doc)
    _setup_dimstyle(doc)

    msp = doc.modelspace()
    metadata = metadata or {}
    layout = _layout(geometry)
    doc.header["$LTSCALE"] = layout["ltscale"]

    _draw_rack(msp, geometry, layout)
    _draw_spare_band(msp, geometry, layout)
    _draw_pipes(msp, geometry, layout)
    _draw_dimensions(msp, geometry, layout)
    _draw_notes(msp, geometry, layout)
    _draw_scale_bar(msp, layout)
    _draw_pipe_schedule(msp, geometry, layout)
    _draw_legend(msp, layout)
    _draw_title_block(msp, geometry, layout, metadata)
    _draw_sheet_border(msp, layout)

    stream = StringIO()
    doc.write(stream)
    return stream.getvalue().encode("utf-8")


# ── Setup ──────────────────────────────────────────────────────────────────

def _setup_layers(doc):
    for name, spec in LAYER_SPECS.items():
        if name not in doc.layers:
            doc.layers.add(name=name, color=spec["color"])
        layer = doc.layers.get(name)
        layer.dxf.color = spec["color"]
        if "linetype" in spec:
            layer.dxf.linetype = spec["linetype"]
        if "lineweight" in spec:
            layer.dxf.lineweight = spec["lineweight"]


def _setup_dimstyle(doc):
    if "RACK" in doc.dimstyles:
        return
    ds = doc.dimstyles.add("RACK")
    ds.dxf.dimtxt = DIM_TEXT_HEIGHT
    ds.dxf.dimasz = 70
    ds.dxf.dimexe = 35
    ds.dxf.dimexo = 45
    ds.dxf.dimgap = 20
    ds.dxf.dimtad = 1
    ds.dxf.dimdec = 0
    ds.dxf.dimlunit = 2


# ── Layout (schematic vertical zone map; horizontal stays true-scale) ──────

def _notes_list(geometry):
    notes = [
        "NOTES:",
        "1. ALL DIMENSIONS IN MILLIMETRES.",
        "2. PIPE RACK SPACING ARRANGEMENT - SCHEMATIC. NOT FOR CONSTRUCTION.",
        "3. HORIZONTAL SPACING IS TRUE SCALE; VERTICAL REPRESENTATION IS "
        "SCHEMATIC (SINGLE TIER).",
        "4. PIPE SPACING AND RACK WIDTH PER APPROVED RACK WIDTH CALCULATION.",
        "5. FLANGE ENVELOPES ARE INCLUDED IN THE SPACING ONLY FOR PIPES MARKED "
        "AS HAVING A FLANGE AT THE RACK SECTION; FLANGE CIRCLES ARE NOT DRAWN.",
        "6. SUPPORT REPRESENTATION IS SCHEMATIC - DIRECT REST = PIPE SHOWN ON "
        "RACK BEAM; PIPE SHOE = NOMINAL SCHEMATIC SHOE (~100 MM). NOT A "
        "FABRICATION DETAIL.",
        "7. PIPE OD AND INSULATION ENVELOPES SHOWN; THIS IS A RACK ARRANGEMENT "
        "DRAWING, NOT A STRUCTURAL SUPPORT DETAIL.",
    ]
    for i, warning in enumerate(geometry.warnings, start=8):
        notes.append(f"{i}. {warning.upper()}")
    return notes


# Approximate width of one character at NOTE_TEXT_HEIGHT (mm). Used to wrap
# notes so they never run past the sheet border.
NOTE_CHAR_W = NOTE_TEXT_HEIGHT * 0.62


def _wrap_notes(notes, max_chars):
    """Word-wrap each note to ``max_chars``; continuation lines are indented
    under the note text (past the 'N. ' number) so the block stays readable."""
    max_chars = max(int(max_chars), 24)
    wrapped = []
    for note in notes:
        # Preserve any 'N. ' numeric prefix as a hanging indent.
        prefix = ""
        body = note
        dot = note.find(". ")
        if 0 < dot <= 3 and note[:dot].isdigit():
            prefix = note[: dot + 2]
            body = note[dot + 2:]
        indent = " " * len(prefix)
        line = prefix
        for word in body.split():
            if line in (prefix, indent):
                line += word
            elif len(line) + 1 + len(word) <= max_chars:
                line += " " + word
            else:
                wrapped.append(line)
                line = indent + word
        wrapped.append(line)
    return wrapped


def _legend_entries(geometry):
    entries = [
        ("PIPE OD", "PIPE_OD"),
        ("INSULATION OD", "INSULATION_OD"),
        ("PIPE CENTERLINE", "PIPE_CL"),
        ("FUTURE SPARE", "SPARE_ZONE"),
    ]
    if any(getattr(p, "support_condition", "direct_rest") == "pipe_shoe"
           for p in geometry.pipes):
        entries.append(("PIPE SHOE", "SUPPORT"))
    return entries


def _layout(geometry):
    pipes = geometry.pipes
    col_half = geometry.column_width / 2
    rack_left = geometry.column_cl_left - col_half
    rack_right = geometry.column_cl_right + col_half
    rack_mid = (rack_left + rack_right) / 2
    rack_span = rack_right - rack_left

    # Every direct-rest pipe bottom rests exactly on the beam-top datum
    # (PIPE_Y); shoe pipes are raised by the fixed nominal shoe height. The
    # envelope top accounts for that elevation so raised pipes/insulation are
    # never clipped.
    max_top = max((_pipe_cl_y(p) + max(p.pipe_od, p.ins_od) / 2 for p in pipes), default=150)

    beam_top = PIPE_Y
    beam_bottom = beam_top - BEAM_HEIGHT
    col_top = max_top + COL_RISE
    col_bottom = beam_bottom - COL_DROP

    top_rows = max((d.row for d in geometry.top_dimensions), default=0) + 1
    top_dim_y0 = col_top + TOP_DIM_GAP
    top_dim_high = top_dim_y0 + (top_rows - 1) * DIM_ROW_STEP

    bottom_dim_y0 = col_bottom - BOTTOM_DIM_GAP

    # ── Sheet width is known up-front (depends only on the rack span), so
    #    notes can be wrapped to fit inside the borders before sizing the
    #    note block. Leave room at the right for the graphic scale bar. ──
    sheet_width = max(rack_span + 2 * SHEET_SIDE_MARGIN, MIN_SHEET_WIDTH)
    sheet_left = rack_mid - sheet_width / 2
    sheet_right = rack_mid + sheet_width / 2
    notes_x = sheet_left + 160
    notes_avail = (sheet_right - 160 - 1200) - notes_x   # keep clear of scale bar
    max_note_chars = notes_avail / NOTE_CHAR_W

    notes = _wrap_notes(_notes_list(geometry), max_note_chars)
    notes_block_h = len(notes) * NOTE_STEP
    notes_top = top_dim_high + 220 + notes_block_h

    # Bottom dims we render: rack width (row 0) + optional spare (row 1).
    n_bottom_rows = 2 if geometry.spare_zones else 1
    bottom_dim_low = bottom_dim_y0 - (n_bottom_rows - 1) * DIM_ROW_STEP

    lower_top = bottom_dim_low - LOWER_ZONE_GAP
    sched_rows = len(pipes) + 2
    sched_top = lower_top
    sched_bottom = sched_top - SCHEDULE_ROW_H * sched_rows
    legend_entries = _legend_entries(geometry)
    legend_top = sched_bottom - LEGEND_GAP
    legend_height = LEGEND_HEADER_H + len(legend_entries) * LEGEND_ROW_H + LEGEND_PAD
    legend_bottom = legend_top - legend_height
    title_top = lower_top
    title_bottom = title_top - TITLE_BLOCK_H
    content_bottom = min(legend_bottom, title_bottom)

    sheet_top = notes_top + SHEET_TOP_MARGIN
    sheet_bottom = content_bottom - SHEET_BOTTOM_MARGIN

    ltscale = min(max(rack_span / 220.0, 20.0), 60.0)

    return {
        "rack_left": rack_left,
        "rack_right": rack_right,
        "rack_mid": rack_mid,
        "max_top": max_top,
        "beam_top": beam_top,
        "beam_bottom": beam_bottom,
        "col_top": col_top,
        "col_bottom": col_bottom,
        "top_dim_y0": top_dim_y0,
        "top_dim_high": top_dim_high,
        "bottom_dim_y0": bottom_dim_y0,
        "notes": notes,
        "notes_top": notes_top,
        "notes_x": notes_x,
        "sched_top": sched_top,
        "sched_bottom": sched_bottom,
        "legend_entries": legend_entries,
        "legend_top": legend_top,
        "legend_bottom": legend_bottom,
        "title_top": title_top,
        "title_bottom": title_bottom,
        "sheet_left": sheet_left,
        "sheet_right": sheet_right,
        "sheet_top": sheet_top,
        "sheet_bottom": sheet_bottom,
        "ltscale": ltscale,
    }


# ── Primitives ─────────────────────────────────────────────────────────────

def _rect(msp, x1, y1, x2, y2, layer):
    points = [(x1, y1), (x2, y1), (x2, y2), (x1, y2), (x1, y1)]
    return msp.add_lwpolyline(points, dxfattribs={"layer": layer})


def _add_text(msp, text, point, height=TAG_TEXT_HEIGHT, layer="TEXT", align="CENTER"):
    entity = msp.add_text(str(text), dxfattribs={"layer": layer, "height": height})
    entity.set_placement(point, align=TEXT_ALIGN.get(align, TextEntityAlignment.CENTER))
    return entity


def _linear_dim(msp, x1, x2, dim_y, origin_y, label):
    if x1 == x2:
        return
    dim = msp.add_linear_dim(
        base=((x1 + x2) / 2, dim_y),
        p1=(x1, origin_y),
        p2=(x2, origin_y),
        text=label,
        dimstyle="RACK",
        override=DIM_OVERRIDE,
        dxfattribs={"layer": "DIMENSIONS"},
    )
    dim.render()


# ── Rack section (the visual hero): beam + columns ─────────────────────────

def _draw_rack(msp, geometry, layout):
    col_half = geometry.column_width / 2
    left_cl = geometry.column_cl_left
    right_cl = geometry.column_cl_right
    beam_x1 = left_cl + col_half
    beam_x2 = right_cl - col_half

    _draw_tier_beam(msp, beam_x1, beam_x2, layout["beam_top"])
    for cl in (left_cl, right_cl):
        _draw_column(msp, cl, geometry.column_width, layout["col_top"], layout["col_bottom"])
        msp.add_line(
            (cl, layout["col_top"] + 120),
            (cl, layout["bottom_dim_y0"] - 180),
            dxfattribs={"layer": "PIPE_CL"},
        )

    _add_text(msp, "COLUMN CL", (left_cl, layout["col_top"] + 200), height=NOTE_TEXT_HEIGHT, layer="TEXT")
    _add_text(msp, "COLUMN CL", (right_cl, layout["col_top"] + 200), height=NOTE_TEXT_HEIGHT, layer="TEXT")


def _draw_tier_beam(msp, x1, x2, beam_top):
    beam_bottom = beam_top - BEAM_HEIGHT
    flange_t = 64
    _rect(msp, x1, beam_top, x2, beam_bottom, "RACK_BEAM")
    msp.add_line((x1, beam_top - flange_t), (x2, beam_top - flange_t), dxfattribs={"layer": "RACK_BEAM"})
    msp.add_line((x1, beam_bottom + flange_t), (x2, beam_bottom + flange_t), dxfattribs={"layer": "RACK_BEAM"})


def _draw_column(msp, cl, width, top_y, bottom_y):
    flange_t = max(width * 0.18, 36)
    web_t = max(width * 0.20, 40)
    x1 = cl - width / 2
    x2 = cl + width / 2
    web_x1 = cl - web_t / 2
    web_x2 = cl + web_t / 2

    _rect(msp, x1, top_y, x2, top_y - flange_t, "RACK_COLUMN")
    _rect(msp, web_x1, top_y - flange_t, web_x2, bottom_y + flange_t, "RACK_COLUMN")
    _rect(msp, x1, bottom_y + flange_t, x2, bottom_y, "RACK_COLUMN")


# ── Future spare: light reserved-width band ────────────────────────────────

def _draw_spare_band(msp, geometry, layout):
    top_y = layout["max_top"]
    bottom_y = layout["beam_bottom"]
    for zone in geometry.spare_zones:
        _rect(msp, zone.x1, top_y, zone.x2, bottom_y, "SPARE_ZONE")
        try:
            # Magenta hatch so the future spare zone reads instantly against
            # the red pipes and grey structure.
            hatch = msp.add_hatch(color=6, dxfattribs={"layer": "SPARE_ZONE"})
            hatch.paths.add_polyline_path(
                [(zone.x1, top_y), (zone.x2, top_y), (zone.x2, bottom_y), (zone.x1, bottom_y)],
                is_closed=True,
            )
            hatch.set_pattern_fill("ANSI31", scale=160, angle=45)
        except ezdxf.DXFError:
            pass

        cx = (zone.x1 + zone.x2) / 2
        if zone.width >= 280:
            mid = (top_y + bottom_y) / 2
            _add_text(msp, "FUTURE", (cx, mid + 45), height=NOTE_TEXT_HEIGHT, layer="SPARE_ZONE")
            _add_text(msp, "SPARE", (cx, mid - 45), height=NOTE_TEXT_HEIGHT, layer="SPARE_ZONE")
        else:
            msp.add_line((cx, bottom_y), (cx, bottom_y - 170), dxfattribs={"layer": "SPARE_ZONE"})
            _add_text(msp, "FUTURE SPARE", (cx, bottom_y - 230), height=NOTE_TEXT_HEIGHT, layer="SPARE_ZONE")


# ── Pipes: OD + insulation + centerline + tag + schematic rest tick ────────

def _draw_pipes(msp, geometry, layout):
    cl_top = layout["col_top"] - 60
    cl_bottom = layout["beam_top"]
    tag_y = layout["max_top"] + TAG_GAP

    for pipe in geometry.pipes:
        x = pipe.cl_x
        cy = _pipe_cl_y(pipe)
        env_r = max(pipe.pipe_od, pipe.ins_od) / 2

        # Centerlines (vertical + short horizontal through the pipe at its
        # schematic elevation).
        msp.add_line((x, cl_top), (x, cl_bottom), dxfattribs={"layer": "PIPE_CL"})
        msp.add_line(
            (x - env_r - 110, cy),
            (x + env_r + 110, cy),
            dxfattribs={"layer": "PIPE_CL"},
        )

        if pipe.insulation > 0 and pipe.ins_od > pipe.pipe_od:
            msp.add_circle((x, cy), pipe.ins_od / 2, dxfattribs={"layer": "INSULATION_OD"})

        msp.add_circle((x, cy), pipe.pipe_od / 2, dxfattribs={"layer": "PIPE_OD"})

        _draw_pipe_support(msp, pipe, layout["beam_top"])
        _add_text(msp, pipe.label_main, (x, tag_y), height=TAG_TEXT_HEIGHT, layer="TEXT")


def _pipe_cl_y(pipe):
    """Schematic centerline elevation (mm) for a pipe above the beam top.

    Direct-rest pipes have their OD bottom resting *directly on* the beam-top
    datum (``PIPE_Y``), so the centerline sits at ``PIPE_Y + r`` — no gap.
    Pipe-shoe pipes have their bottom raised by the fixed nominal shoe height,
    so the shoe height is identical for every pipe regardless of DN and the
    elevation difference between shoe and direct-rest pipes is unmistakable.
    Vertical only; the horizontal geometry stays true-scale.
    """
    r = pipe.pipe_od / 2
    if getattr(pipe, "support_condition", "direct_rest") == "pipe_shoe":
        return PIPE_Y + SHOE_NOMINAL_HEIGHT + r
    return PIPE_Y + r


def _draw_pipe_support(msp, pipe, beam_top):
    """Schematic support under a pipe, per its support condition.

    * ``direct_rest`` -- nothing fabricated is drawn; the pipe is shown
      resting directly on the rack beam (honest, schematic).
    * ``pipe_shoe``   -- a simple inverted-T shoe (base plate on the beam +
      a narrow vertical web up to the pipe bottom). Schematic only; not a
      fabrication detail.
    """
    if getattr(pipe, "support_condition", "direct_rest") != "pipe_shoe":
        return

    pipe_bottom = _pipe_cl_y(pipe) - pipe.pipe_od / 2
    if pipe_bottom <= beam_top + 10:
        return

    # Compact inverted-T, kept deliberately small so it reads cleanly when
    # printed without dominating the drawing. Height is fixed by the standard
    # shoe height (pipe_bottom - beam_top); only the footprint scales slightly.
    x = pipe.cl_x
    web_half = min(max(pipe.pipe_od * 0.045, 22), 42)
    base_half = min(web_half * 1.7, 75)
    base_thickness = min(max(pipe_bottom - beam_top, 0) * 0.18, 22)

    # Base plate sitting on the beam top.
    _rect(msp, x - base_half, beam_top + base_thickness, x + base_half, beam_top, "SUPPORT")
    # Vertical web rising from the base plate to the pipe bottom.
    _rect(msp, x - web_half, pipe_bottom, x + web_half, beam_top + base_thickness, "SUPPORT")


# ── Dimensions (real DIMENSION entities) ───────────────────────────────────

def _draw_dimensions(msp, geometry, layout):
    top_origin = layout["max_top"] + 40
    for d in geometry.top_dimensions:
        y = layout["top_dim_y0"] + d.row * DIM_ROW_STEP
        _linear_dim(msp, d.x1, d.x2, y, top_origin, d.label)

    bottom_origin = layout["beam_bottom"] - 40
    # Single rack-width readout (style "total") + light spare-band dimension.
    row = 0
    for d in geometry.bottom_dimensions:
        if d.style == "total":
            _linear_dim(msp, d.x1, d.x2, layout["bottom_dim_y0"], bottom_origin, d.label)
    for zone in geometry.spare_zones:
        row += 1
        y = layout["bottom_dim_y0"] - row * DIM_ROW_STEP
        _linear_dim(msp, zone.x1, zone.x2, y, bottom_origin, zone.label)


# ── Notes, scale bar ───────────────────────────────────────────────────────

def _draw_notes(msp, geometry, layout):
    x = layout["notes_x"]
    y = layout["notes_top"]
    for i, note in enumerate(layout["notes"]):
        _add_text(msp, note, (x, y - i * NOTE_STEP), height=NOTE_TEXT_HEIGHT, layer="NOTES", align="LEFT")


def _draw_scale_bar(msp, layout):
    # Simple graphic scale bar: one 1000 mm segment, true to horizontal scale.
    x1 = layout["sheet_right"] - 160 - 1000
    x2 = layout["sheet_right"] - 160
    y = layout["notes_top"]
    msp.add_line((x1, y), (x2, y), dxfattribs={"layer": "SCALE_BAR"})
    for x in (x1, (x1 + x2) / 2, x2):
        msp.add_line((x, y - 40), (x, y + 40), dxfattribs={"layer": "SCALE_BAR"})
    _add_text(msp, "0", (x1, y + 70), height=NOTE_TEXT_HEIGHT, layer="SCALE_BAR")
    _add_text(msp, "1000 mm", (x2, y + 70), height=NOTE_TEXT_HEIGHT, layer="SCALE_BAR", align="RIGHT")
    _add_text(msp, "SCALE BAR (HORIZONTAL)", ((x1 + x2) / 2, y - 130), height=NOTE_TEXT_HEIGHT, layer="SCALE_BAR")


# ── Pipe schedule (lower-left) ─────────────────────────────────────────────

def _draw_pipe_schedule(msp, geometry, layout):
    if not geometry.pipes:
        return
    col_w = [180, 300, 320, 260, 320]
    headers = ("TAG", "DN", "RATING", "OD", "INSUL")
    x1 = layout["sheet_left"] + 160
    x_cols = [x1]
    for w in col_w:
        x_cols.append(x_cols[-1] + w)
    x2 = x_cols[-1]
    y_top = layout["sched_top"]
    row_h = SCHEDULE_ROW_H
    y_bottom = y_top - row_h * (len(geometry.pipes) + 2)

    _rect(msp, x1, y_top, x2, y_bottom, "SCHEDULE")
    msp.add_line((x1, y_top - row_h), (x2, y_top - row_h), dxfattribs={"layer": "SCHEDULE"})
    msp.add_line((x1, y_top - row_h * 2), (x2, y_top - row_h * 2), dxfattribs={"layer": "SCHEDULE"})
    for x in x_cols[1:-1]:
        msp.add_line((x, y_top - row_h), (x, y_bottom), dxfattribs={"layer": "SCHEDULE"})

    _add_text(msp, "PIPE SCHEDULE", ((x1 + x2) / 2, y_top - row_h * 0.62),
              height=SUBTITLE_TEXT_HEIGHT, layer="SCHEDULE")
    for i, header in enumerate(headers):
        _add_text(msp, header, (x_cols[i] + 35, y_top - row_h - row_h * 0.6),
                  height=SCHEDULE_TEXT_HEIGHT, layer="SCHEDULE", align="LEFT")

    for row, pipe in enumerate(geometry.pipes):
        y = y_top - row_h * (row + 2) - row_h * 0.6
        rating = pipe.label_spec.replace(f"DN{pipe.dn} ", "")
        values = (
            pipe.label_main,
            f"DN{pipe.dn}",
            rating,
            str(int(round(pipe.pipe_od))),
            pipe.label_ins.replace("Ins ", "") if pipe.label_ins else "-",
        )
        for i, value in enumerate(values):
            _add_text(msp, value, (x_cols[i] + 35, y),
                      height=SCHEDULE_TEXT_HEIGHT, layer="SCHEDULE", align="LEFT")


# ── Legend strip (under schedule) ──────────────────────────────────────────

def _draw_legend(msp, layout):
    """Bordered legend box with one stacked row per entry: a colour sample on
    its own layer + an aligned label. Easy to read, clear colour hierarchy."""
    entries = layout["legend_entries"]
    x1 = layout["sheet_left"] + 160
    y_top = layout["legend_top"]
    y_bottom = layout["legend_bottom"]
    box_w = LEGEND_SAMPLE_W + 1600
    x2 = x1 + box_w

    _rect(msp, x1, y_top, x2, y_bottom, "LEGEND")
    header_y = y_top - LEGEND_HEADER_H * 0.62
    _add_text(msp, "LEGEND", ((x1 + x2) / 2, header_y),
              height=SUBTITLE_TEXT_HEIGHT, layer="LEGEND")
    msp.add_line((x1, y_top - LEGEND_HEADER_H), (x2, y_top - LEGEND_HEADER_H),
                 dxfattribs={"layer": "LEGEND"})

    sample_x1 = x1 + 120
    sample_x2 = sample_x1 + LEGEND_SAMPLE_W
    label_x = sample_x2 + 160
    for i, (label, layer) in enumerate(entries):
        row_mid = y_top - LEGEND_HEADER_H - (i + 0.5) * LEGEND_ROW_H
        msp.add_line((sample_x1, row_mid), (sample_x2, row_mid),
                     dxfattribs={"layer": layer})
        _add_text(msp, label, (label_x, row_mid - NOTE_TEXT_HEIGHT * 0.4),
                  height=NOTE_TEXT_HEIGHT, layer="LEGEND", align="LEFT")


# ── Title block (bottom-right) ─────────────────────────────────────────────

def _draw_title_block(msp, geometry, layout, metadata):
    x2 = layout["sheet_right"] - 160
    x1 = x2 - TITLE_BLOCK_W
    y1 = layout["title_top"]
    y2 = layout["title_bottom"]

    _rect(msp, x1, y1, x2, y2, "TITLE_BLOCK")
    header_y = y1 - 300
    msp.add_line((x1, header_y), (x2, header_y), dxfattribs={"layer": "TITLE_BLOCK"})

    _add_text(msp, "PIPE RACK", (x1 + 70, y1 - 130), height=TITLE_TEXT_HEIGHT, layer="TITLE_BLOCK", align="LEFT")
    _add_text(msp, "SPACING ARRANGEMENT (SCHEMATIC)", (x1 + 70, y1 - 250),
              height=SUBTITLE_TEXT_HEIGHT, layer="TITLE_BLOCK", align="LEFT")

    rows = [
        ("PROJECT", metadata.get("project", "-")),
        ("CLIENT", metadata.get("client", "-")),
        ("PROFILE", metadata.get("profile_label", "N/A")),
        ("COLUMN", metadata.get("column_label", metadata.get("profile_label", "N/A"))),
        ("UNITS / SCALE", "mm / AS SHOWN (HORIZONTAL)"),
        ("DRN  CHK  APP", "-    -    -"),
        ("DWG No.  REV", "PRS-AUTO    A"),
        ("DATE  SHEET", "-    1 OF 1"),
    ]
    label_x = x1 + 70
    value_x = x1 + 760
    for i, (key, value) in enumerate(rows):
        y = header_y - 90 - i * 96
        _add_text(msp, key, (label_x, y), height=NOTE_TEXT_HEIGHT, layer="TITLE_BLOCK", align="LEFT")
        _add_text(msp, ":", (value_x - 40, y), height=NOTE_TEXT_HEIGHT, layer="TITLE_BLOCK", align="LEFT")
        _add_text(msp, value, (value_x, y), height=NOTE_TEXT_HEIGHT, layer="TITLE_BLOCK", align="LEFT")


def _draw_sheet_border(msp, layout):
    _rect(msp, layout["sheet_left"], layout["sheet_top"],
          layout["sheet_right"], layout["sheet_bottom"], "TITLE_BLOCK")
