"""Boundary-case tests for the SCLL Chart 1 / Chart 2 criticality thresholds.

These pin the classifier to the EXACT translated values from the JESA criticality
reference document (charts.docx), including the exclusive boundary semantics:

    Level 3 : T <= A
    Level 2 : A <  T <= B
    Level 1 : T >  B

where per size band (l2_threshold = A, l1_threshold = B). Charts 3/4 keep their
original inclusive (>=) semantics and are not covered here.
"""

import pandas as pd
import pytest

from scll_phase1_module_final.backend import rules_engine
from scll_phase1_module_final.backend.classifier import (
    MATERIAL_MAP_PATH,
    RULES_PATH,
)
from scll_phase1_module_final.backend.parser import load_material_map, load_rules


@pytest.fixture(scope="module")
def rules():
    return load_rules(str(RULES_PATH))


@pytest.fixture(scope="module")
def material_map():
    return load_material_map(str(MATERIAL_MAP_PATH))


def classify(material, size, temp, rules, material_map, **extra):
    row = {"material": material, "size": str(size), "design_temperature": str(temp)}
    row.update(extra)
    result = rules_engine.classify_row(pd.Series(row), material_map, rules)
    return result["level"]


# ─────────────────────────────────────────────────────────────────────────────
# Chart 1 — Carbon / Low-Alloy Steel  (material code BA1 -> CS -> chart_1)
# Table:
#   2-4"  : L3 T<=140 | L2 140<T<=270 | L1 T>270
#   6"    : L3 T<=140 | L2 140<T<=240 | L1 T>240
#   8-12" : L3 T<=80  | L2 80<T<=240  | L1 T>240
#   14"   : L3 T<=40  | L2 40<T<=180  | L1 T>180  (gap 140-180 resolved to L2)
#   16"   : L3 T<=40  | L2 40<T<=140  | L1 T>140
#   18"+  : always L1
# ─────────────────────────────────────────────────────────────────────────────

CHART1_CASES = [
    # size, temp, expected level
    (2, 140, "Level 3"), (2, 141, "Level 2"), (2, 270, "Level 2"), (2, 271, "Level 1"),
    (3, 140, "Level 3"), (3, 271, "Level 1"),
    (4, 140, "Level 3"), (4, 270, "Level 2"), (4, 271, "Level 1"),
    (6, 140, "Level 3"), (6, 141, "Level 2"), (6, 240, "Level 2"), (6, 241, "Level 1"),
    (8, 80, "Level 3"), (8, 81, "Level 2"), (8, 240, "Level 2"), (8, 241, "Level 1"),
    (10, 80, "Level 3"), (10, 240, "Level 2"), (10, 241, "Level 1"),
    (12, 80, "Level 3"), (12, 240, "Level 2"), (12, 241, "Level 1"),
    (14, 40, "Level 3"), (14, 41, "Level 2"), (14, 160, "Level 2"),  # gap resolved -> L2
    (14, 180, "Level 2"), (14, 181, "Level 1"),
    (16, 40, "Level 3"), (16, 140, "Level 2"), (16, 141, "Level 1"),
    (18, -50, "Level 1"), (18, 0, "Level 1"), (18, 300, "Level 1"),
]


@pytest.mark.parametrize("size,temp,expected", CHART1_CASES)
def test_chart_1_boundaries(size, temp, expected, rules, material_map):
    assert classify("BA1", size, temp, rules, material_map) == expected


# ─────────────────────────────────────────────────────────────────────────────
# Chart 2 — Other materials  (material code BD1 -> SS -> chart_2)
# Table:
#   2"    : L3 T<=140 | L2 140<T<=270 | L1 T>270
#   3"    : L3 T<=140 | L2 140<T<=180 | L1 T>180
#   4"    : L3 T<=80  | L2 80<T<=180  | L1 T>180
#   6-8"  : L3 T<=80  | L2 80<T<=140  | L1 T>140
#   10-14": L3 T<=40  | L2 40<T<=80   | L1 T>80
#   16"+  : always L1
# ─────────────────────────────────────────────────────────────────────────────

