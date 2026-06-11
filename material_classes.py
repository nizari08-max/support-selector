"""
material_classes.py — JESA MPMS piping class → span material mapping.

Source: JESA Master Piping Material Specification (MPMS), project QW2507.
Used by:
  • Support Selector  (app.py / selector.py)  — material category routing
  • Span Calculator   (app.py /api/mpms-classes) — Table 13 / Table 14 lookup

Corrections applied (this file is the single source of truth):
  • BS1, BS3 → DS  (Duplex SS S32205)         — Table 14, not Table 13 SS
  • BS2     → SD  (Super Duplex SS S32750)    — Table 14, not Table 13 SS
  • CS1     → DS  (Duplex SS S32205)          — Table 14, not Table 13 SS
  • ES2     → SD  (Super Duplex SS S32750)    — Table 14, not Table 13 SS
  • CJ1     → AS  (1¼Cr–½Mo Alloy Steel)     — Table 14, not Table 13 CS
  • FJ1     → AS  (1¼Cr–½Mo Alloy Steel)     — Table 14, not Table 13 CS
  Note: the span calculator uses material code "AS"; the support selector
  dropdown uses "SA" for the same alloy-steel category. The /api/resolve-class
  endpoint returns "AS"; app.js maps AS→SA before setting the dropdown.

Excluded classes and reason:
  BH1, BH2 — HDPE:
      Non-metallic; spans governed by manufacturer data only.
  BL5 — Rubber Lined CS:
      Rubber liner changes effective stiffness; not in Tables 13–14.
  BN1 — PTFE Lined CS:
      PTFE liner changes effective stiffness; not in Tables 13–14.
  BR1 — CPVC:
      Non-metallic thermoplastic; not in Tables 13–14.
  BT1 — Reinforced Flexible Rubber:
      Flexible hose; span concept does not apply.
  BV1 — Dual Laminate PP/FRP:
      Polypropylene liner invalidates the Fiberbond FRP basis; use
      manufacturer span data.
  BX1, BX2, BX3 — Polypropylene:
      Non-metallic; not in Tables 13–14.
  BY1, BY3 — PVC:
      Non-metallic; not in Tables 13–14.
  BZ1 — PVDF:
      Non-metallic; not in Tables 13–14.
"""

# ── Span-material code labels ─────────────────────────────────────────────────
SPAN_MATERIAL_LABELS = {
    "CS":  "Carbon Steel",
    "LT":  "Low Temp. Carbon Steel",
    "SS":  "Stainless Steel",
    "DS":  "Duplex Stainless Steel",
    "SD":  "Super Duplex Stainless Steel",
    "AS":  "Alloy Steel",
    "AL":  "Aluminium",
    "AY":  "Aluminium Alloy",
    "TI":  "Titanium",
    "CN":  "Copper-Nickel",
    "FRP": "Fibre-Reinforced Plastic",
}

# Which materials use Table 13 (CS/LT/SS) vs Table 14 (all others)
TABLE_13_MATERIALS = {"CS", "LT", "SS"}
TABLE_14_MATERIALS = {"DS", "SD", "AS", "AL", "AY", "TI", "CN", "FRP"}


# ── MPMS_SPAN_MAP — every included piping class ───────────────────────────────
# Keys are upper-case class codes.  Extend this dict when the MPMS file
# is updated; do NOT duplicate entries in app.js.
#
# Fields:
#   material : span-lookup code (see SPAN_MATERIAL_LABELS)
#   table    : 13 or 14
#   rating   : ASME pressure class string
#   desc     : human-readable description

