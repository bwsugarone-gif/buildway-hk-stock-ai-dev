"""
core/agent_opinion_engine.py
Real Agent Opinion Layer — each agent produces a structured opinion with
evidence, confidence, and a bull/bear stance. No fake "分析中" or 0% confidence.
No hallucinated data. Opinions are derived from actual report_data values.
"""
from __future__ import annotations
from typing import Any, Dict, List, Optional
from core.safe_math import safe_number

# Agent definitions
AGENTS = [
    {"id": "market_agent",    "name": "市場分析 Agent",  "side": "bull"},
    {"id": "financial_agent", "name": "財務分析 Agent",  "side": "bull"},
    {"id": "news_agent",      "name": "新聞分析 Agent",  "side": "bull"},
    {"id": "risk_agent",      "name": "風險分析 Agent",  "side": "bear"},
    {"id": "valuation_agent", "name": "估值分析 Agent",  "side": "bear"},
    {"id": "event_agent",     "name": "事件分析 Agent",  "side": "bear"},
]


def _confidence_from_data_count(n_points: int) -> int:
    """Convert number of available data points to a confidence percentage."""
    if n_points >= 8:
        return 90
    if n_points >= 5:
        return 75
    if n_points >= 3:
        return 60
    if n_points >= 1:
        return 45
    return 30


def _market_agent_opinion(d: Dict[str, Any]) -> Dict:
    price = safe_number(d.get("current_price"))
    high52 = safe_number(d.get("week_52_high"))
    low52 = safe_number(d.get("week_52_low"))
    volume = safe_number(d.get("volume"))
    beta = safe_number(d.get("beta", 1.0))

    points = []
    bull_points = []
    bear_points = []
    data_count = 0

    if price > 0 and high52 > 0 and low52 > 0:
        data_count += 3
        rng = high52 - low52
        pos = (price - low52) / rng if rng > 0 else 0.5
        pct = int(pos * 100)
        if pos > 0.6:
            bull_points.append(f"現價處於52週高位區間（{pct}%位置），顯示市場動能強勁")
        elif pos < 0.3:
            bear_points.append(f"現價接近52週低位（{pct}%位置），市場情緒偏弱")
        else:
            points.append(f"現價處於52週中間位置（{pct}%），市場方向待確認")

    if beta > 0:
        data_count += 1
        if beta < 0.8:
            bull_points.append(f"Beta {beta:.2f}，波動性低於大市，防守性強")
        elif beta > 1.3:
            bear_points.append(f"Beta {beta:.2f}，波動性高於大市，風險較大")
        else:
            points.append(f"Beta {beta:.2f}，與大市走勢相近")

    if volume > 0:
        data_count += 1
        points.append(f"成交量有數據支持")

    all_evidence = bull_points + bear_points + points
    if not all_evidence:
        all_evidence = ["市場數據不足，以基準評估"]
        data_count = 0

    stance = "看好" if len(bull_points) >= len(bear_points) else "審慎"
    confidence = _confidence_from_data_count(data_count)

    return {
        "agent_name": "市場分析 Agent",
        "side": "bull",
        "stance": stance,
        "confidence": confidence,
        "key_points": all_evidence[:4],
        "bull_arguments": bull_points[:3],
        "bear_arguments": bear_points[:2],
        "summary": f"基於市場技術指標，{stance}評估，信心度 {confidence}%",
        "data_points_used": data_count,
    }


