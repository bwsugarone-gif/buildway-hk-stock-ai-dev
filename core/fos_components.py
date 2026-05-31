"""
core/fos_components.py
FOS V3.5 — Investor Decision Cockpit Components
v3.5.0: Peer Comparison, Source Transparency, Bull vs Bear Debate, Risk Dashboard
"""
from __future__ import annotations
from typing import Any, Dict, List, Optional
import streamlit as st


# ─── helpers ──────────────────────────────────────────────────────────────────

def _safe(d: Dict, *keys, default="—"):
    for k in keys:
        if isinstance(d, dict):
            d = d.get(k, default)
        else:
            return default
    return d if d not in (None, "", "N/A") else default


def _pct_bar(value: float, color: str = "#1a73e8") -> str:
    pct = max(0, min(100, float(value or 0)))
    return (
        f'<div style="background:#e8eaed;border-radius:4px;height:8px;width:100%;">'
        f'<div style="background:{color};width:{pct}%;height:8px;border-radius:4px;"></div>'
        f'</div><small style="color:#5f6368;">{pct:.0f}%</small>'
    )


def _badge(text: str, color: str = "#1a73e8") -> str:
    return (
        f'<span style="background:{color};color:#fff;padding:2px 10px;'
        f'border-radius:12px;font-size:0.78rem;font-weight:600;">{text}</span>'
    )


def _risk_color(level: str) -> str:
    l = str(level).upper()
    if any(x in l for x in ("HIGH", "高", "嚴重")):
        return "#d93025"
    if any(x in l for x in ("MEDIUM", "MED", "中")):
        return "#f29900"
    return "#1e8e3e"


def _confidence_color(score: float) -> str:
    if score >= 75:
        return "#1e8e3e"
    if score >= 50:
        return "#f29900"
    return "#d93025"


# ─── 1. Company Profile Sidebar ───────────────────────────────────────────────

def render_company_sidebar(report_data: Dict[str, Any]) -> None:
    """Render company profile in the Streamlit sidebar."""
    cover = report_data.get("cover", {}) or {}
    meta  = report_data.get("company_metadata", {}) or {}
    mkt   = report_data.get("market_data", {}) or {}

    ticker  = _safe(cover, "ticker")
    name    = _safe(cover, "company_name") or _safe(meta, "name")
    sector  = _safe(meta, "sector") or _safe(cover, "sector", default="—")
    mktcap  = _safe(mkt, "market_cap_hkd") or _safe(cover, "market_cap")
    biz     = _safe(meta, "business_description", default="—")
    markets = _safe(meta, "main_markets", default="—")
    founded = _safe(meta, "founded_year", default="—")
    emp     = _safe(meta, "employees", default="—")
    website = _safe(meta, "website", default="—")

    with st.sidebar:
        st.markdown("---")
        st.markdown("### 🏢 公司資料")
        if ticker and ticker != "—":
            st.markdown(f"**{name}**  \n`{ticker}`")
        else:
            st.markdown(f"**{name}**")

        rows = [
            ("行業", sector),
            ("市值", mktcap),
            ("核心業務", biz),
            ("主要市場", markets),
            ("成立年份", str(founded)),
            ("員工人數", str(emp)),
        ]
        for label, val in rows:
            st.markdown(f"**{label}**  \n{val}")

        if website and website != "—":
            st.markdown(f"**官方網站**  \n[{website}]({website})")
        st.markdown("---")


# ─── 2. Competitive Landscape ─────────────────────────────────────────────────

