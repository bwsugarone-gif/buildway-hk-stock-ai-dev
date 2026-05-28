"""
core/data_normalizer.py

Data Coverage Expansion Layer — v2.0

Normalizes yfinance field aliases and applies multi-field fallback mapping
to improve coverage of PE, PB, Revenue, EBITDA, Beta, Dividend Yield,
52w Range, and Enterprise Value.

Rules:
- Never fabricate values
- Never return HK$0.00 / 0.0% / 0.00x as valid data
- If no valid value found, return None (caller decides display)
- All calculations are Python-based
"""

from __future__ import annotations

from typing import Any

from core.safe_math import safe_number


# ─── Field alias priority maps ────────────────────────────────────────────────

_PE_FIELDS = [
    "trailingPE", "forwardPE", "trailing_pe", "pe_ratio",
    "priceEarningsRatio", "price_earnings",
]

_PB_FIELDS = [
    "priceToBook", "pb_ratio", "price_book",
    "priceToBookRatio", "price_to_book",
]

_DIVIDEND_FIELDS = [
    "dividendYield", "trailingAnnualDividendYield",
    "dividend_yield", "trailing_dividend_yield",
    "fiveYearAvgDividendYield",
]

_BETA_FIELDS = [
    "beta", "beta3Year", "beta_3year",
]

_REVENUE_FIELDS = [
    "totalRevenue", "revenue_ttm", "revenue",
    "revenueQuarterlyGrowth", "annualRevenue",
]

_EBITDA_FIELDS = [
    "ebitda", "EBITDA", "ebitdaMargins",
]

_MARKET_CAP_FIELDS = [
    "marketCap", "market_cap", "enterpriseValue",
]

_W52_HIGH_FIELDS = [
    "fiftyTwoWeekHigh", "52w_high", "52WeekHigh",
    "yearHigh", "year_high",
]

_W52_LOW_FIELDS = [
    "fiftyTwoWeekLow", "52w_low", "52WeekLow",
    "yearLow", "year_low",
]

_GROSS_MARGIN_FIELDS = [
    "grossMargins", "gross_margin", "grossProfitMargin",
]

_NET_MARGIN_FIELDS = [
    "profitMargins", "net_margin", "netProfitMargin",
    "netMargin",
]

_ROE_FIELDS = [
    "returnOnEquity", "roe", "return_on_equity",
]

_CURRENT_RATIO_FIELDS = [
    "currentRatio", "current_ratio",
]

_DEBT_TO_EQUITY_FIELDS = [
    "debtToEquity", "debt_to_equity", "leverageRatio",
]

_VOLUME_FIELDS = [
    "regularMarketVolume", "volume", "averageVolume",
    "averageVolume10days", "avg_volume",
]

_PRICE_FIELDS = [
    "regularMarketPrice", "currentPrice", "current_price",
    "price", "lastPrice",
]

_PREV_CLOSE_FIELDS = [
    "regularMarketPreviousClose", "previousClose", "prev_close",
    "regularMarketClose",
]

_DAY_HIGH_FIELDS = [
    "dayHigh", "regularMarketDayHigh", "day_high",
    "highPrice",
]

_DAY_LOW_FIELDS = [
    "dayLow", "regularMarketDayLow", "day_low",
    "lowPrice",
]


# ─── Core extraction helpers ──────────────────────────────────────────────────

def _extract_first_valid(data: dict[str, Any], fields: list[str]) -> float | None:
    """
    Try each field in priority order. Return the first positive numeric value.
    Returns None if no valid value found — never returns 0.
    """
    for field in fields:
        raw = data.get(field)
        if raw is None:
            continue
        try:
            value = float(raw)
        except (TypeError, ValueError):
            continue
        if value > 0:
            return value
    return None


def _extract_ratio(data: dict[str, Any], fields: list[str]) -> float | None:
    """
    Like _extract_first_valid but allows values between 0 and 1 (e.g. margins).
    Returns None if no valid value found.
    """
    for field in fields:
        raw = data.get(field)
        if raw is None:
            continue
        try:
            value = float(raw)
        except (TypeError, ValueError):
            continue
        # Accept any non-zero value (margins can be negative)
        if value != 0.0:
            return value
    return None


