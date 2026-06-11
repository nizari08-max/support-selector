# =============================================================================
# selector.py
# Core Selection Logic — Piping Support Selector
# =============================================================================

from support_rules import SUPPORT_RULES, NOTES
from drawing_index import get_drawings, label_drawings
from note_refinement import apply_refinements


WL_WARNING = (
    "Use only when specified on stress isometrics or approved by stress engineer. "
    "Local stress checks may be required."
)


# =============================================================================
# STEP 1 — NPS to size range key
# Table 15 (rest) and Table 16 (guide/line_stop/hold_down) use different ranges.
# =============================================================================

def get_size_range(nps: float, function_key: str) -> str:
    """
    Convert NPS to the size-range key used in SUPPORT_RULES.

    Table 15 ranges (rest):
        0.5_to_1 | 1.5 | 2_to_16 | 18_to_24 | 26_to_30 | 32_to_48

    Table 16 ranges (guide / line_stop / hold_down):
        0.5_to_1 | 1.5_to_6 | 8_to_10 | 12_to_48
    """
    if nps < 0.5:
        raise ValueError(f"NPS {nps}\" is below the minimum supported size (1/2\").")
    if nps > 48:
        raise ValueError(f"NPS {nps}\" is above the maximum supported size (48\").")

    if function_key == "rest":
        # Table 15 breakpoints
        if nps <= 1.0:    return "0.5_to_1"
        elif nps <= 1.5:  return "1.5"
        elif nps <= 16.0: return "2_to_16"
        elif nps <= 24.0: return "18_to_24"
        elif nps <= 30.0: return "26_to_30"
        else:             return "32_to_48"
    else:
        # Table 16 breakpoints (guide / line_stop / hold_down)
        if nps <= 1.0:    return "0.5_to_1"
        elif nps <= 6.0:  return "1.5_to_6"
        elif nps <= 10.0: return "8_to_10"
        else:             return "12_to_48"


# =============================================================================
# STEP 2 — Material class normalizer
# =============================================================================

MATERIAL_ALIASES = {
    # CS / LT / Internally Cladded
    "cs":                 "cs_lt",
    "lt":                 "cs_lt",
    "cs/lt":              "cs_lt",
    "cs_lt":              "cs_lt",
    "cladded":            "cs_lt",
    "internally cladded": "cs_lt",

    # SS / DS / SD / SA
    "ss":          "ss_ds_sd_sa",
    "ds":          "ss_ds_sd_sa",
    "sd":          "ss_ds_sd_sa",
    "sa":          "ss_ds_sd_sa",
    "ss/ds":       "ss_ds_sd_sa",
    "ss_ds_sd_sa": "ss_ds_sd_sa",

    # AL / AY / CN
    "al":        "al_ay_cn",
    "ay":        "al_ay_cn",
    "cn":        "al_ay_cn",
    "al/ay":     "al_ay_cn",
    "al_ay_cn":  "al_ay_cn",
    "aluminum":  "al_ay_cn",
    "aluminium": "al_ay_cn",

    # FRP
    "frp":        "frp",
    "fiberglass": "frp",
    "grp":        "frp",
}


def normalize_material(raw_material: str) -> str:
    key = raw_material.strip().lower()
    if key in MATERIAL_ALIASES:
        return MATERIAL_ALIASES[key]
    key_stripped = key.replace(" ", "").replace("/", "_")
    if key_stripped in MATERIAL_ALIASES:
        return MATERIAL_ALIASES[key_stripped]
    raise ValueError(
        f"Unknown material class: '{raw_material}'.\n"
        f"Accepted values: CS, LT, SS, DS, SD, SA, AL, AY, CN, FRP."
    )


# =============================================================================
# STEP 3 — Insulation condition normalizer
# =============================================================================

def normalize_insulation(raw_insulation: str) -> str:
    val = raw_insulation.strip().lower()
    if val in ("uninsulated", "bare", "no insulation", "none", "u"):
        return "uninsulated"
    elif val in ("hot_insulated", "hot insulated", "insulated", "hot", "hi", "h"):
        return "hot_insulated"
    else:
        raise ValueError(
            f"Unknown insulation condition: '{raw_insulation}'.\n"
            f"Accepted values: 'uninsulated' or 'hot_insulated'."
        )


