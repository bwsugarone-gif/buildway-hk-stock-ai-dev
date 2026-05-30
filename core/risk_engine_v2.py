"""
core/risk_engine_v2.py
Fixed 7-category risk engine. Every score has a source. Every weight sums to 100%.
Score format: x.x/10. No duplicate categories. No hallucinated data.
"""
from __future__ import annotations
from typing import Any, Dict, List
from core.safe_math import safe_number

# Fixed 7 categories — weights must sum to 100
RISK_CATEGORIES: List[Dict] = [
    {"id": "financial",  "name": "財務風險",     "weight": 20},
    {"id": "cashflow",   "name": "現金流風險",   "weight": 18},
    {"id": "liquidity",  "name": "流動性風險",   "weight": 15},
    {"id": "valuation",  "name": "估值風險",     "weight": 17},
    {"id": "market",     "name": "市場風險",     "weight": 15},
    {"id": "policy",     "name": "政策風險",     "weight": 10},
    {"id": "downside",   "name": "下行情景風險", "weight": 5},
]
assert sum(c["weight"] for c in RISK_CATEGORIES) == 100, "Weights must sum to 100"


def _level(score: float) -> str:
    if score <= 3.0:
        return "低風險"
    if score <= 6.0:
        return "中等風險"
    if score <= 8.0:
        return "高風險"
    return "極高風險"


def _fmt(score: float) -> str:
    return f"{score:.1f}/10"


def _score_financial(d: Dict) -> tuple:
    roe = safe_number(d.get("roe"))
    debt_ratio = safe_number(d.get("debt_to_equity"))
    margin = safe_number(d.get("net_margin"))
    score = 5.0
    evidence_parts = []
    if roe > 0:
        if roe < 5:
            score += 1.5
            evidence_parts.append(f"ROE {roe:.1f}% 偏低")
        elif roe > 15:
            score -= 1.0
            evidence_parts.append(f"ROE {roe:.1f}% 良好")
        else:
            evidence_parts.append(f"ROE {roe:.1f}%")
    if debt_ratio > 0:
        if debt_ratio > 2.0:
            score += 1.5
            evidence_parts.append(f"負債比率 {debt_ratio:.2f}x 偏高")
        elif debt_ratio < 0.5:
            score -= 0.5
            evidence_parts.append(f"負債比率 {debt_ratio:.2f}x 健康")
        else:
            evidence_parts.append(f"負債比率 {debt_ratio:.2f}x")
    if margin > 0:
        if margin < 5:
            score += 0.5
            evidence_parts.append(f"淨利率 {margin:.1f}% 偏低")
        elif margin > 20:
            score -= 0.5
            evidence_parts.append(f"淨利率 {margin:.1f}% 優秀")
    score = max(1.0, min(10.0, score))
    evidence = "；".join(evidence_parts) if evidence_parts else "財務數據不足，使用基準分"
    reason = f"基於財務指標評估：{evidence}"
    signal = "監察 ROE 趨勢及負債比率變化"
    return score, reason, evidence, signal


def _score_cashflow(d: Dict) -> tuple:
    fcf = safe_number(d.get("free_cash_flow"))
    op_cf = safe_number(d.get("operating_cash_flow"))
    score = 5.0
    evidence_parts = []
    if fcf != 0:
        if fcf < 0:
            score += 2.0
            evidence_parts.append(f"自由現金流為負 ({fcf:,.0f})")
        else:
            score -= 0.5
            evidence_parts.append(f"自由現金流正數 ({fcf:,.0f})")
    if op_cf != 0:
        if op_cf < 0:
            score += 1.5
            evidence_parts.append("經營現金流為負")
        else:
            evidence_parts.append("經營現金流正數")
    score = max(1.0, min(10.0, score))
    evidence = "；".join(evidence_parts) if evidence_parts else "現金流數據不足，使用基準分"
    reason = f"基於現金流分析：{evidence}"
    signal = "監察季度自由現金流及資本支出"
    return score, reason, evidence, signal


