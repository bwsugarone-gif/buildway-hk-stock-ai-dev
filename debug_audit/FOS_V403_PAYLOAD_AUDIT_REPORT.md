# FOS v4.0.3 Payload Audit Report
**Date:** 2026-05-31  
**Auditor:** Static Code Analysis — Engine Output vs UI Input  
**Status:** ❌ MERGE BLOCKED — 3 confirmed payload failures

---

## Executive Summary

Browser QA contradicts the v4.0.3 audit report because the audit tested engine output in isolation. The actual failures occur in **app.py's fallback injection layer** — between engine output and UI render. Three distinct bugs cause the UI to display fabricated data instead of real engine output or a hidden panel.

---

## Bug Index

| ID | Ticker | Component | Severity | Status |
|----|--------|-----------|----------|--------|
| BUG-1 | 12345 | source_transparency fallback | CRITICAL | ❌ FAIL |
| BUG-2 | 0941.HK | peer name resolution | HIGH | ❌ FAIL |
| BUG-3 | 3416.HK | investment_committee panel | HIGH | ❌ FAIL |

---

## BUG-1: INVALID Ticker Shows 65% Coverage + Green Ticks

**File:** `app.py` L1646–1667  
**Evidence:** `debug_audit/12345_payload_audit.json`

### Engine Output (correct)
```
data_confidence = "INVALID"
data_confidence_score = 0
source_transparency = null
verified_sources = []
```

### What app.py Does (wrong)
```python
# L1646
_st_data = report_package.get("source_transparency", {}) or {}
# → {} for invalid ticker, triggers fallback

# L1649  ← ROOT CAUSE
_cov = report_package.get("data_confidence_score", 65) or 65
# engine returns 0, but `0 or 65` = 65 in Python
# Result: coverage_pct = 65 (WRONG, should be 0)

# L1657-1659  ← SECONDARY CAUSE
{"icon": "✓", "name": "Yahoo Finance", "verified": True},   # always True
{"icon": "✓", "name": "Company Metadata", "verified": True}, # always True
# No condition on confidence_level for these two sources
```

### UI Render Keys
- `render_source_transparency` ← `source_transparency.coverage_pct` = **65** (should be 0)
- `source_transparency.verified_sources[0].verified` = **True** (should be False)
- `source_transparency.verified_sources[1].verified` = **True** (should be False)

### Fix
```python
# app.py L1649 — fix the `or 65` guard
_cov = 0 if _conf_level == "INVALID" else (report_package.get("data_confidence_score", 65) or 65)

# app.py L1657-1659 — gate Yahoo/Metadata on confidence_level
{"icon": "✓" if _conf_level not in ("INVALID", "LOW") else "✗",
 "name": "Yahoo Finance",
 "verified": _conf_level not in ("INVALID", "LOW")},
{"icon": "✓" if _conf_level not in ("INVALID", "LOW") else "✗",
 "name": "Company Metadata",
 "verified": _conf_level not in ("INVALID", "LOW")},
```

---

## BUG-2: 0941.HK Peer Comparison Shows Ticker Codes Not Names

**File:** `core/fos_components.py` → `render_peer_comparison`  
**Evidence:** `debug_audit/0941_payload_audit.json`

### Engine Output (incomplete)
```json
{
  "peers": [
    {"ticker": "0728.HK", "name": null},
    {"ticker": "0762.HK", "name": null}
  ]
}
```

### What render_peer_comparison Does (wrong)
```python
# fos_components.py — render_peer_comparison
peer_name = peer.get("name") or peer.get("company_name")
# → None or None = None
# UI then falls back to displaying peer["ticker"] = "0728.HK"
# No "公司名稱未收錄" fallback defined
```

### UI Render Keys
- `competitive_landscape.peers[0].name` = **null** → renders **"0728.HK"**
- `competitive_landscape.peers[1].name` = **null** → renders **"0762.HK"**
- Expected: **"中國電信股份有限公司"** or **"公司名稱未收錄"**

### Fix (two-layer)
```python
# Layer 1: core/fos_components.py — render_peer_comparison
peer_name = peer.get("name") or peer.get("company_name") or "公司名稱未收錄"

# Layer 2: core/competitive_landscape_engine.py — when building peer dict
name = master_data.get(ticker, {}).get("name") or master_data.get(ticker, {}).get("company_name") or "公司名稱未收錄"
peer_dict = {"ticker": ticker, "name": name, ...}
```

