"""
Safe numeric helpers for financial calculations.

These helpers intentionally coerce missing, blank, non-finite, and non-numeric
values to conservative defaults so analysis/report generation never crashes on
partial market data.
"""

from __future__ import annotations

import math
from typing import Any


def safe_number(value: Any, default: float = 0.0) -> float:
    """Return value as float, or default when value is missing/non-numeric."""
    if value is None:
        return default
    if isinstance(value, bool):
        return float(value)
    if isinstance(value, (int, float)):
        number = float(value)
    elif isinstance(value, str):
        cleaned = value.strip().replace(",", "").replace("HK$", "").replace("$", "")
        if cleaned.endswith("%"):
            cleaned = cleaned[:-1]
        if not cleaned:
            return default
        # Treat common placeholder strings as missing
        if cleaned.upper() in {"N/A", "NA", "-", "--", "NONE", "NULL", "NAN", "N.A.", "N.A"}:
            return default
        try:
            number = float(cleaned)
        except ValueError:
            return default
    else:
        return default

    if math.isnan(number) or math.isinf(number):
        return default
    return number


def safe_divide(numerator: Any, denominator: Any, default: float = 0.0) -> float:
    """Safely divide numeric values without ZeroDivisionError or TypeError."""
    num = safe_number(numerator, default)
    den = safe_number(denominator, 0.0)
    if den == 0:
        return default
    return num / den


def safe_multiply(a: Any, b: Any, default: float = 0.0) -> float:
    """Safely multiply numeric values."""
    return safe_number(a, default) * safe_number(b, default)


def safe_percentage(value: Any, default: float = 0.0) -> float:
    """Return value as a decimal percentage-friendly number."""
    return safe_number(value, default)


# Aliases for backward compatibility with v4.0 modules
safe_float = safe_number
