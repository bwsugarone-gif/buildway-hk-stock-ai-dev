"""
test_v030.py — v0.3.0 Production Stability Layer validation tests
Run from buildway-hk-stock-ai/ directory:
    python test_v030.py
"""
import sys
import os

# Ensure we run from the project root
os.chdir(os.path.dirname(os.path.abspath(__file__)))

print(f"Python: {sys.version}")
print(f"Working dir: {os.getcwd()}")
print()

errors = []

def check(label, condition, detail=""):
    if condition:
        print(f"  [OK] {label}" + (f" — {detail}" if detail else ""))
    else:
        print(f"  [FAIL] {label}" + (f" — {detail}" if detail else ""))
        errors.append(label)

# ── Test 1: config imports & version ─────────────────────────────────────────
print("=== Test 1: config.py ===")
try:
    from core.config import APP_VERSION, BUILD_STAGE, DEPLOY_ENV, BUILD_VERSION
    check("APP_VERSION == v0.3.0", APP_VERSION == "v0.3.0", APP_VERSION)
    check("BUILD_STAGE set", bool(BUILD_STAGE), BUILD_STAGE)
    check("DEPLOY_ENV set", DEPLOY_ENV in ("local", "streamlit-cloud"), DEPLOY_ENV)
    check("BUILD_VERSION contains v0.3.0", "v0.3.0" in BUILD_VERSION, BUILD_VERSION)
except Exception as e:
    print(f"  [FAIL] config import: {e}")
    errors.append("config import")

# ── Test 2: stock code normalization ─────────────────────────────────────────
print("\n=== Test 2: normalize_hk_ticker ===")
try:
    from core.utils import normalize_hk_ticker
    cases = [
        ("3416",    "3416.HK"),
        ("3416.HK", "3416.HK"),
        ("03416",   "3416.HK"),
        ("700",     "0700.HK"),
        ("0005",    "0005.HK"),
        ("9988",    "9988.HK"),
        ("12345",   "12345.HK"),
    ]
    for inp, expected in cases:
        result = normalize_hk_ticker(inp)
        check(f"normalize({inp!r})", result == expected, f"{result!r}")
except Exception as e:
    print(f"  [FAIL] normalize_hk_ticker: {e}")
    errors.append("normalize_hk_ticker")

# ── Test 3: safe_math guards ──────────────────────────────────────────────────
print("\n=== Test 3: safe_math ===")
try:
    from core.safe_math import safe_number, safe_divide, safe_multiply
    check("safe_number(None) == 0.0",      safe_number(None) == 0.0)
    check("safe_number('N/A') == 0.0",     safe_number("N/A") == 0.0)
    check("safe_number('') == 0.0",        safe_number("") == 0.0)
    check("safe_number('3.14') == 3.14",   safe_number("3.14") == 3.14)
    check("safe_divide(10, 0) == 0.0",     safe_divide(10, 0) == 0.0)
    check("safe_divide(None, 2) == 0.0",   safe_divide(None, 2) == 0.0)
    check("safe_multiply(None, 5) == 0.0", safe_multiply(None, 5) == 0.0)
    check("safe_multiply(2, 3) == 6.0",    safe_multiply(2, 3) == 6.0)
except Exception as e:
    print(f"  [FAIL] safe_math: {e}")
    errors.append("safe_math")

# ── Test 4: sample_data 3416.HK ───────────────────────────────────────────────
print("\n=== Test 4: sample_data 3416.HK ===")
try:
    from data.sample_data import get_sample_market_data, SAMPLE_HK_STOCKS
    check("3416.HK in SAMPLE_HK_STOCKS", "3416.HK" in SAMPLE_HK_STOCKS)
    data = get_sample_market_data("3416.HK")
    check("company_name correct", data.get("company_name") == "保興財務集團有限公司", data.get("company_name"))
    check("ticker = 3416.HK", data.get("ticker") == "3416.HK", data.get("ticker"))
    check("current_price > 0", data.get("current_price", 0) > 0, str(data.get("current_price")))
except Exception as e:
    print(f"  [FAIL] sample_data: {e}")
    errors.append("sample_data 3416.HK")

# ── Test 5: PDFGenerator import ───────────────────────────────────────────────
print("\n=== Test 5: PDFGenerator import ===")
try:
    from core.pdf_generator import PDFGenerator, FontManager
    check("PDFGenerator imported", True)
    check("FontManager has _try_download_noto", hasattr(FontManager, "_try_download_noto"))
    check("FontManager._FONTS_DIR set", bool(FontManager._FONTS_DIR))
except Exception as e:
    print(f"  [FAIL] PDFGenerator import: {e}")
    errors.append("PDFGenerator import")

# ── Test 6: CEOAgent ─────────────────────────────────────────────────────────
print("\n=== Test 6: CEOAgent ===")
try:
    from agents.ceo_agent import CEOAgent
    ceo = CEOAgent()
    check("CEOAgent instantiated", True)
    check("run_agent_safely exists", callable(getattr(ceo, "run_agent_safely", None)))
    # Test fallback status
    ceo.agent_status = {}
    ceo.agent_error_log = []
    result = ceo.run_agent_safely("TestAgent", lambda: 1/0, {"fallback": True})
    check("Failsafe returns fallback on error", isinstance(result, dict))
    check("Status set to 備援", ceo.agent_status.get("TestAgent") == "備援", ceo.agent_status.get("TestAgent"))
    check("Error log populated", len(ceo.agent_error_log) > 0)
except Exception as e:
    print(f"  [FAIL] CEOAgent: {e}")
    errors.append("CEOAgent")

# ── Summary ───────────────────────────────────────────────────────────────────
print()
if errors:
    print(f"FAILED: {len(errors)} test(s) failed: {errors}")
    sys.exit(1)
else:
    print("All tests passed. v0.3.0 validation complete.")
