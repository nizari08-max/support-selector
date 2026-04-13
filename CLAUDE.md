# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the Tool

```bash
cd piping_support_tool
python main.py
```

Python 3.7+ required. No external dependencies — all modules are in the same directory.

## Architecture

This is a **four-module CLI decision-support tool** for selecting piping supports per the JESA Piping Support Standard Rev A (Project QW2507).

### Data Flow

```
main.py → selector.py → support_rules.py
                      → drawing_index.py
```

1. `main.py` — Interactive CLI. Collects 5 user inputs: NPS (pipe size), material class, PWHT required, insulation condition, and support function.
2. `selector.py` — Normalizes raw inputs into canonical keys, navigates the rules table, and returns a `SelectionResult`. Entry point is `select_support()`.
3. `support_rules.py` — Nested `SUPPORT_RULES` dict encoding the engineering decision tables. Lookup path: `[function][size_range][material_class][pwht_status][insulation]` → `{"support": "CODE", "notes": [...]}`. Also contains `NOTES` dict for note text.
4. `drawing_index.py` — Maps support codes (e.g. `SC04`, `GL01`) to JESA drawing sheet references (`JS-PE-DPS-XXXX-001/002`).

### Key Normalization Mappings (selector.py)

- **Size ranges**: NPS float → one of `0.5_to_1`, `1.5`, `2_to_16`, `18_to_24`, `26_to_30`, `32_to_48`
- **Material classes**: free-text → one of `cs_lt`, `ss_ds_sd_sa`, `al_ay_cn`, `frp`
- **Insulation**: free-text → `uninsulated` or `hot_insulated`
- **Function**: free-text → `rest`, `guide`, `line_stop`, or `hold_down`

### Current State of the Rules Table

All entries in `SUPPORT_RULES` currently contain `"TODO"` values. Populating these from the JESA standard documents is the primary outstanding task.

### Drawing Code Families

| Prefix | Description |
|--------|-------------|
| BP | Bearing Plates |
| WA | Wear Pad Assemblies |
| SH | Pipe Shoes |
| SC | Shoe Clamps / Saddle Supports |
| GL | Guide Supports |
| LS | Line Stop Supports |
| GH | Hold Down / Guide-Hold Supports |
| CF | FRP Clamp Shoes |