---

## BUG-3: AI Investment Committee Shows Placeholder / Fake Data

**File:** `app.py` L1748–1812, `core/fos_components.py` → `render_multi_agent_committee`  
**Evidence:** `debug_audit/3416_payload_audit.json`

### Engine Output (empty — correct when no data)
```
investment_committee = {}
multi_agent_discussion.table = []
```

### What app.py Does (wrong — 3 compounding issues)

**Issue A: Hardcoded fallback bull/bear agents (L1777-1782)**
```python
if not _bull_agents_v2:  # True when table=[]
    for pt in ic_data.get("bull_points", ["估值合理", "股息率具吸引力", "業務穩定"]):
        _bull_agents_v2.append({"name": "牛市 Agent", "view": pt, "reasons": []})
# → Injects 3 fake bull agents with hardcoded generic text
```

**Issue B: Hardcoded default scores (L1787-1789)**
```python
"bull_score": ic_data.get("bull_score", 60),   # → 60 (fake)
"bear_score": ic_data.get("bear_score", 40),   # → 40 (fake)
"confidence": ic_data.get("confidence", 70),   # → 70 (fake)
```

**Issue C: render_multi_agent_committee shows placeholder (fos_components.py)**
```python
# When agents={}, renders "觀點待整合" placeholder cards
# No early-return guard for empty agents
```

### UI Render Keys
- `render_bull_bear_debate` ← `agent_opinions_v2.bull_agents` = **[fake 牛市 Agent x3]**
- `render_multi_agent_committee` ← `investment_committee.agents` = **{}** → **"觀點待整合"**
- `agent_opinions_v2.bull_score` = **60** (fake default)
- `agent_opinions_v2.confidence` = **70** (fake default)

### Fix
```python
# app.py L1748 — add top-level guard
if confidence_level in {"HIGH", "MEDIUM"}:
    _section_title("AI 投資委員會", "AI 投資委員會", "")
    discussion = sections.get("multi_agent_discussion", {}) or {}
    ic_data = report_package.get("investment_committee", {}) or {}
    table = discussion.get("table", []) or []

    # NEW: hide panel if no real data
    if not ic_data and not table:
        st.info("AI 投資委員會資料不足，已略過此區塊。")
    else:
        # ... existing render logic, but REMOVE L1777-1782 fallback injection

# app.py L1777-1782 — REMOVE hardcoded fallback
# DELETE: if not _bull_agents_v2: for pt in ic_data.get("bull_points", [...]):
# DELETE: if not _bear_agents_v2: for pt in ic_data.get("bear_points", [...]):

# fos_components.py — render_multi_agent_committee
def render_multi_agent_committee(data):
    ic = data.get("investment_committee", {})
    agents = ic.get("agents", {})
    if not agents:
        return  # hide panel, do not render placeholder
```

---

## Payload Chain Summary

```
Engine Output
    ↓
report_package (dict)
    ↓
app.py fallback layer  ← ALL 3 BUGS LIVE HERE
    ↓
render_*(payload_dict)
    ↓
Streamlit UI
```

The audit report tested engine output directly and found it correct. The fallback layer in app.py was not tested. This is why audit passed but browser QA failed.

---

## Files Requiring Changes

| File | Lines | Change |
|------|-------|--------|
| `app.py` | L1649 | Fix `or 65` guard for INVALID confidence |
| `app.py` | L1657-1659 | Gate Yahoo/Metadata verified on confidence_level |
| `app.py` | L1748 | Add guard to hide IC panel when no data |
| `app.py` | L1777-1782 | Remove hardcoded bull/bear fallback injection |
| `core/fos_components.py` | render_peer_comparison | Add `or "公司名稱未收錄"` fallback |
| `core/fos_components.py` | render_multi_agent_committee | Return early when agents={} |
| `core/competitive_landscape_engine.py` | peer dict builder | Guarantee name field populated |

---

## Merge Decision

**❌ DO NOT MERGE v4.0.3**

All 3 browser QA failures are confirmed as real bugs with identified root causes in app.py's fallback injection layer. The v4.0.3 audit report was incomplete because it only tested engine output, not the full payload chain through app.py to UI render.

Next step: implement fixes listed above, then re-run browser QA against all 3 test cases before merge.
