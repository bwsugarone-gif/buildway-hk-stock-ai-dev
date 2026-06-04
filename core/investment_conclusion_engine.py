"""
core/investment_conclusion_engine.py
Investment Conclusion Engine — v4.2.1 RC (IC 2.0)

RC-2: Restructured to produce fund-research-grade conclusions even without DCF.
Output: investment_view, core_thesis, key_catalysts, key_risks,
        suitable_investor, allocation_suggestion + rating/horizon/summary.
Never outputs blank, placeholder conclusions, or legacy neutral fallback wording.
"""

from core.safe_math import safe_float
from core.client_polish import TARGET_PRICE_EXPLANATION, TARGET_PRICE_NOT_PROVIDED, UPSIDE_NOT_PROVIDED, NEUTRAL_CLIENT_SUMMARY


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

INSUFFICIENT_DATA_RATING = "資料不足"
INSUFFICIENT_DATA_VIEW = "資料不足，暫不評級"
INSUFFICIENT_DATA_SUMMARY = "公司資料已驗證，但市場價格、財務數據或新聞資料不足，暫不形成投資評級。"
PARTIAL_DATA_LABEL = "部分資料覆蓋"
FULL_DATA_LABEL = "完整資料覆蓋"


def _has_positive(value) -> bool:
    return safe_float(value) > 0


def _has_valid_market_price(*payloads) -> bool:
    price_fields = ("current_price", "price", "last_price", "close", "regularMarketPrice")
    for payload in payloads:
        if not isinstance(payload, dict):
            continue
        if any(_has_positive(payload.get(field)) for field in price_fields):
            return True
    return False


def _raw_market(market_snapshot: dict) -> dict:
    raw = market_snapshot.get("_raw", {}) if isinstance(market_snapshot, dict) else {}
    return raw if isinstance(raw, dict) else {}


def _news_available(agent_opinions, source_registry: dict) -> bool:
    news_entry = (source_registry or {}).get("news", {})
    if isinstance(news_entry, dict) and news_entry.get("verified"):
        return True

    agents_list = []
    if isinstance(agent_opinions, dict):
        agents_list = agent_opinions.get("agents", [])
    elif isinstance(agent_opinions, list):
        agents_list = agent_opinions
    if isinstance(agents_list, dict):
        agents_list = list(agents_list.values())

    for item in agents_list or []:
        if not isinstance(item, dict):
            continue
        text = " ".join(str(item.get(k, "")) for k in ("Agent", "agent_name", "source", "stance", "summary"))
        if any(token in text.lower() for token in ("news", "新聞", "sentiment", "catalyst")):
            return True
    return False


def _coverage_pct(source_registry: dict) -> float:
    try:
        from core.source_registry import compute_coverage_pct

        return float(compute_coverage_pct(source_registry or {}))
    except Exception:
        return 0.0


def _source_verified(source_registry: dict, key: str) -> bool:
    entry = (source_registry or {}).get(key, {})
    return isinstance(entry, dict) and bool(entry.get("verified"))


