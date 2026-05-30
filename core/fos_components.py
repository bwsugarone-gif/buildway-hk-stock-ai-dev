"""
core/fos_components.py
Buildway Tech (HK) Limited
FOS Client Experience Layer v2.8.1 — Bloomberg Lite UI Components

All components are pure Streamlit — no external image dependencies.
Plotly is used for charts with graceful fallback to st.bar_chart / st.progress.
Bull/Bear background uses CSS injection (desktop only, hidden on mobile).
"""

from __future__ import annotations

import html
from typing import Any

import streamlit as st

# ── Plotly availability check ─────────────────────────────────────────────────
try:
    import plotly.graph_objects as go
    import plotly.express as px
    _PLOTLY_OK = True
except ImportError:
    _PLOTLY_OK = False


def _esc(v: Any) -> str:
    return html.escape(str(v if v not in (None, "", "None", "N/A") else "N/A"))


def _safe_float(v: Any, default: float = 0.0) -> float:
    try:
        return float(str(v).replace(",", "").replace("%", "").strip())
    except (TypeError, ValueError):
        return default


# ─────────────────────────────────────────────────────────────────────────────
# PART 2 — Bull / Bear Background CSS
# Desktop: fixed left/right panels with gradient + emoji
# Mobile (@media max-width 719px): hidden
# pointer-events: none so it never blocks clicks
# ─────────────────────────────────────────────────────────────────────────────

