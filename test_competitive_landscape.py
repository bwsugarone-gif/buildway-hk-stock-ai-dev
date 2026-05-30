"""
test_competitive_landscape.py — QA for core/competitive_landscape_engine.py
API: build_competitive_landscape(ticker, report_data) -> dict
"""
import os, sys
os.chdir(os.path.dirname(os.path.abspath(__file__)))
from core.competitive_landscape_engine import build_competitive_landscape

def ok(label, cond):
    if not cond: raise AssertionError(f"FAIL: {label}")
    print(f"[OK] {label}")

def main():
    # ── realistic package ─────────────────────────────────────────────────────
    pkg = {
        "report_metadata": {"data_confidence": "HIGH"},
        "cover": {
            "ticker": "0941.HK",
            "company_name": "中國移動",
            "market_cap": 1620000000000,
            "risk_score": 4.5,
        },
        "market_data": {
            "pe_ratio": 12.5,
            "pb_ratio": 1.08,
            "dividend_yield": 6.2,
        },
        "peer_comparison": {
            "peers": [
                {"ticker": "0728.HK", "name": "中國電信", "pe_ratio": 10.2, "pb_ratio": 0.9,
                 "dividend_yield": 5.8, "market_cap": 380000000000, "risk_score": 4.8},
                {"ticker": "0762.HK", "name": "中國聯通", "pe_ratio": 14.1, "pb_ratio": 0.7,
                 "dividend_yield": 3.5, "market_cap": 220000000000, "risk_score": 5.2},
            ],
            "strengths": ["市佔率最高", "5G覆蓋最廣"],
            "weaknesses": ["估值溢價", "增長放緩"],
        },
    }
    r = build_competitive_landscape("0941", pkg)
    ok("result is dict", isinstance(r, dict))
    ok("result not empty", len(r) > 0)

    # ── empty input fallback ──────────────────────────────────────────────────
    r2 = build_competitive_landscape("0941", {})
    ok("empty input no crash", isinstance(r2, dict))

    # ── LOW confidence ────────────────────────────────────────────────────────
    pkg_low = {"report_metadata": {"data_confidence": "LOW"}, "cover": {"ticker": "3416.HK"}}
    r3 = build_competitive_landscape("3416", pkg_low)
    ok("LOW confidence no crash", isinstance(r3, dict))

    # ── INVALID ticker ────────────────────────────────────────────────────────
    r4 = build_competitive_landscape("99999", {"report_metadata": {"data_confidence": "INVALID"}})
    ok("INVALID ticker no crash", isinstance(r4, dict))

    print("\nAll competitive_landscape tests passed.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
