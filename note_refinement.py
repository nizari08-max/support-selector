# =============================================================================
# note_refinement.py
# Active Engineering Note Refinement Logic
# =============================================================================
#
# The base selector maps the five core inputs to a table result.  This module
# turns selected engineering notes and drawing-family ambiguities into active
# conditional questions and final support-code refinements.
# =============================================================================

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any


DESIGN_TEMP_FIELD = "design_temperature_c"
PIPE_ORIENTATION_FIELD = "pipe_orientation"
AXIAL_STOP_FIELD = "is_axial_stop_location"
LIMIT_STOP_FIELD = "is_limit_stop_location"
WALL_SCHEDULE_FIELD = "wall_schedule"


@dataclass
class RefinementOutcome:
    support_code: str | None
    notes: list[int]
    questions: list[dict[str, Any]] = field(default_factory=list)
    applied: list[dict[str, str]] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def status(self) -> str:
        return "needs_refinement" if self.questions else "complete"


def apply_refinements(
    support_code: str | None,
    notes: list[int],
    inputs: dict[str, Any],
    refinements: dict[str, Any] | None = None,
) -> RefinementOutcome:
    """Return a refined support code or the dynamic questions needed to refine it."""
    refinements = refinements or {}
    outcome = RefinementOutcome(support_code=support_code, notes=list(notes or []))

    if not support_code:
        return outcome

    # Apply case-specific refinements before generic temperature/orientation
    # logic so the targeted engineering paths remain fully deterministic.
    _apply_hot_insulated_ss_al_rest_refinement(outcome, inputs, refinements)
    _apply_large_ss_al_rest_shoe_refinement(outcome, inputs, refinements)
    _apply_temperature_refinement(outcome, inputs, refinements)
    _apply_axial_stop_refinement(outcome, refinements)
    _apply_wall_schedule_refinement(outcome, inputs, refinements)
    _apply_orientation_refinement(outcome, inputs, refinements)

    # FRP line stop is a project deviation.  Keep it structured so the frontend
    # can separate it from ordinary engineering notes later if needed.
    if 6 in outcome.notes:
        outcome.warnings.append(
            "FRP line stop uses CF03 as the nearest available standard support. "
            "Project approval is required before use."
        )

    return outcome


def _has_answer(refinements: dict[str, Any], field: str) -> bool:
    val = refinements.get(field)
    return val is not None and val != ""


def _add_question(outcome: RefinementOutcome, question: dict[str, Any]) -> None:
    if not any(q.get("id") == question.get("id") for q in outcome.questions):
        outcome.questions.append(question)


def _design_temperature_question(reason: str) -> dict[str, Any]:
    return {
        "id": DESIGN_TEMP_FIELD,
        "label": "Design Temperature (°C)",
        "type": "number",
        "unit": "°C",
        "required": True,
        "reason": reason,
        "min": -273,
        "step": 1,
    }


def _orientation_question() -> dict[str, Any]:
    return {
        "id": PIPE_ORIENTATION_FIELD,
        "label": "Pipe Orientation",
        "type": "choice",
        "required": True,
        "reason": "Required to select the correct straight-pipe or sloping-pipe drawing.",
        "options": [
            {"value": "straight", "label": "Straight Pipe"},
            {"value": "sloping", "label": "Sloping Pipe"},
        ],
    }


def _axial_stop_question() -> dict[str, Any]:
    return {
        "id": AXIAL_STOP_FIELD,
        "label": "Axial Stop Location",
        "type": "choice",
        "required": True,
        "reason": "Required by the engineering note for clamped-shoe or bare SS axial-stop cases.",
        "options": [
            {"value": "false", "label": "No"},
            {"value": "true", "label": "Yes"},
        ],
    }


def _limit_stop_question() -> dict[str, Any]:
    return {
        "id": LIMIT_STOP_FIELD,
        "label": "Limit Stop Location",
        "type": "choice",
        "required": True,
        "reason": "Required to determine whether the support is at a limit-stop location.",
        "options": [
            {"value": "false", "label": "No"},
            {"value": "true", "label": "Yes"},
        ],
    }


