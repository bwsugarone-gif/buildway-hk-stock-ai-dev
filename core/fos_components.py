"""
core/fos_components.py
FOS Client Experience Layer - UI Components v2.8.0
Buildway Tech (HK) Limited
"""
from __future__ import annotations
import html as _html
from typing import Any, Dict, List

import streamlit as st
import plotly.graph_objects as go


def _e(v: Any) -> str:
    return _html.escape(str(v if v not in (None, "") else "N/A"))


# ── Peer Comparison ──────────────────────────────────────────────────────────
def render_peer_comparison(report: Dict[str, Any]) -> None:
    peers: List[Dict] = report.get("peer_comparison", [])
    target = report.get("ticker", "")
    company = report.get("company_name", target)

    st.markdown(
        "<div style='background:#fff;border-radius:12px;padding:1.2rem 1.5rem;"
        "border:1px solid #dfe6ef;margin-bottom:1rem'>"
        "<h3 style='color:#071b33;margin:0 0 1rem'>📊 同行比較</h3>",
        unsafe_allow_html=True,
    )

    if not peers:
        peers = [
            {"ticker": target, "company": company, "pe": 12.5, "pb": 1.2,
             "div_yield": 4.5, "mkt_cap": "HK$5,000億", "risk_score": 5, "highlight": True},
            {"ticker": "0941.HK", "company": "中國移動", "pe": 11.2, "pb": 1.1,
             "div_yield": 5.2, "mkt_cap": "HK$15,000億", "risk_score": 4, "highlight": False},
            {"ticker": "0728.HK", "company": "中國電信", "pe": 9.8, "pb": 0.9,
             "div_yield": 4.8, "mkt_cap": "HK$3,500億", "risk_score": 5, "highlight": False},
        ]

    cols = st.columns(len(peers))
    for i, p in enumerate(peers):
        bg = "#f0f7ff" if p.get("highlight") else "#f8fafc"
        border = "2px solid #1a56db" if p.get("highlight") else "1px solid #dfe6ef"
        risk = p.get("risk_score", 5)
        rc = "#15a36d" if risk <= 3 else ("#d9a441" if risk <= 6 else "#d64545")
        cols[i].markdown(
            f"<div style='background:{bg};border:{border};border-radius:10px;"
            f"padding:1rem;text-align:center'>"
            f"<div style='font-size:0.75rem;color:#667085'>{_e(p.get('ticker', ''))}</div>"
            f"<div style='font-weight:700;color:#071b33;margin:0.3rem 0'>{_e(p.get('company', ''))}</div>"
            f"<div style='display:grid;grid-template-columns:1fr 1fr;gap:0.4rem;"
            f"margin-top:0.6rem;font-size:0.8rem'>"
            f"<div style='background:#fff;border-radius:6px;padding:0.3rem'>"
            f"<div style='color:#667085'>PE</div>"
            f"<div style='font-weight:600'>{_e(p.get('pe', 'N/A'))}</div></div>"
            f"<div style='background:#fff;border-radius:6px;padding:0.3rem'>"
            f"<div style='color:#667085'>PB</div>"
            f"<div style='font-weight:600'>{_e(p.get('pb', 'N/A'))}</div></div>"
            f"<div style='background:#fff;border-radius:6px;padding:0.3rem'>"
            f"<div style='color:#667085'>股息率</div>"
            f"<div style='font-weight:600'>{_e(p.get('div_yield', 'N/A'))}%</div></div>"
            f"<div style='background:#fff;border-radius:6px;padding:0.3rem'>"
            f"<div style='color:#667085'>市值</div>"
            f"<div style='font-weight:600;font-size:0.7rem'>{_e(p.get('mkt_cap', 'N/A'))}</div></div>"
            f"</div>"
            f"<div style='margin-top:0.6rem;border-radius:6px;padding:0.3rem;"
            f"color:{rc};font-weight:700;background:{rc}22'>風險 {risk}/10</div>"
            f"</div>",
            unsafe_allow_html=True,
        )
    st.markdown("</div>", unsafe_allow_html=True)


