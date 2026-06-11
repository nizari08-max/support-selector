"""
Geometry data model for the pipe rack schematic.

``build_geometry_model()`` converts the output of ``calculate_rack()``
(rack_calculator.py) into a structured, true-scale (millimetre) description
of the rack layout. This model performs **no engineering calculations** of
its own -- every dimension value comes straight from ``calculate_rack()``.
It exists so that:

  - the SVG renderer (rack_diagram.render_svg) and any future DXF renderer
    can share the same geometry, in the same units (mm), with the same
    centerline coordinates;
  - rendering concerns (px scaling, minimum symbol sizes, label stacking)
    stay entirely out of the calculation/geometry layer.

Coordinate system: x = 0 is the rack's left outer steel edge, increasing to
the right, units = millimetres. All pipe centerlines (`cl_x`) are real
CL-to-CL positions consistent with ``result['spacings']`` and
``result['edge_offset']``.
"""

from dataclasses import dataclass, field

from pipe_flange_data import get_pipe_od, get_flange_od, rating_label


@dataclass
class PipeGeom:
    index: int
    dn: int
    rating: object
    insulation: float
    pipe_od: float
    flange_od: float
    ins_od: float
    cl_x: float        # mm - rendering centerline (may be shifted by a center spare zone)
    calc_cl_x: float    # mm - calculated centerline (matches result['spacings'] exactly)
    label_main: str
    label_spec: str
    label_ins: str = ""


@dataclass
class SpareZone:
    x1: float
    x2: float
    width: float
    label: str
    gap_index: int = -1   # pipe-pair gap the zone was inserted into; -1 = after the last pipe


@dataclass
class DimensionSpec:
    x1: float
    x2: float
    label: str
    row: int = 0
    style: str = "default"   # "default" | "total" | "spare" | "annotation"


@dataclass
class RackGeometry:
    rack_width: float
    column_width: float
    column_cl_left: float
    column_cl_right: float
    inner_total: float
    occupied_width: float
    expansion: float
    pipes: list = field(default_factory=list)
    spare_zones: list = field(default_factory=list)
    top_dimensions: list = field(default_factory=list)
    bottom_dimensions: list = field(default_factory=list)
    warnings: list = field(default_factory=list)


def _envelope_radius(pipe):
    """Outer-envelope radius (mm) of a pipe = max(pipe, flange, insulation) OD / 2."""
    pipe_od = get_pipe_od(pipe['dn'])
    flange_od = get_flange_od(pipe['dn'], pipe['rating']) or pipe_od
    ins_od = pipe_od + 2 * pipe['insulation']
    return max(pipe_od, flange_od, ins_od) / 2


def _pack_rows(dims):
    """
    Greedily assign each dimension to the lowest-numbered row such that no
    two dimensions sharing a row overlap horizontally. Mutates ``d.row``.
    """
    rows = []  # rows[r] = list of (lo, hi) spans already placed in row r
    for d in sorted(dims, key=lambda d: min(d.x1, d.x2)):
        lo, hi = sorted((d.x1, d.x2))
        for r, spans in enumerate(rows):
            if all(hi <= s0 or lo >= s1 for (s0, s1) in spans):
                spans.append((lo, hi))
                d.row = r
                break
        else:
            rows.append([(lo, hi)])
            d.row = len(rows) - 1
    return dims