def _wall_schedule_question(material_key: str) -> dict[str, Any]:
    if material_key == "cs_lt":
        threshold = "Schedule 20"
        options = [
            {"value": "lt_sch20", "label": "< Schedule 20"},
            {"value": "ge_sch20", "label": ">= Schedule 20"},
        ]
    else:
        threshold = "Schedule 10S"
        options = [
            {"value": "lt_sch10s", "label": "< Schedule 10S"},
            {"value": "ge_sch10s", "label": ">= Schedule 10S"},
        ]

    return {
        "id": WALL_SCHEDULE_FIELD,
        "label": "Pipe Wall Schedule",
        "type": "choice",
        "required": True,
        "reason": f"Required to determine whether wall protection is needed below {threshold}.",
        "options": options,
    }


def _apply_temperature_refinement(
    outcome: RefinementOutcome,
    inputs: dict[str, Any],
    refinements: dict[str, Any],
) -> None:
    code = outcome.support_code or ""
    material_key = inputs.get("material")
    function_key = inputs.get("function")

    if _is_hot_insulated_ss_al_rest_case(inputs, code) or _is_large_ss_al_rest_shoe_case(inputs, code):
        return

    temp_rule_required = (
        "PER TEMP CRITERIA" in code.upper()
        or "SH03" in code.upper()
        or 5 in outcome.notes
    )
    if not temp_rule_required:
        return

    if not _has_answer(refinements, DESIGN_TEMP_FIELD):
        _add_question(
            outcome,
            _design_temperature_question(
                "Required to resolve temperature-dependent support selection."
            ),
        )
        return

    try:
        design_temp_c = float(refinements[DESIGN_TEMP_FIELD])
    except (TypeError, ValueError):
        _add_question(
            outcome,
            _design_temperature_question(
                "Enter a numeric Design Temperature (°C) to resolve this rule."
            ),
        )
        return

    # Note 5 is written in the current table as >=750 degF.  The drawings use
    # the same practical threshold as approximately 400 deg C.
    if 5 in outcome.notes and function_key == "line_stop":
        ls_code = "LS02" if float(inputs.get("nps", 0)) <= 6 else "LS03"
        if design_temp_c >= 400:
            outcome.support_code = _replace_or_expression(
                outcome.support_code,
                preferred_pattern=r"LS0[23]\s*\+\s*SH03",
            )
            outcome.support_code = re.sub(r"\bLS0[23]\b", ls_code, outcome.support_code or "", count=1)
            outcome.applied.append({
                "id": "design_temperature_c",
                "label": "Design Temperature (°C)",
                "result": ">= 400 °C; selected the high-temperature line-stop shoe branch.",
            })
        else:
            outcome.support_code = _remove_branch_matching(outcome.support_code, r"LS0[23]\s*\+\s*SH03")
            if outcome.support_code and not re.search(r"\bLS0[23]\b", outcome.support_code, flags=re.IGNORECASE):
                outcome.support_code = f"{ls_code} + {outcome.support_code}"
            outcome.applied.append({
                "id": "design_temperature_c",
                "label": "Design Temperature (°C)",
                "result": "< 400 °C; selected the standard welded-shoe plus wear-pad branch.",
            })
        return

    # Rest supports for SS/AL families use clamped shoes above the temperature
    # threshold; otherwise the welded shoe + wear pad branch remains.
    if "PER TEMP CRITERIA" in code.upper() and material_key in {"ss_ds_sd_sa", "al_ay_cn"}:
        if design_temp_c >= 350:
            outcome.support_code = _replace_or_expression(
                outcome.support_code,
                preferred_pattern=r"CLAMPED SHOE\s*\([^)]*\)",
            )
            outcome.applied.append({
                "id": "design_temperature_c",
                "label": "Design Temperature (°C)",
                "result": ">= 350 °C; selected the high-temperature clamped-shoe branch.",
            })
        else:
            outcome.support_code = _remove_branch_matching(outcome.support_code, r"CLAMPED SHOE\s*\([^)]*\)")
            outcome.applied.append({
                "id": "design_temperature_c",
                "label": "Design Temperature (°C)",
                "result": "< 350 °C; selected the welded-shoe plus wear-pad branch.",
            })


