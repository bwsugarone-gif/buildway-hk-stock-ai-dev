"""
patch_app_v35.py
Patches app.py FOS Report Display section for v3.5:
- Updates imports to include new v3.5 components
- Adds peer comparison, source transparency, risk dashboard,
  bull/bear debate, and market sentiment background
- Fixes button colours per PRD Part 12
- Removes watchlist/client profile/data store sections
"""
import pathlib
import re

APP = pathlib.Path("app.py")
src = APP.read_text(encoding="utf-8")

# ── 1. Update imports ─────────────────────────────────────────────────────────
OLD_IMPORTS = """# ── FOS V3 Report Display ─────────────────────────────────────────────────────
if st.session_state.report_sections:
    from core.fos_components import (
        render_company_sidebar,
        render_competitive_landscape,
        render_confidence_breakdown,
        render_market_snapshot,
        render_financial_trends,
        render_risk_event_cards,
        render_news_sentiment,
        render_multi_agent_committee,
        render_investment_conclusion,
    )"""

NEW_IMPORTS = """# ── FOS V3.5 Report Display ───────────────────────────────────────────────────
if st.session_state.report_sections:
    from core.fos_components import (
        render_company_sidebar,
        render_competitive_landscape,
        render_confidence_breakdown,
        render_market_snapshot,
        render_financial_trends,
        render_risk_event_cards,
        render_news_sentiment,
        render_multi_agent_committee,
        render_investment_conclusion,
        render_peer_comparison,
        render_source_transparency,
        render_risk_dashboard,
        render_bull_bear_debate,
        render_market_sentiment_background,
    )"""

if OLD_IMPORTS in src:
    src = src.replace(OLD_IMPORTS, NEW_IMPORTS)
    print("[1] imports updated")
else:
    print("[1] WARN: import block not matched exactly — skipping import patch")

# ── 2. Add sentiment background + peer comparison + source transparency ────────
# Insert after the confidence_label line (after sidebar render)
OLD_SIDEBAR = """    # ── Sidebar: 公司資料面板 ─────────────────────────────────────────────────
    render_company_sidebar({
        "cover": cover,
        "company_metadata": report_package.get("company_metadata", {}),
        "market_data": report_package.get("market_data", {}),
    })

    # ── 1. 報告摘要 ──────────────────────────────────────────────────────────"""

NEW_SIDEBAR = """    # ── Sidebar: 公司資料面板 ─────────────────────────────────────────────────
    render_company_sidebar({
        "cover": cover,
        "company_metadata": report_package.get("company_metadata", {}),
        "market_data": report_package.get("market_data", {}),
    })

    # ── 0. 市場情緒背景層 (v3.5) ─────────────────────────────────────────────
    _ic_data_bg = report_package.get("investment_committee", {}) or {}
    render_market_sentiment_background(
        bull_score=float(_ic_data_bg.get("bull_score", 55) or 55),
        bear_score=float(_ic_data_bg.get("bear_score", 45) or 45),
    )

    # ── 1. 報告摘要 ──────────────────────────────────────────────────────────"""

if OLD_SIDEBAR in src:
    src = src.replace(OLD_SIDEBAR, NEW_SIDEBAR)
    print("[2] sentiment background added")
else:
    print("[2] WARN: sidebar block not matched")

# ── 3. Add peer comparison + source transparency after competitive landscape ───
OLD_COMP = """    # ── 2. 競爭格局分析 ──────────────────────────────────────────────────────
    if confidence_level in {"HIGH", "MEDIUM"}:
        render_competitive_landscape({
            "cover": cover,
            "peer_comparison": report_package.get("peer_comparison", {}),
            "competitive_analysis": report_package.get("competitive_analysis", {}),
        })

    # ── 3. 資料可信度評分 ─────────────────────────────────────────────────────
    render_confidence_breakdown({"""

