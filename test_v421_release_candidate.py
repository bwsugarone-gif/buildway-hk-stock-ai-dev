"""
test_v421_release_candidate.py
FOS v4.2.1 RC Sprint — Automated QA
RC-1: Competitive Summary Enrichment
RC-2: Investment Committee 2.0
RC-3: Institutional Source Registry
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────
PASSED = []
FAILED = []

def ok(name, msg=""):
    PASSED.append(name)
    print(f"  ✓ PASS  {name}" + (f" — {msg}" if msg else ""))

def fail(name, msg):
    FAILED.append(name)
    print(f"  ✗ FAIL  {name} — {msg}")


# ─────────────────────────────────────────────
# TEST CONFIG VERSION
# ─────────────────────────────────────────────
def test_config_version():
    print("\n[CONFIG] Version check")
    try:
        from core.config import APP_VERSION, BUILD_STAGE
        assert APP_VERSION == "v4.2.1", f"Expected v4.2.1, got {APP_VERSION}"
        assert "RC" in BUILD_STAGE, f"BUILD_STAGE must contain RC: {BUILD_STAGE}"
        ok("CONFIG-version", f"{APP_VERSION} / {BUILD_STAGE}")
    except Exception as e:
        fail("CONFIG-version", str(e))


# ─────────────────────────────────────────────
# RC-1: Competitive Summary Enrichment
# ─────────────────────────────────────────────
def test_rc1_competitive_summary():
    print("\n[RC-1] Competitive summary enrichment")
    try:
        from core.competitive_landscape_engine import build_competitive_landscape

        # build_competitive_landscape(ticker, report_data)
        report_data = {
            "market_data": {
                "ticker": "0700",
                "company_name": "騰訊控股",
                "sector": "科技",
                "current_price": 350.0,
                "pe_ratio": 18.0,
                "market_cap": 3_400_000_000_000,
            },
            "company_metadata": {
                "name_zh": "騰訊控股",
                "sector": "科技",
            },
        }
        cl = build_competitive_landscape("0700", report_data)
        peers = cl.get("peers", [])

        # Must have at least one peer
        assert len(peers) > 0, "No peers returned"
        ok("RC-1-peers-exist", f"{len(peers)} peers")

        # Each peer must have readable content
        banned_summaries = ["", "*", "空白", "待補充", "N/A", "n/a"]
        for p in peers:
            pticker = p.get("ticker", p.get("name", "?"))
            products = p.get("product_lines", [])
            summary = p.get("summary", "")

            has_products = isinstance(products, list) and len(products) > 0
            has_summary = (
                isinstance(summary, str)
                and summary.strip() not in banned_summaries
                and len(summary.strip()) > 4
            )

            assert has_products or has_summary, (
                f"Peer {pticker} has no readable content: "
                f"products={products}, summary='{summary}'"
            )
            ok(f"RC-1-peer-{pticker}", summary[:40] if has_summary else str(products[:2]))

        # No peer may show banned placeholder text
        for p in peers:
            for field in ["summary", "products_text"]:
                val = str(p.get(field, ""))
                for ban in ["來源不明", "待補充", "暫無資料 (placeholder)"]:
                    assert ban not in val, (
                        f"Banned text '{ban}' found in peer field '{field}'"
                    )
        ok("RC-1-no-banned-placeholders")

    except Exception as e:
        fail("RC-1", str(e))


# ─────────────────────────────────────────────
# RC-2: Investment Committee 2.0
# ─────────────────────────────────────────────
def _make_ic_inputs():
    """Build minimal valid inputs for build_investment_conclusion."""
    market_snapshot = {
        "ticker": "0941",
        "company_name": "中國移動",
        "current_price": 68.0,
        "pe_ratio": 12.0,
        "pb_ratio": 1.1,
        "dividend_yield": 0.065,
        "market_cap": 1_500_000_000_000,
    }
    financial_data = {
        "revenue_growth": 0.08,
        "net_margin": 0.18,
        "gross_margin": 0.32,
        "roe": 0.12,
    }
    risk_assessment = {
        "composite_score": 4.5,
        "risk_label": "中等風險",
        "risk_items": [],
    }
    agent_opinions = {
        "bull_score": 65,
        "bear_score": 35,
        "committee_summary": "電訊行業穩定，股息吸引",
    }
    competitive_landscape = []
    source_registry = {}
    return (
        market_snapshot, financial_data, risk_assessment,
        agent_opinions, competitive_landscape, source_registry,
    )


def test_rc2_investment_committee_20():
    print("\n[RC-2] Investment Committee 2.0")
    try:
        from core.investment_conclusion_engine import build_investment_conclusion

        args = _make_ic_inputs()
        ic = build_investment_conclusion(*args)

        # Must have valid rating
        valid_ratings = [
            "買入", "觀察", "中性", "減持", "避免",
            "Buy", "Watch", "Neutral", "Reduce", "Avoid",
            "OVERWEIGHT", "NEUTRAL", "UNDERWEIGHT",
        ]
        rating = ic.get("rating", "")
        assert rating, "No rating returned"
        assert any(r.lower() in rating.lower() for r in valid_ratings), \
            f"Invalid rating: '{rating}'"
        ok("RC-2-valid-rating", rating)

        # Must have non-empty final_summary or conclusion
        summary = ic.get("final_summary", ic.get("conclusion", ic.get("summary", "")))
        assert summary and len(summary.strip()) > 10, "Summary too short or missing"
        ok("RC-2-has-summary", summary[:60])

        # Must NOT use banned placeholder phrases
        banned_phrases = ["數據不足採用中性評分", "目標價未能可靠估算", "升幅未能可靠估算"]
        for phrase in banned_phrases:
            assert phrase not in summary, \
                f"Banned placeholder phrase detected: '{phrase}'"
        ok("RC-2-no-banned-phrases")

        # Must have at least 3 IC 2.0 decision basis fields
        basis = ic.get("decision_basis", [])
        if not basis:
            basis = [
                ic.get("investment_view", ""),
                ic.get("core_thesis", ""),
                ic.get("key_catalysts", ""),
                ic.get("key_risks", ""),
                ic.get("suitable_investor", ""),
                ic.get("allocation_suggestion", ""),
            ]
            basis = [b for b in basis if b]
        assert len(basis) >= 3, f"Decision basis incomplete: {len(basis)} fields"
        ok("RC-2-decision-basis", f"{len(basis)} fields")

    except Exception as e:
        fail("RC-2", str(e))


# ─────────────────────────────────────────────
# RC-3: Institutional Source Registry
# ─────────────────────────────────────────────
def test_rc3_institutional_source_registry():
    print("\n[RC-3] Institutional Source Registry")
    try:
        from core.report_builder import build_source_registry
        from core.source_registry import get_verified_sources

        sample_data = {"ticker": "0700", "name": "騰訊控股"}
        registry = build_source_registry(sample_data)

        # Must be a dict or list
        assert registry is not None, "Source registry returned None"
        ok("RC-3-registry-exists")

        # get_verified_sources must return list
        verified = get_verified_sources(registry)
        assert isinstance(verified, list), f"Expected list, got {type(verified)}"
        ok("RC-3-verified-is-list", f"{len(verified)} sources")

        # Banned strings must NOT appear
        banned = ["來源不明", "未已驗證來源", "資料待補充", "unknown source", "unverified"]
        for src in verified:
            src_str = str(src).lower()
            for ban in banned:
                assert ban.lower() not in src_str, \
                    f"Banned string '{ban}' found in source: '{src}'"
        ok("RC-3-no-banned-strings")

        # If sources exist, they must match institutional labels
        approved = ["Yahoo Finance", "HKEX", "Company Master Data",
                    "Risk Engine", "Competitive Database", "無額外驗證來源"]
        if len(verified) > 0:
            for src in verified:
                assert any(appr.lower() in str(src).lower() for appr in approved), \
                    f"Non-institutional source label: '{src}'"
            ok("RC-3-institutional-labels", str(verified[:3]))
        else:
            ok("RC-3-empty-registry-allowed", "0 sources (acceptable)")

    except Exception as e:
        fail("RC-3", str(e))


# ─────────────────────────────────────────────
# RC-3b: Source registry fallback text check
# ─────────────────────────────────────────────
def test_rc3b_empty_registry_fallback():
    print("\n[RC-3b] Empty registry fallback text")
    try:
        from core.source_registry import get_verified_sources

        # When empty dict / None passed, must return list (not crash)
        result = get_verified_sources({})
        assert isinstance(result, list), "Must return list even for empty input"
        ok("RC-3b-empty-dict")

        result2 = get_verified_sources(None)
        assert isinstance(result2, list), "Must return list even for None input"
        ok("RC-3b-none-input")

    except Exception as e:
        fail("RC-3b", str(e))


# ─────────────────────────────────────────────
# RC-4 (static): PDF / Mobile QA flags
# ─────────────────────────────────────────────
def test_rc4_static_qa_flags():
    """Static code scan: ensure banned UI strings not present in fos_components."""
    print("\n[RC-4] Static PDF/Mobile QA scan")
    try:
        import pathlib, re
        fos_path = pathlib.Path(__file__).parent / "core" / "fos_components.py"
        if not fos_path.exists():
            ok("RC-4-skipped", "fos_components.py not found, skip")
            return

        text = fos_path.read_text(encoding="utf-8")

        banned_ui = [
            "來源不明",
            "未已驗證來源",
            "資料待補充",
            "數據不足採用中性評分",
        ]
        found = [b for b in banned_ui if b in text]
        assert len(found) == 0, f"Banned UI strings in fos_components: {found}"
        ok("RC-4-no-banned-ui-strings")

        # Check no duplicate section markers
        for marker in ["## Market Snapshot", "## Risk"]:
            count = text.count(marker)
            assert count <= 1, f"Duplicate section '{marker}' found ({count}x)"
        ok("RC-4-no-duplicate-sections")

    except AssertionError:
        raise
    except Exception as e:
        fail("RC-4", str(e))


# ─────────────────────────────────────────────
# Main runner
# ─────────────────────────────────────────────
def run_all():
    print("=" * 60)
    print("FOS v4.2.1 Release Candidate — QA Suite")
    print("=" * 60)

    test_config_version()
    test_rc1_competitive_summary()
    test_rc2_investment_committee_20()
    test_rc3_institutional_source_registry()
    test_rc3b_empty_registry_fallback()
    test_rc4_static_qa_flags()

    total = len(PASSED) + len(FAILED)
    print("\n" + "=" * 60)
    print(f"RESULT: {len(PASSED)}/{total} PASS")
    if FAILED:
        print(f"FAILED: {FAILED}")
        print("✗ v4.2.1 RC QA: NOT READY")
    else:
        print("✓ v4.2.1 RC QA: ALL PASS")
    print("=" * 60)
    return len(FAILED) == 0


if __name__ == "__main__":
    success = run_all()
    sys.exit(0 if success else 1)
