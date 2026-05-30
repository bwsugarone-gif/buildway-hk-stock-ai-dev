"""
test_agent_opinion_engine.py — QA for core/agent_opinion_engine.py
API: build_agent_opinions(report_data) ->
     {opinions, bull_opinions, bear_opinions, bull_score, bear_score,
      committee_verdict, verdict_reason, overall_confidence, agent_count}
"""
import os, sys
os.chdir(os.path.dirname(os.path.abspath(__file__)))
from core.agent_opinion_engine import build_agent_opinions

def ok(label, cond):
    if not cond: raise AssertionError(f"FAIL: {label}")
    print(f"[OK] {label}")

def main():
    # ── realistic package ─────────────────────────────────────────────────────
    pkg = {
        "report_metadata": {"data_confidence": "HIGH"},
        "cover": {"final_rating": "買入", "risk_score": 5.5},
        "investment_committee": {
            "bull_score": 65,
            "bear_score": 35,
            "confidence": 72,
            "bull_points": ["估值合理", "股息率具吸引力", "業務穩定"],
            "bear_points": ["市場競爭加劇", "監管風險", "增長放緩"],
        },
        "sections": {
            "multi_agent_discussion": {
                "table": [
                    {"Agent": "Market Data Agent", "核心觀點": "技術面偏強", "正面因素": "突破阻力位", "主要憂慮": ""},
                    {"Agent": "Financial Analyst Agent", "核心觀點": "盈利穩健", "正面因素": "ROE 15%", "主要憂慮": ""},
                    {"Agent": "Risk Management Agent", "核心觀點": "風險可控", "正面因素": "", "主要憂慮": "負債偏高"},
                ],
                "final_statement": "整體評估正面，建議買入。",
            }
        },
    }
    r = build_agent_opinions(pkg)
    ok("result is dict", isinstance(r, dict))
    ok("bull_opinions present", "bull_opinions" in r)
    ok("bear_opinions present", "bear_opinions" in r)
    ok("bull_score present", "bull_score" in r)
    ok("bear_score present", "bear_score" in r)
    ok("committee_verdict present", "committee_verdict" in r)
    ok("agent_count present", "agent_count" in r)

    ok("bull_opinions not empty", len(r.get("bull_opinions", [])) > 0)
    ok("bear_opinions not empty", len(r.get("bear_opinions", [])) > 0)

    for op in r["bull_opinions"]:
        ok(f"bull opinion has non-blank content", bool(str(op).strip()))

    for op in r["bear_opinions"]:
        ok(f"bear opinion has non-blank content", bool(str(op).strip()))

    ok("bull_score in 0-100", 0 <= float(r.get("bull_score", 0)) <= 100)
    ok("bear_score in 0-100", 0 <= float(r.get("bear_score", 0)) <= 100)
    ok("committee_verdict not empty", bool(str(r.get("committee_verdict", "")).strip()))

    # ── empty input fallback ──────────────────────────────────────────────────
    r2 = build_agent_opinions({})
    ok("empty input no crash", isinstance(r2, dict))
    ok("empty input bull_opinions present", "bull_opinions" in r2)
    ok("empty input bear_opinions present", "bear_opinions" in r2)

    print("\nAll agent_opinion_engine tests passed.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
