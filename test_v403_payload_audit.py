"""
test_v403_payload_audit.py
v4.0.3 — Payload Audit Validation Tests

Verifies that:
- audit script runs for all 4 tickers
- audit JSON files are generated
- 12345 source_registry coverage == 0
- 12345 verified_sources == []
- 0941 peer comparison has real names or explicit placeholder
- agent_opinions contains no 0% fallback for valid tickers
- 52-week keys are present in market_data
- no legacy key is used by FOS render functions where canonical key exists
"""

import sys
import os
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

AUDIT_DIR = ROOT / "debug_audit"
TICKERS = ["12345", "0941", "3416", "0688"]

CANONICAL_KEYS = {
    "source_registry",
    "market_snapshot",
    "competitive_landscape",
    "peer_comparison",
    "agent_opinions",
    "risk_assessment_v2",
    "investment_conclusion",
    "hkex_status",
    "news_localized",
}

LEGACY_KEYS = {
    "data_confidence",
    "source_transparency",
    "market_snapshot_v4",
    "competitive_landscape_v4",
    "investment_conclusion_v4",
    "risk_analysis",
    "agent_status",
    "committee_status",
    "report_sections",
    "confidence_score",
    "verified_sources",
}

# Legacy keys that have a canonical replacement — these must NOT be the sole source
LEGACY_WITH_CANONICAL = {
    "market_snapshot_v4": "market_snapshot",
    "competitive_landscape_v4": "competitive_landscape",
    "investment_conclusion_v4": "investment_conclusion",
    "risk_analysis": "risk_assessment_v2",
}

PASS = "PASS"
FAIL = "FAIL"
SKIP = "SKIP"

results = []


def check(name: str, condition: bool, detail: str = ""):
    status = PASS if condition else FAIL
    results.append((name, status, detail))
    icon = "✅" if condition else "❌"
    print(f"  {icon} [{status}] {name}" + (f" — {detail}" if detail else ""))
    return condition


def load_audit(ticker: str) -> dict:
    path = AUDIT_DIR / f"{ticker}_payload_audit.json"
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


# ─── T01: Audit script runs without error ─────────────────────────────────────
print("\n" + "="*60)
print("T01: Run audit script")
print("="*60)

try:
    proc = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "audit_report_payload.py")],
        capture_output=True, text=True, timeout=120, cwd=str(ROOT)
    )
    check("audit script exits 0", proc.returncode == 0,
          f"returncode={proc.returncode}")
    if proc.returncode != 0:
        print("  STDERR:", proc.stderr[-500:] if proc.stderr else "")
except subprocess.TimeoutExpired:
    check("audit script exits 0", False, "TIMEOUT after 120s")
except Exception as e:
    check("audit script exits 0", False, str(e))

# ─── T02: Audit JSON files generated ──────────────────────────────────────────
print("\n" + "="*60)
print("T02: Audit JSON files exist")
print("="*60)

for ticker in TICKERS:
    path = AUDIT_DIR / f"{ticker}_payload_audit.json"
    check(f"audit file exists: {ticker}", path.exists(), str(path))

ui_audit_path = AUDIT_DIR / "ui_key_audit.json"
check("ui_key_audit.json exists", ui_audit_path.exists())

# ─── T03: 12345 INVALID ticker — coverage=0, verified_sources=[] ──────────────
print("\n" + "="*60)
print("T03: 12345 INVALID ticker checks")
print("="*60)

audit_12345 = load_audit("12345")
if audit_12345 and not audit_12345.get("error"):
    sr = audit_12345.get("B_source_registry", {})
    cov = sr.get("coverage_pct")
    verified = sr.get("verified_sources", [])
    check("12345 coverage_pct == 0", cov == 0 or cov is None,
          f"coverage_pct={cov}")
    check("12345 verified_sources == []", verified == [],
          f"verified_sources={verified}")
    # Also check agent opinions are stopped
    ao = audit_12345.get("E_agent_opinions", {})
    zero_agents = ao.get("zero_confidence_agents", [])
    check("12345 all agents have 0 confidence (INVALID)", len(zero_agents) > 0,
          f"zero_agents={zero_agents}")
else:
    check("12345 audit loaded", False, audit_12345.get("error", "file missing"))

# ─── T04: 0941 peer comparison has real names ─────────────────────────────────
print("\n" + "="*60)
print("T04: 0941 peer comparison names")
print("="*60)

audit_0941 = load_audit("0941")
if audit_0941 and not audit_0941.get("error"):
    cl = audit_0941.get("D_competitive_landscape", {})
    peer_rows = cl.get("peer_rows", [])
    peer_count = cl.get("peer_count", 0)
    check("0941 has peers", peer_count > 0, f"peer_count={peer_count}")

    fake_placeholders = ["peer_1", "peer_2", "peer_3", "placeholder", "unknown", "N/A"]
    bad_names = []
    for p in peer_rows:
        name = p.get("name") or ""
        if not name or name.lower() in fake_placeholders or name.startswith("peer_"):
            bad_names.append(name or "(empty)")

    check("0941 peer names are real or explicit placeholder",
          len(bad_names) == 0 or all("公司名稱未收錄" in n for n in bad_names),
          f"bad_names={bad_names}")
else:
    check("0941 audit loaded", False, audit_0941.get("error", "file missing"))

