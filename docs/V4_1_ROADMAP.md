# V4.0 → V4.1 Roadmap
**Buildway Tech (HK) Limited — HK Stock Intelligence Platform**

---

## V4.0 完成項目（本次交付）

### Phase A — Version Bump
- `core/config.py` → v4.0.0, BUILD_STAGE = "Research Platform Hardening Layer"

### Phase B — HKEX Engine
- `core/hkex_engine.py` — 三態 HKEX 模組（DISABLED / ENABLED_EMPTY / ENABLED_WITH_DATA）
- DISABLED 狀態下永不顯示「已驗證」，永不計入資料可信度評分

### Phase C — Source Registry
- `core/source_registry.py` — 單一資料來源登記冊
- 所有 UI、PDF、data_lake 必須從 `report_package["source_registry"]` 讀取
- 提供 `compute_coverage_pct()` 和 `compute_confidence_level()` 函數

### Phase D — Competitive Profile Data
- `data/competitive_profile.json` — 10隻主要港股競爭資料
- 包含：sector, product_lines, market_positioning, strengths, weaknesses, future_strategy, peer_group

### Phase E — Peer Comparison Engine 升級
- `core/competitive_landscape_engine.py` — 整合 competitive_profile.json
- 同行組別優先從 competitive_profile.json 讀取，fallback 到 SECTOR_PEERS
- 修正 0688 行業分類（地產，非保險）
- 新增 `get_competitive_profile()` 函數

### Phase F — Market Snapshot Engine
- `core/market_snapshot_engine.py` — 統一市場數據快照
- 所有 UI 和 PDF 必須從 `report_package["market_snapshot"]` 讀取
- 52週數據缺失時，所有顯示位置一致顯示「未取得」

### Phase G — Financial History（待 app.py 整合）
- 財務歷史趨勢圖（Revenue / EBITDA / Net Profit / FCF）
- 多年比較圖，避免大量文字

### Phase H — News Localizer
- `core/news_localizer.py` — 繁體中文新聞標題本地化
- 規則式翻譯，永不虛構新聞內容
- 提供 `LABEL_MAP` 用於 UI 標籤替換

### Phase I — Agent Opinion Engine（已完整）
- `core/agent_opinion_engine.py` — 6個 Agent 意見引擎
- 永不輸出「分析中」或 0% 信心度

### Phase K — Investment Conclusion Engine
- `core/investment_conclusion_engine.py` — 投資結論引擎
- 5因素加權評分（估值25% + 風險25% + 財務20% + 新聞15% + 市場15%）
- 輸出：評級、投資週期、適合投資者類型
- 目標價明確說明「未能可靠估算」，不虛構數字

---

## V4.1 待辦項目

### 優先級 HIGH

#### app.py 整合
- [ ] 頁面重組：開始分析 → 報告摘要 → 同行比較 → 市場分析 → 財務分析 → 風險分析 → 新聞 → AI委員會 → 最終結論 → 市場板塊
- [ ] 移除：客戶觀察名單、客戶資料、資料儲存狀態、Session Data Lake Status、Report History Workspace
- [ ] 整合 `build_source_registry()` 到 report_package 生成流程
- [ ] 整合 `build_market_snapshot()` 到 report_package 生成流程
- [ ] 整合 `build_investment_conclusion()` 到最終結論區塊
- [ ] 整合 `get_competitive_profile()` 到同行比較區塊

#### UI 顏色規範
- [ ] 分析按鈕：藍色 (#1E88E5)
- [ ] 下載按鈕：綠色 (#43A047)
- [ ] 重新分析按鈕：橙色 (#FB8C00)
- [ ] 清除按鈕：紅色 (#E53935)
- [ ] 禁止所有按鈕同色

#### Bull/Bear 視覺設計
- [ ] 頁面左側固定：🐂 Bull Market（綠色系背景圖層）
- [ ] 頁面右側固定：🐻 Bear Market（紅色系背景圖層）
- [ ] 覆蓋範圍：市場分析、財務分析、風險分析、新聞分析、AI委員會、最終結論
- [ ] AI委員會維持獨立模組，保留原有背景設計

### 優先級 MEDIUM

#### PDF V3 升級
- [ ] 加入同行比較頁
- [ ] 加入可信度來源頁
- [ ] 加入 Bull vs Bear 辯論頁
- [ ] 加入最終投資結論卡
- [ ] 所有圖表輸出到 PDF
- [ ] 風格：Bloomberg / Morningstar / Institutional Research

#### 財務分析視覺化
- [ ] Revenue Trend 圖
- [ ] EBITDA Trend 圖
- [ ] Net Profit Trend 圖
- [ ] FCF Trend 圖
- [ ] 多年比較圖（避免大量文字）

#### 風險儀表板
- [ ] 流動性風險、估值風險、市場風險、財務風險、新聞風險
- [ ] 總風險分數儀表板形式顯示

#### 新聞分析升級
- [ ] 正面/中性/負面新聞數量統計
- [ ] 新聞可信度顯示
- [ ] 催化事件 / 監察事項分類
- [ ] 禁止生成虛構新聞

### 優先級 LOW

#### HKEX 模組啟用
- [ ] 接入 HKEX 披露易 API 或爬蟲
- [ ] 將 `_CURRENT_HKEX_STATUS` 改為 `ENABLED_EMPTY` 或 `ENABLED_WITH_DATA`

#### 更多股票競爭資料
- [ ] 擴展 competitive_profile.json 至 50+ 港股
- [ ] 加入銀行、保險、能源板塊詳細資料

---

## 技術債務

| 項目 | 優先級 | 說明 |
|------|--------|------|
| source_transparency.py 與 source_registry.py 統一 | HIGH | 兩個模組功能重疊，需合併 |
| fos_components.py 重構 | MEDIUM | 部分組件仍有硬編碼「—」 |
| report_builder.py 整合新引擎 | HIGH | 需調用 market_snapshot_engine, source_registry |
| PDF 中文字體 | MEDIUM | 確保 NotoSansCJK 在所有環境可用 |

---

## 版本歷史

| 版本 | 日期 | 主要變更 |
|------|------|----------|
| v2.5 | 2025-Q4 | UX Cleanup Layer |
| v2.6 | 2025-Q4 | Peer Comparison Layer |
| v2.7 | 2025-Q4 | Investment Committee Layer |
| v2.8 | 2025-Q4 | Institutional Research Layer |
| v3.5 | 2026-Q1 | FOS Client Experience Layer |
| v4.0 | 2026-05 | Research Platform Hardening Layer |
| v4.1 | TBD | Full app.py Integration + PDF V3 |

---

*© 2026 Buildway Tech (HK) Limited. Internal Development Document.*