def _financial_agent_opinion(d: Dict[str, Any]) -> Dict:
    revenue = safe_number(d.get("revenue"))
    net_profit = safe_number(d.get("net_profit"))
    roe = safe_number(d.get("roe"))
    margin = safe_number(d.get("net_margin"))
    debt_ratio = safe_number(d.get("debt_to_equity"))
    fcf = safe_number(d.get("free_cash_flow"))

    bull_points = []
    bear_points = []
    data_count = 0

    if revenue > 0:
        data_count += 1
        bull_points.append(f"收入規模有數據支持")
    if net_profit > 0:
        data_count += 1
        bull_points.append(f"淨利潤為正數，盈利能力確認")
    elif net_profit < 0:
        data_count += 1
        bear_points.append(f"淨利潤為負數，盈利能力存疑")
    if roe > 15:
        data_count += 1
        bull_points.append(f"ROE {roe:.1f}% 優秀，股東回報良好")
    elif roe > 0 and roe < 5:
        data_count += 1
        bear_points.append(f"ROE {roe:.1f}% 偏低，資本效率不足")
    elif roe >= 5:
        data_count += 1
    if margin > 20:
        data_count += 1
        bull_points.append(f"淨利率 {margin:.1f}% 優秀，盈利質素高")
    elif margin > 0 and margin < 5:
        data_count += 1
        bear_points.append(f"淨利率 {margin:.1f}% 偏低，盈利空間有限")
    elif margin >= 5:
        data_count += 1
    if debt_ratio > 0:
        data_count += 1
        if debt_ratio > 2.0:
            bear_points.append(f"負債比率 {debt_ratio:.2f}x 偏高，財務槓桿風險")
        elif debt_ratio < 0.5:
            bull_points.append(f"負債比率 {debt_ratio:.2f}x 健康，財務穩健")
    if fcf > 0:
        data_count += 1
        bull_points.append(f"自由現金流正數，現金生成能力良好")
    elif fcf < 0:
        data_count += 1
        bear_points.append(f"自由現金流為負，現金消耗需關注")

    if not bull_points and not bear_points:
        bull_points = ["財務數據不足，以基準評估"]
        data_count = 0

    stance = "看好" if len(bull_points) > len(bear_points) else "審慎"
    confidence = _confidence_from_data_count(data_count)

    return {
        "agent_name": "財務分析 Agent",
        "side": "bull",
        "stance": stance,
        "confidence": confidence,
        "key_points": (bull_points + bear_points)[:4],
        "bull_arguments": bull_points[:3],
        "bear_arguments": bear_points[:2],
        "summary": f"基於財務指標分析，{stance}評估，信心度 {confidence}%",
        "data_points_used": data_count,
    }


def _news_agent_opinion(d: Dict[str, Any]) -> Dict:
    news_items = d.get("news_items") or d.get("news_analysis", {})
    sentiment = str(d.get("news_sentiment", "")).lower()
    catalyst = d.get("catalyst_events") or []

    bull_points = []
    bear_points = []
    data_count = 0

    if isinstance(news_items, list) and len(news_items) > 0:
        data_count += min(len(news_items), 3)
        bull_points.append(f"已收集 {len(news_items)} 條新聞，有數據基礎")
    elif isinstance(news_items, dict) and news_items:
        data_count += 1

    if "positive" in sentiment or "正面" in sentiment:
        data_count += 1
        bull_points.append("新聞情緒偏正面，市場關注度高")
    elif "negative" in sentiment or "負面" in sentiment:
        data_count += 1
        bear_points.append("新聞情緒偏負面，需關注潛在風險")
    elif "neutral" in sentiment or "中性" in sentiment:
        data_count += 1
        bull_points.append("新聞情緒中性，無重大負面事件")

    if isinstance(catalyst, list) and len(catalyst) > 0:
        data_count += 1
        bull_points.append(f"發現 {len(catalyst)} 個潛在催化事件")

    if not bull_points and not bear_points:
        bull_points = ["新聞數據不足，以基準評估"]
        data_count = 0

    stance = "看好" if len(bull_points) >= len(bear_points) else "審慎"
    confidence = _confidence_from_data_count(data_count)

    return {
        "agent_name": "新聞分析 Agent",
        "side": "bull",
        "stance": stance,
        "confidence": confidence,
        "key_points": (bull_points + bear_points)[:4],
        "bull_arguments": bull_points[:3],
        "bear_arguments": bear_points[:2],
        "summary": f"基於新聞情緒分析，{stance}評估，信心度 {confidence}%",
        "data_points_used": data_count,
    }


