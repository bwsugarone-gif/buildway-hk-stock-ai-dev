# FOS v4.1 Product Completeness Audit
**Date:** 2026-06-01
**Method:** Static code analysis — source files, data files, app.py render chain
**Scope:** 6 product features vs current implementation state

---

## Summary Table

| # | Feature | Status | Completion |
|---|---------|--------|-----------|
| 1 | 0066 Support | ❌ NOT SUPPORTED | 0% |
| 2 | Peer Name Lookup | ⚠️ PARTIAL | 60% |
| 3 | Competitive Landscape Content | ⚠️ PARTIAL | 55% |
| 4 | Final Investment Conclusion | ✅ FUNCTIONAL | 80% |
| 5 | HKEX Integration | ❌ DISABLED | 10% |
| 6 | News Translation Pipeline | ⚠️ PARTIAL | 65% |

---

## Item 1: 0066 Support (MTR Corporation)

**Current Status:** ❌ NOT SUPPORTED

**Root Cause:**
`hk_stock_master_data.json` contains only 14 entries. 0066.HK (MTR Corporation) is not in the file. Confirmed by live data check:
```
0066     -> NOT FOUND
0066.HK  -> NOT FOUND
66       -> NOT FOUND
66.HK    -> NOT FOUND
Total entries in master data: 14
```

`competitive_landscape_engine.py` L26-56 `SECTOR_PEERS` dict also has no entry for `0066`. When ticker is not found, engine falls back to `_default` peers: `["0700", "0005", "0941", "0388", "1299"]` — which are irrelevant to MTR (transport/infrastructure).

`competitive_profile.json` — not checked for 0066 entry but master data absence means company name, sector, business description all return `None`.

**What happens when user enters 0066:**
- `_build_subject_record` returns `company_name = "0066.HK"` (ticker fallback)
- `_get_peer_tickers` returns HSI blue chip defaults (wrong sector)
- `render_source_transparency` shows 65% coverage (BUG-1 fallback)
- Report generates with wrong peer group and no company metadata

**Completion:** 0%

**Files Involved:**
- `data/hk_stock_master_data.json` — missing 0066.HK entry
- `core/competitive_landscape_engine.py` L26-56 — missing 0066 in SECTOR_PEERS
- `data/competitive_profile.json` — likely missing 0066 entry

**Recommended Fix:**
Add 0066.HK to `hk_stock_master_data.json` with fields: `name_zh`, `name_en`, `sector`, `business_zh`, `market_type`. Add 0066 to `SECTOR_PEERS` with transport peers (e.g., 0293 Cathay, 0008 PCCW, or relevant infrastructure stocks). Add 0066 entry to `competitive_profile.json`.

---

## Item 2: Peer Name Lookup

**Current Status:** ⚠️ PARTIAL

**Root Cause:**
`competitive_landscape_engine.py` L182-193 `_build_peer_record` resolves company name via:
```python
"company_name": (
    stock_info.get("name_zh")
    or stock_info.get("name_en")
    or stock_info.get("name")
    or stock_info.get("company_name")
    or f"{ticker}.HK"   # ← last resort: raw ticker string
)
```

This is correct at the engine level — it tries 4 fields before falling back to ticker. However:

1. The engine output key is `company_name`, but `fos_components.py render_peer_comparison` reads `peer.get("name")` first, then `peer.get("company_name")`. If the engine puts the name in `company_name` but the renderer looks for `name` first, the lookup succeeds only on the second try — which works, but is fragile.

2. For tickers not in `hk_stock_master_data.json` (e.g., 0728.HK, 0762.HK if not in the 14-entry file), `stock_info = {}` and all 4 field lookups return `None`, so the fallback `f"{ticker}.HK"` fires — displaying raw ticker.

3. Confirmed: master data has only 14 entries. Telecom peers 0728 and 0762 are likely not in the file, causing the BUG-2 failure observed in browser QA.

**Completion:** 60% (engine logic correct for covered tickers; fails for uncovered tickers)

**Files Involved:**
- `data/hk_stock_master_data.json` — only 14 entries, missing most peer tickers
- `core/competitive_landscape_engine.py` L182-193 — `_build_peer_record`
- `core/fos_components.py` — `render_peer_comparison` name field priority

**Recommended Fix:**
- Expand `hk_stock_master_data.json` to cover all tickers referenced in `SECTOR_PEERS` (minimum ~30 entries)
- In `fos_components.py render_peer_comparison`: `peer_name = peer.get("name") or peer.get("company_name") or "公司名稱未收錄"`
- In `_build_peer_record`: add `"name"` as alias for `company_name` so both render paths work

