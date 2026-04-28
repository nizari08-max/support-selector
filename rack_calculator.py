"""
Pipe spacing and rack width calculator.

Implements the rules visible in the reference Excel calculator
(by Boutrih Boujemaa, April 2024 Rev. 1):

  - Pipe data: ASME B36.10M-2000
  - Flanges DN 15-600: ASME B16.5-2009
  - Flanges DN 650-1000: ASME B16.47-2017
  - Max 16 pipes per tier
  - Pipe expansion effects NOT included
  - Minimum center-to-center spacing rules:
        DN <= 200 -> minimum 250 mm
        DN  > 200 -> minimum 350 mm
  - Edge-of-rack to first pipe centerline: 50 mm minimum (rack edge clearance)
  - Pipe expansion margin on total width: 20%
  - Spacings rounded to nearest 5 mm (Excel-style)

Spacing rule (reverse-engineered from reference Excel, validated 6/6 match):
  Adjacent flanges are assumed to be STAGGERED (alternating up-of-beam /
  down-of-beam at supports), so a larger flange does not clash with the
  smaller adjacent pipe at the support point - only with that pipe's bare
  body. The center-to-center spacing is therefore:

        spacing = max(flange_A, flange_B) / 2
                + min(pipe_A,   pipe_B  ) / 2
                + clearance_gap

  where flange/pipe values include 2x insulation thickness when applicable.
"""

import math
from pipe_flange_data import get_pipe_od, get_flange_od


# -----------------------------------------------------------------------------
# Configuration constants (matching the reference Excel)
# -----------------------------------------------------------------------------
EDGE_CLEARANCE_MM = 50          # Distance from rack edge to first pipe centerline
EXPANSION_MARGIN_PCT = 20       # % added to total width for expansion / future pipes
ROUND_TO_MM = 5                 # Round all spacings to nearest 5 mm
MAX_PIPES_PER_TIER = 16         # Maximum pipes allowed per tier
PAIR_CLEARANCE_MM = 50          # Clearance between staggered envelopes


def round_to_5(value):
    """Round a value to the nearest 5 mm (Excel-style)."""
    return int(round(value / ROUND_TO_MM) * ROUND_TO_MM)


def round_up_to_5(value):
    """Round a value UP to the nearest 5 mm (used for safety-critical totals)."""
    return int(math.ceil(value / ROUND_TO_MM) * ROUND_TO_MM)


def get_pipe_envelope(dn, insulation_mm):
    """Insulated pipe OD = pipe_OD + 2 * insulation."""
    return get_pipe_od(dn) + 2 * insulation_mm


def get_flange_envelope(dn, rating, insulation_mm):
    """
    Flange envelope OD. Flange OD is typically larger than insulated pipe,
    but if heavy insulation exceeds the flange OD, that governs instead.

    Raises ValueError if the DN/rating combination is not standardized.
    """
    flange_od = get_flange_od(dn, rating)
    if flange_od is None:
        raise ValueError(
            f"Flange size for DN{dn} Class #{rating} is not standardized. "
            f"Please choose a different rating."
        )
    insulated_od = get_pipe_envelope(dn, insulation_mm)
    return max(flange_od, insulated_od)


def minimum_center_spacing(dn_a, dn_b):
    """
    Minimum center-to-center spacing rule (visible note in reference Excel):
      DN <= 200  -> 250 mm
      DN  > 200  -> 350 mm
    """
    governing_dn = max(dn_a, dn_b)
    return 250 if governing_dn <= 200 else 350


def calculate_pair_spacing(pipe_a, pipe_b):
    """
    Calculate center-to-center spacing between two adjacent pipes,
    using the staggered-flange rule (validated against reference Excel).

    pipe_a, pipe_b are dicts with keys: 'dn', 'rating', 'insulation'.
    Returns spacing in mm, rounded to nearest 5 mm,
    respecting the DN-based minimum.
    """
    flange_a = get_flange_envelope(pipe_a['dn'], pipe_a['rating'], pipe_a['insulation'])
    flange_b = get_flange_envelope(pipe_b['dn'], pipe_b['rating'], pipe_b['insulation'])
    pipe_env_a = get_pipe_envelope(pipe_a['dn'], pipe_a['insulation'])
    pipe_env_b = get_pipe_envelope(pipe_b['dn'], pipe_b['insulation'])

    # Staggered flange model: larger flange clears the smaller pipe's bare body
    raw_spacing = max(flange_a, flange_b) / 2 + min(pipe_env_a, pipe_env_b) / 2 + PAIR_CLEARANCE_MM

    # Apply DN-based minimum
    min_spacing = minimum_center_spacing(pipe_a['dn'], pipe_b['dn'])
    spacing = max(raw_spacing, min_spacing)

    return round_to_5(spacing)


def calculate_edge_offset(pipe):
    """
    Distance from the rack steel edge to the first/last pipe centerline.

    Must clear half the flange envelope (so flange doesn't hit rack steel)
    plus the EDGE_CLEARANCE_MM minimum. Rounded UP to nearest 5 mm
    (always conservative on the boundary).
    """
    flange = get_flange_envelope(pipe['dn'], pipe['rating'], pipe['insulation'])
    raw = flange / 2 + EDGE_CLEARANCE_MM
    return round_up_to_5(raw)


def calculate_rack(pipes, expansion_pct=EXPANSION_MARGIN_PCT, steel_column_mm=190):
    """
    Main entry point.

    Args:
        pipes: list of dicts, each with keys 'dn', 'rating', 'insulation'.
               Order matters - this is the left-to-right order on the rack.
        expansion_pct: % to add for future expansion / spare pipes (default 20%).
        steel_column_mm: half-width of the rack support steel column at each
                         end, added to total (default 190 mm, matching the
                         reference Excel). Set to 0 for centerline-only width.

    Returns:
        dict with full breakdown of the calculation.
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

    # Edge offsets (rack steel edge to first/last pipe centerline)
    left_offset = calculate_edge_offset(pipes[0])
    right_offset = calculate_edge_offset(pipes[-1])

    # Build totals
    pipe_run = sum(spacings)
    total_width = left_offset + pipe_run + right_offset
    expansion = round_up_to_5(total_width * expansion_pct / 100)
    rack_width = total_width + expansion + steel_column_mm

    # Sanity warnings
    if len(pipes) >= MAX_PIPES_PER_TIER:
        warnings.append(
            f"At maximum capacity ({MAX_PIPES_PER_TIER} pipes per tier)."
        )

    return {
        'spacings': spacings,
        'left_offset': left_offset,
        'right_offset': right_offset,
        'pipe_run': pipe_run,
        'total_width': total_width,
        'expansion': expansion,
        'rack_width': rack_width,
        'warnings': warnings,
    }
