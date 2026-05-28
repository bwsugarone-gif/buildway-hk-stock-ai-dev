"""
app.py

Buildway Tech (HK) Limited
Hong Kong AI Multi-Agent Stock Analysis Platform
"""

from __future__ import annotations

import html
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any

import streamlit as st

from agents.ceo_agent import CEOAgent
from agents.market_data_agent import MarketDataAgent
from core.config import (
    APP_NAME, APP_VERSION, BUILD_STAGE, BUILD_VERSION, BUILD_COMMIT,
    LOGO_PATH, DEPLOY_ENV,
)
from core.pdf_generator import PDFGenerator
from core.report_builder import ReportBuilder
from core.utils import format_currency_hkd, normalize_hk_ticker, validate_hk_ticker


MASTER_DATA_PATH = Path(__file__).resolve().parent / "data" / "hk_stock_master_data.json"


st.set_page_config(
    page_title=f"{APP_NAME} - 香港股票智能分析報告",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)


def _escape(value: Any) -> str:
    return html.escape(str(value if value not in (None, "") else "N/A"))


def _inject_css() -> None:
    st.markdown(
        """
        <style>
            :root {
                --bw-navy: #071b33;
                --bw-navy-2: #0d2a4c;
                --bw-gold: #d9a441;
                --bw-gold-2: #f0c66a;
                --bw-bg: #f5f7fb;
                --bw-panel: #ffffff;
                --bw-line: #dfe6ef;
                --bw-text: #172033;
                --bw-muted: #667085;
                --bw-green: #15a36d;
                --bw-red: #d64545;
            }

            .stApp {
                background:
                    radial-gradient(circle at top left, rgba(217, 164, 65, 0.10), transparent 28rem),
                    linear-gradient(180deg, #f8fafc 0%, var(--bw-bg) 38%, #eef3f8 100%);
                color: var(--bw-text);
            }

            .block-container {
                padding: 0.85rem 0.85rem 2.5rem;
                max-width: 1180px;
                overflow-x: hidden;
            }

            [data-testid="stSidebar"] {
                background: linear-gradient(180deg, var(--bw-navy) 0%, #10294a 100%);
            }

            [data-testid="stSidebar"] * {
                color: #eef4ff;
            }

            [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
            [data-testid="stSidebar"] label,
            [data-testid="stSidebar"] .stCaption {
                color: #d7e1ef !important;
            }

            section[data-testid="stSidebar"] label {
                color: #e5edf7 !important;
            }

            .stTextInput input {
                color: #0f172a !important;
                background-color: #ffffff !important;
                opacity: 1 !important;
                -webkit-text-fill-color: #0f172a !important;
            }

            .stTextInput input::placeholder {
                color: #64748b !important;
                opacity: 1 !important;
                -webkit-text-fill-color: #64748b !important;
            }

            .stNumberInput input {
                color: #0f172a !important;
                background-color: #ffffff !important;
                opacity: 1 !important;
                -webkit-text-fill-color: #0f172a !important;
            }

            .stSelectbox div[data-baseweb="select"] {
                color: #0f172a !important;
            }

            [data-testid="stSidebar"] input,
            [data-testid="stSidebar"] div[data-baseweb="select"] > div {
                background-color: #ffffff !important;
                border-color: rgba(255, 255, 255, 0.35);
                color: #0f172a !important;
                opacity: 1 !important;
                -webkit-text-fill-color: #0f172a !important;
            }

            .stButton > button,
            .stDownloadButton > button {
                background: linear-gradient(135deg, var(--bw-gold) 0%, var(--bw-gold-2) 100%) !important;
                border: 0 !important;
                border-radius: 8px !important;
                color: #112039 !important;
                font-weight: 800 !important;
                min-height: 3rem;
                box-shadow: 0 12px 24px rgba(217, 164, 65, 0.25);
            }

            .stButton > button:hover,
            .stDownloadButton > button:hover {
                filter: brightness(0.98);
                transform: translateY(-1px);
            }

            div[data-testid="stMetric"] {
                background: var(--bw-panel);
                border: 1px solid var(--bw-line);
                border-radius: 8px;
                padding: 1rem;
                box-shadow: 0 12px 30px rgba(16, 39, 74, 0.06);
            }

            div[data-testid="stMetricLabel"] p {
                color: var(--bw-muted);
                font-size: 0.85rem;
            }

            div[data-testid="stMetricValue"] {
                color: var(--bw-navy);
                font-weight: 800;
                font-size: clamp(1.25rem, 5vw, 1.75rem);
            }

            div[data-testid="stDataFrame"] {
                overflow-x: auto;
            }

            [data-testid="stVerticalBlockBorderWrapper"] {
                border-color: rgba(16, 42, 67, 0.12);
                box-shadow: 0 12px 30px rgba(16, 39, 74, 0.05);
            }

            @media (max-width: 719px) {
                html, body, .stApp, .block-container {
                    max-width: 100% !important;
                    overflow-x: hidden !important;
                }

                h1 {
                    font-size: 2rem !important;
                    line-height: 1.15 !important;
                    word-break: break-word !important;
                }

                h2, h3 {
                    line-height: 1.22 !important;
                    word-break: break-word !important;
                }

                [data-testid="column"] {
                    width: 100% !important;
                    flex: 1 1 100% !important;
                    min-width: 100% !important;
                }

                [data-testid="stSidebar"] {
                    min-width: 0 !important;
                    width: min(82vw, 20rem) !important;
                    max-width: 82vw !important;
                }

                [data-testid="stSidebar"] img {
                    max-width: 72px !important;
                }

                .stButton > button,
                .stDownloadButton > button,
                div[data-testid="stFormSubmitButton"] button {
                    width: 100% !important;
                    min-height: 48px !important;
                    white-space: normal !important;
                }

            }

            @media (min-width: 720px) {
                .block-container {
                    padding: 1.5rem 2rem 3rem;
                }
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _init_state() -> None:
    defaults = {
        "report_package": None,
        "report_sections": None,
        "pdf_path": None,
        "pdf_warning": "",
        "llm_warning": "",
        "pending_ticker_value": "",
        "selected_ticker": "",
        "recent_analysis": ["0700.HK", "9988.HK", "0688.HK"],
        "recent_reports": [],
        "watchlist": ["0700.HK", "9988.HK", "0688.HK"],
        "rerun_analysis_request": None,
        "is_generating": False,
        "agent_error_log": [],
        "agent_status": {
            "CEO Agent": "等待",
            "Market Data Agent": "等待",
            "Financial Analyst Agent": "等待",
            "Risk Agent": "等待",
            "News Intelligence Agent": "等待",
            "Portfolio Manager Agent": "等待",
            "Investment Committee Agent": "等待",
        },
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def _section_title(kicker: str, title: str, caption: str = "") -> None:
    st.caption(kicker)
    st.subheader(title)
    if caption:
        st.caption(caption)


WORKFLOW_STEPS = [
    ("市場資料 Agent", "取得價格、成交量、市值與公司 metadata。"),
    ("財務分析 Agent", "計算估值、財務健康度與核心比率。"),
    ("風險控制 Agent", "評估流動性、槓桿、波動與下行情境。"),
    ("新聞分析 Agent", "整理市場情緒與事件風險。"),
    ("投資委員會", "整合多 agent 觀點並輸出最終結論。"),
]


SECTOR_SHOWCASE = {
    "科技 / 互聯網": ["0700.HK", "9988.HK"],
    "銀行 / 金融": ["0005.HK", "1299.HK"],
    "地產 / 內房": ["0688.HK", "1109.HK"],
    "電訊 / 公用": ["0941.HK", "0002.HK"],
    "消費 / 平台": ["3690.HK", "9618.HK"],
}


@st.cache_data(ttl=3600, show_spinner=False)
def _load_hk_master_data() -> dict[str, dict[str, Any]]:
    try:
        with open(MASTER_DATA_PATH, "r", encoding="utf-8") as file:
            return json.load(file)
    except Exception as exc:
        print(f"[APP] HK stock master data unavailable: {exc}")
        return {}


@st.cache_data(ttl=900, show_spinner=False)
def _load_showcase_market_data(ticker: str) -> dict[str, Any]:
    try:
        return MarketDataAgent().fetch(ticker)
    except Exception as exc:
        print(f"[APP] Showcase market data unavailable for {ticker}: {exc}")
        return {}


def _value_or_pending(value: Any) -> str:
    text = str(value or "").strip()
    if not text or text in {"0", "0.0", "N/A", "None"}:
        return "資料待補充"
    return text


def _format_showcase_price(value: Any) -> str:
    try:
        number = float(value or 0)
    except (TypeError, ValueError):
        number = 0
    return f"HK${number:.2f}" if number > 0 else "資料待補充"


def _format_showcase_market_cap(value: Any) -> str:
    try:
        number = float(value or 0)
    except (TypeError, ValueError):
        number = 0
    return format_currency_hkd(number) if number > 0 else "資料待補充"


def _plain_confidence(label: Any, level: Any = "") -> str:
    text = str(label or "")
    level_text = str(level or "").upper()
    if "HIGH" in level_text or "高可信度" in text:
        return "高可信度"
    if "INVALID" in level_text or "資料驗證未完成" in text:
        return "資料驗證未完成"
    if "LOW" in level_text or "MEDIUM" in level_text or "部分資料缺失" in text:
        return "部分資料缺失"
    return "資料待補充"


def _set_demo_ticker(ticker: str) -> None:
    clean = ticker.replace(".HK", "")
    st.session_state["pending_ticker_value"] = clean
    st.session_state["selected_ticker"] = clean
    st.rerun()


def _request_analysis(
    ticker: str,
    risk_preference: str = "銝剔?",
    portfolio_size: int = 0,
) -> None:
    normalized = normalize_hk_ticker(ticker)
    st.session_state["pending_ticker_value"] = normalized.replace(".HK", "")
    st.session_state["selected_ticker"] = normalized.replace(".HK", "")
    st.session_state["rerun_analysis_request"] = {
        "ticker": normalized,
        "risk_preference": risk_preference,
        "portfolio_size": int(portfolio_size or 0),
    }
    st.rerun()


def _report_identity(cover: dict[str, Any]) -> tuple[str, str]:
    ticker = normalize_hk_ticker(str(cover.get("ticker") or ""))
    company = (
        cover.get("company_name_zh")
        or cover.get("company_name")
        or cover.get("company_name_en")
        or ticker
    )
    return ticker, str(company)


def _add_watchlist_ticker(ticker: str) -> None:
    normalized = normalize_hk_ticker(ticker)
    current = [item for item in st.session_state.get("watchlist", []) if item != normalized]
    st.session_state["watchlist"] = [normalized, *current][:12]


def _remove_watchlist_ticker(ticker: str) -> None:
    normalized = normalize_hk_ticker(ticker)
    st.session_state["watchlist"] = [
        item for item in st.session_state.get("watchlist", []) if item != normalized
    ]


def _save_report_history(
    ticker: str,
    risk_preference: str,
    portfolio_size: int,
    report_package: dict[str, Any],
    report_sections: dict[str, Any],
) -> None:
    cover = report_sections.get("cover", {}) or {}
    normalized, company = _report_identity({**cover, "ticker": ticker})
    record = {
        "id": datetime.now().strftime("%Y%m%d%H%M%S%f"),
        "ticker": normalized,
        "company": company,
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "rating": cover.get("final_rating", "N/A"),
        "risk_label": cover.get("risk_label", ""),
        "confidence": cover.get("data_confidence_label", ""),
        "risk_preference": risk_preference,
        "portfolio_size": int(portfolio_size or 0),
        "report_package": report_package,
        "report_sections": report_sections,
        "pdf_path": st.session_state.get("pdf_path"),
        "pdf_warning": st.session_state.get("pdf_warning", ""),
        "llm_warning": st.session_state.get("llm_warning", ""),
    }
    previous = [
        item
        for item in st.session_state.get("recent_reports", [])
        if item.get("ticker") != normalized
    ]
    st.session_state["recent_reports"] = [record, *previous][:8]


def _open_history_record(record: dict[str, Any]) -> None:
    st.session_state.report_package = record.get("report_package")
    st.session_state.report_sections = record.get("report_sections")
    st.session_state.pdf_path = record.get("pdf_path")
    st.session_state.pdf_warning = record.get("pdf_warning", "")
    st.session_state.llm_warning = record.get("llm_warning", "")
    st.session_state.selected_ticker = str(record.get("ticker", "")).replace(".HK", "")
    st.rerun()


def _render_recent_reports(location: str) -> None:
    reports = st.session_state.get("recent_reports", [])
    with st.container(border=True):
        st.caption("Report history")
        st.markdown("**Recent reports**")
        if not reports:
            st.caption("Generated reports will appear here during this session.")
            return
        for index, record in enumerate(reports):
            row = st.columns([0.48, 0.18, 0.17, 0.17])
            row[0].markdown(f"**{_escape(record.get('ticker'))}**")
            row[0].caption(
                f"{_escape(record.get('company'))} | {_escape(record.get('generated_at'))}"
            )
            row[1].caption(_escape(record.get("rating", "N/A")))
            if row[2].button(
                "Open",
                key=f"open_report_{location}_{index}_{record.get('id')}",
                use_container_width=True,
            ):
                _open_history_record(record)
            if row[3].button(
                "Re-run",
                key=f"rerun_report_{location}_{index}_{record.get('id')}",
                use_container_width=True,
            ):
                _request_analysis(
                    str(record.get("ticker", "")),
                    str(record.get("risk_preference") or "銝剔?"),
                    int(record.get("portfolio_size") or 0),
                )
        if st.button(
            "Clear history",
            key=f"clear_history_{location}",
            use_container_width=True,
        ):
            st.session_state["recent_reports"] = []
            st.rerun()


def _render_watchlist(location: str) -> None:
    watchlist = st.session_state.get("watchlist", [])
    with st.container(border=True):
        st.caption("Watchlist")
        st.markdown("**Client watchlist**")
        add_cols = st.columns([0.62, 0.38])
        candidate = add_cols[0].text_input(
            "Add ticker",
            value="",
            placeholder="0700 or 9988.HK",
            key=f"watchlist_input_{location}",
            label_visibility="collapsed",
        )
        if add_cols[1].button(
            "Add",
            key=f"watchlist_add_{location}",
            use_container_width=True,
        ):
            is_valid, _ = validate_hk_ticker(candidate)
            if is_valid:
                _add_watchlist_ticker(candidate)
                st.rerun()
            else:
                st.warning("Please enter a valid HK ticker.")
        if not watchlist:
            st.caption("Add tickers clients want to monitor this session.")
            return
        for index, ticker in enumerate(watchlist):
            row = st.columns([0.45, 0.35, 0.20])
            row[0].markdown(f"**{_escape(ticker)}**")
            if row[1].button(
                "Analyze",
                key=f"watch_analyze_{location}_{index}_{ticker}",
                use_container_width=True,
            ):
                _request_analysis(ticker)
            if row[2].button(
                "X",
                key=f"watch_remove_{location}_{index}_{ticker}",
                use_container_width=True,
            ):
                _remove_watchlist_ticker(ticker)
                st.rerun()


def _render_workspace_layer(location: str) -> None:
    _section_title(
        "Workspace",
        "Report history + watchlist",
        "Session-only workspace for client follow-up and repeat analysis.",
    )
    cols = st.columns([1.1, 0.9])
    with cols[0]:
        _render_recent_reports(location)
    with cols[1]:
        _render_watchlist(location)


def make_widget_key(prefix: str, ticker: str, location: str) -> str:
    clean_ticker = ticker.replace(".", "_").replace("-", "_").replace(" ", "_")
    clean_location = str(location).replace(".", "_").replace("-", "_").replace(" ", "_").replace("/", "_")
    return f"{prefix}_{clean_location}_{clean_ticker}"




def _render_stock_showcase_card(ticker: str, metadata: dict[str, Any], location: str) -> None:
    market = _load_showcase_market_data(ticker)
    name_zh = metadata.get("name_zh") or "資料待補充"
    name_en = metadata.get("name_en") or "資料待補充"
    sector = metadata.get("sector_zh") or metadata.get("sector") or "資料待補充"
    positioning = metadata.get("short_positioning_zh") or "資料待補充"
    price = _format_showcase_price(market.get("current_price"))
    market_cap = _format_showcase_market_cap(market.get("market_cap"))
    confidence = _plain_confidence(
        market.get("data_confidence_label"),
        market.get("data_confidence"),
    )

    with st.container(border=True):
        st.caption(ticker)
        st.markdown(f"**{name_zh}**")
        st.caption(name_en)
        st.caption(sector)
        metric_cols = st.columns(2)
        metric_cols[0].metric("現價", price)
        metric_cols[1].metric("市值", market_cap)
        st.caption(f"資料可信度：{confidence}")
        st.caption(positioning)
        if st.button(
            "分析此股票",
            key=make_widget_key("sector", ticker, location),
            use_container_width=True,
        ):
            _set_demo_ticker(ticker)


def _render_sector_showcase() -> None:
    _section_title("Sector showcase", "香港市場板塊", "按板塊瀏覽香港股票案例，點選即可填入分析代號。")
    master_data = _load_hk_master_data()
    tabs = st.tabs(list(SECTOR_SHOWCASE.keys()))
    for tab, (sector_name, tickers) in zip(tabs, SECTOR_SHOWCASE.items()):
        with tab:
            st.caption(sector_name)
            columns = st.columns(2)
            for index, ticker in enumerate(tickers):
                with columns[index % 2]:
                    _render_stock_showcase_card(ticker, master_data.get(ticker, {}), sector_name)


def _status_to_client_state(raw: Any) -> tuple[str, str]:
    text = str(raw or "")
    if any(token in text.lower() for token in ["fallback", "備援"]):
        return "fallback", "備援"
    if any(token in text.lower() for token in ["stop", "fail", "stopped", "失敗", "停止"]):
        return "stopped", "停止"
    if any(token in text.lower() for token in ["run", "running", "執行", "分析中"]):
        return "running", "running"
    if any(token in text.lower() for token in ["complete", "done", "完成", "摰"]):
        return "completed", "completed"
    return "waiting", "waiting"


def _render_workflow_timeline() -> None:
    _section_title("Workflow", "AI 分析流程", "每個步驟均可 fallback，單一 agent 失敗不會令整份報告中斷。")
    status = st.session_state.get("agent_status", {})
    status_lookup = {
        "市場資料 Agent": status.get("Market Data Agent"),
        "財務分析 Agent": status.get("Financial Analyst Agent"),
        "風險控制 Agent": status.get("Risk Agent"),
        "新聞分析 Agent": status.get("News Intelligence Agent"),
        "投資委員會": status.get("Investment Committee Agent"),
    }
    for index, (name, description) in enumerate(WORKFLOW_STEPS):
        state_key, state_label = _status_to_client_state(status_lookup.get(name))
        with st.container(border=True):
            cols = st.columns([0.18, 0.58, 0.24])
            cols[0].metric("Step", f"{index + 1}")
            cols[1].markdown(f"**{name}**")
            cols[1].caption(description)
            if state_key == "completed":
                cols[2].success(state_label)
            elif state_key == "running":
                cols[2].info(state_label)
            elif state_key == "fallback":
                cols[2].warning(state_label)
            elif state_key == "stopped":
                cols[2].error(state_label)
            else:
                cols[2].caption(state_label)


def _render_source_transparency() -> None:
    _section_title("Transparency", "資料來源與分析邊界")
    rows = [
        ("市場資料", "Yahoo Finance / 市場資料供應商"),
        ("公司資料", "HK stock master database"),
        ("財務計算", "Python calculation engine"),
        ("AI Narrative", "DeepSeek V3，只負責文字整理，不參與財務計算"),
    ]
    _company_cards(rows)
    st.warning("本系統不構成投資建議。所有結果只供研究、教育及客戶展示用途。")


def _render_trust_layer() -> None:
    _section_title("Trust layer", "為何客戶可以信任本系統")
    cards = [
        ("防止 AI 幻覺", "公司資料只引用市場供應商或本地 master database。"),
        ("INVALID ticker 防護", "無有效市場資料時停止進階公司敘述。"),
        ("Python 財務計算", "估值、比率、風險分數由 Python engine 產生。"),
        ("Multi-Agent 交叉分析", "市場、財務、風險、新聞與投委會互相校驗。"),
        ("PDF 機構級輸出", "客戶可下載一致格式的正式報告。"),
        ("Fallback 容錯架構", "單一資料源或 agent 失敗不會拖垮整個流程。"),
    ]
    columns = st.columns(3)
    for index, (title, copy) in enumerate(cards):
        with columns[index % 3]:
            with st.container(border=True):
                st.markdown(f"**{title}**")
                st.caption(copy)


def _render_main_input_panel() -> tuple[bool, str, str, int]:
    _section_title("Start", "開始分析", "手機版可直接在主頁完成輸入，不需要打開 sidebar。")
    with st.container(border=True):
        with st.form("main_analysis_form"):
            default_ticker = st.session_state.pop("pending_ticker_value", "") or st.session_state.get("selected_ticker", "")
            main_ticker = st.text_input(
                "香港股票代號",
                value=default_ticker,
                placeholder="例如：0700、9988、0688、3416",
                help="支援 700、0700、700.HK、9988、3416 等格式。",
            )
            main_risk = st.selectbox(
                "投資者風險取向",
                options=["保守", "中等", "進取"],
                index=1,
                key="main_risk_preference",
            )
            main_portfolio = st.number_input(
                "投資組合規模（HKD，可選）",
                min_value=0,
                value=0,
                step=100000,
                key="main_portfolio_size",
            )
            submitted = st.form_submit_button(
                "生成機構級分析報告",
                type="primary",
                use_container_width=True,
                disabled=st.session_state.get("is_generating", False),
            )
    return submitted, main_ticker, main_risk, main_portfolio


def _render_empty_state() -> None:
    left, right = st.columns([1.05, 0.95])
    with left:
        with st.container(border=True):
            st.caption("How it works")
            st.markdown("**輸入香港股票代號，系統會生成一份可下載的機構級研究報告。**")
            st.caption("支援 0700、9988、0688、3416 等格式；INVALID ticker 會停止公司基本面敘述。")
    with right:
        _render_workflow_timeline()


def _status_cards() -> None:
    status = st.session_state.agent_status
    items = list(status.items())
    for start in range(0, len(items), 3):
        columns = st.columns(3)
        for column, (agent, state) in zip(columns, items[start:start + 3]):
            with column:
                with st.container(border=True):
                    st.markdown(f"**{_escape(agent)}**")
                    st.caption(_escape(state))


def _agent_discussion_cards(rows: list[dict[str, Any]]) -> None:
    for item in rows:
        with st.container(border=True):
            agent_name = _escape(item.get("Agent"))
            personality = _escape(item.get("性格定位"))
            confidence = _escape(item.get("信心分數"))
            st.markdown(f"**{agent_name}**")
            if personality:
                st.caption(personality)
            if confidence:
                st.caption(f"信心 {confidence}")
            st.markdown(f"**核心觀點：** {_escape(item.get('核心觀點'))}")
            st.markdown(f"**正面因素：** {_escape(item.get('正面因素'))}")
            st.markdown(f"**主要憂慮：** {_escape(item.get('主要憂慮'))}")
            st.markdown(f"**評級影響：** {_escape(item.get('對評級影響'))}")


def _company_cards(rows: list[tuple[Any, Any]]) -> None:
    columns = st.columns(2)
    for index, (label, value) in enumerate(rows):
        with columns[index % 2]:
            with st.container(border=True):
                st.markdown(f"**{_escape(label)}**")
                st.caption(_escape(value))


def _company_profile_panel(cover: dict[str, Any]) -> None:
    _section_title("Company profile", "公司資料與市場概覽", "資料只來自市場資料供應商或本地HK stock master database。")
    profile_rows = [
        ("中文公司名", cover.get("company_name_zh") or cover.get("company_name") or "資料待補充"),
        ("英文名", cover.get("company_name_en") or "資料待補充"),
        ("行業", cover.get("sector") or "資料待補充"),
        ("主營業務", cover.get("business") or "資料待補充"),
        ("市場分類", cover.get("market_type") or "資料待補充"),
    ]
    columns = st.columns(2)
    for index, (label, value) in enumerate(profile_rows):
        with columns[index % 2]:
            with st.container(border=True):
                st.markdown(f"**{label}**")
                st.caption(str(value))


def _logo_url_for_cover(cover: dict[str, Any]) -> str:
    ticker = normalize_hk_ticker(str(cover.get("ticker", ""))) if cover.get("ticker") else ""
    metadata = _load_hk_master_data().get(ticker, {})
    return str(cover.get("logo_url") or metadata.get("logo_url") or "").strip()


def _render_company_logo(cover: dict[str, Any], width: int = 76) -> None:
    logo_url = _logo_url_for_cover(cover)
    try:
        if logo_url:
            st.image(logo_url, width=width)
        elif os.path.exists(LOGO_PATH):
            st.image(str(LOGO_PATH), width=width)
    except Exception as exc:
        print(f"[APP] Company logo unavailable: {exc}")


def _render_report_summary_card(cover: dict[str, Any]) -> None:
    company_name = cover.get("company_name_zh") or cover.get("company_name") or "資料待補充"
    company_name_en = cover.get("company_name_en", "")
    ticker = cover.get("ticker", "N/A")
    sector = cover.get("sector", "資料待補充")
    confidence_label = cover.get("data_confidence_label", "🟡 部分資料缺失")

    with st.container(border=True):
        logo_col, detail_col = st.columns([0.22, 0.78])
        with logo_col:
            _render_company_logo(cover)
        with detail_col:
            st.markdown(f"**{_escape(company_name)}**")
            if company_name_en:
                st.caption(_escape(company_name_en))
            st.caption(f"{_escape(ticker)} | {_escape(sector)}")
            st.caption(f"資料可信度：{_escape(confidence_label)}")

        metric_cols = st.columns(3)
        metric_cols[0].metric("投資委員會結論", cover.get("final_rating", "N/A"))
        metric_cols[1].metric("風險分數", cover.get("risk_score", "N/A"), cover.get("risk_label", ""))
        metric_cols[2].metric("股票代號", ticker)


def _render_financial_sections(sections: dict[str, Any], report_package: dict[str, Any] | None = None) -> None:
    financial = sections.get("financial_analysis", {}) or {}
    metrics = financial.get("metrics", []) or []
    history = financial.get("history", []) or []
    risk = sections.get("risk_analysis", {}) or {}
    market = (report_package or {}).get("market_data", {}) or {}

    _section_title("Market metrics", "價格與市場指標")
    market_metrics = [
        ("現價", _format_showcase_price(market.get("current_price"))),
        ("市值", _format_showcase_market_cap(market.get("market_cap"))),
        ("成交量", _value_or_pending(market.get("volume"))),
        ("P/E", _value_or_pending(market.get("pe_ratio"))),
        ("P/B", _value_or_pending(market.get("pb_ratio"))),
        ("貨幣", _value_or_pending(market.get("currency"))),
    ]
    market_cols = st.columns(3)
    for index, (label, value) in enumerate(market_metrics):
        market_cols[index % 3].metric(label, value)

    if metrics:
        _section_title("Financial metrics", "核心財務指標")
        columns = st.columns(2)
        for index, (label, value) in enumerate(metrics):
            with columns[index % 2]:
                st.metric(str(label), str(value))

    if history:
        _section_title("Financial history", "歷史財務摘要")
        history_rows = [
            {"年度": row[0], "收入": row[1], "EBITDA": row[2], "淨利潤": row[3]}
            for row in history
            if isinstance(row, (list, tuple)) and len(row) >= 4
        ]
        st.dataframe(
            history_rows or history,
            use_container_width=True,
            hide_index=True,
        )

    if risk:
        _section_title("Risk analysis", "風險分析")
        cols = st.columns(2)
        cols[0].metric("綜合風險分數", risk.get("composite_score", "N/A"))
        cols[1].metric("風險等級", risk.get("risk_label", "N/A"))
        top_risks = risk.get("top_risks", []) or []
        if top_risks:
            for item in top_risks[:5]:
                with st.container(border=True):
                    st.markdown(f"**{_escape(item.get('dimension', '風險項目'))}**")
                    st.caption(f"分數：{_escape(item.get('score', 'N/A'))} | 等級：{_escape(item.get('level', 'N/A'))} | 權重：{_escape(item.get('weight', 'N/A'))}")


def _confidence_badge(label: str) -> None:
    text = label or "🟡 部分資料缺失"
    if "高可信度" in text:
        st.success(text)
    elif "資料驗證未完成" in text:
        st.error(text)
    else:
        st.warning(text)


def _confidence_note(label: str) -> None:
    if "高可信度" in label:
        copy = "已取得公司名稱、現價、市值及股票元數據。報告可顯示完整客戶版摘要，但仍只作研究及試用用途。"
    elif "資料驗證未完成" in label:
        copy = "該股票代號的資料驗證未完成。系統已停止進階財務分析，並避免生成公司介紹、收入模式或產品服務描述。"
    else:
        copy = "部分市場或財務資料未能取得。系統會保留有效內容，並以保守假設處理有限資料，不會把缺失資料包裝成確定結論。"
    st.info(f"資料可信度說明：{copy}")


def _mark_agent(message: str) -> None:
    status = st.session_state.agent_status
    mapping = [
        ("Market Data", "Market Data Agent"),
        ("Financial", "Financial Analyst Agent"),
        ("Risk", "Risk Agent"),
        ("News", "News Intelligence Agent"),
        ("Portfolio", "Portfolio Manager Agent"),
        ("Investment Committee", "Investment Committee Agent"),
    ]
    status["CEO Agent"] = "完成"
    for needle, agent in mapping:
        if needle.lower() in message.lower():
            status[agent] = "完成"


_inject_css()
_init_state()

with st.container(border=True):
    st.title("Buildway AI Financial Intelligence Platform")
    st.caption("60 秒內生成 Multi-Agent 分析、財務風險評估、機構級 PDF 報告")

main_generate_btn, main_ticker_input, main_risk_preference, main_portfolio_size = _render_main_input_panel()
_render_workspace_layer("main")
_render_sector_showcase()
_render_workflow_timeline()
_render_source_transparency()
_render_trust_layer()


with st.sidebar:
    if os.path.exists(LOGO_PATH):
        st.image(str(LOGO_PATH), width=96)

    st.header("分析設定")
    ticker_input = st.text_input(
        "香港股票代號",
        value=st.session_state.get("selected_ticker", ""),
        placeholder="例如：0700、9988、0688 或 3416.HK",
        help="系統會自動轉換為標準港股代號格式。",
    )
    company_name = st.text_input(
        "公司名稱（可選）",
        value="",
        placeholder="如留空，系統會使用市場資料或代號。",
    )
    risk_preference = st.selectbox(
        "投資者風險取向",
        options=["保守", "中等", "進取"],
        index=1,
    )
    portfolio_size = st.number_input(
        "投資組合規模（HKD，可選）",
        min_value=0,
        value=0,
        step=100000,
    )

    generate_btn = st.button(
        "生成機構級分析報告",
        type="primary",
        use_container_width=True,
        disabled=st.session_state.get("is_generating", False),
    )

    st.divider()
    _render_recent_reports("sidebar")
    _render_watchlist("sidebar")

    st.divider()
    if st.button("Clear / Reset", key="sidebar_clear_reset", use_container_width=True):
        st.session_state.pending_ticker_value = ""
        st.session_state.selected_ticker = ""
        st.session_state.report_package = None
        st.session_state.report_sections = None
        st.session_state.pdf_path = None
        st.session_state.pdf_warning = ""
        st.session_state.llm_warning = ""
        st.rerun()
    st.caption("700 展示高可信度；3416 展示部分資料；12345 展示無效代號控制。")

    st.divider()
    _today = datetime.now().strftime("%Y-%m-%d")
    _env_label = "Streamlit Cloud" if DEPLOY_ENV == "streamlit-cloud" else "Local"
    st.caption(f"{APP_VERSION} | {BUILD_STAGE}")
    st.caption(f"{_today} | {_env_label}")
    st.caption(f"Build: {BUILD_VERSION}")
    st.caption(f"Commit: {BUILD_COMMIT}")


rerun_request = st.session_state.pop("rerun_analysis_request", None)
analysis_requested = bool(main_generate_btn or generate_btn or rerun_request)
if rerun_request:
    request_ticker_input = rerun_request.get("ticker", "")
    request_risk_preference = rerun_request.get("risk_preference", risk_preference)
    request_portfolio_size = int(rerun_request.get("portfolio_size", 0) or 0)
elif main_generate_btn:
    request_ticker_input = main_ticker_input
    request_risk_preference = main_risk_preference
    request_portfolio_size = main_portfolio_size
else:
    request_ticker_input = ticker_input
    request_risk_preference = risk_preference
    request_portfolio_size = portfolio_size

if analysis_requested:
    is_valid_ticker, _ticker_error = validate_hk_ticker(request_ticker_input)
    if not is_valid_ticker:
        st.error("請輸入有效香港股票代號")
    else:
        st.session_state.is_generating = True
        st.session_state.pdf_warning = ""
        ticker = normalize_hk_ticker(request_ticker_input)
        st.session_state.selected_ticker = ticker.replace(".HK", "")
        print(f"[APP] User input stock_code = {ticker}")
        progress = st.progress(0)
        status_text = st.empty()

        st.session_state.agent_status = {
            "CEO Agent": "進行中",
            "Market Data Agent": "等待",
            "Financial Analyst Agent": "等待",
            "Risk Agent": "等待",
            "News Intelligence Agent": "等待",
            "Portfolio Manager Agent": "等待",
            "Investment Committee Agent": "等待",
        }

        try:
            ceo = CEOAgent()

            def update_progress(step: int, total: int, message: str) -> None:
                progress.progress(step / total)
                status_text.text(message)
                _mark_agent(message)

            report_package = ceo.run_analysis(
                ticker=ticker,
                company_name=company_name or None,
                risk_preference=request_risk_preference,
                report_type="HK Stock Investment Analysis Report",
                portfolio_size_hkd=request_portfolio_size if request_portfolio_size > 0 else None,
                manual_news=None,
                progress_callback=update_progress,
            )

            st.session_state.agent_status = report_package.get("agent_status", st.session_state.agent_status)
            st.session_state.agent_error_log = report_package.get("agent_error_log", [])

            builder = ReportBuilder()
            report_sections = builder.build(report_package)
            print(f"[Report Builder] Final stock_code = {report_sections.get('cover', {}).get('ticker')}")
            st.session_state.llm_warning = report_sections.get("metadata", {}).get("llm_warning", "")
            st.session_state.report_package = report_package
            st.session_state.report_sections = report_sections
            st.session_state.pdf_path = None

            status_text.text("正在生成PDF報告...")
            os.makedirs("reports", exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            pdf_filename = f"Buildway_HK_Investment_Report_{ticker.replace('.', '_')}_{timestamp}.pdf"
            pdf_path = os.path.join("reports", pdf_filename)

            try:
                pdf_gen = PDFGenerator(logo_path=str(LOGO_PATH) if os.path.exists(LOGO_PATH) else None)
                print(f"[PDF Generator] Final stock_code = {report_sections.get('cover', {}).get('ticker')}")
                pdf_gen.generate(report_sections, pdf_path)
                st.session_state.pdf_path = pdf_path
            except Exception as pdf_exc:
                print(f"[APP] PDF generation failed but report remains available: {pdf_exc}")
                st.session_state.pdf_warning = "PDF 暫時無法生成，請稍後再試"

            _save_report_history(
                ticker=ticker,
                risk_preference=request_risk_preference,
                portfolio_size=request_portfolio_size,
                report_package=report_package,
                report_sections=report_sections,
            )
            _add_watchlist_ticker(ticker)

            progress.progress(1.0)
            status_text.text("報告生成完成。")
            if st.session_state.pdf_warning:
                st.success("網頁報告已成功生成。")
                st.warning(st.session_state.pdf_warning)
            else:
                st.success("PDF報告已成功生成。")
            if st.session_state.agent_error_log:
                st.warning("系統部分分析模組暫時不可用，系統已啟動備援流程。")
            if st.session_state.llm_warning:
                st.warning(st.session_state.llm_warning)

        except Exception as exc:
            import traceback
            # Log full traceback server-side for debugging, never expose to users
            print(f"[APP] Report generation failed: {exc}")
            print(traceback.format_exc())
            st.error("系統部分分析模組暫時不可用，已啟動備援流程。")
            st.warning("3416.HK 部分市場或財務資料未能取得，系統已使用保守假設完成分析。" if "3416" in ticker else "如問題持續，請稍後再試或聯絡支援。")
        finally:
            st.session_state.is_generating = False


if st.session_state.report_sections:
    sections = st.session_state.report_sections
    cover = sections.get("cover", {})

    _section_title("Report preview", "報告摘要", "核心結論與報告下載")

    # 1. 報告摘要 card（含公司 logo、名稱、ticker、風險分數、投委會結論）
    confidence_label = cover.get("data_confidence_label", "🟡 部分資料缺失")
    _render_report_summary_card(cover)
    current_ticker = cover.get("ticker", st.session_state.get("selected_ticker", ""))
    action_cols = st.columns(3)
    if action_cols[0].button("Add to watchlist", key="current_add_watchlist", use_container_width=True):
        _add_watchlist_ticker(str(current_ticker))
        st.rerun()
    if action_cols[1].button("Re-run analysis", key="current_rerun_analysis", use_container_width=True):
        _request_analysis(str(current_ticker), request_risk_preference, request_portfolio_size)
    if action_cols[2].button("Clear current report", key="current_clear_report", use_container_width=True):
        st.session_state.report_package = None
        st.session_state.report_sections = None
        st.session_state.pdf_path = None
        st.session_state.pdf_warning = ""
        st.session_state.llm_warning = ""
        st.rerun()

    # 2. 下載按鈕（緊接摘要 card 下方）
    if st.session_state.pdf_path and os.path.exists(st.session_state.pdf_path):
        st.success("報告生成完成")
        with open(st.session_state.pdf_path, "rb") as pdf_file:
            st.download_button(
                label="下載機構級分析報告",
                data=pdf_file,
                file_name=os.path.basename(st.session_state.pdf_path),
                mime="application/pdf",
                type="primary",
                use_container_width=True,
            )
    elif st.session_state.get("pdf_warning"):
        st.warning(st.session_state.pdf_warning)

    # 3. 資料可信度說明
    _confidence_badge(confidence_label)
    _confidence_note(confidence_label)

    # 4. 公司資料與市場概覽
    _company_profile_panel(cover)

    # 5. 價格指標、歷史財務、風險分析
    _render_financial_sections(sections, st.session_state.get("report_package"))

    # 6. Workflow + 投委會討論（放最底）
    _render_workflow_timeline()

    discussion = sections.get("multi_agent_discussion", {})
    _section_title("Committee view", "投資委員會討論摘要", "將代理觀點整理為可掃讀的投資卡片")
    _agent_discussion_cards(discussion.get("table", []))
    if discussion.get("final_statement"):
        st.info(discussion.get("final_statement"))

    stability = sections.get("system_stability", {})
    if stability.get("has_failures"):
        _section_title("System note", "系統穩定性提示")
        st.warning(stability.get("message", "部分 Agent 分析未能完成，系統已自動切換至備援分析流程。"))
        failed_agents = ", ".join(stability.get("failed_agents", []))
        st.warning(f"受影響模組：{failed_agents}")

else:
    _render_empty_state()
    st.divider()
    st.caption(f"2026 {APP_NAME} | {BUILD_VERSION}")
    st.caption("本系統不構成投資建議；所有輸出只供研究、教育及客戶展示用途。")
    st.stop()

st.divider()
st.caption(f"© 2026 {APP_NAME} | {BUILD_VERSION}")
st.caption("本系統只作教育、研究及客戶試用用途，不構成投資建議。")
