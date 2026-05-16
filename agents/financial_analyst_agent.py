"""
agents/financial_analyst_agent.py
Buildway Tech (HK) Limited — Financial Analyst Agent
Role: Wall Street-style financial analysis using DCF, Comps, and Valuation Range
DEV version uses simplified calculations with clearly labeled assumptions
"""

from typing import Dict, Any, List, Optional
from core.safe_math import safe_divide, safe_multiply, safe_number
from core.utils import format_currency_hkd, format_percentage, clamp
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

    def analyze(
        self,
        market_data: Dict[str, Any],
        financial_history: Dict[str, Any],
        analysis_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Main entry point. Run full financial analysis.
        Returns structured analysis dict.
        """
        ticker = (analysis_context or {}).get("stock_code") or market_data.get("ticker", "N/A")
        print(f"[Financial Agent] Received stock_code = {ticker}")
        sector = market_data.get("sector", "綜合企業")

        # Detect missing data for any ticker (including 3416.HK)
        _missing = sorted(set(market_data.get("missing_data_flags", [])))
        _base_code = ticker.replace(".HK", "").lstrip("0") or "0"
        _has_missing = bool(_missing) or safe_number(market_data.get("current_price")) == 0

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

        missing_data_flags = sorted(set(market_data.get("missing_data_flags", [])))

        # Build data warning — always shown when data is incomplete, with
        # a specific message for 3416.HK to satisfy client requirements.
        if _has_missing:
            if _base_code == "3416":
                data_warning = "3416.HK 部分市場或財務資料未能取得，系統已使用保守假設完成分析。"
            else:
                data_warning = "部分財務數據暫時不可用，以下分析已採用保守假設。"
        else:
            data_warning = ""

        return {
            "ticker": ticker,
            "is_demo": market_data.get("is_demo", True),
            "metrics": metrics,
            "dcf": dcf,
            "comps": comps,
            "valuation_range": valuation_range,
            "health_score": health_score,
            "sector": sector,
            "data_warning": data_warning,
            "missing_data_flags": missing_data_flags,
        }

    def _compute_metrics(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Compute key financial ratios and metrics."""
        revenue = safe_number(data.get("revenue_ttm"))
        net_income = safe_number(data.get("net_income_ttm"))
        ebitda = safe_number(data.get("ebitda"))
        total_debt = safe_number(data.get("total_debt"))
        cash = safe_number(data.get("cash"))
        market_cap = safe_number(data.get("market_cap"))
        current_price = safe_number(data.get("current_price"))

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
            "pe_ratio": safe_number(data.get("pe_ratio")),
            "pb_ratio": safe_number(data.get("pb_ratio")),
            "gross_margin": safe_number(data.get("gross_margin")),
            "net_margin": safe_number(data.get("net_margin")),
            "roe": safe_number(data.get("roe")),
            "debt_to_equity": safe_number(data.get("debt_to_equity")),
            "current_ratio": safe_number(data.get("current_ratio")),
            "dividend_yield": safe_number(data.get("dividend_yield")),
            "beta": safe_number(data.get("beta"), 1.0),
        }

    def _run_dcf(self, data: Dict[str, Any], history: Dict[str, Any]) -> Dict[str, Any]:
        """
        Simplified DCF valuation.
        Uses FCF as base, projects 5 years, applies terminal value.
        """
        # Base FCF — use last year's FCF from history or estimate from net income
        fcf_list = [safe_number(v) for v in history.get("free_cash_flow", [])]
        base_fcf = fcf_list[-1] if fcf_list else safe_multiply(data.get("net_income_ttm"), 0.7)
        if not base_fcf or base_fcf <= 0:
            base_fcf = safe_multiply(data.get("ebitda"), 0.5)  # rough proxy

        market_cap = safe_number(data.get("market_cap"), 1)
        shares_outstanding = safe_divide(market_cap, max(safe_number(data.get("current_price"), 1), 0.01))

        scenarios = {}
        for scenario, growth_rate in self.DEFAULT_FCF_GROWTH_RATES.items():
            # Project FCF for 5 years
            projected_fcf = []
            fcf = base_fcf
            for year in range(1, self.DEFAULT_PROJECTION_YEARS + 1):
                fcf = safe_multiply(fcf, 1 + growth_rate)
                projected_fcf.append(fcf)

            # Discount projected FCFs
            wacc = self.DEFAULT_WACC
            pv_fcfs = sum(
                fcf / ((1 + wacc) ** (i + 1))
                for i, fcf in enumerate(projected_fcf)
            )

            # Terminal value (Gordon Growth Model)
            terminal_fcf = safe_multiply(projected_fcf[-1], 1 + self.DEFAULT_TERMINAL_GROWTH)
            terminal_value = safe_divide(terminal_fcf, wacc - self.DEFAULT_TERMINAL_GROWTH)
            pv_terminal = safe_divide(terminal_value, ((1 + wacc) ** self.DEFAULT_PROJECTION_YEARS))

            # Total intrinsic value
            total_ev = pv_fcfs + pv_terminal
            net_debt = safe_number(data.get("total_debt")) - safe_number(data.get("cash"))
            equity_value = total_ev - net_debt
            intrinsic_price = safe_divide(equity_value, shares_outstanding)

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

        current_price = safe_number(data.get("current_price"))
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

        # Sanitize all inputs before any arithmetic — guards against None from yfinance
        pb_ratio = safe_number(data.get("pb_ratio"), 1.0)
        market_cap = safe_number(data.get("market_cap"), 0.0)
        current_price = max(safe_number(data.get("current_price"), 1.0), 0.01)
        print(f"[SAFE CHECK] _run_comps using sanitized values: pb_ratio={pb_ratio} market_cap={market_cap} current_price={current_price}")

        shares_base = safe_divide(market_cap, current_price, 1.0)
        eps = safe_divide(data.get("net_income_ttm", 0), shares_base)
        book_value_per_share = safe_divide(
            market_cap,
            safe_multiply(safe_number(data.get("pb_ratio"), 1), max(shares_base, 1))
        )
        ebitda = safe_number(data.get("ebitda"))
        net_debt = safe_number(data.get("total_debt")) - safe_number(data.get("cash"))
        shares = shares_base

        # Implied prices from sector multiples
        implied_pe = safe_multiply(eps, pe_median) if eps > 0 else 0
        implied_pb = safe_multiply(book_value_per_share, pb_median) if book_value_per_share > 0 else 0
        implied_ev_ebitda = safe_divide((safe_multiply(ebitda, ev_ebitda_median) - net_debt), shares) if shares > 0 and ebitda > 0 else 0

        # Company's own multiples vs sector
        company_pe = safe_number(data.get("pe_ratio"))
        company_pb = safe_number(data.get("pb_ratio"))
        company_ev_ebitda = safe_divide(
            market_cap + net_debt,
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
        current_price = safe_number(data.get("current_price"))

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
                prices = [safe_multiply(current_price, 0.8), current_price, safe_multiply(current_price, 1.2)]

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
        net_margin = safe_number(data.get("net_margin"))
        scores["盈利能力"] = clamp(int(net_margin * 100), 0, 10)

        # 2. Leverage (debt-to-equity, lower is better)
        dte = safe_number(data.get("debt_to_equity"))
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
        cr = safe_number(data.get("current_ratio"))
        if cr >= 2.0:
            scores["流動性"] = 9
        elif cr >= 1.5:
            scores["流動性"] = 7
        elif cr >= 1.0:
            scores["流動性"] = 5
        else:
            scores["流動性"] = 2

        # 4. Return on equity
        roe = safe_number(data.get("roe"))
        scores["股本回報率"] = clamp(int(roe * 50), 0, 10)

        # 5. Dividend yield (bonus for income investors)
        dy = safe_number(data.get("dividend_yield"))
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
