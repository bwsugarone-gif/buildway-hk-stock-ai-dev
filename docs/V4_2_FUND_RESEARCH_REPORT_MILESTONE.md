# FOS v4.2.0 Fund Research Report Milestone
**Buildway Tech (HK) Limited — HK Stock Intelligence Platform**

---

## 概述

v4.2.0 是 Fund Research Report 質量提升 milestone，針對 Web、Mobile、PDF 三端進行一致性修正與體驗優化。

**目標**: 清除資料污染、補完競爭分析、統一報告結構、強化投資結論。

---

## 核心修正項目

### 1. 清除競爭格局分析的 `?` 污染
**問題**: 競爭對手數據缺失時顯示 `?`，造成視覺污染。

**解決方案**:
- `fos_components.py` 的 `render_peer_comparison` 和 `render_competitive_landscape` 中，所有 `?` 改為 `N/A` 或 `資料未收錄`
- `competitive_landscape_engine.py` 確保所有 fallback 返回 `N/A` 而非 `?`
- 統一顯示邏輯：數值欄位用 `N/A`，文字欄位用 `資料未收錄`

---

### 2. 補完整競爭對手摘要
**問題**: 競爭對手分析內容過於簡略，缺乏產品線、市場定位、競爭優勢等關鍵信息。

**解決方案**:
- 擴展 `data/competitive_profile.json`，補齊至少 30+ 主要港股的完整資料
- 包含字段：
  - `product_lines`: 產品線列表
  - `market_positioning`: 市場定位描述
  - `strengths`: 競爭優勢（3-5點）
  - `weaknesses`: 競爭弱點（3-5點）
  - `future_strategy`: 未來戰略
  - `peer_group`: 同行組別
- `competitive_landscape_engine.py` 輸出完整結構化數據
- UI 顯示：
  - 產品線以標籤形式展示
  - 優勢/弱點以列表展示
  - 市場定位以簡短段落展示

---

### 3. 修正資料來源顯示
**問題**: 出現「資料來源不明」或「未已驗證來源」等混亂文字。

**解決方案**:
- `source_registry.py` 和 `source_transparency.py` 統一來源標籤：
  - `yahoo_finance` → 「Yahoo Finance」
  - `hkex` → 「HKEX 披露易」
  - `company_meta` → 「公司基本資料」
  - `news_api` → 「新聞資料源」
  - `analyst_consensus` → 「分析師共識」（預留）
- 未驗證來源顯示：`🔴 未驗證` 而非「資料來源不明」
- 已驗證來源顯示：`✅ 已驗證`
- `fos_components.py` 的 `render_source_transparency` 統一顯示邏輯

---

### 4. 刪除重覆市場快照
**問題**: 報告中多次顯示 Market Snapshot，造成冗餘。

**解決方案**:
- `app.py` 中只在「市場分析」section 顯示一次完整 Market Snapshot
- 刪除其他 section 的重覆 Market Snapshot 卡片
- `market_snapshot_engine.py` 確保輸出格式統一

---

### 5. 刪除風險事件分析，保留風險儀表板
**問題**: 風險事件分析與風險儀表板內容重疊。

**解決方案**:
- `app.py` 刪除「風險事件分析」section
- 保留並強化「風險儀表板」：
  - 流動性風險
  - 估值風險
  - 市場風險
  - 財務風險
  - 新聞情緒風險
- 總風險分數以儀表板形式顯示（1-10分）
- `risk_engine_v2.py` 確保 5 項風險分數完整

---

### 6. 最終投資結論升級為 Investment Committee
**問題**: 最終結論常出現「數據不足，採用中性評分」，缺乏實質建議。

**解決方案**:
- `investment_conclusion_engine.py` 強化決策邏輯：
  - 5 因素加權評分（估值25% + 風險25% + 財務20% + 新聞15% + 市場15%）
  - 當單一因素數據缺失，使用保守分數 5.0，但不影響其他因素評分
  - 至少 3 個因素有真實數據才輸出結論，否則顯示「數據不足，建議待更多數據後重新評估」
- 評級映射：
  - `8.0-10.0` → 買入
  - `6.5-7.9` → 觀察
  - `5.0-6.4` → 中性
  - `3.5-4.9` → 減持
  - `1.0-3.4` → 避免
- 目標價：明確說明「需要 DCF 模型或分析師共識，目前未能可靠估算」
- `app.py` 的「最終投資結論」section 改用 `investment_conclusion_engine` 輸出，不再依賴 `cover.get("final_rating")`

---