def _apply_axial_stop_refinement(
    outcome: RefinementOutcome,
    refinements: dict[str, Any],
) -> None:
    if 3 not in outcome.notes:
        return

    if not _has_answer(refinements, AXIAL_STOP_FIELD):
        _add_question(outcome, _axial_stop_question())
        return

    is_axial_stop = str(refinements.get(AXIAL_STOP_FIELD)).lower() == "true"

    if 3 in outcome.notes:
        if is_axial_stop:
            outcome.support_code = _select_or_branch(
                outcome.support_code,
                preferred_pattern=r"WELDED SHOE\s*\([^)]*\)",
            )
            outcome.applied.append({
                "id": "axial_stop_location",
                "label": "Axial Stop Location",
                "result": "Axial stop selected; using welded shoe + wear pad instead of clamped shoe.",
            })
        else:
            outcome.support_code = _select_or_branch(
                outcome.support_code,
                preferred_pattern=r"CLAMPED SHOE\s*\([^)]*\)",
            )
            outcome.applied.append({
                "id": "axial_stop_location",
                "label": "Axial Stop Location",
                "result": "Non-axial-stop location selected; using the normal clamped-shoe support.",
            })

def _apply_wall_schedule_refinement(
    outcome: RefinementOutcome,
    inputs: dict[str, Any],
    refinements: dict[str, Any],
) -> None:
    code = outcome.support_code or ""
    material_key = inputs.get("material")
    nps = float(inputs.get("nps", 0))

    if 1 not in outcome.notes and 2 not in outcome.notes:
        return

    if _is_ss_family_uninsulated_rest_path(inputs, code):
        _apply_ss_family_uninsulated_rest_refinement(outcome, inputs, refinements)
        return

    # Do not ask wall-thickness questions when the base result already provides
    # shoe or wear-pad protection.  The active question is only needed for
    # direct-rest or "if applicable" protection choices.
    upper_code = code.upper()
    if (
        "DIRECT REST" not in upper_code
        and "IF APPLICABLE" not in upper_code
        and "BEARING PLATE" not in upper_code
    ):
        return

    wall_rule_applies = material_key in {"cs_lt"}
    if not wall_rule_applies:
        return

    if not _has_answer(refinements, WALL_SCHEDULE_FIELD):
        _add_question(outcome, _wall_schedule_question(material_key))
        return

    wall_schedule = str(refinements.get(WALL_SCHEDULE_FIELD))
    thin_wall = wall_schedule in {"lt_sch20", "lt_sch10s"}

    if not thin_wall:
        outcome.applied.append({
            "id": "wall_schedule",
            "label": "Pipe Wall Schedule",
            "result": "Wall schedule is not below the note threshold.",
        })
        return

    if material_key == "cs_lt" and nps <= 24 and "DIRECT REST" in code.upper():
        shoe = "WELDED SHOE (SH01/SH04)" if nps <= 4 else "WELDED SHOE (SH01/SH05)"
        outcome.support_code = shoe
        outcome.applied.append({
            "id": "wall_schedule",
            "label": "Pipe Wall Schedule",
            "result": "Thin-wall CS/LT pipe requires a pipe shoe for wall protection.",
        })

def _is_ss_family_uninsulated_rest_path(inputs: dict[str, Any], code: str) -> bool:
    material_key = inputs.get("material")
    function_key = inputs.get("function")
    insulation_key = inputs.get("insulation")
    nps = float(inputs.get("nps", 0))
    upper_code = code.upper()

    return (
        function_key == "rest"
        and insulation_key == "uninsulated"
        and material_key in {"ss_ds_sd_sa", "al_ay_cn"}
        and 1.5 <= nps <= 24.0
        and "BEARING PLATE" in upper_code
        and "WA01" in upper_code
    )