def build_geometry_model(pipes, result, spare_space_location='right'):
    """
    Build a RackGeometry from pipe inputs + calculate_rack() output.

    spare_space_location:
        'right'  - spare zone placed after the last pipe, before the right
                   column (does not change any pipe centerline).
        'center' - spare zone is *inserted* into the pipe-pair gap nearest
                   the rack center; every pipe after that gap shifts right
                   by ``expansion`` mm. Falls back to 'right' for a single
                   pipe (no internal gap to insert into).
    """
    edge_offset = result['edge_offset']
    spacings = result['spacings']
    inner_total = result['inner_total']
    expansion = result['expansion']
    rack_width = result['rack_width']
    steel_column = result['steel_column']
    first_gap = result['first_gap']
    occupied_width = result['occupied_width']

    # Reference origin (x=0) is the LEFT COLUMN CENTERLINE; rack_width spans
    # column CL -> column CL exactly (see rack_calculator.calculate_rack()).
    column_cl_left = 0.0
    column_cl_right = rack_width

    # Calculated (unshifted) pipe centerlines - the true CL-to-CL chain.
    calc_cl = [edge_offset]
    for s in spacings:
        calc_cl.append(calc_cl[-1] + s)

    # ── Decide spare-zone placement (and any centerline shift it implies) ──
    spare_zones = []
    geom_warnings = []
    shift_after = -1  # pipe index after which CLs shift right by `expansion`
    if expansion > 0:
        if spare_space_location == 'center' and len(pipes) >= 2:
            # Insert the spare bay into the pipe-pair gap nearest the middle
            # of the pipe list (by index, not by geometric position):
            #   4 pipes -> between P2/P3 (gap index 1)
            #   5 pipes -> between P3/P4 (gap index 2)
            #   6 pipes -> between P3/P4 (gap index 2)
            best_i = (len(pipes) - 1) // 2
            shift_after = best_i

            # Outer-envelope radii (mm) of the two pipes flanking the chosen
            # gap, so the spare bay sits between pipe envelopes (not CLs)
            # with balanced clearance on either side.
            r_left = _envelope_radius(pipes[best_i])
            r_right = _envelope_radius(pipes[best_i + 1])

            # The gap available to the spare bay, once everything after it
            # has shifted right by `expansion`, runs from this gap's start to
            # its (shifted) end.
            full_lo = calc_cl[best_i]
            full_hi = calc_cl[best_i + 1] + expansion

            env_lo = full_lo + r_left    # right edge of left pipe's envelope
            env_hi = full_hi - r_right   # left edge of right pipe's envelope
            available = env_hi - env_lo

            # Center the spare bay between the two envelopes, giving equal
            # clearance on each side (clearance may be negative if the
            # envelopes themselves leave less room than `expansion` -
            # in that case the unavoidable overlap is at least symmetric).
            leftover = available - expansion
            spare_x1 = env_lo + leftover / 2
            spare_x2 = spare_x1 + expansion

            if leftover < 0:
                geom_warnings.append(
                    "Future spare space could not maintain full clearance "
                    "from adjacent pipe envelopes in this gap; spacing may "
                    "be tight."
                )

            # Round to whole millimetres so flanking dimension splits stay
            # integer-consistent with their labels, then clamp into the gap.
            spare_x1 = min(max(round(spare_x1), full_lo), full_hi - expansion)
            spare_x2 = spare_x1 + expansion
            spare_zones.append(SpareZone(
                x1=spare_x1, x2=spare_x2, width=expansion,
                label=f"Future spare space = {expansion} mm", gap_index=best_i,
            ))
        else:
            # 'right' (default), or 'center' with a single pipe -> fall back to right.
            spare_x1 = inner_total
            spare_x2 = inner_total + expansion
            spare_zones.append(SpareZone(
                x1=spare_x1, x2=spare_x2, width=expansion,
                label=f"Future spare space = {expansion} mm", gap_index=-1,
            ))

    def render_x(calc_x, pipe_i):
        if shift_after >= 0 and pipe_i > shift_after:
            return calc_x + expansion
        return calc_x

    # ── Pipe geometry ────────────────────────────────────────────────────
    pipe_geoms = []
    for i, (pipe, calc_x) in enumerate(zip(pipes, calc_cl)):
        pipe_od = get_pipe_od(pipe['dn'])
        flange_od = get_flange_od(pipe['dn'], pipe['rating']) or pipe_od
        ins = pipe['insulation']
        ins_od = pipe_od + 2 * ins
        spec = (
            f"DN{pipe['dn']} "
            f"{rating_label(pipe['rating']).replace('Class ', '#').replace(' (Series ', '-S').replace(')', '')}"
        )
        pipe_geoms.append(PipeGeom(
            index=i,
            dn=pipe['dn'],
            rating=pipe['rating'],
            insulation=ins,
            pipe_od=pipe_od,
            flange_od=flange_od,
            ins_od=ins_od,
            cl_x=render_x(calc_x, i),
            calc_cl_x=calc_x,
            label_main=f"P{i + 1}",
            label_spec=spec,
            label_ins=f"Ins {ins} mm" if ins else "",
        ))

    # ── Top dimensions: column CL -> pipe1 CL, then CL-to-CL spacings ──────
    top_dims = [
        DimensionSpec(
            x1=column_cl_left, x2=pipe_geoms[0].cl_x,
            label=f"{first_gap} CL-CL",
        )
    ]
    for i, s in enumerate(spacings):
        p_a, p_b = pipe_geoms[i], pipe_geoms[i + 1]
        if shift_after == i:
            # The pipe-pair gap now contains the spare bay. Split the
            # original CL-CL spacing into the portions that flank the bay
            # on either side; their sum still equals `s`.
            zone = spare_zones[0]
            left_part = zone.x1 - p_a.cl_x
            right_part = p_b.cl_x - zone.x2
            if left_part > 0:
                top_dims.append(DimensionSpec(x1=p_a.cl_x, x2=zone.x1, label=str(int(round(left_part)))))
            if right_part > 0:
                top_dims.append(DimensionSpec(x1=zone.x2, x2=p_b.cl_x, label=str(int(round(right_part)))))
        else:
            top_dims.append(DimensionSpec(x1=p_a.cl_x, x2=p_b.cl_x, label=str(s)))
    _pack_rows(top_dims)

    # ── Bottom dimensions: occupied width, rack width CL-CL, spare space ──
    bottom_dims = [
        DimensionSpec(
            x1=column_cl_left, x2=column_cl_right,
            label=f"Occupied Width = {occupied_width} mm", row=0, style="annotation",
        ),
        DimensionSpec(
            x1=column_cl_left, x2=column_cl_right,
            label=f"{rack_width} mm rack width CL-CL", row=1, style="total",
        ),
    ]
    for zone in spare_zones:
        bottom_dims.append(DimensionSpec(x1=zone.x1, x2=zone.x2, label=zone.label, row=2, style="spare"))

    return RackGeometry(
        rack_width=rack_width,
        column_width=steel_column,
        column_cl_left=column_cl_left,
        column_cl_right=column_cl_right,
        inner_total=inner_total,
        occupied_width=occupied_width,
        expansion=expansion,
        pipes=pipe_geoms,
        spare_zones=spare_zones,
        top_dimensions=top_dims,
        bottom_dimensions=bottom_dims,
        warnings=geom_warnings + list(result.get('warnings', [])),
    )
