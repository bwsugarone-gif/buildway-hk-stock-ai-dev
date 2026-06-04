"""
FOS v4.3.0 client polish QA.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from agents.market_data_agent import MarketDataAgent
from core.client_polish import (
    TARGET_PRICE_EXPLANATION,
    TARGET_PRICE_NOT_PROVIDED,
    UPSIDE_NOT_PROVIDED,
    resolve_logo_path_or_url,
    sanitize_decision_basis,
    sanitize_report_payload,
)
from core.config import APP_VERSION, BUILD_STAGE
from core.investment_conclusion_engine import INSUFFICIENT_DATA_RATING, build_investment_conclusion
from core.pdf_generator import PDFGenerator, sanitize_pdf_payload
from core.report_builder import ReportBuilder


PASSED: list[str] = []
FAILED: list[str] = []


BANNED = (
    "??",
    "????",
    "Bull Case",
    "Base Case",
    "Bear Case",
    "Disclaimer",
    "Investment Conclusion Engine composite score",
    "數據不足，採用中性評分",
    "資料待補充",
    "中性持有",
)


def ok(name: str, msg: str = "") -> None:
    PASSED.append(name)
    print(f"  PASS  {name}" + (f" - {msg}" if msg else ""))


def fail(name: str, msg: str) -> None:
    FAILED.append(name)
    print(f"  FAIL  {name} - {msg}")


def _risk_payload() -> dict:
    items = [
        {"risk_name": "市場風險", "score": "4.2/10", "score_raw": 4.2, "weight": "20%", "level": "中等"},
        {"risk_name": "財務風險", "score": "3.8/10", "score_raw": 3.8, "weight": "20%", "level": "中等"},
        {"risk_name": "估值風險", "score": "4.5/10", "score_raw": 4.5, "weight": "15%", "level": "中等"},
        {"risk_name": "政策風險", "score": "4.0/10", "score_raw": 4.0, "weight": "15%", "level": "中等"},
        {"risk_name": "流動性風險", "score": "3.5/10", "score_raw": 3.5, "weight": "10%", "level": "中等"},
        {"risk_name": "營運風險", "score": "4.1/10", "score_raw": 4.1, "weight": "10%", "level": "中等"},
        {"risk_name": "情景風險", "score": "4.4/10", "score_raw": 4.4, "weight": "10%", "level": "中等"},
    ]
    return {
        "risk_items": items,
        "composite_score": "4.1/10",
        "composite_score_raw": 4.1,
        "composite_risk_score": 4.1,
        "risk_label": "中等風險",
        "top_risks": items[:3],
    }


def _stock_9988_like() -> dict:
    return {
        "ticker": "9988.HK",
        "company_name": "Alibaba Group",
        "company_name_zh": "阿里巴巴集團",
        "sector": "Technology",
        "current_price": 82.35,
        "price_unavailable": False,
        "valid_ticker_price_unavailable": False,
        "pe_ratio": 14.8,
        "pb_ratio": 1.6,
        "market_cap": 1_700_000_000_000,
        "revenue_ttm": 941_000_000_000,
        "net_income_ttm": 79_000_000_000,
        "roe": 0.086,
        "net_margin": 0.084,
        "ebitda": 170_000_000_000,
    }


def _registry() -> dict:
    return {
        "company_metadata": {"verified": True, "verified_fields": ["name"]},
        "market_data": {"verified": True, "verified_fields": ["price"]},
        "financial_statement": {"verified": True, "verified_fields": ["revenue_ttm", "net_income_ttm"]},
        "news": {"verified": True, "verified_fields": ["positive_catalysts", "risk_events"]},
    }


def test_decision_basis_sanitizer() -> None:
    result = sanitize_decision_basis(["??", "", None, "-", "市盈率合理"])
    assert result == [{"factor": "主要依據", "weight": "參考", "score": "未量化", "summary": "市盈率合理"}], result
    ok("decision-basis-sanitizer")


def test_logo_fallback() -> None:
    empty = resolve_logo_path_or_url({"cover": {"logo_url": ""}}, "9988.HK")
    invalid = resolve_logo_path_or_url({"cover": {"logo_url": "not-a-url"}}, "9988.HK")
    assert empty and Path(empty).exists(), empty
    assert invalid and Path(invalid).exists(), invalid
    assert "broken" not in str({"logo": empty}).lower()
    ok("logo-fallback")


def test_target_price_missing_does_not_force_insufficient() -> None:
    market = _stock_9988_like()
    result = build_investment_conclusion(
        {"_raw": market},
        market,
        _risk_payload(),
        {"agents": [{"agent_name": "News", "summary": "news catalyst and risk events"}]},
        [],
        _registry(),
    )
    assert result.get("rating") != INSUFFICIENT_DATA_RATING, result
    assert result.get("target_price") == TARGET_PRICE_NOT_PROVIDED, result
    assert result.get("potential_upside") == UPSIDE_NOT_PROVIDED, result
    assert result.get("target_price_explanation") == TARGET_PRICE_EXPLANATION, result
    ok("target-price-missing-not-insufficient", str(result.get("rating")))


def test_invalid_ticker_guard() -> None:
    result = build_investment_conclusion({"_raw": {"invalid_symbol": True}}, {"invalid_symbol": True}, {}, {}, [], {})
    assert result.get("data_coverage") == "INVALID", result
    assert result.get("invalid_symbol") is True, result
    ok("invalid-ticker-guard")


def test_metadata_only_fallback_not_invalid() -> None:
    for ticker in ("0006.HK", "1810.HK"):
        market = {"ticker": ticker, "company_name": ticker, "price_unavailable": True, "current_price": 0}
        result = build_investment_conclusion({"_raw": market}, market, {}, {}, [], {"company_metadata": {"verified": True}})
        assert result.get("rating") == INSUFFICIENT_DATA_RATING, result
        assert result.get("data_coverage") == "INSUFFICIENT", result
    ok("metadata-only-fallback-insufficient")


def test_payload_has_no_placeholder_pollution() -> None:
    market = _stock_9988_like()
    package = {
        "report_metadata": {"stock_code": "9988.HK"},
        "market_data": market,
        "financial_analysis": market,
        "risk_analysis": _risk_payload(),
        "news_analysis": {"positive_catalysts": ["Cloud recovery"], "risk_events": ["Macro softness"]},
    }
    sections = ReportBuilder().build(package)
    payload = str(sanitize_report_payload(sections))
    for banned in BANNED:
        assert banned not in payload, banned
    ok("payload-no-placeholder-pollution")


def test_pdf_text_sanitizer_and_dashboard() -> None:
    payload = sanitize_pdf_payload({
        "scenario": ["Bull Case", "Base Case", "Bear Case", "??"],
        "conclusion": "Investment Conclusion Engine composite score",
        "disclaimer": "Disclaimer",
    })
    text = str(payload)
    for banned in BANNED:
        assert banned not in text, banned
    pdf = PDFGenerator()
    dashboard = pdf._risk_dashboard(_risk_payload())
    assert dashboard is not None, "risk dashboard should still render"
    ok("pdf-sanitizer-and-risk-dashboard")


def test_app_version() -> None:
    assert APP_VERSION == "v4.3.0", APP_VERSION
    assert BUILD_STAGE == "Client Polish Release", BUILD_STAGE
    ok("app-version")


def run_all() -> bool:
    print("=" * 60)
    print("FOS v4.3.0 Client Polish QA Suite")
    print("=" * 60)
    for test in (
        test_decision_basis_sanitizer,
        test_logo_fallback,
        test_target_price_missing_does_not_force_insufficient,
        test_invalid_ticker_guard,
        test_metadata_only_fallback_not_invalid,
        test_payload_has_no_placeholder_pollution,
        test_pdf_text_sanitizer_and_dashboard,
        test_app_version,
    ):
        try:
            test()
        except Exception as exc:
            fail(test.__name__, str(exc))

    total = len(PASSED) + len(FAILED)
    print("\n" + "=" * 60)
    print(f"RESULT: {len(PASSED)}/{total} PASS")
    if FAILED:
        print(f"FAILED: {FAILED}")
    else:
        print("FOS v4.3.0 Client Polish QA: ALL PASS")
    print("=" * 60)
    return not FAILED


if __name__ == "__main__":
    sys.exit(0 if run_all() else 1)
