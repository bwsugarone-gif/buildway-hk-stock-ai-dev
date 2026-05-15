"""
app.py

Buildway Tech (HK) Limited
Hong Kong AI Multi-Agent Stock Analysis Platform
"""

from __future__ import annotations

import os
from datetime import datetime

import streamlit as st

from agents.ceo_agent import CEOAgent
from core.config import APP_NAME, APP_VERSION, LOGO_PATH
from core.pdf_generator import PDFGenerator
from core.report_builder import ReportBuilder
from core.utils import normalize_hk_ticker


st.set_page_config(
    page_title=f"{APP_NAME} - 香港股票智能分析報告",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


def _init_state() -> None:
    defaults = {
        "report_package": None,
        "report_sections": None,
        "pdf_path": None,
        "llm_warning": "",
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


def _status_table() -> None:
    status = st.session_state.agent_status
    rows = [{"Agent": agent, "Status": state} for agent, state in status.items()]
    st.dataframe(rows, use_container_width=True, hide_index=True)


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


_init_state()


header_left, header_right = st.columns([1, 5])
with header_left:
    if os.path.exists(LOGO_PATH):
        st.image(str(LOGO_PATH), width=110)
with header_right:
    st.title("Buildway Tech (HK) Limited")
    st.subheader("香港股票智能分析報告")
    st.caption("AI Multi-Agent Financial Intelligence System")

st.divider()


with st.sidebar:
    st.header("分析設定")
    ticker_input = st.text_input(
        "香港股票代號",
        value="03311",
        placeholder="例如：03311 或 03311.HK",
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

    generate_btn = st.button("生成機構級PDF報告", type="primary", use_container_width=True)


if generate_btn:
    if not ticker_input.strip():
        st.error("請輸入香港股票代號。")
    else:
        ticker = normalize_hk_ticker(ticker_input)
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
                portfolio_size_hkd=portfolio_size if portfolio_size > 0 else None,
                manual_news=None,
                progress_callback=update_progress,
            )

            st.session_state.agent_status["CEO Agent"] = "完成"
            st.session_state.agent_status["Investment Committee Agent"] = "完成"

            builder = ReportBuilder()
            report_sections = builder.build(report_package)
            st.session_state.llm_warning = report_sections.get("metadata", {}).get("llm_warning", "")

            status_text.text("正在生成PDF報告...")
            os.makedirs("reports", exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            pdf_filename = f"Buildway_HK_Investment_Report_{ticker.replace('.', '_')}_{timestamp}.pdf"
            pdf_path = os.path.join("reports", pdf_filename)

            pdf_gen = PDFGenerator(logo_path=str(LOGO_PATH) if os.path.exists(LOGO_PATH) else None)
            pdf_gen.generate(report_sections, pdf_path)

            st.session_state.report_package = report_package
            st.session_state.report_sections = report_sections
            st.session_state.pdf_path = pdf_path

            progress.progress(1.0)
            status_text.text("報告生成完成。")
            st.success("PDF報告已成功生成。")
            if st.session_state.llm_warning:
                st.warning(st.session_state.llm_warning)

        except Exception as exc:
            st.error(f"生成報告時發生錯誤：{exc}")
            st.exception(exc)


if st.session_state.report_sections:
    sections = st.session_state.report_sections
    cover = sections.get("cover", {})
    risk = sections.get("risk_analysis", {})

    st.header("報告預覽")
    col1, col2, col3 = st.columns(3)
    col1.metric("Final committee rating", cover.get("final_rating", "N/A"))
    col2.metric("Risk score", cover.get("risk_score", "N/A"), cover.get("risk_label", ""))
    col3.metric("Stock code", cover.get("ticker", "N/A"))

    st.subheader("Multi-Agent status")
    _status_table()

    discussion = sections.get("multi_agent_discussion", {})
    st.subheader("Multi-Agent 投資委員會討論摘要")
    st.dataframe(discussion.get("table", []), use_container_width=True, hide_index=True)
    st.info(discussion.get("final_statement", ""))

    company = sections.get("company_intelligence", {})
    st.subheader("公司基本面與業務分析")
    for label, value in company.get("rows", [])[:4]:
        st.write(f"**{label}：** {value}")

    if st.session_state.pdf_path and os.path.exists(st.session_state.pdf_path):
        with open(st.session_state.pdf_path, "rb") as pdf_file:
            st.download_button(
                label="下載PDF報告",
                data=pdf_file,
                file_name=os.path.basename(st.session_state.pdf_path),
                mime="application/pdf",
                type="primary",
                use_container_width=True,
            )
else:
    st.info("請在左側輸入股票代號並生成報告。")
    st.subheader("Multi-Agent status")
    _status_table()


st.divider()
st.caption(f"© 2026 {APP_NAME} | {APP_VERSION}")
st.caption("本系統只作教育、研究及客戶試用用途，不構成投資建議。")
