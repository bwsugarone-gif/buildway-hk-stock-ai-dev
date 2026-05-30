"""
test_source_transparency.py — QA for core/source_transparency.py
API: build_source_transparency(report_data) ->
     {sources_present, sources_missing, field_coverage, coverage_pct,
      confidence_level, confidence_reason, data_gaps, present_count, total_fields}
"""
import os, sys
os.chdir(os.path.dirname(os.path.abspath(__file__)))
from core.source_transparency import build_source_transparency

def ok(label, cond):
    if not cond: raise AssertionError(f"FAIL: {label}")
    print(f"[OK] {label}")

def main():
    # ── full data package ─────────────────────────────────────────────────────
    pkg_full = {
        "report_metadata": {"data_confidence": "HIGH"},
        "company_metadata": {"name": "騰訊控股", "sector": "科技", "business": "互聯網"},
        "market_data": {"current_price": 385.4, "market_cap": 3710000000000,
                        "pe_ratio": 18.5, "pb_ratio": 3.2, "dividend_yield": 0.8},
        "financial_data": {"revenue": 600000000000, "net_profit": 120000000000,
                           "roe": 18.5, "debt_to_equity": 0.4},
        "news_data": {"articles": [{"title": "騰訊業績超預期"}]},
    }
    r = build_source_transparency(pkg_full)
    ok("result is dict", isinstance(r, dict))
    ok("coverage_pct present", "coverage_pct" in r)
    ok("confidence_level present", "confidence_level" in r)
    ok("confidence_reason present", "confidence_reason" in r)
    ok("sources_present is list", isinstance(r.get("sources_present", []), list))
    ok("coverage_pct > 0", float(r.get("coverage_pct", 0)) > 0)
    ok("confidence_level is valid", r["confidence_level"] in {"HIGH", "MEDIUM", "LOW", "INVALID"})
    ok("confidence_reason not empty", bool(str(r.get("confidence_reason", "")).strip()))
    ok("present_count >= 0", int(r.get("present_count", 0)) >= 0)
    ok("total_fields > 0", int(r.get("total_fields", 0)) > 0)

    # ── minimal data → lower coverage ─────────────────────────────────────────
    pkg_min = {"report_metadata": {"data_confidence": "LOW"}}
    r2 = build_source_transparency(pkg_min)
    ok("minimal: result is dict", isinstance(r2, dict))
    ok("minimal: confidence_level valid", r2.get("confidence_level") in {"HIGH","MEDIUM","LOW","INVALID"})
    ok("minimal: coverage_pct <= full coverage",
       float(r2.get("coverage_pct", 0)) <= float(r.get("coverage_pct", 100)))

    # ── empty input ───────────────────────────────────────────────────────────
    r3 = build_source_transparency({})
    ok("empty: no crash", isinstance(r3, dict))
    ok("empty: confidence_level valid", r3.get("confidence_level") in {"HIGH","MEDIUM","LOW","INVALID",None})

    print("\nAll source_transparency tests passed.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
