# =============================================================================
# support_rules.py
# Piping Support Selection Rules - Tables 15 & 16
# Project: QW2507 | Standard: JESA Piping Support Standard Rev A
# =============================================================================
#
# TABLE 15 (rest) uses these size range keys:
#   0.5_to_1 | 1.5 | 2_to_16 | 18_to_24 | 26_to_30 | 32_to_48
#
# TABLE 16 (guide / line_stop / hold_down) uses different size range keys:
#   0.5_to_1 | 1.5_to_6 | 8_to_10 | 12_to_48
#
# MATERIAL CLASSES:
#   cs_lt        → CS, LT, Internally Cladded  (has no_pwht / pwht sub-keys)
#   ss_ds_sd_sa  → SS, DS, SD, SA
#   al_ay_cn     → AL, AY, CN
#   frp          → FRP  (Table 16 FRP handled as special case in selector.py)
#
# support: None  →  not applicable for this combination ("-" in original table)
# =============================================================================

SUPPORT_RULES = {

    # =========================================================================
    # TABLE 15  -  REST SUPPORTS
    # =========================================================================
    "rest": {

        # NPS 1/2" - 1"
        "0.5_to_1": {
            "cs_lt": {
                "no_pwht": {
                    "uninsulated":   {"support": "DIRECT REST",  "notes": []},
                    "hot_insulated": {"support": "DIRECT REST",  "notes": []},
                },
                "pwht": {
                    "uninsulated":   {"support": "DIRECT REST",  "notes": []},
                    "hot_insulated": {"support": "DIRECT REST",  "notes": []},
                },
            },
            "ss_ds_sd_sa": {
                "uninsulated":   {"support": "BEARING PLATE (BP02)",  "notes": []},
                "hot_insulated": {"support": "BEARING PLATE (BP02)",  "notes": []},
            },
            "al_ay_cn": {
                "uninsulated":   {"support": "BEARING PLATE (BP02)",  "notes": []},
                "hot_insulated": {"support": "BEARING PLATE (BP02)",  "notes": []},
            },
            "frp": {
                "uninsulated":   {"support": None, "notes": []},
                "hot_insulated": {"support": None, "notes": []},
            },
        },

        # NPS 1-1/2"
        "1.5": {
            "cs_lt": {
                "no_pwht": {
                    "uninsulated":   {"support": "DIRECT REST",                          "notes": []},
                    "hot_insulated": {"support": "WELDED SHOE (SH01/SH04)",              "notes": []},
                },
                "pwht": {
                    "uninsulated":   {"support": "DIRECT REST",                          "notes": []},
                    "hot_insulated": {"support": "CLAMPED SHOE (SC01/SC05) per PWHT criteria  OR  WELDED SHOE (SH01/SH04) + WEAR PAD (WA01)",
                                      "notes": [3]},
                },
            },
            "ss_ds_sd_sa": {
                "uninsulated":   {"support": "BEARING PLATE (BP02) / ISOLATION PAD (PR01/PR02) / WEAR PAD (WA01)",
                                  "notes": [1, 2, 4]},
                "hot_insulated": {"support": "CLAMPED SHOE (SC02-SC04, SC06-SC09)  OR  WELDED SHOE (SH01/SH03/SH04) + WEAR PAD (WA01)",
                                  "notes": []},
            },
            "al_ay_cn": {
                "uninsulated":   {"support": "BEARING PLATE (BP02) / ISOLATION PAD (PR01/PR02) / WEAR PAD (WA01)",
                                  "notes": [1, 2, 4]},
                "hot_insulated": {"support": "CLAMPED SHOE (SC02-SC04, SC06-SC09)  OR  WELDED SHOE (SH01/SH03/SH04) + WEAR PAD (WA01)",
                                  "notes": []},
            },
            "frp": {
                "uninsulated":   {"support": None, "notes": []},
                "hot_insulated": {"support": None, "notes": []},
            },
        },

        # NPS 2" - 16"
        "2_to_16": {
            "cs_lt": {
                "no_pwht": {
                    "uninsulated":   {"support": "DIRECT REST",                          "notes": [1, 2]},
                    "hot_insulated": {"support": "WELDED SHOE (SH01/SH05)",              "notes": [1, 2]},
                },
                "pwht": {
                    "uninsulated":   {"support": "DIRECT REST",                          "notes": [1, 2]},
                    "hot_insulated": {"support": "CLAMPED SHOE (SC01/SC05) per PWHT criteria  OR  WELDED SHOE (SH01/SH04/SH05) + WEAR PAD (WA01)",
                                      "notes": [3]},
                },
            },
            "ss_ds_sd_sa": {
                "uninsulated":   {"support": "BEARING PLATE (BP02) / ISOLATION PAD (PR01/PR02) / WEAR PAD (WA01)",
                                  "notes": [1, 2, 4]},
                "hot_insulated": {"support": "CLAMPED SHOE (SC02-SC04, SC06-SC09)  OR  WELDED SHOE (SH01/SH03/SH05) + WEAR PAD (WA01)",
                                  "notes": []},
            },
            "al_ay_cn": {
                "uninsulated":   {"support": "BEARING PLATE (BP02) / ISOLATION PAD (PR01/PR02) / WEAR PAD (WA01)",
                                  "notes": [1, 2, 4]},
                "hot_insulated": {"support": "CLAMPED SHOE (SC02-SC04, SC06-SC09)  OR  WELDED SHOE (SH01/SH03/SH05) + WEAR PAD (WA01)",
                                  "notes": []},
            },
            "frp": {
                "uninsulated":   {"support": "CLAMP SHOE (CF01)", "notes": []},
                "hot_insulated": {"support": "CLAMP SHOE (CF01)", "notes": []},
            },
        },

        # NPS 18" - 24"
        "18_to_24": {
            "cs_lt": {
                "no_pwht": {
                    "uninsulated":   {"support": "WEAR PAD (WA01)",                      "notes": [1, 2]},
                    "hot_insulated": {"support": "WELDED SHOE (SH01/SH05) + WEAR PAD (WA01)",
                                      "notes": []},
                },
                "pwht": {
                    "uninsulated":   {"support": "WEAR PAD (WA01)",                      "notes": [1, 2]},
                    "hot_insulated": {"support": "CLAMPED SHOE (SC01/SC05) per PWHT criteria  OR  WELDED SHOE (SH01/SH05) + WEAR PAD (WA01)",
                                      "notes": [3]},
                },
            },
            "ss_ds_sd_sa": {
                "uninsulated":   {"support": "BEARING PLATE (BP02) / ISOLATION PAD (PR01/PR02) / WEAR PAD (WA01)",
                                  "notes": [1, 2, 4]},
                "hot_insulated": {"support": "CLAMPED SHOE (SC02-SC04, SC06-SC09) per temp criteria  OR  WELDED SHOE (SH01/SH03/SH05) + WEAR PAD (WA01)",
                                  "notes": [4]},
            },
            "al_ay_cn": {
                "uninsulated":   {"support": "BEARING PLATE (BP02) / ISOLATION PAD (PR01/PR02) / WEAR PAD (WA01)",
                                  "notes": [1, 2, 4]},
                "hot_insulated": {"support": "CLAMPED SHOE (SC02-SC04, SC06-SC09) per temp criteria  OR  WELDED SHOE (SH01/SH03/SH05) + WEAR PAD (WA01)",
                                  "notes": [4]},
            },
            "frp": {
                "uninsulated":   {"support": "CLAMP SHOE (CF01)", "notes": []},
                "hot_insulated": {"support": "CLAMP SHOE (CF01)", "notes": []},
            },
        },

        # NPS 26" - 30"
        "26_to_30": {
            "cs_lt": {
                "no_pwht": {
                    "uninsulated":   {"support": "WELDED SHOE (SH02/SH05) + WEAR PAD (WA01)", "notes": []},
                    "hot_insulated": {"support": "WELDED SHOE (SH02/SH05) + WEAR PAD (WA01)", "notes": []},
                },
                "pwht": {
                    "uninsulated":   {"support": "WELDED SHOE (SH02/SH05) + WEAR PAD (WA01)", "notes": []},
                    "hot_insulated": {"support": "WELDED SHOE (SH02/SH05) + WEAR PAD (WA01)", "notes": []},
                },
            },
            "ss_ds_sd_sa": {
                "uninsulated":   {"support": "WELDED SHOE (SH02/SH03/SH05) + WEAR PAD (WA01)", "notes": []},
                "hot_insulated": {"support": "WELDED SHOE (SH02/SH03/SH05) + WEAR PAD (WA01)", "notes": []},
            },
            "al_ay_cn": {
                "uninsulated":   {"support": "WELDED SHOE (SH02/SH03/SH05) + WEAR PAD (WA01)", "notes": []},
                "hot_insulated": {"support": "WELDED SHOE (SH02/SH03/SH05) + WEAR PAD (WA01)", "notes": []},
            },
            "frp": {
                "uninsulated":   {"support": "CLAMP SHOE (CF02)", "notes": []},
                "hot_insulated": {"support": "CLAMP SHOE (CF02)", "notes": []},
            },
        },

        # NPS 32" - 48"
        "32_to_48": {
            "cs_lt": {
                "no_pwht": {
                    "uninsulated":   {"support": "WELDED SHOE (SH02/SH05) + WEAR PAD (WA01)", "notes": []},
                    "hot_insulated": {"support": "WELDED SHOE (SH02/SH05) + WEAR PAD (WA01)", "notes": []},
                },
                "pwht": {
                    "uninsulated":   {"support": "WELDED SHOE (SH02/SH05) + WEAR PAD (WA01)", "notes": []},
                    "hot_insulated": {"support": "WELDED SHOE (SH02/SH05) + WEAR PAD (WA01)", "notes": []},
                },
            },
            "ss_ds_sd_sa": {
                "uninsulated":   {"support": "WELDED SHOE (SH02/SH03/SH05) + WEAR PAD (WA01)", "notes": []},
                "hot_insulated": {"support": "WELDED SHOE (SH02/SH03/SH05) + WEAR PAD (WA01)", "notes": []},
            },
            "al_ay_cn": {
                "uninsulated":   {"support": "WELDED SHOE (SH02/SH03/SH05) + WEAR PAD (WA01)", "notes": []},
                "hot_insulated": {"support": "WELDED SHOE (SH02/SH03/SH05) + WEAR PAD (WA01)", "notes": []},
            },
            "frp": {
                "uninsulated":   {"support": None, "notes": []},
                "hot_insulated": {"support": None, "notes": []},
            },
        },
    },

    # =========================================================================
    # TABLE 16  -  GUIDE SUPPORTS
    # Size ranges: 0.5_to_1 | 1.5_to_6 | 8_to_10 | 12_to_48
    # FRP (NPS 2"-24") is handled as a special case in selector.py → CF03
    # =========================================================================
    "guide": {

        # NPS 1/2" - 1"  (hot insulated = not applicable)
        "0.5_to_1": {
            "cs_lt": {
                "no_pwht": {
                    "uninsulated":   {"support": "GL01", "notes": []},
                    "hot_insulated": {"support": None,   "notes": []},
                },
                "pwht": {
                    "uninsulated":   {"support": "GL01", "notes": []},
                    "hot_insulated": {"support": None,   "notes": []},
                },
            },
            "ss_ds_sd_sa": {
                "uninsulated":   {"support": "GL01 + PR01/PR02 or WA01 (if applicable)", "notes": []},
                "hot_insulated": {"support": None,                                        "notes": []},
            },
            "al_ay_cn": {
                "uninsulated":   {"support": "GL01 + PR01/PR02 or WA01 (if applicable)", "notes": []},
                "hot_insulated": {"support": None,                                        "notes": []},
            },
            "frp": {
                "uninsulated":   {"support": None, "notes": []},
                "hot_insulated": {"support": None, "notes": []},
            },
        },

        # NPS 1-1/2" - 6"
        "1.5_to_6": {
            "cs_lt": {
                "no_pwht": {
                    "uninsulated":   {"support": "GL01", "notes": []},
                    "hot_insulated": {"support": "GL02", "notes": []},
                },
                "pwht": {
                    "uninsulated":   {"support": "GL01", "notes": []},
                    "hot_insulated": {"support": "GL02", "notes": []},
                },
            },
            "ss_ds_sd_sa": {
                "uninsulated":   {"support": "GL01 + PR01/PR02 or WA01 (if applicable)", "notes": []},
                "hot_insulated": {"support": "GL02",                                      "notes": []},
            },
            "al_ay_cn": {
                "uninsulated":   {"support": "GL01 + PR01/PR02 or WA01 (if applicable)", "notes": []},
                "hot_insulated": {"support": "GL02",                                      "notes": []},
            },
            "frp": {
                "uninsulated":   {"support": None, "notes": []},
                "hot_insulated": {"support": None, "notes": []},
            },
        },

        # NPS 8" - 10"
        "8_to_10": {
            "cs_lt": {
                "no_pwht": {
                    "uninsulated":   {"support": "GL01", "notes": []},
                    "hot_insulated": {"support": "GL02", "notes": []},
                },
                "pwht": {
                    "uninsulated":   {"support": "GL01", "notes": []},
                    "hot_insulated": {"support": "GL02", "notes": []},
                },
            },
            "ss_ds_sd_sa": {
                "uninsulated":   {"support": "GL01 + PR01/PR02 or WA01 (if applicable)", "notes": []},
                "hot_insulated": {"support": "GL02",                                      "notes": []},
            },
            "al_ay_cn": {
                "uninsulated":   {"support": "GL01 + PR01/PR02 or WA01 (if applicable)", "notes": []},
                "hot_insulated": {"support": "GL02",                                      "notes": []},
            },
            "frp": {
                "uninsulated":   {"support": None, "notes": []},
                "hot_insulated": {"support": None, "notes": []},
            },
        },

        # NPS 12" - 48"
        "12_to_48": {
            "cs_lt": {
                "no_pwht": {
                    "uninsulated":   {"support": "GL01", "notes": []},
                    "hot_insulated": {"support": "GL02", "notes": []},
                },
                "pwht": {
                    "uninsulated":   {"support": "GL01", "notes": []},
                    "hot_insulated": {"support": "GL02", "notes": []},
                },
            },
            "ss_ds_sd_sa": {
                "uninsulated":   {"support": "GL01 + PR01/PR02 or WA01 (if applicable)", "notes": []},
                "hot_insulated": {"support": "GL02",                                      "notes": []},
            },
            "al_ay_cn": {
                "uninsulated":   {"support": "GL01 + PR01/PR02 or WA01 (if applicable)", "notes": []},
                "hot_insulated": {"support": "GL02",                                      "notes": []},
            },
            "frp": {
                "uninsulated":   {"support": None, "notes": []},
                "hot_insulated": {"support": None, "notes": []},
            },
        },
    },

    # =========================================================================
    # TABLE 16  -  LINE STOP SUPPORTS
    # FRP (NPS 2"-24") is handled as a special case in selector.py → CF04
    # =========================================================================
    "line_stop": {

        # NPS 1/2" - 1"  (hot insulated = not applicable)
        "0.5_to_1": {
            "cs_lt": {
                "no_pwht": {
                    "uninsulated":   {"support": "LS01", "notes": []},
                    "hot_insulated": {"support": None,   "notes": []},
                },
                "pwht": {
                    "uninsulated":   {"support": "LS01", "notes": []},
                    "hot_insulated": {"support": None,   "notes": []},
                },
            },
            "ss_ds_sd_sa": {
                "uninsulated":   {"support": "LS01 + WEAR PAD (WA01)", "notes": []},
                "hot_insulated": {"support": None,                      "notes": []},
            },
            "al_ay_cn": {
                "uninsulated":   {"support": "LS01 + WEAR PAD (WA01)", "notes": []},
                "hot_insulated": {"support": None,                      "notes": []},
            },
            "frp": {
                "uninsulated":   {"support": None, "notes": []},
                "hot_insulated": {"support": None, "notes": []},
            },
        },

        # NPS 1-1/2" - 6"
        "1.5_to_6": {
            "cs_lt": {
                "no_pwht": {
                    "uninsulated":   {"support": "LS01 + WA01", "notes": []},
                    "hot_insulated": {"support": "LS02",         "notes": []},
                },
                "pwht": {
                    "uninsulated":   {"support": "LS01 + WA01", "notes": []},
                    "hot_insulated": {"support": "LS02",         "notes": []},
                },
            },
            "ss_ds_sd_sa": {
                "uninsulated":   {"support": "LS01 + WA01",                                                    "notes": []},
                "hot_insulated": {"support": "LS02 + SH03  OR  SH01/SH04 + WEAR PAD (WA01)",  "notes": [5]},
            },
            "al_ay_cn": {
                "uninsulated":   {"support": "LS01 + WA01",                                                    "notes": []},
                "hot_insulated": {"support": "LS02 + SH03  OR  SH01/SH04 + WEAR PAD (WA01)",  "notes": [5]},
            },
            "frp": {
                "uninsulated":   {"support": None, "notes": []},
                "hot_insulated": {"support": None, "notes": []},
            },
        },

        # NPS 8" - 10"
        "8_to_10": {
            "cs_lt": {
                "no_pwht": {
                    "uninsulated":   {"support": "LS01 + WA01", "notes": []},
                    "hot_insulated": {"support": "LS03",         "notes": []},
                },
                "pwht": {
                    "uninsulated":   {"support": "LS01 + WA01", "notes": []},
                    "hot_insulated": {"support": "LS03",         "notes": []},
                },
            },
            "ss_ds_sd_sa": {
                "uninsulated":   {"support": "LS01 + WA01",                                                    "notes": []},
                "hot_insulated": {"support": "LS02 + SH03  OR  SH01/SH04 + WEAR PAD (WA01)",  "notes": [5]},
            },
            "al_ay_cn": {
                "uninsulated":   {"support": "LS01 + WA01",                                                    "notes": []},
                "hot_insulated": {"support": "LS02 + SH03  OR  SH01/SH04 + WEAR PAD (WA01)",  "notes": [5]},
            },
            "frp": {
                "uninsulated":   {"support": None, "notes": []},
                "hot_insulated": {"support": None, "notes": []},
            },
        },

        # NPS 12" - 48"
        "12_to_48": {
            "cs_lt": {
                "no_pwht": {
                    "uninsulated":   {"support": "LS01 + WA01", "notes": []},
                    "hot_insulated": {"support": "LS03",         "notes": []},
                },
                "pwht": {
                    "uninsulated":   {"support": "LS01 + WA01", "notes": []},
                    "hot_insulated": {"support": "LS03",         "notes": []},
                },
            },
            "ss_ds_sd_sa": {
                "uninsulated":   {"support": "LS01 + WA01",                                                    "notes": []},
                "hot_insulated": {"support": "LS02 + SH03  OR  SH01/SH04 + WEAR PAD (WA01)",  "notes": [5]},
            },
            "al_ay_cn": {
                "uninsulated":   {"support": "LS01 + WA01",                                                    "notes": []},
                "hot_insulated": {"support": "LS02 + SH03  OR  SH01/SH04 + WEAR PAD (WA01)",  "notes": [5]},
            },
            "frp": {
                "uninsulated":   {"support": None, "notes": []},
                "hot_insulated": {"support": None, "notes": []},
            },
        },
    },

    # =========================================================================
    # TABLE 16  -  HOLD DOWN SUPPORTS
    # =========================================================================
    "hold_down": {

        # NPS 1/2" - 1"  (hot insulated = not applicable)
        "0.5_to_1": {
            "cs_lt": {
                "no_pwht": {
                    "uninsulated":   {"support": "GH02", "notes": []},
                    "hot_insulated": {"support": None,   "notes": []},
                },
                "pwht": {
                    "uninsulated":   {"support": "GH02", "notes": []},
                    "hot_insulated": {"support": None,   "notes": []},
                },
            },
            "ss_ds_sd_sa": {
                "uninsulated":   {"support": "GH02 + PR01/PR02 or WA01 (if applicable)", "notes": []},
                "hot_insulated": {"support": None,                                        "notes": []},
            },
            "al_ay_cn": {
                "uninsulated":   {"support": "GH02 + PR01/PR02 or WA01 (if applicable)", "notes": []},
                "hot_insulated": {"support": None,                                        "notes": []},
            },
            "frp": {
                "uninsulated":   {"support": None, "notes": []},
                "hot_insulated": {"support": None, "notes": []},
            },
        },

        # NPS 1-1/2" - 6"
        "1.5_to_6": {
            "cs_lt": {
                "no_pwht": {
                    "uninsulated":   {"support": "GH02", "notes": []},
                    "hot_insulated": {"support": "GH01", "notes": []},
                },
                "pwht": {
                    "uninsulated":   {"support": "GH02", "notes": []},
                    "hot_insulated": {"support": "GH01", "notes": []},
                },
            },
            "ss_ds_sd_sa": {
                "uninsulated":   {"support": "GH02 + PR01/PR02 or WA01 (if applicable)", "notes": []},
                "hot_insulated": {"support": "GH01",                                      "notes": []},
            },
            "al_ay_cn": {
                "uninsulated":   {"support": "GH02 + PR01/PR02 or WA01 (if applicable)", "notes": []},
                "hot_insulated": {"support": "GH01",                                      "notes": []},
            },
            "frp": {
                "uninsulated":   {"support": None, "notes": []},
                "hot_insulated": {"support": None, "notes": []},
            },
        },

        # NPS 8" - 10"
        "8_to_10": {
            "cs_lt": {
                "no_pwht": {
                    "uninsulated":   {"support": "GH02", "notes": []},
                    "hot_insulated": {"support": "GH01", "notes": []},
                },
                "pwht": {
                    "uninsulated":   {"support": "GH02", "notes": []},
                    "hot_insulated": {"support": "GH01", "notes": []},
                },
            },
            "ss_ds_sd_sa": {
                "uninsulated":   {"support": "GH02 + PR01/PR02 or WA01 (if applicable)", "notes": []},
                "hot_insulated": {"support": "GH01",                                      "notes": []},
            },
            "al_ay_cn": {
                "uninsulated":   {"support": "GH02 + PR01/PR02 or WA01 (if applicable)", "notes": []},
                "hot_insulated": {"support": "GH01",                                      "notes": []},
            },
            "frp": {
                "uninsulated":   {"support": None, "notes": []},
                "hot_insulated": {"support": None, "notes": []},
            },
        },

        # NPS 12" - 48"  (uninsulated = not applicable for all materials)
        "12_to_48": {
            "cs_lt": {
                "no_pwht": {
                    "uninsulated":   {"support": None,   "notes": []},
                    "hot_insulated": {"support": "GH01", "notes": []},
                },
                "pwht": {
                    "uninsulated":   {"support": None,   "notes": []},
                    "hot_insulated": {"support": "GH01", "notes": []},
                },
            },
            "ss_ds_sd_sa": {
                "uninsulated":   {"support": None,   "notes": []},
                "hot_insulated": {"support": "GH01", "notes": []},
            },
            "al_ay_cn": {
                "uninsulated":   {"support": None,   "notes": []},
                "hot_insulated": {"support": "GH01", "notes": []},
            },
            "frp": {
                "uninsulated":   {"support": None, "notes": []},
                "hot_insulated": {"support": None, "notes": []},
            },
        },
    },
}


# =============================================================================
# ENGINEERING NOTES  (from footnotes of Tables 15 & 16)
# =============================================================================
NOTES = {
    1: ("NOTE 1 - Non-insulated pipes should rest directly on supporting steel, "
        "EXCEPT when pipe shoes are required to protect the pipe wall: "
        "(a) NPS > 24\", "
        "(b) CS/LT pipes with wall thickness < Schedule 20, "
        "(c) SS pipes with wall thickness < Schedule 10S."),

    2: ("NOTE 2 - Wear Pad required for thin-wall pipes: "
        "CS/LT at NPS 18\" and above; "
        "SS/DS/SD/AS/AL/AY at NPS 1-1/2\" and above. "
        "Contact-length adequacy must be verified by Stress Engineer."),

    3: ("NOTE 3 - For lines requiring clamped shoes, at axial stop locations "
        "use a combination of Welded Shoe + Wear Pad (if required) instead."),

    4: ("NOTE 4 - For axial stops on bare SS lines, axial stop members shall be SS "
        "(same as parent pipe), or use a combination of Wear Pad + Axial Stop."),

    5: ("NOTE 5 - Applicable only for Line Stop on SS/DS/SD/SA/AL/AY lines "
        "with operating temperature >= 750 degF."),
}
