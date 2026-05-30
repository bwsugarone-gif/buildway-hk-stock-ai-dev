"""
core/source_registry.py
Single Source Registry — v4.0 Hardening Layer

All components (UI, PDF, source_transparency, data_lake) must read from
report_package["source_registry"] — never generate their own source lists.

Schema per source:
{
  "enabled": bool,
  "verified": bool,
  "source": str,
  "last_updated": str,
  "verified_fields": list[str],
  "missing_fields": list[str],
  "note": str  (optional explanation)
}
"""

from datetime import datetime
from core.hkex_engine import get_hkex_source_registry_entry


def build_source_registry(report_package: dict) -> dict:
    """
    Build the single source registry from a report_package.
    This is the authoritative source list for the entire report.

    All UI sections, PDF pages, and data lake entries must use this registry.
    """
    meta = report_package.get("report_metadata", {})
    market = report_package.get("market_data", {})
    # Support both key names: company_metadata (legacy) and market_data sub-fields
    company = (
        report_package.get("company_metadata")
        or report_package.get("company_data")
        or {}
    )
    # If company_metadata is empty, fall back to market_data fields
    if not company.get("name_zh") and not company.get("name_en"):
        company = {
            "name_zh": market.get("company_name_zh") or market.get("company_name", ""),
            "name_en": market.get("company_name_en") or market.get("company_name", ""),
            "sector": market.get("sector", ""),
            "business_profile": market.get("business_summary", ""),
            "market_category": market.get("market_category", ""),
        }
    # Support both key names: financial_data (legacy) and financial_analysis (v4)
    fin_raw = (
        report_package.get("financial_data")
        or report_package.get("financial_analysis")
        or {}
    )
    # Flatten financial_analysis sub-dicts into a single lookup dict
    financials = dict(fin_raw)
    for sub_key in ("metrics", "comps", "health_score"):
        sub = fin_raw.get(sub_key, {})
        if isinstance(sub, dict):
            financials.update(sub)
    # Also check financial_history for revenue
    fin_history = report_package.get("financial_history", {})
    if not financials.get("revenue") and fin_history.get("revenue"):
        financials["revenue"] = fin_history["revenue"][0] if isinstance(fin_history["revenue"], list) else fin_history["revenue"]
    # Support both key names: news_data (legacy) and news_analysis (v4)
    news = (
        report_package.get("news_data")
        or report_package.get("news_analysis")
        or {}
    )
    now = datetime.now().strftime("%Y-%m-%d")

    # ── Market Data (Yahoo Finance / yfinance) ────────────────────────────────
    market_verified = bool(market.get("current_price") or market.get("price"))
    market_fields = []
    market_missing = []
    for field, label in [
        ("current_price", "現價"),
        ("pe_ratio", "市盈率"),
        ("pb_ratio", "市帳率"),
        ("dividend_yield", "股息率"),
        ("market_cap", "市值"),
        ("fifty_two_week_high", "52週高位"),
        ("fifty_two_week_low", "52週低位"),
        ("volume", "成交量"),
        ("beta", "Beta"),
    ]:
        val = market.get(field) or market.get(field.replace("_", ""))
        if val and str(val) not in ("0", "0.0", "None", ""):
            market_fields.append(label)
        else:
            market_missing.append(label)

    # ── Company Metadata ──────────────────────────────────────────────────────
    meta_verified = bool(company.get("name_zh") or company.get("name_en"))
    meta_fields = []
    meta_missing = []
    for field, label in [
        ("name_zh", "中文名稱"),
        ("name_en", "英文名稱"),
        ("sector", "行業板塊"),
        ("business_profile", "業務簡介"),
        ("market_category", "市場類別"),
    ]:
        if company.get(field) and str(company[field]).strip() not in ("", "未知", "N/A"):
            meta_fields.append(label)
        else:
            meta_missing.append(label)

    # ── Financial Statement ───────────────────────────────────────────────────
    fin_verified = bool(financials.get("revenue") or financials.get("revenue_trend"))
    fin_fields = []
    fin_missing = []
    for field, label in [
        ("revenue", "收入"),
        ("net_profit", "淨利潤"),
        ("ebitda", "EBITDA"),
        ("free_cash_flow", "自由現金流"),
        ("gross_margin", "毛利率"),
        ("net_margin", "淨利率"),
        ("roe", "ROE"),
        ("total_assets", "總資產"),
        ("total_debt", "總負債"),
    ]:
        if financials.get(field) and str(financials[field]).strip() not in ("", "N/A", "0"):
            fin_fields.append(label)
        else:
            fin_missing.append(label)

    # ── News ──────────────────────────────────────────────────────────────────
    news_items = news.get("items", news.get("news_items", []))
    news_verified = len(news_items) > 0
    news_fields = ["新聞標題", "新聞來源"] if news_verified else []
    news_missing = [] if news_verified else ["新聞資料"]

    # ── HKEX (always from hkex_engine — never self-generate) ─────────────────
    hkex_entry = get_hkex_source_registry_entry()

    registry = {
        "market_data": {
            "enabled": True,
            "verified": market_verified,
            "source": "Yahoo Finance / yfinance",
            "last_updated": now,
            "verified_fields": market_fields,
            "missing_fields": market_missing,
            "note": "" if market_verified else "市場數據未能取得，使用本地參考數據。",
        },
        "company_metadata": {
            "enabled": True,
            "verified": meta_verified,
            "source": "本地公司資料庫 / HK Stock Master Data",
            "last_updated": now,
            "verified_fields": meta_fields,
            "missing_fields": meta_missing,
            "note": "" if meta_verified else "公司資料未收錄，請確認股票代碼是否正確。",
        },
        "financial_statement": {
            "enabled": True,
            "verified": fin_verified,
            "source": "Yahoo Finance 財務報表 / yfinance",
            "last_updated": now,
            "verified_fields": fin_fields,
            "missing_fields": fin_missing,
            "note": "" if fin_verified else "財務報表數據未能取得，部分財務分析可能不完整。",
        },
        "news": {
            "enabled": True,
            "verified": news_verified,
            "source": "TipRanks / Yahoo Finance News",
            "last_updated": now,
            "verified_fields": news_fields,
            "missing_fields": news_missing,
            "note": "" if news_verified else "新聞資料未能取得，新聞分析將顯示為不可用。",
        },
        "hkex": hkex_entry,
    }

    return registry