def _apply_ss_family_uninsulated_rest_refinement(
    outcome: RefinementOutcome,
    inputs: dict[str, Any],
    refinements: dict[str, Any],
) -> None:
    nps = float(inputs.get("nps", 0))

    if not _has_answer(refinements, WALL_SCHEDULE_FIELD):
        _add_question(outcome, _wall_schedule_question(inputs.get("material")))
        return

    wall_schedule = str(refinements.get(WALL_SCHEDULE_FIELD))
    thin_wall = wall_schedule == "lt_sch10s"

    if thin_wall:
        shoe = "WELDED SHOE (SH01/SH04)" if nps <= 4 else "WELDED SHOE (SH01/SH05)"
        outcome.support_code = f"{shoe} + WEAR PAD (WA01)"
        outcome.applied.append({
            "id": "wall_schedule",
            "label": "Pipe Wall Schedule",
            "result": "Schedule < 10S; selected welded shoe + wear pad for this material group.",
        })
    else:
        outcome.support_code = "WEAR PAD (WA01)"
        outcome.applied.append({
            "id": "wall_schedule",
            "label": "Pipe Wall Schedule",
            "result": "Schedule >= 10S; selected wear pad as the governing support result.",
        })


def _apply_orientation_refinement(
    outcome: RefinementOutcome,
    inputs: dict[str, Any],
    refinements: dict[str, Any],
) -> None:
    code = outcome.support_code or ""

    if _is_hot_insulated_ss_al_rest_case(inputs, code):
        return

    if not _needs_orientation(code):
        return

    if not _has_answer(refinements, PIPE_ORIENTATION_FIELD):
        _add_question(outcome, _orientation_question())
        return

    orientation = str(refinements.get(PIPE_ORIENTATION_FIELD)).lower()
    if orientation not in {"straight", "sloping"}:
        _add_question(outcome, _orientation_question())
        return

    nps = float(inputs.get("nps", 0))
    resolved = _resolve_orientation_codes(code, orientation, nps)
    if resolved != code:
        outcome.support_code = resolved
        outcome.applied.append({
            "id": "pipe_orientation",
            "label": "Pipe Orientation",
            "result": f"{'Straight Pipe' if orientation == 'straight' else 'Sloping Pipe'} selected; drawing family narrowed.",
        })


def _is_large_ss_al_rest_shoe_case(inputs: dict[str, Any], code: str) -> bool:
    material_key = inputs.get("material")
    function_key = inputs.get("function")
    nps = float(inputs.get("nps", 0))
    upper_code = code.upper()

    return (
        function_key == "rest"
        and material_key in {"ss_ds_sd_sa", "al_ay_cn"}
        and 26.0 <= nps <= 48.0
        and "SH02/SH03/SH05" in upper_code
        and "WA01" in upper_code
    )


def _is_hot_insulated_ss_al_rest_case(inputs: dict[str, Any], code: str) -> bool:
    material_key = inputs.get("material")
    function_key = inputs.get("function")
    insulation_key = inputs.get("insulation")
    nps = float(inputs.get("nps", 0))
    upper_code = code.upper()

    return (
        function_key == "rest"
        and insulation_key == "hot_insulated"
        and material_key in {"ss_ds_sd_sa", "al_ay_cn"}
        and 1.5 <= nps <= 24.0
        and "SC02-SC04" in upper_code
        and "SC06-SC08" in upper_code
    )


