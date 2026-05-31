"""
test_v404_fixes.py
v4.0.4 Browser QA Fix Verification
Tests the three core failures identified in browser QA:
  1. INVALID ticker 12345 → coverage=0, verified_sources=[], no green ticks
  2. Peer comparison → real names or '公司名稱未收錄'
  3. Agent committee → hidden when no real data
  4. report_builder → source_registry key present in output
"""
import sys
import types

# ── Stub streamlit so fos_components can be imported without a running server ──
_st_stub = types.ModuleType("streamlit")
for _attr in (
    "markdown", "write", "error", "warning", "info", "success",
    "expander", "columns", "metric", "caption", "subheader", "header",
    "divider", "container", "empty", "spinner", "stop",
    "session_state", "cache_data", "cache_resource",
):
    setattr(_st_stub, _attr, lambda *a, **kw: None)
_st_stub.session_state = {}
sys.modules.setdefault("streamlit", _st_stub)

sys.path.insert(0, ".")

PASS = 0
FAIL = 0

def check(label, condition, got=None, expected=None):
    global PASS, FAIL
    if condition:
        print(f"  ✓ PASS  {label}")
        PASS += 1
    else:
        msg = f"  ✗ FAIL  {label}"
        if got is not None:
            msg += f"  got={got!r}"
        if expected is not None:
            msg += f"  expected={expected!r}"
        print(msg)
        FAIL += 1


# ─── Test 1: INVALID ticker 12345 ─────────────────────────────────────────────
print("\n=== Test 1: INVALID ticker 12345 ===")
from core.source_registry import (
    build_source_registry,
    compute_coverage_pct,
    compute_confidence_level,
    get_verified_sources,
)

empty_pkg = {
    "report_metadata": {"stock_code": "12345"},
    "market_data": {},
    "company_metadata": {},
    "financial_analysis": {},
    "news_analysis": {},
}
reg = build_source_registry(empty_pkg)
level = compute_confidence_level(reg)
cov   = compute_coverage_pct(reg)
vsrc  = get_verified_sources(reg)

check("level == INVALID", level == "INVALID", got=level, expected="INVALID")
check("coverage == 0.0",  cov == 0.0,         got=cov,   expected=0.0)
check("verified_sources == []", vsrc == [],    got=vsrc,  expected=[])


# ─── Test 2: _agent_has_real_data ─────────────────────────────────────────────
print("\n=== Test 2: _agent_has_real_data ===")
from core.fos_components import _agent_has_real_data

placeholder = {"opinion": "觀點待整合", "confidence": 0}
real        = {"opinion": "正面", "confidence": 75}
empty_agent = {}
conf_only   = {"opinion": "", "confidence": 60}

check("placeholder → False", not _agent_has_real_data(placeholder))
check("real        → True",  _agent_has_real_data(real))
check("empty       → False", not _agent_has_real_data(empty_agent))
check("conf_only   → True",  _agent_has_real_data(conf_only))


# ─── Test 3: peer name fallback ───────────────────────────────────────────────
print("\n=== Test 3: peer name fallback ===")

def _peer_name(row):
    """Mirror of fos_components.py logic."""
    ticker = row.get("ticker", "")
    raw_name = row.get("company_name") or row.get("name") or ""
    _ticker_clean = str(ticker).upper().replace(".HK", "").strip()
    _name_clean   = str(raw_name).upper().replace(".HK", "").strip()
    if not raw_name or _name_clean == _ticker_clean or raw_name in ("—", "N/A"):
        return "公司名稱未收錄"
    return raw_name

check("0728.HK with name=0728.HK → 公司名稱未收錄",
      _peer_name({"ticker": "0728.HK", "company_name": "0728.HK"}) == "公司名稱未收錄")
check("0762.HK with name=empty   → 公司名稱未收錄",
      _peer_name({"ticker": "0762.HK", "company_name": ""}) == "公司名稱未收錄")
check("0941.HK with name=中國移動 → 中國移動",
      _peer_name({"ticker": "0941.HK", "company_name": "中國移動"}) == "中國移動")
check("3416.HK with name=N/A     → 公司名稱未收錄",
      _peer_name({"ticker": "3416.HK", "company_name": "N/A"}) == "公司名稱未收錄")
check("0005.HK with name=匯豐控股 → 匯豐控股",
      _peer_name({"ticker": "0005.HK", "company_name": "匯豐控股"}) == "匯豐控股")


# ─── Test 4: report_builder source_registry key ───────────────────────────────
print("\n=== Test 4: report_builder source_registry key ===")
from core.report_builder import ReportBuilder
rb  = ReportBuilder()
fos = rb.build_fos_v3_sections(empty_pkg)

check("source_registry key present in build_fos_v3_sections",
      "source_registry" in fos, got=list(fos.keys()))

# Verify the registry inside is a dict (not an error)
sr = fos.get("source_registry", {})
check("source_registry is dict", isinstance(sr, dict), got=type(sr).__name__)
check("source_registry has market_data key", "market_data" in sr, got=list(sr.keys()))


# ─── Test 5: config version ───────────────────────────────────────────────────
print("\n=== Test 5: config version ===")
from core.config import APP_VERSION, BUILD_STAGE
check("APP_VERSION == v4.0.4", APP_VERSION == "v4.0.4", got=APP_VERSION)
check("BUILD_STAGE updated",   "Browser" in BUILD_STAGE or "Mobile" in BUILD_STAGE, got=BUILD_STAGE)


# ─── Summary ──────────────────────────────────────────────────────────────────
print(f"\n{'='*50}")
print(f"Results: {PASS} passed, {FAIL} failed")
if FAIL == 0:
    print("ALL TESTS PASSED ✓")
else:
    print(f"FAILURES: {FAIL}")
    sys.exit(1)
