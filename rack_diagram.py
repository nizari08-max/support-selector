"""SVG schematic generator for rack calculator results.

Pipeline:  calculate_rack() -> build_geometry_model() -> render_svg()

``rack_geometry.build_geometry_model()`` produces a true-scale (mm) layout
that is independent of any rendering target. This module turns that model
into an SVG. The only rendering-specific concession to readability is a
minimum on-screen radius for very small pipe symbols (``MIN_PIPE_R_PX``) -
the underlying geometry model stays true-scale so a future DXF renderer can
reuse it unmodified.
"""

import math

from rack_geometry import build_geometry_model

# Minimum on-screen radius (px) for the bold pipe-body circle, applied only
# to the SVG rendering so very small pipes (e.g. DN50 next to DN1000) remain
# readable. Does not affect geometry coordinates or dimensions.
MIN_PIPE_R_PX = 4

# Minimum visible clearance (px) between adjacent pipe envelopes (and
# between an end pipe's envelope and the rack column it sits closest to).
# This is an SVG-only readability constraint - it never changes the
# underlying mm geometry/dimensions, only how large the flange/insulation
# circles are drawn.
ENVELOPE_CLEARANCE_PX = 6


def generate_diagram(pipes, result, scale_max_width=1100, spare_space_location='right'):
    """
    Build an inline SVG schematic showing the rack, pipes, flanges,
    spacing dimensions, total width, and future spare space zone.

    spare_space_location:
        'right'  - spare space shown after last pipe, before right column
        'center' - spare space inserted into the pipe-pair gap nearest the
                   rack center (pipes after that gap shift right)
    Returns SVG as a string.
    """
    geometry = build_geometry_model(pipes, result, spare_space_location=spare_space_location)
    return render_svg(geometry, scale_max_width=scale_max_width)


