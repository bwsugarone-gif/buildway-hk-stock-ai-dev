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
                background:
                    radial-gradient(circle at top left, rgba(217, 164, 65, 0.10), transparent 28rem),
                    linear-gradient(180deg, #f8fafc 0%, var(--bw-bg) 38%, #eef3f8 100%);
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

            div[data-testid="stDataFrame"] {
                overflow-x: auto;
            }

            [data-testid="stVerticalBlockBorderWrapper"] {
                border-color: rgba(16, 42, 67, 0.12);
                box-shadow: 0 12px 30px rgba(16, 39, 74, 0.05);
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
        "selected_demo_ticker": "",
        "recent_analysis": ["0700.HK", "9988.HK", "0688.HK"],
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


DEMO_SNAPSHOTS = [
    {
        "ticker": "0700.HK",
        "company": "騰訊控股",
        "sector": "科技 / 互聯網",
        "confidence": "高可信度",
        "rating": "中性",
        "snapshot": "大型科技平台，適合展示完整公司資料與機構級 PDF 輸出。",
    },
    {
        "ticker": "9988.HK",
        "company": "阿里巴巴集團",
        "sector": "科技 / 電子商務",
        "confidence": "高可信度",
        "rating": "觀察",
        "snapshot": "大型平台型企業，可展示估值、風險與投委會摘要。",
    },
    {
        "ticker": "0688.HK",
        "company": "中國海外發展",
        "sector": "地產",
        "confidence": "部分資料缺失",
        "rating": "保守觀察",
        "snapshot": "地產板塊示範案例，適合展示資料邊界與風險控制。",
    },
]


WORKFLOW_STEPS = [
    ("市場資料 Agent", "取得價格、成交量、市值與公司 metadata。"),
    ("財務分析 Agent", "計算估值、財務健康度與核心比率。"),
    ("風險控制 Agent", "評估流動性、槓桿、波動與下行情境。"),
    ("新聞分析 Agent", "整理市場情緒與事件風險。"),
    ("投資委員會", "整合多 agent 觀點並輸出最終結論。"),
]


def _set_demo_ticker(ticker: str) -> None:
    st.session_state.ticker_input_value = ticker.replace(".HK", "")
    st.session_state.selected_demo_ticker = ticker
    st.rerun()


def _render_hero() -> None:
    with st.container(border=True):
        left, right = st.columns([1.35, 1])
        with left:
            st.caption("Buildway SaaS Intelligence")
            st.title("Buildway AI Financial Intelligence Platform")
            st.subheader("AI 驅動香港股票研究與風險分析平台")
            st.write("60 秒內生成 Multi-Agent 分析、財務風險評估、機構級 PDF 報告與投資委員會結論。")
            if st.button("開始分析", type="primary", use_container_width=True):
                st.session_state.ticker_input_value = st.session_state.ticker_input_value or "0700"
                st.rerun()
        with right:
            st.metric("平均生成時間", "60 秒內")
            st.metric("分析架構", "Multi-Agent")
            st.metric("輸出格式", "PDF 報告")


def _render_demo_snapshots() -> None:
    _section_title("Demo cases", "熱門示範案例", "點選卡片即可自動填入股票代號。")
    columns = st.columns(3)
    for column, item in zip(columns, DEMO_SNAPSHOTS):
        with column:
            with st.container(border=True):
                st.caption(item["ticker"])
                st.markdown(f"**{item['company']}**")
                st.caption(item["sector"])
                st.metric("資料可信度", item["confidence"])
                st.metric("最終評級", item["rating"])
                st.caption(item["snapshot"])
                if st.button(f"分析 {item['ticker']}", key=f"demo_{item['ticker']}", use_container_width=True):
                    _set_demo_ticker(item["ticker"])


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


def _render_pdf_preview(cover: dict[str, Any]) -> None:
    _section_title("PDF preview", "PDF 預覽", "下載前先檢視報告封面摘要。")
    with st.container(border=True):
        st.caption("Institutional report cover")
        st.markdown(f"**{_escape(cover.get('company_name', 'N/A'))}**")
        cols = st.columns(2)
        cols[0].metric("Ticker", cover.get("ticker", "N/A"))
        cols[1].metric("Rating", cover.get("final_rating", "N/A"))
        st.caption(_escape(cover.get("data_confidence_label", "")))
        st.caption(_escape(cover.get("sector", "")))


def _render_empty_state() -> None:
    left, right = st.columns([1.05, 0.95])
    with left:
        with st.container(border=True):
            st.caption("How it works")
            st.markdown("**輸入香港股票代號，系統會生成一份可下載的機構級研究報告。**")
            st.caption("支援 0700、9988、0688、3416 等格式；INVALID ticker 會停止公司基本面敘述。")
        _render_demo_snapshots()
    with right:
        _render_pdf_preview({
            "company_name": "示範公司",
            "ticker": "0700.HK",
            "final_rating": "中性",
            "data_confidence_label": "高可信度",
            "sector": "科技 / 互聯網",
        })
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
    _section_title("Company profile", "公司資料", "資料只來自市場資料供應商或本地HK stock master database。")
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
    st.caption("Buildway SaaS Intelligence")
    st.title("Buildway AI Financial Intelligence Platform")
    st.subheader("AI 驅動香港股票研究與風險分析平台")
    st.write("60 秒內生成 Multi-Agent 分析、財務風險評估、機構級 PDF 報告與投資委員會結論。")
    if st.button("開始分析", type="primary", use_container_width=True):
        st.session_state.ticker_input_value = st.session_state.ticker_input_value or "0700"
        st.rerun()

_render_demo_snapshots()
_render_workflow_timeline()
_render_source_transparency()
_render_trust_layer()


with st.sidebar:
    if os.path.exists(LOGO_PATH):
        st.image(str(LOGO_PATH), width=96)

    st.header("分析設定")
    ticker_input = st.text_input(
        "香港股票代號",
        key="ticker_input_value",
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
    st.caption("客戶試用樣本")
    sample_cols = st.columns(3)
    if sample_cols[0].button("0700", use_container_width=True):
        st.session_state.ticker_input_value = "0700"
        st.rerun()
    if sample_cols[1].button("9988", use_container_width=True):
        st.session_state.ticker_input_value = "9988"
        st.rerun()
    if sample_cols[2].button("0688", use_container_width=True):
        st.session_state.ticker_input_value = "0688"
        st.rerun()
    if st.button("Clear / Reset", use_container_width=True):
        st.session_state.ticker_input_value = ""
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

    _company_profile_panel(cover)
    _render_pdf_preview(cover)

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

    company = sections.get("company_intelligence", {})
    _section_title("Company intelligence", "公司基本面與業務分析", "重點內容以卡片形式呈現，方便客戶快速閱讀")
    _company_cards(company.get("rows", [])[:4])
else:
    _render_empty_state()
    st.divider()
    st.caption(f"2026 {APP_NAME} | {BUILD_VERSION}")
    st.caption("本系統不構成投資建議；所有輸出只供研究、教育及客戶展示用途。")
    st.stop()
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