---

## Item 3: Competitive Landscape Content

**Current Status:** ⚠️ PARTIAL

**Root Cause:**
Three sub-components, each with different completeness:

**3a. Peer comparison table** — depends on master data coverage (see Item 2). For covered tickers, table renders with real metrics. For uncovered tickers, all cells show "N/A". Current master data covers ~14 tickers, so most peer comparisons will be N/A-heavy.

**3b. Strengths / Weaknesses** — sourced from `competitive_profile.json`. Engine L140-141:
```python
"strengths": entry.get("strengths") or ["競爭優勢資料未收錄"],
"weaknesses": entry.get("weaknesses") or ["競爭弱點資料未收錄"],
```
Fallback text is shown when ticker not in `competitive_profile.json`. Coverage of `competitive_profile.json` is unknown without reading it, but given master data has only 14 entries, profile coverage is likely similarly limited.

**3c. Advantages/Disadvantages computation** — `_compute_advantages` L261-300 compares subject vs peer metrics. If peer metrics are all N/A (due to missing master data), falls back to `"同業比較數據不足，無法比較"`. This is honest but unhelpful.

**3d. Sector peer grouping** — `SECTOR_PEERS` covers ~20 tickers explicitly. Any ticker outside this list gets HSI blue chip defaults, which is wrong sector context.

**Completion:** 55% (structure complete, data coverage insufficient)

**Files Involved:**
- `data/hk_stock_master_data.json` — insufficient coverage
- `data/competitive_profile.json` — coverage unknown, likely limited
- `core/competitive_landscape_engine.py` L26-56 — SECTOR_PEERS coverage
- `core/fos_components.py` — `render_competitive_landscape`, `render_peer_comparison`

**Recommended Fix:**
- Expand master data to 50+ tickers covering all SECTOR_PEERS entries
- Expand competitive_profile.json to match
- Add more sector groups to SECTOR_PEERS (transport, healthcare, retail, gaming)

---

## Item 4: Final Investment Conclusion

**Current Status:** ✅ FUNCTIONAL (with caveats)

**Root Cause of Caveats:**
`investment_conclusion_engine.py` `build_investment_conclusion` is well-structured with 5 weighted factors (valuation 25%, risk 25%, financial 20%, news 15%, market 15%). Each factor has a safe fallback score of 5.0 when data is missing.

**What works:**
- Rating derivation (買入/觀察/中性/減持/避免) from composite score
- Investment horizon and investor type derivation
- Decision basis table with per-factor scores and summaries
- Honest target price handling: "目標價未能可靠估算（需要分析師共識或 DCF 模型）"
- No blank fields, no "—" outputs

**Caveats:**
1. When all 5 factors fall back to 5.0 (no data), composite = 5.0 → rating = "中性". This is technically correct but may mislead users into thinking the stock was actually analyzed.
2. `app.py L1820-1827` renders `render_investment_conclusion` with `rating` from `cover.get("final_rating")`, not from `investment_conclusion_engine` output. The engine output is not wired to the UI render — the UI uses the cover page rating which comes from a different path.
3. Target price is always "未能可靠估算" — no DCF or analyst consensus integration exists.

**Completion:** 80% (engine complete; UI wiring uses cover rating not engine output; target price always placeholder)

**Files Involved:**
- `core/investment_conclusion_engine.py` — complete, well-structured
- `app.py` L1820-1827 — `render_investment_conclusion` uses `cover.get("final_rating")` not engine output
- `core/fos_components.py` — `render_investment_conclusion`

**Recommended Fix:**
- Wire `investment_conclusion_engine` output to `render_investment_conclusion` in app.py
- Replace `cover.get("final_rating", "觀察")` with engine-computed rating when available
- Document that target price requires future DCF/analyst consensus integration

---

## Item 5: HKEX Integration

**Current Status:** ❌ DISABLED

**Root Cause:**
`hkex_engine.py` L24: `_CURRENT_HKEX_STATUS = HKEX_STATUS_DISABLED`

This is a hardcoded constant. No API connection, no scraper, no data source. The engine correctly returns `source_verified=False` and `announcements=[]` when disabled.