def _coverage_flags(
    market_snapshot: dict,
    financial_data: dict,
    risk_assessment: dict,
    agent_opinions,
    source_registry: dict,
) -> dict:
    raw = _raw_market(market_snapshot)
    financial_data = financial_data or {}
    risk_assessment = risk_assessment or {}
    source_registry = source_registry or {}

    price_available = _has_valid_market_price(raw, financial_data)
    price_unavailable_flag = bool(
        raw.get("price_unavailable")
        or raw.get("valid_ticker_price_unavailable")
        or financial_data.get("price_unavailable")
        or financial_data.get("valid_ticker_price_unavailable")
    )

    valuation_available = any(
        _has_positive(v)
        for v in (
            raw.get("pe"),
            raw.get("pb"),
            raw.get("pe_ratio"),
            raw.get("pb_ratio"),
            financial_data.get("pe_ratio"),
            financial_data.get("pb_ratio"),
            financial_data.get("trailingPE"),
            financial_data.get("priceToBook"),
        )
    )
    financial_available = any(
        _has_positive(v)
        for v in (
            financial_data.get("revenue"),
            financial_data.get("revenue_ttm"),
            financial_data.get("totalRevenue"),
            financial_data.get("net_profit"),
            financial_data.get("net_income"),
            financial_data.get("net_income_ttm"),
            financial_data.get("roe"),
            financial_data.get("net_margin"),
            financial_data.get("ebitda"),
        )
    )
    risk_available = bool(
        risk_assessment.get("risk_items")
        or risk_assessment.get("dimension_scores")
        or risk_assessment.get("composite_score")
        or risk_assessment.get("composite_risk_score")
    )
    news_available = _news_available(agent_opinions, source_registry)
    metadata_available = any(
        str(v or "").strip()
        for v in (
            raw.get("ticker"),
            raw.get("company_name"),
            raw.get("company_name_zh"),
            raw.get("sector"),
            financial_data.get("ticker"),
            financial_data.get("company_name"),
            financial_data.get("sector"),
        )
    ) or _source_verified(source_registry, "company_metadata")

    return {
        "metadata_available": metadata_available,
        "price_available": price_available,
        "price_unavailable_flag": price_unavailable_flag,
        "stale_price_unavailable_flag_ignored": bool(price_available and price_unavailable_flag),
        "valuation_available": valuation_available,
        "financial_available": financial_available,
        "risk_available": risk_available,
        "news_available": news_available,
    }


def _coverage_state(flags: dict) -> str:
    if not flags["price_available"]:
        return "INSUFFICIENT"
    if not flags["risk_available"]:
        return "INSUFFICIENT"
    if not (flags["valuation_available"] or flags["financial_available"]):
        return "INSUFFICIENT"
    if flags["financial_available"] and flags["risk_available"] and flags["news_available"]:
        return "FULL"
    return "PARTIAL"


def _data_sufficiency_issues(
    market_snapshot: dict,
    financial_data: dict,
    risk_assessment: dict,
    agent_opinions,
    source_registry: dict,
) -> list[dict]:
    source_registry = source_registry or {}
    flags = _coverage_flags(market_snapshot, financial_data, risk_assessment, agent_opinions, source_registry)

    issues = []
    if not flags["price_available"]:
        issues.append({"factor": "市場價格", "weight": "必要", "score": "N/A", "summary": "市場價格暫時未能取得"})
    if not flags["valuation_available"]:
        issues.append({"factor": "估值資料", "weight": "必要", "score": "N/A", "summary": "缺少 P/E、P/B 或其他估值輸入"})
    if not flags["financial_available"]:
        issues.append({"factor": "財務資料", "weight": "必要", "score": "N/A", "summary": "缺少收入、盈利、ROE、利潤率或 EBITDA 等財務資料"})
    if not flags["news_available"]:
        issues.append({"factor": "新聞情緒", "weight": "必要", "score": "N/A", "summary": "缺少已驗證新聞或情緒資料"})
    if not flags["risk_available"]:
        issues.append({"factor": "風險評估", "weight": "必要", "score": "N/A", "summary": "缺少有效風險評估輸入"})

    if source_registry:
        market_verified = _source_verified(source_registry, "market_data")
        financial_verified = _source_verified(source_registry, "financial_statement")
        news_verified = _source_verified(source_registry, "news")
        if not any((market_verified, financial_verified, news_verified)):
            issues.append({
                "factor": "來源覆蓋",
                "weight": "必要",
                "score": "N/A",
                "summary": "source_registry 只顯示 metadata/master data，缺少核心市場、財務或新聞來源",
            })
        coverage = _coverage_pct(source_registry)
        if coverage and coverage < 50:
            issues.append({
                "factor": "資料覆蓋率",
                "weight": "必要",
                "score": "N/A",
                "summary": f"資料覆蓋率過低（{coverage:.1f}%）",
            })

    deduped = []
    seen = set()
    for issue in issues:
        key = issue["factor"]
        if key not in seen:
            seen.add(key)
            deduped.append(issue)
    return deduped


