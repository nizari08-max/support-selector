"""SVG schematic generator for rack calculator results."""

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

    # Drawing layout
    margin_left = 80
    margin_right = 80
    margin_top = 110
    margin_bottom = 130
    drawable = scale_max_width - margin_left - margin_right
    scale = drawable / rack_width  # px per mm

    def mx(mm):
        return margin_left + mm * scale

    pipe_y = margin_top + 80
    rack_top = margin_top + 30
    rack_bottom = pipe_y + 80

    svg_h = rack_bottom + margin_bottom
    svg_w = scale_max_width

    parts = []
    parts.append(f'<svg viewBox="0 0 {svg_w} {svg_h}" xmlns="http://www.w3.org/2000/svg" '
                 f'style="font-family: -apple-system, sans-serif; font-size: 11px;">')

    # Gradients for visual depth
    parts.append('''
      <defs>
        <linearGradient id="rackGrad" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stop-color="#4a8569"/>
          <stop offset="100%" stop-color="#2e5e44"/>
        </linearGradient>
        <linearGradient id="pipeGrad" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stop-color="#d65d54"/>
          <stop offset="100%" stop-color="#a23a32"/>
        </linearGradient>
        <linearGradient id="insulGrad" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stop-color="#f0e8d8"/>
          <stop offset="100%" stop-color="#d8c8a0"/>
        </linearGradient>
        <linearGradient id="flangeGrad" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stop-color="#5a6470"/>
          <stop offset="100%" stop-color="#384149"/>
        </linearGradient>
      </defs>
    ''')

    # ---- Rack horizontal beam ----
    rack_left_x = mx(0)
    rack_right_x = mx(rack_width)
    beam_y = pipe_y + 25
    beam_h = 18
    parts.append(f'<rect x="{rack_left_x}" y="{beam_y}" width="{rack_right_x - rack_left_x}" '
                 f'height="{beam_h}" fill="url(#rackGrad)" stroke="#2e5e44" stroke-width="0.8"/>')

    # ---- Rack vertical columns at the ends (using actual steel column width) ----
    col_w_px = max(steel_column * scale, 8)
    parts.append(f'<rect x="{rack_left_x}" y="{rack_top}" width="{col_w_px}" '
                 f'height="{rack_bottom - rack_top}" fill="url(#rackGrad)" '
                 f'stroke="#2e5e44" stroke-width="0.8"/>')
    parts.append(f'<rect x="{rack_right_x - col_w_px}" y="{rack_top}" width="{col_w_px}" '
                 f'height="{rack_bottom - rack_top}" fill="url(#rackGrad)" '
                 f'stroke="#2e5e44" stroke-width="0.8"/>')

    # ---- Pipes with insulation rings and staggered flanges ----
    for i, (pipe, x_mm) in enumerate(zip(pipes, x_positions)):
        cx = mx(x_mm)
        pipe_od = get_pipe_od(pipe['dn'])
        flange_od = get_flange_od(pipe['dn'], pipe['rating']) or pipe_od
        ins = pipe['insulation']

        pipe_r_px = max(pipe_od * scale / 2, 3)
        ins_r_px = max((pipe_od + 2 * ins) * scale / 2, pipe_r_px)
        flange_r_px = max(flange_od * scale / 2, 5)

        # Stagger flanges: even-index up, odd-index down
        flange_offset = -8 if i % 2 == 0 else 8

        # Insulation ring (drawn first, behind pipe)
        if ins > 0:
            parts.append(f'<circle cx="{cx}" cy="{pipe_y}" r="{ins_r_px}" '
                         f'fill="url(#insulGrad)" stroke="#a89870" stroke-width="0.5" opacity="0.85"/>')

        # Pipe
        parts.append(f'<circle cx="{cx}" cy="{pipe_y}" r="{pipe_r_px}" '
                     f'fill="url(#pipeGrad)" stroke="#7a2620" stroke-width="0.7"/>')

        # Flange (offset for stagger)
        parts.append(f'<ellipse cx="{cx}" cy="{pipe_y + flange_offset}" '
                     f'rx="{flange_r_px}" ry="{flange_r_px*0.35}" '
                     f'fill="url(#flangeGrad)" stroke="#2a3138" stroke-width="0.7" opacity="0.85"/>')

        # Pipe number + spec label below
        label_y_base = pipe_y + max(flange_r_px*0.35, ins_r_px) + 14
        parts.append(f'<text x="{cx}" y="{label_y_base}" text-anchor="middle" '
                     f'fill="#1d2733" font-weight="600">{i+1}</text>')

        spec = f"DN{pipe['dn']} {rating_label(pipe['rating']).replace('Class ', '#').replace(' (Series ','-S').replace(')','')}"
        parts.append(f'<text x="{cx}" y="{label_y_base + 14}" text-anchor="middle" '
                     f'fill="#6c7a89" font-size="10">{spec}</text>')
        if ins:
            parts.append(f'<text x="{cx}" y="{label_y_base + 27}" text-anchor="middle" '
                         f'fill="#6c7a89" font-size="9" font-style="italic">ins {ins}mm</text>')

    # ---- Dimension lines ----
    dim_y = rack_top - 8

    def dim_line(x1, x2, label, y, color="#1d2733"):
        s = []
        s.append(f'<line x1="{x1}" y1="{y}" x2="{x2}" y2="{y}" stroke="{color}" stroke-width="1"/>')
        s.append(f'<line x1="{x1}" y1="{y-4}" x2="{x1}" y2="{y+4}" stroke="{color}" stroke-width="1"/>')
        s.append(f'<line x1="{x2}" y1="{y-4}" x2="{x2}" y2="{y+4}" stroke="{color}" stroke-width="1"/>')
        cx = (x1 + x2) / 2
        text_w = max(len(label) * 6 + 6, 32)
        s.append(f'<rect x="{cx - text_w/2}" y="{y-12}" width="{text_w}" height="14" '
                 f'fill="white" stroke="none"/>')
        s.append(f'<text x="{cx}" y="{y-2}" text-anchor="middle" fill="{color}" '
                 f'font-weight="600">{label}</text>')
        return ''.join(s)

    # Edge offset
    parts.append(dim_line(mx(0), mx(edge_offset), str(edge_offset), dim_y))
    # Inter-pipe spacings
    for i, s in enumerate(spacings):
        parts.append(dim_line(mx(x_positions[i]), mx(x_positions[i+1]), str(s), dim_y))

    # ---- Total dimensions below ----
    bot_y1 = beam_y + beam_h + 50
    bot_y2 = bot_y1 + 25
    parts.append(dim_line(mx(0), mx(inner_total), f"{inner_total} mm (inner)",
                          bot_y1, color="#9a2723"))
    parts.append(dim_line(mx(0), mx(rack_width), f"{rack_width} mm (rack width)",
                          bot_y2, color="#c8332e"))

    # ---- Vertical extension lines ----
    for x_mm in [0] + x_positions:
        x = mx(x_mm)
        parts.append(f'<line x1="{x}" y1="{rack_top}" x2="{x}" y2="{dim_y - 6}" '
                     f'stroke="#b0bac4" stroke-width="0.5" stroke-dasharray="2,3"/>')
    for x_mm in [0, inner_total, rack_width]:
        x = mx(x_mm)
        parts.append(f'<line x1="{x}" y1="{rack_bottom}" x2="{x}" y2="{bot_y2 + 6}" '
                     f'stroke="#b0bac4" stroke-width="0.5" stroke-dasharray="2,3"/>')

    parts.append('</svg>')
    return ''.join(parts)