def render_svg(geometry, scale_max_width=1100):
    rack_width   = geometry.rack_width
    steel_column = geometry.column_width

    margin_left  = 112
    margin_right = 112
    drawable = scale_max_width - margin_left - margin_right

    # x=0 / x=rack_width are the LEFT/RIGHT COLUMN CENTERLINES; the rack's
    # drawable extent runs from the outer edge of the left column
    # (-column/2) to the outer edge of the right column (rack_width + column/2).
    rack_left_edge  = -steel_column / 2
    rack_right_edge = rack_width + steel_column / 2
    total_span = rack_right_edge - rack_left_edge
    scale = drawable / total_span  # px per mm

    def mx(mm):
        return margin_left + (mm - rack_left_edge) * scale

    # ── Rack/column extents in px (computed early - independent of the
    #    vertical layout below) ─────────────────────────────────────────────
    rack_left_x  = mx(rack_left_edge)
    rack_right_x = mx(rack_right_edge)
    col_w_px = max(steel_column * scale, 8)
    col_inner_left_x  = rack_left_x + col_w_px
    col_inner_right_x = rack_right_x - col_w_px

    cx_list = [mx(p.cl_x) for p in geometry.pipes]

    # ── Two-scale symbol sizing ──────────────────────────────────────────────
    # `scale` (px/mm) positions every centerline/dimension at true scale
    # (requirement B/G). Pipe/flange/insulation symbols additionally use a
    # single uniform `sym_scale_factor` (<= 1) so that the rack's largest
    # envelope just fits in its tightest available gap - this keeps relative
    # OD differences (DN900 vs DN200, flange class, insulation) visible
    # instead of collapsing every pipe to the same capped radius.
    n_pipes = len(geometry.pipes)
    available_px = []
    for i in range(n_pipes):
        cx = cx_list[i]
        if i > 0:
            left_avail = (cx - cx_list[i - 1]) / 2 - ENVELOPE_CLEARANCE_PX / 2
        else:
            left_avail = (cx - col_inner_left_x) - ENVELOPE_CLEARANCE_PX
        if i < n_pipes - 1:
            right_avail = (cx_list[i + 1] - cx) / 2 - ENVELOPE_CLEARANCE_PX / 2
        else:
            right_avail = (col_inner_right_x - cx) - ENVELOPE_CLEARANCE_PX
        available_px.append(max(min(left_avail, right_avail), 1))

    sym_scale_factor = 1.0
    for i, p in enumerate(geometry.pipes):
        envelope_od = max(p.pipe_od, p.ins_od, p.flange_od)
        ideal_r_px = envelope_od * scale / 2
        if ideal_r_px > 0:
            sym_scale_factor = min(sym_scale_factor, available_px[i] / ideal_r_px)

    render_pipes = []
    any_undersized = False
    for i, p in enumerate(geometry.pipes):
        pipe_r_px = p.pipe_od * scale / 2 * sym_scale_factor
        ins_r_px = max(p.ins_od * scale / 2 * sym_scale_factor, pipe_r_px)
        flange_r_px = max(p.flange_od * scale / 2 * sym_scale_factor, pipe_r_px + 3 * sym_scale_factor)

        if pipe_r_px < MIN_PIPE_R_PX:
            # Last-resort floor for pipes that remain sub-pixel even after
            # uniform scaling - enlarge only this pipe's symbols, preserving
            # their relative proportions.
            any_undersized = True
            floor_factor = (MIN_PIPE_R_PX / pipe_r_px) if pipe_r_px > 0 else 1.0
            pipe_r_px = MIN_PIPE_R_PX
            ins_r_px = max(ins_r_px * floor_factor, pipe_r_px)
            flange_r_px = max(flange_r_px * floor_factor, pipe_r_px + 3)

        render_pipes.append((p, pipe_r_px, ins_r_px, flange_r_px))

    max_symbol_r = max((max(ins_r, fl_r) for _, _, ins_r, fl_r in render_pipes), default=20)

    # ── Label sizing / collision detection ──────────────────────────────────
    # Estimate each pipe's label width from its spec text; if neighboring
    # pipes are closer together (in px) than their combined label widths
    # would allow, stagger labels onto two rows so they don't overlap.
    label_widths = [
        max(70, min(112, len(p.label_spec) * 6 + 16))
        for p in geometry.pipes
    ]
    stagger_labels = False
    for i in range(n_pipes - 1):
        gap_px = cx_list[i + 1] - cx_list[i]
        if gap_px < (label_widths[i] + label_widths[i + 1]) / 2:
            stagger_labels = True
            break
    label_row_h = 35  # vertical offset between staggered label rows

    # ── Dynamic vertical layout ──────────────────────────────────────────────
    top_rows = (max((d.row for d in geometry.top_dimensions), default=0) + 1)
    bottom_rows = (max((d.row for d in geometry.bottom_dimensions), default=0) + 1)

    margin_top = 60 + top_rows * 22
    rack_top = margin_top + 26
    pipe_y = rack_top + max_symbol_r + 14
    beam_y = pipe_y + max_symbol_r + 14
    beam_h = 20
    rack_bottom = beam_y + beam_h

    label_h = 31  # max pipe-label block height (with insulation line)
    label_extra = label_row_h if stagger_labels else 0
    bottom_y0 = rack_bottom + 50 + label_extra
    bottom_y_for_row = lambda r: bottom_y0 + r * 28
    bottom_limit = bottom_y_for_row(bottom_rows - 1) + 8
    margin_bottom = (bottom_limit - rack_bottom) + 20

    svg_h = rack_bottom + margin_bottom
    svg_w = scale_max_width

    parts = []
    parts.append(
        f'<svg viewBox="0 0 {svg_w} {svg_h}" xmlns="http://www.w3.org/2000/svg" '
        f'style="font-family: Inter, -apple-system, BlinkMacSystemFont, sans-serif; font-size: 11px;">'
    )

    # ── Defs ─────────────────────────────────────────────────────────────────
    parts.append('''
      <defs>
        <marker id="dimArrowEnd" markerWidth="7" markerHeight="7" refX="3.5" refY="3.5" orient="auto">
          <path d="M 0 0 L 7 3.5 L 0 7 z" fill="#dc2626"/>
        </marker>
        <marker id="dimArrowStart" markerWidth="7" markerHeight="7" refX="3.5" refY="3.5" orient="auto">
          <path d="M 7 0 L 0 3.5 L 7 7 z" fill="#dc2626"/>
        </marker>
        <marker id="dimArrowRedEnd" markerWidth="7" markerHeight="7" refX="3.5" refY="3.5" orient="auto">
          <path d="M 0 0 L 7 3.5 L 0 7 z" fill="#b91c1c"/>
        </marker>
        <marker id="dimArrowRedStart" markerWidth="7" markerHeight="7" refX="3.5" refY="3.5" orient="auto">
          <path d="M 7 0 L 0 3.5 L 7 7 z" fill="#b91c1c"/>
        </marker>
        <marker id="dimArrowAmberEnd" markerWidth="7" markerHeight="7" refX="3.5" refY="3.5" orient="auto">
          <path d="M 0 0 L 7 3.5 L 0 7 z" fill="#b45309"/>
        </marker>
        <marker id="dimArrowAmberStart" markerWidth="7" markerHeight="7" refX="3.5" refY="3.5" orient="auto">
          <path d="M 7 0 L 0 3.5 L 7 7 z" fill="#b45309"/>
        </marker>
        <linearGradient id="rackGrad" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stop-color="#5f9a75"/>
          <stop offset="100%" stop-color="#2f6f4c"/>
        </linearGradient>
        <linearGradient id="pipeGrad" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stop-color="#f1746a"/>
          <stop offset="55%" stop-color="#d8473f"/>
          <stop offset="100%" stop-color="#a72f2c"/>
        </linearGradient>
        <linearGradient id="insulGrad" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stop-color="#fff7df"/>
          <stop offset="100%" stop-color="#e5d5a9"/>
        </linearGradient>
        <linearGradient id="flangeGrad" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stop-color="#d8dee6"/>
          <stop offset="100%" stop-color="#8f9aa6"/>
        </linearGradient>
        <pattern id="hatch" patternUnits="userSpaceOnUse" width="6" height="6" patternTransform="rotate(45)">
          <line x1="0" y1="0" x2="0" y2="6" stroke="#1e5d3d" stroke-width="1" opacity="0.32"/>
        </pattern>
        <pattern id="spareHatch" patternUnits="userSpaceOnUse" width="10" height="10" patternTransform="rotate(45)">
          <line x1="0" y1="0" x2="0" y2="10" stroke="#b45309" stroke-width="2.2" opacity="0.30"/>
        </pattern>
      </defs>
    ''')

    # ── Future spare space zone(s) (drawn first, behind pipes) ───────────────
    zone_h = beam_y + beam_h - rack_top
    for zone in geometry.spare_zones:
        sx1 = mx(zone.x1)
        sx2 = mx(zone.x2)
        parts.append(
            f'<rect x="{sx1}" y="{rack_top}" width="{sx2 - sx1}" height="{zone_h}" '
            f'fill="#fef9c3" opacity="0.60" rx="2"/>'
        )
        parts.append(
            f'<rect x="{sx1}" y="{rack_top}" width="{sx2 - sx1}" height="{zone_h}" '
            f'fill="url(#spareHatch)" rx="2"/>'
        )
        parts.append(
            f'<rect x="{sx1}" y="{rack_top}" width="{sx2 - sx1}" height="{zone_h}" '
            f'fill="none" stroke="#d97706" stroke-width="1.4" stroke-dasharray="5,3" rx="2"/>'
        )
        zone_w_px = sx2 - sx1
        zone_cx = (sx1 + sx2) / 2
        zone_mid_y = rack_top + zone_h / 2 - 6
        if zone_w_px >= 28:
            parts.append(
                f'<text x="{zone_cx}" y="{zone_mid_y}" text-anchor="middle" '
                f'fill="#92400e" font-size="8" font-weight="700" opacity="0.85">FUTURE</text>'
            )
            parts.append(
                f'<text x="{zone_cx}" y="{zone_mid_y + 11}" text-anchor="middle" '
                f'fill="#92400e" font-size="8" font-weight="700" opacity="0.85">SPARE</text>'
            )
        else:
            # Too narrow for the in-zone "FUTURE / SPARE" label - place a
            # compact label below the rack with a leader line instead.
            leader_y = rack_bottom + 12
            parts.append(
                f'<line x1="{zone_cx}" y1="{rack_bottom}" x2="{zone_cx}" y2="{leader_y - 7}" '
                f'stroke="#b45309" stroke-width="0.8" stroke-dasharray="2,2"/>'
            )
            parts.append(
                f'<text x="{zone_cx}" y="{leader_y}" text-anchor="middle" '
                f'fill="#92400e" font-size="8" font-weight="700">SPARE</text>'
            )

    # ── Rack beam and columns ────────────────────────────────────────────────
    parts.append(
        f'<rect x="{rack_left_x}" y="{beam_y}" width="{rack_right_x - rack_left_x}" '
        f'height="{beam_h}" rx="2" fill="url(#rackGrad)" stroke="#215c3d" stroke-width="1"/>'
    )

    for col_x in (rack_left_x, rack_right_x - col_w_px):
        parts.append(
            f'<rect x="{col_x}" y="{rack_top}" width="{col_w_px}" '
            f'height="{rack_bottom - rack_top}" rx="3" fill="url(#rackGrad)" '
            f'stroke="#215c3d" stroke-width="1"/>'
        )
        parts.append(
            f'<rect x="{col_x}" y="{rack_top}" width="{col_w_px}" '
            f'height="{rack_bottom - rack_top}" rx="3" fill="url(#hatch)" opacity="0.45"/>'
        )

    left_col_cl  = mx(geometry.column_cl_left)
    right_col_cl = mx(geometry.column_cl_right)
    cl_top = rack_top - 16 - top_rows * 22
    for cl_x in (left_col_cl, right_col_cl):
        parts.append(
            f'<line x1="{cl_x}" y1="{cl_top}" x2="{cl_x}" y2="{rack_bottom + 44}" '
            f'stroke="#14532d" stroke-width="1" stroke-dasharray="8,5"/>'
        )
    parts.append(
        f'<text x="{left_col_cl}" y="{cl_top - 6}" text-anchor="middle" '
        f'fill="#14532d" font-size="9" font-weight="700">COLUMN CL</text>'
    )
    parts.append(
        f'<text x="{right_col_cl}" y="{cl_top - 6}" text-anchor="middle" '
        f'fill="#14532d" font-size="9" font-weight="700">COLUMN CL</text>'
    )

    # ── Pipes ────────────────────────────────────────────────────────────────
    def bolt_holes(cx, cy, bolt_circle_r, bolt_r, count=8):
        holes = []
        for j in range(count):
            angle = (math.tau * j / count) - math.pi / 2
            bx = cx + math.cos(angle) * bolt_circle_r
            by = cy + math.sin(angle) * bolt_circle_r
            holes.append(
                f'<circle cx="{bx:.2f}" cy="{by:.2f}" r="{bolt_r:.2f}" '
                f'fill="#f8fafc" stroke="#475569" stroke-width="0.55"/>'
            )
        return ''.join(holes)

    for idx, (pipe, pipe_r_px, ins_r_px, flange_r_px) in enumerate(render_pipes):
        cx = cx_list[idx]

        # Pipe centerline (vertical + horizontal)
        parts.append(
            f'<line x1="{cx}" y1="{rack_top - 10}" x2="{cx}" y2="{rack_bottom + 10}" '
            f'stroke="#94a3b8" stroke-width="0.7" stroke-dasharray="4,4"/>'
        )
        parts.append(
            f'<line x1="{cx - max(flange_r_px, ins_r_px) - 5}" y1="{pipe_y}" '
            f'x2="{cx + max(flange_r_px, ins_r_px) + 5}" y2="{pipe_y}" '
            f'stroke="#94a3b8" stroke-width="0.6" stroke-dasharray="4,4"/>'
        )

        if pipe.insulation > 0:
            parts.append(
                f'<circle cx="{cx}" cy="{pipe_y}" r="{ins_r_px}" '
                f'fill="url(#insulGrad)" stroke="#b69b57" stroke-width="0.7" opacity="0.9"/>'
            )

        bolt_circle_r = max(flange_r_px * 0.72, pipe_r_px + 4)
        bolt_r        = max(min(flange_r_px * 0.075, 2.5), 1.25)
        parts.append(
            f'<circle cx="{cx}" cy="{pipe_y}" r="{flange_r_px}" '
            f'fill="url(#flangeGrad)" stroke="#475569" stroke-width="1.1"/>'
        )
        parts.append(
            f'<circle cx="{cx}" cy="{pipe_y}" r="{max(pipe_r_px + 3, flange_r_px * 0.42)}" '
            f'fill="#f8fafc" stroke="#64748b" stroke-width="0.7"/>'
        )
        parts.append(bolt_holes(cx, pipe_y, bolt_circle_r, bolt_r))
        parts.append(
            f'<circle cx="{cx}" cy="{pipe_y}" r="{pipe_r_px}" '
            f'fill="url(#pipeGrad)" stroke="#7f1d1d" stroke-width="1.1"/>'
        )
        parts.append(
            f'<circle cx="{cx}" cy="{pipe_y}" r="{max(pipe_r_px * 0.48, 2)}" '
            f'fill="#fff5f5" stroke="#991b1b" stroke-width="0.7"/>'
        )

        label_y_base = pipe_y + max(flange_r_px, ins_r_px, pipe_r_px) + 22
        if stagger_labels and idx % 2 == 1:
            label_y_base += label_row_h
        label_w = label_widths[idx]
        l_h = 31  # uniform 3-row label block height for all pipes (requirement E)
        parts.append(
            f'<rect x="{cx - label_w/2}" y="{label_y_base - 12}" width="{label_w}" height="{l_h}" '
            f'rx="3" fill="#ffffff" stroke="#e2e8f0" opacity="0.96"/>'
        )
        parts.append(
            f'<text x="{cx}" y="{label_y_base}" text-anchor="middle" '
            f'fill="#0f172a" font-size="10" font-weight="700">{pipe.label_main}</text>'
        )
        parts.append(
            f'<text x="{cx}" y="{label_y_base + 14}" text-anchor="middle" '
            f'fill="#475569" font-size="9">{pipe.label_spec}</text>'
        )
        if pipe.label_ins:
            parts.append(
                f'<text x="{cx}" y="{label_y_base + 27}" text-anchor="middle" '
                f'fill="#64748b" font-size="8" font-style="italic">{pipe.label_ins}</text>'
            )

    # ── Dimension line helper ────────────────────────────────────────────────
    def dim_line(x1, x2, label, y, color="#dc2626", bg="#ffffff",
                 border="#fee2e2", arrow_id="dimArrow"):
        s = []
        s.append(
            f'<line x1="{x1}" y1="{y}" x2="{x2}" y2="{y}" stroke="{color}" stroke-width="1.1" '
            f'marker-start="url(#{arrow_id}Start)" marker-end="url(#{arrow_id}End)"/>'
        )
        s.append(f'<line x1="{x1}" y1="{y-7}" x2="{x1}" y2="{y+7}" stroke="{color}" stroke-width="1"/>')
        s.append(f'<line x1="{x2}" y1="{y-7}" x2="{x2}" y2="{y+7}" stroke="{color}" stroke-width="1"/>')
        cx = (x1 + x2) / 2
        text_w = max(len(label) * 6 + 10, 38)
        s.append(
            f'<rect x="{cx - text_w/2}" y="{y-18}" width="{text_w}" height="14" '
            f'rx="3" fill="{bg}" stroke="{border}" stroke-width="0.6"/>'
        )
        s.append(
            f'<text x="{cx}" y="{y-8}" text-anchor="middle" fill="{color}" '
            f'font-size="10" font-weight="700">{label}</text>'
        )
        return ''.join(s)

    # ── Top dimension lines (column CL -> pipe1 CL, then pipe-to-pipe) ───────
    for d in geometry.top_dimensions:
        y = (rack_top - 12) - d.row * 22
        parts.append(dim_line(mx(d.x1), mx(d.x2), d.label, y))

    # ── Bottom dimension lines ───────────────────────────────────────────────
    for d in geometry.bottom_dimensions:
        y = bottom_y_for_row(d.row)
        if d.style == "annotation":
            cx = (mx(d.x1) + mx(d.x2)) / 2
            parts.append(
                f'<text x="{cx}" y="{y - 8}" text-anchor="middle" '
                f'fill="#7c2d12" font-size="10" font-weight="700">{d.label}</text>'
            )
        elif d.style == "spare":
            parts.append(dim_line(
                mx(d.x1), mx(d.x2), d.label, y,
                color="#b45309", bg="#fffbeb", border="#fde68a", arrow_id="dimArrowAmber"
            ))
        elif d.style == "total":
            parts.append(dim_line(
                mx(d.x1), mx(d.x2), d.label, y,
                color="#b91c1c", bg="#fff7ed", border="#fca5a5", arrow_id="dimArrowRed"
            ))
        else:
            parts.append(dim_line(
                mx(d.x1), mx(d.x2), d.label, y,
                color="#dc2626", bg="#fff7ed", border="#fca5a5"
            ))

    # ── Vertical extension lines (top) ───────────────────────────────────────
    top_ext_xs = {geometry.column_cl_left, geometry.column_cl_right}
    for p in geometry.pipes:
        top_ext_xs.add(p.cl_x)
    for x_mm in top_ext_xs:
        x = mx(x_mm)
        parts.append(
            f'<line x1="{x}" y1="{rack_top}" x2="{x}" y2="{(rack_top - 12) - (top_rows - 1) * 22 - 8}" '
            f'stroke="#cbd5e1" stroke-width="0.7" stroke-dasharray="3,4"/>'
        )

    # ── Vertical extension lines (bottom) ────────────────────────────────────
    bottom_ext_xs = {geometry.column_cl_left, geometry.column_cl_right}
    if geometry.spare_zones and geometry.spare_zones[0].gap_index == -1:
        # 'right'-placed spare: also mark the end of the occupied zone.
        bottom_ext_xs.add(geometry.column_cl_left + geometry.occupied_width)
    elif not geometry.spare_zones:
        bottom_ext_xs.add(geometry.column_cl_left + geometry.occupied_width)
    for zone in geometry.spare_zones:
        bottom_ext_xs.add(zone.x1)
        bottom_ext_xs.add(zone.x2)
    for x_mm in bottom_ext_xs:
        x = mx(x_mm)
        parts.append(
            f'<line x1="{x}" y1="{rack_bottom}" x2="{x}" y2="{bottom_limit}" '
            f'stroke="#cbd5e1" stroke-width="0.7" stroke-dasharray="3,4"/>'
        )

    # ── Notes / warnings ──────────────────────────────────────────────────────
    note_y = svg_h - 6
    for warning in reversed(geometry.warnings):
        parts.append(
            f'<text x="{margin_left}" y="{note_y}" '
            f'fill="#b45309" font-size="8" font-style="italic">'
            f'Note: {warning}</text>'
        )
        note_y -= 11

    if any_undersized:
        parts.append(
            f'<text x="{margin_left}" y="{note_y}" '
            f'fill="#94a3b8" font-size="8" font-style="italic">'
            f'Note: small-diameter pipes shown enlarged to a minimum visual size for readability.</text>'
        )
        note_y -= 11

    parts.append('</svg>')
    return ''.join(parts)