def get_verified_sources(registry: dict) -> list:
    """Return list of verified source names for display."""
    verified = []
    labels = {
        "market_data": "Yahoo Finance",
        "company_metadata": "公司資料庫",
        "financial_statement": "財務報表",
        "news": "新聞資料",
        "hkex": "HKEX 披露易",
    }
    for key, label in labels.items():
        entry = registry.get(key, {})
        if entry.get("verified"):
            verified.append(label)
    return verified


def get_unverified_sources(registry: dict) -> list:
    """Return list of unverified/disabled source names for display."""
    unverified = []
    labels = {
        "market_data": "Yahoo Finance",
        "company_metadata": "公司資料庫",
        "financial_statement": "財務報表",
        "news": "新聞資料",
        "hkex": "HKEX 披露易",
    }
    for key, label in labels.items():
        entry = registry.get(key, {})
        if not entry.get("verified"):
            unverified.append(label)
    return unverified


def compute_coverage_pct(registry: dict) -> float:
    """
    Compute overall data coverage percentage from registry.
    Based on verified_fields vs total expected fields per source.
    """
    total_expected = 0
    total_verified = 0

    weights = {
        "market_data": 9,       # 9 expected fields
        "company_metadata": 5,  # 5 expected fields
        "financial_statement": 9,
        "news": 2,
        "hkex": 0,              # HKEX not counted in coverage (optional module)
    }

    for key, expected_count in weights.items():
        if expected_count == 0:
            continue
        entry = registry.get(key, {})
        verified_count = len(entry.get("verified_fields", []))
        total_expected += expected_count
        total_verified += min(verified_count, expected_count)

    if total_expected == 0:
        return 0.0
    return round((total_verified / total_expected) * 100, 1)


def compute_confidence_level(registry: dict) -> str:
    """
    Compute overall confidence level from registry.
    HIGH: market + metadata + financials all verified
    MEDIUM: market + metadata verified, financials partial
    LOW: only metadata or less
    """
    mkt = registry.get("market_data", {}).get("verified", False)
    meta = registry.get("company_metadata", {}).get("verified", False)
    fin = registry.get("financial_statement", {}).get("verified", False)
    news = registry.get("news", {}).get("verified", False)

    verified_count = sum([mkt, meta, fin, news])

    if verified_count >= 3 and mkt and meta:
        return "HIGH"
    elif verified_count >= 2 and meta:
        return "MEDIUM"
    else:
        return "LOW"