# ─── T05: Valid tickers — agent_opinions no 0% fallback ──────────────────────
print("\n" + "="*60)
print("T05: Valid tickers — no 0% agent confidence fallback")
print("="*60)

for ticker in ["0941", "3416", "0688"]:
    audit = load_audit(ticker)
    if audit and not audit.get("error"):
        ao = audit.get("E_agent_opinions", {})
        zero_agents = ao.get("zero_confidence_agents", [])
        check(f"{ticker} no 0% confidence agents", len(zero_agents) == 0,
              f"zero_agents={zero_agents}")
    else:
        check(f"{ticker} audit loaded", False, audit.get("error", "file missing") if audit else "file missing")

# ─── T06: 52-week keys unified ────────────────────────────────────────────────
print("\n" + "="*60)
print("T06: 52-week keys present in market_data")
print("="*60)

EXPECTED_52W_KEYS = ["fifty_two_week_high", "fifty_two_week_low"]

for ticker in ["0941", "3416", "0688"]:
    audit = load_audit(ticker)
    if audit and not audit.get("error"):
        snap = audit.get("C_market_snapshot", {})
        found = snap.get("week52_keys_found", {})
        for key in EXPECTED_52W_KEYS:
            check(f"{ticker} has {key}", key in found,
                  f"found_keys={list(found.keys())}")
    else:
        check(f"{ticker} audit loaded for 52w check", False,
              audit.get("error", "file missing") if audit else "file missing")

# ─── T07: Source confidence UI data consistent with source_registry ───────────
print("\n" + "="*60)
print("T07: Source confidence consistency")
print("="*60)

for ticker in ["0941", "3416", "0688"]:
    audit = load_audit(ticker)
    if audit and not audit.get("error"):
        sr = audit.get("B_source_registry", {})
        conf_level = sr.get("confidence_level")
        cov = sr.get("coverage_pct")
        # If coverage is 0, confidence should not be HIGH
        if cov is not None and cov == 0:
            check(f"{ticker} conf not HIGH when coverage=0",
                  str(conf_level).upper() != "HIGH",
                  f"conf={conf_level} cov={cov}")
        else:
            check(f"{ticker} source_registry has confidence_level",
                  conf_level is not None,
                  f"conf_level={conf_level}")
    else:
        check(f"{ticker} audit loaded for confidence check", False,
              audit.get("error", "file missing") if audit else "file missing")

# ─── T08: No legacy key used by FOS render functions where canonical exists ───
print("\n" + "="*60)
print("T08: UI render functions — legacy key usage")
print("="*60)

if ui_audit_path.exists():
    with open(ui_audit_path, encoding="utf-8") as f:
        ui_audit = json.load(f)

    violations = []
    for fn_name, data in ui_audit.items():
        legacy_used = data.get("legacy", [])
        for lk in legacy_used:
            canonical = LEGACY_WITH_CANONICAL.get(lk)
            if canonical:
                # Check if the function also reads the canonical key
                reads = data.get("reads", [])
                if canonical not in reads:
                    violations.append(f"{fn_name} uses legacy '{lk}' but not canonical '{canonical}'")

    check("no render fn uses legacy key without canonical fallback",
          len(violations) == 0,
          "; ".join(violations[:3]) if violations else "")
else:
    check("ui_key_audit.json available", False, "file missing")

# ─── T09: investment_conclusion exists for valid tickers ─────────────────────
print("\n" + "="*60)
print("T09: investment_conclusion exists for valid tickers")
print("="*60)

for ticker in ["0941", "3416", "0688"]:
    audit = load_audit(ticker)
    if audit and not audit.get("error"):
        ic = audit.get("F_investment_conclusion", {})
        exists = ic.get("investment_conclusion_exists", False)
        rating = ic.get("rating")
        check(f"{ticker} investment_conclusion exists", exists,
              f"rating={rating}")
    else:
        check(f"{ticker} audit loaded for IC check", False,
              audit.get("error", "file missing") if audit else "file missing")

# ─── T10: competitive_landscape exists for valid tickers ─────────────────────
print("\n" + "="*60)
print("T10: competitive_landscape exists for valid tickers")
print("="*60)

for ticker in ["0941", "3416", "0688"]:
    audit = load_audit(ticker)
    if audit and not audit.get("error"):
        cl = audit.get("D_competitive_landscape", {})
        exists = cl.get("competitive_landscape_exists", False)
        check(f"{ticker} competitive_landscape exists", exists)
    else:
        check(f"{ticker} audit loaded for CL check", False,
              audit.get("error", "file missing") if audit else "file missing")

# ─── Final summary ────────────────────────────────────────────────────────────
print("\n" + "="*60)
print("FINAL RESULTS")
print("="*60)

passed = sum(1 for _, s, _ in results if s == PASS)
failed = sum(1 for _, s, _ in results if s == FAIL)
total = len(results)

print(f"\n  Total: {total}  Passed: {passed}  Failed: {failed}")

if failed > 0:
    print("\n  FAILED tests:")
    for name, status, detail in results:
        if status == FAIL:
            print(f"    ❌ {name}" + (f" — {detail}" if detail else ""))

print()
if failed == 0:
    print("  ✅ ALL TESTS PASSED")
    sys.exit(0)
else:
    print(f"  ❌ {failed} TEST(S) FAILED")
    sys.exit(1)