MPMS_SPAN_MAP = {

    # ── 150 Lb. Carbon Steel → Table 13 ─────────────────────────────────
    "BA1":  {"material": "CS",  "table": 13, "rating": "150 Lb.",      "desc": "Carbon Steel, Galvanized"},
    "BA2":  {"material": "CS",  "table": 13, "rating": "150 Lb.",      "desc": "Carbon Steel, Galvanized"},
    "BB1":  {"material": "CS",  "table": 13, "rating": "150 Lb.",      "desc": "Carbon Steel"},
    "BB1U": {"material": "CS",  "table": 13, "rating": "150 Lb.",      "desc": "Carbon Steel + PE Coating"},
    "BB2":  {"material": "CS",  "table": 13, "rating": "150 Lb.",      "desc": "Carbon Steel + PE Coating"},
    "BB3":  {"material": "CS",  "table": 13, "rating": "150 Lb.",      "desc": "Carbon Steel"},
    "BB4":  {"material": "CS",  "table": 13, "rating": "150 Lb.",      "desc": "Carbon Steel"},
    "BB5":  {"material": "CS",  "table": 13, "rating": "150 Lb.",      "desc": "Impact Tested Carbon Steel"},
    "BB6":  {"material": "CS",  "table": 13, "rating": "150 Lb.",      "desc": "Carbon Steel"},
    "BP1":  {"material": "CS",  "table": 13, "rating": "150 Lb.",      "desc": "Carbon Steel, Jacketed"},

    # ── 300 Lb. Carbon Steel → Table 13 ─────────────────────────────────
    "CB1":  {"material": "CS",  "table": 13, "rating": "300 Lb.",      "desc": "Carbon Steel"},
    "CB2":  {"material": "CS",  "table": 13, "rating": "300 Lb.",      "desc": "Impact Tested Carbon Steel"},
    "CB3":  {"material": "CS",  "table": 13, "rating": "300 Lb.",      "desc": "Carbon Steel"},
    "CP1":  {"material": "CS",  "table": 13, "rating": "300 Lb.",      "desc": "Carbon Steel"},

    # ── 900/1500 Lb. Carbon Steel → Table 13 ────────────────────────────
    "FB1":  {"material": "CS",  "table": 13, "rating": "900/1500 Lb.", "desc": "Carbon Steel"},

    # ── Alloy Steel (Chrome-Moly) → Table 14 ────────────────────────────
    "CJ1":  {"material": "AS",  "table": 14, "rating": "300 Lb.",      "desc": "1¼Cr–½Mo Chrome Moly"},
    "FJ1":  {"material": "AS",  "table": 14, "rating": "900/1500 Lb.", "desc": "1¼Cr–½Mo Chrome Moly"},

    # ── 150 Lb. Stainless Steel (Austenitic) → Table 13 ─────────────────
    "BD1":  {"material": "SS",  "table": 13, "rating": "150 Lb.",      "desc": "316/316L Stainless Steel"},
    "BD2":  {"material": "SS",  "table": 13, "rating": "150 Lb.",      "desc": "316/316L Stainless Steel"},
    "BD2U": {"material": "SS",  "table": 13, "rating": "150 Lb.",      "desc": "316/316L SS + PE Coated"},
    "BG1":  {"material": "SS",  "table": 13, "rating": "150 Lb.",      "desc": "904L Stainless Steel"},
    "BG2":  {"material": "SS",  "table": 13, "rating": "150 Lb.",      "desc": "904L Stainless Steel"},

    # ── 300 Lb. Stainless Steel (Austenitic) → Table 13 ─────────────────
    "CD1":  {"material": "SS",  "table": 13, "rating": "300 Lb.",      "desc": "316/316L Stainless Steel"},
    "CD2":  {"material": "SS",  "table": 13, "rating": "300 Lb.",      "desc": "316/316L Stainless Steel"},
    "CG1":  {"material": "SS",  "table": 13, "rating": "300 Lb.",      "desc": "904L Stainless Steel"},
    "CG2":  {"material": "SS",  "table": 13, "rating": "300 Lb.",      "desc": "904L Stainless Steel"},

    # ── 600 Lb. + 1500 Lb. Stainless Steel → Table 13 ───────────────────
    "GC1":  {"material": "SS",  "table": 13, "rating": "1500 Lb.",     "desc": "Stainless Steel SS 304H"},
    "GD1":  {"material": "SS",  "table": 13, "rating": "1500 Lb.",     "desc": "316/316L Stainless Steel"},
    "GD2":  {"material": "SS",  "table": 13, "rating": "1500 Lb.",     "desc": "316/316L Stainless Steel"},
    "KD1":  {"material": "SS",  "table": 13, "rating": "N/A",          "desc": "316/316L Stainless Steel"},

    # ── Duplex / Super Duplex Stainless Steel → Table 14 ────────────────
    "BS1":  {"material": "DS",  "table": 14, "rating": "150 Lb.",      "desc": "Duplex SS S32205"},
    "BS2":  {"material": "SD",  "table": 14, "rating": "150 Lb.",      "desc": "Super Duplex SS S32750"},
    "BS3":  {"material": "DS",  "table": 14, "rating": "150 Lb.",      "desc": "Duplex SS S32205"},
    "CS1":  {"material": "DS",  "table": 14, "rating": "300 Lb.",      "desc": "Duplex SS S32205"},
    "ES2":  {"material": "SD",  "table": 14, "rating": "600 Lb.",      "desc": "Super Duplex SS S32750"},

    # ── FRP / Fiberglass → Table 14 ─────────────────────────────────────
    "BK1":  {"material": "FRP", "table": 14, "rating": "150 Lb.",      "desc": "Fiberglass Reinforced Pipe"},
    "BK2":  {"material": "FRP", "table": 14, "rating": "150 Lb.",      "desc": "Fiberglass Reinforced Pipe"},
    "BK3":  {"material": "FRP", "table": 14, "rating": "150 Lb.",      "desc": "Fiberglass Reinforced Pipe"},
    "BK4":  {"material": "FRP", "table": 14, "rating": "150 Lb.",      "desc": "Fiberglass Reinforced Pipe"},
    "CK3":  {"material": "FRP", "table": 14, "rating": "300 Lb.",      "desc": "Fiberglass Reinforced Pipe"},
}