def _score_liquidity(d: Dict) -> tuple:
    current_ratio = safe_number(d.get("current_ratio"))
    quick_ratio = safe_number(d.get("quick_ratio"))
    score = 5.0
    evidence_parts = []
    if current_ratio > 0:
        if current_ratio < 1.0:
            score += 2.5
            evidence_parts.append(f"流動比率 {current_ratio:.2f}x 低於1")
        elif current_ratio > 2.0:
            score -= 1.0
            evidence_parts.append(f"流動比率 {current_ratio:.2f}x 充裕")
        else:
            evidence_parts.append(f"流動比率 {current_ratio:.2f}x")
    if quick_ratio > 0:
        if quick_ratio < 0.8:
            score += 1.0
            evidence_parts.append(f"速動比率 {quick_ratio:.2f}x 偏低")
        else:
            evidence_parts.append(f"速動比率 {quick_ratio:.2f}x")
    score = max(1.0, min(10.0, score))
    evidence = "；".join(evidence_parts) if evidence_parts else "流動性數據不足，使用基準分"
    reason = f"基於流動性指標：{evidence}"
    signal = "監察流動比率及短期債務到期情況"
    return score, reason, evidence, signal


def _score_valuation(d: Dict) -> tuple:
    pe = safe_number(d.get("pe_ratio"))
    pb = safe_number(d.get("pb_ratio"))
    sector_pe = safe_number(d.get("sector_pe", 15.0))
    if sector_pe <= 0:
        sector_pe = 15.0
    score = 5.0
    evidence_parts = []
    if pe > 0:
        if pe > sector_pe * 1.5:
            score += 2.0
            evidence_parts.append(f"P/E {pe:.1f}x 高於行業 {sector_pe:.1f}x")
        elif pe < sector_pe * 0.7:
            score -= 1.0
            evidence_parts.append(f"P/E {pe:.1f}x 低於行業 {sector_pe:.1f}x")
        else:
            evidence_parts.append(f"P/E {pe:.1f}x 接近行業均值")
    if pb > 0:
        if pb > 3.0:
            score += 1.0
            evidence_parts.append(f"P/B {pb:.2f}x 偏高")
        elif pb < 0.5:
            score -= 0.5
            evidence_parts.append(f"P/B {pb:.2f}x 低估")
        else:
            evidence_parts.append(f"P/B {pb:.2f}x")
    score = max(1.0, min(10.0, score))
    evidence = "；".join(evidence_parts) if evidence_parts else "估值數據不足，使用基準分"
    reason = f"基於估值指標：{evidence}"
    signal = "監察 P/E 相對行業變化及盈利預測修訂"
    return score, reason, evidence, signal


def _score_market(d: Dict) -> tuple:
    beta = safe_number(d.get("beta", 1.0))
    if beta <= 0:
        beta = 1.0
    week52_high = safe_number(d.get("week_52_high"))
    week52_low = safe_number(d.get("week_52_low"))
    current_price = safe_number(d.get("current_price"))
    score = 5.0
    evidence_parts = []
    if beta > 1.5:
        score += 1.5
        evidence_parts.append(f"Beta {beta:.2f} 高波動")
    elif beta < 0.7:
        score -= 0.5
        evidence_parts.append(f"Beta {beta:.2f} 低波動")
    else:
        evidence_parts.append(f"Beta {beta:.2f}")
    if week52_high > 0 and week52_low > 0 and current_price > 0:
        rng = week52_high - week52_low
        pos = (current_price - week52_low) / rng if rng > 0 else 0.5
        pct = int(pos * 100)
        if pos < 0.2:
            score += 1.0
            evidence_parts.append(f"現價接近52週低位（{pct}%位置）")
        elif pos > 0.8:
            score += 0.5
            evidence_parts.append(f"現價接近52週高位（{pct}%位置）")
        else:
            evidence_parts.append(f"52週位置 {pct}%")
    score = max(1.0, min(10.0, score))
    evidence = "；".join(evidence_parts) if evidence_parts else "市場數據不足，使用基準分"
    reason = f"基於市場指標：{evidence}"
    signal = "監察 Beta 變化及大市走勢"
    return score, reason, evidence, signal


