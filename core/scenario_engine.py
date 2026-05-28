"""
core/scenario_engine.py

Scenario Intelligence Layer — v1.1

Generates Bull / Base / Bear case scenarios from Python-calculated inputs.
All implied prices and assumptions are derived from market snapshot,
financial ratios, and risk scores. LLM does NOT generate numerical values.
"""

from __future__ import annotations

from typing import Any

from core.safe_math import safe_number


def _num(value: Any, default: float = 0.0) -> float:
    return safe_number(value, default)


def _fmt_price(value: float) -> str:
    return f"HK${value:.2f}" if value > 0 else "資料待補充"


def _fmt_pct(value: float) -> str:
    sign = "+" if value >= 0 else ""
    return f"{sign}{value * 100:.1f}%"


def _risk_label(score: float) -> str:
    if score <= 3:
        return "低風險"
    if score <= 6:
        return "中等風險"
    if score <= 8:
        return "高風險"
    return "極高風險"


def build_scenario_analysis(
    market_data: dict[str, Any],
    financial_analysis: dict[str, Any],
    risk_analysis: dict[str, Any],
    news_catalyst: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Build Bull / Base / Bear scenario analysis from Python-calculated inputs.

    Implied prices are derived from:
    - current_price (market_data)
    - valuation_range (financial_analysis)
    - composite_risk_score (risk_analysis)
    - positive/negative catalysts (news_catalyst)

    No LLM involvement in numerical calculations.
    """
    from core.data_confidence import INVALID

    if market_data.get("data_confidence") == INVALID:
        return _invalid_scenario()

    current = _num(market_data.get("current_price"))
    vr = (financial_analysis or {}).get("valuation_range", {}) or {}
    val_low = _num(vr.get("low"))
    val_mid = _num(vr.get("mid"))
    val_high = _num(vr.get("high"))
    risk_score = _num((risk_analysis or {}).get("composite_risk_score"), 5.0)

    # Derive implied prices from valuation range or fallback multiples
    if val_mid > 0 and current > 0:
        bull_price = val_high if val_high > 0 else current * 1.25
        base_price = val_mid
        bear_price = val_low if val_low > 0 else current * 0.80
    elif current > 0:
        # No valuation range — use risk-adjusted multiples
        bull_price = current * 1.20
        base_price = current * 1.00
        bear_price = current * (0.85 - (risk_score - 5) * 0.02)
    else:
        bull_price = 0.0
        base_price = 0.0
        bear_price = 0.0

    # Upside / downside from current
    bull_upside = (bull_price - current) / current if current > 0 else 0.0
    base_upside = (base_price - current) / current if current > 0 else 0.0
    bear_upside = (bear_price - current) / current if current > 0 else 0.0

    # Catalyst inputs from news
    news = news_catalyst or {}
    positive_catalysts = news.get("positive_catalysts") or news.get("positive_factors") or []
    negative_catalysts = news.get("negative_catalysts") or news.get("negative_factors") or []
    risk_events = news.get("risk_events") or news.get("monitor_items") or []

    # Build scenario rows
    bull_catalyst = positive_catalysts[0] if positive_catalysts else "盈利上修或估值倍數改善"
    bear_catalyst = negative_catalysts[0] if negative_catalysts else "盈利預警或現金流惡化"

    scenarios = [
        {
            "name": "Bull Case",
            "name_zh": "樂觀情景",
            "description": "收入增長加速，估值倍數改善，市場風險偏好回升。",
            "key_assumption": f"估值修復至模型高位，{bull_catalyst}",
            "implied_price": _fmt_price(bull_price),
            "implied_upside": _fmt_pct(bull_upside),
            "key_catalyst": bull_catalyst,
            "probability_note": "需要業績超預期及市場情緒改善",
        },
        {
            "name": "Base Case",
            "name_zh": "基準情景",
            "description": "業務維持穩定，估值接近模型中位，等待業績確認。",
            "key_assumption": "估值維持模型中位，業務無重大變化",
            "implied_price": _fmt_price(base_price),
            "implied_upside": _fmt_pct(base_upside),
            "key_catalyst": "業績符合預期，無重大政策或市場衝擊",
            "probability_note": "最可能情景，需持續監察基本面",
        },
        {
            "name": "Bear Case",
            "name_zh": "悲觀情景",
            "description": "收入或利潤率下滑，估值收縮，高槓桿或現金流壓力。",
            "key_assumption": f"估值收縮至模型低位，{bear_catalyst}",
            "implied_price": _fmt_price(bear_price),
            "implied_upside": _fmt_pct(bear_upside),
            "key_catalyst": bear_catalyst,
            "probability_note": f"風險分數 {risk_score:.1f}/10，屬{_risk_label(risk_score)}",
        },
    ]

    # Downside triggers
    top_risks = (risk_analysis or {}).get("top_risks", []) or []
    triggers = [item.get("dimension", "") for item in top_risks[:3] if item.get("dimension")]
    if not triggers:
        triggers = [
            "盈利預警或收入增長放緩",
            "現金流惡化或債務再融資壓力",
            "政策或市場情緒急劇轉弱",
            "成交量急跌並跌穿關鍵支持位",
        ]
    else:
        triggers.extend([
            "成交量急跌並跌穿關鍵支持位",
            "重大公告或監管事件",
        ])

    # Monitor items from risk events
    monitor_items = risk_events[:3] if risk_events else [
        "下一期業績收入及利潤率變化",
        "現金流及債務再融資情況",
        "市場風險偏好及成交量趨勢",
    ]

    return {
        "title": "情景分析 Scenario Analysis",
        "is_valid": True,
        "current_price": _fmt_price(current),
        "risk_score": f"{risk_score:.1f}/10",
        "risk_label": _risk_label(risk_score),
        "scenarios": scenarios,
        "triggers": triggers,
        "monitor_items": monitor_items,
        "analysis_note": (
            "情景分析基於 Python 計算的估值區間、風險分數及市場資料，"
            "不由 LLM 生成數值。所有隱含價格只作研究參考，不構成投資建議。"
        ),
        # PDF-compatible rows format
        "rows": [
            [
                s["name"],
                s["key_assumption"],
                f"{s['implied_price']} ({s['implied_upside']})",
                s["key_catalyst"],
            ]
            for s in scenarios
        ],
    }


def _invalid_scenario() -> dict[str, Any]:
    return {
        "title": "情景分析 Scenario Analysis",
        "is_valid": False,
        "current_price": "N/A",
        "risk_score": "N/A",
        "risk_label": "無法評估",
        "scenarios": [],
        "triggers": ["股票代號或市場資料驗證未完成"],
        "monitor_items": [],
        "analysis_note": "資料驗證未完成，情景分析已停止。",
        "rows": [["N/A", "資料驗證未完成，情景分析已停止。", "N/A", "N/A"]],
    }
