"""Backward-compatibility shim.

Column/format detection now uses the final standalone tool's detection engine
verbatim (``format_detector.py``). This module re-exports its public functions so
any legacy import of ``column_mapper`` keeps working.
"""

from __future__ import annotations

from .format_detector import (  # noqa: F401
    apply_detection_to_rules,
    detect_format,
    load_mapping,
)

__all__ = ["apply_detection_to_rules", "detect_format", "load_mapping"]