# =============================================================================
# STEP 4 — Support function normalizer
# =============================================================================

def normalize_function(raw_function: str) -> str:
    val = raw_function.strip().lower().replace(" ", "_").replace("-", "_")
    if val in ("rest", "r"):
        return "rest"
    elif val in ("guide", "g"):
        return "guide"
    elif val in ("line_stop", "ls", "linestop"):
        return "line_stop"
    elif val in ("hold_down", "hd", "holddown"):
        return "hold_down"
    else:
        raise ValueError(
            f"Unknown support function: '{raw_function}'.\n"
            f"Accepted values: rest, guide, line_stop, hold_down."
        )


def normalize_pipe_orientation(raw_orientation: str | None) -> str:
    val = (raw_orientation or "horizontal").strip().lower()
    if val in ("horizontal", "h"):
        return "horizontal"
    if val in ("vertical", "v"):
        return "vertical"
    raise ValueError(
        f"Unknown pipe orientation: '{raw_orientation}'.\n"
        f"Accepted values: horizontal or vertical."
    )


def normalize_vertical_restraint(raw_restraint: str | None) -> str:
    val = (raw_restraint or "").strip().lower().replace(" ", "_").replace("-", "_")
    if val in ("sliding", "shear", "slide", "sliding_shear"):
        return "sliding"
    if val in ("fixed", "fix"):
        return "fixed"
    raise ValueError(
        f"Unknown vertical restraint type: '{raw_restraint}'.\n"
        f"Accepted values: sliding or fixed."
    )


def normalize_frp_vertical_support(raw_support: str | None, function_key: str) -> str:
    val = (raw_support or "").strip().lower().replace(" ", "_").replace("-", "_").replace("+", "_")
    val = "_".join(part for part in val.split("_") if part)
    if val in ("rest", "riser_clamp_rest", "rc71"):
        return "rest"
    if val in (
        "rest_guide_hold_down",
        "rest_guide_holddown",
        "rest_guide_hold",
        "riser_clamp_rest_guide_hold_down",
        "rc72",
    ):
        return "rest_guide_hold_down"
    if val in ("all_around_guide", "guide", "riser_clamp_all_around_guide", "rc73"):
        return "all_around_guide"

    if raw_support is None:
        if function_key == "rest":
            return "rest"
        if function_key == "guide":
            return "all_around_guide"
        if function_key == "hold_down":
            return "rest_guide_hold_down"

    raise ValueError(
        f"Unknown FRP vertical support type: '{raw_support}'.\n"
        f"Accepted values: rest, rest_guide_hold_down, all_around_guide."
    )


# =============================================================================
# STEP 5 — Result data class
# =============================================================================

class SelectionResult:
    """
    Holds the output of a support selection.

    support_code = None   →  not applicable for this combination
    support_code = string →  selected support description
    """

    def __init__(
        self,
        support_code,
        drawings,
        notes,
        size_range,
        inputs,
        status="complete",
        refinement_questions=None,
        applied_refinements=None,
        refinement_warnings=None,
    ):
        self.support_code     = support_code
        self.drawings         = drawings
        self.drawings_labeled = label_drawings(drawings)
        self.notes            = notes
        self.note_texts   = [NOTES[n] for n in notes if n in NOTES]
        self.size_range   = size_range
        self.inputs       = inputs
        self.status       = status
        self.refinement_questions = refinement_questions or []
        self.applied_refinements  = applied_refinements or []
        self.refinement_warnings  = refinement_warnings or []

    def is_applicable(self) -> bool:
        return self.support_code is not None

    def __str__(self) -> str:
        lines = [
            "",
            "=" * 65,
            "  PIPING SUPPORT SELECTION RESULT",
            "=" * 65,
            f"  Pipe Size (NPS)      : {self.inputs.get('nps', '?')}\"",
            f"  Material Class       : {self.inputs.get('material', '?')}",
            f"  PWHT Required        : {'Yes' if self.inputs.get('pwht') else 'No'}",
            f"  Insulation           : {self.inputs.get('insulation', '?')}",
            f"  Support Function     : {self.inputs.get('function', '?')}",
            "-" * 65,
        ]

        if self.is_applicable():
            lines.append(f"  SELECTED SUPPORT     : {self.support_code}")
            if self.drawings:
                lines.append("  DRAWING REFERENCE(S) :")
                for dwg in self.drawings:
                    lines.append(f"      - {dwg}")

            if self.note_texts:
                lines.append("")
                lines.append("  APPLICABLE NOTES:")
                for text in self.note_texts:
                    # Wrap long note text at 60 chars
                    lines.append(f"      {text}")
        else:
            lines.append(
                "  RESULT               : Not applicable for this combination.\n"
                "                         No support type assigned in Tables 15/16."
            )

        lines.append("=" * 65)
        return "\n".join(lines)