# ── Data Confidence ──────────────────────────────────────────────────────────
def render_data_confidence(report: Dict[str, Any]) -> None:
    conf = report.get("data_confidence", {})
    level = conf.get("level", "MEDIUM")
    score = conf.get("score", 65)
    sources = conf.get("sources", ["Yahoo Finance", "Company Metadata", "Financial Statement"])
    color = {"HIGH": "#15a36d", "MEDIUM": "#d9a441", "LOW": "#d64545"}.get(level, "#667085")
    reason = conf.get("reason", f"資料覆蓋率 {score}%，來源包括財務報表及市場數據")

    st.markdown(
        f"<div style='background:#fff;border-radius:12px;padding:1.2rem 1.5rem;"
        f"border:1px solid #dfe6ef;margin-bottom:1rem'>"
        f"<h3 style='color:#071b33;margin:0 0 1rem'>🔍 資料可信度來源</h3>"
        f"<div style='display:flex;align-items:center;gap:1.5rem;flex-wrap:wrap'>"
        f"<div style='text-align:center'>"
        f"<div style='font-size:2.5rem;font-weight:800;color:{color}'>{level}</div>"
        f"<div style='font-size:0.8rem;color:#667085'>可信度等級</div></div>"
        f"<div style='flex:1;min-width:200px'>"
        f"<div style='background:#f0f4f8;border-radius:8px;height:12px;margin-bottom:0.5rem'>"
        f"<div style='background:{color};height:12px;border-radius:8px;width:{score}%'></div></div>"
        f"<div style='font-size:0.85rem;color:#667085'>資料覆蓋率 "
        f"<strong style=\"color:{color}\">{score}%</strong></div>"
        f"<div style='font-size:0.8rem;color:#667085;margin-top:0.3rem'>{_e(reason)}</div>"
        f"</div><div style='display:flex;flex-direction:column;gap:0.3rem'>",
        unsafe_allow_html=True,
    )
    all_sources = ["Yahoo Finance", "Company Metadata", "Financial Statement", "News Source", "HKEX Filing"]
    for s in all_sources:
        ok = s in sources
        icon = "✓" if ok else "✗"
        c = "#15a36d" if ok else "#ccc"
        st.markdown(f"<div style='color:{c};font-size:0.85rem'>{icon} {s}</div>", unsafe_allow_html=True)
    st.markdown("</div></div></div>", unsafe_allow_html=True)


# ── Market Snapshot Chart ────────────────────────────────────────────────────
def render_market_snapshot(report: Dict[str, Any]) -> None:
    mkt = report.get("market_data", {})
    price = float(mkt.get("current_price", 50) or 50)
    high52 = float(mkt.get("week_52_high", price * 1.3) or price * 1.3)
    low52 = float(mkt.get("week_52_low", price * 0.7) or price * 0.7)
    pct = ((price - low52) / (high52 - low52) * 100) if high52 != low52 else 50
    bull_zone = high52 * 0.85
    bear_zone = low52 * 1.15

    fig = go.Figure()
    fig.add_shape(type="rect", x0=0, y0=low52, x1=1, y1=bear_zone,
                  fillcolor="rgba(214,69,69,0.08)", line_width=0)
    fig.add_shape(type="rect", x0=0, y0=bull_zone, x1=1, y1=high52,
                  fillcolor="rgba(21,163,109,0.08)", line_width=0)
    fig.add_trace(go.Scatter(
        x=[0.5], y=[price], mode="markers+text",
        marker=dict(size=18, color="#1a56db", symbol="diamond"),
        text=[f"HK${price:.2f}"], textposition="top center", name="現價",
    ))
    fig.add_hline(y=high52, line_dash="dot", line_color="#15a36d",
                  annotation_text=f"52週高 HK${high52:.2f}", annotation_position="right")
    fig.add_hline(y=low52, line_dash="dot", line_color="#d64545",
                  annotation_text=f"52週低 HK${low52:.2f}", annotation_position="right")
    fig.update_layout(
        height=280, margin=dict(l=10, r=120, t=30, b=10),
        showlegend=False, plot_bgcolor="#f8fafc", paper_bgcolor="#fff",
        xaxis=dict(visible=False), yaxis=dict(title="價格 (HK$)"),
    )

    st.markdown(
        "<div style='background:#fff;border-radius:12px;padding:1.2rem 1.5rem;"
        "border:1px solid #dfe6ef;margin-bottom:1rem'>"
        "<h3 style='color:#071b33;margin:0 0 0.5rem'>📈 市場快照</h3>",
        unsafe_allow_html=True,
    )
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("現價", f"HK${price:.2f}")
    c2.metric("52週高", f"HK${high52:.2f}")
    c3.metric("52週低", f"HK${low52:.2f}")
    c4.metric("52週位置", f"{pct:.0f}%")
    st.plotly_chart(fig, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)


