"""
core/fos_components.py
FOS V3 — Investor Decision Cockpit Components
No decorative panels. Decision-making information only.
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
    risk = report_data.get("risk_analysis", {}) or {}
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

        opinion    = agent.get("opinion", agent.get("view", agent.get("stance", "分析中")))
        reasoning  = agent.get("reasoning", agent.get("rationale", agent.get("analysis", "—")))
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
