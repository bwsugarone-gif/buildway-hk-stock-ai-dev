"""
agents/risk_management_agent.py
Buildway Tech (HK) Limited — Risk Management Agent
Role: Multi-dimensional risk analysis for HK stocks
Produces risk score 1-10 across 7 risk dimensions
"""

from typing import Dict, Any
from core.utils import safe_divide, clamp, get_risk_label, get_risk_color


class RiskManagementAgent:
    """
    Risk Management Agent
    Analyzes liquidity, debt, cash flow, market, policy, HK sector, and downside risks.
    Produces a composite risk score from 1 (lowest) to 10 (highest).
    """

    AGENT_NAME = "風險管理代理"
    AGENT_ROLE = "分析流動性、債務、現金流、市場、政策、香港行業及下行風險，生成綜合風險評分"

    # Risk dimension weights (must sum to 1.0)
    RISK_WEIGHTS = {
        "流動性風險":   0.18,
        "債務風險":     0.20,
        "現金流風險":   0.17,
        "市場風險":     0.15,
        "政策風險":     0.10,
        "香港行業風險": 0.10,
        "下行情景風險": 0.10,
    }

    # HK sector policy risk baseline (1=low, 10=high)
    SECTOR_POLICY_RISK = {
        "科技 / 互聯網": 7,
        "金融 / 銀行":   5,
        "地產":          8,
        "建築 / 基建":   4,
        "能源":          5,
        "消費":          4,
        "醫療健康":      4,
        "綜合企業":      5,
    }

    def analyze(
        self,
        market_data: Dict[str, Any],
        financial_analysis: Dict[str, Any],
        risk_preference: str = "中等",
    ) -> Dict[str, Any]:
        """
        Main entry point. Run full risk analysis.
        risk_preference: '保守' | '中等' | '進取'
        """
        ticker = market_data.get("ticker", "N/A")
        sector = market_data.get("sector", "綜合企業")

        # Score each risk dimension (1=low risk, 10=high risk)
        dimension_scores = {
            "流動性風險":   self._liquidity_risk(market_data),
            "債務風險":     self._debt_risk(market_data),
            "現金流風險":   self._cashflow_risk(market_data, financial_analysis),
            "市場風險":     self._market_risk(market_data),
            "政策風險":     self._policy_risk(sector),
            "香港行業風險": self._hk_sector_risk(sector, market_data),
            "下行情景風險": self._downside_scenario_risk(market_data, financial_analysis),
        }

        # Weighted composite score
        composite_score = sum(
            score * self.RISK_WEIGHTS[dim]
            for dim, score in dimension_scores.items()
        )
        composite_score = round(clamp(composite_score, 1, 10), 1)

        # Risk narratives
        narratives = self._build_narratives(dimension_scores, market_data, sector)

        # Downside scenarios
        scenarios = self._build_scenarios(market_data, financial_analysis)

        return {
            "ticker": ticker,
            "is_demo": market_data.get("is_demo", True),
            "composite_risk_score": composite_score,
            "risk_label": get_risk_label(int(composite_score)),
            "risk_color": get_risk_color(int(composite_score)),
            "dimension_scores": dimension_scores,
            "risk_weights": self.RISK_WEIGHTS,
            "narratives": narratives,
            "scenarios": scenarios,
            "risk_preference": risk_preference,
            "recommendation_note": self._preference_note(composite_score, risk_preference),
        }

    # ─── Individual Risk Scorers ──────────────────────────────────────────────

    def _liquidity_risk(self, data: Dict[str, Any]) -> int:
        """Score liquidity risk based on current ratio and cash position."""
        cr = data.get("current_ratio", 1.0) or 1.0
        cash = data.get("cash", 0) or 0
        total_debt = data.get("total_debt", 1) or 1

        cash_ratio = safe_divide(cash, total_debt)

        score = 5  # baseline
        if cr >= 2.0:
            score -= 2
        elif cr >= 1.5:
            score -= 1
        elif cr < 1.0:
            score += 3
        elif cr < 1.2:
            score += 1

        if cash_ratio >= 0.3:
            score -= 1
        elif cash_ratio < 0.1:
            score += 2

        return clamp(score, 1, 10)

    def _debt_risk(self, data: Dict[str, Any]) -> int:
        """Score debt risk based on D/E ratio and net debt/EBITDA."""
        dte = data.get("debt_to_equity", 1.0) or 1.0
        ebitda = data.get("ebitda", 1) or 1
        total_debt = data.get("total_debt", 0) or 0
        cash = data.get("cash", 0) or 0
        net_debt = total_debt - cash
        net_debt_ebitda = safe_divide(net_debt, ebitda)

        score = 5
        # D/E ratio
        if dte <= 0.3:
            score -= 3
        elif dte <= 0.7:
            score -= 1
        elif dte <= 1.5:
            score += 1
        elif dte <= 3.0:
            score += 3
        else:
            score += 4

        # Net debt / EBITDA
        if net_debt_ebitda <= 1.0:
            score -= 1
        elif net_debt_ebitda >= 4.0:
            score += 2
        elif net_debt_ebitda >= 6.0:
            score += 3

        return clamp(score, 1, 10)

    def _cashflow_risk(self, data: Dict[str, Any], fin: Dict[str, Any]) -> int:
        """Score cash flow risk based on FCF generation and coverage."""
        net_margin = data.get("net_margin", 0) or 0
        ebitda = data.get("ebitda", 0) or 0
        total_debt = data.get("total_debt", 1) or 1

        # Estimate interest coverage (simplified)
        # Assume avg interest rate ~5% on debt
        interest_est = total_debt * 0.05
        interest_coverage = safe_divide(ebitda, interest_est)

        score = 5
        if net_margin >= 0.15:
            score -= 2
        elif net_margin >= 0.08:
            score -= 1
        elif net_margin < 0.03:
            score += 2
        elif net_margin < 0:
            score += 4

        if interest_coverage >= 5:
            score -= 1
        elif interest_coverage < 2:
            score += 2
        elif interest_coverage < 1:
            score += 3

        return clamp(score, 1, 10)

    def _market_risk(self, data: Dict[str, Any]) -> int:
        """Score market risk based on beta, 52w range, and volatility."""
        beta = data.get("beta", 1.0) or 1.0
        price = data.get("current_price", 1) or 1
        high_52w = data.get("52w_high", price) or price
        low_52w = data.get("52w_low", price) or price

        # 52-week range as volatility proxy
        range_pct = safe_divide(high_52w - low_52w, low_52w)

        score = 5
        # Beta
        if beta <= 0.5:
            score -= 2
        elif beta <= 0.8:
            score -= 1
        elif beta >= 1.5:
            score += 2
        elif beta >= 1.2:
            score += 1

        # 52w range
        if range_pct >= 0.5:
            score += 2
        elif range_pct >= 0.3:
            score += 1
        elif range_pct <= 0.15:
            score -= 1

        # Price vs 52w high (drawdown)
        drawdown = safe_divide(high_52w - price, high_52w)
        if drawdown >= 0.4:
            score += 1  # significant drawdown = higher risk

        return clamp(score, 1, 10)

    def _policy_risk(self, sector: str) -> int:
        """Score policy/regulatory risk based on sector."""
        for key, risk in self.SECTOR_POLICY_RISK.items():
            if any(word in sector for word in key.split(" / ")):
                return risk
        return 5  # default

    def _hk_sector_risk(self, sector: str, data: Dict[str, Any]) -> int:
        """Score HK-specific sector risk (macro, geopolitical, regulatory)."""
        # HK market specific risk factors
        base_score = 5

        # Tech/internet: higher regulatory risk from mainland China
        if "科技" in sector or "互聯網" in sector:
            base_score = 7
        # Property: ongoing HK property market headwinds
        elif "地產" in sector:
            base_score = 7
        # Banking: interest rate sensitivity
        elif "銀行" in sector or "金融" in sector:
            base_score = 5
        # Infrastructure: relatively stable
        elif "基建" in sector or "建築" in sector:
            base_score = 4

        # Adjust for market cap (smaller = higher risk)
        mktcap = data.get("market_cap", 0) or 0
        if mktcap < 5_000_000_000:  # < HK$5B
            base_score += 2
        elif mktcap < 20_000_000_000:  # < HK$20B
            base_score += 1

        return clamp(base_score, 1, 10)

    def _downside_scenario_risk(self, data: Dict[str, Any], fin: Dict[str, Any]) -> int:
        """Score downside scenario risk based on valuation and leverage."""
        pe = data.get("pe_ratio") or 0
        pb = data.get("pb_ratio") or 0
        dte = data.get("debt_to_equity", 1) or 1

        score = 5

        # High PE = more downside if earnings disappoint
        if pe and pe > 30:
            score += 2
        elif pe and pe > 20:
            score += 1
        elif pe and pe < 8:
            score -= 1  # low PE = limited downside

        # PB < 1 = some asset protection
        if pb and pb < 1.0:
            score -= 1
        elif pb and pb > 4.0:
            score += 1

        # High leverage amplifies downside
        if dte > 3.0:
            score += 2
        elif dte > 1.5:
            score += 1

        return clamp(score, 1, 10)

    # ─── Narrative Builder ────────────────────────────────────────────────────

    def _build_narratives(
        self,
        scores: Dict[str, int],
        data: Dict[str, Any],
        sector: str,
    ) -> Dict[str, str]:
        """Build plain-language risk narratives for each dimension."""
        cr = data.get("current_ratio", 0) or 0
        dte = data.get("debt_to_equity", 0) or 0
        beta = data.get("beta", 1.0) or 1.0

        return {
            "流動性風險": (
                f"流動比率為 {cr:.2f}x。"
                + ("流動性充裕，短期償債能力強。" if cr >= 1.5 else
                   "流動性一般，需關注短期債務到期情況。" if cr >= 1.0 else
                   "流動性偏緊，存在短期流動性壓力。")
            ),
            "債務風險": (
                f"債務股本比為 {dte:.2f}x。"
                + ("槓桿水平偏低，財務結構穩健。" if dte <= 0.5 else
                   "槓桿水平適中，需持續監控。" if dte <= 1.5 else
                   "槓桿水平偏高，利率上升或盈利下滑將增加財務壓力。")
            ),
            "現金流風險": (
                "現金流生成能力"
                + ("強勁，能有效覆蓋利息及資本開支。" if scores["現金流風險"] <= 4 else
                   "一般，需關注自由現金流趨勢。" if scores["現金流風險"] <= 6 else
                   "偏弱，存在現金流壓力風險。")
            ),
            "市場風險": (
                f"Beta值為 {beta:.2f}，"
                + ("市場波動性低於大市，防禦性較強。" if beta < 0.8 else
                   "市場波動性與大市相近。" if beta <= 1.2 else
                   "市場波動性高於大市，股價波幅較大。")
            ),
            "政策風險": (
                f"{sector}行業面臨的政策及監管風險"
                + ("相對較低。" if scores["政策風險"] <= 4 else
                   "處於中等水平，需關注監管動態。" if scores["政策風險"] <= 6 else
                   "偏高，監管環境存在不確定性。")
            ),
            "香港行業風險": (
                "香港市場特定風險，包括地緣政治、人民幣匯率及港股流動性因素，"
                + ("影響相對有限。" if scores["香港行業風險"] <= 4 else
                   "需持續關注。" if scores["香港行業風險"] <= 6 else
                   "影響較為顯著，建議密切監控。")
            ),
            "下行情景風險": (
                "在悲觀情景下（盈利下滑30%、估值收縮），"
                + ("股價下行空間相對有限。" if scores["下行情景風險"] <= 4 else
                   "股價存在一定下行風險。" if scores["下行情景風險"] <= 6 else
                   "股價下行風險較大，需設定嚴格止損。")
            ),
        }

    def _build_scenarios(
        self,
        data: Dict[str, Any],
        fin: Dict[str, Any],
    ) -> Dict[str, Dict]:
        """Build bull/base/bear scenario analysis."""
        price = data.get("current_price", 0) or 0
        pe = data.get("pe_ratio") or 10
        eps = safe_divide(data.get("net_income_ttm", 0), data.get("market_cap", 1) / max(price, 0.01))

        return {
            "牛市情景": {
                "description": "盈利超預期增長20%，估值倍數擴張",
                "eps_change": "+20%",
                "pe_change": "+15%",
                "implied_price": price * 1.38,
                "upside": "+38%",
                "probability": "25%",
                "key_catalyst": "業績超預期、行業政策利好、市場情緒改善",
            },
            "基本情景": {
                "description": "盈利符合市場預期，估值倍數維持",
                "eps_change": "+8%",
                "pe_change": "0%",
                "implied_price": price * 1.08,
                "upside": "+8%",
                "probability": "50%",
                "key_catalyst": "業績穩定增長，宏觀環境無重大變化",
            },
            "熊市情景": {
                "description": "盈利低於預期，估值倍數收縮",
                "eps_change": "-15%",
                "pe_change": "-20%",
                "implied_price": price * 0.68,
                "upside": "-32%",
                "probability": "25%",
                "key_catalyst": "宏觀經濟下行、行業監管收緊、流動性收縮",
            },
        }

    def _preference_note(self, score: float, preference: str) -> str:
        """Generate a note based on risk score and investor preference."""
        if preference == "保守":
            if score <= 4:
                return "風險評分符合保守型投資者要求，但仍需做好分散投資。"
            elif score <= 6:
                return "風險評分偏高，保守型投資者應謹慎考慮，建議降低倉位。"
            else:
                return "風險評分過高，不建議保守型投資者持有此股票。"
        elif preference == "進取":
            if score <= 6:
                return "風險評分在進取型投資者可接受範圍內。"
            elif score <= 8:
                return "風險較高，進取型投資者可小倉位參與，需設定止損。"
            else:
                return "極高風險，即使進取型投資者亦需謹慎，建議嚴格控制倉位。"
        else:  # 中等
            if score <= 5:
                return "風險評分適合中等風險承受能力的投資者。"
            elif score <= 7:
                return "風險偏高，中等風險投資者應適當降低倉位並設定止損。"
            else:
                return "風險過高，超出中等風險承受能力，建議觀望。"
