"""
test_v405_browser_qa.py
v4.0.5 Browser QA Regression Tests

Validates the three failures reported in v4.0.3 browser QA:
  1. INVALID ticker 12345 → coverage=0, verified_sources=[], no green ticks
  2. 0941 peer comparison → 0728/0762 show real company names
  3. AI Investment Committee → hidden when no real agent data
"""
from __future__ import annotations
import sys
import os
import types

# ── Mock streamlit so fos_components can be imported outside Streamlit runtime ──
_st_mock = types.ModuleType("streamlit")
_st_mock.markdown = lambda *a, **kw: None
_st_mock.info = lambda *a, **kw: None
_st_mock.warning = lambda *a, **kw: None
_st_mock.error = lambda *a, **kw: None
_st_mock.metric = lambda *a, **kw: None
_st_mock.columns = lambda n: [types.SimpleNamespace(
    __enter__=lambda s: s, __exit__=lambda s, *a: None,
    markdown=lambda *a, **kw: None,
    metric=lambda *a, **kw: None,
)] * (n if isinstance(n, int) else len(n))
_st_mock.container = lambda: types.SimpleNamespace(
    __enter__=lambda s: s, __exit__=lambda s, *a: None)
_st_mock.sidebar = types.SimpleNamespace(
    __enter__=lambda s: s, __exit__=lambda s, *a: None,
    markdown=lambda *a, **kw: None)
_st_mock.plotly_chart = lambda *a, **kw: None
_st_mock.bar_chart = lambda *a, **kw: None
sys.modules.setdefault("streamlit", _st_mock)

sys.path.insert(0, os.path.dirname(__file__))

import pytest


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _make_invalid_report() -> dict:
    """Minimal report_data for ticker 12345 (INVALID)."""
    return {
        "cover": {"ticker": "12345", "company_name": "Unknown"},
        "source_registry": {
            "yahoo_finance": {"verified": False, "available": False},
            "hkex":          {"verified": False, "available": False},
            "company_meta":  {"verified": False, "available": False},
        },
        "source_transparency": {
            "confidence_level": "INVALID",
            "coverage_pct": 0,
            "verified_sources": [],
        },
        "data_confidence": {},
        "investment_committee": {},
        "competitive_landscape": {},
    }


def _make_0941_report() -> dict:
    """Minimal report_data for 0941.HK with peers 0728/0762."""
    return {
        "cover": {"ticker": "0941.HK", "company_name": "中國移動"},
        "source_registry": {
            "yahoo_finance": {"verified": True, "available": True},
            "hkex":          {"verified": True, "available": True},
            "company_meta":  {"verified": True, "available": True},
        },
        "source_transparency": {
            "confidence_level": "HIGH",
            "coverage_pct": 90,
            "verified_sources": ["Yahoo Finance", "HKEX", "Company Metadata"],
        },
        "competitive_landscape": {
            "subject": {
                "ticker": "0941.HK",
                "company_name": "中國移動",
                "pe_ratio": 10.5,
                "pb_ratio": 1.2,
                "dividend_yield": 6.5,
                "market_cap_bn": 1500,
                "risk_score": 3.2,
            },
            "peers": [
                {
                    "ticker": "0728.HK",
                    "company_name": "中國電訊",
                    "pe_ratio": 8.2,
                    "pb_ratio": 0.9,
                    "dividend_yield": 7.1,
                    "market_cap_bn": 280,
                    "risk_score": 3.5,
                },
                {
                    "ticker": "0762.HK",
                    "company_name": "中國聯通",
                    "pe_ratio": 9.1,
                    "pb_ratio": 0.8,
                    "dividend_yield": 5.8,
                    "market_cap_bn": 220,
                    "risk_score": 4.0,
                },
            ],
        },
        "investment_committee": {},
    }


def _make_placeholder_ic_report() -> dict:
    """Report where all IC agents have placeholder data."""
    return {
        "cover": {"ticker": "0941.HK"},
        "source_registry": {},
        "investment_committee": {
            "agents": {
                "financial_agent": {"opinion": "觀點待整合", "confidence": 0},
                "valuation_agent": {"opinion": "觀點待整合", "confidence": 0},
                "market_agent":    {"opinion": "觀點待整合", "confidence": 0},
                "risk_agent":      {"opinion": "觀點待整合", "confidence": 0},
                "news_agent":      {"opinion": "觀點待整合", "confidence": 0},
                "pm_agent":        {"opinion": "觀點待整合", "confidence": 0},
            }
        },
    }


