"""
core/utils.py
Buildway Tech (HK) Limited — Shared Utility Functions
"""

import re
import datetime
from typing import Optional
from core.safe_math import safe_divide as _safe_divide


def normalize_hk_ticker(ticker: str) -> str:
    """
    Normalize a HK stock ticker to standard yfinance format.
    Examples:
        '3416'     -> '3416.HK'
        '3416.HK'  -> '3416.HK'
        '0700'     -> '0700.HK'
        '700'      -> '0700.HK'
    """
    ticker = ticker.strip().upper()
    # Remove .HK suffix if present, then re-add
    base = ticker.replace(".HK", "").replace(".hk", "")
    # Pad to 4 digits for HK stocks
    if base.isdigit():
        if len(base) == 5 and base.startswith("0"):
            base = base[1:]
        base = base.zfill(4)
    return f"{base}.HK"


def format_currency_hkd(value: float, decimals: int = 2) -> str:
    """Format a number as HKD currency string."""
    if value is None:
        return "N/A"
    if abs(value) >= 1_000_000_000:
        return f"HK${value / 1_000_000_000:.{decimals}f}B"
    elif abs(value) >= 1_000_000:
        return f"HK${value / 1_000_000:.{decimals}f}M"
    elif abs(value) >= 1_000:
        return f"HK${value / 1_000:.{decimals}f}K"
    else:
        return f"HK${value:.{decimals}f}"


def format_percentage(value: float, decimals: int = 1) -> str:
    """Format a decimal as percentage string."""
    if value is None:
        return "N/A"
    return f"{value * 100:.{decimals}f}%"


def format_large_number(value: float) -> str:
    """Format large numbers with B/M/K suffixes."""
    if value is None:
        return "N/A"
    if abs(value) >= 1_000_000_000:
        return f"{value / 1_000_000_000:.2f}B"
    elif abs(value) >= 1_000_000:
        return f"{value / 1_000_000:.2f}M"
    elif abs(value) >= 1_000:
        return f"{value / 1_000:.1f}K"
    return str(round(value, 2))


def get_risk_label(score: int) -> str:
    """Convert numeric risk score (1-10) to Chinese label."""
    if score <= 3:
        return "低風險 🟢"
    elif score <= 6:
        return "中等風險 🟡"
    elif score <= 8:
        return "高風險 🟠"
    else:
        return "極高風險 🔴"


def get_risk_color(score: int) -> str:
    """Return hex color for risk score."""
    if score <= 3:
        return "#27AE60"
    elif score <= 6:
        return "#F39C12"
    elif score <= 8:
        return "#E67E22"
    else:
        return "#C0392B"


def get_timestamp() -> str:
    """Return current HK timestamp string."""
    now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8)))
    return now.strftime("%Y年%m月%d日 %H:%M HKT")


def get_report_filename(ticker: str) -> str:
    """Generate a safe PDF filename for the report."""
    now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8)))
    safe_ticker = ticker.replace(".", "_").replace("/", "_")
    timestamp = now.strftime("%Y%m%d_%H%M")
    return f"Buildway_HK_Report_{safe_ticker}_{timestamp}.pdf"


def validate_hk_ticker(ticker: str) -> tuple[bool, str]:
    """
    Validate that a ticker looks like a valid HK stock code.
    Returns (is_valid, error_message).
    """
    ticker = ticker.strip().upper().replace(".HK", "")
    if not ticker:
        return False, "請輸入股票代碼"
    if not ticker.isdigit():
        return False, "香港股票代碼應為數字，例如：3416 或 0700"
    if len(ticker) > 5:
        return False, "股票代碼過長，請檢查輸入"
    return True, ""


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """Safe division that returns default if denominator is zero."""
    return _safe_divide(numerator, denominator, default)


def clamp(value: float, min_val: float, max_val: float) -> float:
    """Clamp a value between min and max."""
    return max(min_val, min(max_val, value))


def score_to_stars(score: int, max_score: int = 10) -> str:
    """Convert a score to a star rating string."""
    stars = round((score / max_score) * 5)
    return "★" * stars + "☆" * (5 - stars)


def truncate_text(text: str, max_length: int = 200) -> str:
    """Truncate text to max_length with ellipsis."""
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."