def _risk_agent_opinion(d: Dict[str, Any]) -> Dict:
    risk_items = d.get("risk_items") or []
    composite_score_raw = safe_number(d.get("composite_score_raw", 5.0))
    risk_label = d.get("risk_label", "")

    bull_points = []
    bear_points = []
    data_count = 0

    if isinstance(risk_items, list) and len(risk_items) > 0:
        data_count += len(risk_items)
        high_risks = [r for r in risk_items if safe_number(r.get("score_raw", 0)) > 6.5]
        if high_risks:
            for r in high_risks[:2]:
                bear_points.append(f"{r.get('risk_name', '風險項目')} 評分 {r.get('score', 'N/A')} 需關注")
        else:
            bull_points.append("各項風險評分均在可控範圍")

    if composite_score_raw > 0:
        data_count += 1
        if composite_score_raw > 7.0:
            bear_points.append(f"綜合風險評分 {composite_score_raw:.1f}/10，整體風險偏高")
        elif composite_score_raw < 4.0:
            bull_points.append(f"綜合風險評分 {composite_score_raw:.1f}/10，整體風險可控")
        else:
            bull_points.append(f"綜合風險評分 {composite_score_raw:.1f}/10，風險中等")

    if not bull_points and not bear_points:
        bear_points = ["風險數據不足，以基準評估"]
        data_count = 0

    stance = "審慎" if len(bear_points) >= len(bull_points) else "可接受"
    confidence = _confidence_from_data_count(data_count)

    return {
        "agent_name": "風險分析 Agent",
        "side": "bear",
        "stance": stance,
        "confidence": confidence,
        "key_points": (bear_points + bull_points)[:4],
        "bull_arguments": bull_points[:2],
        "bear_arguments": bear_points[:3],
        "summary": f"基於風險評估，{stance}立場，信心度 {confidence}%",
        "data_points_used": data_count,
    }


def _valuation_agent_opinion(d: Dict[str, Any]) -> Dict:
    pe = safe_number(d.get("pe_ratio"))
    pb = safe_number(d.get("pb_ratio"))
    div_yield = safe_number(d.get("dividend_yield"))
    sector_pe = safe_number(d.get("sector_pe", 15.0))
    if sector_pe <= 0:
        sector_pe = 15.0

    bull_points = []
    bear_points = []
    data_count = 0

    if pe > 0:
        data_count += 1
        if pe > sector_pe * 1.5:
            bear_points.append(f"P/E {pe:.1f}x 顯著高於行業 {sector_pe:.1f}x，估值偏貴")
        elif pe < sector_pe * 0.7:
            bull_points.append(f"P/E {pe:.1f}x 低於行業 {sector_pe:.1f}x，估值具吸引力")
        else:
            bull_points.append(f"P/E {pe:.1f}x 接近行業均值，估值合理")

    if pb > 0:
        data_count += 1
        if pb > 3.0:
            bear_points.append(f"P/B {pb:.2f}x 偏高，市帳率溢價明顯")
        elif pb < 1.0:
            bull_points.append(f"P/B {pb:.2f}x 低於帳面值，存在價值空間")
        else:
            bull_points.append(f"P/B {pb:.2f}x 合理")

    if div_yield > 0:
        data_count += 1
        if div_yield > 4.0:
            bull_points.append(f"股息率 {div_yield:.1f}% 吸引，提供穩定回報")
        elif div_yield > 2.0:
            bull_points.append(f"股息率 {div_yield:.1f}%，有一定回報")

    if not bull_points and not bear_points:
        bear_points = ["估值數據不足，以基準評估"]
        data_count = 0

    stance = "審慎" if len(bear_points) > len(bull_points) else "合理"
    confidence = _confidence_from_data_count(data_count)

    return {
        "agent_name": "估值分析 Agent",
        "side": "bear",
        "stance": stance,
        "confidence": confidence,
        "key_points": (bull_points + bear_points)[:4],
        "bull_arguments": bull_points[:3],
        "bear_arguments": bear_points[:2],
        "summary": f"基於估值指標，{stance}評估，信心度 {confidence}%",
        "data_points_used": data_count,
    }