### 7. 手機版隱藏 sidebar，避免橫向 overflow
**問題**: 手機版 sidebar 造成橫向滾動，體驗差。

**解決方案**:
- `.streamlit/config.toml` 新增 mobile 配置：
  ```toml
  [browser]
  gatherUsageStats = false
  
  [client]
  showSidebarNavigation = false
  ```
- `app.py` 使用 `st.set_page_config` 設定：
  ```python
  st.set_page_config(
      page_title="Buildway HK Stock AI",
      page_icon="📊",
      layout="wide",
      initial_sidebar_state="collapsed"  # 預設收起
  )
  ```
- CSS 隱藏 mobile 版 sidebar：
  ```css
  @media (max-width: 768px) {
      [data-testid="stSidebar"] {
          display: none;
      }
  }
  ```

---

### 8. PDF 與 Web section 一致
**問題**: PDF 輸出結構與 Web UI 不一致。

**解決方案**:
- `pdf_generator.py` 同步 Web 結構：
  1. 封面頁
  2. 市場快照（一次）
  3. 同行比較
  4. 財務分析
  5. 風險儀表板（不含風險事件）
  6. 新聞分析
  7. AI 投資委員會
  8. 最終投資結論（使用 investment_conclusion_engine）
  9. 資料來源與可信度
  10. 免責聲明
- 所有 section 標題、內容、格式與 Web 一致
- 中文字體確保 NotoSansCJK 正確載入

---

## 技術實施清單

### Core Engine 修改
- [x] `core/config.py` → `APP_VERSION = "v4.2.0"`, `BUILD_STAGE = "Fund Research Report Quality Layer"`
- [ ] `core/competitive_landscape_engine.py` → 移除所有 `?` fallback
- [ ] `core/source_registry.py` → 統一來源標籤映射
- [ ] `core/investment_conclusion_engine.py` → 強化決策邏輯（至少3因素有數據）
- [ ] `core/risk_engine_v2.py` → 確認 5 項風險完整輸出

### Data 修改
- [ ] `data/competitive_profile.json` → 擴展至 30+ 股票，補齊所有字段

### UI 修改
- [ ] `app.py`:
  - 只保留一個 Market Snapshot section
  - 刪除風險事件分析 section
  - 最終投資結論接線 `investment_conclusion_engine`
  - `st.set_page_config(initial_sidebar_state="collapsed")`
- [ ] `core/fos_components.py`:
  - `render_peer_comparison` 移除 `?`
  - `render_competitive_landscape` 移除 `?`，補完顯示邏輯
  - `render_source_transparency` 統一來源標籤
  - `render_investment_conclusion` 使用 engine 輸出

### PDF 修改
- [ ] `core/pdf_generator.py` → 同步 Web 結構，移除重覆 sections

### Config 修改
- [ ] `.streamlit/config.toml` → mobile sidebar 配置

### 測試
- [ ] `test_v420_fund_research_milestone.py`:
  - 競爭分析無 `?` 污染
  - 資料來源標籤統一
  - Market Snapshot 只出現一次
  - 風險事件分析已刪除
  - 投資結論使用 engine 輸出
  - Mobile sidebar 預設收起

---

## QA 驗收標準

| # | 項目 | 驗收條件 | 測試方法 |
|---|------|---------|---------|
| 1 | 競爭分析 | 無 `?` 字符，所有缺失數據顯示 `N/A` 或 `資料未收錄` | Browser QA + pytest |
| 2 | 競爭對手摘要 | 至少 30 個主要港股有完整資料（產品線、優勢、弱點、定位） | 檢查 `competitive_profile.json` |
| 3 | 資料來源 | 無「資料來源不明」或「未已驗證來源」 | Browser QA + PDF QA |
| 4 | Market Snapshot | 整個報告只出現一次 | Browser QA + PDF QA |
| 5 | 風險分析 | 只有風險儀表板，無風險事件分析 | Browser QA + PDF QA |
| 6 | 投資結論 | 使用 engine 輸出，至少 3 因素有數據才給結論 | pytest + Browser QA |
| 7 | Mobile UI | Sidebar 預設收起，無橫向滾動 | Mobile browser QA (iPhone/Android) |
| 8 | PDF 一致性 | PDF 結構與 Web 完全一致 | PDF QA |

---

## 版本歷史

| 版本 | 日期 | 主要變更 |
|------|------|----------|
| v4.1.1 | 2026-06-01 | Product Completion Sprint Layer |
| v4.2.0 | 2026-06-03 | Fund Research Report Quality Layer |

---

*© 2026 Buildway Tech (HK) Limited. Internal Development Document.*
