# Buildway AI Financial Intelligence Platform

香港股票智能分析試用平台，使用 Python 計算、市場資料分級、Multi-Agent 流程及繁體中文 PDF 輸出，協助客戶快速生成可閱讀的研究摘要。

目前版本：`v1.7.0`

階段：`Product Readiness Sprint`

## 快速開始

```bash
pip install -r requirements.txt
streamlit run app.py
```

目標 Python 版本為 `3.11`。部署環境請使用 `runtime.txt` 內的 `python-3.11`，不要改用 Python 3.14。

## Streamlit 部署

1. 將程式碼推送到 GitHub。
2. 到 Streamlit Community Cloud 建立新 app。
3. Repository 選擇本專案。
4. Main file path 設定為 `app.py`。
5. Python 版本使用 `runtime.txt` 的 `python-3.11`。
6. 部署後在 app 內測試 `0700`、`9988`、`0688`、`0941`、`3416`、`12345`。

`streamlit_app.py` 只作兼容入口，正式 UI 以 `app.py` 為準。

## Secrets 設定

目前系統可在沒有即時新聞 API 的情況下安全運行，不會生成假新聞或未驗證公告。

Streamlit secrets 可設定：

```toml
FINANCIAL_API_KEY = "your_financial_api_key"
NEWS_API_PROVIDER = "none"
NEWS_API_KEY = "your_news_api_key"
NEWS_API_BASE_URL = ""
DEEPSEEK_API_KEY = "your_deepseek_api_key"
```

預設：

```env
NEWS_API_PROVIDER=none
```

## PDF 字型

PDF 使用 ReportLab 生成，繁體中文需要 CJK 字型。

字型搜尋順序：

1. `assets/fonts/NotoSansTC-Regular.ttf`
2. `assets/fonts/NotoSansTC-Bold.ttf`
3. Windows 系統字型，例如 Microsoft JhengHei
4. 其他可用 CJK fallback

部署到 Streamlit Cloud 時，建議將 Noto Sans TC 字型放入 `assets/fonts/`，避免 PDF 中文出現方格或亂碼。

## 資料品質規則

系統會按資料可信度控制顯示深度：

| 狀態 | 顯示策略 |
|---|---|
| 高可信度 | 顯示完整市場快照、財務、情景、風險及 PDF |
| 部分資料缺失 | 隱藏不可靠章節，只保留可驗證資料 |
| 資料驗證未完成 | 停止深度分析，不生成公司敘述或未驗證內容 |

所有財務數值只由 Python 計算。DeepSeek 只可用於文字整理，不參與數值計算。

## Beta 測試清單

每次部署前請完成：

- [ ] `python -m compileall app.py core agents`
- [ ] `python test_v041_data_confidence.py`
- [ ] `python test_font_setup.py`
- [ ] `python quick_regression_test.py`
- [ ] Streamlit AppTest 無 crash
- [ ] 無 `DuplicateElementKey`
- [ ] 無 raw HTML 顯示
- [ ] PDF 中文正常
- [ ] `12345` 不生成公司敘述
- [ ] 手機及桌面版主要區塊不爆位
- [ ] 不重新引入 sidebar UI

## 主要檔案

```text
app.py                         Streamlit 主程式
core/config.py                 版本與設定
core/report_builder.py         報告資料結構
core/pdf_generator.py          PDF 生成
core/client_profile.py         session-only 客戶狀態
core/hkex_parser.py            HKEX 佔位資料邊界
agents/                        Multi-Agent 分析模組
data/hk_stock_master_data.json 港股本地 fallback metadata
quick_regression_test.py       快速回歸測試
```

## 免責聲明

本系統為 Beta 試用版本，只作教育、研究及客戶展示用途，不構成投資建議、招攬或任何買賣建議。市場資料可能延遲、缺失或只作示範用途；使用者應自行核實資料並諮詢持牌專業人士。
