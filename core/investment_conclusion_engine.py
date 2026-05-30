"""
core/investment_conclusion_engine.py
Investment Conclusion Engine — v4.0 Hardening Layer

Integrates all analysis modules to produce a structured investment conclusion.
Never outputs '—', '分析中', or blank fields.
If data is insufficient, outputs conservative defaults with explanation.
"""

from core.safe_math import safe_float


# ── Rating definitions ────────────────────────────────────────────────────────
RATINGS = ["買入", "觀察", "中性", "減持", "避免"]
HORIZONS = ["短線", "中線", "長線"]
INVESTOR_TYPES = ["保守型", "平衡型", "進取型"]

# ── Decision factor weights ───────────────────────────────────────────────────
DECISION_FACTORS = [
    {"factor": "估值",  "weight": "25%", "weight_num": 0.25},
    {"factor": "風險",  "weight": "25%", "weight_num": 0.25},
    {"factor": "財務",  "weight": "20%", "weight_num": 0.20},
    {"factor": "新聞",  "weight": "15%", "weight_num": 0.15},
    {"factor": "市場",  "weight": "15%", "weight_num": 0.15},
]


def _safe_score(val, default=5.0) -> float:
    """Extract a numeric score safely."""
    try:
        s = str(val).replace("/10", "").replace("%", "").strip()
        f = float(s)
        if 0 <= f <= 10:
            return f
        if 0 <= f <= 100:
            return f / 10
    except (TypeError, ValueError):
        pass
    return default


def _score_to_rating(score: float) -> str:
    """Convert composite score (0-10) to rating."""
    if score >= 7.5:
        return "買入"
    elif score >= 6.5:
        return "觀察"
    elif score >= 5.0:
        return "中性"
    elif score >= 3.5:
        return "減持"
    else:
        return "避免"


def _score_to_horizon(score: float, risk_score: float) -> str:
    """Determine investment horizon from scores."""
    if risk_score >= 7.0:
        return "短線"
    elif score >= 6.5:
        return "長線"
    else:
        return "中線"


def _score_to_investor_type(score: float, risk_score: float) -> str:
    """Determine suitable investor type."""
    if risk_score >= 7.0:
        return "進取型"
    elif risk_score >= 5.0:
        return "平衡型"
    else:
        return "保守型"


def _extract_valuation_score(market_snapshot: dict, financial_data: dict) -> tuple:
    """Extract valuation score and summary."""
    pe = safe_float(market_snapshot.get("_raw", {}).get("pe"))
    pb = safe_float(market_snapshot.get("_raw", {}).get("pb"))

    if not pe and not pb:
        return 5.0, "估值數據不足，採用中性評分"

    score = 5.0
    notes = []

    if pe:
        if pe < 10:
            score += 1.5
            notes.append(f"市盈率 {pe:.1f}x 偏低，估值具吸引力")
        elif pe < 20:
            score += 0.5
            notes.append(f"市盈率 {pe:.1f}x 合理")
        elif pe < 35:
            score -= 0.5
            notes.append(f"市盈率 {pe:.1f}x 偏高")
        else:
            score -= 1.5
            notes.append(f"市盈率 {pe:.1f}x 估值偏貴")

    if pb:
        if pb < 1.0:
            score += 1.0
            notes.append(f"市帳率 {pb:.2f}x 低於賬面值")
        elif pb < 2.0:
            score += 0.3
            notes.append(f"市帳率 {pb:.2f}x 合理")
        else:
            score -= 0.3
            notes.append(f"市帳率 {pb:.2f}x 偏高")

    score = max(1.0, min(10.0, score))
    summary = "；".join(notes) if notes else "估值處於合理水平"
    return score, summary


