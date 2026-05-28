"""
core/hkex_parser.py

HKEX + Earnings Intelligence Layer — v1.3

Placeholder architecture for HKEX announcement and earnings intelligence.
When no verified filing data is available, returns explicit "資料待補充" —
never fabricates filing summaries, management outlooks, or earnings figures.
"""

from __future__ import annotations

from typing import Any


NOT_CONNECTED = "資料待補充"
BOUNDARY_NOTE = "本節只使用已接入及已驗證的公告或業績資料，不會生成未經驗證的公告摘要。"


def _safe_str(value: Any, fallback: str = NOT_CONNECTED) -> str:
    text = str(value or "").strip()
    return text if text else fallback


def fetch_hkex_announcements(
    ticker: str,
    max_items: int = 5,
) -> dict[str, Any]:
    """
    Fetch HKEX announcements for a given ticker.

    Currently a placeholder — returns not-connected result.
    When a verified HKEX API is integrated, this function will parse
    real filing data without fabrication.

    Returns:
        dict with announcements list and connection status.
    """
    # Placeholder: no live HKEX API connected
    return {
        "ticker": ticker,
        "status": "未接入",
        "is_connected": False,
        "announcements": [],
        "latest_announcement": NOT_CONNECTED,
        "announcement_count": 0,
        "boundary_note": BOUNDARY_NOTE,
        "not_connected_message": (
            "暫未接入 HKEX 公告資料庫，本節不生成未經驗證的公告摘要。"
        ),
    }


def fetch_earnings_summary(
    ticker: str,
    financial_data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Build an earnings summary from available financial data.

    Uses Python-calculated financial data only.
    Does not fabricate management outlooks or earnings guidance.

    Args:
        ticker: HK stock ticker
        financial_data: dict from MarketDataAgent / FinancialAnalystAgent

    Returns:
        dict with earnings summary fields.
    """
    fin = financial_data or {}

    # Extract available earnings data from financial_data
    revenue = fin.get("revenue_ttm") or fin.get("revenue")
    net_income = fin.get("net_income_ttm") or fin.get("net_income")
    ebitda = fin.get("ebitda")
    gross_margin = fin.get("gross_margin")
    net_margin = fin.get("net_margin")
    roe = fin.get("roe")

    def _fmt_num(v: Any) -> str:
        from core.utils import format_currency_hkd
        from core.safe_math import safe_number
        n = safe_number(v, 0.0)
        return format_currency_hkd(n) if n > 0 else NOT_CONNECTED

    def _fmt_pct(v: Any) -> str:
        from core.safe_math import safe_number
        n = safe_number(v, 0.0)
        return f"{n * 100:.1f}%" if n != 0 else NOT_CONNECTED

    has_data = any(v is not None and v != 0 for v in [revenue, net_income, ebitda])

    return {
        "ticker": ticker,
        "has_earnings_data": has_data,
        "status": "已取得財務資料" if has_data else "未接入",
        "revenue_ttm": _fmt_num(revenue),
        "net_income_ttm": _fmt_num(net_income),
        "ebitda": _fmt_num(ebitda),
        "gross_margin": _fmt_pct(gross_margin),
        "net_margin": _fmt_pct(net_margin),
        "roe": _fmt_pct(roe),
        "management_outlook": NOT_CONNECTED,
        "earnings_guidance": NOT_CONNECTED,
        "risk_factors": [],
        "boundary_note": (
            "業績摘要只引用 Python 計算的財務數值，"
            "管理層指引及業績預測需以公司正式公告核對，系統不生成未經驗證的預測。"
        ),
        "not_connected_message": (
            "管理層指引及業績預測暫未接入，系統不生成未經驗證的公告摘要。"
        ),
    }


def build_hkex_intelligence(
    ticker: str,
    market_data: dict[str, Any] | None = None,
    financial_data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Combine HKEX announcements and earnings summary into a single intelligence dict.

    This is the main entry point for the HKEX intelligence layer.
    All data is Python-sourced or explicitly marked as not connected.
    """
    announcements = fetch_hkex_announcements(ticker)
    earnings = fetch_earnings_summary(ticker, financial_data or market_data or {})

    has_any_data = announcements.get("is_connected") or earnings.get("has_earnings_data")

    return {
        "title": "HKEX 公告與業績分析",
        "ticker": ticker,
        "has_data": has_any_data,
        "announcements": announcements,
        "earnings": earnings,
        "analysis_boundary": BOUNDARY_NOTE,
        "status_summary": (
            f"公告資料：{announcements.get('status', '未接入')} | "
            f"業績資料：{earnings.get('status', '未接入')}"
        ),
    }