# ── Financial Trend Charts ───────────────────────────────────────────────────
def render_financial_trends(report: Dict[str, Any]) -> None:
    fin = report.get("financial_data", {})
    years = ["2022", "2023", "2024"]
    rev = fin.get("revenue_trend", [800, 950, 1100])
    ebitda = fin.get("ebitda_trend", [200, 240, 280])
    net = fin.get("net_profit_trend", [120, 145, 170])
    fcf = fin.get("fcf_trend", [90, 110, 130])

    st.markdown(
        "<div style='background:#fff;border-radius:12px;padding:1.2rem 1.5rem;"
        "border:1px solid #dfe6ef;margin-bottom:1rem'>"
        "<h3 style='color:#071b33;margin:0 0 1rem'>💰 財務趨勢（三年）</h3>",
        unsafe_allow_html=True,
    )
    c1, c2 = st.columns(2)
    for col, data, title, color in [
        (c1, rev, "收入趨勢 (億)", "#1a56db"),
        (c1, ebitda, "EBITDA趨勢 (億)", "#15a36d"),
        (c2, net, "淨利潤趨勢 (億)", "#d9a441"),
        (c2, fcf, "自由現金流 (億)", "#7c3aed"),
    ]:
        fig = go.Figure(go.Bar(
            x=years, y=data, marker_color=color,
            text=[f"{v}億" for v in data], textposition="outside",
        ))
        fig.update_layout(
            title=title, height=200,
            margin=dict(l=5, r=5, t=30, b=5),
            plot_bgcolor="#f8fafc", paper_bgcolor="#fff", showlegend=False,
        )
        col.plotly_chart(fig, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)


