"""
test_v41_sprint_verify.py
Quick verification of FOS v4.1 Data Foundation Sprint changes.
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))

PASS = 0
FAIL = 0

def check(label, condition, detail=""):
    global PASS, FAIL
    if condition:
        print(f"  PASS  {label}")
        PASS += 1
    else:
        print(f"  FAIL  {label}" + (f" — {detail}" if detail else ""))
        FAIL += 1

print("\n=== T1: Master Data Coverage ===")
data_path = os.path.join(os.path.dirname(__file__), "data", "hk_stock_master_data.json")
with open(data_path, encoding="utf-8") as f:
    master = json.load(f)

check("Total entries >= 80", len(master) >= 80, f"got {len(master)}")
for ticker, expected_name in [
    ("0066.HK", "港鐵公司"),
    ("0728.HK", "中國電訊"),
    ("0762.HK", "中國聯通"),
    ("0941.HK", "中國移動"),
    ("0388.HK", "香港交易所"),
]:
    entry = master.get(ticker, {})
    name = entry.get("name_zh", "")
    check(f"{ticker} = {expected_name}", name == expected_name, f"got '{name}'")

print("\n=== T2: SECTOR_PEERS Coverage ===")
from core.competitive_landscape_engine import SECTOR_PEERS, _normalize_ticker, _build_peer_record, _load_master_data

t66 = _normalize_ticker("0066.HK")
check("0066 in SECTOR_PEERS", t66 in SECTOR_PEERS, f"normalized={t66}")
check("0066 peers not empty", bool(SECTOR_PEERS.get(t66, [])))

print("\n=== T3: Peer Name Resolution ===")
m = _load_master_data()
for ticker, expected in [("0728", "中國電訊"), ("0762", "中國聯通"), ("0066", "港鐵公司")]:
    rec = _build_peer_record(ticker, m, {})
    name = rec.get("company_name", "")
    check(f"{ticker} company_name = {expected}", name == expected, f"got '{name}'")

print("\n=== T4: fos_components Peer Fallback ===")
fos_path = os.path.join(os.path.dirname(__file__), "core", "fos_components.py")
with open(fos_path, encoding="utf-8") as f:
    fos_content = f.read()
check("fallback label '公司名稱未收錄' in render_peer_comparison", "公司名稱未收錄" in fos_content)
check("ticker-as-name rejection logic present", "_ticker_clean" in fos_content)

print("\n=== T5: Investment Conclusion Wiring ===")
app_path = os.path.join(os.path.dirname(__file__), "app.py")
with open(app_path, encoding="utf-8") as f:
    app_content = f.read()
check("_ic_engine wiring present", '_ic_engine = report_package.get("investment_conclusion")' in app_content)
check("_ic_rating from engine", "_ic_rating = _ic_engine.get" in app_content)
check("_ic_decision_basis from engine", "_ic_decision_basis = _ic_engine.get" in app_content)
check("render_investment_conclusion uses engine output", '"decision_basis": _ic_decision_basis' in app_content)

print("\n=== T6: debug_audit Files ===")
audit_dir = os.path.join(os.path.dirname(__file__), "debug_audit")
for fname in [
    "master_data_expansion_report.md",
    "hkex_integration_audit.md",
    "FOS_V41_PRODUCT_COMPLETENESS_AUDIT.md",
    "FOS_V403_PAYLOAD_AUDIT_REPORT.md",
]:
    fpath = os.path.join(audit_dir, fname)
    check(f"{fname} exists", os.path.exists(fpath))

print(f"\n{'='*50}")
print(f"Results: {PASS} PASS, {FAIL} FAIL")
if FAIL == 0:
    print("ALL CHECKS PASSED")
else:
    print(f"{FAIL} CHECKS FAILED")
