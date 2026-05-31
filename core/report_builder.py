"""
core/report_builder.py

Builds a client-ready institutional investment report from Python-calculated
agent outputs. LLM use is optional and limited to narrative wording only.
"""

from __future__ import annotations

from typing import Any, Dict, List

from core.config import APP_NAME, APP_VERSION, USE_AI_ANALYSIS
from core.market_snapshot import build_market_snapshot
from core.scenario_engine import build_scenario_analysis
from core.risk_engine_v2 import build_risk_assessment
from core.source_transparency import build_source_transparency
from core.source_registry import build_source_registry
from core.agent_opinion_engine import build_agent_opinions
from core.competitive_landscape_engine import build_competitive_landscape
from core.data_confidence import (
    INVALID,
    INVALID_MARKET_DATA_MESSAGE,
    INVALID_PDF_NOTICE,
    PARTIAL_DATA_WARNING,
    confidence_label,
)
from core.llm_provider import LLMProvider, LLMProviderError
from core.safe_math import safe_number
from core.utils import format_currency_hkd, format_percentage, get_timestamp


RATING_MAP = {
    "strong_watch": "積極關注",
    "watch": "觀察名單",
    "neutral": "中性",
    "high_risk": "高風險",
    "avoid": "暫不建議",
}


def _num(value: Any, default: float = 0.0) -> float:
    return safe_number(value, default)


def _risk_label(score: float) -> str:
    if score <= 3:
        return "低風險"
    if score <= 6:
        return "中等風險"
    if score <= 8:
        return "高風險"
    return "極高風險"


def _fmt_pct(value: Any, decimals: int = 1) -> str | None:
    n = _num(value)
    return format_percentage(n, decimals) if n != 0 else None


def _fmt_hkd(value: Any) -> str | None:
    n = _num(value)
    return format_currency_hkd(n) if n > 0 else None


def _fmt_ratio(value: Any, decimals: int = 2) -> str | None:
    n = _num(value)
    return f"{n:.{decimals}f}x" if n > 0 else None


def _valid_text(value: Any) -> bool:
    text = str(value if value is not None else "").strip()
    if not text or text in {"N/A", "None", "0", "0.0", "0.00", "資料待補充"}:
        return False
    return not any(token in text for token in ("HK$0.00", "0.0%", "0.00x", "0.0x"))


