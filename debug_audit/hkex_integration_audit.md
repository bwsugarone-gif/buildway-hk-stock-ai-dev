# HKEX Integration Audit
**Date:** 2026-06-01
**Status:** DISABLED — Not shown to clients

## Current Completion: 10%

### What Exists (Architecture Ready)

| Component | Status | File |
|-----------|--------|------|
| Three-state engine | COMPLETE | core/hkex_engine.py |
| UI render section | COMPLETE | app.py _render_hkex_section |
| Parser skeleton | COMPLETE | core/hkex_parser.py |
| Source registry entry | COMPLETE | core/hkex_engine.py L87-106 |

### Current State

hkex_engine.py L24:
  _CURRENT_HKEX_STATUS = HKEX_STATUS_DISABLED

When DISABLED, engine returns:
  source_verified = False
  announcements = []
  message = HKEX 公告模組尚未啟用

Three states defined:
  DISABLED — current state, no data source
  ENABLED_EMPTY — connected but no recent announcements
  ENABLED_WITH_DATA — connected with real announcement data

### Why Not Shown to Clients

Per Sprint rules: HKEX module completion too low for client display.
_render_hkex_section in app.py is called but returns early when status=DISABLED.
No fake data is shown. No verified tick is shown.

### Data Source Options for Future Integration

Option A — HKEX披露易 Web Scraper
  URL: https://www.hkexnews.hk/listedco/listconews/advancedsearch/
  Method: requests + BeautifulSoup
  Rate limit: ~1 req/sec recommended
  Data: announcement title, date, type, PDF link
  Effort: 2-3 days

Option B — HKEX OpenAPI (if available)
  Check: https://www.hkex.com.hk/eng/market/sec_tradinfo/openapi.htm
  Status: Limited availability, mostly market data not announcements
  Effort: 1-2 days if API exists

Option C — Third-party Data Provider
  Examples: Refinitiv, Bloomberg, Wind, Futu OpenAPI
  Cost: Subscription required
  Effort: 1 day integration once API key obtained

### Recommended Path

1. Implement Option A (scraper) as MVP
2. Set _CURRENT_HKEX_STATUS = HKEX_STATUS_ENABLED_WITH_DATA only after scraper tested
3. Add rate limiting and error handling
4. Test with 0941.HK, 0700.HK, 0005.HK before enabling for all tickers

### UI Hiding Confirmation

app.py _render_hkex_section:
  - Called only when confidence_level in {HIGH, MEDIUM}
  - Returns early when hkex_engine returns status=DISABLED
  - No HKEX section visible to clients in current build

source_transparency fallback (app.py L1657-1659):
  - HKEX Filing shown as verified=False (circle icon, not tick)
  - This is correct behavior

### Next Steps Before Enabling

1. Implement scraper or API integration
2. Change _CURRENT_HKEX_STATUS constant
3. Test ENABLED_EMPTY path (connected but no announcements)
4. Test ENABLED_WITH_DATA path with real announcement data
5. Browser QA: verify HKEX section renders correctly
6. Only then show to clients