def _score_policy(d: Dict) -> tuple:
    sector = str(d.get("sector", "")).lower()
    score = 5.0
    evidence_parts = []
    high_policy = ["bank", "finance", "telecom", "utility", "property", "real estate", "銀行", "電訊", "地產"]
    low_policy = ["tech", "consumer", "科技", "消費"]
    if any(s in sector for s in high_policy):
        score += 1.5
        evidence_parts.append(f"行業受監管政策影響較大")
    elif any(s in sector for s in low_policy):
        score -= 0.5
        evidence_parts.append(f"行業政策風險相對較低")
    else:
        evidence_parts.append("行業政策風險中等")
    score = max(1.0, min(10.0, score))
    evidence = "；".join(evidence_parts) if evidence_parts else "政策風險基準評估"
    reason = f"基於行業政策環境：{evidence}"
    signal = "監察監管政策變化及政府公告"
    return score, reason, evidence, signal


def _score_downside(d: Dict, other_scores: List[float]) -> tuple:
    avg_other = sum(other_scores) / len(other_scores) if other_scores else 5.0
    score = min(10.0, avg_other * 1.1)
    score = max(1.0, score)
    evidence = f"綜合其他6項風險均值 {avg_other:.1f}，下行情景風險相應調整"
    reason = f"基於整體風險組合評估下行情景：{evidence}"
    signal = "監察多項風險同時惡化的觸發因素"
    return score, reason, evidence, signal


def build_risk_assessment(report_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build a 7-category risk assessment from report_data.
    Returns dict with risk_items (exactly 7, no duplicates), composite_score,
    risk_label, total_weight (always 100%), top_risks.
    """
    market = report_data.get("market_data", {}) or {}
    fin = report_data.get("financial_analysis", {}) or {}
    history = report_data.get("financial_history", {}) or {}
    meta = report_data.get("report_metadata", {}) or {}
    d: Dict[str, Any] = {**meta, **history, **fin, **market}

    scorers = [
        _score_financial,
        _score_cashflow,
        _score_liquidity,
        _score_valuation,
        _score_market,
        _score_policy,
    ]

    items: List[Dict] = []
    raw_scores: List[float] = []

    for cat, scorer in zip(RISK_CATEGORIES[:6], scorers):
        score, reason, evidence, signal = scorer(d)
        raw_scores.append(score)
        items.append({
            "risk_name": cat["name"],
            "score": _fmt(score),
            "score_raw": score,
            "weight": f"{cat['weight']}%",
            "weight_raw": cat["weight"],
            "level": _level(score),
            "reason": reason,
            "evidence": evidence,
            "monitoring_signal": signal,
        })

    ds_score, ds_reason, ds_evidence, ds_signal = _score_downside(d, raw_scores)
    raw_scores.append(ds_score)
    items.append({
        "risk_name": RISK_CATEGORIES[6]["name"],
        "score": _fmt(ds_score),
        "score_raw": ds_score,
        "weight": f"{RISK_CATEGORIES[6]['weight']}%",
        "weight_raw": RISK_CATEGORIES[6]["weight"],
        "level": _level(ds_score),
        "reason": ds_reason,
        "evidence": ds_evidence,
        "monitoring_signal": ds_signal,
    })

    # Invariant checks
    total_weight = sum(c["weight"] for c in RISK_CATEGORIES)
    assert total_weight == 100, f"Weight sum error: {total_weight}"
    names = [i["risk_name"] for i in items]
    assert len(names) == len(set(names)), f"Duplicate risk names: {names}"

    weighted_score = sum(
        item["score_raw"] * item["weight_raw"] / 100
        for item in items
    )
    composite_label = _level(weighted_score)

    return {
        "risk_items": items,
        "composite_score": _fmt(weighted_score),
        "composite_score_raw": round(weighted_score, 2),
        "risk_label": composite_label,
        "total_weight": f"{total_weight}%",
        "category_count": len(items),
        "top_risks": sorted(items, key=lambda x: x["score_raw"], reverse=True)[:3],
    }
