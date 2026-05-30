"""
test_v40_regression.py
V4.0 Hardening Layer — Regression Test Suite

Tests all new v4.0 modules:
  - hkex_engine
  - source_registry
  - market_snapshot_engine
  - competitive_landscape_engine (v4.0 enhancements)
  - news_localizer
  - investment_conclusion_engine

Run: python -m pytest buildway-hk-stock-ai/test_v40_regression.py -v
  or: python buildway-hk-stock-ai/test_v40_regression.py
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

PASS = "✅ PASS"
FAIL = "❌ FAIL"
results = []


def check(name: str, condition: bool, detail: str = ""):
    status = PASS if condition else FAIL
    msg = f"{status} {name}"
    if detail and not condition:
        msg += f"\n       → {detail}"
    results.append((name, condition))
    print(msg)
    return condition


# ─────────────────────────────────────────────────────────────────────────────
# Phase B: hkex_engine
# ─────────────────────────────────────────────────────────────────────────────
print("\n── Phase B: hkex_engine ──────────────────────────────────────────────")
try:
    from core.hkex_engine import (
        get_hkex_status, build_hkex_module, get_hkex_source_registry_entry,
        HKEX_STATUS_DISABLED, HKEX_STATUS_ENABLED_EMPTY, HKEX_STATUS_ENABLED_WITH_DATA
    )

    status = get_hkex_status()
    check("hkex_engine: default status is DISABLED", status == HKEX_STATUS_DISABLED)

    module = build_hkex_module("0700")
    check("hkex_engine: DISABLED module has source_verified=False",
          module["source_verified"] == False,
          f"got source_verified={module.get('source_verified')}")
    check("hkex_engine: DISABLED module has empty announcements",
          module["announcements"] == [],
          f"got {module.get('announcements')}")
    check("hkex_engine: DISABLED module has message",
          bool(module.get("message")),
          "message is empty")

    entry = get_hkex_source_registry_entry()
    check("hkex_engine: registry entry verified=False when DISABLED",
          entry["verified"] == False,
          f"got verified={entry.get('verified')}")
    check("hkex_engine: registry entry has note when DISABLED",
          bool(entry.get("note")),
          "note is empty")

except Exception as e:
    check("hkex_engine: import/run", False, str(e))


# ─────────────────────────────────────────────────────────────────────────────
# Phase C: source_registry
# ─────────────────────────────────────────────────────────────────────────────
print("\n── Phase C: source_registry ──────────────────────────────────────────")
try:
    from core.source_registry import (
        build_source_registry, get_verified_sources, get_unverified_sources,
        compute_coverage_pct, compute_confidence_level
    )

    # Minimal report_package
    rp_empty = {
        "report_metadata": {"stock_code": "0700", "data_confidence": "LOW"},
        "market_data": {},
        "company_metadata": {},
        "financial_data": {},
        "news_data": {},
    }
    reg_empty = build_source_registry(rp_empty)
    check("source_registry: builds with empty data", isinstance(reg_empty, dict))
    check("source_registry: has all 5 keys",
          all(k in reg_empty for k in ["market_data", "company_metadata", "financial_statement", "news", "hkex"]))
    check("source_registry: hkex not verified when DISABLED",
          reg_empty["hkex"]["verified"] == False)

    # With some data
    rp_partial = {
        "report_metadata": {"stock_code": "0700"},
        "market_data": {"current_price": 380.0, "pe_ratio": 15.0},
        "company_metadata": {"name_zh": "騰訊控股", "sector": "科技"},
        "financial_data": {"revenue": 600e9},
        "news_data": {"items": [{"title": "Tencent reports earnings"}]},
    }
    reg_partial = build_source_registry(rp_partial)
    check("source_registry: market_data verified with price",
          reg_partial["market_data"]["verified"] == True)
    check("source_registry: company_metadata verified with name",
          reg_partial["company_metadata"]["verified"] == True)
    check("source_registry: news verified with items",
          reg_partial["news"]["verified"] == True)

    verified = get_verified_sources(reg_partial)
    check("source_registry: get_verified_sources returns list",
          isinstance(verified, list) and len(verified) > 0,
          f"got {verified}")

    cov = compute_coverage_pct(reg_partial)
    check("source_registry: coverage_pct is 0-100",
          0 <= cov <= 100,
          f"got {cov}")

    conf = compute_confidence_level(reg_partial)
    check("source_registry: confidence_level is valid string",
          conf in ("HIGH", "MEDIUM", "LOW"),
          f"got {conf}")

except Exception as e:
    check("source_registry: import/run", False, str(e))


# ─────────────────────────────────────────────────────────────────────────────
# Phase F: market_snapshot_engine
# ─────────────────────────────────────────────────────────────────────────────
print("\n── Phase F: market_snapshot_engine ──────────────────────────────────")
try:
    from core.market_snapshot_engine import build_market_snapshot, get_snapshot_field

    rp_market = {
        "report_metadata": {"stock_code": "0700", "data_confidence": "MEDIUM"},
        "market_data": {
            "current_price": 380.0,
            "pe_ratio": 15.0,
            "pb_ratio": 2.5,
            "dividend_yield": 0.8,
            "market_cap": 3.6e12,
            "fifty_two_week_high": 420.0,
            "fifty_two_week_low": 280.0,
            "volume": 15000000,
            "beta": 0.95,
        },
        "company_metadata": {"name_zh": "騰訊控股"},
    }
    snap = build_market_snapshot(rp_market)
    check("market_snapshot: builds successfully", isinstance(snap, dict))
    check("market_snapshot: current_price formatted",
          snap["current_price"].startswith("HK$"),
          f"got {snap.get('current_price')}")
    check("market_snapshot: 52-week position computed",
          snap["fifty_two_week_position"] != "未取得",
          f"got {snap.get('fifty_two_week_position')}")
    check("market_snapshot: market_cap formatted with 億/萬億",
          "億" in snap["market_cap"] or "萬億" in snap["market_cap"],
          f"got {snap.get('market_cap')}")
    check("market_snapshot: cached in report_package",
          rp_market.get("market_snapshot") is snap)

    # Missing 52-week data
    rp_no52 = {
        "report_metadata": {},
        "market_data": {"current_price": 100.0},
        "company_metadata": {},
    }
    snap2 = build_market_snapshot(rp_no52)
    check("market_snapshot: missing 52wk shows 未取得",
          snap2["fifty_two_week_high"] == "未取得" and snap2["fifty_two_week_low"] == "未取得",
          f"got high={snap2.get('fifty_two_week_high')}, low={snap2.get('fifty_two_week_low')}")

    # get_snapshot_field never returns None
    val = get_snapshot_field(rp_market, "pe")
    check("market_snapshot: get_snapshot_field returns string",
          isinstance(val, str) and val != "",
          f"got {val!r}")

except Exception as e:
    check("market_snapshot_engine: import/run", False, str(e))


# ─────────────────────────────────────────────────────────────────────────────
# Phase E: competitive_landscape_engine (v4.0)
# ─────────────────────────────────────────────────────────────────────────────
print("\n── Phase E: competitive_landscape_engine v4.0 ────────────────────────")
try:
    from core.competitive_landscape_engine import (
        _get_peer_tickers, get_competitive_profile, build_competitive_landscape,
        _normalize_ticker
    )

    # Normalize ticker
    check("competitive: normalize 700 → 0700", _normalize_ticker("700") == "0700")
    check("competitive: normalize 0700.HK → 0700", _normalize_ticker("0700.HK") == "0700")
    check("competitive: normalize 9988 → 9988", _normalize_ticker("9988") == "9988")

    # Peer tickers from competitive_profile.json
    peers_0700 = _get_peer_tickers("0700")
    check("competitive: 0700 has 3 peers", len(peers_0700) == 3,
          f"got {peers_0700}")
    check("competitive: 0700 peers are tech stocks",
          any(p in peers_0700 for p in ["9988", "9618", "3690"]),
          f"got {peers_0700}")

    # get_competitive_profile
    cp = get_competitive_profile("0700")
    check("competitive: profile has sector", cp["sector"] != "資料未收錄",
          f"got sector={cp.get('sector')}")
    check("competitive: profile has strengths list",
          isinstance(cp["strengths"], list) and len(cp["strengths"]) > 0)
    check("competitive: profile has weaknesses list",
          isinstance(cp["weaknesses"], list) and len(cp["weaknesses"]) > 0)
    check("competitive: profile has product_lines",
          isinstance(cp["product_lines"], list) and len(cp["product_lines"]) > 0)

    # Unknown ticker fallback
    cp_unknown = get_competitive_profile("9999")
    check("competitive: unknown ticker returns fallback (not crash)",
          isinstance(cp_unknown, dict) and "sector" in cp_unknown)

    # build_competitive_landscape
    rp_cl = {
        "report_metadata": {"stock_code": "0700"},
        "market_data": {"pe_ratio": 15.0, "pb_ratio": 2.5, "dividend_yield": 0.8},
        "financial_analysis": {"roe": 20.0, "net_margin": 25.0},
        "risk_analysis": {"composite_score_raw": 5.5},
    }
    landscape = build_competitive_landscape("0700", rp_cl)
    check("competitive: landscape has subject", "subject" in landscape)
    check("competitive: landscape has peers list",
          isinstance(landscape.get("peers"), list))
    check("competitive: landscape has advantages",
          isinstance(landscape.get("advantages"), list) and len(landscape["advantages"]) > 0)
    check("competitive: landscape has disadvantages",
          isinstance(landscape.get("disadvantages"), list) and len(landscape["disadvantages"]) > 0)
    check("competitive: comparison_table has rows",
          isinstance(landscape.get("comparison_table"), list) and len(landscape["comparison_table"]) > 0)

except Exception as e:
    check("competitive_landscape_engine: import/run", False, str(e))


# ─────────────────────────────────────────────────────────────────────────────
# Phase H: news_localizer
# ─────────────────────────────────────────────────────────────────────────────
print("\n── Phase H: news_localizer ───────────────────────────────────────────")
try:
    from core.news_localizer import localize_news_item, localize_news_list, replace_labels

    # Earnings pattern
    item1 = {"title": "Tencent reports record quarterly earnings"}
    loc1 = localize_news_item(item1)
    check("news_localizer: earnings title localized",
          bool(loc1.get("title_zh")) and loc1["title_zh"] != "",
          f"got title_zh={loc1.get('title_zh')!r}")
    check("news_localizer: original title preserved",
          loc1["title_original"] == item1["title"])
    check("news_localizer: display_title set",
          bool(loc1.get("display_title")))

    # Already has Chinese title
    item2 = {"title": "Some English title", "title_zh": "已有中文標題"}
    loc2 = localize_news_item(item2)
    check("news_localizer: existing title_zh preserved",
          loc2["title_zh"] == "已有中文標題")

    # Empty title
    item3 = {"title": ""}
    loc3 = localize_news_item(item3)
    check("news_localizer: empty title handled (no crash)",
          isinstance(loc3, dict))

    # List localization
    items = [{"title": "Alibaba beats earnings estimates"}, {"title": "HSBC raises dividend"}]
    locs = localize_news_list(items)
    check("news_localizer: list localization returns same count",
          len(locs) == len(items))

    # Label replacement
    replaced = replace_labels("Bull Case analysis shows HIGH confidence")
    check("news_localizer: replace_labels works",
          "樂觀情景" in replaced or "高" in replaced,
          f"got {replaced!r}")

    # Empty list
    check("news_localizer: empty list returns []", localize_news_list([]) == [])

except Exception as e:
    check("news_localizer: import/run", False, str(e))


# ─────────────────────────────────────────────────────────────────────────────
# Phase K: investment_conclusion_engine
# ─────────────────────────────────────────────────────────────────────────────
print("\n── Phase K: investment_conclusion_engine ─────────────────────────────")
try:
    from core.investment_conclusion_engine import build_investment_conclusion, RATINGS, HORIZONS

    market_snap = {
        "_raw": {
            "current_price": 380.0,
            "pe": 15.0,
            "pb": 2.5,
            "fifty_two_week_high": 420.0,
            "fifty_two_week_low": 280.0,
        }
    }
    financial = {"revenue": 600e9, "net_profit": 150e9, "roe": 20.0, "net_margin": 25.0}
    risk = {"composite_score": "5.5/10", "risk_level": "中等風險", "risk_items": []}
    opinions = {"agents": [{"agent_name": "新聞分析 Agent", "stance": "正面", "confidence": 65}]}
    landscape = []
    registry = {}

    conclusion = build_investment_conclusion(
        market_snap, financial, risk, opinions, landscape, registry
    )

    check("conclusion: has rating", conclusion.get("rating") in RATINGS,
          f"got {conclusion.get('rating')!r}")
    check("conclusion: has composite_score",
          bool(conclusion.get("composite_score")) and "/10" in conclusion["composite_score"],
          f"got {conclusion.get('composite_score')!r}")
    check("conclusion: has investment_horizon",
          conclusion.get("investment_horizon") in HORIZONS,
          f"got {conclusion.get('investment_horizon')!r}")
    check("conclusion: has suitable_investor",
          bool(conclusion.get("suitable_investor")),
          f"got {conclusion.get('suitable_investor')!r}")
    check("conclusion: target_price says cannot estimate",
          "未能可靠估算" in conclusion.get("target_price", ""),
          f"got {conclusion.get('target_price')!r}")
    check("conclusion: has decision_basis list",
          isinstance(conclusion.get("decision_basis"), list) and len(conclusion["decision_basis"]) == 5)
    check("conclusion: has final_summary",
          bool(conclusion.get("final_summary")),
          f"got {conclusion.get('final_summary')!r}")
    check("conclusion: confidence is 30-95",
          30 <= conclusion.get("confidence", 0) <= 95,
          f"got {conclusion.get('confidence')}")

    # No data fallback
    conclusion_empty = build_investment_conclusion({}, {}, {}, {}, [], {})
    check("conclusion: handles empty data (no crash)",
          conclusion_empty.get("rating") in RATINGS)

except Exception as e:
    check("investment_conclusion_engine: import/run", False, str(e))


# ─────────────────────────────────────────────────────────────────────────────
# Summary
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "═" * 60)
passed = sum(1 for _, ok in results if ok)
failed = sum(1 for _, ok in results if not ok)
total = len(results)
print(f"V4.0 Regression: {passed}/{total} passed, {failed} failed")

if failed > 0:
    print("\nFailed tests:")
    for name, ok in results:
        if not ok:
            print(f"  ❌ {name}")
    sys.exit(1)
else:
    print("All V4.0 regression tests passed ✅")
    sys.exit(0)
