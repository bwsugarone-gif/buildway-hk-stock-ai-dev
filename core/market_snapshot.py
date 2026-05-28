"""
core/market_snapshot.py

Bloomberg-style market snapshot layer.

Extracts and structures key market KPIs from MarketDataAgent output.
All values are Python-calculated from verified market data.
No LLM involvement in numerical fields.
"""

from __future__ import annotations

from typing import Any

from core.data_confidence import INVALID
from core.safe_math import safe_number
from core.utils import format_currency_hkd, format_percentage


def _num(value: Any, default: float = 0.0) -> float:
    return safe_number(value, default)


def _fmt_price(value: Any) -> str:
    n = _num(value)
    return f"HK${n:.2f}" if n > 0 else "資料待補充"


def _fmt_pct(value: Any, decimals: int = 2) -> str:
    n = _num(value)
    if n == 0:
        return "資料待補充"
    return format_percentage(n, decimals)


def _fmt_hkd(value: Any) -> str:
    n = _num(value)
    return format_currency_hkd(n) if n > 0 else "資料待補充"


def _fmt_ratio(value: Any, suffix: str = "x") -> str:
    n = _num(value)
    return f"{n:.2f}{suffix}" if n > 0 else "資料待補充"


def _fmt_volume(value: Any) -> str:
    n = _num(value)
    if n <= 0:
        return "資料待補充"
    if n >= 1_000_000_000:
        return f"{n / 1_000_000_000:.2f}B"
    if n >= 1_000_000:
        return f"{n / 1_000_000:.2f}M"
    if n >= 1_000:
        return f"{n / 1_000:.1f}K"
    return f"{n:,.0f}"


def _price_change_pct(current: float, prev_close: float) -> float:
    """Calculate day change % from current price and previous close."""
    if prev_close <= 0 or current <= 0:
        return 0.0
    return (current - prev_close) / prev_close


def _snapshot_confidence(market_data: dict[str, Any]) -> str:
    """
    Derive snapshot confidence from market data confidence.
    Separate from main data_confidence — only reflects snapshot KPI completeness.
    """
    if market_data.get("data_confidence") == INVALID:
        return "無效"
    price = _num(market_data.get("current_price"))
    market_cap = _num(market_data.get("market_cap"))
    if price > 0 and market_cap > 0:
        return "高"
    if price > 0 or market_cap > 0:
        return "中"
    return "低"


def build_market_snapshot(market_data: dict[str, Any]) -> dict[str, Any]:
    """
    Build a Bloomberg-style market snapshot from MarketDataAgent output.

    Returns a structured dict with KPI fields ready for UI cards and PDF.
    All values are Python-calculated — no LLM involvement.
    """
    if market_data.get("data_confidence") == INVALID:
        return {
            "ticker": market_data.get("ticker", "N/A"),
            "snapshot_confidence": "無效",
            "is_valid": False,
            "status_message": "股票代號資料驗證未完成，市場快照不可用。",
            "kpis": [],
            "price_section": {},
            "valuation_section": {},
            "range_section": {},
        }

    current = _num(market_data.get("current_price"))
    prev_close = _num(market_data.get("prev_close"))
    day_change_pct = _price_change_pct(current, prev_close)
    day_change_abs = current - prev_close if current > 0 and prev_close > 0 else 0.0

    # Format day change with sign
    if day_change_abs != 0:
        sign = "+" if day_change_abs >= 0 else ""
        day_change_str = f"{sign}HK${day_change_abs:.2f} ({sign}{day_change_pct * 100:.2f}%)"
    else:
        day_change_str = "資料待補充"

    dividend_yield = _num(market_data.get("dividend_yield"))
    dividend_str = f"{dividend_yield * 100:.2f}%" if dividend_yield > 0 else "資料待補充"

    beta = _num(market_data.get("beta"), 1.0)
    beta_str = f"{beta:.2f}" if beta != 0 else "資料待補充"

    w52_high = _num(market_data.get("52w_high"))
    w52_low = _num(market_data.get("52w_low"))
    w52_range_str = (
        f"HK${w52_low:.2f} – HK${w52_high:.2f}"
        if w52_high > 0 and w52_low > 0
        else "資料待補充"
    )

    # Position within 52-week range (0% = at low, 100% = at high)
    w52_position: str = "資料待補充"
    if w52_high > w52_low > 0 and current > 0:
        pos = (current - w52_low) / (w52_high - w52_low) * 100
        w52_position = f"{pos:.1f}%（52週區間位置）"

    snapshot_conf = _snapshot_confidence(market_data)

    # Flat KPI list for UI cards (label, value, delta)
    kpis: list[dict[str, str]] = [
        {"label": "現價", "value": _fmt_price(current), "delta": day_change_str},
        {"label": "今日高", "value": _fmt_price(market_data.get("day_high")), "delta": ""},
        {"label": "今日低", "value": _fmt_price(market_data.get("day_low")), "delta": ""},
        {"label": "成交量", "value": _fmt_volume(market_data.get("volume")), "delta": ""},
        {"label": "市值", "value": _fmt_hkd(market_data.get("market_cap")), "delta": ""},
        {"label": "市盈率 (P/E)", "value": _fmt_ratio(market_data.get("pe_ratio")), "delta": ""},
        {"label": "市帳率 (P/B)", "value": _fmt_ratio(market_data.get("pb_ratio")), "delta": ""},
        {"label": "股息率", "value": dividend_str, "delta": ""},
        {"label": "Beta", "value": beta_str, "delta": ""},
        {"label": "52週高低", "value": w52_range_str, "delta": w52_position},
    ]

    return {
        "ticker": market_data.get("ticker", "N/A"),
        "snapshot_confidence": snapshot_conf,
        "is_valid": True,
        "status_message": "",
        "data_source": market_data.get("data_source", ""),
        "is_demo": market_data.get("is_demo", True),
        "kpis": kpis,
        # Structured sections for PDF
        "price_section": {
            "現價": _fmt_price(current),
            "今日漲跌": day_change_str,
            "今日高": _fmt_price(market_data.get("day_high")),
            "今日低": _fmt_price(market_data.get("day_low")),
            "昨日收市": _fmt_price(prev_close),
            "成交量": _fmt_volume(market_data.get("volume")),
        },
        "valuation_section": {
            "市值": _fmt_hkd(market_data.get("market_cap")),
            "市盈率 (P/E)": _fmt_ratio(market_data.get("pe_ratio")),
            "市帳率 (P/B)": _fmt_ratio(market_data.get("pb_ratio")),
            "股息率": dividend_str,
            "Beta": beta_str,
        },
        "range_section": {
            "52週高低區間": w52_range_str,
            "52週區間位置": w52_position,
            "3個月價格變動": (
                f"{market_data.get('price_change_3m', 0) * 100:+.2f}%"
                if market_data.get("price_change_3m") is not None
                else "資料待補充"
            ),
        },
    }