def _extract_risk_score(risk_assessment: dict) -> tuple:
    """Extract risk score and summary."""
    composite = risk_assessment.get("composite_score", "5.0/10")
    score = _safe_score(composite)
    # Risk score: higher = more risky = lower investment attractiveness
    inv_score = 10.0 - score  # invert for conclusion scoring
    level = risk_assessment.get("risk_level", "中等風險")
    top_risks = risk_assessment.get("risk_items", [])
    top_risk_names = [r.get("risk_name", "") for r in top_risks[:2] if r.get("risk_name")]
    summary = f"整體風險評分 {score:.1f}/10（{level}）"
    if top_risk_names:
        summary += f"，主要風險：{'、'.join(top_risk_names)}"
    return inv_score, summary, score


def _extract_financial_score(financial_data: dict) -> tuple:
    """Extract financial health score and summary."""
    revenue = safe_float(financial_data.get("revenue"))
    net_profit = safe_float(financial_data.get("net_profit"))
    roe = safe_float(financial_data.get("roe"))
    net_margin = safe_float(financial_data.get("net_margin"))

    if not any([revenue, net_profit, roe]):
        return 5.0, "財務數據不足，採用中性評分"

    score = 5.0
    notes = []

    if roe:
        if roe > 15:
            score += 1.5
            notes.append(f"ROE {roe:.1f}% 優秀")
        elif roe > 8:
            score += 0.5
            notes.append(f"ROE {roe:.1f}% 合理")
        else:
            score -= 0.5
            notes.append(f"ROE {roe:.1f}% 偏低")

    if net_margin:
        if net_margin > 20:
            score += 1.0
            notes.append(f"淨利率 {net_margin:.1f}% 優秀")
        elif net_margin > 10:
            score += 0.3
            notes.append(f"淨利率 {net_margin:.1f}% 合理")
        elif net_margin > 0:
            score -= 0.3
            notes.append(f"淨利率 {net_margin:.1f}% 偏低")
        else:
            score -= 1.5
            notes.append("淨利率為負，盈利能力存疑")

    score = max(1.0, min(10.0, score))
    summary = "；".join(notes) if notes else "財務狀況處於合理水平"
    return score, summary


def _extract_news_score(agent_opinions: dict) -> tuple:
    """Extract news/sentiment score from agent opinions."""
    news_agent = next(
        (a for a in agent_opinions.get("agents", []) if "新聞" in a.get("agent_name", "")),
        None
    )
    if not news_agent:
        return 5.0, "新聞情緒數據不足，採用中性評分"

    stance = news_agent.get("stance", "中性")
    confidence = safe_float(news_agent.get("confidence", 50)) / 10

    if stance == "正面":
        score = 5.0 + confidence * 0.5
        summary = f"新聞情緒正面（信心 {news_agent.get('confidence', 50)}%）"
    elif stance == "負面":
        score = 5.0 - confidence * 0.5
        summary = f"新聞情緒負面（信心 {news_agent.get('confidence', 50)}%）"
    else:
        score = 5.0
        summary = f"新聞情緒中性（信心 {news_agent.get('confidence', 50)}%）"

    return max(1.0, min(10.0, score)), summary


def _extract_market_score(market_snapshot: dict) -> tuple:
    """Extract market momentum score."""
    raw = market_snapshot.get("_raw", {})
    current = safe_float(raw.get("current_price"))
    wk52_high = safe_float(raw.get("fifty_two_week_high"))
    wk52_low = safe_float(raw.get("fifty_two_week_low"))

    if not current or not wk52_high or not wk52_low:
        return 5.0, "市場數據不足，採用中性評分"

    if (wk52_high - wk52_low) > 0:
        position = (current - wk52_low) / (wk52_high - wk52_low)
        score = 3.0 + position * 4.0  # 3.0 to 7.0 range
        pct = position * 100
        summary = f"現價處於52週區間 {pct:.0f}% 位置"
    else:
        score = 5.0
        summary = "52週高低位數據不足"

    return max(1.0, min(10.0, score)), summary


