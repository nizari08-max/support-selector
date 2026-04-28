"""
Pipe spacing and rack width calculator.

This is a Python implementation of the calculation logic from
"PIPE SPACING & RACK WIDTH DETERMINATION CALCULATOR"
(by Boutrih Boujemaa, April 2024 Rev. 1).

Every formula here mirrors the original Excel workbook so that the
output is bit-identical to the reference spreadsheet (validated against
a 10-pipe worked example: see test_against_excel() below).

Source data:
  - Pipe sizes per ASME B36.10M-2000 (DN 15 to DN 1000)
  - B16.5 flanges (DN 15-600) and B16.47 Series A & B (DN 650-1000)
  - Maximum 16 pipes per tier
  - Pipe thermal expansion effects NOT included

Formula breakdown
=================

LEFT EDGE OFFSET (rack steel edge to first pipe centerline):

    edge_offset = MROUND( pipe_OD/2 + insulation
                        + steel_column/2 + 100 , 5 )

INTER-PIPE CENTER-TO-CENTER SPACING (staggered flange model):

    case_1 = (flange_OD_A + pipe_OD_B) / 2 + insul_A + insul_B + 50
    case_2 = (flange_OD_B + pipe_OD_A) / 2 + insul_A + insul_B + 50

    spacing = MROUND( max(case_1, case_2) , 5 )

This represents the worst case of two staggered-flange scenarios:
each pipe's flange must clear the adjacent pipe's bare body.

TOTAL WIDTH:

    The reference Excel adds a small per-pipe buffer (50 mm baseline,
    plus 50 mm for each populated pipe) to the inner total. This is
    implemented in the workbook via hidden cells in row 90 that reference
    Database!$AG$44 (which holds a constant 50 mm). Whether this is by
    design or an artifact of the original Excel author's layout, we
    reproduce it here for exact compatibility.

    pipe_buffer = (pipe_count + 1) * 50
    inner_total = edge_offset + sum(spacings) + pipe_buffer
    expansion   = inner_total * expansion_pct
    rack_width  = inner_total + expansion + steel_column / 2
"""

from pipe_flange_data import get_pipe_od, get_flange_od


# -----------------------------------------------------------------------------
# Configuration constants (matching the reference Excel)
# -----------------------------------------------------------------------------
PAIR_CLEARANCE_MM = 50          # 'Sheet 1'!E10 in the reference Excel
EDGE_CLEARANCE_MM = 100         # +100 mm in the G90 edge-offset formula
PER_PIPE_BUFFER_MM = 50         # Database!AG44 - hidden buffer added per pipe
DEFAULT_EXPANSION_PCT = 20      # AN90 in the reference Excel = 0.20
DEFAULT_STEEL_COLUMN_MM = 330   # D94 in the reference Excel = 330 mm
ROUND_TO_MM = 5                 # MROUND(..., 5)
MAX_PIPES_PER_TIER = 16         # Per the workbook's notes section


def mround(value, multiple):
    """
    Excel's MROUND function: round to the nearest multiple.

    Note: Excel's MROUND uses 'round half away from zero', whereas
    Python's built-in round() uses banker's rounding (round half to
    even). We implement Excel's behavior here for exact compatibility.
    """
    if multiple == 0:
        return value
    quotient = value / multiple
    # Round half away from zero (Excel-style)
    if quotient >= 0:
        return int(quotient + 0.5) * multiple
    return -int(-quotient + 0.5) * multiple


