# Master Data Expansion Report
**Date:** 2026-06-01
**Sprint:** FOS v4.1 Data Foundation Sprint

## Summary

| Metric | Before | After |
|--------|--------|-------|
| Total entries | 14 | 80 |
| New entries added | — | 66 |
| Sectors covered | 5 | 43 |
| Coverage increase | — | +471% |

## Key Tickers Now Covered

| Ticker | Company | Sector |
|--------|---------|--------|
| 0066.HK | 港鐵公司 | 交通運輸 / 基建 |
| 0728.HK | 中國電訊 | 電訊 / 公用 |
| 0762.HK | 中國聯通 | 電訊 / 公用 |
| 0388.HK | 香港交易所 | 金融 / 交易所 |
| 0939.HK | 建設銀行 | 銀行 / 金融 |
| 1398.HK | 工商銀行 | 銀行 / 金融 |
| 1288.HK | 農業銀行 | 銀行 / 金融 |
| 2318.HK | 中國平安保險 | 保險 / 金融 |
| 2628.HK | 中國人壽保險 | 保險 / 金融 |
| 1211.HK | 比亞迪股份 | 汽車 / 新能源 |
| 9868.HK | 小鵬汽車 | 汽車 / 新能源 |
| 2015.HK | 理想汽車 | 汽車 / 新能源 |
| 1093.HK | 石藥集團 | 醫藥 / 健康 |
| 2269.HK | 藥明生物 | 醫藥 / 生物科技 |
| 6160.HK | 百济神州 | 醫藥 / 生物科技 |

## Sector Coverage

| Sector | Count |
|--------|-------|
| 銀行 / 金融 | 11 |
| 地產 / 香港 | 5 |
| 地產 / 內房 | 5 |
| 保險 / 金融 | 5 |
| 電訊 / 公用 | 4 |
| 科技 / 互聯網 | 4 |
| 綜合企業 | 3 |
| 食品 / 消費 | 3 |
| 其他板塊 | 40 |

## SECTOR_PEERS Updates

competitive_landscape_engine.py SECTOR_PEERS expanded from 12 groups to 22 groups:

- Added: 0066 (Transport/Infrastructure) → peers: 0293, 0019, 1038
- Added: Banking groups for 0939, 1398, 1288, 3968
- Added: Tech groups for 1024, 9626, 9999
- Added: Insurance groups for 2628, 2601
- Added: Property HK groups for 0083, 0101
- Added: Energy groups for 1088, 1171
- Added: Automobiles/EV groups for 0175, 1211, 9868, 2015
- Added: Healthcare/Pharma groups for 1093, 1177, 2269, 6160
- Added: Consumer/Sportswear groups for 2020, 2331
- Added: Gaming/Macau groups for 0027, 1128

## Fields Per Entry

Each entry contains:
- ticker (key)
- name_zh (Traditional Chinese name)
- name_en (English name)
- sector / sector_zh / sector_en
- business_zh / business_en
- market_type / market_type_zh / market_type_en

## Impact on Browser QA

- BUG-2 (0941 peer names): 0728.HK now resolves to 中國電訊, 0762.HK to 中國聯通
- 0066.HK: now has company name, sector, business description
- render_peer_comparison: company_name field populated for all SECTOR_PEERS tickers

## Remaining Gaps

- competitive_profile.json not yet expanded (strengths/weaknesses still show fallback text for new tickers)
- Market metrics (PE, PB, dividend_yield) not in master data — these come from Yahoo Finance at runtime
- Target: 100+ entries for v4.2 (need to add more mid-cap and small-cap stocks)
