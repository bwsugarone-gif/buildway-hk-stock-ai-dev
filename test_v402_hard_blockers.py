"""
test_v402_hard_blockers.py
v4.0.2 Hard Blocker Regression Tests

Verifies all fixes in v4.0.2:
1. config.py: version = v4.0.2
2. pdf_generator.py: no "Downside trigger points" English string
3. competitive_landscape_engine.py: peer company_name never "股票 {ticker}"
4. hk_stock_master_data.json: 3416.HK name_en is clean (no "Build King / Local...")
5. fos_components.py: no "分析中" fallback string
6. source_registry.py: INVALID returned when zero sources verified
"""

import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

PASS = 0
FAIL = 0


def check(label: str, condition: bool, detail: str = ""):
    global PASS, FAIL
    if condition:
        print(f"  ✅ PASS  {label}")
        PASS += 1
    else:
        print(f"  ❌ FAIL  {label}" + (f" — {detail}" if detail else ""))
        FAIL += 1


# ── 1. config.py version ──────────────────────────────────────────────────────
print("\n── 1. config.py version ──────────────────────────────────────────────")
try:
    from core.config import APP_VERSION, BUILD_STAGE
    check("APP_VERSION == v4.0.2", APP_VERSION == "v4.0.2", f"got {APP_VERSION}")
    check("BUILD_STAGE contains 'Hard Blocker'", "Hard Blocker" in BUILD_STAGE, BUILD_STAGE)
except Exception as e:
    check("config.py import", False, str(e))


# ── 2. pdf_generator.py: no English "Downside trigger points" ─────────────────
print("\n── 2. pdf_generator.py: no English 'Downside trigger points' ─────────")
try:
    pdf_path = os.path.join(os.path.dirname(__file__), "core", "pdf_generator.py")
    with open(pdf_path, "r", encoding="utf-8") as f:
        pdf_src = f.read()
    check(
        "No 'Downside trigger points' in pdf_generator.py",
        "Downside trigger points" not in pdf_src,
        "English string still present",
    )
    check(
        "'下行觸發因素' present in pdf_generator.py",
        "下行觸發因素" in pdf_src,
        "TC replacement missing",
    )
except Exception as e:
    check("pdf_generator.py read", False, str(e))


# ── 3. competitive_landscape_engine.py: peer fallback uses ticker.HK not 股票 ──
print("\n── 3. competitive_landscape_engine.py: peer fallback ─────────────────")
try:
    cl_path = os.path.join(os.path.dirname(__file__), "core", "competitive_landscape_engine.py")
    with open(cl_path, "r", encoding="utf-8") as f:
        cl_src = f.read()
    # The old bad pattern was: f"股票 {ticker}"
    # The new pattern should be: f"{ticker}.HK"
    check(
        "No 'f\"股票 {ticker}\"' in _build_peer_record",
        'f"股票 {ticker}"' not in cl_src,
        "Old fallback still present in _build_peer_record",
    )
    check(
        "'{ticker}.HK' fallback present",
        'f"{ticker}.HK"' in cl_src,
        "New fallback missing",
    )
except Exception as e:
    check("competitive_landscape_engine.py read", False, str(e))


# ── 4. hk_stock_master_data.json: 3416.HK name_en clean ──────────────────────
print("\n── 4. hk_stock_master_data.json: 3416.HK name_en ─────────────────────")
try:
    data_path = os.path.join(os.path.dirname(__file__), "data", "hk_stock_master_data.json")
    with open(data_path, "r", encoding="utf-8") as f:
        master = json.load(f)
    entry = master.get("3416.HK", {})
    name_en = entry.get("name_en", "")
    check(
        "3416.HK name_en does not contain 'Build King'",
        "Build King" not in name_en,
        f"got: {name_en}",
    )
    check(
        "3416.HK name_en does not contain 'Local financial'",
        "Local financial" not in name_en,
        f"got: {name_en}",
    )
    check(
        "3416.HK name_en is non-empty",
        bool(name_en.strip()),
        "name_en is empty",
    )
except Exception as e:
    check("hk_stock_master_data.json read", False, str(e))


# ── 5. fos_components.py: no "分析中" fallback ────────────────────────────────
print("\n── 5. fos_components.py: no '分析中' fallback ─────────────────────────")
try:
    fos_path = os.path.join(os.path.dirname(__file__), "core", "fos_components.py")
    with open(fos_path, "r", encoding="utf-8") as f:
        fos_src = f.read()
    # Count occurrences of "分析中" as a string value (not in comments)
    # We check for the pattern used as a default value
    bad_pattern = '"分析中"'
    count = fos_src.count(bad_pattern)
    check(
        f"No '\"分析中\"' default value in fos_components.py (found {count})",
        count == 0,
        f"Found {count} occurrence(s)",
    )
    check(
        "'觀點待整合' replacement present",
        "觀點待整合" in fos_src,
        "Replacement string missing",
    )
except Exception as e:
    check("fos_components.py read", False, str(e))


# ── 6. source_registry.py: INVALID when zero sources verified ─────────────────
print("\n── 6. source_registry.py: INVALID guard ──────────────────────────────")
try:
    from core.source_registry import compute_confidence_level

    # Empty registry → all False → INVALID
    empty_registry = {
        "market_data":        {"verified": False},
        "company_metadata":   {"verified": False},
        "financial_statement":{"verified": False},
        "news":               {"verified": False},
        "hkex":               {"verified": False},
    }
    level_empty = compute_confidence_level(empty_registry)
    check(
        "compute_confidence_level(all_false) == 'INVALID'",
        level_empty == "INVALID",
        f"got: {level_empty}",
    )

    # Only metadata verified → LOW
    meta_only = {
        "market_data":        {"verified": False},
        "company_metadata":   {"verified": True},
        "financial_statement":{"verified": False},
        "news":               {"verified": False},
        "hkex":               {"verified": False},
    }
    level_meta = compute_confidence_level(meta_only)
    check(
        "compute_confidence_level(meta_only) == 'LOW'",
        level_meta == "LOW",
        f"got: {level_meta}",
    )

    # Market + metadata + financials → HIGH
    high_registry = {
        "market_data":        {"verified": True},
        "company_metadata":   {"verified": True},
        "financial_statement":{"verified": True},
        "news":               {"verified": False},
        "hkex":               {"verified": False},
    }
    level_high = compute_confidence_level(high_registry)
    check(
        "compute_confidence_level(mkt+meta+fin) == 'HIGH'",
        level_high == "HIGH",
        f"got: {level_high}",
    )

    # Market + metadata only → MEDIUM
    medium_registry = {
        "market_data":        {"verified": True},
        "company_metadata":   {"verified": True},
        "financial_statement":{"verified": False},
        "news":               {"verified": False},
        "hkex":               {"verified": False},
    }
    level_med = compute_confidence_level(medium_registry)
    check(
        "compute_confidence_level(mkt+meta) == 'MEDIUM'",
        level_med == "MEDIUM",
        f"got: {level_med}",
    )

except Exception as e:
    check("source_registry import / test", False, str(e))


# ── Summary ───────────────────────────────────────────────────────────────────
print(f"\n{'='*60}")
print(f"v4.0.2 Hard Blocker Tests: {PASS} passed, {FAIL} failed")
if FAIL == 0:
    print("✅ ALL HARD BLOCKER TESTS PASSED — v4.0.2 ready")
else:
    print(f"❌ {FAIL} test(s) failed — review above")
print("=" * 60)

sys.exit(0 if FAIL == 0 else 1)