def render_competitive_landscape(report_data: Dict[str, Any]) -> None:
    """Competitive landscape — products, position, strengths, weaknesses, strategy."""
    peer = report_data.get("peer_comparison", {}) or {}
    comp = report_data.get("competitive_analysis", {}) or {}

    st.markdown("## 🏆 競爭格局分析")

    # Subject company summary
    cover = report_data.get("cover", {}) or {}
    name  = _safe(cover, "company_name", default="目標公司")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"#### {name}")
        products  = _safe(comp, "products", default=_safe(peer, "products"))
        position  = _safe(comp, "market_position", default=_safe(peer, "market_position"))
        strengths = _safe(comp, "strengths", default=_safe(peer, "strengths"))
        weaknesses= _safe(comp, "weaknesses", default=_safe(peer, "weaknesses"))
        strategy  = _safe(comp, "future_strategy", default=_safe(peer, "future_strategy"))

        for label, val in [
            ("📦 產品線", products),
            ("📍 市場定位", position),
            ("✅ 優勢", strengths),
            ("⚠️ 弱點", weaknesses),
            ("🔭 未來策略", strategy),
        ]:
            st.markdown(f"**{label}**  \n{val}")

    with col2:
        st.markdown("#### 競爭對手摘要")
        peers = peer.get("peers", []) or comp.get("competitors", []) or []
        if peers:
            for p in peers[:4]:
                if isinstance(p, dict):
                    pname = p.get("name", p.get("ticker", "—"))
                    pdesc = p.get("summary", p.get("description", "—"))
                    st.markdown(f"**{pname}**  \n{pdesc}")
                    st.markdown("---")
                else:
                    st.markdown(f"- {p}")
        else:
            st.info("競爭對手資料待補充")


# ─── 3. Confidence Score Breakdown ────────────────────────────────────────────

def render_confidence_breakdown(report_data: Dict[str, Any]) -> None:
    """5-dimension confidence score breakdown."""
    conf = report_data.get("data_confidence", {}) or {}
    cover= report_data.get("cover", {}) or {}

    # Try to get overall score
    overall_raw = (
        conf.get("overall_score")
        or conf.get("score")
        or cover.get("data_confidence_score")
        or 0
    )
    try:
        overall = float(overall_raw)
    except (TypeError, ValueError):
        overall = 0.0

    level_text = str(conf.get("level") or cover.get("data_confidence") or "").upper()
    if not overall:
        if "HIGH" in level_text:
            overall = 85.0
        elif "MEDIUM" in level_text:
            overall = 60.0
        elif "LOW" in level_text:
            overall = 35.0

    color = _confidence_color(overall)

    st.markdown("## 📊 資料可信度評分")
    st.markdown(
        f'<div style="font-size:2.2rem;font-weight:700;color:{color};">'
        f'{overall:.0f}<span style="font-size:1rem;"> / 100</span></div>',
        unsafe_allow_html=True,
    )

    dimensions = [
        ("財務數據覆蓋率", conf.get("financial_coverage", conf.get("financial_data_coverage", 0))),
        ("新聞驗證",       conf.get("news_verification", conf.get("news_score", 0))),
        ("HKEX 驗證",     conf.get("hkex_verification", conf.get("hkex_score", 0))),
        ("Agent 共識度",  conf.get("agent_consensus", conf.get("consensus_score", 0))),
        ("數據新鮮度",    conf.get("data_freshness", conf.get("freshness_score", 0))),
    ]

    for dim_name, raw_val in dimensions:
        try:
            val = float(raw_val or 0)
        except (TypeError, ValueError):
            val = 0.0
        c = _confidence_color(val)
        st.markdown(f"**{dim_name}**", unsafe_allow_html=False)
        st.markdown(_pct_bar(val, c), unsafe_allow_html=True)

    # Sources
    sources = conf.get("sources", []) or []
    if sources:
        st.markdown("**已驗證來源**")
        for s in sources:
            st.markdown(f"✓ {s}")


# ─── 4. Risk Event Cards ──────────────────────────────────────────────────────

