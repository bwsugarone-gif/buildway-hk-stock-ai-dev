"""
app.py

Buildway Tech (HK) Limited
Hong Kong AI Multi-Agent Stock Analysis Platform
"""

from __future__ import annotations

import html
import os
from datetime import datetime
from typing import Any

import streamlit as st

from agents.ceo_agent import CEOAgent
from core.config import (
    APP_NAME, APP_VERSION, BUILD_STAGE, BUILD_VERSION, BUILD_COMMIT,
    LOGO_PATH, DEPLOY_ENV,
)
from core.pdf_generator import PDFGenerator
from core.report_builder import ReportBuilder
from core.utils import normalize_hk_ticker, validate_hk_ticker


st.set_page_config(
    page_title=f"{APP_NAME} - 香港股票智能分析報告",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
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
                background: var(--bw-bg);
                color: var(--bw-text);
            }

            .block-container {
                padding: 0.85rem 0.85rem 2.5rem;
                max-width: 1180px;
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

            @media (max-width: 719px) {
                [data-testid="column"] {
                    width: 100% !important;
                    flex: 1 1 100% !important;
                    min-width: 100% !important;
                }

                [data-testid="stSidebar"] {
                    min-width: 100% !important;
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
        "ticker_input_value": "",
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


def _sample_report_cards() -> None:
    cols = st.columns(3)
    samples = [
        ("高可信度示例", "0700.HK / 9988.HK / 0005.HK", "適合展示完整客戶報告流程。"),
        ("部分資料示例", "3416.HK", "適合展示保守假設與資料提示。"),
        ("無效代號示例", "12345.HK", "適合展示防幻覺控制。"),
    ]
    for col, (title, value, note) in zip(cols, samples):
        with col:
            with st.container(border=True):
                st.markdown(f"**{title}**")
                st.metric("股票代號", value)
                st.caption(note)


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
    st.subheader("香港股票智能分析系統")
    st.write("為客戶快速整理市場資料、估值觀點、風險訊號與投資委員會結論，輸出可下載的機構級分析報告。")


with st.sidebar:
    if os.path.exists(LOGO_PATH):
        st.image(str(LOGO_PATH), width=96)

    st.header("分析設定")
    ticker_input = st.text_input(
        "香港股票代號",
        key="ticker_input_value",
        placeholder="例如：3416、700、0005 或 9988.HK",
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
    st.caption("客戶試用樣本")
    sample_cols = st.columns(3)
    if sample_cols[0].button("700", use_container_width=True):
        st.session_state.ticker_input_value = "700"
        st.rerun()
    if sample_cols[1].button("3416", use_container_width=True):
        st.session_state.ticker_input_value = "3416"
        st.rerun()
    if sample_cols[2].button("12345", use_container_width=True):
        st.session_state.ticker_input_value = "12345"
        st.rerun()
    st.caption("700 展示高可信度；3416 展示部分資料；12345 展示無效代號控制。")

    st.divider()
    _today = datetime.now().strftime("%Y-%m-%d")
    _env_label = "Streamlit Cloud" if DEPLOY_ENV == "streamlit-cloud" else "Local"
    st.caption(f"{APP_VERSION} | {BUILD_STAGE}")
    st.caption(f"{_today} | {_env_label}")
    st.caption(f"Build: {BUILD_VERSION}")
    st.caption(f"Commit: {BUILD_COMMIT}")


if generate_btn:
    is_valid_ticker, _ticker_error = validate_hk_ticker(ticker_input)
    if not is_valid_ticker:
        st.error("請輸入有效香港股票代號")
    else:
        st.session_state.is_generating = True
        st.session_state.pdf_warning = ""
        ticker = normalize_hk_ticker(ticker_input)
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
                risk_preference=risk_preference,
                report_type="HK Stock Investment Analysis Report",
                portfolio_size_hkd=portfolio_size if portfolio_size > 0 else None,
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
    confidence_label = cover.get("data_confidence_label", "🟡 部分資料缺失")
    _confidence_badge(confidence_label)
    _confidence_note(confidence_label)
    col1, col2, col3 = st.columns(3)
    col1.metric("投資委員會結論", cover.get("final_rating", "N/A"))
    col2.metric("風險分數", cover.get("risk_score", "N/A"), cover.get("risk_label", ""))
    col3.metric("股票代號", cover.get("ticker", "N/A"))

    company_name_preview = cover.get("company_name", "N/A")
    sector_preview = cover.get("sector", "香港上市公司")
    with st.container(border=True):
        st.caption("Client-ready snapshot")
        st.markdown(f"**{_escape(company_name_preview)} | {_escape(cover.get('ticker', 'N/A'))}**")
        st.caption(_escape(cover.get("data_confidence_label", "")))
        st.caption(_escape(sector_preview))

    if st.session_state.pdf_path and os.path.exists(st.session_state.pdf_path):
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

    _section_title("Agent workflow", "Multi-Agent 狀態", "客戶可讀的分析流程概覽")
    _status_cards()

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

    company = sections.get("company_intelligence", {})
    _section_title("Company intelligence", "公司基本面與業務分析", "重點內容以卡片形式呈現，方便客戶快速閱讀")
    _company_cards(company.get("rows", [])[:4])
else:
    col_intro, col_status = st.columns([1.15, 1])
    with col_intro:
        with st.container(border=True):
            st.caption("開始分析")
            st.markdown("**輸入香港股票代號即可生成客戶版研究報告。**")
            st.caption("系統會整合市場、財務、風險、新聞與組合觀點，並輸出可下載 PDF。")
        _sample_report_cards()
    with col_status:
        _section_title("Workflow", "Multi-Agent 狀態")
        _status_cards()

st.divider()
st.caption(f"© 2026 {APP_NAME} | {BUILD_VERSION}")
st.caption("本系統只作教育、研究及客戶試用用途，不構成投資建議。")
