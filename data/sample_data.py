"""
data/sample_data.py
Buildway Tech (HK) Limited — Demo / Fallback Sample Data
Used when live API data is unavailable (DEV mode)
All data is clearly marked as DEMO DATA
"""

from typing import Dict, Any


# ─── Sample HK Stock Universe ─────────────────────────────────────────────────
SAMPLE_HK_STOCKS = {
    "0700.HK": "騰訊控股有限公司",
    "0005.HK": "匯豐控股有限公司",
    "0941.HK": "中國移動有限公司",
    "1299.HK": "友邦保險控股有限公司",
    "0388.HK": "香港交易及結算所有限公司",
    "3690.HK": "美團",
    "9988.HK": "阿里巴巴集團控股有限公司",
    "0001.HK": "長和",
    "0016.HK": "新鴻基地產發展有限公司",
    "2318.HK": "中國平安保險（集團）股份有限公司",
    "0883.HK": "中國海洋石油有限公司",
    "1398.HK": "中國工商銀行股份有限公司",
    "0939.HK": "中國建設銀行股份有限公司",
    "3988.HK": "中國銀行股份有限公司",
}


def get_sample_market_data(ticker: str) -> Dict[str, Any]:
    """
    Return sample market data for a given ticker.
    All values are illustrative demo data only.
    """
    # Base demo data template
    base_data = {
        "ticker": ticker,
        "data_source": "DEMO DATA — 示範數據（非實時）",
        "is_demo": True,
        "currency": "HKD",
        "exchange": "HKEX",
    }

    # Ticker-specific demo data
    stock_demos = {
        "0700.HK": {
            "company_name": "騰訊控股有限公司",
            "sector": "科技 / 互聯網",
            "current_price": 385.40,
            "prev_close": 382.00,
            "day_high": 389.20,
            "day_low": 381.00,
            "volume": 18_500_000,
            "market_cap": 3_710_000_000_000,
            "pe_ratio": 18.5,
            "pb_ratio": 3.2,
            "dividend_yield": 0.008,
            "52w_high": 420.00,
            "52w_low": 280.00,
            "revenue_ttm": 609_000_000_000,
            "net_income_ttm": 115_000_000_000,
            "total_debt": 180_000_000_000,
            "cash": 350_000_000_000,
            "ebitda": 180_000_000_000,
            "gross_margin": 0.445,
            "net_margin": 0.189,
            "roe": 0.195,
            "debt_to_equity": 0.38,
            "current_ratio": 1.85,
            "beta": 0.92,
        },
        "0005.HK": {
            "company_name": "匯豐控股有限公司",
            "sector": "金融 / 銀行",
            "current_price": 72.15,
            "prev_close": 71.80,
            "day_high": 72.90,
            "day_low": 71.50,
            "volume": 32_000_000,
            "market_cap": 1_450_000_000_000,
            "pe_ratio": 8.2,
            "pb_ratio": 0.85,
            "dividend_yield": 0.072,
            "52w_high": 82.00,
            "52w_low": 58.00,
            "revenue_ttm": 210_000_000_000,
            "net_income_ttm": 175_000_000_000,
            "total_debt": 2_800_000_000_000,
            "cash": 450_000_000_000,
            "ebitda": 220_000_000_000,
            "gross_margin": 0.62,
            "net_margin": 0.28,
            "roe": 0.112,
            "debt_to_equity": 12.5,
            "current_ratio": 1.12,
            "beta": 0.78,
        },
    }

    # Return specific data if available, otherwise generate generic demo data
    if ticker in stock_demos:
        return {**base_data, **stock_demos[ticker]}
    else:
        # Generic fallback for any HK ticker
        return {
            **base_data,
            "company_name": SAMPLE_HK_STOCKS.get(ticker, f"{ticker} 公司"),
            "sector": "綜合企業",
            "current_price": 12.50,
            "prev_close": 12.30,
            "day_high": 12.80,
            "day_low": 12.10,
            "volume": 2_500_000,
            "market_cap": 15_000_000_000,
            "pe_ratio": 9.5,
            "pb_ratio": 1.1,
            "dividend_yield": 0.035,
            "52w_high": 16.00,
            "52w_low": 9.50,
            "revenue_ttm": 8_000_000_000,
            "net_income_ttm": 800_000_000,
            "total_debt": 3_500_000_000,
            "cash": 1_200_000_000,
            "ebitda": 1_500_000_000,
            "gross_margin": 0.22,
            "net_margin": 0.10,
            "roe": 0.12,
            "debt_to_equity": 1.2,
            "current_ratio": 1.35,
            "beta": 1.05,
        }


