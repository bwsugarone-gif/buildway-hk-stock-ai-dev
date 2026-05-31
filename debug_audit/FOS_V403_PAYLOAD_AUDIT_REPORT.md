# FOS V4.0.3 Payload Audit Report

**生成時間**: 2026-05-31 09:25:12  
**審計版本**: FOS_V4.0.3  
**審計方法**: 直接調用引擎函數，擷取原始 payload，對比 UI render keys  
**JSON 證據文件**: `debug_audit/12345_payload_audit.json`, `0941_payload_audit.json`, `3416_payload_audit.json`

---

## 執行摘要

Browser QA 觀察到的三個失敗，均已通過 payload 審計確認為真實 bug。審計報告與 v4.0.3 audit report 存在矛盾，原因如下：

| # | 失敗項目 | 根本原因 | 嚴重程度 |
|---|---------|---------|---------|
| 1 | 12345 顯示 65% coverage + 綠勾 | `source_registry` 返回 `confidence_level: "INVALID"` 但 UI 讀取 `source_transparency.confidence_level: "LOW"` — 兩個引擎輸出不一致，UI 讀錯 key | 🔴 CRITICAL |
| 2 | 0941 peer 顯示 `0728.HK` / `0762.HK` | `hk_stock_master_data.json` 所有 ticker 均 `found=False`，`competitive_landscape_engine` fallback 直接用 `{ticker}.HK` 作 company_name | 🔴 CRITICAL |
| 3 | AI 投資委員會顯示「觀點待整合」0% | `investment_committee` dict 缺少 `agents` subkey，`fos_components.render_multi_agent_committee` 讀取 `ic['agents']` 返回 `null` | 🔴 CRITICAL |

---

## BUG 1：12345 INVALID Ticker — source_registry vs source_transparency 不一致

### Engine Output（實際 payload）

**source_registry** 輸出：
```json
{
  "market_data":       { "verified": false, "verified_fields": [] },
  "company_metadata":  { "verified": false, "verified_fields": [] },
  "financial_statement": { "verified": false, "verified_fields": [] },
  "news":              { "verified": false, "verified_fields": [] }
}
```

**source_registry UI render keys**：
```json
{
  "verified_sources": [],
  "coverage_pct": 0.0,
  "confidence_level": "INVALID"
}
```

**source_transparency** 輸出：
```json
{
  "sources_present": [],
  "sources_missing": ["新聞來源", "Yahoo Finance", "公司基本資料", "財務報表", "港交所披露"],
  "coverage_pct": 0,
  "confidence_level": "LOW",
  "data_gaps": ["current_price", "pe_ratio", "company_name", "sector", "revenue"],
  "present_count": 0,
  "total_fields": 30
}
```

### UI Render Keys（fos_components 讀取路徑）

```json
{
  "fos_render_source_transparency": {
    "level_read_from": "source_transparency.confidence_level",
    "level_value": "LOW",
    "coverage_read_from": "source_transparency.coverage_pct",
    "coverage_value": 0,
    "sources_read_from": "source_transparency.sources_present",
    "sources_value": []
  }
}
```

### 診斷

- `source_registry.confidence_level` = `"INVALID"` ✅ 正確
- `source_transparency.confidence_level` = `"LOW"` ⚠️ 不夠嚴格
- `source_transparency.coverage_pct` = `0` ✅ 正確
- `source_transparency.sources_present` = `[]` ✅ 正確

**根本原因**：`source_transparency.build_source_transparency()` 對 invalid ticker 返回 `confidence_level: "LOW"` 而非 `"INVALID"`。UI 讀取 `source_transparency` 而非 `source_registry`，因此顯示 LOW 而非 INVALID。

**Browser QA 觀察到「65% coverage + Yahoo Finance verified + Company Metadata verified」的原因**：
- 這說明 browser 測試時的 report_package 並非空白 package，而是 app.py 在 invalid ticker 情況下仍然填充了部分 fallback 數據到 `market_data` 和 `company_metadata`
- `source_registry` 的 `verified` 邏輯基於欄位是否有值，而非是否來自真實 API
- **結論**：app.py 對 invalid ticker 的 fallback 填充了假數據，導致 source_registry 誤判為 verified

### 預期 vs 實際

| 項目 | 預期 | 實際 Engine Output | 實際 UI 顯示 |
|-----|------|-------------------|------------|
| coverage_pct | 0% | 0% ✅ | 65% ❌ (app fallback 污染) |
| verified_sources | [] | [] ✅ | ["Yahoo Finance", "Company Metadata"] ❌ |
| confidence_level | INVALID | INVALID (registry) / LOW (transparency) | 顯示有效 ❌ |

---

## BUG 2：0941 Peer Comparison — 顯示 raw ticker 而非公司名稱

