"""
core/data_confidence.py

Data confidence controls for market-data driven report generation.
"""

from __future__ import annotations

from typing import Any, Dict

from core.safe_math import safe_number


HIGH = "HIGH"
MEDIUM = "MEDIUM"
LOW = "LOW"
INVALID = "INVALID"

INVALID_MARKET_DATA_MESSAGE = "該股票代號的資料驗證未完成。\n系統已停止進階財務分析。"
PARTIAL_DATA_WARNING = "部分市場或財務資料未能取得，\n系統已使用保守假設進行分析。"
INVALID_PDF_NOTICE = "本報告未能取得有效市場資料，\n內容僅供系統測試用途。"


CONFIDENCE_LABELS = {
    HIGH: "🟢 高可信度",
    MEDIUM: "🟡 部分資料缺失",
    LOW: "🟡 部分資料缺失",
    INVALID: "🔴 資料驗證未完成",
}


def confidence_label(level: str) -> str:
    return CONFIDENCE_LABELS.get(level, CONFIDENCE_LABELS[LOW])


def _has_text(value: Any) -> bool:
    text = str(value or "").strip()
    return bool(text) and text.upper() not in {"N/A", "NONE", "NULL"}


def _has_positive_number(value: Any) -> bool:
    return safe_number(value, 0.0) > 0


def assess_market_data_confidence(data: Dict[str, Any]) -> str:
    """Assess whether fetched market data is usable for financial narration."""
    if not data:
        return INVALID

    if data.get("invalid_symbol") or data.get("data_confidence") == INVALID:
        return INVALID

    has_company_name = _has_text(data.get("company_name"))
    has_price = _has_positive_number(data.get("current_price"))
    has_market_cap = _has_positive_number(data.get("market_cap"))
    has_ticker_metadata = _has_text(data.get("ticker")) and _has_text(data.get("exchange"))

    if not any([has_company_name, has_price, has_market_cap, has_ticker_metadata]):
        return INVALID

    if not has_company_name or not has_price or not has_market_cap or not has_ticker_metadata:
        return LOW

    if data.get("missing_data_flags"):
        return LOW

    return HIGH


def invalid_market_data(ticker: str, reason: str = "") -> Dict[str, Any]:
    return {
        "ticker": ticker,
        "data_source": "NO VALID MARKET DATA",
        "data_confidence": INVALID,
        "data_confidence_label": confidence_label(INVALID),
        "invalid_symbol": True,
        "validation_reason": reason or "Market data provider returned no valid symbol metadata.",
        "is_demo": False,
        "company_name": "",
        "sector": "",
        "currency": "HKD",
        "exchange": "",
        "current_price": 0,
        "prev_close": 0,
        "day_high": 0,
        "day_low": 0,
        "volume": 0,
        "market_cap": 0,
        "pe_ratio": 0,
        "pb_ratio": 0,
        "dividend_yield": 0,
        "52w_high": 0,
        "52w_low": 0,
        "revenue_ttm": 0,
        "net_income_ttm": 0,
        "total_debt": 0,
        "cash": 0,
        "ebitda": 0,
        "gross_margin": 0,
        "net_margin": 0,
        "roe": 0,
        "debt_to_equity": 0,
        "current_ratio": 0,
        "beta": 0,
        "missing_data_flags": ["invalid_or_unconfirmed_ticker"],
        "data_warning": INVALID_MARKET_DATA_MESSAGE,
    }