def get_sample_financial_history(ticker: str) -> Dict[str, Any]:
    """Return sample 3-year financial history for DCF/trend analysis."""
    return {
        "ticker": ticker,
        "is_demo": True,
        "years": ["FY2022", "FY2023", "FY2024E"],
        "revenue": [45_000_000_000, 49_500_000_000, 54_450_000_000],
        "ebitda": [7_200_000_000, 7_920_000_000, 8_712_000_000],
        "net_income": [3_600_000_000, 3_960_000_000, 4_356_000_000],
        "free_cash_flow": [2_800_000_000, 3_080_000_000, 3_388_000_000],
        "total_debt": [16_000_000_000, 17_500_000_000, 18_000_000_000],
        "cash": [5_500_000_000, 6_000_000_000, 6_500_000_000],
        "capex": [1_800_000_000, 1_980_000_000, 2_178_000_000],
        "revenue_growth": [None, 0.10, 0.10],
        "ebitda_margin": [0.16, 0.16, 0.16],
        "net_margin": [0.08, 0.08, 0.08],
    }


def get_sample_news_sentiment(ticker: str) -> Dict[str, Any]:
    """Return sample news sentiment data (placeholder for DEV)."""
    return {
        "ticker": ticker,
        "is_demo": True,
        "last_updated": "示範數據",
        "overall_sentiment": "中性",
        "sentiment_score": 0.52,
        "positive_factors": [
            "公司近期訂單量穩定增長",
            "管理層對全年業績展望正面",
            "行業政策環境持續改善",
        ],
        "negative_factors": [
            "原材料成本上升壓力持續",
            "地緣政治不確定性影響市場情緒",
            "港股整體市場流動性偏弱",
        ],
        "neutral_signals": [
            "公司正進行年度業績審計",
            "行業監管框架調整中",
            "匯率波動對業績影響有限",
        ],
        "recent_headlines": [
            {"title": "【示範】公司公佈季度業績，符合市場預期", "sentiment": "中性", "date": "2025-05-10"},
            {"title": "【示範】管理層出席投資者日，重申增長目標", "sentiment": "正面", "date": "2025-05-08"},
            {"title": "【示範】行業協會發佈最新市場報告", "sentiment": "中性", "date": "2025-05-05"},
        ],
    }


def get_hk_sector_benchmarks() -> Dict[str, Dict]:
    """Return HK sector benchmark multiples for comparison."""
    return {
        "科技 / 互聯網": {"pe_median": 22.0, "pb_median": 3.5, "ev_ebitda_median": 15.0},
        "金融 / 銀行": {"pe_median": 8.5, "pb_median": 0.9, "ev_ebitda_median": 7.0},
        "地產": {"pe_median": 7.0, "pb_median": 0.6, "ev_ebitda_median": 12.0},
        "建築 / 基建": {"pe_median": 6.5, "pb_median": 0.75, "ev_ebitda_median": 6.0},
        "能源": {"pe_median": 9.0, "pb_median": 1.1, "ev_ebitda_median": 5.5},
        "消費": {"pe_median": 18.0, "pb_median": 2.8, "ev_ebitda_median": 12.0},
        "醫療健康": {"pe_median": 28.0, "pb_median": 4.0, "ev_ebitda_median": 18.0},
        "綜合企業": {"pe_median": 10.0, "pb_median": 1.0, "ev_ebitda_median": 8.0},
    }
