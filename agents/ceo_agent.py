"""
agents/ceo_agent.py
Buildway Tech (HK) Limited — CEO Agent
Role: Main coordinator — receives user request, orchestrates all agents,
combines outputs into a unified report package
"""

import logging
from typing import Dict, Any, Optional, List
from core.agent_personas import get_persona
from core.config import APP_VERSION, BUILD_STAGE
from core.safe_math import safe_number
from core.utils import normalize_hk_ticker, get_timestamp
from data.sample_data import get_sample_market_data, get_sample_financial_history, get_sample_news_sentiment

from agents.market_data_agent import MarketDataAgent
from agents.financial_analyst_agent import FinancialAnalystAgent
from agents.risk_management_agent import RiskManagementAgent
from agents.news_intelligence_agent import NewsIntelligenceAgent
from agents.hk_ipo_agent import HKIPOAgent
from agents.portfolio_manager_agent import PortfolioManagerAgent
from agents.investment_committee_agent import InvestmentCommitteeAgent


logger = logging.getLogger(__name__)


class CEOAgent:
    """
    CEO Agent — Master Coordinator
    Orchestrates the full multi-agent analysis pipeline.
    Receives user input, delegates to specialist agents, assembles final report package.
    """

    AGENT_NAME = "首席執行官代理"
    AGENT_ROLE = "主協調員：接收用戶請求，分配工作給各專業代理，整合最終報告"

    def __init__(self):
        # Instantiate all specialist agents
        self.market_agent = MarketDataAgent()
        self.financial_agent = FinancialAnalystAgent()
        self.risk_agent = RiskManagementAgent()
        self.news_agent = NewsIntelligenceAgent()
        self.ipo_agent = HKIPOAgent()
        self.portfolio_agent = PortfolioManagerAgent()
        self.ic_agent = InvestmentCommitteeAgent()
        self.agent_status: Dict[str, str] = {}
        self.agent_error_log: List[str] = []

    def run_agent_safely(self, agent_name, agent_callable, fallback_data):
        """Run an agent without allowing one failure to stop orchestration."""
        self.agent_status[agent_name] = "執行中"
        try:
            result = agent_callable()
            self.agent_status[agent_name] = "完成"
            return result
        except Exception as exc:
            logger.exception("%s failed: %s", agent_name, exc)
            # Fallback succeeded → 備援 (not 失敗, since we have a result)
            self.agent_status[agent_name] = "備援"
            self.agent_error_log.append(f"{agent_name} 備援啟動: {str(exc)}")
            if isinstance(fallback_data, dict):
                fallback = dict(fallback_data)
                fallback["status"] = "fallback"
                fallback["failed_agent"] = agent_name
                fallback["warning"] = fallback.get("warning") or "系統已使用備援分析流程。"
                return fallback
            return fallback_data

    def run_analysis(
        self,
        ticker: str,
        company_name: Optional[str] = None,
        risk_preference: str = "中等",
        report_type: str = "香港股票智能分析報告",
        portfolio_size_hkd: Optional[float] = None,
        manual_news: Optional[List[Dict]] = None,
        progress_callback=None,
    ) -> Dict[str, Any]:
        """
        Main entry point. Run the full multi-agent analysis pipeline.

        Args:
            ticker: HK stock code (e.g. '3416' or '3416.HK')
            company_name: Optional company name override
            risk_preference: '保守' | '中等' | '進取'
            portfolio_size_hkd: Optional portfolio size for position sizing
            manual_news: Optional list of manually entered news items
            progress_callback: Optional callable(step, total, message) for UI progress

        Returns:
            Complete report package dict
        """
        normalized_ticker = normalize_hk_ticker(ticker)
        analysis_context = {
            "stock_code": normalized_ticker,
            "company_name": company_name or f"{normalized_ticker} 公司",
            "investor_style": risk_preference,
            "report_type": report_type,
            "language": "zh-HK",
        }
        print(f"[CEO Agent] Received stock_code = {analysis_context['stock_code']}")
        self.agent_status = {
            "CEO Agent": "進行中",
            "Market Data Agent": "等待",
            "Financial Analyst Agent": "等待",
            "Risk Agent": "等待",
            "News Intelligence Agent": "等待",
            "Portfolio Manager Agent": "等待",
            "Investment Committee Agent": "等待",
        }
        self.agent_error_log = []
        total_steps = 7

        def _progress(step: int, message: str):
            if progress_callback:
                progress_callback(step, total_steps, message)

        # ── Step 1: Market Data ───────────────────────────────────────────────
        _progress(1, f"📊 市場數據代理：正在獲取 {normalized_ticker} 市場數據...")
        market_data = self.run_agent_safely(
            "Market Data Agent",
            lambda: self.market_agent.fetch(
                normalized_ticker,
                company_name,
                analysis_context=analysis_context,
            ),
            self._fallback_market_data(analysis_context),
        )
        market_data["ticker"] = analysis_context["stock_code"]
        financial_history = self.run_agent_safely(
            "Market Data Agent",
            lambda: self.market_agent.get_financial_history(normalized_ticker),
            self._fallback_financial_history(analysis_context),
        )
        financial_history["ticker"] = analysis_context["stock_code"]

        # ── Step 2: Financial Analysis ────────────────────────────────────────
        _progress(2, "💹 財務分析師代理：正在進行DCF及估值分析...")
        # Debug logging for 3416 data issues
        _base_code = analysis_context["stock_code"].replace(".HK", "").lstrip("0") or "0"
        if _base_code in {"3416"}:
            print(f"[DEBUG 3416] market_data: {market_data}")
            print(f"[DEBUG 3416] financial_history: {financial_history}")
        financial_analysis = self.run_agent_safely(
            "Financial Analyst Agent",
            lambda: self.financial_agent.analyze(
                market_data,
                financial_history,
                analysis_context=analysis_context,
            ),
            self._fallback_financial_analysis(analysis_context),
        )

        # ── Step 3: Risk Analysis ─────────────────────────────────────────────
        _progress(3, "⚠️ 風險管理代理：正在評估多維度風險...")
        risk_analysis = self.run_agent_safely(
            "Risk Agent",
            lambda: self.risk_agent.analyze(
                market_data,
                financial_analysis,
                risk_preference,
                analysis_context=analysis_context,
            ),
            self._fallback_risk_analysis(analysis_context, risk_preference),
        )

        # ── Step 4: News Intelligence ─────────────────────────────────────────
        _progress(4, "📰 新聞情報代理：正在分析市場情緒...")
        news_analysis = self.run_agent_safely(
            "News Intelligence Agent",
            lambda: self.news_agent.analyze(
                normalized_ticker,
                company_name=market_data.get("company_name"),
                manual_news=manual_news,
                analysis_context=analysis_context,
            ),
            self._fallback_news_analysis(analysis_context),
        )

        # ── Step 5: Portfolio Management ──────────────────────────────────────
        _progress(5, "📁 投資組合管理代理：正在計算倉位建議...")
        portfolio_analysis = self.run_agent_safely(
            "Portfolio Manager Agent",
            lambda: self.portfolio_agent.analyze(
                market_data,
                risk_analysis,
                financial_analysis,
                risk_preference=risk_preference,
                portfolio_size_hkd=portfolio_size_hkd,
                analysis_context=analysis_context,
            ),
            self._fallback_portfolio_analysis(analysis_context, risk_preference),
        )

        # ── Step 6: Investment Committee ──────────────────────────────────────
        _progress(6, "🏛️ 投資委員會代理：正在進行最終評審...")
        ic_result = self.run_agent_safely(
            "Investment Committee Agent",
            lambda: self.ic_agent.deliberate(
                market_data,
                financial_analysis,
                risk_analysis,
                news_analysis,
                portfolio_analysis,
                analysis_context=analysis_context,
            ),
            self._fallback_ic_result(analysis_context),
        )
        self.agent_status["CEO Agent"] = "完成"
        agent_opinions = self._build_agent_opinions(
            analysis_context,
            market_data,
            financial_analysis,
            risk_analysis,
            news_analysis,
            portfolio_analysis,
            ic_result,
        )

        # ── Step 7: Assemble Report Package ───────────────────────────────────
        _progress(7, "📄 正在整合報告...")
        report_package = self._assemble_report_package(
            ticker=normalized_ticker,
            analysis_context=analysis_context,
            market_data=market_data,
            financial_history=financial_history,
            financial_analysis=financial_analysis,
            risk_analysis=risk_analysis,
            news_analysis=news_analysis,
            portfolio_analysis=portfolio_analysis,
            ic_result=ic_result,
            agent_opinions=agent_opinions,
            risk_preference=risk_preference,
        )

        return report_package

    def _assemble_report_package(
        self,
        ticker: str,
        analysis_context: Dict[str, Any],
        market_data: Dict[str, Any],
        financial_history: Dict[str, Any],
        financial_analysis: Dict[str, Any],
        risk_analysis: Dict[str, Any],
        news_analysis: Dict[str, Any],
        portfolio_analysis: Dict[str, Any],
        ic_result: Dict[str, Any],
        agent_opinions: List[Dict[str, Any]],
        risk_preference: str,
    ) -> Dict[str, Any]:
        """Assemble all agent outputs into a unified report package."""
        return {
            # ── Metadata ──────────────────────────────────────────────────────
            "report_metadata": {
                "ticker": ticker,
                "stock_code": analysis_context["stock_code"],
                "company_name": analysis_context.get("company_name") or market_data.get("company_name", ticker),
                "generated_at": get_timestamp(),
                "report_type": analysis_context.get("report_type", "香港股票智能分析報告"),
                "version": APP_VERSION,
                "build_stage": BUILD_STAGE,
                "brand": "Buildway Tech (HK) Limited",
                "risk_preference": risk_preference,
                "analysis_context": analysis_context,
                "is_demo": market_data.get("is_demo", True),
                "data_source": market_data.get("data_source", "示範數據"),
                "data_completeness_note": "資料完整度提示：部分市場或財務資料未能取得，系統已使用保守假設進行分析。" if financial_analysis.get("missing_data_flags") else "",
                "agent_status": dict(self.agent_status),
                "agent_error_log": list(self.agent_error_log),
                "failed_agents": self._failed_agents(),
            },

            # ── Agent Outputs ─────────────────────────────────────────────────
            "market_data": market_data,
            "financial_history": financial_history,
            "financial_analysis": financial_analysis,
            "risk_analysis": risk_analysis,
            "news_analysis": news_analysis,
            "portfolio_analysis": portfolio_analysis,
            "ic_result": ic_result,
            "agent_opinions": agent_opinions,
            "agent_status": dict(self.agent_status),
            "agent_error_log": list(self.agent_error_log),

            # ── Top-level Summary (for quick access) ──────────────────────────
            "summary": {
                "ticker": ticker,
                "stock_code": analysis_context["stock_code"],
                "company_name": analysis_context.get("company_name") or market_data.get("company_name", ticker),
                "current_price": market_data.get("current_price", 0),
                "sector": market_data.get("sector", ""),
                "verdict": ic_result.get("verdict", "中性"),
                "verdict_icon": ic_result.get("verdict_meta", {}).get("icon", "🟡"),
                "risk_score": risk_analysis.get("composite_risk_score", 5),
                "risk_label": risk_analysis.get("risk_label", "中等風險 🟡"),
                "valuation_low": financial_analysis.get("valuation_range", {}).get("low", 0),
                "valuation_mid": financial_analysis.get("valuation_range", {}).get("mid", 0),
                "valuation_high": financial_analysis.get("valuation_range", {}).get("high", 0),
                "health_grade": financial_analysis.get("health_score", {}).get("grade", "N/A"),
                "suggested_position_pct": portfolio_analysis.get("suggested_position_pct", 0),
                "executive_summary": ic_result.get("executive_summary", ""),
            },

            # ── IPO Module Status ─────────────────────────────────────────────
            "ipo_module": self.ipo_agent.get_status(),
        }

    def _failed_agents(self) -> List[str]:
        return [agent for agent, status in self.agent_status.items() if status == "失敗"]

    def _fallback_market_data(self, analysis_context: Dict[str, Any]) -> Dict[str, Any]:
        stock_code = analysis_context["stock_code"]
        data = get_sample_market_data(stock_code)
        data.update({
            "ticker": stock_code,
            "company_name": analysis_context.get("company_name") or f"{stock_code} 公司",
            "status": "fallback",
            "summary": "市場數據暫時不可用",
            "warning": "系統已使用備援市場數據流程。",
            "missing_data_flags": ["market_data agent unavailable"],
        })
        return data

    def _fallback_financial_history(self, analysis_context: Dict[str, Any]) -> Dict[str, Any]:
        data = get_sample_financial_history(analysis_context["stock_code"])
        data.update({
            "status": "fallback",
            "warning": "系統已使用備援財務歷史數據。",
        })
        return data

    def _fallback_financial_analysis(self, analysis_context: Dict[str, Any]) -> Dict[str, Any]:
        stock_code = analysis_context["stock_code"]
        return {
            "ticker": stock_code,
            "status": "fallback",
            "summary": "財務分析暫時不可用",
            "warning": "系統已使用備援分析流程。",
            "valuation": "N/A",
            "confidence": 0,
            "is_demo": True,
            "metrics": {"net_debt": 0, "ev_ebitda": 0, "ev_revenue": 0, "dividend_yield": 0},
            "dcf": {"base_intrinsic_price": 0, "scenarios": {}},
            "comps": {"company_pe": 0, "company_pb": 0, "company_ev_ebitda": 0},
            "valuation_range": {
                "current_price": 0,
                "low": 0,
                "mid": 0,
                "high": 0,
                "upside_to_mid": 0,
                "upside_to_high": 0,
                "downside_to_low": 0,
                "verdict": "備援估值，不作方向性判斷",
            },
            "health_score": {"dimension_scores": {}, "overall_score": 0, "grade": "N/A"},
            "sector": "香港上市公司",
            "data_warning": "部分財務數據暫時不可用，以下分析已採用保守假設。",
            "missing_data_flags": ["financial_analysis agent unavailable"],
        }

    def _fallback_risk_analysis(self, analysis_context: Dict[str, Any], risk_preference: str) -> Dict[str, Any]:
        stock_code = analysis_context["stock_code"]
        dimension_scores = {
            "流動性風險": 6,
            "債務風險": 6,
            "現金流風險": 6,
            "市場風險": 6,
            "政策風險": 6,
            "香港行業風險": 6,
            "下行情景風險": 6,
        }
        weights = {key: 1 / len(dimension_scores) for key in dimension_scores}
        return {
            "ticker": stock_code,
            "status": "fallback",
            "summary": "風險分析暫時不可用",
            "warning": "系統已使用備援風險分析流程。",
            "confidence": 0,
            "is_demo": True,
            "composite_risk_score": 6.0,
            "risk_label": "中等風險",
            "risk_color": "#F39C12",
            "dimension_scores": dimension_scores,
            "risk_weights": weights,
            "narratives": {},
            "scenarios": {},
            "risk_preference": risk_preference,
            "recommendation_note": "備援風險評估採用保守中性假設。",
        }

    def _fallback_news_analysis(self, analysis_context: Dict[str, Any]) -> Dict[str, Any]:
        stock_code = analysis_context["stock_code"]
        data = get_sample_news_sentiment(stock_code)
        data.update({
            "ticker": stock_code,
            "status": "fallback",
            "summary": "新聞分析暫時不可用",
            "warning": "系統已使用備援新聞分析流程。",
            "confidence": 0,
            "sentiment_analysis": {
                "score": 0.5,
                "label": "中性",
                "confidence": "低",
                "positive_count": 0,
                "negative_count": 0,
                "neutral_count": 0,
            },
            "market_signals": [],
        })
        return data

    def _fallback_portfolio_analysis(self, analysis_context: Dict[str, Any], risk_preference: str) -> Dict[str, Any]:
        return {
            "ticker": analysis_context["stock_code"],
            "status": "fallback",
            "summary": "投資組合分析暫時不可用",
            "warning": "系統已使用備援倉位分析流程。",
            "confidence": 0,
            "is_demo": True,
            "risk_preference": risk_preference,
            "framework": {},
            "risk_score": 6,
            "suggested_position_pct": 0,
            "kelly_fraction": 0,
            "dollar_amounts": None,
            "risk_metrics": {},
            "portfolio_fit": {"portfolio_fits": {}, "best_fit": risk_preference, "health_grade": "N/A"},
            "educational_disclaimer": "備援倉位結果只作教育用途。",
            "position_rationale": "由於模組暫時不可用，系統不提供具體倉位建議。",
        }

    def _fallback_ic_result(self, analysis_context: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "ticker": analysis_context["stock_code"],
            "company_name": analysis_context.get("company_name") or f"{analysis_context['stock_code']} 公司",
            "status": "fallback",
            "summary": "投資委員會分析暫時不可用",
            "warning": "系統已使用備援最終評審流程。",
            "confidence": 0,
            "is_demo": True,
            "timestamp": get_timestamp(),
            "verdict": "中性",
            "verdict_meta": {"icon": "🟡", "color": "#F39C12", "description": "備援結論，保持中性。"},
            "ic_scores": {},
            "investment_thesis": ["部分 Agent 分析未能完成，系統已自動切換至備援分析流程。"],
            "key_risks": [],
            "key_catalysts": [],
            "executive_summary": "部分 Agent 分析未能完成，系統已自動切換至備援分析流程。",
            "risk_warning": "備援結論只作教育用途。",
            "data_quality_note": "部分分析模組暫時不可用。",
        }

    def _build_agent_opinions(
        self,
        analysis_context: Dict[str, Any],
        market_data: Dict[str, Any],
        financial_analysis: Dict[str, Any],
        risk_analysis: Dict[str, Any],
        news_analysis: Dict[str, Any],
        portfolio_analysis: Dict[str, Any],
        ic_result: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Build autonomous agent views for the discussion table."""
        stock_code = analysis_context["stock_code"]
        price = safe_number(market_data.get("current_price"))
        volume = safe_number(market_data.get("volume"))
        risk_score = safe_number(risk_analysis.get("composite_risk_score"), 5)
        valuation = financial_analysis.get("valuation_range", {})
        upside = safe_number(valuation.get("upside_to_mid"))
        sentiment = news_analysis.get("sentiment_analysis", {})
        position = safe_number(portfolio_analysis.get("suggested_position_pct"))
        health = financial_analysis.get("health_score", {})
        missing_flags = financial_analysis.get("missing_data_flags", [])

        positive_rating_allowed = risk_score < 7 and not (risk_score >= 6 and upside < 0.1)
        disagreement = "Risk Agent較保守，Financial Agent較重視估值上行。" if upside > 0 and risk_score >= 6 else "主要代理意見大致一致。"

        rows = [
            ("CEO Agent", f"{stock_code} 的決策需要同時看估值、風險與倉位，不宜只因單一指標作結論。",
             "多代理框架已完成交叉檢查。", "若資料不完整，結論必須保持保守。", 8 if not missing_flags else 6, "neutral"),
            ("Market Data Agent", f"現價約HK${price:.2f}，成交量約{volume:,.0f}，短線需留意波動與流動性。",
             "市場價格及成交資料提供即時參考。", "成交或價格訊號可能快速轉弱。", 7 if price > 0 else 4, "neutral"),
            ("Financial Analyst Agent", f"估值中位數相對現價約{upside * 100:.1f}%；財務健康評級為{health.get('grade', 'N/A')}。",
             "若現價低於估值中位數，存在估值修復空間。", "收入、利潤、現金流或估值倍數缺失會降低可信度。", 7 if not missing_flags else 5, "positive" if upside > 0.1 else "neutral"),
            ("Risk Management Agent", f"綜合風險分數為{risk_score:.1f}/10，需先問最壞情況會否傷害本金。",
             "若流動性及槓桿受控，下行壓力可管理。", "高槓桿、政策風險或黑天鵝事件會壓低評級。", 8 if risk_score >= 6 else 7, "negative" if risk_score >= 7 else "neutral"),
            ("News Intelligence Agent", f"新聞情緒分數約{safe_number(sentiment.get('score'), 0.5):.2f}，暫以催化因素和敘事變化為核心觀察。",
             "正面公告或行業事件可改善市場敘事。", "缺乏即時新聞來源時，事件判斷需保留折讓。", 6, "neutral"),
            ("Portfolio Manager Agent", f"建議倉位約{position * 100:.1f}%，重點是避免過度集中及保留風險緩衝。",
             "小倉位可保留參與上行的彈性。", "單一股票過度集中會放大回撤。", 8, "neutral"),
            ("Investment Committee Agent", f"{disagreement} 最終評級需以風險分數與代理共識約束。",
             "若風險受控且估值合理，可維持觀察或中性偏正面。", "Risk Agent信心低或風險分數偏高時，不應給出過度正面結論。", 7, "positive" if positive_rating_allowed and upside > 0 else "neutral"),
        ]

        opinions = []
        for agent, view, positive, concern, confidence, impact in rows:
            persona = get_persona(agent)
            opinions.append({
                "Agent": agent,
                "性格定位": persona["positioning"],
                "核心觀點": view,
                "正面因素": positive,
                "主要憂慮": concern,
                "信心分數": f"{confidence}/10",
                "對評級影響": impact,
            })
        return opinions

    def get_agent_roster(self) -> List[Dict[str, str]]:
        """Return the full agent roster for display."""
        return [
            {"name": self.AGENT_NAME, "role": self.AGENT_ROLE, "status": "活躍"},
            {"name": self.market_agent.AGENT_NAME, "role": self.market_agent.AGENT_ROLE, "status": "活躍"},
            {"name": self.financial_agent.AGENT_NAME, "role": self.financial_agent.AGENT_ROLE, "status": "活躍"},
            {"name": self.risk_agent.AGENT_NAME, "role": self.risk_agent.AGENT_ROLE, "status": "活躍"},
            {"name": self.news_agent.AGENT_NAME, "role": self.news_agent.AGENT_ROLE, "status": "活躍"},
            {"name": self.ipo_agent.AGENT_NAME, "role": self.ipo_agent.AGENT_ROLE, "status": "Phase 2.5 預留"},
            {"name": self.portfolio_agent.AGENT_NAME, "role": self.portfolio_agent.AGENT_ROLE, "status": "活躍"},
            {"name": self.ic_agent.AGENT_NAME, "role": self.ic_agent.AGENT_ROLE, "status": "活躍"},
        ]