CHART2_CASES = [
    (2, 140, "Level 3"), (2, 141, "Level 2"), (2, 270, "Level 2"), (2, 271, "Level 1"),
    (3, 140, "Level 3"), (3, 180, "Level 2"), (3, 181, "Level 1"),
    (4, 80, "Level 3"), (4, 81, "Level 2"), (4, 180, "Level 2"), (4, 181, "Level 1"),
    (6, 80, "Level 3"), (6, 140, "Level 2"), (6, 141, "Level 1"),
    (8, 80, "Level 3"), (8, 140, "Level 2"), (8, 141, "Level 1"),
    (10, 40, "Level 3"), (10, 41, "Level 2"), (10, 80, "Level 2"), (10, 81, "Level 1"),
    (12, 40, "Level 3"), (12, 80, "Level 2"), (12, 81, "Level 1"),
    (14, 40, "Level 3"), (14, 80, "Level 2"), (14, 81, "Level 1"),
    (16, -50, "Level 1"), (16, 0, "Level 1"),
    (18, 300, "Level 1"),
]


@pytest.mark.parametrize("size,temp,expected", CHART2_CASES)
def test_chart_2_boundaries(size, temp, expected, rules, material_map):
    assert classify("BD1", size, temp, rules, material_map) == expected


# ─────────────────────────────────────────────────────────────────────────────
# Reason strings must surface the exact chart thresholds.
# ─────────────────────────────────────────────────────────────────────────────

def test_chart_1_reason_mentions_exact_threshold(rules, material_map):
    row = pd.Series({"material": "BA1", "size": "6", "design_temperature": "180"})
    result = rules_engine.classify_row(row, material_map, rules)
    assert result["level"] == "Level 2"
    assert "Chart 1" in result["reason"]
    # 6" band: L2 140<T<=240, L1 T>240
    assert "T>240" in result["reason"]
    assert "140<T<=240" in result["reason"]


def test_chart_2_reason_mentions_exact_threshold(rules, material_map):
    row = pd.Series({"material": "BD1", "size": "3", "design_temperature": "160"})
    result = rules_engine.classify_row(row, material_map, rules)
    assert result["level"] == "Level 2"
    assert "Chart 2" in result["reason"]
    # 3" band: L2 140<T<=180, L1 T>180
    assert "T>180" in result["reason"]


# ─────────────────────────────────────────────────────────────────────────────
# Level 1 exception flags (document item 5 list)
# ─────────────────────────────────────────────────────────────────────────────

def test_frp_material_is_level_1(rules, material_map):
    # Non-metallic -> Level 1 regardless of size / temperature (Step 1)
    assert classify("HDPE", 2, 20, rules, material_map) == "Level 1"


def test_jacketed_exception_forces_level_1(rules, material_map):
    # A CS 2" at 20C would be Level 3 by chart; jacketed flag overrides to Level 1
    assert classify("BA1", 2, 20, rules, material_map) == "Level 3"
    assert classify("BA1", 2, 20, rules, material_map, jacketed="Yes") == "Level 1"


def test_large_deflection_exception_forces_level_1(rules, material_map):
    # Newly added exception (external moments / large deflections)
    assert classify("BA1", 2, 20, rules, material_map, large_deflection="Yes") == "Level 1"


def test_vertical_tower_requires_size_threshold(rules, material_map):
    # Vertical-tower exception only fires at D >= 4"
    assert classify("BA1", 2, 20, rules, material_map, vertical_tower="Yes") == "Level 3"
    assert classify("BA1", 4, 20, rules, material_map, vertical_tower="Yes") == "Level 1"


def test_vacuum_exception_has_no_size_limit(rules, material_map):
    # Reference document: any vacuum line -> Level 1, regardless of size.
    assert classify("BA1", 2, 20, rules, material_map) == "Level 3"
    assert classify("BA1", 2, 20, rules, material_map, vacuum="Yes") == "Level 1"   # small bore
    assert classify("BA1", 8, 20, rules, material_map, vacuum="Yes") == "Level 1"   # large bore


def test_vacuum_exception_fires_with_missing_size(rules, material_map):
    # Vacuum should still force Level 1 even if the size cell is blank.
    row = pd.Series({"material": "BA1", "size": "", "design_temperature": "20", "vacuum": "Yes"})
    assert rules_engine.classify_row(row, material_map, rules)["level"] == "Level 1"