def inject_bull_bear_bg() -> None:
    """Inject fixed left/right Bull/Bear decorative panels via CSS only."""
    st.markdown(
        """
        <style>
        /* ── Bull/Bear side panels ── */
        .bw-bull-panel,
        .bw-bear-panel {
            position: fixed;
            top: 50%;
            transform: translateY(-50%);
            width: 52px;
            z-index: 0;
            pointer-events: none;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            gap: 8px;
            border-radius: 0 12px 12px 0;
            padding: 24px 6px;
            opacity: 0.82;
        }

        .bw-bull-panel {
            left: 0;
            background: linear-gradient(
                180deg,
                rgba(21, 163, 109, 0.18) 0%,
                rgba(21, 163, 109, 0.08) 100%
            );
            border-right: 2px solid rgba(21, 163, 109, 0.35);
        }

        .bw-bear-panel {
            right: 0;
            background: linear-gradient(
                180deg,
                rgba(214, 69, 69, 0.18) 0%,
                rgba(214, 69, 69, 0.08) 100%
            );
            border-left: 2px solid rgba(214, 69, 69, 0.35);
            border-radius: 12px 0 0 12px;
        }

        .bw-bull-panel .bw-side-emoji,
        .bw-bear-panel .bw-side-emoji {
            font-size: 1.5rem;
            line-height: 1;
        }

        .bw-bull-panel .bw-side-label,
        .bw-bear-panel .bw-side-label {
            writing-mode: vertical-rl;
            text-orientation: mixed;
            font-size: 0.62rem;
            font-weight: 700;
            letter-spacing: 0.12em;
            text-transform: uppercase;
        }

        .bw-bull-panel .bw-side-label {
            color: rgba(21, 163, 109, 0.75);
        }

        .bw-bear-panel .bw-side-label {
            color: rgba(214, 69, 69, 0.75);
        }

        /* Hide on mobile */
        @media (max-width: 719px) {
            .bw-bull-panel,
            .bw-bear-panel {
                display: none !important;
            }
        }
        </style>

        <div class="bw-bull-panel" aria-hidden="true">
            <span class="bw-side-emoji">🐂</span>
            <span class="bw-side-label">Bull Market</span>
        </div>
        <div class="bw-bear-panel" aria-hidden="true">
            <span class="bw-side-emoji">🐻</span>
            <span class="bw-side-label">Bear Market</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────────────────────────────────────
# PART 3 — Peer Comparison
# ─────────────────────────────────────────────────────────────────────────────

def render_peer_comparison(data: dict[str, Any]) -> None:
    """Peer comparison table — PE / PB / dividend / market cap / risk score."""
    ticker = str(data.get("ticker", "")).upper()
    company = str(data.get("company_name", "") or ticker)
    peers: list[dict[str, Any]] = data.get("peer_comparison", []) or []

    with st.container(border=True):
        st.caption("同行比較 · Peer Comparison")
        st.markdown("**同業估值比較**")

        if not peers:
            # Build a placeholder row for the subject stock
            st.info("同行比較資料暫未取得，系統已記錄請求。")
            st.caption(f"分析股票：{_esc(ticker)} {_esc(company)}")
            return

        # Build table rows
        rows = []
        for p in peers:
            rows.append({
                "股票": _esc(p.get("ticker", "")),
                "公司": _esc(p.get("company", "")),
                "PE": _esc(p.get("pe", "N/A")),
                "PB": _esc(p.get("pb", "N/A")),
                "股息率": _esc(p.get("dividend_yield", "N/A")),
                "市值": _esc(p.get("market_cap", "N/A")),
                "風險分數": _esc(p.get("risk_score", "N/A")),
            })

        st.dataframe(rows, use_container_width=True, hide_index=True)

        # Advantage / disadvantage summary
        adv = data.get("advantage", "")
        dis = data.get("disadvantage", "")
        if adv or dis:
            cols = st.columns(2)
            if adv:
                with cols[0]:
                    with st.container(border=True):
                        st.markdown("**✅ 相對優勢**")
                        st.caption(_esc(adv))
            if dis:
                with cols[1]:
                    with st.container(border=True):
                        st.markdown("**⚠️ 相對弱勢**")
                        st.caption(_esc(dis))


# ─────────────────────────────────────────────────────────────────────────────
# PART 4 — Data Confidence Evidence
# ─────────────────────────────────────────────────────────────────────────────

_SOURCE_ICONS = {
    "Yahoo Finance": "✓",
    "Company Metadata": "✓",
    "Financial Statement": "✓",
    "News Source": "✓",
    "HKEX Filing": "✓",
}

_CONFIDENCE_REASONS = {
    "HIGH": "已取得公司名稱、現價、市值及股票元數據，財務指標完整。",
    "MEDIUM": "部分市場或財務資料未能取得，系統以保守假設處理缺失資料。",
    "LOW": "主要資料來源缺失，分析深度受限，結論僅供參考。",
    "INVALID": "股票代號驗證未完成，系統已停止深度分析，避免生成未驗證內容。",
}


def render_data_confidence(data: dict[str, Any]) -> None:
    """Data confidence evidence panel with coverage % and source checklist."""
    dc = data.get("data_confidence", {}) or {}
    level = str(dc.get("level", "MEDIUM")).upper()
    score = _safe_float(dc.get("score", 65), 65.0)
    sources: list[str] = dc.get("sources", []) or ["Yahoo Finance", "Company Metadata"]
    reason = str(dc.get("reason", "") or _CONFIDENCE_REASONS.get(level, ""))

    # Normalise level
    if "HIGH" in level:
        level_clean = "HIGH"
        badge_color = "🟢"
    elif "INVALID" in level or "驗證未完成" in level:
        level_clean = "INVALID"
        badge_color = "🔴"
    elif "LOW" in level:
        level_clean = "LOW"
        badge_color = "🔴"
    else:
        level_clean = "MEDIUM"
        badge_color = "🟡"

    with st.container(border=True):
        st.caption("資料可信度 · Data Confidence Evidence")
        top = st.columns([0.55, 0.45])

        with top[0]:
            st.markdown(f"**{badge_color} 資料可信度：{level_clean}**")
            st.caption(_esc(reason) if reason else _CONFIDENCE_REASONS.get(level_clean, ""))
            # Coverage bar
            cov_pct = min(max(int(score), 0), 100)
            st.caption(f"資料覆蓋率：{cov_pct}%")
            st.progress(cov_pct / 100)

        with top[1]:
            st.markdown("**已接入資料來源**")
            all_sources = ["Yahoo Finance", "Company Metadata", "Financial Statement", "News Source", "HKEX Filing"]
            for src in all_sources:
                icon = "✅" if src in sources else "⬜"
                st.caption(f"{icon} {src}")


# ─────────────────────────────────────────────────────────────────────────────
# PART 5 — Market Snapshot Chart (52-week range + price position)
# ─────────────────────────────────────────────────────────────────────────────

def render_market_snapshot(data: dict[str, Any]) -> None:
    """52-week high/low range bar with current price marker."""
    mkt = data.get("market_data", {}) or {}
    current = _safe_float(mkt.get("current_price"))
    high_52 = _safe_float(mkt.get("week_52_high"))
    low_52 = _safe_float(mkt.get("week_52_low"))
    volume = mkt.get("volume")

    if not (current > 0 and high_52 > 0 and low_52 > 0 and high_52 > low_52):
        return

    with st.container(border=True):
        st.caption("52週價格區間 · 52-Week Range")

        # Position percentage
        pos_pct = (current - low_52) / (high_52 - low_52) if (high_52 - low_52) > 0 else 0.5
        pos_pct = min(max(pos_pct, 0.0), 1.0)

        # Zone label
        if pos_pct >= 0.75:
            zone = "🐂 Bull Zone（接近52週高）"
        elif pos_pct <= 0.25:
            zone = "🐻 Bear Zone（接近52週低）"
        else:
            zone = "⚖️ 中性區間"

        cols = st.columns(3)
        cols[0].metric("52週低", f"HK${low_52:.2f}")
        cols[1].metric("現價", f"HK${current:.2f}", zone)
        cols[2].metric("52週高", f"HK${high_52:.2f}")

        st.caption(f"現價位置：{pos_pct * 100:.1f}%（由52週低計算）")
        st.progress(pos_pct)

        if _PLOTLY_OK:
            fig = go.Figure()
            # Range bar
            fig.add_trace(go.Bar(
                x=[high_52 - low_52],
                y=["52週區間"],
                base=[low_52],
                orientation="h",
                marker_color="rgba(100,160,220,0.25)",
                showlegend=False,
                hovertemplate=f"低: HK${low_52:.2f} | 高: HK${high_52:.2f}<extra></extra>",
            ))
            # Current price marker
            fig.add_trace(go.Scatter(
                x=[current],
                y=["52週區間"],
                mode="markers+text",
                marker=dict(size=14, color="#d9a441", symbol="diamond"),
                text=[f"HK${current:.2f}"],
                textposition="top center",
                showlegend=False,
                hovertemplate=f"現價: HK${current:.2f}<extra></extra>",
            ))
            fig.update_layout(
                height=120,
                margin=dict(l=0, r=0, t=8, b=8),
                xaxis=dict(showgrid=False, zeroline=False),
                yaxis=dict(showgrid=False),
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
            )
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

        if volume:
            st.caption(f"成交量：{_esc(volume)}")


# ─────────────────────────────────────────────────────────────────────────────
# PART 6 — Financial Trends (3-year bar charts)
# ─────────────────────────────────────────────────────────────────────────────

def _trend_chart(label: str, trend: list[Any]) -> None:
    """Render a single trend chart — plotly bar or st.bar_chart fallback."""
    if not trend:
        return

    # Parse trend items: each item is dict with "year"/"label" and "value"
    years = []
    values = []
    for item in trend:
        if isinstance(item, dict):
            yr = str(item.get("year") or item.get("label") or "")
            val = _safe_float(item.get("value") or item.get("amount") or 0)
        elif isinstance(item, (list, tuple)) and len(item) >= 2:
            yr = str(item[0])
            val = _safe_float(item[1])
        else:
            continue
        if yr:
            years.append(yr)
            values.append(val)

    if not years:
        return

    with st.container(border=True):
        st.caption(label)
        if _PLOTLY_OK:
            colors = ["#15a36d" if v >= 0 else "#d64545" for v in values]
            fig = go.Figure(go.Bar(
                x=years,
                y=values,
                marker_color=colors,
                hovertemplate="%{x}: %{y:,.0f}<extra></extra>",
            ))
            fig.update_layout(
                height=200,
                margin=dict(l=0, r=0, t=8, b=8),
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                xaxis=dict(showgrid=False),
                yaxis=dict(showgrid=True, gridcolor="rgba(0,0,0,0.06)"),
            )
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        else:
            import pandas as pd
            df = pd.DataFrame({"年度": years, label: values}).set_index("年度")
            st.bar_chart(df)


def render_financial_trends(data: dict[str, Any]) -> None:
    """Revenue / EBITDA / Net Profit / FCF 3-year trend charts."""
    fin = data.get("financial_data", {}) or {}
    revenue = fin.get("revenue_trend", []) or []
    ebitda = fin.get("ebitda_trend", []) or []
    net_profit = fin.get("net_profit_trend", []) or []
    fcf = fin.get("fcf_trend", []) or []

    has_any = any([revenue, ebitda, net_profit, fcf])
    if not has_any:
        return

    with st.container(border=True):
        st.caption("財務趨勢 · Financial Trends（三年）")
        cols = st.columns(2)
        with cols[0]:
            _trend_chart("收入趨勢 Revenue", revenue)
            _trend_chart("淨利潤趨勢 Net Profit", net_profit)
        with cols[1]:
            _trend_chart("EBITDA 趨勢", ebitda)
            _trend_chart("自由現金流 FCF", fcf)


# ─────────────────────────────────────────────────────────────────────────────
# PART 7 — Risk Dashboard
# ─────────────────────────────────────────────────────────────────────────────

_RISK_DIMS = [
    ("liquidity_risk", "流動性風險"),
    ("valuation_risk", "估值風險"),
    ("market_risk", "市場風險"),
    ("financial_risk", "財務風險"),
    ("news_risk", "新聞風險"),
]


def _risk_color(score: float) -> str:
    if score <= 3:
        return "🟢"
    if score <= 6:
        return "🟡"
    return "🔴"


def render_risk_dashboard(data: dict[str, Any]) -> None:
    """5-dimension risk dashboard with progress bars and total score."""
    risk = data.get("risk_analysis", {}) or {}

    with st.container(border=True):
        st.caption("風險儀表板 · Risk Dashboard")

        total_raw = risk.get("total_risk_score") or risk.get("composite_score")
        total = _safe_float(total_raw, 0.0)

        # Total score big display
        if total > 0:
            color = _risk_color(total)
            level = "低風險" if total <= 3 else ("中等風險" if total <= 6 else ("高風險" if total <= 8 else "極高風險"))
            top_cols = st.columns([0.3, 0.7])
            top_cols[0].metric("總風險分數", f"{total:.1f}/10", level)
            top_cols[1].markdown(f"**{color} {level}**")
            st.progress(min(total / 10, 1.0))
            st.divider()

        # 5 dimensions
        dim_cols = st.columns(2)
        for i, (key, label) in enumerate(_RISK_DIMS):
            val = _safe_float(risk.get(key), 0.0)
            if val <= 0:
                continue
            with dim_cols[i % 2]:
                with st.container(border=True):
                    icon = _risk_color(val)
                    st.caption(f"{icon} {label}")
                    st.markdown(f"**{val:.1f} / 10**")
                    st.progress(min(val / 10, 1.0))


# ─────────────────────────────────────────────────────────────────────────────
# PART 8 — News Sentiment Dashboard
# ─────────────────────────────────────────────────────────────────────────────

def render_news_sentiment(data: dict[str, Any]) -> None:
    """News sentiment counts + catalyst / watchlist items."""
    news = data.get("news_analysis", {}) or {}
    pos = int(news.get("positive_count", 0) or 0)
    neu = int(news.get("neutral_count", 0) or 0)
    neg = int(news.get("negative_count", 0) or 0)
    catalysts: list[str] = news.get("catalysts", []) or []
    watchlist: list[str] = news.get("watchlist", []) or []
    confidence = str(news.get("confidence", "") or "")

    with st.container(border=True):
        st.caption("新聞情緒分析 · News Sentiment Dashboard")

        count_cols = st.columns(3)
        count_cols[0].metric("🟢 正面新聞", pos)
        count_cols[1].metric("⚪ 中性新聞", neu)
        count_cols[2].metric("🔴 負面新聞", neg)

        if confidence:
            st.caption(f"新聞可信度：{_esc(confidence)}")

        total_news = pos + neu + neg
        if total_news > 0 and _PLOTLY_OK:
            fig = go.Figure(go.Bar(
                x=["正面", "中性", "負面"],
                y=[pos, neu, neg],
                marker_color=["#15a36d", "#8899aa", "#d64545"],
                hovertemplate="%{x}: %{y}<extra></extra>",
            ))
            fig.update_layout(
                height=160,
                margin=dict(l=0, r=0, t=8, b=8),
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                showlegend=False,
                xaxis=dict(showgrid=False),
                yaxis=dict(showgrid=False),
            )
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

        if catalysts:
            with st.container(border=True):
                st.markdown("**🚀 催化事件**")
                for item in catalysts[:5]:
                    st.caption(f"• {_esc(item)}")

        if watchlist:
            with st.container(border=True):
                st.markdown("**👁️ 監察事項**")
                for item in watchlist[:5]:
                    st.caption(f"• {_esc(item)}")

        if total_news == 0 and not catalysts and not watchlist:
            st.info("暫未接入即時新聞資料，系統不會生成未驗證事件。")


# ─────────────────────────────────────────────────────────────────────────────
# PART 9 — AI Investment Committee (Bull vs Bear Debate)
# ─────────────────────────────────────────────────────────────────────────────

def render_investment_committee(data: dict[str, Any]) -> None:
    """Bull vs Bear debate layout with committee verdict in centre."""
    ic = data.get("investment_committee", {}) or {}
    bull_pts: list[str] = ic.get("bull_points", []) or []
    bear_pts: list[str] = ic.get("bear_points", []) or []
    bull_score = _safe_float(ic.get("bull_score", 60), 60.0)
    bear_score = _safe_float(ic.get("bear_score", 40), 40.0)
    confidence = _safe_float(ic.get("confidence", 70), 70.0)
    summary = str(ic.get("committee_summary", "") or "")
    recommendation = str(ic.get("final_recommendation", "觀察") or "觀察")

    with st.container(border=True):
        st.caption("AI 投資委員會 · Investment Committee")
        st.markdown("### 🐂 牛熊辯論 🐻")

        left, centre, right = st.columns([0.38, 0.24, 0.38])

        # Bull side
        with left:
            with st.container(border=True):
                st.markdown("#### 🐂 牛市觀點")
                st.caption("市場分析 · 財務分析 · 新聞分析")
                if bull_pts:
                    for pt in bull_pts[:4]:
                        st.markdown(f"✅ {_esc(pt)}")
                else:
                    st.caption("暫無牛市論點。")
                st.metric("Bull Score", f"{bull_score:.0f}")

        # Centre verdict
        with centre:
            with st.container(border=True):
                st.markdown("#### ⚖️ 裁決")
                st.metric("信心指數", f"{confidence:.0f}%")
                st.metric("最終評級", _esc(recommendation))
                if summary:
                    st.caption(_esc(summary[:200]))

        # Bear side
        with right:
            with st.container(border=True):
                st.markdown("#### 🐻 熊市觀點")
                st.caption("風險分析 · 估值分析 · 事件分析")
                if bear_pts:
                    for pt in bear_pts[:4]:
                        st.markdown(f"⚠️ {_esc(pt)}")
                else:
                    st.caption("暫無熊市論點。")
                st.metric("Bear Score", f"{bear_score:.0f}")

        # Score bar
        if _PLOTLY_OK and (bull_score + bear_score) > 0:
            total = bull_score + bear_score
            fig = go.Figure()
            fig.add_trace(go.Bar(
                name="Bull",
                x=[bull_score / total * 100],
                y=["評分"],
                orientation="h",
                marker_color="#15a36d",
                hovertemplate=f"Bull: {bull_score:.0f}<extra></extra>",
            ))
            fig.add_trace(go.Bar(
                name="Bear",
                x=[bear_score / total * 100],
                y=["評分"],
                orientation="h",
                marker_color="#d64545",
                hovertemplate=f"Bear: {bear_score:.0f}<extra></extra>",
            ))
            fig.update_layout(
                barmode="stack",
                height=80,
                margin=dict(l=0, r=0, t=4, b=4),
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                showlegend=True,
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                xaxis=dict(showgrid=False, range=[0, 100], ticksuffix="%"),
                yaxis=dict(showgrid=False),
            )
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


# ─────────────────────────────────────────────────────────────────────────────
# PART 10 — Investment Conclusion Card
# ─────────────────────────────────────────────────────────────────────────────

_RATING_COLORS = {
    "買入": "#15a36d",
    "觀察": "#d9a441",
    "中性": "#667085",
    "減持": "#e07b39",
    "避免": "#d64545",
}

_RATING_EMOJI = {
    "買入": "🟢",
    "觀察": "🟡",
    "中性": "⚪",
    "減持": "🟠",
    "避免": "🔴",
}


def render_investment_conclusion(data: dict[str, Any]) -> None:
    """Final investment conclusion card."""
    ic = data.get("investment_conclusion", {}) or {}
    rating = str(ic.get("rating", "觀察") or "觀察")
    horizon = str(ic.get("horizon", "中線") or "中線")
    investor_type = str(ic.get("investor_type", "平衡") or "平衡")
    summary = str(ic.get("summary", "") or "")

    emoji = _RATING_EMOJI.get(rating, "⚪")

    with st.container(border=True):
        st.caption("最終投資結論 · Investment Conclusion")

        top = st.columns([0.4, 0.6])
        with top[0]:
            st.markdown(f"## {emoji} {_esc(rating)}")
            st.caption("投資委員會最終評級")

        with top[1]:
            detail_cols = st.columns(2)
            detail_cols[0].metric("投資週期", _esc(horizon))
            detail_cols[1].metric("適合投資者", _esc(investor_type))

        if summary:
            with st.container(border=True):
                st.markdown("**結論摘要**")
                st.caption(_esc(summary))

        # Rating scale visual
        all_ratings = ["買入", "觀察", "中性", "減持", "避免"]
        rating_cols = st.columns(len(all_ratings))
        for col, r in zip(rating_cols, all_ratings):
            is_active = r == rating
            bg = _RATING_COLORS.get(r, "#667085")
            style = f"background:{bg};color:#fff;border-radius:6px;padding:4px 2px;text-align:center;font-weight:{'900' if is_active else '400'};opacity:{'1' if is_active else '0.35'};"
            col.markdown(
                f'<div style="{style}">{_RATING_EMOJI.get(r,"")} {r}</div>',
                unsafe_allow_html=True,
            )