def _insufficient_data_result(decision_basis: list[dict]) -> dict:
    return {
        "rating": INSUFFICIENT_DATA_RATING,
        "score": None,
        "composite_score": "N/A",
        "investment_view": INSUFFICIENT_DATA_VIEW,
        "recommendation": "暫不評級",
        "investment_horizon": None,
        "horizon": None,
        "suitable_investor": None,
        "investor_type": None,
        "target_price": None,
        "potential_upside": None,
        "upside": None,
        "allocation_suggestion": None,
        "confidence": 0,
        "decision_basis": decision_basis,
        "final_summary": INSUFFICIENT_DATA_SUMMARY,
        "conclusion_summary": INSUFFICIENT_DATA_SUMMARY,
        "summary": INSUFFICIENT_DATA_SUMMARY,
        "valuation_score": None,
        "risk_score": None,
        "financial_score": None,
        "news_score": None,
        "market_score": None,
        "data_sufficient": False,
        "data_coverage": "INSUFFICIENT",
        "data_coverage_label": "資料不足",
    }


def _invalid_result(reason: str = "股票代號或市場資料無法驗證") -> dict:
    return {
        "rating": "無法評估",
        "score": None,
        "composite_score": "N/A",
        "investment_view": "資料驗證未完成",
        "recommendation": "無法評估",
        "investment_horizon": None,
        "horizon": None,
        "suitable_investor": None,
        "investor_type": None,
        "target_price": None,
        "potential_upside": None,
        "upside": None,
        "allocation_suggestion": None,
        "confidence": 0,
        "decision_basis": [{"factor": "股票代號驗證", "weight": "必要", "score": "N/A", "summary": reason}],
        "final_summary": "股票代號或市場資料無法驗證，系統不形成投資評級。",
        "conclusion_summary": "股票代號或市場資料無法驗證，系統不形成投資評級。",
        "summary": "股票代號或市場資料無法驗證，系統不形成投資評級。",
        "valuation_score": None,
        "risk_score": None,
        "financial_score": None,
        "news_score": None,
        "market_score": None,
        "data_sufficient": False,
        "data_coverage": "INVALID",
        "data_coverage_label": "無法驗證",
        "invalid_symbol": True,
    }


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


def _score_or_none(val) -> float | None:
    try:
        s = str(val).replace("/10", "").replace("%", "").strip()
        f = float(s)
        if 0 <= f <= 10:
            return f
        if 0 <= f <= 100:
            return f / 10
    except (TypeError, ValueError):
        return None
    return None


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
    raw = market_snapshot.get("_raw", {}) or {}
    pe = safe_float(raw.get("pe") or raw.get("pe_ratio") or financial_data.get("pe_ratio"))
    pb = safe_float(raw.get("pb") or raw.get("pb_ratio") or financial_data.get("pb_ratio"))

    if not pe and not pb:
        return None, "估值資料不足"

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
    composite = risk_assessment.get("composite_score") or risk_assessment.get("composite_risk_score")
    score = _score_or_none(composite)
    if score is None:
        return None, "風險評估資料不足", None
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
    revenue = safe_float(financial_data.get("revenue") or financial_data.get("revenue_ttm") or financial_data.get("totalRevenue"))
    net_profit = safe_float(financial_data.get("net_profit") or financial_data.get("net_income") or financial_data.get("net_income_ttm"))
    roe = safe_float(financial_data.get("roe"))
    net_margin = safe_float(financial_data.get("net_margin"))

    if not any([revenue, net_profit, roe]):
        return None, "財務資料不足"

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


