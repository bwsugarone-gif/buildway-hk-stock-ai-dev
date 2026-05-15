"""
agents/portfolio_manager_agent.py
Buildway Tech (HK) Limited — Portfolio Manager Agent
Role: Position sizing logic and portfolio allocation suggestions
Educational only — not financial advice
"""

from typing import Dict, Any, Optional
from core.utils import safe_divide, clamp, format_percentage


class PortfolioManagerAgent:
    """
    Portfolio Manager Agent
    Suggests position sizing based on risk score and investor profile.
    All output is educational and must not be construed as financial advice.
    """

    AGENT_NAME = "投資組合管理代理"
    AGENT_ROLE = "提供倉位管理建議及投資組合配置邏輯（教育用途，非投資建議）"

    # Position sizing frameworks by risk profile
    POSITION_FRAMEWORKS = {
        "保守": {
            "max_single_position": 0.05,   # 5% max per stock
            "max_sector_exposure": 0.20,    # 20% max per sector
            "cash_buffer": 0.30,            # 30% cash minimum
            "stop_loss": 0.08,              # 8% stop loss
            "description": "保守型：低波動、高股息、藍籌為主",
        },
        "中等": {
            "max_single_position": 0.10,   # 10% max per stock
            "max_sector_exposure": 0.30,    # 30% max per sector
            "cash_buffer": 0.15,            # 15% cash minimum
            "stop_loss": 0.12,              # 12% stop loss
            "description": "中等型：平衡增長與防禦，分散配置",
        },
        "進取": {
            "max_single_position": 0.15,   # 15% max per stock
            "max_sector_exposure": 0.40,    # 40% max per sector
            "cash_buffer": 0.05,            # 5% cash minimum
            "stop_loss": 0.20,              # 20% stop loss
            "description": "進取型：追求增長，接受較高波動",
        },
    }

    def analyze(
        self,
        market_data: Dict[str, Any],
        risk_analysis: Dict[str, Any],
        financial_analysis: Dict[str, Any],
        risk_preference: str = "中等",
        portfolio_size_hkd: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Main entry point. Generate position sizing recommendation.
        portfolio_size_hkd: Optional total portfolio size in HKD for dollar amounts.
        """
        ticker = market_data.get("ticker", "N/A")
        risk_score = risk_analysis.get("composite_risk_score", 5)
        current_price = market_data.get("current_price", 0)

        framework = self.POSITION_FRAMEWORKS.get(risk_preference, self.POSITION_FRAMEWORKS["中等"])

        # Adjust position size based on risk score
        position_pct = self._calculate_position_size(risk_score, framework, risk_preference)

        # Kelly Criterion (simplified, educational)
        kelly = self._simplified_kelly(risk_analysis, financial_analysis)

        # Dollar amounts if portfolio size provided
        dollar_amounts = None
        if portfolio_size_hkd and portfolio_size_hkd > 0:
            dollar_amounts = self._calculate_dollar_amounts(
                portfolio_size_hkd, position_pct, current_price
            )

        # Risk-adjusted return metrics
        risk_metrics = self._compute_risk_metrics(market_data, risk_analysis, financial_analysis)

        # Portfolio fit assessment
        fit = self._assess_portfolio_fit(risk_score, risk_preference, financial_analysis)

        return {
            "ticker": ticker,
            "is_demo": market_data.get("is_demo", True),
            "risk_preference": risk_preference,
            "framework": framework,
            "risk_score": risk_score,
            "suggested_position_pct": position_pct,
            "kelly_fraction": kelly,
            "dollar_amounts": dollar_amounts,
            "risk_metrics": risk_metrics,
            "portfolio_fit": fit,
            "educational_disclaimer": self._get_disclaimer(),
            "position_rationale": self._build_rationale(
                risk_score, position_pct, risk_preference, framework
            ),
        }

    def _calculate_position_size(
        self,
        risk_score: float,
        framework: Dict,
        preference: str,
    ) -> float:
        """
        Calculate suggested position size as % of portfolio.
        Higher risk score = smaller position.
        """
        max_pos = framework["max_single_position"]

        # Scale down based on risk score (1=full size, 10=minimal)
        risk_multiplier = 1.0 - ((risk_score - 1) / 9) * 0.8  # 1.0 to 0.2

        position = max_pos * risk_multiplier

        # Round to nearest 0.5%
        position = round(position * 200) / 200

        return clamp(position, 0.01, max_pos)

    def _simplified_kelly(
        self,
        risk_analysis: Dict[str, Any],
        financial_analysis: Dict[str, Any],
    ) -> float:
        """
        Simplified Kelly Criterion for educational purposes.
        Kelly % = (bp - q) / b
        where b = odds, p = win probability, q = loss probability
        """
        scenarios = risk_analysis.get("scenarios", {})

        # Extract scenario probabilities and returns
        bull = scenarios.get("牛市情景", {})
        bear = scenarios.get("熊市情景", {})

        # Parse upside/downside
        try:
            upside = float(str(bull.get("upside", "+38%")).replace("%", "").replace("+", "")) / 100
        except (ValueError, TypeError):
            upside = 0.38

        try:
            downside = abs(float(str(bear.get("upside", "-32%")).replace("%", "").replace("-", ""))) / 100
        except (ValueError, TypeError):
            downside = 0.32

        # Simplified: assume 50/50 bull/bear (educational)
        p_win = 0.50
        p_loss = 0.50
        b = upside / max(downside, 0.01)

        kelly = (b * p_win - p_loss) / b
        kelly = clamp(kelly, 0, 0.25)  # cap at 25% (half-Kelly in practice)

        return round(kelly * 0.5, 3)  # half-Kelly for safety

    def _calculate_dollar_amounts(
        self,
        portfolio_size: float,
        position_pct: float,
        current_price: float,
    ) -> Dict[str, Any]:
        """Calculate dollar amounts for position sizing."""
        position_value = portfolio_size * position_pct
        shares = int(position_value / current_price) if current_price > 0 else 0

        # HK stocks trade in board lots (typically 500 or 1000 shares)
        # Simplified: assume 500 share lots
        board_lot = 500
        lots = max(1, round(shares / board_lot))
        actual_shares = lots * board_lot
        actual_value = actual_shares * current_price

        return {
            "portfolio_size_hkd": portfolio_size,
            "suggested_position_hkd": position_value,
            "suggested_shares": shares,
            "board_lots": lots,
            "actual_shares": actual_shares,
            "actual_value_hkd": actual_value,
            "note": "以500股為一手計算（示範用途，實際手數視乎個股而定）",
        }

    def _compute_risk_metrics(
        self,
        market_data: Dict[str, Any],
        risk_analysis: Dict[str, Any],
        financial_analysis: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Compute risk-adjusted return metrics."""
        beta = market_data.get("beta", 1.0) or 1.0
        dividend_yield = market_data.get("dividend_yield", 0) or 0
        risk_score = risk_analysis.get("composite_risk_score", 5)

        # Simplified Sharpe-like ratio (educational)
        # Assume risk-free rate = 4% (HK)
        risk_free = 0.04
        expected_return = dividend_yield + 0.08  # dividend + assumed capital gain
        excess_return = expected_return - risk_free
        volatility_proxy = beta * 0.20  # rough proxy

        sharpe_proxy = safe_divide(excess_return, volatility_proxy)

        # Risk-reward ratio from scenarios
        scenarios = risk_analysis.get("scenarios", {})
        bull_upside = 0.38
        bear_downside = 0.32
        risk_reward = safe_divide(bull_upside, bear_downside)

        return {
            "beta": beta,
            "dividend_yield": dividend_yield,
            "sharpe_proxy": round(sharpe_proxy, 2),
            "risk_reward_ratio": round(risk_reward, 2),
            "risk_score": risk_score,
            "note": "以上指標為教育性估算，非精確計算",
        }

    def _assess_portfolio_fit(
        self,
        risk_score: float,
        preference: str,
        financial_analysis: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Assess how well this stock fits different portfolio types."""
        health = financial_analysis.get("health_score", {})
        health_score = health.get("overall_score", 5)

        fits = {
            "保守型投資組合": "適合" if risk_score <= 4 and health_score >= 6 else
                             "謹慎" if risk_score <= 6 else "不適合",
            "中等型投資組合": "適合" if risk_score <= 6 else
                             "謹慎" if risk_score <= 8 else "不適合",
            "進取型投資組合": "適合" if risk_score <= 8 else "謹慎",
            "收息型投資組合": "適合" if financial_analysis.get("metrics", {}).get("dividend_yield", 0) >= 0.04 else "不適合",
            "增長型投資組合": "適合" if health_score >= 7 else "謹慎",
        }

        return {
            "portfolio_fits": fits,
            "best_fit": preference,
            "health_grade": health.get("grade", "N/A"),
        }

    def _build_rationale(
        self,
        risk_score: float,
        position_pct: float,
        preference: str,
        framework: Dict,
    ) -> str:
        """Build a plain-language rationale for the position sizing."""
        pct_str = f"{position_pct * 100:.1f}%"
        max_str = f"{framework['max_single_position'] * 100:.0f}%"
        stop_str = f"{framework['stop_loss'] * 100:.0f}%"

        if risk_score <= 3:
            risk_desc = "風險評分偏低，財務狀況穩健"
        elif risk_score <= 6:
            risk_desc = "風險評分中等，需保持適度分散"
        else:
            risk_desc = "風險評分偏高，建議嚴格控制倉位"

        return (
            f"基於{preference}型投資框架，{risk_desc}。\n"
            f"建議倉位：{pct_str}（{preference}型最大單一倉位：{max_str}）。\n"
            f"建議止損位：入場價下方 {stop_str}。\n"
            f"請確保此倉位符合您的整體投資組合分散原則。"
        )

    def _get_disclaimer(self) -> str:
        return (
            "【重要聲明】以上倉位建議僅供教育及參考用途，"
            "不構成任何投資建議或財務意見。"
            "實際投資決定應基於個人財務狀況、風險承受能力及專業顧問意見。"
            "投資涉及風險，過往表現不代表未來回報。"
        )
