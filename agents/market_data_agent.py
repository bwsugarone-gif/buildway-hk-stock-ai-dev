"""
agents/market_data_agent.py
Buildway Tech (HK) Limited — Market Data Agent
Role: Fetch live or fallback market data for HK stocks
DEV version uses yfinance with graceful fallback to demo data
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional
from core.data_confidence import (
    HIGH,
    LOW,
    MEDIUM,
    INVALID,
    PARTIAL_DATA_WARNING,
    assess_market_data_confidence,
    confidence_label,
    invalid_market_data,
)
from core.data_normalizer import normalize_market_data
from core.data_coverage_engine import DataCoverageEngine
from core.safe_math import safe_number
from data.sample_data import SAMPLE_HK_STOCKS, get_sample_market_data, get_sample_financial_history
from core.utils import normalize_hk_ticker, format_currency_hkd, format_percentage


MASTER_DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "hk_stock_master_data.json"


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
        self._master_data = self._load_master_data()
        self._coverage_engine = DataCoverageEngine()

    def _check_yfinance(self) -> bool:
        """Check if yfinance is available."""
        try:
            import yfinance  # noqa: F401
            return True
        except ImportError:
            return False

    def _load_master_data(self) -> Dict[str, Dict[str, Any]]:
        try:
            with open(MASTER_DATA_PATH, "r", encoding="utf-8") as file:
                return json.load(file)
        except Exception as exc:
            print(f"[Market Data Agent] HK stock master data unavailable: {exc}")
            return {}

    def _get_company_metadata(self, ticker: str) -> Dict[str, Any]:
        return dict(self._master_data.get(normalize_hk_ticker(ticker), {}))

    def _apply_company_metadata(
        self,
        data: Dict[str, Any],
        metadata: Dict[str, Any],
        company_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        if not metadata:
            return data

        data["company_metadata"] = metadata
        data["company_name"] = company_name or data.get("company_name") or metadata.get("name_zh") or ""
        data["company_name_zh"] = metadata.get("name_zh", data.get("company_name_zh", ""))
        data["company_name_en"] = metadata.get("name_en", data.get("company_name_en", ""))
        data["sector"] = data.get("sector") or metadata.get("sector", "")
        data["business"] = metadata.get("business", data.get("business", ""))
        data["market_type"] = metadata.get("market_type", data.get("market_type", ""))
        data["metadata_source"] = "hk_stock_master_data"
        return data

    def _metadata_only_market_data(
        self,
        ticker: str,
        company_name: Optional[str],
        reason: str,
    ) -> Dict[str, Any]:
        metadata = self._get_company_metadata(ticker)
        data = {
            "ticker": ticker,
            "data_source": "HK stock master metadata fallback",
            "is_demo": True,
            "currency": "HKD",
            "exchange": "HKEX",
            "company_name": company_name or metadata.get("name_zh", ""),
            "sector": metadata.get("sector", ""),
            "fallback_reason": reason,
            "missing_data_flags": ["market_price_unavailable", "market_cap_unavailable"],
        }
        return self._apply_company_metadata(data, metadata, company_name)

    def fetch(
        self,
        ticker: str,
        company_name: Optional[str] = None,
        analysis_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Main entry point. Fetch market data for a given ticker.
        Returns a standardized data dict with is_demo flag.
        """
        normalized = (analysis_context or {}).get("stock_code") or normalize_hk_ticker(ticker)
        print(f"[Market Data Agent] Received stock_code = {normalized}")
        metadata = self._get_company_metadata(normalized)

        if self._yfinance_available:
            try:
                result = self._fetch_live(normalized, company_name)
                sample_candidate = get_sample_market_data(normalized)
                sample_has_market_data = safe_number(sample_candidate.get("current_price"), 0.0) > 0 or safe_number(sample_candidate.get("market_cap"), 0.0) > 0
                if sample_has_market_data and not (
                    safe_number(result.get("current_price"), 0.0) > 0
                    or safe_number(result.get("market_cap"), 0.0) > 0
                ):
                    result = sample_candidate
                    result["fallback_reason"] = "live provider returned no usable price or market cap"
                result["ticker"] = normalized
                result = self._apply_company_metadata(result, metadata, company_name)
                result["company_name"] = company_name or result.get("company_name") or metadata.get("name_zh", "")
                return self._finalize_market_data(result)
            except Exception as e:
                if normalized not in SAMPLE_HK_STOCKS and not metadata:
                    return invalid_market_data(normalized, str(e))
                sample_candidate = get_sample_market_data(normalized)
                sample_has_market_data = safe_number(sample_candidate.get("current_price"), 0.0) > 0 or safe_number(sample_candidate.get("market_cap"), 0.0) > 0
                result = sample_candidate if sample_has_market_data else self._metadata_only_market_data(normalized, company_name, str(e))
                result["fallback_reason"] = str(e)
                result["ticker"] = normalized
                result = self._apply_company_metadata(result, metadata, company_name)
                result["company_name"] = company_name or result.get("company_name") or metadata.get("name_zh", "")
                return self._finalize_market_data(result)

        if normalized not in SAMPLE_HK_STOCKS and not metadata:
            return invalid_market_data(normalized, "yfinance unavailable and ticker is outside validated sample universe.")
        sample_candidate = get_sample_market_data(normalized)
        sample_has_market_data = safe_number(sample_candidate.get("current_price"), 0.0) > 0 or safe_number(sample_candidate.get("market_cap"), 0.0) > 0
        result = sample_candidate if sample_has_market_data else self._metadata_only_market_data(normalized, company_name, "yfinance unavailable")
        result["ticker"] = normalized
        result = self._apply_company_metadata(result, metadata, company_name)
        result["company_name"] = company_name or result.get("company_name") or metadata.get("name_zh", "")
        return self._finalize_market_data(result)

    def _sanitize_numeric_fields(self, data: Dict[str, Any]) -> Dict[str, Any]:
        numeric_fields = [
            "current_price", "prev_close", "day_high", "day_low", "volume",
            "market_cap", "pe_ratio", "pb_ratio", "dividend_yield", "52w_high",
            "52w_low", "revenue_ttm", "net_income_ttm", "total_debt", "cash",
            "ebitda", "gross_margin", "net_margin", "roe", "debt_to_equity",
            "current_ratio", "beta",
        ]
        missing = list(data.get("missing_data_flags", []))
        for field in numeric_fields:
            if data.get(field) is None or data.get(field) == "":
                missing.append(f"{field} unavailable")
            data[field] = safe_number(data.get(field), 0.0)
        data["missing_data_flags"] = sorted(set(missing))
        if missing:
            data["data_warning"] = "部分財務數據暫時不可用，以下分析已採用保守假設。"
        return data

    def _finalize_market_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        if data.get("data_confidence") == INVALID:
            return data

        sanitized = self._sanitize_numeric_fields(data)
        sanitized = self._coverage_engine.enhance(sanitized)
        confidence = assess_market_data_confidence(sanitized)
        coverage = sanitized.get("coverage_score") or confidence
        sanitized["data_confidence"] = coverage
        sanitized["data_confidence_label"] = confidence_label(coverage)

        if coverage == INVALID:
            return invalid_market_data(
                sanitized.get("ticker", "N/A"),
                "Missing company name, current price, market cap, and ticker metadata.",
            )

        if coverage in {LOW, MEDIUM}:
            sanitized["data_warning"] = PARTIAL_DATA_WARNING

        return sanitized

    def _fetch_live(self, ticker: str, company_name: Optional[str] = None) -> Dict[str, Any]:
        """Fetch live data from yfinance."""
        import yfinance as yf

        stock = yf.Ticker(ticker)
        info = stock.info

        # yfinance may return empty dict for invalid tickers
        if not info:
            raise ValueError(f"無法獲取 {ticker} 的實時數據")

        has_price = info.get("regularMarketPrice") is not None or info.get("currentPrice") is not None
        has_market_cap = info.get("marketCap") is not None
        if not has_price and not has_market_cap and not self._get_company_metadata(ticker):
            raise ValueError(f"{ticker} 缺少有效股票元數據")

        # Map yfinance fields to our standard schema
        data = {
            "ticker": ticker,
            "data_source": "Yahoo Finance (實時數據)",
            "is_demo": False,
            "currency": info.get("currency", "HKD"),
            "exchange": info.get("exchange") or "HKEX",
            "company_name": company_name or info.get("longName") or info.get("shortName") or "",
            "sector": info.get("sector") or info.get("industry") or "",
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

        # Apply multi-field fallback normalization to improve coverage
        # Pass the full yfinance info dict for alias resolution
        data_with_info = {**data, **info}
        normalized = normalize_market_data(data_with_info)
        # Only copy back fields that were improved (non-None values)
        for field in ("pe_ratio", "pb_ratio", "dividend_yield", "beta",
                      "52w_high", "52w_low", "gross_margin", "net_margin",
                      "roe", "current_ratio", "debt_to_equity", "volume",
                      "market_cap", "revenue_ttm", "ebitda"):
            if normalized.get(field) is not None:
                data[field] = normalized[field]

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
