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
VALID_TICKER_PRICE_UNAVAILABLE = "VALID_TICKER_PRICE_UNAVAILABLE"

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
    if level == VALID_TICKER_PRICE_UNAVAILABLE:
        return "公司資料已驗證，市場價格暫時未能取得"
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
    if data.get("valid_ticker_price_unavailable") or data.get("price_unavailable"):
        return LOW

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


def valid_ticker_price_unavailable_data(
    ticker: str,
    metadata: Dict[str, Any],
    reason: str = "",
) -> Dict[str, Any]:
    """Return a non-INVALID payload for validated tickers with no live price."""
    name_zh = metadata.get("name_zh", "")
    name_en = metadata.get("name_en", "")
    business = (
        metadata.get("business_summary")
        or metadata.get("business")
        or metadata.get("business_zh")
        or metadata.get("business_en")
        or ""
    )
    message = "公司資料已驗證，市場價格暫時未能取得"
    return {
        "ticker": ticker,
        "data_source": "HK Stock Master Data (price unavailable fallback)",
        "data_status": VALID_TICKER_PRICE_UNAVAILABLE,
        "data_confidence": LOW,
        "data_confidence_label": confidence_label(VALID_TICKER_PRICE_UNAVAILABLE),
        "valid_ticker_price_unavailable": True,
        "price_unavailable": True,
        "market_data_status": "price_unavailable",
        "validation_reason": reason or message,
        "fallback_reason": reason,
        "is_demo": True,
        "is_live": False,
        "company_metadata": dict(metadata),
        "company_name": name_zh or name_en,
        "company_name_zh": name_zh,
        "company_name_en": name_en,
        "sector": metadata.get("sector", ""),
        "business": business,
        "business_summary": business,
        "currency": "HKD",
        "exchange": "HKEX",
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
        "missing_data_flags": ["market_price_unavailable", "market_cap_unavailable"],
        "data_warning": message,
        "metadata_source": "hk_stock_master_data",
    }