### Engine Output（實際 payload）

**competitive_landscape** 輸出（0941 的 peers）：
```json
{
  "peers": [
    { "ticker": "0728", "company_name": "0728.HK", "data_quality": "minimal", "metrics_count": 0 },
    { "ticker": "0762", "company_name": "0762.HK", "data_quality": "minimal", "metrics_count": 0 }
  ],
  "peer_tickers": ["0728", "0762"],
  "data_note": "同業數據不足，顯示部分已驗證資料"
}
```

### Master Data Check（根本原因）

```json
{
  "0941": { "found_in_master": false, "name_zh": null, "name_en": null },
  "0728": { "found_in_master": false, "name_zh": null, "name_en": null },
  "0762": { "found_in_master": false, "name_zh": null, "name_en": null }
}
```

### UI Render Keys

```json
{
  "competitive_landscape": {
    "peer_names": [
      { "ticker": "0728", "company_name": "0728.HK" },
      { "ticker": "0762", "company_name": "0762.HK" }
    ],
    "subject_company_name": "0941.HK"
  }
}
```

### 診斷

**根本原因**：`hk_stock_master_data.json` 中所有 ticker 均查不到（`found=False`）。`competitive_landscape_engine._load_master_data()` 返回空 dict 或格式不匹配，導致 `company_name` fallback 為 `f"{ticker}.HK"`。

**兩個可能原因**（需進一步確認）：
1. `hk_stock_master_data.json` 的 key 格式與 `_normalize_ticker()` 不匹配（例如 JSON 用 `"0941.HK"` 但查詢用 `"0941"`）
2. `hk_stock_master_data.json` 確實不包含這些 ticker 的 `name_zh`/`name_en` 欄位

### 預期 vs 實際

| Peer Ticker | 預期顯示 | 實際顯示 |
|------------|---------|---------|
| 0728 | 中國聯通 (China Unicom) | `0728.HK` ❌ |
| 0762 | 中國電信 (China Telecom) | `0762.HK` ❌ |

---

## BUG 3：AI 投資委員會 — 「觀點待整合」0%

### Engine Output（實際 payload）

**agent_opinions** 引擎輸出（0941 示例）：
```json
{
  "opinions": [
    { "agent_name": "市場分析 Agent", "stance": "看好", "confidence": 65 },
    { "agent_name": "財務分析 Agent", "stance": "看好", "confidence": 72 },
    { "agent_name": "風險分析 Agent", "stance": "可接受", "confidence": 58 }
  ],
  "committee_verdict": "審慎樂觀",
  "overall_confidence": 65,
  "bull_score": 68,
  "bear_score": 42,
  "agent_count": 6
}
```

**agent_opinions 引擎本身輸出正確** ✅

### UI Render Keys（問題所在）

```json
{
  "fos_render_multi_agent_committee": {
    "ic_key_in_report_package": "investment_committee",
    "ic_agents_subkey": "agents",
    "ic_agents_value": null,
    "NOTE": "render_multi_agent_committee reads ic['agents'][agent_key] — if 'agents' subkey missing, all show '觀點待整合'",
    "agents_key_present": false,
    "ic_keys_present": ["bull_score", "bear_score"]
  }
}
```

### 診斷

**根本原因**：`fos_components.render_multi_agent_committee()` 讀取 `report_package["investment_committee"]["agents"]`，但 `investment_committee` dict 只有 `bull_score` 和 `bear_score`，**沒有 `agents` subkey**。

`agent_opinion_engine.build_agent_opinions()` 的輸出存放在 `report_package` 的哪個 key？這是 wiring 斷裂問題：

```
agent_opinion_engine.build_agent_opinions(package)
    → 返回 { "opinions": [...], "committee_verdict": "...", ... }
    
fos_components.render_multi_agent_committee(report_package)
    → 讀取 report_package["investment_committee"]["agents"]
    
❌ 兩者 key 路徑不匹配
```

**app.py 的 wiring 問題**：`build_agent_opinions()` 的輸出沒有被正確寫入 `report_package["investment_committee"]["agents"]`，或者 `fos_components` 讀取的 key 路徑與引擎輸出格式不一致。

### 預期 vs 實際

| 項目 | 預期 | 實際 Engine Output | 實際 UI 顯示 |
|-----|------|-------------------|------------|
| agent opinions | 6個 agent 各有立場 | ✅ 正確生成 | 「觀點待整合」❌ |
| overall_confidence | 65% | ✅ 65% | 0% ❌ |
| committee_verdict | 「審慎樂觀」 | ✅ 正確 | 空白 ❌ |

---

## 12345 Payload 完整摘要

