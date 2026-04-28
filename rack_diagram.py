"""SVG schematic generator for rack calculator results."""

from pipe_flange_data import get_pipe_od, get_flange_od


def generate_diagram(pipes, result, scale_max_width=1100):
    """
    Build an inline SVG schematic showing the rack, pipes, flanges,
    spacing dimensions, and total width.

    Returns SVG as a string.
    """
    # Build cumulative x positions (mm) for each pipe centerline
    x_positions = [result['left_offset']]
    for s in result['spacings']:
        x_positions.append(x_positions[-1] + s)

    inner_width = result['total_width']
    rack_width = result['rack_width']

    # Scale to fit display: pick px-per-mm so rack fits in scale_max_width
    margin_left = 70
    margin_right = 70
    margin_top = 110
    margin_bottom = 130
    drawable = scale_max_width - margin_left - margin_right
    scale = drawable / rack_width  # px per mm

    def mx(mm):
        """Convert mm to SVG x in pixels."""
        return margin_left + mm * scale

    # Pipe vertical center
    pipe_y = margin_top + 80
    rack_top = margin_top + 30
    rack_bottom = pipe_y + 80

    svg_h = rack_bottom + margin_bottom
    svg_w = scale_max_width

    parts = []
    parts.append(f'<svg viewBox="0 0 {svg_w} {svg_h}" xmlns="http://www.w3.org/2000/svg" '
                 f'style="font-family: -apple-system, sans-serif; font-size: 11px;">')

    # Defs - subtle gradients
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
        <linearGradient id="flangeGrad" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stop-color="#5a6470"/>
          <stop offset="100%" stop-color="#384149"/>
        </linearGradient>
      </defs>
    ''')

    # ---- Rack steel beam (horizontal, behind the pipes) ----
    rack_left_x = mx(0)
    rack_right_x = mx(rack_width)
    beam_y = pipe_y + 25
    beam_h = 18
    parts.append(f'<rect x="{rack_left_x}" y="{beam_y}" width="{rack_right_x - rack_left_x}" height="{beam_h}" '
                 f'fill="url(#rackGrad)" stroke="#2e5e44" stroke-width="0.8"/>')

    # ---- Rack vertical columns at the ends ----
    col_w = 14
    for cx in [rack_left_x, rack_right_x - col_w]:
        parts.append(f'<rect x="{cx}" y="{rack_top}" width="{col_w}" height="{rack_bottom - rack_top}" '
                     f'fill="url(#rackGrad)" stroke="#2e5e44" stroke-width="0.8"/>')

    # ---- Pipes with flanges (alternating staggered) ----
    for i, (pipe, x_mm) in enumerate(zip(pipes, x_positions)):
        cx = mx(x_mm)
        pipe_od = get_pipe_od(pipe['dn']) + 2 * pipe['insulation']
        flange_od = get_flange_od(pipe['dn'], pipe['rating']) or pipe_od

        # Pipe radius (display-scaled, but capped so tiny pipes are visible)
        pipe_r_px = max(pipe_od * scale / 2, 3)
        flange_r_px = max(flange_od * scale / 2, 5)

        # Stagger flanges: even-index pipes have flange on top, odd on bottom
        # (visually shown above/below the centerline)
        flange_offset = -8 if i % 2 == 0 else 8

        # Pipe (circle)
        parts.append(f'<circle cx="{cx}" cy="{pipe_y}" r="{pipe_r_px}" '
                     f'fill="url(#pipeGrad)" stroke="#7a2620" stroke-width="0.7"/>')

        # Flange disc (smaller ellipse to suggest depth, offset for staggering)
        parts.append(f'<ellipse cx="{cx}" cy="{pipe_y + flange_offset}" '
                     f'rx="{flange_r_px}" ry="{flange_r_px*0.35}" '
                     f'fill="url(#flangeGrad)" stroke="#2a3138" stroke-width="0.7" opacity="0.85"/>')

        # Pipe number label
        parts.append(f'<text x="{cx}" y="{pipe_y + flange_r_px*0.35 + 16}" '
                     f'text-anchor="middle" fill="#1d2733" font-weight="600">{i+1}</text>')
        # DN label below
        parts.append(f'<text x="{cx}" y="{pipe_y + flange_r_px*0.35 + 30}" '
                     f'text-anchor="middle" fill="#6c7a89" font-size="10">DN{pipe["dn"]} #{pipe["rating"]}</text>')

    # ---- Dimension lines for spacings (above pipes) ----
    dim_y = rack_top - 8

    def dim_line(x1, x2, label, y, color="#1d2733"):
        """Draw a dimension line with arrows and label."""
        s = []
        s.append(f'<line x1="{x1}" y1="{y}" x2="{x2}" y2="{y}" stroke="{color}" stroke-width="1"/>')
        # Tick marks
        s.append(f'<line x1="{x1}" y1="{y-4}" x2="{x1}" y2="{y+4}" stroke="{color}" stroke-width="1"/>')
        s.append(f'<line x1="{x2}" y1="{y-4}" x2="{x2}" y2="{y+4}" stroke="{color}" stroke-width="1"/>')
        # Label background + text
        cx = (x1 + x2) / 2
        s.append(f'<rect x="{cx-22}" y="{y-12}" width="44" height="14" fill="white" stroke="none"/>')
        s.append(f'<text x="{cx}" y="{y-2}" text-anchor="middle" fill="{color}" font-weight="600">{label}</text>')
        return ''.join(s)

    # Left edge offset
    parts.append(dim_line(mx(0), mx(result['left_offset']), str(result['left_offset']), dim_y))
    # Spacings
    for i, s in enumerate(result['spacings']):
        x1 = mx(x_positions[i])
        x2 = mx(x_positions[i+1])
        parts.append(dim_line(x1, x2, str(s), dim_y))
    # Right edge offset
    parts.append(dim_line(mx(x_positions[-1]), mx(inner_width), str(result['right_offset']), dim_y))

    # ---- Total dimensions (below) ----
    bot_y1 = beam_y + beam_h + 50
    bot_y2 = bot_y1 + 25
    # Inner width
    parts.append(dim_line(mx(0), mx(inner_width), f"{inner_width} mm (inner)", bot_y1, color="#9a2723"))
    # Rack width (full)
    parts.append(dim_line(mx(0), mx(rack_width), f"{rack_width} mm (rack width)", bot_y2, color="#c8332e"))

    # ---- Vertical dashed extension lines from beam to top dim line ----
    for x_mm in [0] + x_positions + [inner_width]:
        x = mx(x_mm)
        parts.append(f'<line x1="{x}" y1="{rack_top}" x2="{x}" y2="{dim_y - 6}" '
                     f'stroke="#b0bac4" stroke-width="0.5" stroke-dasharray="2,3"/>')
    # Extensions for total dims
    for x_mm in [0, inner_width, rack_width]:
        x = mx(x_mm)
        parts.append(f'<line x1="{x}" y1="{rack_bottom}" x2="{x}" y2="{bot_y2 + 6}" '
                     f'stroke="#b0bac4" stroke-width="0.5" stroke-dasharray="2,3"/>')

    parts.append('</svg>')
    return ''.join(parts)