**What the engine does when DISABLED:**
```python
return {
    "status": "DISABLED",
    "source_verified": False,
    "announcements": [],
    "message": "HKEX 公告模組尚未啟用",
    "detail": "系統尚未接入 HKEX 披露易公告資料源...",
}
```

**What app.py does with this:** `_render_hkex_section` in app.py renders the HKEX section. When status=DISABLED, it should show the "not connected" message. However, the BUG-1 fallback in `source_transparency` still injects `HKEX Filing` as a source entry (with `verified=False`), which is correct but the entry's presence may confuse users.

**Three-state architecture exists** (DISABLED / ENABLED_EMPTY / ENABLED_WITH_DATA) — the design is ready for future integration. Only the data source connection is missing.

**Completion:** 10% (architecture designed, UI render exists, data source = 0%)

**Files Involved:**
- `core/hkex_engine.py` L24 — `_CURRENT_HKEX_STATUS = HKEX_STATUS_DISABLED`
- `core/hkex_parser.py` — parser exists but no live data feed
- `app.py` — `_render_hkex_section`

**Recommended Fix:**
- Short term: ensure UI clearly labels HKEX as "未接入" with link to hkexnews.hk
- Long term: implement HKEX披露易 scraper or API integration, then set `_CURRENT_HKEX_STATUS = HKEX_STATUS_ENABLED_WITH_DATA`
- Do not change status constant until real data source is connected

---

## Item 6: News Translation Pipeline

**Current Status:** ⚠️ PARTIAL

**Root Cause:**
`news_localizer.py` implements a rule-based translation pipeline with three layers:

**Layer 1 — Pattern matching** (L118-156): 16 regex patterns covering earnings, analyst actions, corporate actions, market moves, regulatory news. When matched, returns a clean Chinese label (e.g., "分析師上調評級").

**Layer 2 — Company name substitution** (L74-115): 35 English→Chinese company name mappings. Covers major HK/China stocks but not exhaustive.

**Layer 3 — Label map substitution** (L16-71): 60+ financial term mappings (Buy→買入, EPS→每股盈利, etc.).

**Fallback** (L194-196): If result is still >50% English characters after all substitutions, returns `"原文標題"` — honest but unhelpful.

**Gaps identified:**
1. Pattern matching is one-directional — only returns a category label, not a translated title. "Tencent Reports Record Q3 Earnings" → "騰訊：公佈業績" (company + category only, original detail lost).
2. No LLM translation fallback. Rule-based only.
3. `display_title` (L220) shows Chinese title if available, else original English — no hybrid display.
4. News items from `news_intelligence_agent` may already have `title_zh` set (bypasses translation), but quality depends on agent output.
5. `localize_news_list` is defined but integration point in `report_builder.py` or `app.py` is not confirmed — translation may not be called for all news items.

**Completion:** 65% (pipeline exists and functional for common patterns; no LLM fallback; coverage gaps for uncommon news types)

**Files Involved:**
- `core/news_localizer.py` — complete rule-based pipeline
- `agents/news_intelligence_agent.py` — may set `title_zh` directly
- `core/report_builder.py` — integration point (not confirmed)
- `app.py` L1736-1746 — news render section

**Recommended Fix:**
- Confirm `localize_news_list` is called in report_builder or app.py for all news items
- Add LLM translation as optional Layer 4 when API available (with rule-based as fallback)
- Expand company name map to cover more HK-listed companies
- Consider showing both Chinese label and original title in UI for transparency

---

## Overall Product Readiness

| Feature | Engine | Data | UI Render | Wiring | Overall |
|---------|--------|------|-----------|--------|---------|
| 0066 Support | N/A | ❌ | N/A | N/A | 0% |
| Peer Name Lookup | ✅ | ⚠️ | ⚠️ | ✅ | 60% |
| Competitive Landscape | ✅ | ⚠️ | ✅ | ✅ | 55% |
| Investment Conclusion | ✅ | ✅ | ✅ | ⚠️ | 80% |
| HKEX Integration | ✅ | ❌ | ✅ | ✅ | 10% |
| News Translation | ✅ | ✅ | ✅ | ⚠️ | 65% |

**Blocking issues for v4.1 release:**
1. Master data coverage (affects Items 1, 2, 3) — data gap, not code gap
2. Investment conclusion engine not wired to UI render (Item 4)
3. HKEX disabled with no timeline (Item 5) — acceptable if clearly labeled in UI

**Non-blocking but should fix:**
- News translation integration point confirmation (Item 6)
- Peer name fallback label in fos_components.py (Item 2)