# =============================================================================
# STEP 6 — Flange support routing
# Applies only when function=REST and is_flange=True.
# =============================================================================

# Flange Frame: pressure class → (support code, min_nps, max_nps)
_FLANGE_FRAME = {
    150:  ("FF01", 1.0,  24.0),
    300:  ("FF02", 1.0,  24.0),
    600:  ("FF03", 2.0,  16.0),
    900:  ("FF04", 2.0,  16.0),
    1500: ("FF05", 2.0,  16.0),
    2500: ("FF06", 2.0,  12.0),
}


def _select_flange_support(
    nps, material_key, flange_class, size_range, inputs, refinements
) -> SelectionResult:
    # FRP (pipe or valve flange) → FF71 (1"–18")
    if material_key == "frp":
        if 1.0 <= nps <= 18.0:
            return _build_result("FLANGED VALVE HOLDER (FF71)", [], size_range, inputs, refinements)
        return SelectionResult(
            support_code=None, drawings=[], notes=[],
            size_range=size_range, inputs=inputs,
        )

    # Metallic materials → FF01–FF06 by pressure class
    try:
        cls = int(flange_class)
    except (TypeError, ValueError):
        raise ValueError(
            f"Pressure class is required for flange support. "
            f"Expected 150, 300, 600, 900, 1500, or 2500. Got: {flange_class!r}"
        )

    if cls not in _FLANGE_FRAME:
        raise ValueError(
            f"Unknown flange pressure class: {cls}. "
            f"Must be one of 150, 300, 600, 900, 1500, 2500."
        )

    code, min_nps, max_nps = _FLANGE_FRAME[cls]
    if not (min_nps <= nps <= max_nps):
        return SelectionResult(
            support_code=None, drawings=[], notes=[],
            size_range=size_range, inputs=inputs,
        )

    return _build_result(f"FLANGE FRAME ({code})", [], size_range, inputs, refinements)


def _select_vertical_lug_support(
    nps, material_key, insulation_key, vertical_restraint, size_range, inputs
) -> SelectionResult:
    if material_key == "frp":
        return SelectionResult(
            support_code=None,
            drawings=[],
            notes=[],
            size_range=size_range,
            inputs=inputs,
            refinement_warnings=[
                "FRP piping is not applicable for WL03-WL06 vertical pipe lug supports."
            ],
        )

    if not (1.0 <= nps <= 24.0):
        return SelectionResult(
            support_code=None,
            drawings=[],
            notes=[],
            size_range=size_range,
            inputs=inputs,
            refinement_warnings=[
                "WL03-WL06 vertical pipe lug supports are applicable from NPS 1\" to NPS 24\" only."
            ],
        )

    restraint_key = normalize_vertical_restraint(vertical_restraint)
    lookup = {
        ("uninsulated", "sliding"): "SHEAR LUG - SLIDING FOR VERTICAL BARE PIPE (WL03)",
        ("uninsulated", "fixed"): "FIXED LUG - FOR VERTICAL BARE PIPE (WL04)",
        ("hot_insulated", "sliding"): "SHEAR LUG - SLIDING FOR VERTICAL INSULATED PIPE (WL05)",
        ("hot_insulated", "fixed"): "FIXED LUG - FOR VERTICAL INSULATED PIPE (WL06)",
    }
    support_code = lookup[(insulation_key, restraint_key)]

    return SelectionResult(
        support_code=support_code,
        drawings=get_drawings(support_code, nps=nps),
        notes=[],
        size_range=size_range,
        inputs=inputs,
        refinement_warnings=[WL_WARNING],
    )


