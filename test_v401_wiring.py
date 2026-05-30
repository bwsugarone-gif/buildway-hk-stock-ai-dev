"""
test_v401_wiring.py
v4.0.1 Wiring Fix — Regression Test Suite

Tests:
1. config.APP_VERSION == "v4.0.1"
2. source_registry key mapping (market_data / financial_analysis / news_analysis)
3. compute_coverage_pct returns > 0 for demo data
4. compute_confidence_level returns valid string
5. ceo_agent._inject_v4_engines injects expected keys
6. pdf_generator risk section uses Traditional Chinese headers
7. pdf_generator deduplicates risk_table rows
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

PASS = "✅ PASS"
FAIL = "❌ FAIL"
results = []


def check(name: str, condition: bool, detail: str = ""):
    status = PASS if condition else FAIL
    msg = f"{status} | {name}"
    if detail:
        msg += f" — {detail}"
    print(msg)
    results.append((name, condition))
    return condition


# ─── Test 1: version ──────────────────────────────────────────────────────────
try:
    from core.config import APP_VERSION, BUILD_STAGE
    check("T01 APP_VERSION == v4.0.1", APP_VERSION == "v4.0.1", APP_VERSION)
    check("T02 BUILD_STAGE updated", "Wiring Fix" in BUILD_STAGE or "v4" in BUILD_STAGE.lower(), BUILD_STAGE)
except Exception as e:
    check("T01 config import", False, str(e))
    check("T02 BUILD_STAGE", False, "skipped")


# ─── Test 2: source_registry key mapping ─────────────────────────────────────
try:
    from core.source_registry import build_source_registry, compute_coverage_pct, compute_confidence_level

    # Simulate a report_package as assembled by ceo_agent
    demo_package = {
        "report_metadata": {"ticker": "0941.HK"},
        "market_data": {
            "current_price": 68.5,
            "company_name": "中國移動",
            "sector": "電訊",
            "pe_ratio": 12.5,
            "pb_ratio": 1.2,
            "dividend_yield": 0.065,
            "market_cap": 1_500_000_000_000,
            "fifty_two_week_high": 80.0,
            "fifty_two_week_low": 55.0,
            "volume": 25_000_000,
            "beta": 0.7,
        },
        "financial_analysis": {
            "metrics": {
                "net_debt": -50_000_000_000,
                "ev_ebitda": 5.2,
                "gross_margin": 0.58,
                "net_margin": 0.22,
                "roe": 0.12,
            },
            "valuation_range": {"low": 60, "mid": 72, "high": 85},
        },
        "financial_history": {
            "revenue": [200_000_000_000, 190_000_000_000, 180_000_000_000],
        },
        "news_analysis": {
            "status": "未接入",
            "news_items": [],
        },
    }

    registry = build_source_registry(demo_package)
    check("T03 registry is dict", isinstance(registry, dict))
    check("T04 registry has market_data key", "market_data" in registry)
    check("T05 market_data verified=True", registry.get("market_data", {}).get("verified") is True,
          str(registry.get("market_data", {}).get("verified")))
    check("T06 company_metadata verified (fallback from market_data)",
          registry.get("company_metadata", {}).get("verified") is True,
          str(registry.get("company_metadata", {}).get("verified")))

    coverage = compute_coverage_pct(registry)
    check("T07 coverage_pct > 0", coverage > 0, f"{coverage}%")
    check("T08 coverage_pct <= 100", coverage <= 100, f"{coverage}%")

    conf = compute_confidence_level(registry)
    check("T09 confidence_level is valid string", conf in ("HIGH", "MEDIUM", "LOW"), conf)

except Exception as e:
    for i in range(3, 10):
        check(f"T0{i} source_registry", False, str(e))


# ─── Test 3: INVALID package → coverage=0 ────────────────────────────────────
try:
    from core.source_registry import build_source_registry, compute_coverage_pct

    invalid_package = {
        "report_metadata": {"ticker": "9999.HK"},
        "market_data": {
            "current_price": 0,
            "data_confidence": "INVALID",
        },
        "financial_analysis": {},
        "news_analysis": {},
    }
    reg_invalid = build_source_registry(invalid_package)
    cov_invalid = compute_coverage_pct(reg_invalid)
    check("T10 INVALID package market_data.verified=False",
          reg_invalid.get("market_data", {}).get("verified") is False,
          str(reg_invalid.get("market_data", {}).get("verified")))
    check("T11 INVALID package coverage < 50", cov_invalid < 50, f"{cov_invalid}%")

except Exception as e:
    check("T10 INVALID package test", False, str(e))
    check("T11 INVALID coverage", False, "skipped")


# ─── Test 4: ceo_agent._inject_v4_engines ────────────────────────────────────
try:
    from agents.ceo_agent import CEOAgent
    agent = CEOAgent()

    # Build a minimal report_package
    minimal_package = {
        "report_metadata": {"ticker": "0941.HK"},
        "market_data": {
            "current_price": 68.5,
            "company_name": "中國移動",
            "sector": "電訊",
        },
        "financial_analysis": {},
        "financial_history": {},
        "news_analysis": {},
        "risk_analysis": {"composite_risk_score": 4.5, "risk_label": "中等風險"},
        "ic_result": {"verdict": "中性"},
        "summary": {},
        "agent_opinions": [],
        "agent_status": {},
        "agent_error_log": [],
        "ipo_module": {},
    }

    injected = agent._inject_v4_engines(minimal_package)
    check("T12 _inject_v4_engines returns dict", isinstance(injected, dict))
    check("T13 source_registry injected", "source_registry" in injected,
          str(list(injected.keys())))
    check("T14 data_coverage_pct injected", "data_coverage_pct" in injected,
          str(injected.get("data_coverage_pct")))
    check("T15 confidence_level injected", "confidence_level" in injected,
          str(injected.get("confidence_level")))

except Exception as e:
    for i in range(12, 16):
        check(f"T{i} ceo_agent inject", False, str(e))


# ─── Test 5: pdf_generator risk deduplication ────────────────────────────────
try:
    from core.pdf_generator import PDFGenerator

    gen = PDFGenerator()
    risk_section = {
        "composite_score": 5.5,
        "risk_label": "中等風險",
        "risk_table": [
            {"dimension": "流動性風險", "score": 5, "level": "中等", "weight": "20%", "heat": "中"},
            {"dimension": "流動性風險", "score": 5, "level": "中等", "weight": "20%", "heat": "中"},  # duplicate
            {"dimension": "市場風險", "score": 6, "level": "中等", "weight": "20%", "heat": "中"},
        ],
        "top_risks": [
            {"dimension": "市場風險", "score": 6, "level": "中等"},
        ],
    }
    elements = gen._risk(risk_section)
    # Count how many Table elements are in the output
    from reportlab.platypus import Table
    tables = [e for e in elements if isinstance(e, Table)]
    check("T16 risk section renders without error", len(elements) > 0)
    # The risk table should have 3 rows (header + 2 unique dims), not 4
    if tables:
        tbl = tables[0]
        row_count = len(tbl._cellvalues)
        check("T17 risk_table deduplicates rows", row_count == 3, f"rows={row_count}")
    else:
        check("T17 risk_table deduplicates rows", False, "no Table found")

except Exception as e:
    check("T16 pdf risk section", False, str(e))
    check("T17 risk dedup", False, "skipped")


# ─── Test 6: pdf_generator risk title is Traditional Chinese ─────────────────
try:
    from core.pdf_generator import PDFGenerator
    from reportlab.platypus import Paragraph

    gen = PDFGenerator()
    risk_section = {
        "composite_score": 5.0,
        "risk_label": "中等風險",
        "risk_table": [],
        "top_risks": [],
    }
    elements = gen._risk(risk_section)
    # First element should be a Paragraph with "風險分析"
    first = elements[0] if elements else None
    if isinstance(first, Paragraph):
        text = first.text if hasattr(first, "text") else str(first)
        check("T18 risk title is Traditional Chinese", "風險分析" in text, text[:60])
    else:
        check("T18 risk title is Traditional Chinese", False, f"type={type(first)}")

except Exception as e:
    check("T18 pdf risk title", False, str(e))


# ─── Summary ──────────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
passed = sum(1 for _, ok in results if ok)
failed = sum(1 for _, ok in results if not ok)
total = len(results)
print(f"v4.0.1 Wiring Fix QA: {passed}/{total} passed, {failed} failed")
if failed == 0:
    print("🎉 ALL TESTS PASSED — ready to commit")
else:
    print("⚠️  Some tests failed — review above")
    sys.exit(1)