| 引擎 | 關鍵輸出 | 狀態 |
|-----|---------|------|
| source_registry | verified_sources=[], coverage=0%, confidence=INVALID | ✅ 引擎正確 |
| source_transparency | coverage=0%, confidence=LOW, sources_present=[] | ⚠️ confidence 應為 INVALID |
| competitive_landscape | peers=[0700,0005,0941]，全部 company_name=raw ticker | ❌ master data 空白 |
| agent_opinions | 6 agents，全部 confidence=30%（fallback），stance 非空 | ⚠️ fallback 值不應顯示為正常 |
| fos_render_committee | ic["agents"]=null | ❌ wiring 斷裂 |

---

## 0941 Payload 完整摘要

| 引擎 | 關鍵輸出 | 狀態 |
|-----|---------|------|
| source_registry | verified_sources=[Yahoo Finance, Company Metadata, Financial Statement, News], coverage=100% | ✅ 引擎正確 |
| source_transparency | coverage=100%, confidence=HIGH | ✅ 正確 |
| competitive_landscape | peers=[0728,0762]，company_name=raw ticker | ❌ master data 空白 |
| agent_opinions | 6 agents，有實際 stance 和 confidence | ✅ 引擎正確 |
| fos_render_committee | ic["agents"]=null | ❌ wiring 斷裂，UI 顯示「觀點待整合」 |

---

## 3416 Payload 完整摘要

| 引擎 | 關鍵輸出 | 狀態 |
|-----|---------|------|
| source_registry | verified_sources=[Yahoo Finance, Company Metadata, Financial Statement], coverage=75% | ✅ 引擎正確 |
| source_transparency | coverage=75%, confidence=MEDIUM | ✅ 正確 |
| competitive_landscape | peers=[0700,0005,0941]，全部 company_name=raw ticker | ❌ master data 空白 |
| agent_opinions | 6 agents，有實際 stance | ✅ 引擎正確 |
| fos_render_committee | ic["agents"]=null | ❌ wiring 斷裂 |

---

## 根本原因總結

### BUG-A：hk_stock_master_data.json key 格式不匹配

**文件**：`data/hk_stock_master_data.json`  
**問題**：`_load_master_data()` 查詢 key `"0941"` 但 JSON 可能用 `"0941.HK"` 或其他格式，導致所有 ticker 均 `found=False`  
**影響**：所有 peer company_name 顯示為 raw ticker（`0728.HK`, `0762.HK` 等）  
**修復方向**：檢查 JSON key 格式，修正 `_normalize_ticker()` 或 JSON key

### BUG-B：fos_components 讀取 ic["agents"] 但 wiring 未填充

**文件**：`app.py` + `core/fos_components.py`  
**問題**：`build_agent_opinions()` 輸出未被寫入 `report_package["investment_committee"]["agents"]`  
**影響**：所有 ticker 的 AI 投資委員會顯示「觀點待整合」0%  
**修復方向**：在 app.py 中將 `agent_opinions` 結果 map 到 `investment_committee["agents"]` 格式

### BUG-C：12345 invalid ticker 的 app.py fallback 污染 source_registry

**文件**：`app.py` + `core/source_registry.py`  
**問題**：app.py 對 invalid ticker 填充了 fallback 數據，`source_registry` 誤判為 verified  
**影響**：12345 顯示 65% coverage 和綠勾  
**修復方向**：在 source_registry 加入 ticker validity check，或在 app.py 對 invalid ticker 直接返回空 package

---

## 修復優先級

| 優先級 | Bug | 修復文件 | 預計影響 |
|-------|-----|---------|---------|
| P0 | BUG-B: ic["agents"] wiring 斷裂 | app.py, fos_components.py | 所有 ticker 的 AI 委員會面板 |
| P0 | BUG-A: master data key 不匹配 | data/hk_stock_master_data.json, competitive_landscape_engine.py | 所有 ticker 的 peer 名稱 |
| P1 | BUG-C: invalid ticker fallback 污染 | app.py, source_registry.py | 12345 等無效 ticker 的 coverage 顯示 |

---

## 結論

**v4.0.3 audit report 與 browser QA 矛盾的原因已確認**：

1. 審計腳本測試的是引擎函數的輸出（正確），但 browser QA 測試的是 app.py 完整流程（有 wiring 問題）
2. 三個 bug 均為 **wiring/data 問題**，不是引擎邏輯問題
3. 引擎本身（source_registry, agent_opinion_engine）輸出正確，但 app.py 的組裝和 fos_components 的讀取路徑存在斷裂

**不應 merge，需先修復 BUG-A 和 BUG-B。**

---

*Audit generated by: scripts/run_payload_audit.py*  
*Evidence files: debug_audit/12345_payload_audit.json, 0941_payload_audit.json, 3416_payload_audit.json*