def render_risk_event_cards(report_data: Dict[str, Any]) -> None:
    """Risk event cards with category, reason, probability, impact, monitoring."""
    # canonical key first, legacy key as fallback
    risk = (
        report_data.get("risk_assessment_v2", {})
        or report_data.get("risk_analysis", {})
        or {}
    )
    items = risk.get("risk_items", risk.get("risks", risk.get("risk_factors", []))) or []

    st.markdown("## ⚠️ 風險事件分析")

    if not items:
        # Try to build from flat risk fields
        flat_risks = []
        for key, label in [
            ("liquidity_risk",  "流動性風險"),
            ("valuation_risk",  "估值風險"),
            ("market_risk",     "市場風險"),
            ("financial_risk",  "財務風險"),
            ("news_risk",       "新聞風險"),
        ]:
            val = risk.get(key)
            if val:
                flat_risks.append({
                    "category": label,
                    "reason": str(val),
                    "probability": risk.get(f"{key}_probability", "中"),
                    "impact": risk.get(f"{key}_impact", "中"),
                    "monitoring": risk.get(f"{key}_monitoring", "持續監察"),
                })
        items = flat_risks

    if not items:
        st.info("風險資料待分析")
        return

    for item in items:
        if not isinstance(item, dict):
            continue
        category   = item.get("category", item.get("type", "風險"))
        reason     = item.get("reason", item.get("description", "—"))
        prob       = item.get("probability", item.get("prob", "中"))
        impact     = item.get("impact", item.get("impact_level", "中"))
        monitoring = item.get("monitoring", item.get("suggested_monitoring", "持續監察"))

        prob_color   = _risk_color(prob)
        impact_color = _risk_color(impact)

        with st.container():
            st.markdown(
                f'<div style="border-left:4px solid {impact_color};'
                f'padding:12px 16px;margin-bottom:12px;background:#fafafa;border-radius:4px;">'
                f'<strong style="font-size:1rem;">{category}</strong><br>'
                f'<span style="color:#5f6368;font-size:0.9rem;">{reason}</span><br><br>'
                f'{_badge(f"概率：{prob}", prob_color)} &nbsp;'
                f'{_badge(f"影響：{impact}", impact_color)}<br><br>'
                f'<span style="font-size:0.85rem;">📋 建議監察：{monitoring}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )


# ─── 5. Multi-Agent Investment Committee ──────────────────────────────────────

def render_multi_agent_committee(report_data: Dict[str, Any]) -> None:
    """6-agent investment committee — each shows opinion, reasoning, confidence."""
    ic = report_data.get("investment_committee", {}) or {}
    agents_data = ic.get("agents", {}) or {}

    st.markdown("## 🏛️ AI 投資委員會")

    agent_defs = [
        ("financial_agent",  "💹 財務 Agent",  "#1a73e8"),
        ("valuation_agent",  "📐 估值 Agent",  "#7b1fa2"),
        ("market_agent",     "📈 市場 Agent",  "#0097a7"),
        ("risk_agent",       "🛡️ 風險 Agent",  "#d93025"),
        ("news_agent",       "📰 新聞 Agent",  "#f57c00"),
        ("pm_agent",         "🎯 PM Agent",    "#2e7d32"),
    ]

    cols = st.columns(3)
    for idx, (key, label, color) in enumerate(agent_defs):
        agent = agents_data.get(key, {}) or {}
        # Fallback: try top-level keys
        if not agent:
            agent = ic.get(key, {}) or {}

        opinion    = agent.get("opinion", agent.get("view", agent.get("stance", "觀點待整合")))
        reasoning  = agent.get("reasoning", agent.get("rationale", agent.get("analysis", "論據待整合")))
        confidence = agent.get("confidence", agent.get("confidence_score", 0))
        try:
            conf_val = float(confidence or 0)
        except (TypeError, ValueError):
            conf_val = 0.0

        with cols[idx % 3]:
            st.markdown(
                f'<div style="border:1px solid {color};border-radius:8px;'
                f'padding:14px;margin-bottom:12px;">'
                f'<div style="color:{color};font-weight:700;font-size:0.95rem;">{label}</div>'
                f'<div style="margin:8px 0;font-weight:600;">{opinion}</div>'
                f'<div style="color:#5f6368;font-size:0.85rem;margin-bottom:8px;">{reasoning}</div>'
                f'{_pct_bar(conf_val, color)}'
                f'<div style="font-size:0.78rem;color:#5f6368;margin-top:2px;">信心指數</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

    # Committee verdict
    verdict   = ic.get("verdict", ic.get("final_recommendation", ic.get("committee_summary", "")))
    bull_score= ic.get("bull_score", 0)
    bear_score= ic.get("bear_score", 0)
    ic_conf   = ic.get("confidence", ic.get("overall_confidence", 0))

    if verdict or bull_score or bear_score:
        st.markdown("---")
        st.markdown("### 📋 委員會裁決")
        m1, m2, m3 = st.columns(3)
        with m1:
            st.metric("牛市評分", f"{bull_score or '—'}")
        with m2:
            st.metric("熊市評分", f"{bear_score or '—'}")
        with m3:
            st.metric("整體信心", f"{ic_conf or '—'}")
        if verdict:
            st.markdown(f"> {verdict}")


# ─── 6. Market Snapshot ───────────────────────────────────────────────────────

def render_market_snapshot(report_data: Dict[str, Any]) -> None:
    """52-week price range and volume snapshot."""
    mkt = report_data.get("market_data", {}) or {}

    price     = mkt.get("current_price") or mkt.get("price")
    high_52w  = mkt.get("week_52_high") or mkt.get("high_52w")
    low_52w   = mkt.get("week_52_low")  or mkt.get("low_52w")
    volume    = mkt.get("volume") or mkt.get("avg_volume")
    change_pct= mkt.get("change_pct") or mkt.get("price_change_pct")

    st.markdown("## 📉 市場快照")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("現價 (HKD)", f"{price or '—'}")
    with c2:
        st.metric("52週高", f"{high_52w or '—'}")
    with c3:
        st.metric("52週低", f"{low_52w or '—'}")
    with c4:
        delta_str = f"{change_pct:+.2f}%" if change_pct else None
        st.metric("成交量", f"{volume or '—'}", delta=delta_str)

    # Price position bar
    try:
        p  = float(price or 0)
        hi = float(high_52w or 0)
        lo = float(low_52w or 0)
        if hi > lo and p:
            position_pct = (p - lo) / (hi - lo) * 100
            st.markdown("**52週價格區間位置**")
            st.markdown(
                f'<div style="position:relative;background:linear-gradient(to right,#d93025,#f29900,#1e8e3e);'
                f'height:12px;border-radius:6px;margin:4px 0;">'
                f'<div style="position:absolute;left:{position_pct:.1f}%;top:-4px;'
                f'width:4px;height:20px;background:#102a43;border-radius:2px;"></div>'
                f'</div>'
                f'<div style="display:flex;justify-content:space-between;font-size:0.78rem;color:#5f6368;">'
                f'<span>低 {lo}</span><span>現價 {p}</span><span>高 {hi}</span></div>',
                unsafe_allow_html=True,
            )
    except (TypeError, ValueError):
        pass


# ─── 7. Financial Trend Charts ────────────────────────────────────────────────

def render_financial_trends(report_data: Dict[str, Any]) -> None:
    """Revenue / EBITDA / Net Profit / FCF 3-year trend charts."""
    fin = report_data.get("financial_analysis", {}) or {}
    trends = fin.get("trends", fin.get("financial_trends", {})) or {}

    st.markdown("## 📊 財務趨勢（三年）")

    metrics = [
        ("revenue",     "收入趨勢"),
        ("ebitda",      "EBITDA 趨勢"),
        ("net_profit",  "淨利潤趨勢"),
        ("fcf",         "自由現金流趨勢"),
    ]

    try:
        import plotly.graph_objects as go
        use_plotly = True
    except ImportError:
        use_plotly = False

    cols = st.columns(2)
    for i, (key, label) in enumerate(metrics):
        data = trends.get(key, []) or fin.get(key, []) or []
        if not data or not isinstance(data, list):
            continue

        years  = [str(d.get("year", d.get("period", f"Y{j+1}"))) for j, d in enumerate(data)]
        values = []
        for d in data:
            try:
                values.append(float(d.get("value", d.get("amount", 0)) or 0))
            except (TypeError, ValueError):
                values.append(0.0)

        with cols[i % 2]:
            st.markdown(f"**{label}**")
            if use_plotly:
                fig = go.Figure(go.Bar(
                    x=years, y=values,
                    marker_color=["#1a73e8"] * len(values),
                    text=[f"{v:,.0f}" for v in values],
                    textposition="outside",
                ))
                fig.update_layout(
                    height=220, margin=dict(l=0, r=0, t=10, b=0),
                    plot_bgcolor="white", paper_bgcolor="white",
                    yaxis=dict(showgrid=True, gridcolor="#e8eaed"),
                    xaxis=dict(showgrid=False),
                    showlegend=False,
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                import pandas as pd
                df = pd.DataFrame({"年份": years, label: values}).set_index("年份")
                st.bar_chart(df)


# ─── 8. News Sentiment Dashboard ──────────────────────────────────────────────

def render_news_sentiment(report_data: Dict[str, Any]) -> None:
    """News sentiment counts, credibility, catalysts, watchlist."""
    news = report_data.get("news_analysis", {}) or {}

    positive  = news.get("positive_count", news.get("positive", 0)) or 0
    neutral   = news.get("neutral_count",  news.get("neutral",  0)) or 0
    negative  = news.get("negative_count", news.get("negative", 0)) or 0
    credibility = news.get("credibility", news.get("news_credibility", "—"))
    catalysts = news.get("catalysts", news.get("catalyst_events", [])) or []
    watchlist = news.get("watchlist", news.get("monitoring_items", [])) or []

    st.markdown("## 📰 新聞情緒分析")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("正面新聞", positive)
    with c2:
        st.metric("中性新聞", neutral)
    with c3:
        st.metric("負面新聞", negative)
    with c4:
        st.metric("新聞可信度", credibility)

    if catalysts:
        st.markdown("**催化事件**")
        for c in catalysts[:5]:
            st.markdown(f"🔔 {c}")

    if watchlist:
        st.markdown("**監察事項**")
        for w in watchlist[:5]:
            st.markdown(f"👁️ {w}")


# ─── 9. Investment Conclusion Card ────────────────────────────────────────────

def render_investment_conclusion(report_data: Dict[str, Any]) -> None:
    """Final investment conclusion card."""
    conc = report_data.get("investment_conclusion", {}) or {}
    ic   = report_data.get("investment_committee", {}) or {}

    rating   = conc.get("rating", conc.get("recommendation", ic.get("final_recommendation", "—")))
    horizon  = conc.get("horizon", conc.get("investment_horizon", "—"))
    profile  = conc.get("investor_profile", conc.get("suitable_for", "—"))
    summary  = conc.get("summary", conc.get("conclusion_summary", ic.get("committee_summary", "")))
    target   = conc.get("target_price", conc.get("price_target", "—"))
    upside   = conc.get("upside", conc.get("upside_pct", "—"))

    RATING_COLORS = {
        "買入": "#1e8e3e", "BUY": "#1e8e3e",
        "觀察": "#0097a7", "WATCH": "#0097a7",
        "中性": "#5f6368", "NEUTRAL": "#5f6368", "HOLD": "#5f6368",
        "減持": "#f57c00", "REDUCE": "#f57c00",
        "避免": "#d93025", "AVOID": "#d93025", "SELL": "#d93025",
    }
    r_color = RATING_COLORS.get(str(rating).upper(), RATING_COLORS.get(str(rating), "#1a73e8"))

    st.markdown("## 🎯 最終投資結論")
    st.markdown(
        f'<div style="border:2px solid {r_color};border-radius:12px;padding:24px;'
        f'background:linear-gradient(135deg,#fff 80%,{r_color}18);">'
        f'<div style="font-size:2rem;font-weight:800;color:{r_color};">{rating}</div>'
        f'<div style="display:flex;gap:24px;margin:16px 0;flex-wrap:wrap;">'
        f'<div><span style="color:#5f6368;font-size:0.85rem;">投資週期</span><br>'
        f'<strong>{horizon}</strong></div>'
        f'<div><span style="color:#5f6368;font-size:0.85rem;">適合投資者</span><br>'
        f'<strong>{profile}</strong></div>'
        f'<div><span style="color:#5f6368;font-size:0.85rem;">目標價</span><br>'
        f'<strong>{target}</strong></div>'
        f'<div><span style="color:#5f6368;font-size:0.85rem;">潛在升幅</span><br>'
        f'<strong>{upside}</strong></div>'
        f'</div>'
        f'{"<p style=color:#1f2933;>" + summary + "</p>" if summary else ""}'
        f'</div>',
        unsafe_allow_html=True,
    )


# ─── 10. Peer Comparison Table (v3.5) ─────────────────────────────────────────

def render_peer_comparison(report_data: Dict[str, Any]) -> None:
    """Peer comparison table: PE, PB, dividend yield, market cap, risk score."""
    cl = report_data.get("competitive_landscape", {}) or {}
    peers = cl.get("peers", []) or []
    subject = cl.get("subject", {}) or {}

    st.markdown("## 🏆 同行比較")

    if not peers and not subject:
        st.info("同行比較資料待補充")
        return

    # Build rows: subject first, then peers
    all_rows = []
    if subject:
        all_rows.append({**subject, "_is_subject": True})
    for p in peers:
        if isinstance(p, dict):
            all_rows.append({**p, "_is_subject": False})

    if not all_rows:
        st.info("同行比較資料待補充")
        return

    # Header
    header_html = (
        '<table style="width:100%;border-collapse:collapse;font-size:0.88rem;">'
        '<thead><tr style="background:#1a73e8;color:#fff;">'
        '<th style="padding:8px 12px;text-align:left;">股票</th>'
        '<th style="padding:8px 12px;text-align:left;">公司</th>'
        '<th style="padding:8px 12px;text-align:right;">P/E</th>'
        '<th style="padding:8px 12px;text-align:right;">P/B</th>'
        '<th style="padding:8px 12px;text-align:right;">股息率</th>'
        '<th style="padding:8px 12px;text-align:right;">市值(億)</th>'
        '<th style="padding:8px 12px;text-align:right;">風險分數</th>'
        '</tr></thead><tbody>'
    )
    rows_html = ""
    for row in all_rows:
        is_sub = row.get("_is_subject", False)
        bg = "#e8f0fe" if is_sub else "#fff"
        fw = "700" if is_sub else "400"
        ticker = row.get("ticker", "—")
        name = row.get("name", row.get("company_name", "—"))
        pe = row.get("pe_ratio", row.get("pe", "—"))
        pb = row.get("pb_ratio", row.get("pb", "—"))
        div = row.get("dividend_yield", row.get("div_yield", "—"))
        mktcap = row.get("market_cap_bn", row.get("market_cap", "—"))
        risk = row.get("risk_score", "—")

        def _fmt_val(v):
            if v in (None, "", "—", "N/A"):
                return "—"
            try:
                return f"{float(v):.2f}"
            except (TypeError, ValueError):
                return str(v)

        rows_html += (
            f'<tr style="background:{bg};font-weight:{fw};border-bottom:1px solid #e8eaed;">'
            f'<td style="padding:8px 12px;">{ticker}</td>'
            f'<td style="padding:8px 12px;">{name}</td>'
            f'<td style="padding:8px 12px;text-align:right;">{_fmt_val(pe)}</td>'
            f'<td style="padding:8px 12px;text-align:right;">{_fmt_val(pb)}</td>'
            f'<td style="padding:8px 12px;text-align:right;">{_fmt_val(div)}%</td>'
            f'<td style="padding:8px 12px;text-align:right;">{_fmt_val(mktcap)}</td>'
            f'<td style="padding:8px 12px;text-align:right;">{_fmt_val(risk)}</td>'
            f'</tr>'
        )
    st.markdown(header_html + rows_html + "</tbody></table>", unsafe_allow_html=True)

    # Strengths / Weaknesses
    strengths = cl.get("strengths", []) or []
    weaknesses = cl.get("weaknesses", []) or []
    if strengths or weaknesses:
        st.markdown("")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**✅ 相對優勢**")
            for s in strengths[:4]:
                st.markdown(f"- {s}")
        with c2:
            st.markdown("**⚠️ 相對弱勢**")
            for w in weaknesses[:4]:
                st.markdown(f"- {w}")


# ─── 11. Source Transparency (v3.5) ───────────────────────────────────────────

def render_source_transparency(report_data: Dict[str, Any]) -> None:
    """Data confidence evidence: level, coverage %, verified sources."""
    st_data = report_data.get("source_transparency", {}) or {}
    cover = report_data.get("cover", {}) or {}

    level = st_data.get("confidence_level") or cover.get("data_confidence", "LOW")
    coverage = st_data.get("coverage_pct", 0)
    sources = st_data.get("verified_sources", []) or []
    reason = st_data.get("confidence_reason", "")

    LEVEL_COLOR = {"HIGH": "#1e8e3e", "MEDIUM": "#f29900", "LOW": "#d93025"}
    color = LEVEL_COLOR.get(str(level).upper(), "#5f6368")

    try:
        cov_pct = float(coverage)
    except (TypeError, ValueError):
        cov_pct = 0.0

    st.markdown("## 🔍 資料可信度來源")

    col1, col2 = st.columns([1, 2])
    with col1:
        st.markdown(
            f'<div style="text-align:center;padding:20px;border:2px solid {color};'
            f'border-radius:12px;background:{color}18;">'
            f'<div style="font-size:1.6rem;font-weight:800;color:{color};">{level}</div>'
            f'<div style="font-size:2.4rem;font-weight:900;color:{color};">{cov_pct:.0f}%</div>'
            f'<div style="font-size:0.8rem;color:#5f6368;">資料覆蓋率</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
    with col2:
        if reason:
            st.markdown(f"**為何 {level}？**")
            st.markdown(reason)
        if sources:
            st.markdown("**已驗證來源**")
            for src in sources:
                icon = src.get("icon", "✓") if isinstance(src, dict) else "✓"
                name = src.get("name", str(src)) if isinstance(src, dict) else str(src)
                verified = src.get("verified", True) if isinstance(src, dict) else True
                check_color = "#1e8e3e" if verified else "#d93025"
                st.markdown(
                    f'<span style="color:{check_color};font-weight:600;">{icon} {name}</span>',
                    unsafe_allow_html=True,
                )


# ─── 12. Risk Dashboard (v3.5) ────────────────────────────────────────────────

def render_risk_dashboard(report_data: Dict[str, Any]) -> None:
    """Risk dashboard with gauge-style display for 7 risk categories."""
    rv2 = report_data.get("risk_assessment_v2", {}) or {}
    items = rv2.get("risk_items", []) or []
    composite = rv2.get("composite_score", "—")
    risk_label = rv2.get("risk_label", "—")

    st.markdown("## 🎯 風險儀表板")

    if not items:
        st.info("風險儀表板資料待分析")
        return

    # Composite score header
    LEVEL_COLOR = {
        "低風險": "#1e8e3e", "中等風險": "#f29900",
        "高風險": "#d93025", "極高風險": "#7b1fa2",
    }
    comp_color = LEVEL_COLOR.get(risk_label, "#5f6368")
    st.markdown(
        f'<div style="display:flex;align-items:center;gap:16px;margin-bottom:16px;">'
        f'<div style="font-size:2rem;font-weight:800;color:{comp_color};">{composite}</div>'
        f'<div>{_badge(risk_label, comp_color)}</div>'
        f'<div style="color:#5f6368;font-size:0.85rem;">加權綜合風險分數</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # Individual risk items
    cols = st.columns(2)
    for i, item in enumerate(items):
        score_raw = item.get("score_raw", 5.0)
        score_str = item.get("score", "—")
        name = item.get("risk_name", "—")
        level = item.get("level", "—")
        reason = item.get("reason", "—")
        signal = item.get("monitoring_signal", "—")
        weight = item.get("weight", "—")

        bar_pct = (score_raw / 10.0) * 100
        item_color = LEVEL_COLOR.get(level, "#5f6368")

        with cols[i % 2]:
            st.markdown(
                f'<div style="border:1px solid #e8eaed;border-radius:8px;'
                f'padding:12px 14px;margin-bottom:10px;background:#fafafa;">'
                f'<div style="display:flex;justify-content:space-between;align-items:center;">'
                f'<strong style="font-size:0.9rem;">{name}</strong>'
                f'<span style="font-size:0.78rem;color:#5f6368;">權重 {weight}</span>'
                f'</div>'
                f'<div style="display:flex;align-items:center;gap:8px;margin:6px 0;">'
                f'<div style="font-size:1.4rem;font-weight:700;color:{item_color};">{score_str}</div>'
                f'{_badge(level, item_color)}'
                f'</div>'
                f'<div style="background:#e8eaed;border-radius:4px;height:6px;margin:4px 0;">'
                f'<div style="background:{item_color};width:{bar_pct:.0f}%;height:6px;border-radius:4px;"></div>'
                f'</div>'
                f'<div style="color:#5f6368;font-size:0.8rem;margin-top:6px;">{reason}</div>'
                f'<div style="color:#0097a7;font-size:0.78rem;margin-top:4px;">📋 {signal}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )


# ─── 13. Bull vs Bear Debate (v3.5) ───────────────────────────────────────────

def render_bull_bear_debate(report_data: Dict[str, Any]) -> None:
    """Bull vs Bear investment committee debate with central verdict."""
    ao = report_data.get("agent_opinions_v2", {}) or {}
    bull_agents = ao.get("bull_agents", []) or []
    bear_agents = ao.get("bear_agents", []) or []
    verdict = ao.get("verdict", {}) or {}

    st.markdown("## 🏛️ AI 投資委員會 — Bull vs Bear 辯論")

    # Bull / Bear side-by-side
    col_bull, col_mid, col_bear = st.columns([5, 1, 5])

    with col_bull:
        st.markdown(
            '<div style="background:linear-gradient(135deg,#e8f5e9,#f1f8e9);'
            'border-radius:12px;padding:16px;border:1px solid #a5d6a7;">'
            '<div style="font-size:1.2rem;font-weight:800;color:#1e8e3e;margin-bottom:12px;">'
            '🐂 牛市觀點</div>',
            unsafe_allow_html=True,
        )
        if bull_agents:
            for agent in bull_agents:
                name = agent.get("name", "Agent")
                view = agent.get("view", "—")
                reasons = agent.get("reasons", []) or []
                st.markdown(f"**{name}**")
                st.markdown(f"*{view}*")
                for r in reasons[:3]:
                    st.markdown(f"✅ {r}")
                st.markdown("")
        else:
            st.markdown("*牛市論據待補充*")
        st.markdown('</div>', unsafe_allow_html=True)

    with col_mid:
        st.markdown(
            '<div style="display:flex;align-items:center;justify-content:center;'
            'height:100%;font-size:1.5rem;">⚖️</div>',
            unsafe_allow_html=True,
        )

    with col_bear:
        st.markdown(
            '<div style="background:linear-gradient(135deg,#fce4ec,#fff3e0);'
            'border-radius:12px;padding:16px;border:1px solid #ef9a9a;">'
            '<div style="font-size:1.2rem;font-weight:800;color:#d93025;margin-bottom:12px;">'
            '🐻 熊市觀點</div>',
            unsafe_allow_html=True,
        )
        if bear_agents:
            for agent in bear_agents:
                name = agent.get("name", "Agent")
                view = agent.get("view", "—")
                reasons = agent.get("reasons", []) or []
                st.markdown(f"**{name}**")
                st.markdown(f"*{view}*")
                for r in reasons[:3]:
                    st.markdown(f"⚠️ {r}")
                st.markdown("")
        else:
            st.markdown("*熊市論據待補充*")
        st.markdown('</div>', unsafe_allow_html=True)

    # Central verdict
    st.markdown("---")
    st.markdown("### ⚖️ 投資委員會裁決")

    bull_score = verdict.get("bull_score", ao.get("bull_score", "—"))
    bear_score = verdict.get("bear_score", ao.get("bear_score", "—"))
    confidence = verdict.get("confidence", ao.get("confidence", "—"))
    summary = verdict.get("summary", ao.get("committee_summary", ""))
    recommendation = verdict.get("recommendation", ao.get("final_recommendation", "—"))

    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric("🐂 Bull Score", bull_score)
    with m2:
        st.metric("🐻 Bear Score", bear_score)
    with m3:
        st.metric("信心度", confidence)
    with m4:
        st.metric("最終建議", recommendation)

    if summary:
        st.markdown(
            f'<div style="background:#f8f9fa;border-left:4px solid #1a73e8;'
            f'padding:12px 16px;border-radius:4px;margin-top:8px;">'
            f'<strong>委員會摘要：</strong> {summary}'
            f'</div>',
            unsafe_allow_html=True,
        )


# ─── 14. Page Background Sentiment Layer (v3.5) ───────────────────────────────

def render_market_sentiment_background(bull_score: float, bear_score: float) -> None:
    """
    Inject subtle left (bull/green) and right (bear/red) background gradient strips
    as page-level sentiment indicators. Call once at top of report page.
    """
    bull_opacity = min(0.12, max(0.03, bull_score / 100 * 0.15))
    bear_opacity = min(0.12, max(0.03, bear_score / 100 * 0.15))

    st.markdown(
        f"""
        <style>
        .stApp {{
            background: linear-gradient(
                to right,
                rgba(30,142,62,{bull_opacity:.3f}) 0%,
                rgba(255,255,255,0) 8%,
                rgba(255,255,255,0) 92%,
                rgba(217,48,37,{bear_opacity:.3f}) 100%
            ) !important;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )
