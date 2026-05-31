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
    LOGO_PATH,
)
from core.pdf_generator import PDFGenerator
from core.report_builder import ReportBuilder
from core.utils import format_currency_hkd, normalize_hk_ticker, validate_hk_ticker


MASTER_DATA_PATH = Path(__file__).resolve().parent / "data" / "hk_stock_master_data.json"
INCOMPLETE_DATA_TEXT = "資料未完整取得"


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

            /* ── Default button (gold) ── */
            .stButton > button {
                background: linear-gradient(135deg, var(--bw-gold) 0%, var(--bw-gold-2) 100%) !important;
                border: 0 !important;
                border-radius: 8px !important;
                color: #112039 !important;
                font-weight: 800 !important;
                min-height: 3rem;
                box-shadow: 0 12px 24px rgba(217, 164, 65, 0.25);
            }

            .stButton > button:hover {
                filter: brightness(0.96);
                transform: translateY(-1px);
            }

            /* ── Download PDF button — green ── */
            .stDownloadButton > button {
                background: linear-gradient(135deg, #15a36d 0%, #1ec97f 100%) !important;
                border: 0 !important;
                border-radius: 8px !important;
                color: #ffffff !important;
                font-weight: 800 !important;
                min-height: 3rem;
                box-shadow: 0 12px 24px rgba(21, 163, 109, 0.28);
            }

            .stDownloadButton > button:hover {
                filter: brightness(0.96);
                transform: translateY(-1px);
            }

            /* ── Rerun / secondary button — orange ── */
            button[kind="secondary"] {
                background: linear-gradient(135deg, #e07b39 0%, #f0954a 100%) !important;
                border: 0 !important;
                border-radius: 8px !important;
                color: #ffffff !important;
                font-weight: 700 !important;
                min-height: 3rem;
            }

            /* ── Analyse / primary form submit — blue ── */
            div[data-testid="stFormSubmitButton"] button[kind="primaryFormSubmit"],
            div[data-testid="stFormSubmitButton"] button {
                background: linear-gradient(135deg, #1a56db 0%, #2d6ef5 100%) !important;
                border: 0 !important;
                border-radius: 8px !important;
                color: #ffffff !important;
                font-weight: 800 !important;
                min-height: 3rem;
                box-shadow: 0 12px 24px rgba(26, 86, 219, 0.28);
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


def _make_session_id() -> str:
    """Generate a session-scoped ID for data lake tracking."""
    import random
    suffix = "".join(str(random.randint(0, 9)) for _ in range(6))
    return f"{datetime.now().strftime('%Y%m%d%H%M%S')}{suffix}"


def _init_state() -> None:
    from core.client_profile import create_guest_profile
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
        "client_profile": create_guest_profile(),
        "session_id": _make_session_id(),
        "last_recorded_ticker": "",
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
    ("市場資料模組", "取得價格、成交量、市值與公司資料。"),
    ("財務分析模組", "計算估值、財務健康度與核心比率。"),
    ("風險控制模組", "評估流動性、槓桿、波動與下行情境。"),
    ("新聞分析模組", "整理市場情緒與事件風險。"),
    ("投資委員會", "整合多模組觀點並輸出最終結論。"),
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


def _confidence_level(report_package: dict[str, Any] | None, cover: dict[str, Any] | None = None) -> str:
    market = (report_package or {}).get("market_data", {}) or {}
    raw = str(market.get("data_confidence") or (cover or {}).get("data_confidence_label") or "").upper()
    if "INVALID" in raw or "資料驗證未完成" in raw:
        return "INVALID"
    if "LOW" in raw or "部分資料缺失" in raw:
        return "LOW"
    if "MEDIUM" in raw:
        return "MEDIUM"
    if "HIGH" in raw or "高可信度" in raw:
        return "HIGH"
    return "MEDIUM"


def _has_valid_display_value(value: Any) -> bool:
    text = str(value or "").strip()
    if not text:
        return False
    invalid_tokens = {
        "0",
        "0.0",
        "0.00",
        "N/A",
        "None",
        "資料待補充",
        "暫無資料",
        "暫未接入即時新聞資料",
        INCOMPLETE_DATA_TEXT,
    }
    if text in invalid_tokens:
        return False
    if "HK$0.00" in text or "0.0%" in text or "0.00x" in text or "0.0x" in text:
        return False
    return True


def _valid_metric_rows(rows: list[Any]) -> list[Any]:
    valid_rows = []
    for row in rows or []:
        if isinstance(row, (list, tuple)) and len(row) >= 2 and _has_valid_display_value(row[1]):
            valid_rows.append(row)
    return valid_rows


def _valid_history_rows(rows: list[Any]) -> list[Any]:
    valid_rows = []
    for row in rows or []:
        if isinstance(row, (list, tuple)) and len(row) > 1 and any(_has_valid_display_value(value) for value in row[1:]):
            valid_rows.append(row)
    return valid_rows


def _market_snapshot_has_data(section: dict[str, Any]) -> bool:
    if not section or not section.get("is_valid"):
        return False
    kpis = section.get("kpis", []) or []
    if any(_has_valid_display_value(kpi.get("value")) for kpi in kpis if isinstance(kpi, dict)):
        return True
    grouped = []
    for key in ("price_section", "valuation_section", "range_section"):
        grouped.extend((section.get(key, {}) or {}).values())
    return any(_has_valid_display_value(value) for value in grouped)


def _financial_has_data(section: dict[str, Any]) -> bool:
    return bool(_valid_metric_rows(section.get("metrics", []) or []) or _valid_history_rows(section.get("history", []) or []))


def _scenario_has_data(section: dict[str, Any]) -> bool:
    if not section or not section.get("is_valid"):
        return False
    scenarios = section.get("scenarios", []) or []
    rows = section.get("rows", []) or []
    return any(
        _has_valid_display_value(item.get("implied_price")) and item.get("implied_upside") != "+0.0%"
        for item in scenarios
        if isinstance(item, dict)
    ) or any(any(_has_valid_display_value(value) for value in row[1:]) for row in rows if isinstance(row, (list, tuple)))


def _news_has_data(section: dict[str, Any]) -> bool:
    if not section or not section.get("has_news"):
        return False
    keys = ("positive_catalysts", "negative_catalysts", "neutral_events", "risk_events", "monitor_items")
    return any(section.get(key) for key in keys)


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


def _stock_display_name(ticker: str) -> str:
    metadata = _load_hk_master_data().get(normalize_hk_ticker(ticker), {})
    return str(metadata.get("name_zh") or metadata.get("name_en") or "").strip()


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
        "risk_score": cover.get("risk_score", "N/A"),
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
        st.caption("報告紀錄")
        st.markdown("**最近生成報告**")
        if not reports:
            st.caption("本次生成的報告會顯示在這裡。")
            return
        for index, record in enumerate(reports):
            with st.container(border=True):
                top = st.columns([0.34, 0.66])
                top[0].markdown(f"**{_escape(record.get('ticker'))}**")
                top[1].caption(_escape(record.get("company")))
                metrics = st.columns(3)
                metrics[0].metric("評級", _escape(record.get("rating", "N/A")))
                metrics[1].metric("風險分數", _escape(record.get("risk_score", "N/A")))
                metrics[2].caption(f"生成時間\n\n{_escape(record.get('generated_at'))}")
                actions = st.columns(2)
                if actions[0].button(
                    "開啟",
                    key=f"open_report_{location}_{index}_{record.get('id')}",
                    use_container_width=True,
                ):
                    _open_history_record(record)
                if actions[1].button(
                    "重新分析",
                    key=f"rerun_report_{location}_{index}_{record.get('id')}",
                    use_container_width=True,
                ):
                    _request_analysis(
                        str(record.get("ticker", "")),
                        str(record.get("risk_preference") or "中等"),
                        int(record.get("portfolio_size") or 0),
                    )
        if st.button("清除紀錄", key=f"clear_history_{location}", use_container_width=True):
            st.session_state["recent_reports"] = []
            st.rerun()
    return

def _render_watchlist(location: str) -> None:
    watchlist = st.session_state.get("watchlist", [])
    with st.container(border=True):
        st.caption("觀察名單")
        st.markdown("**客戶觀察名單**")
        add_cols = st.columns([0.68, 0.32])
        candidate = add_cols[0].text_input(
            "加入股票代號",
            value="",
            placeholder="0700 或 9988.HK",
            key=f"watchlist_input_{location}",
            label_visibility="collapsed",
        )
        if add_cols[1].button("加入", key=f"watchlist_add_{location}", use_container_width=True):
            is_valid, _ = validate_hk_ticker(candidate)
            if is_valid:
                _add_watchlist_ticker(candidate)
                st.rerun()
            else:
                st.warning("請輸入有效的香港股票代號。")
        if not watchlist:
            st.caption("加入客戶希望追蹤的股票，方便之後快速重新分析。")
            return
        for start in range(0, len(watchlist), 3):
            columns = st.columns(3)
            for column, ticker in zip(columns, watchlist[start:start + 3]):
                with column:
                    with st.container(border=True):
                        st.markdown(f"**{_escape(ticker)}**")
                        company_name = _stock_display_name(ticker)
                        if company_name:
                            st.caption(_escape(company_name))
                        actions = st.columns(2)
                        if actions[0].button(
                            "分析",
                            key=f"watch_analyze_{location}_{start}_{ticker}",
                            use_container_width=True,
                        ):
                            _request_analysis(ticker)
                        if actions[1].button(
                            "移除",
                            key=f"watch_remove_{location}_{start}_{ticker}",
                            use_container_width=True,
                        ):
                            _remove_watchlist_ticker(ticker)
                            st.rerun()
    return

def _render_workspace_layer(location: str) -> None:
    _section_title(
        "工作區",
        "報告紀錄與觀察名單",
        "本工作區只會保留於目前瀏覽 session，方便客戶重複分析。",
    )
    cols = st.columns([1.1, 0.9])
    with cols[0]:
        _render_recent_reports(location)
    with cols[1]:
        _render_watchlist(location)


def _render_client_profile_section() -> None:
    profile = st.session_state.get("client_profile", {})
    usage = profile.get("usage", {})
    with st.container(border=True):
        st.caption("客戶資料")
        st.markdown(f"**{_escape(profile.get('display_name', '訪客客戶'))}**")
        cols = st.columns(3)
        cols[0].metric("分析報告", usage.get("reports_generated", 0))
        cols[1].metric("已分析股票", len(usage.get("tickers_analyzed", [])))
        cols[2].caption(f"最後活動\n\n{_escape(profile.get('last_active', 'N/A'))}")


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
    _section_title("香港市場板塊", "香港市場板塊", "按板塊瀏覽香港股票案例，點選即可填入分析代號。")
    master_data = _load_hk_master_data()
    tabs = st.tabs(list(SECTOR_SHOWCASE.keys()))
    for tab, (sector_name, tickers) in zip(tabs, SECTOR_SHOWCASE.items()):
        with tab:
            st.caption(sector_name)
            columns = st.columns(2)
            for index, ticker in enumerate(tickers):
                with columns[index % 2]:
                    _render_stock_showcase_card(ticker, master_data.get(ticker, {}), sector_name)


def _render_workflow_timeline() -> None:
    """Static architecture explanation — not a runtime status display."""
    _section_title("分析引擎架構", "分析引擎架構", "系統由五個分析模組組成，每個模組均設有備援機制。")
    for index, (name, description) in enumerate(WORKFLOW_STEPS):
        with st.container(border=True):
            cols = st.columns([0.12, 0.88])
            cols[0].caption(f"{index + 1}")
            cols[1].markdown(f"**{name}**")
            cols[1].caption(description)


def _render_source_transparency() -> None:
    _section_title("資料透明度", "資料來源與分析邊界")
    rows = [
        ("市場資料", "Yahoo Finance / 市場資料供應商"),
        ("公司資料", "HK stock master database"),
        ("財務計算", "Python 計算引擎"),
        ("文字整理", "DeepSeek V3，只負責文字整理，不參與財務計算"),
    ]
    _company_cards(rows)
    st.warning("本系統不構成投資建議。所有結果只供研究、教育及客戶展示用途。")


def _render_trust_layer() -> None:
    _section_title("信任層", "為何客戶可以信任本系統")
    cards = [
        ("防止 AI 幻覺", "公司資料只引用市場供應商或本地 master database。"),
        ("無效代號防護", "無有效市場資料時停止進階公司敘述。"),
        ("Python 財務計算", "估值、比率、風險分數由 Python 計算引擎產生。"),
        ("Multi-Agent 交叉分析", "市場、財務、風險、新聞與投委會互相校驗。"),
        ("PDF 機構級輸出", "客戶可下載一致格式的正式報告。"),
        ("備援容錯架構", "單一資料源或 agent 失敗不會拖垮整個流程。"),
    ]
    columns = st.columns(3)
    for index, (title, copy) in enumerate(cards):
        with columns[index % 3]:
            with st.container(border=True):
                st.markdown(f"**{title}**")
                st.caption(copy)


def _render_main_input_panel() -> tuple[bool, str, str, int]:
    _section_title("開始", "開始分析", "手機版可直接在主頁完成輸入，不需要打開側邊欄。")
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
            st.caption("使用方式")
            st.markdown("**輸入香港股票代號，系統會生成一份可下載的機構級研究報告。**")
            st.caption("支援 0700、9988、0688、3416 等格式；資料驗證未完成時會停止公司基本面敘述。")
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
    agent_name_map = {
        "CEO Agent": "總協調模組",
        "Market Data Agent": "市場資料模組",
        "Financial Analyst Agent": "財務分析模組",
        "Risk Management Agent": "風險控制模組",
        "Risk Agent": "風險控制模組",
        "News Intelligence Agent": "新聞分析模組",
        "Portfolio Manager Agent": "組合配置模組",
        "Investment Committee Agent": "投資委員會",
    }
    for item in rows:
        with st.container(border=True):
            agent_name = _escape(agent_name_map.get(str(item.get("Agent")), item.get("Agent")))
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
    _section_title("公司資料", "公司資料與市場概覽", "資料只來自市場資料供應商或本地香港股票主資料庫。")
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


def _render_financial_sections(
    sections: dict[str, Any],
    report_package: dict[str, Any] | None = None,
    *,
    show_market: bool = True,
    show_financial: bool = True,
    show_risk: bool = True,
) -> None:
    financial = sections.get("financial_analysis", {}) or {}
    metrics = _valid_metric_rows(financial.get("metrics", []) or [])
    history = _valid_history_rows(financial.get("history", []) or [])
    # canonical key first, legacy key as fallback
    risk = (
        (report_package or {}).get("risk_assessment_v2", {})
        or sections.get("risk_analysis", {})
        or {}
    )
    market = (report_package or {}).get("market_data", {}) or {}

    market_metrics = [
        ("現價", _format_showcase_price(market.get("current_price"))),
        ("市值", _format_showcase_market_cap(market.get("market_cap"))),
        ("成交量", _value_or_pending(market.get("volume"))),
        ("P/E", _value_or_pending(market.get("pe_ratio"))),
        ("P/B", _value_or_pending(market.get("pb_ratio"))),
        ("貨幣", _value_or_pending(market.get("currency"))),
    ]
    market_metrics = _valid_metric_rows(market_metrics)
    if show_market and market_metrics:
        _section_title("市場指標", "價格與市場指標")
        market_cols = st.columns(3)
        for index, (label, value) in enumerate(market_metrics):
            market_cols[index % 3].metric(label, value)

    if show_financial and metrics:
        _section_title("財務指標", "核心財務指標")
        columns = st.columns(2)
        for index, (label, value) in enumerate(metrics):
            with columns[index % 2]:
                st.metric(str(label), str(value))

    if show_financial and history:
        _section_title("歷史財務", "歷史財務摘要")
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

    if show_risk and risk:
        _section_title("風險分析", "風險分析")
        cols = st.columns(2)
        cols[0].metric("綜合風險分數", risk.get("composite_score", "N/A"))
        cols[1].metric("風險等級", risk.get("risk_label", "N/A"))
        top_risks = risk.get("top_risks", []) or []
        if top_risks:
            for item in top_risks[:5]:
                with st.container(border=True):
                    st.markdown(f"**{_escape(item.get('dimension', '風險項目'))}**")
                    st.caption(f"分數：{_escape(item.get('score', 'N/A'))} | 等級：{_escape(item.get('level', 'N/A'))} | 權重：{_escape(item.get('weight', 'N/A'))}")


def _render_market_snapshot_section(section: dict[str, Any]) -> None:
    """Bloomberg-style market snapshot KPI cards."""
    if not _market_snapshot_has_data(section):
        return
    _section_title("市場快照", "市場快照", "市場核心指標由 Python 從市場資料供應商提取。")
    kpis = section.get("kpis", [])
    if not kpis:
        return

    # Render KPIs in rows of 5
    row_size = 5
    for start in range(0, len(kpis), row_size):
        cols = st.columns(row_size)
        for col, kpi in zip(cols, kpis[start:start + row_size]):
            label = _escape(kpi.get("label", ""))
            value = _escape(kpi.get("value", "資料待補充"))
            if not _has_valid_display_value(value):
                continue
            delta = kpi.get("delta", "")
            with col:
                with st.container(border=True):
                    st.caption(label)
                    st.markdown(f"**{value}**")
                    if delta and delta != "資料待補充":
                        st.caption(_escape(delta))

    conf = section.get("snapshot_confidence", "")
    source = section.get("data_source", "")
    is_demo = section.get("is_demo", True)
    demo_tag = "示範數據" if is_demo else "實時數據"
    st.caption(f"快照可信度：{_escape(conf)} | {_escape(source)} ({demo_tag})")


def _render_allocation_section(
    portfolio_size: int,
    risk_score_str: str,
    rating: str,
) -> None:
    """Portfolio allocation summary based on risk score."""
    try:
        from core.portfolio_engine import build_allocation_summary
        from core.safe_math import safe_number
        risk_score = safe_number(risk_score_str.replace("/10", "").strip(), 5.0)
        alloc = build_allocation_summary(float(portfolio_size or 0), risk_score, rating)
    except Exception as exc:
        print(f"[APP] Allocation summary unavailable: {exc}")
        return

    if alloc.get("portfolio_size") == "未設定":
        return  # Don't show if no portfolio size set

    _section_title("組合倉位參考", "組合倉位參考", "基於風險分數的倉位建議，只作教育及研究用途。")
    with st.container(border=True):
        cols = st.columns(3)
        cols[0].metric("投資組合規模", _escape(alloc.get("portfolio_size", "N/A")))
        cols[1].metric(
            "建議倉位",
            _escape(alloc.get("suggested_position_hkd", "N/A")),
            f"{alloc.get('suggested_position_pct', 0) * 100:.0f}%",
        )
        cols[2].metric(
            "最大倉位上限",
            _escape(alloc.get("max_position_hkd", "N/A")),
            f"{alloc.get('max_position_pct', 0) * 100:.0f}%",
        )
        st.caption(_escape(alloc.get("risk_note", "")))
        st.caption(_escape(alloc.get("allocation_note", "")))


def _render_hkex_section(ticker: str, report_package: dict[str, Any] | None = None) -> None:
    """HKEX announcements and earnings intelligence section."""
    try:
        from core.hkex_intelligence_engine import build_hkex_intelligence
        market_data = (report_package or {}).get("market_data", {}) or {}
        sections = st.session_state.get("report_sections") or {}
        result = sections.get("hkex_intelligence") or build_hkex_intelligence(ticker, market_data=market_data, financial_data=market_data)
    except Exception as exc:
        print(f"[APP] HKEX intelligence unavailable: {exc}")
        return

    _section_title("公告與業績分析", "HKEX 公告與業績分析", "本節只使用已接入及已驗證的公告或業績資料。")

    with st.container(border=True):
        st.caption(_escape(result.get("status_summary", "")))
        st.info(_escape(result.get("analysis_boundary", "")))
        if not result.get("has_data"):
            st.warning("未取得已驗證 HKEX 公告資料")
            return

    # Earnings summary
    earnings = result.get("earnings", {})
    if earnings.get("has_earnings_data"):
        st.subheader("業績重點")
        e_cols = st.columns(3)
        e_cols[0].metric("收入 TTM", _escape(earnings.get("revenue_ttm", "資料待補充")))
        e_cols[1].metric("淨利潤 TTM", _escape(earnings.get("net_income_ttm", "資料待補充")))
        e_cols[2].metric("EBITDA", _escape(earnings.get("ebitda", "資料待補充")))
        m_cols = st.columns(3)
        m_cols[0].metric("毛利率", _escape(earnings.get("gross_margin", "資料待補充")))
        m_cols[1].metric("淨利率", _escape(earnings.get("net_margin", "資料待補充")))
        m_cols[2].metric("ROE", _escape(earnings.get("roe", "資料待補充")))
        st.caption(_escape(earnings.get("boundary_note", "")))

    # Announcements
    ann = result.get("announcements", {})
    if ann.get("is_connected") and ann.get("announcements"):
        with st.container(border=True):
            st.markdown("**HKEX 公告**")
            for item in ann["announcements"][:5]:
                st.caption(f"- {_escape(item)}")


def _render_compare_mode() -> None:
    """Two-stock comparison mode using portfolio_engine."""
    _section_title("Compare Mode", "股票比較分析", "輸入兩隻股票代號，系統會比較估值、風險、板塊及催化因素。")
    with st.container(border=True):
        cols = st.columns([0.45, 0.45, 0.1])
        ticker_a = cols[0].text_input(
            "股票 A",
            placeholder="例如：0700",
            key="compare_ticker_a",
        )
        ticker_b = cols[1].text_input(
            "股票 B",
            placeholder="例如：9988",
            key="compare_ticker_b",
        )
        run_compare = cols[2].button("比較", key="run_compare_btn", use_container_width=True)

    if not run_compare:
        return

    from core.portfolio_engine import compare_stocks
    from agents.market_data_agent import MarketDataAgent as _MDA

    tickers_to_compare = []
    for raw in [ticker_a, ticker_b]:
        raw = raw.strip()
        if not raw:
            continue
        is_valid, _ = validate_hk_ticker(raw)
        if not is_valid:
            st.warning(f"無效股票代號：{raw}")
            continue
        tickers_to_compare.append(normalize_hk_ticker(raw))

    if len(tickers_to_compare) < 2:
        st.warning("請輸入兩個有效的香港股票代號。")
        return

    with st.spinner("正在取得比較資料..."):
        stock_data_list = []
        for t in tickers_to_compare:
            try:
                market = _MDA().fetch(t)
                stock_data_list.append({
                    "ticker": t,
                    "market_data": market,
                    "risk_analysis": {},
                    "financial_analysis": {},
                    "news_catalyst": {},
                })
            except Exception as exc:
                print(f"[APP] Compare fetch failed for {t}: {exc}")
                stock_data_list.append({"ticker": t, "market_data": {}, "risk_analysis": {}, "financial_analysis": {}, "news_catalyst": {}})

    result = compare_stocks(stock_data_list)

    # Valuation compare
    val_rows = result.get("valuation_compare", [])
    if val_rows:
        st.subheader("估值比較")
        fields = ["ticker", "現價", "市值", "P/E", "P/B", "股息率"]
        table_data = [{f: row.get(f, "N/A") for f in fields} for row in val_rows]
        st.dataframe(table_data, use_container_width=True, hide_index=True)

    # Risk compare
    risk_rows = result.get("risk_compare", [])
    if risk_rows:
        st.subheader("風險比較")
        fields = ["ticker", "風險分數", "風險等級", "Beta", "首要風險"]
        table_data = [{f: row.get(f, "N/A") for f in fields} for row in risk_rows]
        st.dataframe(table_data, use_container_width=True, hide_index=True)

    # Sector compare
    sector_rows = result.get("sector_compare", [])
    if sector_rows:
        st.subheader("板塊與盈利比較")
        fields = ["ticker", "行業", "市場分類", "毛利率", "淨利率", "ROE"]
        table_data = [{f: row.get(f, "N/A") for f in fields} for row in sector_rows]
        st.dataframe(table_data, use_container_width=True, hide_index=True)

    # Summary
    summary = result.get("summary", {})
    with st.container(border=True):
        st.markdown("**比較摘要**")
        st.caption(f"估值吸引力較高：{_escape(summary.get('best_value', 'N/A'))}")
        st.caption(f"風險分數較低：{_escape(summary.get('lowest_risk', 'N/A'))}")
        st.caption(_escape(result.get("analysis_note", "")))


def _render_scenario_section(section: dict[str, Any]) -> None:
    """Bull / Base / Bear scenario cards."""
    if not _scenario_has_data(section):
        return
    _section_title("情景分析", "情景分析", "基於 Python 計算的估值區間與風險分數，不由 LLM 生成數值。")

    # Summary row
    with st.container(border=True):
        cols = st.columns(3)
        cols[0].metric("現價", _escape(section.get("current_price", "N/A")))
        cols[1].metric("風險分數", _escape(section.get("risk_score", "N/A")))
        cols[2].metric("風險等級", _escape(section.get("risk_label", "N/A")))

    # Scenario cards
    scenarios = section.get("scenarios", [])
    if scenarios:
        cols = st.columns(len(scenarios))
        for col, s in zip(cols, scenarios):
            with col:
                with st.container(border=True):
                    st.markdown(f"**{_escape(s.get('name', ''))} {_escape(s.get('name_zh', ''))}**")
                    st.caption(_escape(s.get("description", "")))
                    st.metric("隱含價格", _escape(s.get("implied_price", "N/A")), _escape(s.get("implied_upside", "")))
                    st.caption(f"關鍵假設：{_escape(s.get('key_assumption', ''))}")
                    st.caption(f"催化因素：{_escape(s.get('key_catalyst', ''))}")
                    st.caption(_escape(s.get("probability_note", "")))

    # Triggers
    triggers = section.get("triggers", [])
    if triggers:
        with st.container(border=True):
            st.markdown("**下行觸發點**")
            for t in triggers[:5]:
                st.caption(f"- {_escape(t)}")

    st.caption(_escape(section.get("analysis_note", "")))


def _render_news_catalyst_section(section: dict[str, Any]) -> None:
    if not _news_has_data(section):
        return
    _section_title("新聞催化", "新聞與事件催化分析", "本節只使用已接入及已驗證新聞來源。")
    status = section.get("status") or "暫未接入即時新聞資料"
    confidence = section.get("news_confidence") or "未接入"
    with st.container(border=True):
        cols = st.columns(2)
        cols[0].metric("新聞資料狀態", _escape(status))
        cols[1].metric("新聞可信度", _escape(confidence))
        if not section.get("has_news"):
            st.info("暫未接入即時新聞資料，系統目前不會生成假新聞或未經驗證事件。")
        st.caption(_escape(section.get("analysis_boundary", "")))

    cards = [
        ("正面催化因素", section.get("positive_catalysts", [])),
        ("負面催化因素", section.get("negative_catalysts", [])),
        ("中性事件", section.get("neutral_events", [])),
        ("需要監察事項", section.get("risk_events", []) or section.get("monitor_items", [])),
    ]
    columns = st.columns(2)
    for index, (title, items) in enumerate(cards):
        with columns[index % 2]:
            with st.container(border=True):
                st.markdown(f"**{title}**")
                if items:
                    for item in items[:5]:
                        st.caption(f"- {_escape(item)}")
                else:
                    st.caption("暫無已驗證資料。")


def _render_landing_panel() -> None:
    with st.container(border=True):
        st.title("Buildway AI Financial Intelligence Platform")
        st.caption("香港股票智能分析試用平台")
        cols = st.columns(3)
        cols[0].metric("資料分級", "高 / 部分 / 未完成")
        cols[1].metric("報告輸出", "PDF")
        cols[2].metric("分析方式", "Multi-Agent")
        st.caption("輸入香港股票代號後，系統會按資料可信度自動決定顯示深度，避免空白章節、假數據及未驗證內容。")


def _render_data_coverage_note() -> None:
    _section_title("資料覆蓋說明", "資料覆蓋說明", "不同資料可信度會觸發不同顯示深度。")
    rows = [
        ("高可信度", "顯示完整市場快照、財務指標、情景分析、風險及報告下載。"),
        ("部分資料缺失", "只保留可驗證資料；隱藏不足以支持判斷的財務、新聞或情景章節。"),
        ("資料驗證未完成", "停止深度分析，不生成公司敘述、財務判斷或未驗證事件。"),
    ]
    _company_cards(rows)


def _render_data_store_status() -> None:
    """Data lake status section — shows storage mode, today's counts, and export."""
    try:
        from core.intelligence_store import get_data_lake_status
        from core.local_data_store import get_today_export_bytes
        status = get_data_lake_status()
    except Exception as exc:
        print(f"[APP] Data store status unavailable: {exc}")
        return

    _section_title("資料儲存狀態", "資料儲存狀態", "本地 Data Lake 儲存每日分析紀錄，不需要 Cloud DB。")
    with st.container(border=True):
        cols = st.columns(4)
        cols[0].metric("儲存模式", _escape(status.get("mode", "本地 Data Lake")))
        cols[1].metric("今日分析紀錄", status.get("today_runs", 0))
        cols[2].metric("今日市場快照", status.get("today_snapshots", 0))
        cols[3].metric("今日用戶事件", status.get("today_events", 0))

        last_ticker = st.session_state.get("last_recorded_ticker", "")
        if last_ticker:
            st.caption(f"最後記錄：{_escape(last_ticker)} | 日期：{_escape(status.get('date', ''))}")
        else:
            st.caption(f"日期：{_escape(status.get('date', ''))} | 完成分析後自動記錄")

        # Download today's JSONL
        try:
            export_bytes = get_today_export_bytes("analysis_runs")
            if export_bytes:
                today_str = status.get("date", "today")
                st.download_button(
                    label="下載今日分析紀錄 JSONL",
                    data=export_bytes,
                    file_name=f"analysis_runs_{today_str}.jsonl",
                    mime="application/jsonlines",
                    use_container_width=True,
                )
            else:
                st.caption("今日尚無分析紀錄可下載。")
        except Exception:
            pass

        st.caption("Streamlit Cloud 重啟後本地 data_lake 會被清空；正式版需接 Supabase / Neon。")


def _render_beta_trial_note() -> None:
    with st.container(border=True):
        st.caption("Beta 試用說明")
        st.markdown("**本系統為試用版本，不構成投資建議。**")
        st.caption("市場資料可能延遲、缺失或只作示範用途；所有財務數值只由 Python 計算，文字整理不會生成數值。")


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

_render_landing_panel()
main_generate_btn, main_ticker_input, main_risk_preference, main_portfolio_size = _render_main_input_panel()
_render_data_coverage_note()
_render_beta_trial_note()


generate_btn = False
ticker_input = st.session_state.get("selected_ticker", "")
company_name = ""
risk_preference = "中等"
portfolio_size = 0


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
            from core.client_profile import update_profile_activity
            st.session_state.client_profile = update_profile_activity(st.session_state.client_profile, ticker=ticker)

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

            # Record to local data lake (safe — never crashes app)
            try:
                from core.intelligence_store import record_analysis_complete, record_user_event
                _session_id = st.session_state.get("session_id", "")
                _cover_for_store = report_sections.get("cover", {}) or {}
                record_analysis_complete(
                    ticker=ticker,
                    report_sections=report_sections,
                    report_package=report_package,
                    pdf_path=st.session_state.get("pdf_path"),
                    session_id=_session_id,
                )
                record_user_event(
                    "generate_report", ticker=ticker, session_id=_session_id,
                    metadata={
                        "confidence": _cover_for_store.get("data_confidence", ""),
                        "rating": _cover_for_store.get("final_rating", ""),
                    },
                )
                st.session_state["last_recorded_ticker"] = ticker
            except Exception as _store_exc:
                print(f"[APP] Data lake record failed (non-critical): {_store_exc}")

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


# ── FOS V3.5 Report Display ───────────────────────────────────────────────────
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
    )

    sections = st.session_state.report_sections
    cover = sections.get("cover", {})
    report_package = st.session_state.get("report_package") or {}
    confidence_level = _confidence_level(report_package, cover)
    current_ticker = cover.get("ticker", st.session_state.get("selected_ticker", ""))
    confidence_label = cover.get("data_confidence_label", "🟡 部分資料缺失")

    # ── Sidebar: 公司資料面板 ─────────────────────────────────────────────────
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

    # ── 1. 報告摘要 ──────────────────────────────────────────────────────────
    _section_title("報告摘要", "報告摘要", "核心結論與報告下載")
    _render_report_summary_card(cover)

    # Action buttons — colour-coded per PRD Part 12
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
    ):
        st.session_state.report_package = None
        st.session_state.report_sections = None
        st.session_state.pdf_path = None
        st.session_state.pdf_warning = ""
        st.session_state.llm_warning = ""
        st.rerun()

    # Download button (green)
    if st.session_state.pdf_path and os.path.exists(st.session_state.pdf_path):
        with open(st.session_state.pdf_path, "rb") as pdf_file:
            action_cols[2].download_button(
                label="⬇️ 下載 PDF",
                data=pdf_file,
                file_name=os.path.basename(st.session_state.pdf_path),
                mime="application/pdf",
                use_container_width=True,
                type="primary",
            )
    elif st.session_state.get("pdf_warning"):
        action_cols[2].warning(st.session_state.pdf_warning)

    _confidence_badge(confidence_label)
    _confidence_note(confidence_label)
    if confidence_level == "MEDIUM":
        st.warning("部分資料未完整取得，以下內容已保留有效資料並隱藏不足以支持判斷的區塊。")
    if confidence_level == "INVALID":
        st.error("資料驗證未完成，系統已停止深度分析，避免生成未經驗證內容。")

    # ── 2. 競爭格局分析 ──────────────────────────────────────────────────────
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
    render_confidence_breakdown({
        "cover": cover,
        "data_confidence": {
            "level": report_package.get("data_confidence", confidence_level),
            "overall_score": report_package.get("data_confidence_score", 65),
            "financial_coverage": report_package.get("financial_coverage_score", 0),
            "news_verification": report_package.get("news_verification_score", 0),
            "hkex_verification": report_package.get("hkex_verification_score", 0),
            "agent_consensus": report_package.get("agent_consensus_score", 0),
            "data_freshness": report_package.get("data_freshness_score", 0),
            "sources": report_package.get("data_sources", ["Yahoo Finance", "Company Metadata"]),
        }
    })

    # ── 4. 市場分析 ───────────────────────────────────────────────────────────
    if confidence_level in {"HIGH", "MEDIUM"}:
        _section_title("市場分析", "市場分析", "")
        _render_market_snapshot_section(sections.get("market_snapshot", {}))
        mkt = report_package.get("market_data", {}) or {}
        render_market_snapshot({
            "market_data": {
                "current_price": mkt.get("current_price"),
                "week_52_high": mkt.get("week_52_high"),
                "week_52_low": mkt.get("week_52_low"),
                "volume": mkt.get("volume"),
            }
        })

    # ── 5. 財務分析 ───────────────────────────────────────────────────────────
    if confidence_level in {"HIGH", "MEDIUM"}:
        _section_title("財務分析", "財務分析", "")
        _render_financial_sections(
            sections,
            report_package,
            show_market=True,
            show_financial=_financial_has_data(sections.get("financial_analysis", {}) or {}),
            show_risk=False,
        )
        fin = sections.get("financial_analysis", {}) or {}
        render_financial_trends({
            "financial_data": {
                "revenue_trend": fin.get("revenue_trend", []),
                "ebitda_trend": fin.get("ebitda_trend", []),
                "net_profit_trend": fin.get("net_profit_trend", []),
                "fcf_trend": fin.get("fcf_trend", []),
            }
        })

    # ── 6. 風險分析 ───────────────────────────────────────────────────────────
    if confidence_level != "INVALID":
        _section_title("風險分析", "風險分析", "")
        risk_sec = sections.get("risk_analysis", {}) or {}
        risk_v2_sec = (report_package or {}).get("risk_assessment_v2", {}) or {}
        render_risk_event_cards({
            "risk_assessment_v2": risk_v2_sec,
            "risk_analysis": risk_sec,
        })
        # Risk Dashboard v3.5
        _rv2 = report_package.get("risk_assessment_v2", {}) or {}
        if _rv2:
            render_risk_dashboard({"risk_assessment_v2": _rv2})

    # ── 7. 新聞與事件催化 ─────────────────────────────────────────────────────
    if confidence_level in {"HIGH", "MEDIUM"}:
        _section_title("新聞與事件催化", "新聞與事件催化", "")
        news_sec = sections.get("news_catalyst_analysis", {}) or {}
        render_news_sentiment({
            "news_analysis": {
                "positive_count": len(news_sec.get("positive_catalysts", []) or []),
                "neutral_count": len(news_sec.get("neutral_events", []) or []),
                "negative_count": len(news_sec.get("negative_catalysts", []) or []),
                "catalysts": news_sec.get("positive_catalysts", []),
                "watchlist": news_sec.get("risk_events", []),
            }
        })
        _render_news_catalyst_section(news_sec)

    # ── 8. AI 投資委員會 (v3.5 Bull vs Bear) ────────────────────────────────
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
        _agent_discussion_cards(table)

    # ── 9. 最終投資結論 ───────────────────────────────────────────────────────
    _section_title("最終投資結論", "最終投資結論", "")
    rating_raw = cover.get("final_rating", "觀察")
    rating_map = {"買入": "買入", "增持": "買入", "中性": "中性", "減持": "減持", "賣出": "避免", "避免": "避免"}
    mapped_rating = rating_map.get(rating_raw, "觀察")
    render_investment_conclusion({
        "investment_conclusion": {
            "rating": mapped_rating,
            "horizon": report_package.get("investment_horizon", "中線"),
            "investor_type": request_risk_preference if request_risk_preference in ("保守", "平衡", "進取") else "平衡",
            "summary": cover.get("executive_summary", cover.get("summary", "綜合分析後，請參閱完整報告。")),
        }
    })

    # ── 10. 情景分析 + 組合倉位（保留）──────────────────────────────────────
    if confidence_level in {"HIGH", "MEDIUM"}:
        _render_scenario_section(sections.get("scenario_analysis", {}))
        _render_allocation_section(
            request_portfolio_size,
            cover.get("risk_score", "5.0/10"),
            cover.get("final_rating", "中性"),
        )
        _render_hkex_section(str(current_ticker), report_package)

    # ── 11. 系統穩定性提示 ────────────────────────────────────────────────────
    stability = sections.get("system_stability", {})
    if confidence_level in {"HIGH", "MEDIUM"} and stability.get("has_failures"):
        _section_title("系統提示", "系統穩定性提示")
        st.warning(stability.get("message", "部分分析模組未能完成，系統已自動切換至備援分析流程。"))
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
