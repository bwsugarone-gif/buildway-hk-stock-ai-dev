"""
FOS v4.2.3 Investment Data Sufficiency Gate QA.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from agents.market_data_agent import MarketDataAgent
from core.data_confidence import INVALID
from core.investment_conclusion_engine import build_investment_conclusion
from core.source_registry import build_source_registry


PASSED: list[str] = []
FAILED: list[str] = []


def ok(name: str, msg: str = "") -> None:
    PASSED.append(name)
    print(f"  PASS  {name}" + (f" - {msg}" if msg else ""))


def fail(name: str, msg: str) -> None:
    FAILED.append(name)
    print(f"  FAIL  {name} - {msg}")


def _assert_insufficient(result: dict, label: str) -> None:
    assert result.get("rating") == "資料不足", f"{label} rating should be 資料不足: {result.get('rating')}"
    assert result.get("composite_score") in (None, "N/A"), f"{label} must not expose 5.0 score"
    assert result.get("recommendation") == "暫不評級", f"{label} should be 暫不評級"
    text = str(result)
    assert "5.0/10" not in text, f"{label} leaked 5.0 baseline"
    assert "中性" not in text, f"{label} leaked neutral conclusion"
    assert result.get("target_price") is None, f"{label} target price should be None"
    assert result.get("potential_upside") is None, f"{label} upside should be None"
    assert result.get("allocation_suggestion") is None, f"{label} allocation should be None"
    assert result.get("suitable_investor") is None, f"{label} suitable investor should be None"
    assert result.get("decision_basis"), f"{label} should list missing data"


def _agent_with_live_failure() -> MarketDataAgent:
    agent = MarketDataAgent()

    def _raise(*_args, **_kwargs):
        raise RuntimeError("simulated yfinance/cache/network failure")

    agent._fetch_live = _raise  # type: ignore[method-assign]
    agent._yfinance_available = True
    return agent


def _conclusion_for_market_data(market_data: dict) -> dict:
    registry = build_source_registry({"market_data": market_data})
    return build_investment_conclusion(
        {"_raw": market_data},
        market_data,
        {},
        {},
        [],
        registry,
    )


def test_empty_data_is_not_neutral() -> None:
    result = build_investment_conclusion({}, {}, {}, {}, [], {})
    _assert_insufficient(result, "empty-data")
    ok("empty-data-insufficient")


def test_metadata_only_valid_ticker_is_not_neutral() -> None:
    market_data = {
        "ticker": "0006.HK",
        "company_name": "Power Assets Holdings",
        "company_name_zh": "電能實業",
        "company_name_en": "Power Assets Holdings",
        "sector": "Utilities",
        "price_unavailable": True,
        "valid_ticker_price_unavailable": True,
        "current_price": 0,
        "market_cap": 0,
    }
    result = _conclusion_for_market_data(market_data)
    _assert_insufficient(result, "metadata-only")
    ok("metadata-only-insufficient")


def test_0006_and_1810_yfinance_failure_are_insufficient() -> None:
    agent = _agent_with_live_failure()
    for ticker in ("0006.HK", "1810.HK"):
        market_data = agent.fetch(ticker)
        result = _conclusion_for_market_data(market_data)
        _assert_insufficient(result, ticker)
        ok(f"{ticker}-insufficient", result.get("investment_view", ""))


def test_12345_stays_invalid() -> None:
    agent = _agent_with_live_failure()
    market_data = agent.fetch("12345")
    assert market_data.get("data_confidence") == INVALID, "12345 must remain INVALID"
    assert market_data.get("invalid_symbol") is True, "12345 must flag invalid_symbol"
    assert not market_data.get("company_metadata"), "12345 must not receive fake metadata"
    result = _conclusion_for_market_data(market_data)
    assert result.get("rating") == "無法評估", f"12345 conclusion must be invalid/no rating: {result}"
    assert result.get("invalid_symbol") is True, "12345 conclusion must keep invalid guard"
    ok("12345-invalid")


def test_full_data_can_receive_normal_rating() -> None:
    market = {
        "ticker": "0700.HK",
        "company_name": "Tencent Holdings",
        "current_price": 385.0,
        "market_cap": 3_600_000_000_000,
        "pe_ratio": 18.0,
        "pb_ratio": 3.0,
        "52w_high": 450.0,
        "52w_low": 280.0,
        "revenue": 650_000_000_000,
        "net_profit": 120_000_000_000,
        "roe": 18.0,
        "net_margin": 18.0,
        "ebitda": 180_000_000_000,
    }
    registry = {
        "market_data": {
            "verified": True,
            "verified_fields": ["price", "pe", "pb", "dividend", "market_cap", "52w_high", "52w_low", "volume", "beta"],
        },
        "company_metadata": {
            "verified": True,
            "verified_fields": ["name_zh", "name_en", "sector", "business", "market_type"],
        },
        "financial_statement": {
            "verified": True,
            "verified_fields": ["revenue", "net_profit", "ebitda", "fcf", "gross_margin", "net_margin", "roe", "assets", "debt"],
        },
        "news": {"verified": True, "verified_fields": ["headline", "source"]},
    }
    result = build_investment_conclusion(
        {"_raw": market},
        market,
        {"composite_score": "4.8/10", "risk_items": [{"risk_name": "Market risk"}]},
        {"agents": [{"agent_name": "News Intelligence Agent", "stance": "正面", "confidence": 70}]},
        [],
        registry,
    )
    assert result.get("rating") != "資料不足", f"full data should rate normally: {result}"
    assert result.get("composite_score") not in (None, "N/A"), "full data should have composite score"
    ok("full-data-normal-rating", f"{result.get('rating')} / {result.get('composite_score')}")


def test_ui_text_hygiene() -> None:
    app_text = Path("app.py").read_text(encoding="utf-8")
    fos_text = Path("core/fos_components.py").read_text(encoding="utf-8")
    combined = app_text + "\n" + fos_text
    assert "數據不足，採用中性評分" not in combined
    assert "中性持有" not in combined
    assert "#### ????" not in fos_text
    assert 'st.markdown("## ??' not in fos_text
    ok("ui-text-hygiene")


def run_all() -> bool:
    print("=" * 60)
    print("FOS v4.2.3 Investment Sufficiency Gate QA Suite")
    print("=" * 60)
    for test in (
        test_empty_data_is_not_neutral,
        test_metadata_only_valid_ticker_is_not_neutral,
        test_0006_and_1810_yfinance_failure_are_insufficient,
        test_12345_stays_invalid,
        test_full_data_can_receive_normal_rating,
        test_ui_text_hygiene,
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
        print("FOS v4.2.3 Investment Sufficiency Gate QA: ALL PASS")
    print("=" * 60)
    return not FAILED


if __name__ == "__main__":
    sys.exit(0 if run_all() else 1)