class ReportBuilder:
    """Transform raw multi-agent outputs into PDF-ready sections."""

    def build(self, report_package: Dict[str, Any]) -> Dict[str, Any]:
        meta = report_package.get("report_metadata", {})
        market = report_package.get("market_data", {})
        history = report_package.get("financial_history", {})
        fin = report_package.get("financial_analysis", {})
        risk = report_package.get("risk_analysis", {})
        news = report_package.get("news_analysis", {})
        portfolio = report_package.get("portfolio_analysis", {})
        ic = report_package.get("ic_result", {})
        agent_opinions = report_package.get("agent_opinions", [])
        agent_status = report_package.get("agent_status", meta.get("agent_status", {}))
        agent_error_log = report_package.get("agent_error_log", meta.get("agent_error_log", []))
        data_confidence = meta.get("data_confidence") or market.get("data_confidence", "LOW")

        rating = self._final_rating(fin, risk, ic)
        llm_warning = ""

        executive_summary = self._build_executive_summary(
            market, fin, risk, news, portfolio, rating
        )
        if USE_AI_ANALYSIS and data_confidence != INVALID:
            executive_summary, llm_warning = self._maybe_deepseek_summary(
                executive_summary, market, fin, risk, rating
            )

        ticker = meta.get("stock_code") or meta.get("ticker") or market.get("ticker", "")

        # ── v3.5 新增 engines ──────────────────────────────────────────────
        try:
            risk_v2 = build_risk_assessment(report_package)
        except Exception:
            risk_v2 = {}

        try:
            source_transparency = build_source_transparency(report_package)
        except Exception:
            source_transparency = {}

        try:
            agent_opinions_v2 = build_agent_opinions(report_package)
        except Exception:
            agent_opinions_v2 = {}

        try:
            competitive_landscape = build_competitive_landscape(ticker, report_package)
        except Exception:
            competitive_landscape = {}

        # v4.0.4: build authoritative source_registry — UI reads from this key
        try:
            source_registry = build_source_registry(report_package)
        except Exception:
            source_registry = {}

        sections = {
            "metadata": {
                "brand": APP_NAME,
                "version": APP_VERSION,
                "generated_at": meta.get("generated_at", get_timestamp()),
                "llm_warning": llm_warning,
                "analysis_context": meta.get("analysis_context", {}),
                "stock_code": ticker,
                "data_confidence": data_confidence,
                "data_confidence_label": meta.get("data_confidence_label") or market.get("data_confidence_label") or confidence_label(data_confidence),
            },
            "cover": self._build_cover(meta, market, risk, rating),
            "market_snapshot": build_market_snapshot(market),
            "executive_summary": executive_summary,
            "company_intelligence": self._build_company_intelligence(market),
            # ── v3.5 新增 ──
            "competitive_landscape": competitive_landscape,
            "source_transparency": source_transparency,
            "source_registry": source_registry,   # v4.0.4: authoritative registry for UI
            "agent_opinions_v2": agent_opinions_v2,
            "risk_assessment_v2": risk_v2,
            # ─────────────────
            "system_stability": self._build_system_stability(agent_status, agent_error_log),
            "multi_agent_discussion": self._build_multi_agent_discussion(
                market, fin, risk, news, portfolio, ic, rating, agent_opinions
            ),
            "financial_analysis": self._build_financial_analysis(market, history, fin),
            "risk_analysis": self._build_risk_analysis(risk),
            "news_catalyst_analysis": self._build_news_catalyst_analysis(news),
            "hkex_intelligence": self._build_hkex_intelligence(market),
            "scenario_analysis": build_scenario_analysis(market, fin, risk, self._build_news_catalyst_analysis(news)),
            "portfolio_view": self._build_portfolio_view(portfolio, risk, rating),
            "ic_conclusion": self._build_ic_conclusion(ic, risk, rating, llm_warning, fin),
            "disclaimer": self._build_disclaimer(),
        }
        return self._strip_placeholder_values(sections)

    def build_fos_v3_sections(self, report_package: Dict[str, Any]) -> Dict[str, Any]:
        """
        Return only the v3.5 FOS sections for direct use in app.py / fos_components.py.
        Lightweight — does not run the full report pipeline.
        """
        meta = report_package.get("report_metadata", {})
        ticker = meta.get("stock_code") or meta.get("ticker") or report_package.get("market_data", {}).get("ticker", "")

        out: Dict[str, Any] = {}

        try:
            out["risk_assessment_v2"] = build_risk_assessment(report_package)
        except Exception as exc:
            out["risk_assessment_v2"] = {"error": str(exc)}

        try:
            out["source_transparency"] = build_source_transparency(report_package)
        except Exception as exc:
            out["source_transparency"] = {"error": str(exc)}

        try:
            out["agent_opinions_v2"] = build_agent_opinions(report_package)
        except Exception as exc:
            out["agent_opinions_v2"] = {"error": str(exc)}

        try:
            out["competitive_landscape"] = build_competitive_landscape(ticker, report_package)
        except Exception as exc:
            out["competitive_landscape"] = {"error": str(exc)}

        # v4.0.4: authoritative source_registry for UI rendering
        try:
            out["source_registry"] = build_source_registry(report_package)
        except Exception as exc:
            out["source_registry"] = {"error": str(exc)}

        return out

    def _maybe_deepseek_summary(
        self,
        fallback_summary: Dict[str, Any],
        market: Dict[str, Any],
        fin: Dict[str, Any],
        risk: Dict[str, Any],
        rating: str,
    ) -> tuple[Dict[str, Any], str]:
        prompt = (
            "請以繁體中文為香港股票智能分析報告撰寫3至5點Executive Summary。"
            "不可重新計算任何數字，只可引用Python提供的數值與結論。"
        )
        context = {
            "ticker": market.get("ticker"),
            "company_name": market.get("company_name"),
            "final_rating": rating,
            "risk_score": risk.get("composite_risk_score"),
            "valuation_range": fin.get("valuation_range"),
        }
        try:
            narrative = LLMProvider(provider="deepseek", fallback_order=["deepseek"]).generate(
                prompt=prompt,
                context=context,
                fallback=False,
                max_tokens=700,
            )
            if narrative:
                updated = dict(fallback_summary)
                updated["llm_narrative"] = narrative
                return updated, ""
        except LLMProviderError as exc:
            return fallback_summary, f"DeepSeek narrative unavailable; local fallback used. {exc}"
        except Exception as exc:
            return fallback_summary, f"DeepSeek narrative unavailable; local fallback used. {exc}"
        return fallback_summary, ""

    def _build_system_stability(
        self,
        agent_status: Dict[str, str],
        agent_error_log: List[str],
    ) -> Dict[str, Any]:
        failed_agents = [agent for agent, status in agent_status.items() if status == "失敗"]
        return {
            "title": "系統穩定性提示",
            "has_failures": bool(failed_agents),
            "message": (
                "部分 Agent 分析未能完成，系統已自動切換至備援分析流程。部分分析結果可能受限制。"
                if failed_agents
                else "所有核心 Agent 已完成分析。"
            ),
            "failed_agents": failed_agents,
            "agent_status": agent_status,
            "error_log": agent_error_log,
        }

    def _final_rating(self, fin: Dict[str, Any], risk: Dict[str, Any], ic: Dict[str, Any]) -> str:
        if fin.get("data_confidence") == INVALID or risk.get("data_confidence") == INVALID:
            return "無法評估"
        risk_score = _num(risk.get("composite_risk_score"), 5)
        upside = _num(fin.get("valuation_range", {}).get("upside_to_mid"), 0)

        if risk_score >= 8:
            return RATING_MAP["avoid"]
        if risk_score >= 7:
            return RATING_MAP["high_risk"]
        if upside >= 0.15 and risk_score <= 5:
            return RATING_MAP["strong_watch"]
        if upside >= 0 and risk_score <= 6:
            return RATING_MAP["watch"]
        return RATING_MAP["neutral"]

    def _build_cover(
        self,
        meta: Dict[str, Any],
        market: Dict[str, Any],
        risk: Dict[str, Any],
        rating: str,
    ) -> Dict[str, Any]:
        return {
            "brand": "Buildway Tech (HK) Limited",
            "system": "AI Multi-Agent Financial Intelligence System",
            "title": "香港股票智能分析報告",
            "ticker": meta.get("stock_code") or meta.get("ticker") or market.get("ticker", "N/A"),
            "company_name": meta.get("company_name") or market.get("company_name") or "資料驗證未完成",
            "company_name_zh": market.get("company_name_zh") or market.get("company_name") or "",
            "company_name_en": market.get("company_name_en", ""),
            "sector": market.get("sector") or "資料驗證未完成",
            "business": market.get("business", ""),
            "market_type": market.get("market_type", ""),
            "metadata_source": market.get("metadata_source", ""),
            "report_date": meta.get("generated_at", get_timestamp()),
            "final_rating": rating,
            "risk_score": f"{_num(risk.get('composite_risk_score'), 5):.1f}/10",
            "risk_label": _risk_label(_num(risk.get("composite_risk_score"), 5)),
            "data_confidence": meta.get("data_confidence") or market.get("data_confidence", "LOW"),
            "data_confidence_label": meta.get("data_confidence_label") or market.get("data_confidence_label") or confidence_label(meta.get("data_confidence") or market.get("data_confidence", "LOW")),
            "data_completeness_note": meta.get("data_completeness_note", ""),
        }

    def _build_executive_summary(
        self,
        market: Dict[str, Any],
        fin: Dict[str, Any],
        risk: Dict[str, Any],
        news: Dict[str, Any],
        portfolio: Dict[str, Any],
        rating: str,
    ) -> Dict[str, Any]:
        vr = fin.get("valuation_range", {})
        if market.get("data_confidence") == INVALID or fin.get("data_confidence") == INVALID:
            return {
                "title": "Executive Summary",
                "bullets": [
                    INVALID_MARKET_DATA_MESSAGE,
                    INVALID_PDF_NOTICE,
                    "系統未生成公司介紹、收入模式、產品服務或估值敘事，避免產生不可靠內容。",
                ],
                "final_rating": "無法評估",
                "key_risk": "資料驗證未完成",
                "key_opportunity": "不適用",
                "recommended_action": "停止進階分析",
                "data_confidence_label": market.get("data_confidence_label", confidence_label(INVALID)),
                "llm_narrative": "",
            }
        risk_score = _num(risk.get("composite_risk_score"), 5)
        current = _num(market.get("current_price"))
        mid = _num(vr.get("mid"))
        opportunity = (
            "估值中位數高於現價，具備重新評估空間。"
            if mid > current and current > 0
            else "現價接近或高於模型估值中位數，需等待更清晰催化因素。"
        )
        key_risk = self._top_risk_name(risk)

        return {
            "title": "Executive Summary",
            "bullets": [
                f"本報告以Python計算市場、財務、估值及風險指標，並由Multi-Agent架構整合投資觀點。",
                f"最終行動分類為「{rating}」，綜合反映估值吸引力、財務質素及風險承受度。",
                f"風險評級為{_risk_label(risk_score)}，加權風險分數為{risk_score:.1f}/10。",
                f"主要機會：{opportunity}",
                f"主要風險：{key_risk}，需要持續監察。",
            ],
            "final_rating": rating,
            "key_risk": key_risk,
            "key_opportunity": opportunity,
            "recommended_action": rating,
            "data_confidence_label": market.get("data_confidence_label", confidence_label(market.get("data_confidence", "LOW"))),
            "llm_narrative": "",
        }

    def _build_company_intelligence(self, market: Dict[str, Any]) -> Dict[str, Any]:
        ticker = market.get("ticker", "N/A")
        name = market.get("company_name", ticker)
        sector = market.get("sector", "香港上市公司")
        metadata = market.get("company_metadata", {}) or {}
        name_zh = market.get("company_name_zh") or metadata.get("name_zh") or name
        name_en = market.get("company_name_en") or metadata.get("name_en") or ""
        business = market.get("business") or metadata.get("business") or ""
        market_type = market.get("market_type") or metadata.get("market_type") or ""

        if market.get("data_confidence") == INVALID:
            return {
                "title": "公司基本面與業務分析",
                "rows": [
                    ("公司資料", "未能取得有效公司資料，系統已停止公司基本面敘述。"),
                    ("資料狀態", INVALID_MARKET_DATA_MESSAGE),
                    ("分析限制", "系統未生成公司介紹、主要業務、收入來源或產品服務描述。"),
                    ("PDF提示", INVALID_PDF_NOTICE),
                    ("下一步", "請核對股票代號，或改用可確認有效市場資料的香港上市股票代號。"),
                ],
            }

        if market.get("data_confidence") in {"LOW", "MEDIUM"}:
            note = market.get("data_warning") or PARTIAL_DATA_WARNING
            return {
                "title": "公司基本面與業務分析",
                "rows": [
                    ("中文公司名", f"{name_zh}（{ticker}）"),
                    ("英文名", name_en or "資料待補充"),
                    ("行業分類", sector),
                    ("主營業務", business or "資料待補充"),
                    ("市場分類", market_type or "資料待補充"),
                    ("資料可信度", market.get("data_confidence_label", confidence_label(market.get("data_confidence", "LOW")))),
                    ("資料提示", note),
                ],
            }

        return {
            "title": "公司基本面與業務分析",
            "rows": [
                ("中文公司名", f"{name_zh}（{ticker}）"),
                ("英文名", name_en or "資料待補充"),
                ("行業分類", sector),
                ("主營業務", business or "資料待補充"),
                ("市場分類", market_type or "資料待補充"),
                ("資料來源", market.get("metadata_source") or "market data provider"),
                ("分析邊界", "公司資料只引用市場資料供應商或本地HK stock master database，不由LLM生成。"),
            ],
        }

    def _build_multi_agent_discussion(
        self,
        market: Dict[str, Any],
        fin: Dict[str, Any],
        risk: Dict[str, Any],
        news: Dict[str, Any],
        portfolio: Dict[str, Any],
        ic: Dict[str, Any],
        rating: str,
        agent_opinions: List[Dict[str, Any]] | None = None,
    ) -> Dict[str, Any]:
        risk_score = _num(risk.get("composite_risk_score"), 5)
        if market.get("data_confidence") == INVALID:
            return {
                "title": "Multi-Agent 投資委員會討論摘要",
                "table": agent_opinions or [],
                "consensus": INVALID_MARKET_DATA_MESSAGE,
                "final_statement": "經 Multi-Agent Team 覆核後，本系統判定該股票代號資料驗證未完成，已停止進階財務分析。",
            }
        vr = fin.get("valuation_range", {})
        upside = _num(vr.get("upside_to_mid"), 0)
        health = fin.get("health_score", {})
        sentiment = news.get("sentiment_analysis", {})

        table = agent_opinions if agent_opinions else [
            {
                "Agent": "CEO Agent",
                "性格定位": "冷靜、策略性、重紀律",
                "核心觀點": "完成任務拆解，整合市場、財務、風險、新聞及組合觀點。",
                "正面因素": "多代理框架已完成交叉檢查。",
                "主要憂慮": "需確保結論只作研究用途。",
                "信心分數": "7/10",
                "對評級影響": "neutral",
            },
            {
                "Agent": "Market Data Agent",
                "性格定位": "市場敏感、反應快、短線警覺",
                "核心觀點": f"現價HK${_num(market.get('current_price')):.2f}，成交量約{_num(market.get('volume')):,.0f}股，短線需觀察價格與成交配合。",
                "正面因素": "價格及成交資料提供即時參考。",
                "主要憂慮": "股價波動及成交縮減會削弱短期技術確認。",
                "信心分數": "7/10",
                "對評級影響": "neutral",
            },
            {
                "Agent": "Financial Analyst Agent",
                "性格定位": "重細節、估值導向、質疑弱數據",
                "核心觀點": f"估值中位數為{_fmt_hkd(vr.get('mid'))}，對現價潛在差距為{_fmt_pct(upside)}；財務健康評級為{health.get('grade', 'N/A')}。",
                "正面因素": "若現價低於估值中位數，存在估值修復空間。",
                "主要憂慮": "DCF及同業倍數需依賴收入、利潤率及現金流假設。",
                "信心分數": "6/10",
                "對評級影響": "positive" if upside > 0 else "neutral",
            },
            {
                "Agent": "Risk Management Agent",
                "性格定位": "保守、審慎、重視隱藏下行",
                "核心觀點": f"加權風險分數為{risk_score:.1f}/10，屬{_risk_label(risk_score)}。",
                "正面因素": "若流動性及槓桿受控，下行壓力可管理。",
                "主要憂慮": f"首要風險為{self._top_risk_name(risk)}。",
                "信心分數": "8/10",
                "對評級影響": "negative" if risk_score >= 7 else "neutral",
            },
            {
                "Agent": "News Intelligence Agent",
                "性格定位": "好奇、重視事件脈絡、催化因素導向",
                "核心觀點": f"市場情緒分數為{_num(sentiment.get('score'), 0.5):.2f}，正面與負面訊號需要同步跟蹤。",
                "正面因素": "正面公告或行業事件可改善市場敘事。",
                "主要憂慮": "新聞資料仍需與正式公告及業績資料交叉驗證。",
                "信心分數": "6/10",
                "對評級影響": "neutral",
            },
            {
                "Agent": "Portfolio Manager Agent",
                "性格定位": "務實、重視本金保護、倉位敏感",
                "核心觀點": f"建議以風險分數調整觀察倉位，模型參考倉位為{_fmt_pct(portfolio.get('suggested_position_pct'))}。",
                "正面因素": "小倉位可保留參與上行的彈性。",
                "主要憂慮": "倉位控制只作教育及風險管理參考。",
                "信心分數": "8/10",
                "對評級影響": "neutral",
            },
            {
                "Agent": "Investment Committee Agent",
                "性格定位": "最終覆核、平衡、嚴格、專業",
                "核心觀點": "綜合各代理觀點後，採用審慎、分層監察的結論。",
                "正面因素": "若風險受控且估值合理，可維持觀察或中性偏正面。",
                "主要憂慮": "若基本面或風險指標惡化，需下調評級。",
                "信心分數": "7/10",
                "對評級影響": f"最終分類：{rating}",
            },
        ]

        return {
            "title": "Multi-Agent 投資委員會討論摘要",
            "table": table,
            "consensus": "各代理一致認為應以Python計算結果作為估值及風險基礎，LLM只負責報告語言與投資敘事。主要分歧在於估值修復空間與風險承受度之間的取捨。",
            "final_statement": f"經 Multi-Agent Team 綜合討論後，本系統將該股票列為：{rating}",
        }

    def _build_financial_analysis(
        self,
        market: Dict[str, Any],
        history: Dict[str, Any],
        fin: Dict[str, Any],
    ) -> Dict[str, Any]:
        metrics = fin.get("metrics", {})
        if fin.get("data_confidence") == INVALID:
            return {
                "title": "Financial Analysis",
                "commentary": [INVALID_MARKET_DATA_MESSAGE, INVALID_PDF_NOTICE],
                "metrics": [
                    ("資料可信度", confidence_label(INVALID)),
                    ("估值分析", "已停止"),
                    ("財務比率", "不適用"),
                    ("資料用途", "系統測試"),
                ],
                "history": [],
            }
        dcf = fin.get("dcf", {})
        comps = fin.get("comps", {})
        vr = fin.get("valuation_range", {})

        return {
            "title": "Financial Analysis",
            "commentary": [
                fin.get("data_warning", "") or "",
                f"收入規模：{_fmt_hkd(market.get('revenue_ttm'))}，反映公司當前業務體量。",
                f"毛利率：{_fmt_pct(market.get('gross_margin'))}；淨利率：{_fmt_pct(market.get('net_margin'))}，用作衡量收入及利潤質量。",
                f"EBITDA：{_fmt_hkd(market.get('ebitda'))}；淨負債：{_fmt_hkd(metrics.get('net_debt'))}。",
                f"DCF基準內在價值：HK${_num(dcf.get('base_intrinsic_price')):.2f}；估值區間：{_fmt_hkd(vr.get('low'))}至{_fmt_hkd(vr.get('high'))}。",
                f"同業參考：P/E {comps.get('company_pe', 0):.1f}x，P/B {comps.get('company_pb', 0):.2f}x，EV/EBITDA {comps.get('company_ev_ebitda', 0):.1f}x。",
            ],
            "metrics": [
                ("收入 TTM", _fmt_hkd(market.get("revenue_ttm"))),
                ("EBITDA", _fmt_hkd(market.get("ebitda"))),
                ("淨利潤 TTM", _fmt_hkd(market.get("net_income_ttm"))),
                ("毛利率", _fmt_pct(market.get("gross_margin"))),
                ("淨利率", _fmt_pct(market.get("net_margin"))),
                ("ROE", _fmt_pct(market.get("roe"))),
                ("EV/EBITDA", _fmt_ratio(metrics.get("ev_ebitda"), 1)),
                ("P/B", _fmt_ratio(market.get("pb_ratio"), 2)),
            ],
            "history": self._history_rows(history),
        }

    def _history_rows(self, history: Dict[str, Any]) -> List[List[str]]:
        years = history.get("years", [])
        rows = []
        for index, year in enumerate(years):
            rows.append([
                str(year),
                _fmt_hkd((history.get("revenue") or [0])[index] if index < len(history.get("revenue", [])) else 0),
                _fmt_hkd((history.get("ebitda") or [0])[index] if index < len(history.get("ebitda", [])) else 0),
                _fmt_hkd((history.get("free_cash_flow") or [0])[index] if index < len(history.get("free_cash_flow", [])) else 0),
            ])
        return rows

    def _build_risk_analysis(self, risk: Dict[str, Any]) -> Dict[str, Any]:
        risk_table = []
        if risk.get("data_confidence") == INVALID:
            return {
                "title": "Risk Analysis",
                "composite_score": "N/A",
                "risk_label": "無法評估",
                "risk_table": [],
                "top_risks": [],
            }
        for dim, score in risk.get("dimension_scores", {}).items():
            score_num = _num(score)
            risk_table.append({
                "dimension": self._clean_risk_dimension(dim),
                "score": f"{score_num:.1f}",
                "level": _risk_label(score_num),
                "weight": f"{_num(risk.get('risk_weights', {}).get(dim)) * 100:.0f}%",
                "heat": self._heat(score_num),
            })

        return {
            "title": "Risk Analysis",
            "composite_score": f"{_num(risk.get('composite_risk_score'), 5):.1f}/10",
            "risk_label": _risk_label(_num(risk.get("composite_risk_score"), 5)),
            "risk_table": risk_table,
            "top_risks": risk_table[:5],
        }

    def _build_news_catalyst_analysis(self, news: Dict[str, Any]) -> Dict[str, Any]:
        confidence = news.get("news_confidence") or news.get("sentiment_analysis", {}).get("confidence") or "未接入"
        positive = news.get("positive_catalysts") or news.get("positive_factors") or []
        negative = news.get("negative_catalysts") or news.get("negative_factors") or []
        neutral = news.get("neutral_events") or news.get("neutral_signals") or []
        risk_events = news.get("risk_events") or news.get("monitor_items") or []
        has_news = bool(news.get("has_news") or positive or negative or neutral or risk_events)
        if not has_news:
            confidence = "未接入"
        boundary = (
            "新聞催化分析只使用已接入及已驗證的新聞來源，不會生成未經驗證事件。"
            if has_news
            else "暫未接入即時新聞資料，新聞催化分析會於後續版本啟用。"
        )
        return {
            "title": "新聞與事件催化分析",
            "status": news.get("summary") or "暫未接入即時新聞資料",
            "news_confidence": confidence,
            "positive_catalysts": positive,
            "negative_catalysts": negative,
            "neutral_events": neutral,
            "risk_events": risk_events,
            "monitor_items": risk_events,
            "has_news": has_news,
            "analysis_boundary": boundary,
            "no_news_message": "暫未接入即時新聞資料，系統目前不會生成假新聞或未經驗證事件。",
        }

    def _build_hkex_intelligence(self, market: Dict[str, Any]) -> Dict[str, Any]:
        try:
            from core.hkex_intelligence_engine import build_hkex_intelligence
            return build_hkex_intelligence(str(market.get("ticker") or ""))
        except Exception:
            return {
                "ticker": market.get("ticker", ""),
                "has_data": False,
                "status_summary": "未取得已驗證 HKEX 公告資料",
                "analysis_boundary": "未取得已驗證 HKEX 公告資料",
            }

    def _build_scenario_analysis(self, risk: Dict[str, Any]) -> Dict[str, Any]:
        scenarios = risk.get("scenarios", {})
        if risk.get("data_confidence") == INVALID:
            return {
                "title": "Scenario Analysis",
                "rows": [["N/A", INVALID_MARKET_DATA_MESSAGE, "N/A", "N/A"]],
                "triggers": ["股票代號或市場資料驗證未完成"],
            }
        if not scenarios:
            return {
                "title": "Scenario Analysis",
                "rows": [
                    ["Bull case", "收入增長及估值倍數改善", "盈利上修", "市場風險偏好回升"],
                    ["Base case", "業務維持穩定", "估值接近中位", "等待業績確認"],
                    ["Bear case", "收入或利潤率下滑", "估值收縮", "高槓桿或現金流壓力"],
                ],
                "triggers": ["盈利預警", "現金流惡化", "政策或融資環境轉差", "成交量急跌並跌穿重要支持位"],
            }

        rows = []
        for name, item in scenarios.items():
            rows.append([
                self._scenario_name(name),
                item.get("description", ""),
                item.get("implied_price", ""),
                item.get("key_catalyst", ""),
            ])
        return {
            "title": "Scenario Analysis",
            "rows": rows,
            "triggers": ["盈利預警", "現金流惡化", "債務再融資壓力", "政策或市場情緒急劇轉弱"],
        }

    def _build_portfolio_view(
        self,
        portfolio: Dict[str, Any],
        risk: Dict[str, Any],
        rating: str,
    ) -> Dict[str, Any]:
        risk_score = _num(risk.get("composite_risk_score"), 5)
        if portfolio.get("data_confidence") == INVALID or risk.get("data_confidence") == INVALID:
            return {
                "title": "Portfolio & Risk Control View",
                "investor_suitability": "資料驗證未完成，不提供投資者適合性判斷。",
                "position_sizing": "不適用。",
                "risk_control": "請先核對股票代號及市場資料來源。",
                "action_category": "停止進階分析",
                "no_advice": INVALID_PDF_NOTICE,
            }
        return {
            "title": "Portfolio & Risk Control View",
            "investor_suitability": (
                "較適合具備中等風險承受能力、願意以觀察名單方式跟蹤基本面及估值修復的投資者。"
                if risk_score <= 6
                else "較適合高風險承受能力投資者；一般投資者宜降低倉位或等待風險改善。"
            ),
            "position_sizing": f"模型參考倉位為{_fmt_pct(portfolio.get('suggested_position_pct'))}，需按個人投資組合、流動性及風險承受能力調整。",
            "risk_control": "可設定定期檢討點，包括業績公布、債務變化、現金流轉弱、股價跌穿關鍵區間或重大公告。",
            "action_category": rating,
            "no_advice": "以上內容只作教育及研究用途，不構成買入、沽出或持有任何證券的建議。",
        }

    def _build_ic_conclusion(
        self,
        ic: Dict[str, Any],
        risk: Dict[str, Any],
        rating: str,
        llm_warning: str,
        fin: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        fin = fin or {}
        if risk.get("data_confidence") == INVALID or fin.get("data_confidence") == INVALID:
            return {
                "title": "Investment Committee Final Conclusion",
                "final_decision": "無法評估",
                "why": INVALID_MARKET_DATA_MESSAGE,
                "monitor_next": ["核對股票代號", "確認市場資料供應商是否支援該代號", "重新提交有效香港股票代號"],
                "data_limitations": INVALID_PDF_NOTICE,
                "data_completeness_note": INVALID_PDF_NOTICE,
                "llm_warning": llm_warning,
                "multi_agent_statement": "本系統未能取得有效市場資料，因此不生成公司或投資敘事。",
            }
        completeness_note = "資料完整度提示：部分市場或財務資料未能取得，系統已使用保守假設進行分析。" if fin.get("missing_data_flags") else ""
        return {
            "title": "Investment Committee Final Conclusion",
            "final_decision": rating,
            "why": f"最終分類主要基於加權風險分數{_num(risk.get('composite_risk_score'), 5):.1f}/10、估值區間、財務健康度及市場訊號的綜合判斷。",
            "monitor_next": [
                "下一期業績中的收入增長、毛利率及淨利率變化",
                "經營現金流、自由現金流及債務再融資情況",
                "成交量、股價相對52週區間及市場風險偏好",
                "公司公告、政策變化及行業需求訊號",
            ],
            "data_limitations": "如即時市場資料、最新公告或完整年報資料未能取得，系統會以結構化假設補足分析框架；正式投資判斷仍需核對最新公開資料。",
            "data_completeness_note": completeness_note,
            "llm_warning": llm_warning,
            "multi_agent_statement": f"經 Multi-Agent Team 綜合討論後，本系統將該股票列為：{rating}",
        }

    def _build_disclaimer(self) -> Dict[str, str]:
        return {
            "title": "Disclaimer",
            "content": (
                "本報告由 Buildway Tech (HK) Limited 的 AI Multi-Agent Financial Intelligence System 生成，"
                "僅供教育、研究及客戶試用參考，不構成投資建議、招攬、要約或任何受規管財務意見。"
                "所有估值、風險分數及情景分析均由Python模型根據可取得資料及假設計算，"
                "投資者在作出任何投資決定前，應自行核實資料並諮詢持牌專業顧問。"
            ),
        }

    def _strip_placeholder_values(self, value: Any) -> Any:
        if isinstance(value, dict):
            cleaned: Dict[str, Any] = {}
            for key, item in value.items():
                cleaned_item = self._strip_placeholder_values(item)
                if cleaned_item is not None:
                    cleaned[key] = cleaned_item
            return cleaned
        if isinstance(value, list):
            return [
                cleaned_item
                for item in value
                if (cleaned_item := self._strip_placeholder_values(item)) is not None
            ]
        if isinstance(value, tuple):
            cleaned_tuple = tuple(self._strip_placeholder_values(item) for item in value)
            if len(cleaned_tuple) >= 2 and cleaned_tuple[1] is None:
                return None
            return cleaned_tuple
        if isinstance(value, str):
            text = value.strip()
            if not _valid_text(text):
                return None
            return text
        return value

    def _top_risk_name(self, risk: Dict[str, Any]) -> str:
        scores = risk.get("dimension_scores", {})
        if not scores:
            return "資料不足風險"
        top_key = max(scores, key=lambda key: _num(scores[key]))
        return self._clean_risk_dimension(top_key)

    def _clean_risk_dimension(self, raw: str) -> str:
        text = str(raw)
        rules = [
            ("liquidity", "流動性風險"),
            ("debt", "債務風險"),
            ("cash", "現金流風險"),
            ("market", "市場風險"),
            ("policy", "政策風險"),
            ("sector", "香港行業風險"),
            ("downside", "下行情景風險"),
        ]
        lowered = text.lower()
        for needle, label in rules:
            if needle in lowered:
                return label
        labels = ["流動性風險", "債務風險", "現金流風險", "市場風險", "政策風險", "香港行業風險", "下行情景風險"]
        index = abs(hash(text)) % len(labels)
        return labels[index]

    def _heat(self, score: float) -> str:
        if score <= 3:
            return "低"
        if score <= 6:
            return "中"
        if score <= 8:
            return "高"
        return "極高"

    def _scenario_name(self, raw: str) -> str:
        text = str(raw).lower()
        if "bull" in text or "up" in text:
            return "Bull case"
        if "bear" in text or "down" in text:
            return "Bear case"
        if "base" in text:
            return "Base case"
        if not hasattr(self, "_scenario_counter"):
            self._scenario_counter = 0
        names = ["Bull case", "Base case", "Bear case"]
        name = names[self._scenario_counter % len(names)]
        self._scenario_counter += 1
        return name
