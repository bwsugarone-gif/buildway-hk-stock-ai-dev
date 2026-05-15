"""
agents/financial_analyst_agent.py
Buildway Tech (HK) Limited — Financial Analyst Agent
Role: Wall Street-style financial analysis using DCF, Comps, and Valuation Range
DEV version uses simplified calculations with clearly labeled assumptions
"""

from typing import Dict, Any, List, Optional
from core.utils import safe_divide, format_currency_hkd, format_percentage, clamp
from data.sample_data import get_hk_sector_benchmarks


class FinancialAnalystAgent:
    """
    Financial Analyst Agent
    Performs DCF concept, comparable company analysis, and valuation range.
    All calculations are simplified for DEV version with labeled assumptions.
    """

    AGENT_NAME = "財務分析師代理"
    AGENT_ROLE = "運用華爾街框架進行財務分析，包括DCF估值、可比公司分析及估值區間"

    # ─── DCF Assumptions (DEV defaults) ──────────────────────────────────────
    DEFAULT_WACC = 0.10          # 10% WACC
    DEFAULT_TERMINAL_GROWTH = 0.03  # 3% terminal growth
    DEFAULT_PROJECTION_YEARS = 5
    DEFAULT_FCF_GROWTH_RATES = {
        "bull": 0.15,
        "base": 0.08,
        "bear": 0.02,
    }

    def analyze(self, market_data: Dict[str, Any], financial_history: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main entry point. Run full financial analysis.
        Returns structured analysis dict.
        """
        ticker = market_data.get("ticker", "N/A")
        sector = market_data.get("sector", "綜合企業")

        # Core financial metrics
        metrics = self._compute_metrics(market_data)

        # DCF valuation (simplified)
        dcf = self._run_dcf(market_data, financial_history)

        # Comparable company analysis
        comps = self._run_comps(market_data, sector)

        # Valuation range (football field)
        valuation_range = self._compute_valuation_range(market_data, dcf, comps)

        # Financial health score
        health_score = self._compute_financial_health(market_data)

        return {
            "ticker": ticker,
            "is_demo": market_data.get("is_demo", True),
            "metrics": metrics,
            "dcf": dcf,
            "comps": comps,
            "valuation_range": valuation_range,
            "health_score": health_score,
            "sector": sector,
        }

    def _compute_metrics(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Compute key financial ratios and metrics."""
        revenue = data.get("revenue_ttm", 0) or 0
        net_income = data.get("net_income_ttm", 0) or 0
        ebitda = data.get("ebitda", 0) or 0
        total_debt = data.get("total_debt", 0) or 0
        cash = data.get("cash", 0) or 0
        market_cap = data.get("market_cap", 0) or 0
        current_price = data.get("current_price", 0) or 0

        net_debt = total_debt - cash
        ev = market_cap + net_debt  # Enterprise Value

        return {
            "revenue_ttm": revenue,
            "net_income_ttm": net_income,
            "ebitda": ebitda,
            "net_debt": net_debt,
            "enterprise_value": ev,
            "ev_ebitda": safe_divide(ev, ebitda),
            "ev_revenue": safe_divide(ev, revenue),
            "pe_ratio": data.get("pe_ratio"),
            "pb_ratio": data.get("pb_ratio"),
            "gross_margin": data.get("gross_margin", 0),
            "net_margin": data.get("net_margin", 0),
            "roe": data.get("roe", 0),
            "debt_to_equity": data.get("debt_to_equity", 0),
            "current_ratio": data.get("current_ratio", 0),
            "dividend_yield": data.get("dividend_yield", 0),
            "beta": data.get("beta", 1.0),
        }

    def _run_dcf(self, data: Dict[str, Any], history: Dict[str, Any]) -> Dict[str, Any]:
        """
        Simplified DCF valuation.
        Uses FCF as base, projects 5 years, applies terminal value.
        """
        # Base FCF — use last year's FCF from history or estimate from net income
        fcf_list = history.get("free_cash_flow", [])
        base_fcf = fcf_list[-1] if fcf_list else (data.get("net_income_ttm", 0) * 0.7)
        if not base_fcf or base_fcf <= 0:
            base_fcf = data.get("ebitda", 0) * 0.5  # rough proxy

        market_cap = data.get("market_cap", 1)
        shares_outstanding = market_cap / max(data.get("current_price", 1), 0.01)

        scenarios = {}
        for scenario, growth_rate in self.DEFAULT_FCF_GROWTH_RATES.items():
            # Project FCF for 5 years
            projected_fcf = []
            fcf = base_fcf
            for year in range(1, self.DEFAULT_PROJECTION_YEARS + 1):
                fcf = fcf * (1 + growth_rate)
                projected_fcf.append(fcf)

            # Discount projected FCFs
            wacc = self.DEFAULT_WACC
            pv_fcfs = sum(
                fcf / ((1 + wacc) ** (i + 1))
                for i, fcf in enumerate(projected_fcf)
            )

            # Terminal value (Gordon Growth Model)
            terminal_fcf = projected_fcf[-1] * (1 + self.DEFAULT_TERMINAL_GROWTH)
            terminal_value = terminal_fcf / (wacc - self.DEFAULT_TERMINAL_GROWTH)
            pv_terminal = terminal_value / ((1 + wacc) ** self.DEFAULT_PROJECTION_YEARS)

            # Total intrinsic value
            total_ev = pv_fcfs + pv_terminal
            net_debt = (data.get("total_debt", 0) or 0) - (data.get("cash", 0) or 0)
            equity_value = total_ev - net_debt
            intrinsic_price = equity_value / shares_outstanding if shares_outstanding > 0 else 0

            scenarios[scenario] = {
                "growth_rate": growth_rate,
                "projected_fcf": projected_fcf,
                "pv_fcfs": pv_fcfs,
                "terminal_value": terminal_value,
                "pv_terminal": pv_terminal,
                "total_ev": total_ev,
                "equity_value": equity_value,
                "intrinsic_price": intrinsic_price,
            }

        current_price = data.get("current_price", 0)
        base_price = scenarios["base"]["intrinsic_price"]
        upside = safe_divide(base_price - current_price, current_price) if current_price else 0

        return {
            "is_demo": data.get("is_demo", True),
            "base_fcf": base_fcf,
            "wacc": self.DEFAULT_WACC,
            "terminal_growth": self.DEFAULT_TERMINAL_GROWTH,
            "projection_years": self.DEFAULT_PROJECTION_YEARS,
            "scenarios": scenarios,
            "current_price": current_price,
            "base_intrinsic_price": base_price,
            "upside_downside_pct": upside,
            "assumptions_note": (
                "【DEV簡化版】WACC=10%，終端增長率=3%，FCF增長率：牛市15%/基本8%/熊市2%。"
                "實際估值需使用真實財務數據及專業假設。"
            ),
        }

    def _run_comps(self, data: Dict[str, Any], sector: str) -> Dict[str, Any]:
        """
        Comparable company analysis using sector benchmarks.
        DEV version uses sector median multiples.
        """
        benchmarks = get_hk_sector_benchmarks()

        # Find best matching sector
        sector_key = "綜合企業"
        for key in benchmarks:
            if any(word in sector for word in key.split(" / ")):
                sector_key = key
                break

        bench = benchmarks[sector_key]
        pe_median = bench["pe_median"]
        pb_median = bench["pb_median"]
        ev_ebitda_median = bench["ev_ebitda_median"]

        # Company metrics
        eps = safe_divide(
            data.get("net_income_ttm", 0),
            data.get("market_cap", 1) / max(data.get("current_price", 1), 0.01)
        )
        book_value_per_share = safe_divide(
            data.get("market_cap", 0),
            data.get("pb_ratio", 1) * max(data.get("market_cap", 1) / max(data.get("current_price", 1), 0.01), 1)
        )
        ebitda = data.get("ebitda", 0) or 0
        net_debt = (data.get("total_debt", 0) or 0) - (data.get("cash", 0) or 0)
        shares = data.get("market_cap", 1) / max(data.get("current_price", 1), 0.01)

        # Implied prices from sector multiples
        implied_pe = eps * pe_median if eps > 0 else 0
        implied_pb = book_value_per_share * pb_median if book_value_per_share > 0 else 0
        implied_ev_ebitda = ((ebitda * ev_ebitda_median) - net_debt) / shares if shares > 0 and ebitda > 0 else 0

        # Company's own multiples vs sector
        company_pe = data.get("pe_ratio") or 0
        company_pb = data.get("pb_ratio") or 0
        company_ev_ebitda = safe_divide(
            data.get("market_cap", 0) + net_debt,
            ebitda
        )

        return {
            "sector": sector_key,
            "sector_benchmarks": bench,
            "company_pe": company_pe,
            "company_pb": company_pb,
            "company_ev_ebitda": company_ev_ebitda,
            "pe_premium_discount": safe_divide(company_pe - pe_median, pe_median) if pe_median else 0,
            "pb_premium_discount": safe_divide(company_pb - pb_median, pb_median) if pb_median else 0,
            "ev_ebitda_premium_discount": safe_divide(company_ev_ebitda - ev_ebitda_median, ev_ebitda_median) if ev_ebitda_median else 0,
            "implied_price_pe": implied_pe,
            "implied_price_pb": implied_pb,
            "implied_price_ev_ebitda": implied_ev_ebitda,
            "assumptions_note": f"基於{sector_key}行業中位數估值倍數（DEV示範數據）",
        }

    def _compute_valuation_range(
        self,
        data: Dict[str, Any],
        dcf: Dict[str, Any],
        comps: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Compute football field valuation range from multiple methods."""
        current_price = data.get("current_price", 0)

        # Collect all implied prices
        prices = []

        # DCF scenarios
        for scenario in ["bear", "base", "bull"]:
            p = dcf["scenarios"][scenario]["intrinsic_price"]
            if p > 0:
                prices.append(p)

        # Comps implied prices
        for key in ["implied_price_pe", "implied_price_pb", "implied_price_ev_ebitda"]:
            p = comps.get(key, 0)
            if p > 0:
                prices.append(p)

        if not prices:
            prices = [current_price * 0.8, current_price, current_price * 1.2]

        low = min(prices)
        high = max(prices)
        mid = sum(prices) / len(prices)

        return {
            "current_price": current_price,
            "low": low,
            "mid": mid,
            "high": high,
            "upside_to_mid": safe_divide(mid - current_price, current_price),
            "upside_to_high": safe_divide(high - current_price, current_price),
            "downside_to_low": safe_divide(low - current_price, current_price),
            "verdict": self._valuation_verdict(current_price, low, mid, high),
        }

    def _valuation_verdict(self, price: float, low: float, mid: float, high: float) -> str:
        """Give a simple valuation verdict based on price vs range."""
        if price < low:
            return "估值偏低（相對估值區間）"
        elif price < mid:
            return "估值合理偏低"
        elif price < high:
            return "估值合理偏高"
        else:
            return "估值偏高（相對估值區間）"

    def _compute_financial_health(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Score financial health across 5 dimensions (0-10 each)."""
        scores = {}

        # 1. Profitability (net margin)
        net_margin = data.get("net_margin", 0) or 0
        scores["盈利能力"] = clamp(int(net_margin * 100), 0, 10)

        # 2. Leverage (debt-to-equity, lower is better)
        dte = data.get("debt_to_equity", 0) or 0
        if dte <= 0.5:
            scores["槓桿水平"] = 9
        elif dte <= 1.0:
            scores["槓桿水平"] = 7
        elif dte <= 2.0:
            scores["槓桿水平"] = 5
        elif dte <= 3.0:
            scores["槓桿水平"] = 3
        else:
            scores["槓桿水平"] = 1

        # 3. Liquidity (current ratio)
        cr = data.get("current_ratio", 0) or 0
        if cr >= 2.0:
            scores["流動性"] = 9
        elif cr >= 1.5:
            scores["流動性"] = 7
        elif cr >= 1.0:
            scores["流動性"] = 5
        else:
            scores["流動性"] = 2

        # 4. Return on equity
        roe = data.get("roe", 0) or 0
        scores["股本回報率"] = clamp(int(roe * 50), 0, 10)

        # 5. Dividend yield (bonus for income investors)
        dy = data.get("dividend_yield", 0) or 0
        if dy >= 0.06:
            scores["股息回報"] = 9
        elif dy >= 0.04:
            scores["股息回報"] = 7
        elif dy >= 0.02:
            scores["股息回報"] = 5
        elif dy > 0:
            scores["股息回報"] = 3
        else:
            scores["股息回報"] = 1

        overall = sum(scores.values()) / len(scores)
        return {
            "dimension_scores": scores,
            "overall_score": round(overall, 1),
            "grade": self._health_grade(overall),
        }

    def _health_grade(self, score: float) -> str:
        if score >= 8:
            return "A（優秀）"
        elif score >= 6:
            return "B（良好）"
        elif score >= 4:
            return "C（一般）"
        else:
            return "D（偏弱）"