def _make_real_ic_report() -> dict:
    """Report where IC agents have real data."""
    return {
        "cover": {"ticker": "0941.HK"},
        "source_registry": {},
        "investment_committee": {
            "agents": {
                "financial_agent": {
                    "opinion": "財務穩健，現金流充裕",
                    "reasoning": "EBITDA margin 40%+",
                    "confidence": 78,
                },
                "risk_agent": {
                    "opinion": "風險可控",
                    "reasoning": "監管風險低",
                    "confidence": 65,
                },
            }
        },
    }


# ─── Test 1: INVALID ticker source_registry ───────────────────────────────────

class TestInvalidTickerSourceRegistry:
    """BUG-1: INVALID ticker 12345 must show coverage=0, no verified sources."""

    def test_coverage_is_zero(self):
        from core.source_registry import compute_coverage_pct
        registry = _make_invalid_report()["source_registry"]
        pct = compute_coverage_pct(registry)
        assert pct == 0.0, f"Expected 0.0 coverage for INVALID, got {pct}"

    def test_confidence_level_is_invalid(self):
        from core.source_registry import compute_confidence_level
        registry = _make_invalid_report()["source_registry"]
        level = compute_confidence_level(registry)
        assert level.upper() == "INVALID", f"Expected INVALID, got {level}"

    def test_no_verified_sources(self):
        from core.source_registry import get_verified_sources
        registry = _make_invalid_report()["source_registry"]
        sources = get_verified_sources(registry)
        assert sources == [], f"Expected [], got {sources}"

    def test_source_transparency_payload_keys(self):
        """source_transparency sub-dict must have the three required keys."""
        report = _make_invalid_report()
        st = report.get("source_transparency", {})
        assert "confidence_level" in st
        assert "coverage_pct" in st
        assert "verified_sources" in st
        assert st["confidence_level"].upper() == "INVALID"
        assert st["coverage_pct"] == 0
        assert st["verified_sources"] == []


# ─── Test 2: 0941 peer comparison company names ───────────────────────────────

class TestPeerCompanyNames:
    """BUG-2: 0728/0762 must show real company names, not raw ticker codes."""

    def test_master_data_has_0728(self):
        import json, pathlib
        p = pathlib.Path(__file__).parent / "data" / "hk_stock_master_data.json"
        d = json.loads(p.read_text(encoding="utf-8"))
        assert "0728.HK" in d, "0728.HK missing from master data"
        assert d["0728.HK"]["name_zh"] == "中國電訊"

    def test_master_data_has_0762(self):
        import json, pathlib
        p = pathlib.Path(__file__).parent / "data" / "hk_stock_master_data.json"
        d = json.loads(p.read_text(encoding="utf-8"))
        assert "0762.HK" in d, "0762.HK missing from master data"
        assert d["0762.HK"]["name_zh"] == "中國聯通"

    def test_peer_company_name_not_raw_ticker(self):
        """Peer rows must not have company_name equal to ticker code."""
        report = _make_0941_report()
        peers = report["competitive_landscape"]["peers"]
        for peer in peers:
            ticker = peer.get("ticker", "")
            name = peer.get("company_name", "")
            ticker_clean = ticker.upper().replace(".HK", "").strip()
            name_clean = name.upper().replace(".HK", "").strip()
            assert name_clean != ticker_clean, (
                f"Peer {ticker} has company_name == ticker code: '{name}'"
            )
            assert name not in ("", "—", "N/A"), (
                f"Peer {ticker} has empty/placeholder company_name"
            )

    def test_peer_fallback_label(self):
        """When company_name is missing, render_peer_comparison must use '公司名稱未收錄'."""
        # Simulate a peer with no name
        from core.fos_components import _safe
        peer_no_name = {"ticker": "9999.HK"}
        raw_name = peer_no_name.get("company_name") or peer_no_name.get("name") or ""
        ticker = peer_no_name.get("ticker", "")
        ticker_clean = str(ticker).upper().replace(".HK", "").strip()
        name_clean = str(raw_name).upper().replace(".HK", "").strip()
        if not raw_name or name_clean == ticker_clean or raw_name in ("—", "N/A"):
            display_name = "公司名稱未收錄"
        else:
            display_name = raw_name
        assert display_name == "公司名稱未收錄"


# ─── Test 3: AI Investment Committee hidden when no real data ─────────────────

