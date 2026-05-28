# Buildway AI — Local Data Lake

本地資料湖，用於儲存每日分析紀錄、市場快照、用戶事件及報告 metadata。

---

## 資料夾結構

```
data_lake/
├── daily/
│   └── YYYY-MM-DD/
│       ├── analysis_runs.jsonl      每次完成分析的紀錄
│       ├── market_snapshots.jsonl   市場快照 KPI
│       ├── user_events.jsonl        用戶操作事件
│       ├── report_metadata.jsonl    報告 metadata
│       └── manual_notes.jsonl       手動備注（骨架）
├── reports/
│   └── YYYY-MM-DD/                  報告相關資料（預留）
├── exports/                         匯出文件
├── backups/                         備份（手動或自動）
└── README.md                        本文件
```

---

## JSONL 格式

每個文件每行一個 JSON object，使用 UTF-8 編碼，`ensure_ascii=False`。

### analysis_runs.jsonl

```json
{
  "created_at": "2026-05-29T10:00:00.000000",
  "ticker": "0700.HK",
  "company_name": "騰訊控股",
  "data_confidence": "HIGH",
  "risk_score": "4.5/10",
  "final_rating": "觀察名單",
  "summary": "高可信度",
  "pdf_generated": true,
  "pdf_filename": "Buildway_HK_Investment_Report_0700_HK_20260529.pdf",
  "session_id": "20260529100000123456",
  "app_version": "v2.1.0"
}
```

INVALID ticker 只儲存最少欄位，不儲存假公司資料：

```json
{
  "created_at": "2026-05-29T10:00:00.000000",
  "ticker": "12345.HK",
  "data_confidence": "INVALID",
  "summary": "資料驗證未完成，系統已停止深度分析。",
  "pdf_generated": false,
  "session_id": "20260529100000123456",
  "app_version": "v2.1.0"
}
```

### market_snapshots.jsonl

```json
{
  "created_at": "2026-05-29T10:00:00.000000",
  "ticker": "0700.HK",
  "snapshot_confidence": "高",
  "is_demo": false,
  "現價": "HK$385.40",
  "市值": "HK$3.71T",
  "市盈率 (P/E)": "18.50x",
  "session_id": "20260529100000123456"
}
```

### user_events.jsonl

```json
{
  "created_at": "2026-05-29T10:00:00.000000",
  "event_type": "generate_report",
  "ticker": "0700.HK",
  "session_id": "20260529100000123456"
}
```

事件類型：`search_ticker` | `generate_report` | `download_pdf` | `add_watchlist` | `rerun_analysis`

---

## 每日備份方法

### 手動下載

在 Streamlit UI 的「資料儲存狀態」區塊，點選「下載今日分析紀錄 JSONL」。

### 命令行備份

```bash
# 備份今日資料到 backups/
cp -r data_lake/daily/$(date +%Y-%m-%d) data_lake/backups/

# 或壓縮整個 data_lake
zip -r data_lake_backup_$(date +%Y%m%d).zip data_lake/daily/
```

---

## Streamlit Cloud 限制

**重要：** Streamlit Cloud 不提供持久化本地儲存。每次 app 重啟（包括 idle timeout 後重啟），`data_lake/` 資料夾會被清空。

**建議：**
- 本地開發：data_lake 正常持久化
- Streamlit Cloud 試用：每次 session 的資料只在該次 session 有效
- 正式生產環境：需接入 Supabase / Neon / PostgreSQL

---

## 未來升級路徑

### 升級到 Supabase

1. 在 `.env` 設定 `DATABASE_URL=postgresql://...`
2. 設定 `LOCAL_DATA_MODE=false`
3. 在 `local_data_store.py` 的 `_append_jsonl()` 加入 Supabase client 寫入邏輯
4. 現有 JSONL 格式可直接 bulk import 到 Supabase table

### 升級到 Qdrant（向量搜尋）

1. 將 `analysis_runs.jsonl` 的 `summary` 欄位向量化
2. 用 Qdrant 建立 ticker 相似度搜尋
3. 現有 JSONL 可作為 Qdrant payload

### 升級到 Neon（PostgreSQL）

1. 設定 `DATABASE_URL=postgresql://...@neon.tech/...`
2. 建立 `analysis_runs`、`market_snapshots`、`user_events` table
3. 現有 JSONL 可用 `COPY` 命令 bulk import

---

## 安全規則

- 不儲存 API key
- 不儲存密碼或 token
- 不儲存完整個人資料（只儲存 session_id，不儲存 IP 或 email）
- INVALID ticker 不儲存假公司資料

---

*Buildway Tech (HK) Limited — v2.1.0 Local Data Moat Foundation Layer*