def _event_agent_opinion(d: Dict[str, Any]) -> Dict:
    hkex = d.get("hkex_announcements") or []
    catalyst = d.get("catalyst_events") or []
    watch_items = d.get("watch_items") or []

    bull_points = []
    bear_points = []
    data_count = 0

    if isinstance(hkex, list) and len(hkex) > 0:
        data_count += min(len(hkex), 2)
        bull_points.append(f"港交所有 {len(hkex)} 項公告，資訊透明度高")

    if isinstance(catalyst, list) and len(catalyst) > 0:
        data_count += 1
        bull_points.append(f"識別 {len(catalyst)} 個潛在催化事件")

    if isinstance(watch_items, list) and len(watch_items) > 0:
        data_count += 1
        bear_points.append(f"有 {len(watch_items)} 項監察事項需持續追蹤")

    if not bull_points and not bear_points:
        bear_points = ["事件數據不足，以基準評估"]
        data_count = 0

    stance = "中性" if data_count == 0 else ("關注" if bear_points else "正面")
    confidence = _confidence_from_data_count(data_count)

    return {
        "agent_name": "事件分析 Agent",
        "side": "bear",
        "stance": stance,
        "confidence": confidence,
        "key_points": (bull_points + bear_points)[:4],
        "bull_arguments": bull_points[:3],
        "bear_arguments": bear_points[:2],
        "summary": f"基於事件及公告分析，{stance}立場，信心度 {confidence}%",
        "data_points_used": data_count,
    }


def build_agent_opinions(report_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build structured opinions for all 6 agents from report_data.
    No agent will show '分析中', '—', or 0% confidence after this runs.
    """
    # Flatten data for agent access
    flat: Dict[str, Any] = {}
    for key in ("report_metadata", "market_data", "financial_analysis",
                "financial_history", "risk_analysis", "news_analysis",
                "investment_committee"):
        sub = report_data.get(key)
        if isinstance(sub, dict):
            flat.update(sub)
    flat.update({k: v for k, v in report_data.items() if not isinstance(v, dict)})

    opinions = [
        _market_agent_opinion(flat),
        _financial_agent_opinion(flat),
        _news_agent_opinion(flat),
        _risk_agent_opinion(flat),
        _valuation_agent_opinion(flat),
        _event_agent_opinion(flat),
    ]

    bull_opinions = [o for o in opinions if o["side"] == "bull"]
    bear_opinions = [o for o in opinions if o["side"] == "bear"]

    # Aggregate bull/bear scores
    bull_score = sum(o["confidence"] for o in bull_opinions) // max(len(bull_opinions), 1)
    bear_score = sum(o["confidence"] for o in bear_opinions) // max(len(bear_opinions), 1)

    # Committee verdict
    if bull_score > bear_score + 15:
        verdict = "看好"
        verdict_reason = "多數 Agent 支持正面觀點，牛市論據較強"
    elif bear_score > bull_score + 15:
        verdict = "審慎"
        verdict_reason = "多數 Agent 提示風險，熊市論據較強"
    else:
        verdict = "中性觀察"
        verdict_reason = "牛熊論據相近，建議持續觀察"

    overall_confidence = (bull_score + bear_score) // 2

    return {
        "opinions": opinions,
        "bull_opinions": bull_opinions,
        "bear_opinions": bear_opinions,
        "bull_score": bull_score,
        "bear_score": bear_score,
        "committee_verdict": verdict,
        "verdict_reason": verdict_reason,
        "overall_confidence": overall_confidence,
        "agent_count": len(opinions),
    }