def build_investment_conclusion(
    market_snapshot: dict,
    financial_data: dict,
    risk_assessment: dict,
    agent_opinions: dict,
    competitive_landscape: list,
    source_registry: dict,
) -> dict:
    """
    Build the investment conclusion from all analysis modules.

    Never outputs '—', '分析中', or blank fields.
    If target_price cannot be reliably estimated, says so explicitly.
    """
    # ── Extract scores per factor ─────────────────────────────────────────────
    val_score, val_summary   = _extract_valuation_score(market_snapshot, financial_data)
    risk_inv, risk_summary, raw_risk = _extract_risk_score(risk_assessment)
    fin_score, fin_summary   = _extract_financial_score(financial_data)
    news_score, news_summary = _extract_news_score(agent_opinions)
    mkt_score, mkt_summary   = _extract_market_score(market_snapshot)

    # ── Weighted composite score ──────────────────────────────────────────────
    composite = (
        val_score  * 0.25 +
        risk_inv   * 0.25 +
        fin_score  * 0.20 +
        news_score * 0.15 +
        mkt_score  * 0.15
    )
    composite = round(composite, 1)

    # ── Derive outputs ────────────────────────────────────────────────────────
    rating          = _score_to_rating(composite)
    horizon         = _score_to_horizon(composite, raw_risk)
    investor_type   = _score_to_investor_type(composite, raw_risk)
    confidence_pct  = int(min(95, max(30, composite * 10)))

    # ── Target price ─────────────────────────────────────────────────────────
    # Cannot reliably estimate without DCF/analyst consensus — say so clearly
    current_price = safe_float(market_snapshot.get("_raw", {}).get("current_price"))
    if current_price and current_price > 0:
        target_price_note = "目標價未能可靠估算（需要分析師共識或 DCF 模型）"
        potential_upside   = "升幅未能可靠估算"
    else:
        target_price_note = "目標價未能可靠估算（現價數據不足）"
        potential_upside   = "升幅未能可靠估算"

    # ── Decision basis ────────────────────────────────────────────────────────
    decision_basis = [
        {"factor": "估值",  "weight": "25%", "score": f"{val_score:.1f}/10",  "summary": val_summary},
        {"factor": "風險",  "weight": "25%", "score": f"{risk_inv:.1f}/10",   "summary": risk_summary},
        {"factor": "財務",  "weight": "20%", "score": f"{fin_score:.1f}/10",  "summary": fin_summary},
        {"factor": "新聞",  "weight": "15%", "score": f"{news_score:.1f}/10", "summary": news_summary},
        {"factor": "市場",  "weight": "15%", "score": f"{mkt_score:.1f}/10",  "summary": mkt_summary},
    ]

    # ── Final summary ─────────────────────────────────────────────────────────
    rating_desc = {
        "買入": "綜合分析顯示股票具備投資吸引力，建議考慮買入。",
        "觀察": "股票具備一定潛力，但需等待更明確催化劑，建議列入觀察名單。",
        "中性": "股票估值合理，風險與回報相對平衡，建議中性持有。",
        "減持": "股票面臨較大下行風險，建議考慮減持。",
        "避免": "股票風險偏高或估值過貴，建議暫時避免。",
    }
    final_summary = (
        f"綜合評分 {composite}/10，投資評級：{rating}。"
        f"{rating_desc.get(rating, '')} "
        f"適合{investor_type}投資者，建議投資週期：{horizon}。"
    )

    return {
        "rating":             rating,
        "composite_score":    f"{composite}/10",
        "investment_horizon": horizon,
        "suitable_investor":  investor_type,
        "target_price":       target_price_note,
        "potential_upside":   potential_upside,
        "confidence":         confidence_pct,
        "decision_basis":     decision_basis,
        "final_summary":      final_summary,
        # Individual scores for display
        "valuation_score":    f"{val_score:.1f}/10",
        "risk_score":         f"{raw_risk:.1f}/10",
        "financial_score":    f"{fin_score:.1f}/10",
        "news_score":         f"{news_score:.1f}/10",
        "market_score":       f"{mkt_score:.1f}/10",
    }
