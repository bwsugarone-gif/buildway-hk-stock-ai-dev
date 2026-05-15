"""
agents/market_data_agent.py
Buildway Tech (HK) Limited — Market Data Agent
Role: Fetch live or fallback market data for HK stocks
DEV version uses yfinance with graceful fallback to demo data
"""

from typing import Dict, Any, Optional
from data.sample_data import get_sample_market_data, get_sample_financial_history
from core.utils import normalize_hk_ticker, format_currency_hkd, format_percentage


class MarketDataAgent:
    """
    Market Data Agent
    Fetches stock price, market cap, volume, and basic trend data.
    Falls back to demo data if live API is unavailable.
    """

    AGENT_NAME = "市場數據代理"
    AGENT_ROLE = "負責獲取股票市場數據，包括股價、市值、成交量及基本趨勢"

    def __init__(self):
        self._yfinance_available = self._check_yfinance()

    def _check_yfinance(self) -> bool:
        """Check if yfinance is available."""
        try:
            import yfinance  # noqa: F401
            return True
        except ImportError:
            return False

    def fetch(self, ticker: str, company_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Main entry point. Fetch market data for a given ticker.
        Returns a standardized data dict with is_demo flag.
        """
        normalized = normalize_hk_ticker(ticker)

        if self._yfinance_available:
            try:
                return self._fetch_live(normalized, company_name)
            except Exception as e:
                # Graceful fallback
                result = get_sample_market_data(normalized)
                result["fallback_reason"] = str(e)
                result["company_name"] = company_name or result.get("company_name", normalized)
                return result
        else:
            result = get_sample_market_data(normalized)
            result["company_name"] = company_name or result.get("company_name", normalized)
            return result

    def _fetch_live(self, ticker: str, company_name: Optional[str] = None) -> Dict[str, Any]:
        """Fetch live data from yfinance."""
        import yfinance as yf

        stock = yf.Ticker(ticker)
        info = stock.info

        # yfinance may return empty dict for invalid tickers
        if not info or info.get("regularMarketPrice") is None:
            raise ValueError(f"無法獲取 {ticker} 的實時數據")

        # Map yfinance fields to our standard schema
        data = {
            "ticker": ticker,
            "data_source": "Yahoo Finance (實時數據)",
            "is_demo": False,
            "currency": info.get("currency", "HKD"),
            "exchange": info.get("exchange", "HKEX"),
            "company_name": company_name or info.get("longName") or info.get("shortName", ticker),
            "sector": info.get("sector") or info.get("industry", "未知行業"),
            "current_price": info.get("regularMarketPrice") or info.get("currentPrice", 0),
            "prev_close": info.get("regularMarketPreviousClose") or info.get("previousClose", 0),
            "day_high": info.get("dayHigh") or info.get("regularMarketDayHigh", 0),
            "day_low": info.get("dayLow") or info.get("regularMarketDayLow", 0),
            "volume": info.get("regularMarketVolume") or info.get("volume", 0),
            "market_cap": info.get("marketCap", 0),
            "pe_ratio": info.get("trailingPE") or info.get("forwardPE", None),
            "pb_ratio": info.get("priceToBook", None),
            "dividend_yield": info.get("dividendYield", 0),
            "52w_high": info.get("fiftyTwoWeekHigh", 0),
            "52w_low": info.get("fiftyTwoWeekLow", 0),
            "revenue_ttm": info.get("totalRevenue", 0),
            "net_income_ttm": info.get("netIncomeToCommon", 0),
            "total_debt": info.get("totalDebt", 0),
            "cash": info.get("totalCash", 0),
            "ebitda": info.get("ebitda", 0),
            "gross_margin": info.get("grossMargins", 0),
            "net_margin": info.get("profitMargins", 0),
            "roe": info.get("returnOnEquity", 0),
            "debt_to_equity": info.get("debtToEquity", 0),
            "current_ratio": info.get("currentRatio", 0),
            "beta": info.get("beta", 1.0),
        }

        # Fetch recent price history for trend
        try:
            hist = stock.history(period="3mo")
            if not hist.empty:
                prices = hist["Close"].tolist()
                data["price_history_3m"] = prices[-60:]  # last 60 trading days
                data["price_change_3m"] = (prices[-1] - prices[0]) / prices[0] if prices[0] else 0
        except Exception:
            pass

        return data

    def get_financial_history(self, ticker: str) -> Dict[str, Any]:
        """Fetch multi-year financial history for trend analysis."""
        normalized = normalize_hk_ticker(ticker)

        if self._yfinance_available:
            try:
                return self._fetch_financial_history_live(normalized)
            except Exception:
                return get_sample_financial_history(normalized)
        return get_sample_financial_history(normalized)

    def _fetch_financial_history_live(self, ticker: str) -> Dict[str, Any]:
        """Fetch financial history from yfinance."""
        import yfinance as yf

        stock = yf.Ticker(ticker)
        financials = stock.financials
        cashflow = stock.cashflow
        balance = stock.balance_sheet

        if financials is None or financials.empty:
            raise ValueError("無法獲取財務歷史數據")

        years = [str(col.year) for col in financials.columns[:3]]

        def safe_row(df, key):
            """Safely extract a row from a DataFrame."""
            for k in df.index:
                if key.lower() in str(k).lower():
                    return [float(v) if v is not None else 0 for v in df.loc[k].iloc[:3]]
            return [0, 0, 0]

        return {
            "ticker": ticker,
            "is_demo": False,
            "years": years,
            "revenue": safe_row(financials, "Total Revenue"),
            "ebitda": safe_row(financials, "EBITDA"),
            "net_income": safe_row(financials, "Net Income"),
            "free_cash_flow": safe_row(cashflow, "Free Cash Flow"),
            "total_debt": safe_row(balance, "Total Debt"),
            "cash": safe_row(balance, "Cash"),
            "capex": safe_row(cashflow, "Capital Expenditure"),
        }

    def summarize(self, data: Dict[str, Any]) -> str:
        """Return a human-readable summary of market data."""
        ticker = data.get("ticker", "N/A")
        name = data.get("company_name", ticker)
        price = data.get("current_price", 0)
        mktcap = format_currency_hkd(data.get("market_cap", 0))
        pe = data.get("pe_ratio")
        demo_tag = "【示範數據】" if data.get("is_demo") else "【實時數據】"

        pe_str = f"{pe:.1f}x" if pe else "N/A"
        change = data.get("price_change_3m")
        change_str = f"（3個月變動：{change*100:+.1f}%）" if change is not None else ""

        return (
            f"{demo_tag} {name} ({ticker})\n"
            f"現價：HK${price:.2f} {change_str}\n"
            f"市值：{mktcap} | 市盈率：{pe_str}"
        )