# ─── Main normalizer ──────────────────────────────────────────────────────────

def normalize_market_data(raw: dict[str, Any]) -> dict[str, Any]:
    """
    Apply multi-field fallback mapping to a raw market data dict.

    Improves coverage of key financial fields by trying multiple yfinance
    field aliases in priority order. Returns a new dict with normalized fields.

    Fields that cannot be resolved are set to None (not 0.0).
    Callers should use _has_valid_display_value() before rendering.
    """
    result = dict(raw)

    # Price fields
    price = _extract_first_valid(raw, _PRICE_FIELDS)
    if price is not None:
        result["current_price"] = price

    prev_close = _extract_first_valid(raw, _PREV_CLOSE_FIELDS)
    if prev_close is not None:
        result["prev_close"] = prev_close

    day_high = _extract_first_valid(raw, _DAY_HIGH_FIELDS)
    if day_high is not None:
        result["day_high"] = day_high

    day_low = _extract_first_valid(raw, _DAY_LOW_FIELDS)
    if day_low is not None:
        result["day_low"] = day_low

    # Volume
    volume = _extract_first_valid(raw, _VOLUME_FIELDS)
    if volume is not None:
        result["volume"] = volume

    # Market cap
    market_cap = _extract_first_valid(raw, _MARKET_CAP_FIELDS)
    if market_cap is not None:
        result["market_cap"] = market_cap

    # Valuation ratios
    pe = _extract_first_valid(raw, _PE_FIELDS)
    result["pe_ratio"] = pe  # None if not available

    pb = _extract_first_valid(raw, _PB_FIELDS)
    result["pb_ratio"] = pb

    # Dividend yield — stored as decimal (0.03 = 3%)
    div = _extract_first_valid(raw, _DIVIDEND_FIELDS)
    if div is not None:
        # yfinance sometimes returns as percentage (3.0) instead of decimal (0.03)
        result["dividend_yield"] = div if div < 1.0 else div / 100.0
    else:
        result["dividend_yield"] = None

    # Beta
    beta = _extract_first_valid(raw, _BETA_FIELDS)
    result["beta"] = beta

    # 52-week range
    w52_high = _extract_first_valid(raw, _W52_HIGH_FIELDS)
    result["52w_high"] = w52_high

    w52_low = _extract_first_valid(raw, _W52_LOW_FIELDS)
    result["52w_low"] = w52_low

    # Revenue
    revenue = _extract_first_valid(raw, _REVENUE_FIELDS)
    if revenue is not None:
        result["revenue_ttm"] = revenue

    # EBITDA
    ebitda = _extract_first_valid(raw, _EBITDA_FIELDS)
    if ebitda is not None:
        result["ebitda"] = ebitda

    # Margin ratios (can be negative, so use _extract_ratio)
    gross_margin = _extract_ratio(raw, _GROSS_MARGIN_FIELDS)
    result["gross_margin"] = gross_margin

    net_margin = _extract_ratio(raw, _NET_MARGIN_FIELDS)
    result["net_margin"] = net_margin

    roe = _extract_ratio(raw, _ROE_FIELDS)
    result["roe"] = roe

    # Leverage
    current_ratio = _extract_first_valid(raw, _CURRENT_RATIO_FIELDS)
    result["current_ratio"] = current_ratio

    debt_to_equity = _extract_first_valid(raw, _DEBT_TO_EQUITY_FIELDS)
    result["debt_to_equity"] = debt_to_equity

    return result


def is_placeholder_value(value: Any) -> bool:
    """
    Return True if value is a known placeholder that should not be displayed.
    Covers: 0, 0.0, HK$0.00, 0.0%, 0.00x, N/A, None, empty string.
    """
    if value is None:
        return True
    text = str(value).strip()
    if not text:
        return True
    bad = {"0", "0.0", "0.00", "N/A", "None", "資料待補充", "暫無資料"}
    if text in bad:
        return True
    if "HK$0.00" in text or "0.0%" in text or "0.00x" in text or "0.0x" in text:
        return True
    try:
        if float(text) == 0.0:
            return True
    except (ValueError, TypeError):
        pass
    return False
