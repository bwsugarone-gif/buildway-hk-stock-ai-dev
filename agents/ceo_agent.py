"""
agents/ceo_agent.py
Buildway Tech (HK) Limited — CEO Agent
Role: Main coordinator — receives user request, orchestrates all agents,
combines outputs into a unified report package
"""

from typing import Dict, Any, Optional, List
from core.utils import normalize_hk_ticker, get_timestamp

from agents.market_data_agent import MarketDataAgent
from agents.financial_analyst_agent import FinancialAnalystAgent
from agents.risk_management_agent import RiskManagementAgent
from agents.news_intelligence_agent import NewsIntelligenceAgent
from agents.hk_ipo_agent import HKIPOAgent
from agents.portfolio_manager_agent import PortfolioManagerAgent
from agents.investment_committee_agent import InvestmentCommitteeAgent


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

    def run_analysis(
        self,
        ticker: str,
        company_name: Optional[str] = None,
        risk_preference: str = "中等",
        portfolio_size_hkd: Optional[float] = None,
        manual_news: Optional[List[Dict]] = None,
        progress_callback=None,
    ) -> Dict[str, Any]:
        """
        Main entry point. Run the full multi-agent analysis pipeline.

        Args:
            ticker: HK stock code (e.g. '3311' or '3311.HK')
            company_name: Optional company name override
            risk_preference: '保守' | '中等' | '進取'
            portfolio_size_hkd: Optional portfolio size for position sizing
            manual_news: Optional list of manually entered news items
            progress_callback: Optional callable(step, total, message) for UI progress

        Returns:
            Complete report package dict
        """
        normalized_ticker = normalize_hk_ticker(ticker)
        total_steps = 7

        def _progress(step: int, message: str):
            if progress_callback:
                progress_callback(step, total_steps, message)

        # ── Step 1: Market Data ───────────────────────────────────────────────
        _progress(1, f"📊 市場數據代理：正在獲取 {normalized_ticker} 市場數據...")
        market_data = self.market_agent.fetch(normalized_ticker, company_name)
        financial_history = self.market_agent.get_financial_history(normalized_ticker)

        # ── Step 2: Financial Analysis ────────────────────────────────────────
        _progress(2, "💹 財務分析師代理：正在進行DCF及估值分析...")
        financial_analysis = self.financial_agent.analyze(market_data, financial_history)

        # ── Step 3: Risk Analysis ─────────────────────────────────────────────
        _progress(3, "⚠️ 風險管理代理：正在評估多維度風險...")
        risk_analysis = self.risk_agent.analyze(
            market_data, financial_analysis, risk_preference
        )

        # ── Step 4: News Intelligence ─────────────────────────────────────────
        _progress(4, "📰 新聞情報代理：正在分析市場情緒...")
        news_analysis = self.news_agent.analyze(
            normalized_ticker,
            company_name=market_data.get("company_name"),
            manual_news=manual_news,
        )

        # ── Step 5: Portfolio Management ──────────────────────────────────────
        _progress(5, "📁 投資組合管理代理：正在計算倉位建議...")
        portfolio_analysis = self.portfolio_agent.analyze(
            market_data,
            risk_analysis,
            financial_analysis,
            risk_preference=risk_preference,
            portfolio_size_hkd=portfolio_size_hkd,
        )

        # ── Step 6: Investment Committee ──────────────────────────────────────
        _progress(6, "🏛️ 投資委員會代理：正在進行最終評審...")
        ic_result = self.ic_agent.deliberate(
            market_data,
            financial_analysis,
            risk_analysis,
            news_analysis,
            portfolio_analysis,
        )

        # ── Step 7: Assemble Report Package ───────────────────────────────────
        _progress(7, "📄 正在整合報告...")
        report_package = self._assemble_report_package(
            ticker=normalized_ticker,
            market_data=market_data,
            financial_history=financial_history,
            financial_analysis=financial_analysis,
            risk_analysis=risk_analysis,
            news_analysis=news_analysis,
            portfolio_analysis=portfolio_analysis,
            ic_result=ic_result,
            risk_preference=risk_preference,
        )

        return report_package

    def _assemble_report_package(
        self,
        ticker: str,
        market_data: Dict[str, Any],
        financial_history: Dict[str, Any],
        financial_analysis: Dict[str, Any],
        risk_analysis: Dict[str, Any],
        news_analysis: Dict[str, Any],
        portfolio_analysis: Dict[str, Any],
        ic_result: Dict[str, Any],
        risk_preference: str,
    ) -> Dict[str, Any]:
        """Assemble all agent outputs into a unified report package."""
        return {
            # ── Metadata ──────────────────────────────────────────────────────
            "report_metadata": {
                "ticker": ticker,
                "company_name": market_data.get("company_name", ticker),
                "generated_at": get_timestamp(),
                "report_type": "香港股票智能分析報告",
                "version": "DEV v1.0",
                "brand": "Buildway Tech (HK) Limited",
                "risk_preference": risk_preference,
                "is_demo": market_data.get("is_demo", True),
                "data_source": market_data.get("data_source", "示範數據"),
            },

            # ── Agent Outputs ─────────────────────────────────────────────────
            "market_data": market_data,
            "financial_history": financial_history,
            "financial_analysis": financial_analysis,
            "risk_analysis": risk_analysis,
            "news_analysis": news_analysis,
            "portfolio_analysis": portfolio_analysis,
            "ic_result": ic_result,

            # ── Top-level Summary (for quick access) ──────────────────────────
            "summary": {
                "ticker": ticker,
                "company_name": market_data.get("company_name", ticker),
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
