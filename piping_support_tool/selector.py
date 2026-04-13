# =============================================================================
# selector.py
# Core Selection Logic — Piping Support Selector
# =============================================================================

from support_rules import SUPPORT_RULES, NOTES
from drawing_index import get_drawings


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


# =============================================================================
# STEP 5 — Result data class
# =============================================================================

class SelectionResult:
    """
    Holds the output of a support selection.

    support_code = None   →  not applicable for this combination
    support_code = string →  selected support description
    """

    def __init__(self, support_code, drawings, notes, size_range, inputs):
        self.support_code = support_code
        self.drawings     = drawings
        self.notes        = notes
        self.note_texts   = [NOTES[n] for n in notes if n in NOTES]
        self.size_range   = size_range
        self.inputs       = inputs

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
# STEP 6 — Main selection function
# =============================================================================

def select_support(
    nps: float,
    material: str,
    pwht: bool,
    insulation: str,
    support_function: str,
) -> SelectionResult:
    """
    Select the appropriate piping support based on pipe and project conditions.

    Args:
        nps              : Nominal pipe size as a decimal (0.5 … 48)
        material         : Material class string (e.g. "CS", "SS", "FRP")
        pwht             : True if PWHT is required (only relevant for CS/LT)
        insulation       : "uninsulated" or "hot_insulated"
        support_function : "rest", "guide", "line_stop", or "hold_down"

    Returns:
        SelectionResult with the selected support, drawings, and notes.
    """
    # --- Normalize inputs ---
    function_key   = normalize_function(support_function)
    material_key   = normalize_material(material)
    insulation_key = normalize_insulation(insulation)
    size_range     = get_size_range(nps, function_key)

    inputs = {
        "nps":        nps,
        "material":   material_key,
        "pwht":       pwht,
        "insulation": insulation_key,
        "function":   function_key,
    }

    # -----------------------------------------------------------------------
    # FRP special case for Table 16 (guide & line_stop only, NPS 2" – 24")
    # The standard lists FRP as a separate row "2"–24" (FRP)" at the bottom
    # of Table 16 with CF03 (guide) and CF04 (line stop).
    # -----------------------------------------------------------------------
    if material_key == "frp" and function_key in ("guide", "line_stop"):
        if 2.0 <= nps <= 24.0:
            code = "CLAMP SHOE FOR GUIDE (CF03)" if function_key == "guide" else "CLAMP SHOE FOR LINE STOP (CF04)"
            return SelectionResult(
                support_code=code,
                drawings=get_drawings(code),
                notes=[],
                size_range="frp_2_to_24",
                inputs=inputs,
            )
        else:
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
    drawings     = get_drawings(support_code) if support_code else []

    return SelectionResult(
        support_code=support_code,
        drawings=drawings,
        notes=note_numbers,
        size_range=size_range,
        inputs=inputs,
    )