# ── Excluded classes (not supported for span lookup) ─────────────────────────
# Values are human-readable reason strings shown in the UI.
MPMS_EXCLUDED_SPAN = {
    "BH1": "HDPE — spans must follow pipe manufacturer guidelines",
    "BH2": "HDPE — spans must follow pipe manufacturer guidelines",
    "BL5": "Rubber Lined Carbon Steel — liner changes effective stiffness; use manufacturer data",
    "BN1": "PTFE Lined Carbon Steel — liner changes effective stiffness; use manufacturer data",
    "BR1": "CPVC — non-metallic thermoplastic; use manufacturer data",
    "BT1": "Reinforced Flexible Rubber — flexible hose; span concept does not apply",
    "BV1": "Dual Laminate PP/FRP — PP liner invalidates FRP span basis; use manufacturer data",
    "BX1": "Polypropylene (PP) — non-metallic; use manufacturer data",
    "BX2": "Polypropylene (PP) — non-metallic; use manufacturer data",
    "BX3": "Polypropylene (PP) — non-metallic; use manufacturer data",
    "BY1": "PVC — non-metallic; use manufacturer data",
    "BY3": "PVC — non-metallic; use manufacturer data",
    "BZ1": "PVDF — non-metallic; use manufacturer data",
}


# ── Public helpers ────────────────────────────────────────────────────────────

def resolve_class(code: str) -> dict | None:
    """
    Resolve a piping class code to its span lookup entry.

    Returns a dict with keys: material, table, rating, desc, excluded, reason.
    Returns None if the code is completely unknown.
    """
    key = code.strip().upper()

    entry = MPMS_SPAN_MAP.get(key)
    if entry:
        return {**entry, "excluded": False, "reason": None, "code": key}

    reason = MPMS_EXCLUDED_SPAN.get(key)
    if reason:
        return {"excluded": True, "reason": reason, "code": key,
                "material": None, "table": None, "rating": None, "desc": None}

    return None


def classes_for_api() -> dict:
    """
    Return a JSON-serialisable dict for the /api/mpms-classes endpoint.
    Groups included classes by material category, lists excluded codes.
    """
    groups: dict[str, list] = {}
    for code, entry in sorted(MPMS_SPAN_MAP.items()):
        mat = entry["material"]
        groups.setdefault(mat, []).append({
            "code":    code,
            "material": mat,
            "table":   entry["table"],
            "rating":  entry["rating"],
            "desc":    entry["desc"],
        })

    return {
        "groups":   groups,
        "excluded": {k: v for k, v in MPMS_EXCLUDED_SPAN.items()},
        "material_labels": SPAN_MATERIAL_LABELS,
    }
