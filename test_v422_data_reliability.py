"""
FOS v4.2.2 Data Reliability and Fallback Layer QA.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from agents.market_data_agent import MarketDataAgent
from core.data_confidence import INVALID
from core.source_registry import (
    build_source_registry,
    compute_confidence_level,
    compute_coverage_pct,
    get_verified_sources,
)
from data.sample_data import SAMPLE_HK_STOCKS


PASSED: list[str] = []
FAILED: list[str] = []


def ok(name: str, msg: str = "") -> None:
    PASSED.append(name)
    print(f"  PASS  {name}" + (f" - {msg}" if msg else ""))


def fail(name: str, msg: str) -> None:
    FAILED.append(name)
    print(f"  FAIL  {name} - {msg}")


def _agent_with_live_failure() -> MarketDataAgent:
    agent = MarketDataAgent()

    def _raise(*_args, **_kwargs):
        raise RuntimeError("simulated yfinance/cache/network failure")

    agent._fetch_live = _raise  # type: ignore[method-assign]
    agent._yfinance_available = True
    return agent


def _registry_for(market_data: dict) -> dict:
    return build_source_registry({"market_data": market_data})


def test_master_data_exists() -> None:
    agent = MarketDataAgent()
    for ticker in ("0006.HK", "1810.HK"):
        metadata = agent._get_company_metadata(ticker)
        assert metadata, f"{ticker} missing from hk_stock_master_data.json"
        assert metadata.get("name_zh") or metadata.get("name_en"), f"{ticker} missing company name"
        assert metadata.get("sector"), f"{ticker} missing sector"
        ok(f"{ticker}-master-data", metadata.get("name_en", "metadata found"))


def test_sample_universe_contains_validated_tickers() -> None:
    for ticker in ("0006.HK", "1810.HK"):
        assert ticker in SAMPLE_HK_STOCKS, f"{ticker} missing from SAMPLE_HK_STOCKS"
        ok(f"{ticker}-sample-universe")


def test_yfinance_failure_with_master_data_is_not_invalid() -> None:
    agent = _agent_with_live_failure()
    for ticker in ("0006.HK", "1810.HK"):
        data = agent.fetch(ticker)
        assert data.get("data_confidence") != INVALID, f"{ticker} incorrectly marked INVALID"
        assert not data.get("invalid_symbol"), f"{ticker} incorrectly flagged invalid_symbol"
        assert data.get("company_metadata"), f"{ticker} lost company_metadata"
        assert data.get("company_name_zh") or data.get("company_name_en"), f"{ticker} lost names"
        if float(data.get("current_price") or 0) > 0:
            assert data.get("price_unavailable") is False, f"{ticker} has price but still marks price_unavailable"
            assert data.get("valid_ticker_price_unavailable") is False, f"{ticker} has price but still marks valid_ticker_price_unavailable"
        else:
            assert data.get("price_unavailable") or data.get("valid_ticker_price_unavailable"), (
                f"{ticker} metadata-only fallback should expose price unavailable status"
            )

        registry = _registry_for(data)
        assert registry["company_metadata"]["verified"] is True, f"{ticker} metadata not verified"
        assert compute_coverage_pct(registry) > 0, f"{ticker} coverage must not be 0"
        assert compute_confidence_level(registry) != INVALID, f"{ticker} registry must not be INVALID"
        verified = get_verified_sources(registry)
        assert "Company Metadata / Master Data" in verified, f"{ticker} missing master data source"

        source = str(data.get("data_source", "")).lower()
        assert data.get("is_live") is False, f"{ticker} fallback must set is_live=False"
        assert "yahoo finance" not in source and "實時" not in source.lower(), (
            f"{ticker} sample fallback must not be labeled live: {data.get('data_source')}"
        )
        ok(f"{ticker}-yf-failure-valid-fallback", f"{data.get('data_confidence')} / {compute_coverage_pct(registry)}%")


def test_invalid_ticker_stays_invalid_without_fake_metadata() -> None:
    agent = _agent_with_live_failure()
    data = agent.fetch("12345")
    assert data.get("data_confidence") == INVALID, "12345 must remain INVALID"
    assert data.get("invalid_symbol") is True, "12345 must flag invalid_symbol"
    assert not data.get("company_metadata"), "12345 must not receive fake company metadata"
    assert not data.get("company_name"), "12345 must not hallucinate company name"
    assert not data.get("sector"), "12345 must not hallucinate sector"

    registry = _registry_for(data)
    assert registry["company_metadata"]["verified"] is False, "12345 metadata must not verify"
    assert compute_confidence_level(registry) == INVALID, "12345 registry must be INVALID"
    ok("12345-invalid-guard")


def run_all() -> bool:
    print("=" * 60)
    print("FOS v4.2.2 Data Reliability QA Suite")
    print("=" * 60)
    for test in (
        test_master_data_exists,
        test_sample_universe_contains_validated_tickers,
        test_yfinance_failure_with_master_data_is_not_invalid,
        test_invalid_ticker_stays_invalid_without_fake_metadata,
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
        print("FOS v4.2.2 Data Reliability QA: ALL PASS")
    print("=" * 60)
    return not FAILED


if __name__ == "__main__":
    sys.exit(0 if run_all() else 1)