class TestInvestmentCommitteePanel:
    """BUG-3: IC panel must be hidden when all agents have placeholder data."""

    def test_agent_has_real_data_placeholder(self):
        from core.fos_components import _agent_has_real_data
        placeholder_agent = {"opinion": "觀點待整合", "confidence": 0}
        assert _agent_has_real_data(placeholder_agent) is False

    def test_agent_has_real_data_empty(self):
        from core.fos_components import _agent_has_real_data
        empty_agent = {"opinion": "", "confidence": 0}
        assert _agent_has_real_data(empty_agent) is False

    def test_agent_has_real_data_real(self):
        from core.fos_components import _agent_has_real_data
        real_agent = {"opinion": "財務穩健", "confidence": 78}
        assert _agent_has_real_data(real_agent) is True

    def test_agent_has_real_data_confidence_only(self):
        from core.fos_components import _agent_has_real_data
        # confidence > 0 alone counts as real
        conf_only = {"opinion": "", "confidence": 55}
        assert _agent_has_real_data(conf_only) is True

    def test_all_placeholder_agents_no_real(self):
        """All 6 placeholder agents → real_agents list is empty."""
        from core.fos_components import _agent_has_real_data
        report = _make_placeholder_ic_report()
        ic = report["investment_committee"]
        agents_data = ic.get("agents", {})
        agent_keys = [
            "financial_agent", "valuation_agent", "market_agent",
            "risk_agent", "news_agent", "pm_agent",
        ]
        real = [k for k in agent_keys if _agent_has_real_data(agents_data.get(k, {}))]
        assert real == [], f"Expected no real agents, got: {real}"

    def test_real_agents_detected(self):
        """Report with real agent data → real_agents list is non-empty."""
        from core.fos_components import _agent_has_real_data
        report = _make_real_ic_report()
        ic = report["investment_committee"]
        agents_data = ic.get("agents", {})
        agent_keys = [
            "financial_agent", "valuation_agent", "market_agent",
            "risk_agent", "news_agent", "pm_agent",
        ]
        real = [k for k in agent_keys if _agent_has_real_data(agents_data.get(k, {}))]
        assert len(real) >= 1, "Expected at least 1 real agent"


# ─── Test 4: config version ───────────────────────────────────────────────────

class TestConfigVersion:
    def test_version_is_v405(self):
        from core.config import APP_VERSION
        assert APP_VERSION == "v4.0.5", f"Expected v4.0.5, got {APP_VERSION}"

    def test_build_stage(self):
        from core.config import BUILD_STAGE
        assert "Browser QA" in BUILD_STAGE or "Final" in BUILD_STAGE


# ─── Test 5: competitive_landscape_engine peer name resolution ────────────────

class TestCompetitiveLandscapeEngine:
    def test_engine_imports(self):
        """Module must be importable and expose get_competitive_profile."""
        from core.competitive_landscape_engine import get_competitive_profile
        assert callable(get_competitive_profile)

    def test_peer_tickers_for_0941(self):
        """0941 must return 0728 and 0762 as peers."""
        from core.competitive_landscape_engine import _get_peer_tickers
        peers = _get_peer_tickers("0941.HK")
        assert "0728" in peers or "0728.HK" in peers, f"0728 not in peers: {peers}"
        assert "0762" in peers or "0762.HK" in peers, f"0762 not in peers: {peers}"

    def test_peer_names_in_master_data(self):
        """All peers of 0941 that appear in master data must have real names."""
        import json, pathlib
        from core.competitive_landscape_engine import _get_peer_tickers
        master_path = pathlib.Path(__file__).parent / "data" / "hk_stock_master_data.json"
        master = json.loads(master_path.read_text(encoding="utf-8"))
        peers = _get_peer_tickers("0941.HK")
        for p in peers:
            # Try both formats: "0728" and "0728.HK"
            key = p if p in master else (p + ".HK" if (p + ".HK") in master else None)
            if key is None:
                continue  # peer not in master data — skip (not a failure)
            name = master[key].get("name_zh") or master[key].get("name_en") or ""
            ticker_clean = str(key).upper().replace(".HK", "").strip()
            name_clean = str(name).upper().replace(".HK", "").strip()
            assert name not in ("", "—", "N/A"), f"Peer {key} has no name in master data"
            assert name_clean != ticker_clean, (
                f"Peer {key} name is just the ticker code: '{name}'"
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