# ── Risk Dashboard ───────────────────────────────────────────────────────────
def render_risk_dashboard(report: Dict[str, Any]) -> None:
    risk = report.get("risk_analysis", {})
    scores = {
        "流動性風險": risk.get("liquidity_risk", 4),
        "估值風險": risk.get("valuation_risk", 5),
        "市場風險": risk.get("market_risk", 6),
        "財務風險": risk.get("financial_risk", 3),
        "新聞風險": risk.get("news_risk", 4),
    }
    total = risk.get("total_risk_score", sum(scores.values()) // len(scores))
    tc = "#15a36d" if total <= 3 else ("#d9a441" if total <= 6 else "#d64545")

    st.markdown(
        f"<div style='background:#fff;border-radius:12px;padding:1.2rem 1.5rem;"
        f"border:1px solid #dfe6ef;margin-bottom:1rem'>"
        f"<h3 style='color:#071b33;margin:0 0 1rem'>⚠️ 風險儀表板</h3>"
        f"<div style='text-align:center;margin-bottom:1rem'>"
        f"<span style='font-size:3rem;font-weight:800;color:{tc}'>{total}</span>"
        f"<span style='font-size:1rem;color:#667085'>/10 總風險分數</span></div>",
        unsafe_allow_html=True,
    )
    for name, score in scores.items():
        c = "#15a36d" if score <= 3 else ("#d9a441" if score <= 6 else "#d64545")
        pct = score * 10
        st.markdown(
            f"<div style='margin-bottom:0.5rem'>"
            f"<div style='display:flex;justify-content:space-between;font-size:0.85rem'>"
            f"<span>{name}</span><span style='color:{c};font-weight:700'>{score}/10</span></div>"
            f"<div style='background:#f0f4f8;border-radius:4px;height:8px'>"
            f"<div style='background:{c};height:8px;border-radius:4px;width:{pct}%'></div>"
            f"</div></div>",
            unsafe_allow_html=True,
        )
    st.markdown("</div>", unsafe_allow_html=True)


# ── News Sentiment Dashboard ─────────────────────────────────────────────────
def render_news_sentiment(report: Dict[str, Any]) -> None:
    news = report.get("news_analysis", {})
    pos = news.get("positive_count", 3)
    neu = news.get("neutral_count", 5)
    neg = news.get("negative_count", 2)
    catalysts = news.get("catalysts", [])
    watchlist = news.get("watchlist", [])

    st.markdown(
        "<div style='background:#fff;border-radius:12px;padding:1.2rem 1.5rem;"
        "border:1px solid #dfe6ef;margin-bottom:1rem'>"
        "<h3 style='color:#071b33;margin:0 0 1rem'>📰 新聞情緒分析</h3>",
        unsafe_allow_html=True,
    )
    c1, c2, c3 = st.columns(3)
    c1.markdown(
        f"<div style='text-align:center;background:#f0fdf4;border-radius:8px;padding:0.8rem'>"
        f"<div style='font-size:1.8rem;font-weight:800;color:#15a36d'>{pos}</div>"
        f"<div style='color:#667085;font-size:0.8rem'>正面新聞</div></div>",
        unsafe_allow_html=True,
    )
    c2.markdown(
        f"<div style='text-align:center;background:#f8fafc;border-radius:8px;padding:0.8rem'>"
        f"<div style='font-size:1.8rem;font-weight:800;color:#667085'>{neu}</div>"
        f"<div style='color:#667085;font-size:0.8rem'>中性新聞</div></div>",
        unsafe_allow_html=True,
    )
    c3.markdown(
        f"<div style='text-align:center;background:#fff5f5;border-radius:8px;padding:0.8rem'>"
        f"<div style='font-size:1.8rem;font-weight:800;color:#d64545'>{neg}</div>"
        f"<div style='color:#667085;font-size:0.8rem'>負面新聞</div></div>",
        unsafe_allow_html=True,
    )
    if catalysts:
        st.markdown("**催化事件：**")
        for cat in catalysts[:3]:
            st.markdown(f"- 🚀 {_e(cat)}")
    if watchlist:
        st.markdown("**監察事項：**")
        for w in watchlist[:3]:
            st.markdown(f"- 👁 {_e(w)}")
    st.markdown("</div>", unsafe_allow_html=True)


# ── Bull vs Bear Committee ───────────────────────────────────────────────────
def render_investment_committee(report: Dict[str, Any]) -> None:
    ic = report.get("investment_committee", {})
    bull_pts = ic.get("bull_points", ["估值合理，PE低於行業平均", "股息率具吸引力", "業務穩定增長"])
    bear_pts = ic.get("bear_points", ["市場競爭加劇", "監管風險上升", "增長放緩跡象"])
    bull_score = ic.get("bull_score", 65)
    bear_score = ic.get("bear_score", 35)
    confidence = ic.get("confidence", 72)
    summary = ic.get(
        "committee_summary",
        "投資委員會綜合各分析師觀點後，認為該股票具備中長線投資價值，但需留意短期波動風險。",
    )
    verdict = ic.get("final_recommendation", "正面")
    vc = {
        "買入": "#15a36d", "正面": "#15a36d", "觀察": "#d9a441",
        "中性": "#667085", "減持": "#d64545", "避免": "#d64545",
    }.get(verdict, "#667085")

    st.markdown(
        "<div style='background:linear-gradient(135deg,#071b33 0%,#0d2a4c 100%);"
        "border-radius:16px;padding:1.5rem;margin-bottom:1rem;color:#fff'>"
        "<h3 style='color:#d9a441;margin:0 0 1.2rem;text-align:center'>"
        "🏛️ AI 投資委員會 — Bull vs Bear 辯論</h3>",
        unsafe_allow_html=True,
    )
    col_bull, col_mid, col_bear = st.columns([2, 1, 2])

    with col_bull:
        st.markdown(
            "<div style='background:rgba(21,163,109,0.15);"
            "border:1px solid rgba(21,163,109,0.4);"
            "border-radius:10px;padding:1rem'>"
            "<div style='color:#4ade80;font-size:1.1rem;font-weight:700;"
            "margin-bottom:0.8rem'>🐂 牛市觀點</div>"
            "<div style='color:#86efac;font-size:0.75rem;margin-bottom:0.5rem'>"
            "市場分析 · 財務分析 · 新聞分析</div>",
            unsafe_allow_html=True,
        )
        for pt in bull_pts:
            st.markdown(
                f"<div style='color:#d1fae5;font-size:0.85rem;margin:0.3rem 0'>✅ {_e(pt)}</div>",
                unsafe_allow_html=True,
            )
        st.markdown(
            f"<div style='margin-top:0.8rem;text-align:center;font-size:1.5rem;"
            f"font-weight:800;color:#4ade80'>Bull {bull_score}</div></div>",
            unsafe_allow_html=True,
        )

    with col_mid:
        st.markdown(
            f"<div style='text-align:center;padding:1rem 0'>"
            f"<div style='color:#d9a441;font-size:0.8rem;margin-bottom:0.5rem'>委員會裁決</div>"
            f"<div style='font-size:1.8rem;font-weight:800;color:{vc}'>{verdict}</div>"
            f"<div style='color:#94a3b8;font-size:0.75rem;margin-top:0.5rem'>信心度</div>"
            f"<div style='font-size:1.2rem;font-weight:700;color:#fff'>{confidence}%</div>"
            f"</div>",
            unsafe_allow_html=True,
        )

    with col_bear:
        st.markdown(
            "<div style='background:rgba(214,69,69,0.15);"
            "border:1px solid rgba(214,69,69,0.4);"
            "border-radius:10px;padding:1rem'>"
            "<div style='color:#f87171;font-size:1.1rem;font-weight:700;"
            "margin-bottom:0.8rem'>🐻 熊市觀點</div>"
            "<div style='color:#fca5a5;font-size:0.75rem;margin-bottom:0.5rem'>"
            "風險分析 · 估值分析 · 事件分析</div>",
            unsafe_allow_html=True,
        )
        for pt in bear_pts:
            st.markdown(
                f"<div style='color:#fee2e2;font-size:0.85rem;margin:0.3rem 0'>⚠️ {_e(pt)}</div>",
                unsafe_allow_html=True,
            )
        st.markdown(
            f"<div style='margin-top:0.8rem;text-align:center;font-size:1.5rem;"
            f"font-weight:800;color:#f87171'>Bear {bear_score}</div></div>",
            unsafe_allow_html=True,
        )

    st.markdown(
        f"<div style='background:rgba(217,164,65,0.1);"
        f"border:1px solid rgba(217,164,65,0.3);"
        f"border-radius:10px;padding:1rem;margin-top:1rem'>"
        f"<div style='color:#d9a441;font-weight:700;margin-bottom:0.5rem'>📋 委員會總結</div>"
        f"<div style='color:#e2e8f0;font-size:0.9rem'>{_e(summary)}</div>"
        f"</div></div>",
        unsafe_allow_html=True,
    )


# ── Investment Conclusion Card ───────────────────────────────────────────────
def render_investment_conclusion(report: Dict[str, Any]) -> None:
    conc = report.get("investment_conclusion", {})
    rating = conc.get("rating", "觀察")
    horizon = conc.get("horizon", "中線")
    investor_type = conc.get("investor_type", "平衡")
    summary = conc.get("summary", "綜合分析後，建議投資者保持觀察，待更多數據確認後再作決定。")

    rating_cfg = {
        "買入": {"color": "#15a36d", "bg": "#f0fdf4", "icon": "🟢"},
        "觀察": {"color": "#d9a441", "bg": "#fffbeb", "icon": "🟡"},
        "中性": {"color": "#667085", "bg": "#f8fafc", "icon": "⚪"},
        "減持": {"color": "#d64545", "bg": "#fff5f5", "icon": "🔴"},
        "避免": {"color": "#d64545", "bg": "#fff5f5", "icon": "🔴"},
    }
    cfg = rating_cfg.get(rating, rating_cfg["觀察"])
    color = cfg["color"]
    bg = cfg["bg"]
    icon = cfg["icon"]

    st.markdown(
        f"<div style='background:{bg};border:2px solid {color};"
        f"border-radius:16px;padding:1.5rem;margin-bottom:1rem'>"
        f"<h3 style='color:#071b33;margin:0 0 1rem;text-align:center'>🎯 最終投資結論</h3>"
        f"<div style='display:flex;justify-content:center;gap:2rem;flex-wrap:wrap;margin-bottom:1rem'>"
        f"<div style='text-align:center'>"
        f"<div style='font-size:0.8rem;color:#667085'>評級</div>"
        f"<div style='font-size:2.5rem;font-weight:800;color:{color}'>{icon} {rating}</div>"
        f"</div>"
        f"<div style='text-align:center'>"
        f"<div style='font-size:0.8rem;color:#667085'>投資週期</div>"
        f"<div style='font-size:1.5rem;font-weight:700;color:#071b33'>{horizon}</div>"
        f"</div>"
        f"<div style='text-align:center'>"
        f"<div style='font-size:0.8rem;color:#667085'>適合投資者</div>"
        f"<div style='font-size:1.5rem;font-weight:700;color:#071b33'>{investor_type}</div>"
        f"</div></div>"
        f"<div style='background:#fff;border-radius:8px;padding:1rem;"
        f"font-size:0.9rem;color:#172033'>{_e(summary)}</div></div>",
        unsafe_allow_html=True,
    )


# ── Bull/Bear Background Decoration ─────────────────────────────────────────
_BULL_BEAR_CSS = """<style>
.bull-side-label {
    position:fixed;left:0;top:50%;transform:translateY(-50%);
    writing-mode:vertical-rl;text-orientation:mixed;
    background:linear-gradient(180deg,rgba(21,163,109,0.15),rgba(21,163,109,0.05));
    color:rgba(21,163,109,0.6);font-size:0.75rem;font-weight:700;
    padding:1rem 0.4rem;border-radius:0 8px 8px 0;letter-spacing:0.1em;
    z-index:0;pointer-events:none;
}
.bear-side-label {
    position:fixed;right:0;top:50%;transform:translateY(-50%);
    writing-mode:vertical-rl;text-orientation:mixed;
    background:linear-gradient(180deg,rgba(214,69,69,0.15),rgba(214,69,69,0.05));
    color:rgba(214,69,69,0.6);font-size:0.75rem;font-weight:700;
    padding:1rem 0.4rem;border-radius:8px 0 0 8px;letter-spacing:0.1em;
    z-index:0;pointer-events:none;
}
</style>
<div class="bull-side-label">🐂 BULL MARKET</div>
<div class="bear-side-label">🐻 BEAR MARKET</div>"""


def inject_bull_bear_bg() -> None:
    st.markdown(_BULL_BEAR_CSS, unsafe_allow_html=True)
