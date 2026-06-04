"""
FOS v4.2.5 payload consistency and fresh PDF QA.
"""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from agents.market_data_agent import normalize_market_payload_flags
from core.config import APP_VERSION
from core.investment_conclusion_engine import INSUFFICIENT_DATA_RATING, build_investment_conclusion
from core.pdf_freshness import build_fresh_pdf_path, pdf_path_matches_active_report, should_regenerate_pdf
from core.pdf_generator import sanitize_pdf_payload
from core.source_registry import build_source_registry


PASSED: list[str] = []
FAILED: list[str] = []


def ok(name: str, msg: str = "") -> None:
    PASSED.append(name)
    print(f"  PASS  {name}" + (f" - {msg}" if msg else ""))


def fail(name: str, msg: str) -> None:
    FAILED.append(name)
    print(f"  FAIL  {name} - {msg}")


def _risk_payload() -> dict:
    return {
        "risk_items": [{"risk_name": "Market risk", "score": "4.2/10", "score_raw": 4.2, "weight": "20%", "level": "Medium"}],
        "composite_score": "4.2/10",
        "composite_score_raw": 4.2,
        "composite_risk_score": 4.2,
        "risk_label": "Medium",
    }


def _registry() -> dict:
    return {
        "company_metadata": {"verified": True, "verified_fields": ["name"]},
        "market_data": {"verified": True, "verified_fields": ["price"]},
        "financial_statement": {"verified": True, "verified_fields": ["revenue_ttm", "net_income_ttm"]},
        "news": {"verified": True, "verified_fields": ["positive_catalysts", "risk_events"]},
    }


def _stock_9988_like() -> dict:
    return {
        "ticker": "9988.HK",
        "company_name": "Alibaba Group",
        "sector": "Technology",
        "current_price": 82.35,
        "price_unavailable": True,
        "valid_ticker_price_unavailable": True,
        "market_data_status": "sample_fallback_price_stale",
        "pe_ratio": 14.8,
        "pb_ratio": 1.6,
        "revenue_ttm": 941_000_000_000,
        "net_income_ttm": 79_000_000_000,
        "roe": 0.086,
        "net_margin": 0.084,
        "ebitda": 170_000_000_000,
    }


def test_normalize_clears_stale_price_flags() -> None:
    payload = normalize_market_payload_flags(_stock_9988_like())
    assert payload["price_unavailable"] is False, payload
    assert payload["valid_ticker_price_unavailable"] is False, payload
    ok("normalize-clears-stale-price-flags")


def test_9988_like_payload_can_rate() -> None:
    market = _stock_9988_like()
    result = build_investment_conclusion(
        {"_raw": market},
        market,
        _risk_payload(),
        {"agents": [{"agent_name": "News", "summary": "positive catalyst and risk events"}]},
        [],
        _registry(),
    )
    assert result.get("rating") != INSUFFICIENT_DATA_RATING, result
    assert result.get("data_coverage") in {"PARTIAL", "FULL"}, result
    assert "price_unavailable" in str(result.get("decision_basis", [])), result
    ok("9988-like-not-insufficient", str(result.get("rating")))


def test_source_registry_accepts_ttm_financial_keys() -> None:
    registry = build_source_registry({"market_data": _stock_9988_like(), "financial_analysis": _stock_9988_like()})
    assert registry["financial_statement"]["verified"] is True, registry
    ok("registry-accepts-ttm-financial-keys")


def test_source_registry_accepts_news_catalyst_keys() -> None:
    registry = build_source_registry({
        "market_data": _stock_9988_like(),
        "news_analysis": {"positive_catalysts": ["Cloud recovery"], "risk_events": ["Macro softness"]},
    })
    assert registry["news"]["verified"] is True, registry
    ok("registry-accepts-news-catalyst-keys")


def test_source_registry_market_ignores_stale_unavailable_flag() -> None:
    registry = build_source_registry({"market_data": _stock_9988_like()})
    assert registry["market_data"]["verified"] is True, registry
    assert "price unavailable" not in registry["market_data"]["source"].lower(), registry
    ok("registry-market-verified-with-stale-flag")


def test_pdf_path_version_mismatch_regenerates() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        path = build_fresh_pdf_path("9988.HK", "v4.2.4", tmp, "20260605_120000_000000")
        Path(path).write_bytes(b"%PDF-legacy")
        assert should_regenerate_pdf(path, "9988.HK", APP_VERSION) is True
    ok("pdf-version-mismatch-regenerates")


def test_stale_pdf_path_rejected_for_different_ticker() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        path = build_fresh_pdf_path("0700.HK", APP_VERSION, tmp, "20260605_120000_000000")
        Path(path).write_bytes(b"%PDF-current")
        assert pdf_path_matches_active_report(path, "9988.HK", APP_VERSION) is False
        assert should_regenerate_pdf(path, "9988.HK", APP_VERSION) is True
        assert os.path.exists(path)
    ok("stale-pdf-path-rejected-for-different-ticker")


def test_pdf_payload_removes_legacy_english_terms() -> None:
    payload = {
        "scenario": ["Bull Case", "Base Case", "Bear Case"],
        "conclusion": "Investment Conclusion Engine composite score",
        "disclaimer": {"title": "Disclaimer"},
    }
    sanitized = sanitize_pdf_payload(payload)
    text = str(sanitized)
    for banned in ("Bull Case", "Base Case", "Bear Case", "Disclaimer", "Investment Conclusion Engine composite score"):
        assert banned not in text, text
    ok("pdf-payload-removes-legacy-english-terms")


def run_all() -> bool:
    print("=" * 60)
    print("FOS v4.2.5 Payload Consistency and Fresh PDF QA Suite")
    print("=" * 60)
    for test in (
        test_normalize_clears_stale_price_flags,
        test_9988_like_payload_can_rate,
        test_source_registry_accepts_ttm_financial_keys,
        test_source_registry_accepts_news_catalyst_keys,
        test_source_registry_market_ignores_stale_unavailable_flag,
        test_pdf_path_version_mismatch_regenerates,
        test_stale_pdf_path_rejected_for_different_ticker,
        test_pdf_payload_removes_legacy_english_terms,
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
        print("FOS v4.2.5 Payload Consistency and Fresh PDF QA: ALL PASS")
    print("=" * 60)
    return not FAILED


if __name__ == "__main__":
    sys.exit(0 if run_all() else 1)
