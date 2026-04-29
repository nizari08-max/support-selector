"""SVG schematic generator for rack calculator results."""

import math

from pipe_flange_data import get_pipe_od, get_flange_od, rating_label


def generate_diagram(pipes, result, scale_max_width=1100):
    """
    Build an inline SVG schematic showing the rack, pipes, flanges,
    spacing dimensions, and total width.

    Returns SVG as a string.
    """
    edge_offset = result['edge_offset']
    spacings = result['spacings']
    inner_total = result['inner_total']
    rack_width = result['rack_width']
    steel_column = result['steel_column']

    # Build cumulative x positions (mm) for each pipe centerline (left edge = 0)
    x_positions = [edge_offset]
    for s in spacings:
        x_positions.append(x_positions[-1] + s)

    # Drawing layout. All dimensions still use the calculated x positions;
    # the larger margins only give labels and dimension arrows room to breathe.
    margin_left = 112
    margin_right = 112
    margin_top = 150
    margin_bottom = 172
    drawable = scale_max_width - margin_left - margin_right
    scale = drawable / rack_width  # px per mm

    def mx(mm):
        return margin_left + mm * scale

    pipe_y = margin_top + 80
    rack_top = margin_top + 26
    rack_bottom = pipe_y + 92

    svg_h = rack_bottom + margin_bottom
    svg_w = scale_max_width

    parts = []
    parts.append(f'<svg viewBox="0 0 {svg_w} {svg_h}" xmlns="http://www.w3.org/2000/svg" '
                 f'style="font-family: Inter, -apple-system, BlinkMacSystemFont, sans-serif; font-size: 11px;">')

    # Gradients for visual depth
    parts.append('''
      <defs>
        <marker id="dimArrow" markerWidth="7" markerHeight="7" refX="3.5" refY="3.5" orient="auto">
          <path d="M 0 0 L 7 3.5 L 0 7 z" fill="#dc2626"/>
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
      </defs>
    ''')

    # ---- Rack horizontal beam and columns ----
    rack_left_x = mx(0)
    rack_right_x = mx(rack_width)
    beam_y = pipe_y + 34
    beam_h = 20
    parts.append(f'<rect x="{rack_left_x}" y="{beam_y}" width="{rack_right_x - rack_left_x}" '
                 f'height="{beam_h}" rx="2" fill="url(#rackGrad)" stroke="#215c3d" stroke-width="1"/>')

    col_w_px = max(steel_column * scale, 8)
    parts.append(f'<rect x="{rack_left_x}" y="{rack_top}" width="{col_w_px}" '
                 f'height="{rack_bottom - rack_top}" rx="3" fill="url(#rackGrad)" '
                 f'stroke="#215c3d" stroke-width="1"/>')
    parts.append(f'<rect x="{rack_left_x}" y="{rack_top}" width="{col_w_px}" '
                 f'height="{rack_bottom - rack_top}" rx="3" fill="url(#hatch)" opacity="0.45"/>')
    parts.append(f'<rect x="{rack_right_x - col_w_px}" y="{rack_top}" width="{col_w_px}" '
                 f'height="{rack_bottom - rack_top}" rx="3" fill="url(#rackGrad)" '
                 f'stroke="#215c3d" stroke-width="1"/>')
    parts.append(f'<rect x="{rack_right_x - col_w_px}" y="{rack_top}" width="{col_w_px}" '
                 f'height="{rack_bottom - rack_top}" rx="3" fill="url(#hatch)" opacity="0.45"/>')

    left_col_cl = mx(steel_column / 2)
    right_col_cl = mx(rack_width - steel_column / 2)
    parts.append(f'<line x1="{left_col_cl}" y1="{rack_top - 34}" x2="{left_col_cl}" y2="{rack_bottom + 44}" '
                 f'stroke="#14532d" stroke-width="1" stroke-dasharray="8,5"/>')
    parts.append(f'<line x1="{right_col_cl}" y1="{rack_top - 34}" x2="{right_col_cl}" y2="{rack_bottom + 44}" '
                 f'stroke="#14532d" stroke-width="1" stroke-dasharray="8,5"/>')
    parts.append(f'<text x="{left_col_cl}" y="{rack_top - 28}" text-anchor="middle" '
                 f'fill="#14532d" font-size="9" font-weight="700">COLUMN CL</text>')
    parts.append(f'<text x="{right_col_cl}" y="{rack_top - 28}" text-anchor="middle" '
                 f'fill="#14532d" font-size="9" font-weight="700">COLUMN CL</text>')

    def bolt_holes(cx, cy, bolt_circle_r, bolt_r, count=8):
        holes = []
        for j in range(count):
            angle = (math.tau * j / count) - math.pi / 2
            bx = cx + math.cos(angle) * bolt_circle_r
            by = cy + math.sin(angle) * bolt_circle_r
            holes.append(f'<circle cx="{bx:.2f}" cy="{by:.2f}" r="{bolt_r:.2f}" '
                         f'fill="#f8fafc" stroke="#475569" stroke-width="0.55"/>')
        return ''.join(holes)

    # ---- Pipes with insulation rings and staggered flanges ----
    for i, (pipe, x_mm) in enumerate(zip(pipes, x_positions)):
        cx = mx(x_mm)
        draw_cx = cx
        pipe_od = get_pipe_od(pipe['dn'])
        flange_od = get_flange_od(pipe['dn'], pipe['rating']) or pipe_od
        ins = pipe['insulation']

        pipe_r_px = max(min(pipe_od * scale / 2, 20), 5)
        ins_r_px = max(min((pipe_od + 2 * ins) * scale / 2, 26), pipe_r_px)
        flange_r_px = max(min(flange_od * scale / 2, 34), pipe_r_px + 9, 14)
        if i == 0:
            column_clearance_px = cx - (rack_left_x + col_w_px)
            flange_r_px = min(flange_r_px, max(pipe_r_px + 7, column_clearance_px - 16))
            ins_r_px = min(ins_r_px, max(pipe_r_px, column_clearance_px - 20))
        flange_r_px = max(flange_r_px, pipe_r_px + 7)
        if i == 0:
            min_gap_px = 14
            first_symbol_left = draw_cx - max(flange_r_px, ins_r_px)
            min_symbol_left = rack_left_x + col_w_px + min_gap_px
            draw_cx += max(0, min_symbol_left - first_symbol_left)

        parts.append(f'<line x1="{draw_cx}" y1="{rack_top - 10}" x2="{draw_cx}" y2="{rack_bottom + 10}" '
                     f'stroke="#94a3b8" stroke-width="0.7" stroke-dasharray="4,4"/>')
        parts.append(f'<line x1="{draw_cx - max(flange_r_px, ins_r_px) - 5}" y1="{pipe_y}" '
                     f'x2="{draw_cx + max(flange_r_px, ins_r_px) + 5}" y2="{pipe_y}" '
                     f'stroke="#94a3b8" stroke-width="0.6" stroke-dasharray="4,4"/>')

        # Insulation ring (drawn first, behind pipe)
        if ins > 0:
            parts.append(f'<circle cx="{draw_cx}" cy="{pipe_y}" r="{ins_r_px}" '
                         f'fill="url(#insulGrad)" stroke="#b69b57" stroke-width="0.7" opacity="0.9"/>')

        # Circular flange plate with visible bolt holes.
        bolt_circle_r = max(flange_r_px * 0.72, pipe_r_px + 4)
        bolt_r = max(min(flange_r_px * 0.075, 2.5), 1.25)
        parts.append(f'<circle cx="{draw_cx}" cy="{pipe_y}" r="{flange_r_px}" '
                     f'fill="url(#flangeGrad)" stroke="#475569" stroke-width="1.1"/>')
        parts.append(f'<circle cx="{draw_cx}" cy="{pipe_y}" r="{max(pipe_r_px + 3, flange_r_px * 0.42)}" '
                     f'fill="#f8fafc" stroke="#64748b" stroke-width="0.7"/>')
        parts.append(bolt_holes(draw_cx, pipe_y, bolt_circle_r, bolt_r))

        # Pipe
        parts.append(f'<circle cx="{draw_cx}" cy="{pipe_y}" r="{pipe_r_px}" '
                     f'fill="url(#pipeGrad)" stroke="#7f1d1d" stroke-width="1.1"/>')
        parts.append(f'<circle cx="{draw_cx}" cy="{pipe_y}" r="{max(pipe_r_px * 0.48, 2)}" '
                     f'fill="#fff5f5" stroke="#991b1b" stroke-width="0.7"/>')

        # Pipe number + spec label below
        label_y_base = pipe_y + max(flange_r_px, ins_r_px, pipe_r_px) + 22
        label_w = 86
        label_h = 31 if ins else 20
        parts.append(f'<rect x="{draw_cx - label_w/2}" y="{label_y_base - 12}" width="{label_w}" height="{label_h}" '
                     f'rx="3" fill="#ffffff" stroke="#e2e8f0" opacity="0.96"/>')
        parts.append(f'<text x="{draw_cx}" y="{label_y_base}" text-anchor="middle" '
                     f'fill="#0f172a" font-size="10" font-weight="700">P{i+1}</text>')

        spec = f"DN{pipe['dn']} {rating_label(pipe['rating']).replace('Class ', '#').replace(' (Series ','-S').replace(')','')}"
        parts.append(f'<text x="{draw_cx}" y="{label_y_base + 14}" text-anchor="middle" '
                     f'fill="#475569" font-size="9">{spec}</text>')
        if ins:
            parts.append(f'<text x="{draw_cx}" y="{label_y_base + 27}" text-anchor="middle" '
                         f'fill="#64748b" font-size="8" font-style="italic">ins {ins}mm</text>')

    # ---- Dimension lines ----
    dim_y = rack_top - 12

    def dim_line(x1, x2, label, y, color="#dc2626", bg="#ffffff"):
        s = []
        s.append(f'<line x1="{x1}" y1="{y}" x2="{x2}" y2="{y}" stroke="{color}" stroke-width="1.1" '
                 f'marker-start="url(#dimArrow)" marker-end="url(#dimArrow)"/>')
        s.append(f'<line x1="{x1}" y1="{y-7}" x2="{x1}" y2="{y+7}" stroke="{color}" stroke-width="1"/>')
        s.append(f'<line x1="{x2}" y1="{y-7}" x2="{x2}" y2="{y+7}" stroke="{color}" stroke-width="1"/>')
        cx = (x1 + x2) / 2
        text_w = max(len(label) * 6 + 10, 38)
        s.append(f'<rect x="{cx - text_w/2}" y="{y-18}" width="{text_w}" height="14" '
                 f'rx="3" fill="{bg}" stroke="#fee2e2" stroke-width="0.6"/>')
        s.append(f'<text x="{cx}" y="{y-8}" text-anchor="middle" fill="{color}" '
                 f'font-size="10" font-weight="700">{label}</text>')
        return ''.join(s)

    # First dimension is drawn from column centerline to first pipe centerline.
    first_gap = int(round(edge_offset - steel_column / 2))
    parts.append(dim_line(left_col_cl, mx(edge_offset), f"{first_gap} CL-CL", dim_y))
    # Inter-pipe spacings
    for i, s in enumerate(spacings):
        y = dim_y - 22 if i % 2 else dim_y
        parts.append(dim_line(mx(x_positions[i]), mx(x_positions[i+1]), str(s), y))

    # ---- Total dimensions below ----
    bot_y1 = beam_y + beam_h + 50
    bot_y2 = bot_y1 + 25
    parts.append(dim_line(left_col_cl, mx(inner_total), f"{inner_total} mm inner",
                          bot_y1, color="#b91c1c", bg="#fff7ed"))
    parts.append(dim_line(left_col_cl, right_col_cl, f"{rack_width} mm rack width CL-CL",
                          bot_y2, color="#dc2626", bg="#fff7ed"))

    # ---- Vertical extension lines ----
    for x_mm in [steel_column / 2] + x_positions:
        x = mx(x_mm)
        parts.append(f'<line x1="{x}" y1="{rack_top}" x2="{x}" y2="{dim_y - 30}" '
                     f'stroke="#cbd5e1" stroke-width="0.7" stroke-dasharray="3,4"/>')
    for x in [mx(0), mx(inner_total), left_col_cl, right_col_cl]:
        parts.append(f'<line x1="{x}" y1="{rack_bottom}" x2="{x}" y2="{bot_y2 + 6}" '
                     f'stroke="#cbd5e1" stroke-width="0.7" stroke-dasharray="3,4"/>')

    parts.append('</svg>')
    return ''.join(parts)