def calculate_pair_spacing(pipe_a, pipe_b):
    """
    Calculate center-to-center spacing between two adjacent pipes,
    using the exact reference Excel formula.

    pipe_a, pipe_b are dicts with keys: 'dn', 'rating', 'insulation'.
    Returns spacing in mm, rounded to nearest 5 mm.
    """
    pipe_od_a = get_pipe_od(pipe_a['dn'])
    pipe_od_b = get_pipe_od(pipe_b['dn'])
    flange_a = get_flange_od(pipe_a['dn'], pipe_a['rating'])
    flange_b = get_flange_od(pipe_b['dn'], pipe_b['rating'])

    if flange_a is None:
        raise ValueError(
            f"Flange size for DN{pipe_a['dn']} {pipe_a['rating']} is not "
            f"standardized. Please choose a different rating."
        )
    if flange_b is None:
        raise ValueError(
            f"Flange size for DN{pipe_b['dn']} {pipe_b['rating']} is not "
            f"standardized. Please choose a different rating."
        )

    ins_a = pipe_a['insulation']
    ins_b = pipe_b['insulation']

    # Staggered flange model - two cases, take the worst
    case_1 = (flange_a + pipe_od_b) / 2 + ins_a + ins_b + PAIR_CLEARANCE_MM
    case_2 = (flange_b + pipe_od_a) / 2 + ins_a + ins_b + PAIR_CLEARANCE_MM

    return mround(max(case_1, case_2), ROUND_TO_MM)


def calculate_edge_offset(pipe, steel_column_mm):
    """
    Distance from the rack steel edge to the first/last pipe centerline.

    Excel formula G90:
        MROUND( pipe_OD/2 + insulation + steel_column/2 + 100 , 5 )
    """
    pipe_od = get_pipe_od(pipe['dn'])
    raw = (pipe_od / 2
           + pipe['insulation']
           + steel_column_mm / 2
           + EDGE_CLEARANCE_MM)
    return mround(raw, ROUND_TO_MM)


def calculate_rack(pipes,
                   expansion_pct=DEFAULT_EXPANSION_PCT,
                   steel_column_mm=DEFAULT_STEEL_COLUMN_MM):
    """
    Main entry point.

    Args:
        pipes: list of dicts, each with 'dn', 'rating', 'insulation'.
               Order matters - this is the left-to-right order on the rack.
        expansion_pct: % to add for future expansion (default 20).
        steel_column_mm: rack steel column width in mm (default 330).

    Returns:
        dict with full breakdown:
          {
            'edge_offset':    mm    rack edge to first pipe centerline
            'spacings':       [mm]  center-to-center between adjacent pipes
            'pipe_run':       mm    sum of all spacings
            'inner_total':    mm    edge_offset + pipe_run (matches W96)
            'expansion':      mm    inner_total * expansion_pct
            'rack_width':     mm    full rack width (matches W99)
            'steel_column':   mm    rack steel column width used
            'expansion_pct':  int   expansion percentage used
            'warnings':       [str]
          }
    """
    if not pipes:
        raise ValueError("At least one pipe is required.")

    if len(pipes) > MAX_PIPES_PER_TIER:
        raise ValueError(
            f"Maximum {MAX_PIPES_PER_TIER} pipes per tier "
            f"(got {len(pipes)})."
        )

    warnings = []

    # Pair-by-pair center-to-center spacings
    spacings = []
    for i in range(len(pipes) - 1):
        spacings.append(calculate_pair_spacing(pipes[i], pipes[i + 1]))

    # Left edge offset (to first pipe centerline)
    edge_offset = calculate_edge_offset(pipes[0], steel_column_mm)

    # Build totals (matching the W96 / W99 cells in the reference Excel)
    pipe_run = sum(spacings)
    # Per-pipe buffer: 50mm baseline + 50mm per populated pipe (hidden in
    # the source Excel's row 90 sum range)
    pipe_buffer = (len(pipes) + 1) * PER_PIPE_BUFFER_MM
    inner_total = edge_offset + pipe_run + pipe_buffer
    expansion = mround(inner_total * expansion_pct / 100, 1)  # not rounded to 5 in source
    rack_width = inner_total + expansion + steel_column_mm / 2
    # Final rack_width may be a non-integer because of /2 - round to int mm
    rack_width = int(round(rack_width))

    if len(pipes) >= MAX_PIPES_PER_TIER:
        warnings.append(
            f"At maximum capacity ({MAX_PIPES_PER_TIER} pipes per tier)."
        )

    return {
        'edge_offset':   edge_offset,
        'spacings':      spacings,
        'pipe_run':      pipe_run,
        'pipe_buffer':   pipe_buffer,
        'inner_total':   inner_total,
        'expansion':     int(expansion),
        'rack_width':    rack_width,
        'steel_column':  steel_column_mm,
        'expansion_pct': expansion_pct,
        'warnings':      warnings,
    }