def _apply_hot_insulated_ss_al_rest_refinement(
    outcome: RefinementOutcome,
    inputs: dict[str, Any],
    refinements: dict[str, Any],
) -> None:
    code = outcome.support_code or ""
    if not _is_hot_insulated_ss_al_rest_case(inputs, code):
        return

    if not _has_answer(refinements, PIPE_ORIENTATION_FIELD):
        _add_question(outcome, _orientation_question())
        return

    orientation = str(refinements.get(PIPE_ORIENTATION_FIELD)).lower()
    if orientation not in {"straight", "sloping"}:
        _add_question(outcome, _orientation_question())
        return

    if not _has_answer(refinements, LIMIT_STOP_FIELD):
        _add_question(outcome, _limit_stop_question())
        return

    is_limit_stop = str(refinements.get(LIMIT_STOP_FIELD)).lower() == "true"
    if orientation == "straight" and is_limit_stop:
        outcome.support_code = "WELDED SHOE (SH01) + WEAR PAD (WA01)"
        outcome.applied.append({
            "id": "pipe_orientation",
            "label": "Pipe Orientation",
            "result": "Straight Pipe selected for hot-insulated SS/AL-family rest support.",
        })
        outcome.applied.append({
            "id": LIMIT_STOP_FIELD,
            "label": "Limit Stop Location",
            "result": "Yes; selected SH01 and skipped temperature for this branch.",
        })
        return

    if not _has_answer(refinements, DESIGN_TEMP_FIELD):
        _add_question(
            outcome,
            _design_temperature_question(
                "Required to resolve the hot-insulated rest support for this material group."
            ),
        )
        return

    try:
        design_temp_c = float(refinements[DESIGN_TEMP_FIELD])
    except (TypeError, ValueError):
        _add_question(
            outcome,
            _design_temperature_question(
                "Enter a numeric Design Temperature (°C) to resolve this support selection."
            ),
        )
        return

    outcome.applied.append({
        "id": "pipe_orientation",
        "label": "Pipe Orientation",
        "result": f"{'Straight Pipe' if orientation == 'straight' else 'Sloping Pipe'} selected for hot-insulated SS/AL-family rest support.",
    })
    outcome.applied.append({
        "id": LIMIT_STOP_FIELD,
        "label": "Limit Stop Location",
        "result": "Yes" if is_limit_stop else "No",
    })

    if orientation == "straight":
        if design_temp_c <= 350:
            outcome.support_code = "CLAMPED SHOE (SC02 OR SC03)"
            temp_result = "<= 350 °C; selected SC02 OR SC03."
        else:
            outcome.support_code = "CLAMPED SHOE (SC04)"
            temp_result = "> 350 °C; selected SC04."
    else:
        if is_limit_stop:
            if design_temp_c < 400:
                outcome.support_code = "WELDED SHOE (SH05) + WEAR PAD (WA01)"
                temp_result = "< 400 °C at limit stop; selected SH05."
            else:
                outcome.support_code = "WELDED SHOE (SH03) + WEAR PAD (WA01)"
                temp_result = ">= 400 °C at limit stop; selected SH03."
        elif design_temp_c <= 350:
            outcome.support_code = "CLAMPED SHOE (SC06 OR SC07)"
            temp_result = "<= 350 °C; selected SC06 OR SC07."
        elif design_temp_c < 400:
            outcome.support_code = "CLAMPED SHOE (SC08)"
            temp_result = "> 350 °C and < 400 °C; selected SC08."
        else:
            outcome.support_code = "WELDED SHOE (SH03)"
            temp_result = ">= 400 °C; selected SH03."

    outcome.applied.append({
        "id": DESIGN_TEMP_FIELD,
        "label": "Design Temperature (°C)",
        "result": temp_result,
    })


