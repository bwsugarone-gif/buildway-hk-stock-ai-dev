"""
core/source_transparency.py
Source Transparency Layer — explains WHERE each major number comes from.
Every data point must have a named source. No hallucinated sources.
Confidence: HIGH / MEDIUM / LOW with explicit reason.
"""
from __future__ import annotations
from typing import Any, Dict, List, Optional


# Known data sources with display names
SOURCE_LABELS = {
    "yahoo_finance":       "Yahoo Finance",
    "company_metadata":    "公司基本資料",
    "financial_statement": "財務報表",
    "news_source":         "新聞來源",
    "hkex_filing":         "港交所披露",
    "market_data_api":     "市場數據 API",
    "calculated":          "系統計算",
    "user_input":          "用戶輸入",
}

# Data fields and their expected sources
FIELD_SOURCE_MAP: Dict[str, str] = {
    "current_price":       "yahoo_finance",
    "week_52_high":        "yahoo_finance",
    "week_52_low":         "yahoo_finance",
    "volume":              "yahoo_finance",
    "market_cap":          "yahoo_finance",
    "pe_ratio":            "yahoo_finance",
    "pb_ratio":            "yahoo_finance",
    "dividend_yield":      "yahoo_finance",
    "beta":                "yahoo_finance",
    "company_name":        "company_metadata",
    "sector":              "company_metadata",
    "industry":            "company_metadata",
    "description":         "company_metadata",
    "revenue":             "financial_statement",
    "net_profit":          "financial_statement",
    "ebitda":              "financial_statement",
    "free_cash_flow":      "financial_statement",
    "operating_cash_flow": "financial_statement",
    "total_assets":        "financial_statement",
    "total_equity":        "financial_statement",
    "debt_to_equity":      "financial_statement",
    "current_ratio":       "financial_statement",
    "quick_ratio":         "financial_statement",
    "roe":                 "financial_statement",
    "net_margin":          "financial_statement",
    "news_items":          "news_source",
    "news_sentiment":      "news_source",
    "hkex_announcements":  "hkex_filing",
    "risk_score":          "calculated",
    "composite_score":     "calculated",
}


def _check_field(data: Dict[str, Any], field: str) -> bool:
    """Return True if field has a non-empty, non-zero value."""
    val = data.get(field)
    if val is None:
        return False
    if isinstance(val, (int, float)):
        return val != 0
    if isinstance(val, str):
        return val.strip() not in ("", "N/A", "None", "0", "0.0")
    if isinstance(val, (list, dict)):
        return len(val) > 0
    return bool(val)


def build_source_transparency(report_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyse report_data and produce a source transparency record.
    Returns:
        sources_present: list of verified source names
        sources_missing: list of missing source names
        field_coverage: dict of field -> source label
        coverage_pct: int (0-100)
        confidence_level: HIGH / MEDIUM / LOW
        confidence_reason: why this level was assigned
        data_gaps: list of important missing fields
    """
    # Flatten all sub-dicts for field checking
    flat: Dict[str, Any] = {}
    for key in ("report_metadata", "market_data", "financial_analysis",
                "financial_history", "risk_analysis", "news_analysis",
                "investment_committee"):
        sub = report_data.get(key)
        if isinstance(sub, dict):
            flat.update(sub)
    # Also check top-level keys
    flat.update({k: v for k, v in report_data.items() if not isinstance(v, dict)})

    # Determine which fields are present
    present_fields: List[str] = []
    missing_fields: List[str] = []
    for field in FIELD_SOURCE_MAP:
        if _check_field(flat, field):
            present_fields.append(field)
        else:
            missing_fields.append(field)

    # Map present fields to their sources
    sources_hit: Dict[str, int] = {}
    field_coverage: Dict[str, str] = {}
    for field in present_fields:
        src_key = FIELD_SOURCE_MAP[field]
        sources_hit[src_key] = sources_hit.get(src_key, 0) + 1
        field_coverage[field] = SOURCE_LABELS.get(src_key, src_key)

    sources_present = [SOURCE_LABELS.get(k, k) for k in sources_hit]
    all_source_keys = set(FIELD_SOURCE_MAP.values())
    sources_missing = [
        SOURCE_LABELS.get(k, k)
        for k in all_source_keys
        if k not in sources_hit and k != "calculated"
    ]

    # Coverage percentage
    total_fields = len(FIELD_SOURCE_MAP)
    coverage_pct = int(len(present_fields) / total_fields * 100) if total_fields > 0 else 0

    # Important fields for confidence scoring
    critical_fields = [
        "current_price", "pe_ratio", "revenue", "net_profit",
        "debt_to_equity", "company_name", "sector",
    ]
    critical_present = sum(1 for f in critical_fields if f in present_fields)
    critical_ratio = critical_present / len(critical_fields)

    # Assign confidence level
    if coverage_pct >= 70 and critical_ratio >= 0.8:
        confidence_level = "HIGH"
        confidence_reason = (
            f"資料覆蓋率 {coverage_pct}%，核心財務及市場數據完整（"
            f"{critical_present}/{len(critical_fields)} 關鍵欄位已驗證）"
        )
    elif coverage_pct >= 40 or critical_ratio >= 0.5:
        confidence_level = "MEDIUM"
        confidence_reason = (
            f"資料覆蓋率 {coverage_pct}%，部分核心數據缺失（"
            f"{critical_present}/{len(critical_fields)} 關鍵欄位已驗證），"
            "結論僅供參考"
        )
    else:
        confidence_level = "LOW"
        confidence_reason = (
            f"資料覆蓋率僅 {coverage_pct}%，核心數據嚴重不足（"
            f"{critical_present}/{len(critical_fields)} 關鍵欄位已驗證），"
            "請補充數據後重新分析"
        )

    # Identify important data gaps
    important_missing = [f for f in missing_fields if f in critical_fields]
    data_gaps = important_missing[:5]  # top 5 gaps

    return {
        "sources_present": sources_present,
        "sources_missing": sources_missing,
        "field_coverage": field_coverage,
        "coverage_pct": coverage_pct,
        "confidence_level": confidence_level,
        "confidence_reason": confidence_reason,
        "data_gaps": data_gaps,
        "present_count": len(present_fields),
        "total_fields": total_fields,
    }


def get_source_for_field(field_name: str) -> str:
    """Return the display source label for a given field name."""
    src_key = FIELD_SOURCE_MAP.get(field_name, "calculated")
    return SOURCE_LABELS.get(src_key, src_key)


def annotate_number(value: Any, field_name: str, fmt: str = "") -> str:
    """
    Return a formatted string like '12.5x (來源: Yahoo Finance)'.
    Used to annotate individual numbers in reports.
    """
    source = get_source_for_field(field_name)
    if fmt:
        try:
            formatted = format(value, fmt)
        except (ValueError, TypeError):
            formatted = str(value)
    else:
        formatted = str(value)
    return f"{formatted}（來源：{source}）"
