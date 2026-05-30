"""
test_risk_engine_v2.py — QA for core/risk_engine_v2.py
API: build_risk_assessment(report_data) -> {risk_items, composite_score, composite_score_raw,
     risk_label, total_weight, category_count, top_risks}
Verifies: no duplicate categories, weights sum 100%, score x.x/10
"""
import os, sys
os.chdir(os.path.dirname(os.path.abspath(__file__)))
from core.risk_engine_v2 import build_risk_assessment, RISK_CATEGORIES

def ok(label, cond):
    if not cond: raise AssertionError(f"FAIL: {label}")
    print(f"[OK] {label}")

def main():
    # ── static: weights sum to 100 ────────────────────────────────────────────
    total_w = sum(c["weight"] for c in RISK_CATEGORIES)
    ok(f"RISK_CATEGORIES weights sum to 100 (got {total_w})", total_w == 100)

    # ── static: no duplicate category names ───────────────────────────────────
    names = [c["name"] for c in RISK_CATEGORIES]
    ok("no duplicate category names", len(names) == len(set(names)))

    # ── build with sample data ────────────────────────────────────────────────
    sample = {
        "overall_risk_score": 6.2,
        "roe": 12.5,
        "debt_to_equity": 0.8,
        "net_margin": 18.0,
        "current_ratio": 1.5,
        "pe_ratio": 22.0,
        "pb_ratio": 2.1,
        "beta": 1.1,
        "news_sentiment_score": -0.2,
        "risk_factors": ["監管風險", "市場競爭"],
    }
    result = build_risk_assessment(sample)
    ok("result is dict", isinstance(result, dict))
    ok("risk_items key present", "risk_items" in result)
    ok("composite_score key present", "composite_score" in result)
    ok("total_weight key present", "total_weight" in result)

    # ── no duplicate risk item names ──────────────────────────────────────────
    items = result.get("risk_items", [])
    item_names = [i.get("risk_name", "") for i in items]
    ok("no duplicate risk item names", len(item_names) == len(set(item_names)))

    # ── total_weight == 100 (stored as int or "100%") ─────────────────────────
    tw = result.get("total_weight", 0)
    tw_int = int(str(tw).replace("%", ""))
    ok(f"total_weight == 100 (got {tw})", tw_int == 100)

    # ── composite_score_raw in 0-10 range ────────────────────────────────────
    score_raw = result.get("composite_score_raw", result.get("composite_score", 0))
    ok("composite_score_raw is numeric", isinstance(score_raw, (int, float)))
    ok("composite_score_raw in 0-10 range", 0.0 <= float(score_raw) <= 10.0)

    # ── composite_score display format x.x/10 ────────────────────────────────
    score_disp = str(result.get("composite_score", ""))
    ok("composite_score display contains /10", "/10" in score_disp)

    # ── empty input graceful fallback ─────────────────────────────────────────
    r2 = build_risk_assessment({})
    ok("empty input no crash", isinstance(r2, dict))
    items2 = r2.get("risk_items", [])
    names2 = [i.get("risk_name", "") for i in items2]
    ok("empty input no duplicate items", len(names2) == len(set(names2)))
    tw2 = r2.get("total_weight", 0)
    tw2_int = int(str(tw2).replace("%", ""))
    ok("empty input total_weight == 100", tw2_int == 100)

    print("\nAll risk_engine_v2 tests passed.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