def _extract_news_score(agent_opinions) -> tuple:
    """Extract news/sentiment score from agent opinions.
    Accepts either a list of opinion dicts or a dict with an 'agents' key.
    """
    # Normalise to a flat list
    if isinstance(agent_opinions, dict):
        agents_list = agent_opinions.get("agents", [])
    elif isinstance(agent_opinions, list):
        agents_list = agent_opinions
    else:
        agents_list = []

    news_agent = next(
        (
            a for a in agents_list
            if any(token in str(a.get("Agent", a.get("agent_name", ""))).lower() for token in ("新聞", "news", "sentiment"))
        ),
        None
    )
    if not news_agent:
        return None, "新聞情緒資料不足"

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
    wk52_high = safe_float(raw.get("fifty_two_week_high") or raw.get("52w_high"))
    wk52_low = safe_float(raw.get("fifty_two_week_low") or raw.get("52w_low"))

    if not current or not wk52_high or not wk52_low:
        return None, "市場資料不足"

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
    raw = _raw_market(market_snapshot)
    financial_data = financial_data or {}
    if raw.get("invalid_symbol") or financial_data.get("invalid_symbol") or financial_data.get("data_confidence") == "INVALID":
        return _invalid_result(
            financial_data.get("validation_reason")
            or raw.get("validation_reason")
            or "股票代號或市場資料無法驗證"
        )

    coverage_flags = _coverage_flags(
        market_snapshot,
        financial_data,
        risk_assessment,
        agent_opinions,
        source_registry,
    )
    coverage_state = _coverage_state(coverage_flags)
    insufficiency_issues = _data_sufficiency_issues(
        market_snapshot,
        financial_data,
        risk_assessment,
        agent_opinions,
        source_registry,
    )
    if coverage_state == "INSUFFICIENT":
        return _insufficient_data_result(insufficiency_issues)

    val_score, val_summary   = _extract_valuation_score(market_snapshot, financial_data)
    risk_inv, risk_summary, raw_risk = _extract_risk_score(risk_assessment)
    fin_score, fin_summary   = _extract_financial_score(financial_data)
    news_score, news_summary = _extract_news_score(agent_opinions)
    mkt_score, mkt_summary   = _extract_market_score(market_snapshot)
    if risk_inv is None or raw_risk is None:
        return _insufficient_data_result([
            {"factor": "風險評估", "weight": "必要", "score": "N/A", "summary": "缺少有效風險評估輸入"}
        ])
    if val_score is None and fin_score is None:
        return _insufficient_data_result([
            {"factor": "估值或財務資料", "weight": "必要", "score": "N/A", "summary": "缺少估值及財務輸入"}
        ])
    if mkt_score is None:
        mkt_score = 5.0
        mkt_summary = "市場價格已取得，52週區間資料有限"

    # ── Weighted composite score ──────────────────────────────────────────────
    score_components = [
        ("估值", val_score, 0.25, val_summary),
        ("風險", risk_inv, 0.25, risk_summary),
        ("財務", fin_score, 0.20, fin_summary),
        ("新聞", news_score, 0.15, news_summary),
        ("市場", mkt_score, 0.15, mkt_summary),
    ]
    usable_components = [(name, score, weight, summary) for name, score, weight, summary in score_components if score is not None]
    weight_total = sum(weight for _, _, weight, _ in usable_components) or 1.0
    composite = sum(score * weight for _, score, weight, _ in usable_components) / weight_total
    composite = round(composite, 1)

    # ── Derive outputs ────────────────────────────────────────────────────────
    rating          = _score_to_rating(composite)
    if coverage_state == "PARTIAL" and rating == "買入":
        rating = "觀察"
    horizon         = _score_to_horizon(composite, raw_risk)
    investor_type   = _score_to_investor_type(composite, raw_risk)
    confidence_cap  = 80 if coverage_state == "PARTIAL" else 95
    confidence_pct  = int(min(confidence_cap, max(30, composite * 10)))

    # ── Target price ─────────────────────────────────────────────────────────
    # Cannot reliably estimate without DCF/analyst consensus — say so clearly
    current_price = safe_float(market_snapshot.get("_raw", {}).get("current_price"))
    target_price_note = TARGET_PRICE_NOT_PROVIDED
    potential_upside = UPSIDE_NOT_PROVIDED
    target_price_explanation = TARGET_PRICE_EXPLANATION

    # ── Decision basis ────────────────────────────────────────────────────────
    decision_basis = []
    if coverage_flags.get("stale_price_unavailable_flag_ignored"):
        decision_basis.append({
            "factor": "Market price",
            "weight": "Required",
            "score": "Verified",
            "summary": "市場價格存在，已忽略過時 price_unavailable flag。",
        })
    factor_weights = {"估值": "25%", "風險": "25%", "財務": "20%", "新聞": "15%", "市場": "15%"}
    for name, score, _weight, summary in score_components:
        decision_basis.append({
            "factor": name,
            "weight": factor_weights[name],
            "score": f"{score:.1f}/10" if score is not None else "N/A",
            "summary": summary,
        })
    if coverage_state == "PARTIAL":
        decision_basis.append({
            "factor": "資料覆蓋",
            "weight": "提示",
            "score": PARTIAL_DATA_LABEL,
            "summary": "本次有市場價格、風險評估，以及估值或財務資料；缺失項目已降低信心度，不等同整體資料不足。",
        })

    # ── Final summary ─────────────────────────────────────────────────────────
    rating_desc = {
        "買入": "綜合分析顯示股票具備投資吸引力，建議考慮買入。",
        "觀察": "股票具備一定潛力，但需等待更明確催化劑，建議列入觀察名單。",
        "中性": "股票估值合理，風險與回報相對平衡，建議維持觀察。",
        "減持": "股票面臨較大下行風險，建議考慮減持。",
        "避免": "股票風險偏高或估值過貴，建議暫時避免。",
    }
    final_summary = (
        f"綜合評分 {composite}/10，投資評級：{rating}。"
        f"{rating_desc.get(rating, '')} "
        f"適合{investor_type}投資者，建議投資週期：{horizon}。"
    )
    if coverage_state == "PARTIAL":
        final_summary = f"{PARTIAL_DATA_LABEL}：{final_summary}"
    if rating == "中性":
        final_summary = NEUTRAL_CLIENT_SUMMARY

    return {
        "rating":             rating,
        "composite_score":    f"{composite}/10",
        "investment_horizon": horizon,
        "suitable_investor":  investor_type,
        "target_price":       target_price_note,
        "potential_upside":   potential_upside,
        "upside":             potential_upside,
        "target_price_explanation": target_price_explanation,
        "recommendation":     rating,
        "investment_view":    f"{rating}（{PARTIAL_DATA_LABEL}）" if coverage_state == "PARTIAL" else rating,
        "allocation_suggestion": "以小注觀察或等待資料補齊後再提高倉位" if coverage_state == "PARTIAL" else "按投資者風險承受能力分段配置",
        "confidence":         confidence_pct,
        "decision_basis":     decision_basis,
        "final_summary":      final_summary,
        "conclusion_summary":  final_summary,
        "summary":            final_summary,
        # Individual scores for display
        "valuation_score":    f"{val_score:.1f}/10" if val_score is not None else None,
        "risk_score":         f"{raw_risk:.1f}/10",
        "financial_score":    f"{fin_score:.1f}/10" if fin_score is not None else None,
        "news_score":         f"{news_score:.1f}/10" if news_score is not None else None,
        "market_score":       f"{mkt_score:.1f}/10",
        "data_sufficient":    True,
        "data_coverage":      coverage_state,
        "data_coverage_label": FULL_DATA_LABEL if coverage_state == "FULL" else PARTIAL_DATA_LABEL,
    }