def _select_frp_vertical_support(
    nps, function_key, frp_vertical_support, size_range, inputs
) -> SelectionResult:
    if not (0.75 <= nps <= 80.0):
        return SelectionResult(
            support_code=None,
            drawings=[],
            notes=[],
            size_range=size_range,
            inputs=inputs,
            refinement_warnings=[
                "RC71-RC73 FRP riser clamp supports are applicable from NPS 3/4\" to NPS 80\" only."
            ],
        )

    if 4.0 < nps < 6.0 or 10.0 < nps < 12.0:
        return SelectionResult(
            support_code=None,
            drawings=[],
            notes=[],
            size_range=size_range,
            inputs=inputs,
            refinement_warnings=[
                "Selected NPS is not covered by the RC71-RC73 drawing size bands."
            ],
        )

    support_key = normalize_frp_vertical_support(frp_vertical_support, function_key)
    lookup = {
        "rest": "PIPE SUPPORT RISER CLAMP REST FOR FRP PIPING (RC71)",
        "rest_guide_hold_down": "PIPE SUPPORT RISER CLAMP REST + GUIDE + HOLD DOWN FOR FRP PIPING (RC72)",
        "all_around_guide": "PIPE SUPPORT RISER CLAMP ALL AROUND GUIDE FOR FRP PIPING (RC73)",
    }
    support_code = lookup[support_key]

    return SelectionResult(
        support_code=support_code,
        drawings=get_drawings(support_code, nps=nps),
        notes=[],
        size_range=size_range,
        inputs=inputs,
    )


# =============================================================================
# STEP 7 — Main selection function
# =============================================================================

