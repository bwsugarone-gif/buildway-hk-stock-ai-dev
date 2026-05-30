"""
core/market_snapshot_engine.py
Unified Market Snapshot Engine — v4.0 Hardening Layer

Single source of truth for all market data display.
All UI sections and PDF must read from report_package["market_snapshot"].
No component should fetch or compute market data independently.

Standard keys (always present, never None):
  current_price, day_high, day_low, volume, market_cap,
  pe, pb, dividend_yield, beta,
  fifty_two_week_high, fifty_two_week_low, fifty_two_week_position,
  source, confidence
"""

from core.safe_math import safe_float, safe_divide


# ── Sentinel for missing data ─────────────────────────────────────────────────
_MISSING = "未取得"


def _fmt_price(val) -> str:
    """Format a price value, return '未取得' if missing."""
    try:
        f = float(val)
        if f > 0:
            return f"HK${f:,.2f}"
    except (TypeError, ValueError):
        pass
    return _MISSING


def _fmt_num(val, decimals=2, suffix="") -> str:
    """Format a numeric value."""
    try:
        f = float(val)
        if f != 0:
            return f"{f:,.{decimals}f}{suffix}"
    except (TypeError, ValueError):
        pass
    return _MISSING


def _fmt_pct(val) -> str:
    """Format a percentage value."""
    try:
        f = float(val)
        return f"{f:.2f}%"
    except (TypeError, ValueError):
        pass
    return _MISSING


def _fmt_cap(val) -> str:
    """Format market cap in HKD billions/trillions."""
    try:
        f = float(val)
        if f >= 1e12:
            return f"HK${f/1e12:.2f}萬億"
        elif f >= 1e8:
            return f"HK${f/1e8:.1f}億"
        elif f > 0:
            return f"HK${f:,.0f}"
    except (TypeError, ValueError):
        pass
    return _MISSING


def build_market_snapshot(report_package: dict) -> dict:
    """
    Build the unified market snapshot from report_package.
    Stores result in report_package["market_snapshot"] and returns it.

    All UI and PDF components must use this snapshot — never re-fetch.
    If 52-week data is missing, ALL display locations show '未取得' consistently.
    """
    # Already built — return cached version
    if report_package.get("market_snapshot"):
        return report_package["market_snapshot"]

    market = report_package.get("market_data", {})
    company = report_package.get("company_metadata", {})

    # ── Raw values ────────────────────────────────────────────────────────────
    current_price = safe_float(market.get("current_price") or market.get("price"))
    day_high      = safe_float(market.get("day_high") or market.get("high"))
    day_low       = safe_float(market.get("day_low") or market.get("low"))
    volume        = safe_float(market.get("volume"))
    market_cap    = safe_float(market.get("market_cap") or market.get("marketCap"))
    pe            = safe_float(market.get("pe_ratio") or market.get("pe") or market.get("trailingPE"))
    pb            = safe_float(market.get("pb_ratio") or market.get("pb") or market.get("priceToBook"))
    div_yield     = safe_float(market.get("dividend_yield") or market.get("dividendYield"))
    beta          = safe_float(market.get("beta"))
    wk52_high     = safe_float(market.get("fifty_two_week_high") or market.get("52WeekHigh") or market.get("fiftyTwoWeekHigh"))
    wk52_low      = safe_float(market.get("fifty_two_week_low") or market.get("52WeekLow") or market.get("fiftyTwoWeekLow"))

    # ── 52-week position (0-100%) ─────────────────────────────────────────────
    wk52_position = _MISSING
    if current_price and wk52_high and wk52_low and (wk52_high - wk52_low) > 0:
        pos = (current_price - wk52_low) / (wk52_high - wk52_low) * 100
        wk52_position = f"{pos:.1f}%"

    # ── Confidence ────────────────────────────────────────────────────────────
    data_confidence = report_package.get("report_metadata", {}).get("data_confidence", "LOW")

    # ── Build snapshot ────────────────────────────────────────────────────────
    snapshot = {
        # Raw numeric values (for calculations)
        "_raw": {
            "current_price": current_price,
            "day_high": day_high,
            "day_low": day_low,
            "volume": volume,
            "market_cap": market_cap,
            "pe": pe,
            "pb": pb,
            "dividend_yield": div_yield,
            "beta": beta,
            "fifty_two_week_high": wk52_high,
            "fifty_two_week_low": wk52_low,
        },
        # Formatted display values (for UI and PDF)
        "current_price":          _fmt_price(current_price),
        "day_high":               _fmt_price(day_high),
        "day_low":                _fmt_price(day_low),
        "volume":                 _fmt_num(volume, 0) if volume else _MISSING,
        "market_cap":             _fmt_cap(market_cap),
        "pe":                     _fmt_num(pe, 1, "x") if pe else _MISSING,
        "pb":                     _fmt_num(pb, 2, "x") if pb else _MISSING,
        "dividend_yield":         _fmt_pct(div_yield) if div_yield else _MISSING,
        "beta":                   _fmt_num(beta, 2) if beta else _MISSING,
        # 52-week data — consistent across ALL display locations
        "fifty_two_week_high":    _fmt_price(wk52_high) if wk52_high else _MISSING,
        "fifty_two_week_low":     _fmt_price(wk52_low) if wk52_low else _MISSING,
        "fifty_two_week_position": wk52_position,
        # Metadata
        "source":     "Yahoo Finance / yfinance",
        "confidence": data_confidence,
        "ticker":     report_package.get("report_metadata", {}).get("stock_code", ""),
        "company_name": (
            company.get("name_zh") or
            company.get("name_en") or
            "未知公司"
        ),
    }

    # Cache in report_package
    report_package["market_snapshot"] = snapshot
    return snapshot


def get_snapshot_field(report_package: dict, field: str) -> str:
    """
    Safe accessor for any snapshot field.
    Always returns a string — never None, never '—'.
    """
    snapshot = build_market_snapshot(report_package)
    val = snapshot.get(field, _MISSING)
    if val is None or str(val).strip() in ("", "None", "nan", "—"):
        return _MISSING
    return str(val)