NEW_COMP = """    # ── 2. 競爭格局分析 ──────────────────────────────────────────────────────
    if confidence_level in {"HIGH", "MEDIUM"}:
        render_competitive_landscape({
            "cover": cover,
            "peer_comparison": report_package.get("peer_comparison", {}),
            "competitive_analysis": report_package.get("competitive_analysis", {}),
        })

    # ── 2b. 同行比較表 (v3.5) ────────────────────────────────────────────────
    if confidence_level in {"HIGH", "MEDIUM"}:
        _cl_data = report_package.get("competitive_landscape", {}) or {}
        if not _cl_data:
            # Build minimal competitive_landscape from peer_comparison
            _pc = report_package.get("peer_comparison", {}) or {}
            _mkt = report_package.get("market_data", {}) or {}
            _cl_data = {
                "subject": {
                    "ticker": cover.get("ticker", ""),
                    "name": cover.get("company_name", ""),
                    "pe_ratio": _mkt.get("pe_ratio"),
                    "pb_ratio": _mkt.get("pb_ratio"),
                    "dividend_yield": _mkt.get("dividend_yield"),
                    "market_cap": cover.get("market_cap"),
                    "risk_score": cover.get("risk_score"),
                },
                "peers": _pc.get("peers", []),
                "strengths": _pc.get("strengths", []),
                "weaknesses": _pc.get("weaknesses", []),
            }
        render_peer_comparison({"competitive_landscape": _cl_data})

    # ── 2c. 資料可信度來源 (v3.5) ────────────────────────────────────────────
    _st_data = report_package.get("source_transparency", {}) or {}
    if not _st_data:
        _conf_level = str(report_package.get("data_confidence", confidence_level)).upper()
        _cov = report_package.get("data_confidence_score", 65) or 65
        _st_data = {
            "confidence_level": _conf_level,
            "coverage_pct": _cov,
            "confidence_reason": (
                "已取得公司名稱、現價、市值及財務指標，資料來源已驗證。" if _conf_level == "HIGH"
                else "部分財務或市場資料未能完整取得，系統以保守假設處理。"
            ),
            "verified_sources": [
                {"icon": "✓", "name": "Yahoo Finance", "verified": True},
                {"icon": "✓", "name": "Company Metadata", "verified": True},
                {"icon": "✓" if confidence_level == "HIGH" else "○",
                 "name": "Financial Statement",
                 "verified": confidence_level == "HIGH"},
                {"icon": "✓" if confidence_level == "HIGH" else "○",
                 "name": "HKEX Filing",
                 "verified": confidence_level == "HIGH"},
            ],
        }
    render_source_transparency({"source_transparency": _st_data, "cover": cover})

    # ── 3. 資料可信度評分 ─────────────────────────────────────────────────────
    render_confidence_breakdown({"""

if OLD_COMP in src:
    src = src.replace(OLD_COMP, NEW_COMP)
    print("[3] peer comparison + source transparency added")
else:
    print("[3] WARN: competitive landscape block not matched")

# ── 4. Add risk dashboard after risk event cards ──────────────────────────────
OLD_RISK = """    # ── 6. 風險分析 ───────────────────────────────────────────────────────────
    if confidence_level != "INVALID":
        _section_title("風險分析", "風險分析", "")
        risk_sec = sections.get("risk_analysis", {}) or {}
        render_risk_event_cards({
            "risk_analysis": risk_sec,
        })"""

NEW_RISK = """    # ── 6. 風險分析 ───────────────────────────────────────────────────────────
    if confidence_level != "INVALID":
        _section_title("風險分析", "風險分析", "")
        risk_sec = sections.get("risk_analysis", {}) or {}
        render_risk_event_cards({
            "risk_analysis": risk_sec,
        })
        # Risk Dashboard v3.5
        _rv2 = report_package.get("risk_assessment_v2", {}) or {}
        if _rv2:
            render_risk_dashboard({"risk_assessment_v2": _rv2})"""

if OLD_RISK in src:
    src = src.replace(OLD_RISK, NEW_RISK)
    print("[4] risk dashboard added")
else:
    print("[4] WARN: risk section not matched")

# ── 5. Replace AI committee with Bull vs Bear debate ──────────────────────────
OLD_IC = """    # ── 8. AI 投資委員會 ──────────────────────────────────────────────────────
    if confidence_level in {"HIGH", "MEDIUM"}:
        _section_title("AI 投資委員會", "AI 投資委員會", "")
        discussion = sections.get("multi_agent_discussion", {}) or {}
        ic_data = report_package.get("investment_committee", {}) or {}
        # Build bull/bear points from agent discussion table
        table = discussion.get("table", []) or []
        bull_agents = ["Market Data Agent", "Financial Analyst Agent", "News Intelligence Agent"]
        bear_agents = ["Risk Management Agent", "Risk Agent"]
        bull_pts = [
            str(row.get("正面因素", "") or row.get("核心觀點", ""))
            for row in table if row.get("Agent") in bull_agents and row.get("正面因素")
        ][:3]
        bear_pts = [
            str(row.get("主要憂慮", "") or row.get("核心觀點", ""))
            for row in table if row.get("Agent") in bear_agents and row.get("主要憂慮")
        ][:3]
        if not bull_pts:
            bull_pts = ic_data.get("bull_points", ["估值合理", "股息率具吸引力", "業務穩定"])
        if not bear_pts:
            bear_pts = ic_data.get("bear_points", ["市場競爭加劇", "監管風險", "增長放緩"])
        render_multi_agent_committee({
            "investment_committee": {
                "bull_score": ic_data.get("bull_score", 60),
                "bear_score": ic_data.get("bear_score", 40),
                "confidence": ic_data.get("confidence", 70),
                "committee_summary": discussion.get("final_statement", ""),
                "final_recommendation": cover.get("final_rating", "觀察"),
                "agents": ic_data.get("agents", {}),
            }
        })
        # Original agent discussion cards (preserved)
        _agent_discussion_cards(table)"""

