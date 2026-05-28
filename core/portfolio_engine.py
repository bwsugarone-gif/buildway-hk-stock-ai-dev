"""
core/portfolio_engine.py

Portfolio + Compare Layer — v1.2

Provides stock comparison and portfolio allocation analysis.
All calculations are Python-based. No LLM numerical generation.
"""

from __future__ import annotations

from typing import Any

from core.safe_math import safe_number
from core.utils import format_currency_hkd, format_percentage


def _num(value: Any, default: float = 0.0) -> float:
    return safe_number(value, default)


def _fmt_hkd(value: Any) -> str:
    n = _num(value)
    return format_currency_hkd(n) if n > 0 else "資料待補充"


def _fmt_pct(value: Any, decimals: int = 1) -> str:
    n = _num(value)
    return format_percentage(n, decimals) if n != 0 else "資料待補充"


def _fmt_ratio(value: Any, suffix: str = "x") -> str:
    n = _num(value)
    return f"{n:.2f}{suffix}" if n > 0 else "資料待補充"


def _risk_label(score: float) -> str:
    if score <= 3:
        return "低風險"
    if score <= 6:
        return "中等風險"
    if score <= 8:
        return "高風險"
    return "極高風險"


def compare_stocks(
    stock_data_list: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Compare multiple stocks across valuation, risk, sector, and catalyst dimensions.

    Each item in stock_data_list should be a dict with:
    - ticker
    - market_data (from MarketDataAgent)
    - risk_analysis (from RiskManagementAgent)
    - news_catalyst (from NewsIntelligenceAgent, optional)
    - financial_analysis (from FinancialAnalystAgent, optional)

    Returns a structured comparison dict ready for UI and PDF.
    All values are Python-calculated.
    """
    if not stock_data_list:
        return _empty_compare()

    tickers = [item.get("ticker", "N/A") for item in stock_data_list]

    # Build comparison rows
    valuation_rows = _build_valuation_compare(stock_data_list)
    risk_rows = _build_risk_compare(stock_data_list)
    sector_rows = _build_sector_compare(stock_data_list)
    catalyst_rows = _build_catalyst_compare(stock_data_list)

    # Summary: best value, lowest risk
    best_value_ticker = _find_best_value(stock_data_list)
    lowest_risk_ticker = _find_lowest_risk(stock_data_list)

    return {
        "title": "股票比較分析",
        "tickers": tickers,
        "count": len(tickers),
        "valuation_compare": valuation_rows,
        "risk_compare": risk_rows,
        "sector_compare": sector_rows,
        "catalyst_compare": catalyst_rows,
        "summary": {
            "best_value": best_value_ticker,
            "lowest_risk": lowest_risk_ticker,
            "note": "比較分析只基於 Python 計算數值，不由 LLM 生成結論。",
        },
        "analysis_note": (
            "股票比較分析基於各股票的市場資料、財務比率及風險分數，"
            "所有數值由 Python 計算，不構成投資建議。"
        ),
    }


def _build_valuation_compare(stock_data_list: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for item in stock_data_list:
        ticker = item.get("ticker", "N/A")
        market = item.get("market_data", {}) or {}
        fin = item.get("financial_analysis", {}) or {}
        vr = fin.get("valuation_range", {}) or {}
        rows.append({
            "ticker": ticker,
            "現價": f"HK${_num(market.get('current_price')):.2f}" if _num(market.get("current_price")) > 0 else "資料待補充",
            "市值": _fmt_hkd(market.get("market_cap")),
            "P/E": _fmt_ratio(market.get("pe_ratio")),
            "P/B": _fmt_ratio(market.get("pb_ratio")),
            "股息率": f"{_num(market.get('dividend_yield')) * 100:.2f}%" if _num(market.get("dividend_yield")) > 0 else "資料待補充",
            "估值中位": _fmt_hkd(vr.get("mid")),
            "估值區間": f"{_fmt_hkd(vr.get('low'))} – {_fmt_hkd(vr.get('high'))}" if _num(vr.get("low")) > 0 else "資料待補充",
        })
    return rows


def _build_risk_compare(stock_data_list: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for item in stock_data_list:
        ticker = item.get("ticker", "N/A")
        risk = item.get("risk_analysis", {}) or {}
        score = _num(risk.get("composite_risk_score"), 5.0)
        rows.append({
            "ticker": ticker,
            "風險分數": f"{score:.1f}/10",
            "風險等級": _risk_label(score),
            "Beta": _fmt_ratio(item.get("market_data", {}).get("beta"), ""),
            "首要風險": _top_risk_name(risk),
        })
    return rows


def _build_sector_compare(stock_data_list: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for item in stock_data_list:
        ticker = item.get("ticker", "N/A")
        market = item.get("market_data", {}) or {}
        rows.append({
            "ticker": ticker,
            "行業": market.get("sector") or "資料待補充",
            "市場分類": market.get("market_type") or "資料待補充",
            "毛利率": _fmt_pct(market.get("gross_margin")),
            "淨利率": _fmt_pct(market.get("net_margin")),
            "ROE": _fmt_pct(market.get("roe")),
        })
    return rows


def _build_catalyst_compare(stock_data_list: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for item in stock_data_list:
        ticker = item.get("ticker", "N/A")
        news = item.get("news_catalyst", {}) or {}
        positive = news.get("positive_catalysts") or news.get("positive_factors") or []
        negative = news.get("negative_catalysts") or news.get("negative_factors") or []
        confidence = news.get("news_confidence") or "未接入"
        rows.append({
            "ticker": ticker,
            "新聞可信度": confidence,
            "正面催化": positive[0] if positive else "暫無已驗證資料",
            "負面催化": negative[0] if negative else "暫無已驗證資料",
            "催化數量": f"正面 {len(positive)} / 負面 {len(negative)}",
        })
    return rows


def _find_best_value(stock_data_list: list[dict[str, Any]]) -> str:
    """Find ticker with highest upside to valuation mid vs current price."""
    best_ticker = "N/A"
    best_upside = -999.0
    for item in stock_data_list:
        ticker = item.get("ticker", "N/A")
        market = item.get("market_data", {}) or {}
        fin = item.get("financial_analysis", {}) or {}
        current = _num(market.get("current_price"))
        mid = _num((fin.get("valuation_range") or {}).get("mid"))
        if current > 0 and mid > 0:
            upside = (mid - current) / current
            if upside > best_upside:
                best_upside = upside
                best_ticker = ticker
    return best_ticker


def _find_lowest_risk(stock_data_list: list[dict[str, Any]]) -> str:
    """Find ticker with lowest composite risk score."""
    best_ticker = "N/A"
    best_score = 999.0
    for item in stock_data_list:
        ticker = item.get("ticker", "N/A")
        risk = item.get("risk_analysis", {}) or {}
        score = _num(risk.get("composite_risk_score"), 5.0)
        if score < best_score:
            best_score = score
            best_ticker = ticker
    return best_ticker


def _top_risk_name(risk: dict[str, Any]) -> str:
    scores = risk.get("dimension_scores", {}) or {}
    if not scores:
        return "資料不足"
    top_key = max(scores, key=lambda k: _num(scores[k]))
    rules = [
        ("liquidity", "流動性風險"),
        ("debt", "債務風險"),
        ("cash", "現金流風險"),
        ("market", "市場風險"),
        ("policy", "政策風險"),
        ("sector", "行業風險"),
        ("downside", "下行情景風險"),
    ]
    lowered = top_key.lower()
    for needle, label in rules:
        if needle in lowered:
            return label
    return top_key


def _empty_compare() -> dict[str, Any]:
    return {
        "title": "股票比較分析",
        "tickers": [],
        "count": 0,
        "valuation_compare": [],
        "risk_compare": [],
        "sector_compare": [],
        "catalyst_compare": [],
        "summary": {"best_value": "N/A", "lowest_risk": "N/A", "note": ""},
        "analysis_note": "未提供比較股票資料。",
    }


def build_allocation_summary(
    portfolio_size_hkd: float,
    risk_score: float,
    rating: str,
) -> dict[str, Any]:
    """
    Build a simple portfolio allocation summary based on risk score and rating.
    All calculations are Python-based.
    """
    if portfolio_size_hkd <= 0:
        return {
            "portfolio_size": "未設定",
            "suggested_position_pct": 0.0,
            "suggested_position_hkd": "未設定",
            "max_position_pct": 0.0,
            "risk_note": "未設定投資組合規模，無法計算建議倉位。",
            "allocation_note": "以上只作教育及研究用途，不構成投資建議。",
        }

    # Risk-adjusted position sizing
    if risk_score >= 8 or rating in ("暫不建議", "高風險"):
        suggested_pct = 0.0
        max_pct = 0.02
        risk_note = "風險分數過高，建議不持有或極小倉位觀察。"
    elif risk_score >= 6:
        suggested_pct = 0.03
        max_pct = 0.05
        risk_note = "中高風險，建議小倉位觀察，不超過組合 5%。"
    elif risk_score >= 4:
        suggested_pct = 0.05
        max_pct = 0.08
        risk_note = "中等風險，建議標準倉位，不超過組合 8%。"
    else:
        suggested_pct = 0.08
        max_pct = 0.12
        risk_note = "較低風險，可考慮較大倉位，不超過組合 12%。"

    suggested_hkd = portfolio_size_hkd * suggested_pct
    max_hkd = portfolio_size_hkd * max_pct

    return {
        "portfolio_size": format_currency_hkd(portfolio_size_hkd),
        "suggested_position_pct": suggested_pct,
        "suggested_position_hkd": format_currency_hkd(suggested_hkd),
        "max_position_pct": max_pct,
        "max_position_hkd": format_currency_hkd(max_hkd),
        "risk_note": risk_note,
        "allocation_note": "以上倉位建議只作教育及研究用途，不構成投資建議。投資者應按個人風險承受能力及財務狀況調整。",
    }
