# =============================================================================
# main.py
# Piping Support Selector — Command Line Interface (MVP)
# Project: QW2507  |  Standard: JESA Piping Support Standard Rev A
# =============================================================================
#
# HOW TO RUN:
#   python main.py
#
# REQUIREMENTS:
#   Python 3.7 or later. No external libraries needed.
#   All four files must be in the same folder:
#     main.py, selector.py, support_rules.py, drawing_index.py
#
# WHAT IT DOES:
#   Asks the engineer 5 questions, then prints:
#     - Selected support code
#     - Applicable drawing reference number(s)
#     - Applicable engineering notes from the standard
# =============================================================================

from selector import select_support


# =============================================================================
# Accepted NPS values  (add more fractions as needed)
# =============================================================================
NPS_CHOICES = {
    "1/2":  0.5,
    "0.5":  0.5,
    "3/4":  0.75,
    "0.75": 0.75,
    "1":    1.0,
    "1.5":  1.5,
    "1-1/2": 1.5,
    "1 1/2": 1.5,
    "2":    2.0,
    "3":    3.0,
    "4":    4.0,
    "6":    6.0,
    "8":    8.0,
    "10":   10.0,
    "12":   12.0,
    "14":   14.0,
    "16":   16.0,
    "18":   18.0,
    "20":   20.0,
    "22":   22.0,
    "24":   24.0,
    "26":   26.0,
    "28":   28.0,
    "30":   30.0,
    "32":   32.0,
    "36":   36.0,
    "40":   40.0,
    "42":   42.0,
    "48":   48.0,
}


def ask_nps() -> float:
    """Prompt the user for pipe NPS and convert to a float."""
    print("\n  Pipe Size (NPS)")
    print("  Common sizes: 1/2, 3/4, 1, 1.5, 2, 3, 4, 6, 8, 10, 12, 14,")
    print("                16, 18, 20, 22, 24, 26, 28, 30, 32, 36, 40, 42, 48")
    while True:
        raw = input("  Enter NPS: ").strip()
        if raw in NPS_CHOICES:
            return NPS_CHOICES[raw]
        # Try parsing as a plain number
        try:
            val = float(raw)
            return val
        except ValueError:
            pass
        print(f"  [!] Could not parse '{raw}'. Please enter a valid NPS value.")


def ask_material() -> str:
    """Prompt the user for pipe material class."""
    print("\n  Material Class")
    print("  Options:")
    print("    CS  — Carbon Steel (without PWHT)")
    print("    CS  — Carbon Steel (with PWHT — you will be asked separately)")
    print("    LT  — Low Temperature Carbon Steel")
    print("    SS  — Stainless Steel")
    print("    DS  — Duplex Stainless")
    print("    SD  — Super Duplex Stainless")
    print("    SA  — Alloy Steel (treated as SS group)")
    print("    AL  — Aluminum")
    print("    AY  — Aluminum Alloy")
    print("    CN  — Copper-Nickel")
    print("    FRP — Fiberglass Reinforced Plastic")
    while True:
        raw = input("  Enter material class: ").strip()
        if raw:
            return raw
        print("  [!] Please enter a material class.")


def ask_pwht() -> bool:
    """Ask if PWHT is required. Only relevant for CS/LT pipes."""
    print("\n  PWHT Requirement")
    print("  Is Post Weld Heat Treatment (PWHT) required for this line?")
    while True:
        raw = input("  Enter Y or N: ").strip().upper()
        if raw in ("Y", "YES"):
            return True
        elif raw in ("N", "NO"):
            return False
        print("  [!] Please enter Y (yes) or N (no).")


def ask_insulation() -> str:
    """Prompt for insulation condition."""
    print("\n  Insulation Condition")
    print("  Options:")
    print("    U — Uninsulated (bare pipe)")
    print("    H — Hot Insulated (heat-conservation insulation)")
    while True:
        raw = input("  Enter U or H: ").strip().upper()
        if raw in ("U", "UNINSULATED"):
            return "uninsulated"
        elif raw in ("H", "HOT", "HOT_INSULATED", "HOT INSULATED"):
            return "hot_insulated"
        print("  [!] Please enter U (uninsulated) or H (hot insulated).")


def ask_function() -> str:
    """Prompt for the required support function."""
    print("\n  Support Function")
    print("  Options:")
    print("    R  — Rest (the pipe rests on the support, free to slide)")
    print("    G  — Guide (restricts lateral movement, allows axial)")
    print("    LS — Line Stop (restricts axial movement in one direction)")
    print("    HD — Hold Down (prevents upward movement)")
    while True:
        raw = input("  Enter R, G, LS, or HD: ").strip().upper()
        if raw in ("R", "REST"):
            return "rest"
        elif raw in ("G", "GUIDE"):
            return "guide"
        elif raw in ("LS", "LINE STOP", "LINE_STOP"):
            return "line_stop"
        elif raw in ("HD", "HOLD DOWN", "HOLD_DOWN"):
            return "hold_down"
        print("  [!] Please enter R, G, LS, or HD.")


def print_banner():
    """Print the tool title banner."""
    print()
    print("=" * 60)
    print("  JESA PIPING SUPPORT SELECTOR")
    print("  Project: QW2507  |  Standard Rev A")
    print("=" * 60)
    print("  This tool selects the appropriate pipe support type")
    print("  and retrieves the applicable drawing reference number.")
    print("=" * 60)


def run():
    """Main loop — runs the interactive selection tool."""
    print_banner()

    while True:
        print("\n  --- NEW SELECTION ---")

        # Collect inputs
        nps               = ask_nps()
        material          = ask_material()
        pwht              = ask_pwht()
        insulation        = ask_insulation()
        support_function  = ask_function()

        # Run selection
        try:
            result = select_support(
                nps=nps,
                material=material,
                pwht=pwht,
                insulation=insulation,
                support_function=support_function,
            )
            print(result)   # calls SelectionResult.__str__()

        except ValueError as e:
            print(f"\n  [ERROR] {e}")

        # Ask to run again
        print()
        again = input("  Run another selection? (Y/N): ").strip().upper()
        if again not in ("Y", "YES"):
            print()
            print("  Goodbye.")
            print()
            break


# =============================================================================
# Entry point
# =============================================================================
if __name__ == "__main__":
    run()