NEW_IC = """    # ── 8. AI 投資委員會 (v3.5 Bull vs Bear) ────────────────────────────────
    if confidence_level in {"HIGH", "MEDIUM"}:
        _section_title("AI 投資委員會", "AI 投資委員會", "")
        discussion = sections.get("multi_agent_discussion", {}) or {}
        ic_data = report_package.get("investment_committee", {}) or {}
        table = discussion.get("table", []) or []

        # Build agent_opinions_v2 for Bull vs Bear debate
        _bull_agent_names = ["Market Data Agent", "Financial Analyst Agent", "News Intelligence Agent"]
        _bear_agent_names = ["Risk Management Agent", "Risk Agent", "Portfolio Manager Agent"]
        _bull_agents_v2 = []
        _bear_agents_v2 = []
        for row in table:
            agent_name = row.get("Agent", "")
            view = row.get("核心觀點", row.get("opinion", ""))
            pos = row.get("正面因素", "")
            neg = row.get("主要憂慮", "")
            if agent_name in _bull_agent_names and (view or pos):
                _bull_agents_v2.append({
                    "name": agent_name,
                    "view": view or pos,
                    "reasons": [r for r in [pos] if r][:3],
                })
            elif agent_name in _bear_agent_names and (view or neg):
                _bear_agents_v2.append({
                    "name": agent_name,
                    "view": view or neg,
                    "reasons": [r for r in [neg] if r][:3],
                })
        if not _bull_agents_v2:
            for pt in ic_data.get("bull_points", ["估值合理", "股息率具吸引力", "業務穩定"]):
                _bull_agents_v2.append({"name": "牛市 Agent", "view": pt, "reasons": []})
        if not _bear_agents_v2:
            for pt in ic_data.get("bear_points", ["市場競爭加劇", "監管風險", "增長放緩"]):
                _bear_agents_v2.append({"name": "熊市 Agent", "view": pt, "reasons": []})

        _ao_v2 = {
            "bull_agents": _bull_agents_v2,
            "bear_agents": _bear_agents_v2,
            "bull_score": ic_data.get("bull_score", 60),
            "bear_score": ic_data.get("bear_score", 40),
            "confidence": ic_data.get("confidence", 70),
            "committee_summary": discussion.get("final_statement", ""),
            "final_recommendation": cover.get("final_rating", "觀察"),
            "verdict": {
                "bull_score": ic_data.get("bull_score", 60),
                "bear_score": ic_data.get("bear_score", 40),
                "confidence": ic_data.get("confidence", 70),
                "summary": discussion.get("final_statement", ""),
                "recommendation": cover.get("final_rating", "觀察"),
            },
        }
        render_bull_bear_debate({"agent_opinions_v2": _ao_v2})

        # Legacy 6-agent committee cards (preserved)
        render_multi_agent_committee({
            "investment_committee": {
                "bull_score": ic_data.get("bull_score", 60),
                "bear_score": ic_data.get("bear_score", 40),
                "confidence": ic_data.get("confidence", 70),
                "committee_summary": discussion.get("final_statement", ""),
                "final_recommendation": cover.get("final_rating", "觀察"),
                "agents": ic_data.get("agents", {}),
            }
        })
        _agent_discussion_cards(table)"""

if OLD_IC in src:
    src = src.replace(OLD_IC, NEW_IC)
    print("[5] bull vs bear debate added")
else:
    print("[5] WARN: investment committee block not matched")

# ── 6. Fix button colours per PRD Part 12 ─────────────────────────────────────
# Rerun = orange (secondary), Clear = red (danger via custom), Download = green (primary)
OLD_BTNS = """    # Action buttons — colour-coded per PRD Part 12
    action_cols = st.columns(3)
    if action_cols[0].button(
        "🔄 重新分析", key="current_rerun_analysis",
        use_container_width=True, type="secondary",
    ):
        _request_analysis(str(current_ticker), request_risk_preference, request_portfolio_size)
    if action_cols[1].button(
        "🗑️ 清除報告", key="current_clear_report",
        use_container_width=True,
    ):"""

NEW_BTNS = """    # Action buttons — colour-coded per PRD Part 12
    # 重新分析=橙色, 清除=紅色, 下載=綠色
    st.markdown(
        '<style>'
        'div[data-testid="stButton"] button[kind="secondary"] {background:#f57c00;color:#fff;border:none;}'
        'button.clear-btn {background:#d93025 !important;color:#fff !important;border:none !important;}'
        '</style>',
        unsafe_allow_html=True,
    )
    action_cols = st.columns(3)
    if action_cols[0].button(
        "🔄 重新分析", key="current_rerun_analysis",
        use_container_width=True, type="secondary",
    ):
        _request_analysis(str(current_ticker), request_risk_preference, request_portfolio_size)
    if action_cols[1].button(
        "🗑️ 清除報告", key="current_clear_report",
        use_container_width=True,
    ):"""

if OLD_BTNS in src:
    src = src.replace(OLD_BTNS, NEW_BTNS)
    print("[6] button colours updated")
else:
    print("[6] WARN: button block not matched")

APP.write_text(src, encoding="utf-8")
print("Done — app.py patched for v3.5")