def _apply_large_ss_al_rest_shoe_refinement(
    outcome: RefinementOutcome,
    inputs: dict[str, Any],
    refinements: dict[str, Any],
) -> None:
    code = outcome.support_code or ""
    if not _is_large_ss_al_rest_shoe_case(inputs, code):
        return

    if not _has_answer(refinements, PIPE_ORIENTATION_FIELD):
        _add_question(outcome, _orientation_question())
        return

    orientation = str(refinements.get(PIPE_ORIENTATION_FIELD)).lower()
    if orientation not in {"straight", "sloping"}:
        _add_question(outcome, _orientation_question())
        return

    if orientation == "straight":
        outcome.support_code = "WELDED SHOE (SH02) + WEAR PAD (WA01)"
        outcome.applied.append({
            "id": "pipe_orientation",
            "label": "Pipe Orientation",
            "result": "Straight Pipe selected; using SH02 with wear pad WA01.",
        })
        return

    if not _has_answer(refinements, DESIGN_TEMP_FIELD):
        _add_question(
            outcome,
            _design_temperature_question(
                "Required for sloping pipe to select the correct large-bore shoe drawing."
            ),
        )
        return

    try:
        design_temp_c = float(refinements[DESIGN_TEMP_FIELD])
    except (TypeError, ValueError):
        _add_question(
            outcome,
            _design_temperature_question(
                "Enter a numeric Design Temperature (°C) for the sloping-pipe support selection."
            ),
        )
        return

    if design_temp_c >= 400:
        outcome.support_code = "WELDED SHOE (SH03) + WEAR PAD (WA01)"
        outcome.applied.append({
            "id": "pipe_orientation",
            "label": "Pipe Orientation",
            "result": "Sloping Pipe selected; temperature check applied.",
        })
        outcome.applied.append({
            "id": "design_temperature_c",
            "label": "Design Temperature (°C)",
            "result": ">= 400 °C; selected SH03 with wear pad WA01.",
        })
    else:
        outcome.support_code = "WELDED SHOE (SH05) + WEAR PAD (WA01)"
        outcome.applied.append({
            "id": "pipe_orientation",
            "label": "Pipe Orientation",
            "result": "Sloping Pipe selected; temperature check applied.",
        })
        outcome.applied.append({
            "id": "design_temperature_c",
            "label": "Design Temperature (°C)",
            "result": "< 400 °C; selected SH05 with wear pad WA01.",
        })


def _needs_orientation(code: str) -> bool:
    s = code.upper()
    return any(token in s for token in (
        "SH01/SH04",
        "SH01/SH05",
        "SH01/SH04/SH05",
        "SH02/SH05",
        "SC01/SC05",
        "SC02-SC04",
        "SC06-SC08",
    ))


def _resolve_orientation_codes(code: str, orientation: str, nps: float) -> str:
    sloped_small = "SH04" if nps <= 4 else "SH05"

    replacements = []
    if orientation == "straight":
        replacements = [
            (r"SH01/SH04/SH05", "SH01"),
            (r"SH01/SH04", "SH01"),
            (r"SH01/SH05", "SH01"),
            (r"SH02/SH05", "SH02"),
            (r"SC01/SC05", "SC01"),
            (r"SC02-SC04,\s*SC06-SC08", "SC02-SC04"),
        ]
    else:
        replacements = [
            (r"SH01/SH04/SH05", sloped_small),
            (r"SH01/SH04", sloped_small),
            (r"SH01/SH05", sloped_small),
            (r"SH02/SH05", "SH05"),
            (r"SC01/SC05", "SC05"),
            (r"SC02-SC04,\s*SC06-SC08", "SC06-SC08"),
        ]

    out = code
    for pattern, replacement in replacements:
        out = re.sub(pattern, replacement, out, flags=re.IGNORECASE)
    return out


def _replace_or_expression(support_code: str | None, preferred_pattern: str) -> str | None:
    return _select_or_branch(support_code, preferred_pattern)


def _select_or_branch(support_code: str | None, preferred_pattern: str) -> str | None:
    if not support_code:
        return support_code
    parts = re.split(r"\s+OR\s+", support_code, flags=re.IGNORECASE)
    for part in parts:
        if re.search(preferred_pattern, part, flags=re.IGNORECASE):
            return _clean_support_text(part)
    return support_code


def _remove_branch_matching(support_code: str | None, pattern: str) -> str | None:
    if not support_code:
        return support_code
    parts = re.split(r"\s+OR\s+", support_code, flags=re.IGNORECASE)
    remaining = [part for part in parts if not re.search(pattern, part, flags=re.IGNORECASE)]
    if not remaining:
        return support_code
    return _clean_support_text(" OR ".join(remaining))


def _clean_support_text(value: str) -> str:
    value = re.sub(r"\s+", " ", value).strip()
    value = re.sub(r"\s+per\s+(PWHT|temp)\s+criteria", "", value, flags=re.IGNORECASE)
    return value.strip()