def select_support(
    nps: float,
    material: str,
    pwht: bool,
    insulation: str,
    support_function: str,
    refinements: dict = None,
    is_flange: bool = False,
    flange_class=None,
    pipe_orientation: str = "horizontal",
    vertical_restraint: str = None,
    frp_vertical_support: str = None,
) -> SelectionResult:
    """
    Select the appropriate piping support based on pipe and project conditions.

    Args:
        nps              : Nominal pipe size as a decimal (0.5 … 48)
        material         : Material class string (e.g. "CS", "SS", "FRP")
        pwht             : True if PWHT is required (only relevant for CS/LT)
        insulation       : "uninsulated" or "hot_insulated"
        support_function : "rest", "guide", "line_stop", or "hold_down"
        refinements      : optional answers to active engineering-note questions
        is_flange        : True when the support is located at a flange (REST only)
        flange_class     : ASME pressure class int (150/300/600/900/1500/2500);
                           required for metallic materials; ignored for FRP (→ FF71)

    Returns:
        SelectionResult with the selected support, drawings, and notes.
    """
    # --- Normalize inputs ---
    function_key   = normalize_function(support_function)
    material_key   = normalize_material(material)
    insulation_key = normalize_insulation(insulation)
    orientation_key = normalize_pipe_orientation(pipe_orientation)
    size_range     = "vertical" if orientation_key == "vertical" else get_size_range(nps, function_key)

    inputs = {
        "nps":          nps,
        "material":     material_key,
        "pwht":         pwht,
        "insulation":   insulation_key,
        "function":     function_key,
        "is_flange":    is_flange,
        "flange_class": flange_class,
        "pipe_orientation": orientation_key,
        "vertical_restraint": vertical_restraint,
        "frp_vertical_support": frp_vertical_support,
    }

    # -----------------------------------------------------------------------
    # Vertical pipe lug branch - WL03 to WL06 only.
    # This dedicated path bypasses the normal horizontal support tables.
    # -----------------------------------------------------------------------
    if orientation_key == "vertical":
        if material_key == "frp":
            return _select_frp_vertical_support(
                nps, function_key, frp_vertical_support, size_range, inputs
            )
        return _select_vertical_lug_support(
            nps, material_key, insulation_key, vertical_restraint, size_range, inputs
        )

    # -----------------------------------------------------------------------
    # Flange REST branch — short-circuits standard rules and FRP saddle path.
    # Only active when function=REST and the engineer flags a flange location.
    # Non-REST functions (guide / line_stop / hold_down) ignore is_flange.
    # FRP → FF71 regardless of component type (pipe or valve flange).
    # Metallic → FF01–FF06 selected by ASME pressure class.
    # -----------------------------------------------------------------------
    if function_key == "rest" and is_flange:
        return _select_flange_support(
            nps, material_key, flange_class,
            size_range, inputs, refinements,
        )

    # -----------------------------------------------------------------------
    # FRP special case — handled entirely here for all support functions.
    #
    # New standard rules (JESA Rev A update):
    #   REST      : SC71 (3/4"–68") primary; SC72 (3/4"–52") as alternative
    #   GUIDE     : SC73 (3/4"–52") for all sizes
    #   LINE STOP : No FRP-specific type — use CF03 with engineering note
    #   HOLD DOWN : Not applicable
    #
    # Sizes below NPS 3/4" are not covered by any FRP support type.
    # -----------------------------------------------------------------------
    if material_key == "frp":
        # NPS 1/2" (0.5) is below the minimum FRP support size (3/4")
        if nps < 0.75:
            return SelectionResult(
                support_code=None,
                drawings=[],
                notes=[],
                size_range=size_range,
                inputs=inputs,
            )

        if function_key == "rest":
            # SC71 covers 3/4"–68" (all tool sizes); SC72 also available up to 52"
            # Both cover the full tool range (max 48" < 52"), except NPS 26" where
            # SC72 sub-ranges jump from 16"-24" directly to 28"-52".
            if nps == 26.0:
                # NPS 26" falls between SC72 sub-ranges — SC71 only
                code = "SADDLE SUPPORT (SC71)"
            else:
                # All other sizes: SC71 primary, SC72 as alternative
                code = "SADDLE SUPPORT (SC71)  OR  SC72 (alternative)"
            return _build_result(code, [], size_range, inputs, refinements)

        elif function_key == "guide":
            # SC73 covers 3/4"–52" (all tool sizes up to 48")
            # Sub-range gap: 25"-27" — NPS 26" falls between 16"-24" and 28"-52"
            if nps == 26.0:
                return SelectionResult(
                    support_code=None,
                    drawings=[],
                    notes=[],
                    size_range=size_range,
                    inputs=inputs,
                )
            code = "SADDLE GUIDE SUPPORT (SC73)"
            return _build_result(code, [], size_range, inputs, refinements)

        elif function_key == "line_stop":
            # No dedicated FRP line stop in the standard.
            # CF03 (FRP Clamp Shoe for Guide) is used as the nearest alternative.
            # Note 6 explains the deviation to the engineer.
            code = "CF03"
            return _build_result(code, [6], size_range, inputs, refinements)

        else:
            # hold_down — not applicable for FRP
            return SelectionResult(
                support_code=None,
                drawings=[],
                notes=[],
                size_range=size_range,
                inputs=inputs,
            )

    # -----------------------------------------------------------------------
    # Standard rules-table lookup
    # -----------------------------------------------------------------------
    try:
        function_table = SUPPORT_RULES[function_key]
        size_table     = function_table[size_range]
        mat_table      = size_table[material_key]

        if material_key == "cs_lt":
            pwht_key = "pwht" if pwht else "no_pwht"
            entry    = mat_table[pwht_key][insulation_key]
        else:
            entry    = mat_table[insulation_key]

    except KeyError as e:
        raise ValueError(
            f"No rule found for: function={function_key}, size={size_range}, "
            f"material={material_key}, pwht={pwht}, insulation={insulation_key}.\n"
            f"Missing key: {e}"
        )

    support_code = entry.get("support")          # None = not applicable
    note_numbers = entry.get("notes", [])

    return _build_result(support_code, note_numbers, size_range, inputs, refinements)


def _build_result(
    support_code,
    note_numbers,
    size_range,
    inputs,
    refinements=None,
) -> SelectionResult:
    refinement = apply_refinements(
        support_code=support_code,
        notes=note_numbers,
        inputs=inputs,
        refinements=refinements,
    )
    final_code = refinement.support_code
    drawings = get_drawings(final_code, nps=inputs["nps"]) if final_code else []

    return SelectionResult(
        support_code=final_code,
        drawings=drawings,
        notes=refinement.notes,
        size_range=size_range,
        inputs=inputs,
        status=refinement.status,
        refinement_questions=refinement.questions,
        applied_refinements=refinement.applied,
        refinement_warnings=refinement.warnings,
    )
