# Buildway Tech (HK) Limited
## 香港股票智能分析系統 — v0.6.3 Session State + Cloud Runtime Fix Layer

Multi-Agent Stock Analysis & Risk Report System for Hong Kong equities.

---

## Overview

This is **v0.6.3 Session State + Cloud Runtime Fix Layer** of the Buildway Tech HK stock intelligence platform. It uses a multi-agent architecture to analyze Hong Kong-listed stocks and generate professional PDF risk reports in Traditional Chinese.

**Current Version:** v0.6.3 — Session State + Cloud Runtime Fix Layer  
**Previous Phase:** v0.6.2 — Sector Showcase Landing Layer  
**LLM Provider:** DeepSeek only (Claude not activated)

---

## Features

- 🤖 **8-Agent Team**: CEO, Market Data, Financial Analyst, Risk Management, News Intelligence, HK IPO, Portfolio Manager, Investment Committee
- 📊 **Comprehensive Analysis**: Market data, financial health, risk scoring, valuation range
- 📄 **PDF Report Generation**: Professional branded reports with Traditional Chinese
- 🏢 **HK-Focused**: Designed for Hong Kong Stock Exchange (HKEX) listed companies
- 🔒 **No API Keys Required**: DEV version uses demo data with clear labeling

---

## Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/your-org/buildway-hk-stock-ai.git
cd buildway-hk-stock-ai
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the app

```bash
streamlit run app.py
```

---

## Project Structure

```
buildway-hk-stock-ai/
│
├── app.py                          # Canonical Streamlit application
├── streamlit_app.py                # Compatibility shim that imports app.py
├── requirements.txt                # Python dependencies
├── README.md                       # This file
├── .gitignore                      # Git ignore rules
├── .env.example                    # Environment variables template
│
├── assets/
│   └── logo.png                    # Company logo
│
├── agents/                         # Multi-agent team modules
│   ├── __init__.py
│   ├── ceo_agent.py                # Coordinator agent
│   ├── market_data_agent.py        # Market data fetcher
│   ├── financial_analyst_agent.py  # Financial analysis
│   ├── risk_management_agent.py    # Risk scoring
│   ├── news_intelligence_agent.py  # News & sentiment
│   ├── hk_ipo_agent.py             # IPO module (Phase 2.5)
│   ├── portfolio_manager_agent.py  # Position sizing
│   └── investment_committee_agent.py # Final verdict
│
├── core/                           # Core system modules
│   ├── __init__.py
│   ├── config.py                   # App configuration
│   ├── report_builder.py           # Report structure builder
│   ├── pdf_generator.py            # PDF generation engine
│   └── utils.py                    # Utility functions
│
├── data/
│   ├── hk_stock_master_data.json   # HK stock metadata fallback database
│   └── sample_data.py              # Demo data for DEV version
│
└── reports/                        # Generated PDF reports (gitignored)
```

---

## Streamlit Cloud Deployment

### 1. Push to GitHub

```bash
git add .
git commit -m "Initial DEV deployment"
git push origin main
```

### 2. Deploy on Streamlit Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Connect your GitHub repository
3. Set main file: `app.py`
4. Deploy

`app.py` is the canonical deployment entry file. `streamlit_app.py` is only a
compatibility shim for older Streamlit Cloud settings and must not contain a
separate UI implementation.

Streamlit Cloud must use Python 3.11. The repository includes `runtime.txt`
with `python-3.11`; do not deploy this app on Python 3.14.

### 3. Chinese Font Setup (Required for PDF)

PDF Traditional Chinese rendering requires a CJK-compatible font.
The system checks for fonts in this priority order:

1. **Bundled fonts** (cross-platform, works on Streamlit Cloud):
   ```
   assets/fonts/NotoSansTC-Regular.ttf
   assets/fonts/NotoSansTC-Bold.ttf
   ```
2. **Windows system fonts** (local dev only, auto-detected):
   - `C:/Windows/Fonts/msjh.ttc` (Microsoft JhengHei)
   - `C:/Windows/Fonts/msjhbd.ttc` (Microsoft JhengHei Bold)

**For Streamlit Cloud deployment**, you must upload the Noto Sans TC font files to `assets/fonts/`. Windows system fonts are not available in cloud environments and Chinese text will appear as black boxes without a bundled font.

Download Noto Sans TC from Google Fonts:
https://fonts.google.com/noto/specimen/Noto+Sans+TC

Place these two files in `assets/fonts/`:
- `NotoSansTC-Regular.ttf`
- `NotoSansTC-Bold.ttf`

> Note: Font files are excluded from git by default. Add them to your repository or upload them separately to your deployment environment.

### 4. Secrets (optional for DEV)

In Streamlit Cloud, add secrets under **Settings → Secrets**:

```toml
FINANCIAL_API_KEY = "your_key_here"
NEWS_API_KEY = "your_key_here"
```

---

## Agent Architecture

| Agent | Role | DEV Status |
|-------|------|------------|
| CEO Agent | Coordinator, orchestrates all agents | ✅ Active |
| Market Data Agent | Stock price, volume, market cap | ✅ Demo data |
| Financial Analyst Agent | DCF, comparables, valuation range | ✅ Demo data |
| Risk Management Agent | Risk scoring 1-10 across 7 dimensions | ✅ Active |
| News Intelligence Agent | Sentiment analysis, news factors | ✅ Placeholder |
| HK IPO Agent | IPO analysis module | 🔒 Phase 2.5 |
| Portfolio Manager Agent | Position sizing suggestions | ✅ Active |
| Investment Committee Agent | Final verdict and thesis | ✅ Active |

---

## Risk Disclaimer

> **重要免責聲明 / Important Disclaimer**
>
> 本系統生成的所有報告僅供教育及參考用途，不構成任何投資建議、招攬或要約。
> 投資涉及風險，過往表現不代表未來回報。在作出任何投資決定前，請諮詢持牌財務顧問。
>
> All reports generated by this system are for educational and reference purposes only and do not constitute investment advice, solicitation, or offer. Investments involve risks and past performance does not guarantee future results. Please consult a licensed financial advisor before making any investment decisions.

---

## Technology Stack

- **Python 3.11.9**
- **Streamlit 1.35.0** — Web interface
- **ReportLab 4.2.2** — PDF generation
- **yfinance 0.2.40** — Market data (Phase 2.5+)
- **pandas / numpy** — Data processing

---

## v0.6.3 Deployment Checklist

Use this checklist after every code change to ensure cross-platform consistency.

### After every fix

- [ ] **1. Local test** — Run `streamlit run app.py`, test with: `0700`, `9988`, `0688`, `3416`, `12345`
- [ ] **2. Verify PDF** — Download PDF, open on desktop, confirm Chinese text is not garbled (no □ boxes)
- [ ] **3. Check logs** — Console must show `[APP]`, `[CEO Agent]`, `[Financial Agent]`, `[Risk]`, `[PDF]` stock_code lines
- [ ] **4. Verify version** — App must show `v0.6.3 — Session State + Cloud Runtime Fix Layer` and today's date
- [ ] **5. Git commit** — `git add . && git commit -m "..."` with a clear message
- [ ] **6. Git push** — `git push origin main`
- [ ] **7. Streamlit Cloud** — Go to share.streamlit.io → your app → **Reboot app** (or Rerun)
- [ ] **8. Desktop browser test** — Open app URL in Chrome/Edge on desktop, generate report, download PDF
- [ ] **9. Mobile browser test** — Open same URL on mobile browser (iOS Safari or Android Chrome), generate report, download PDF
- [ ] **10. PDF Chinese check (mobile)** — Open downloaded PDF on mobile, confirm Traditional Chinese renders correctly

### Stock code normalization expected outputs

| Input | Expected normalized | Notes |
|-------|-------------------|-------|
| `3416` | `3416.HK` | No leading zero — correct |
| `3416.HK` | `3416.HK` | Already normalized |
| `03416` | `3416.HK` | 5-digit with leading 0 → strip |
| `700` | `0700.HK` | Pad to 4 digits |
| `0005` | `0005.HK` | Keep leading zero |
| `9988` | `9988.HK` | Normal 4-digit |
| `12345` | `12345.HK` | Invalid but no crash — blocks advanced analysis |

### Agent status values (v0.6.3)

| Status | Meaning |
|--------|---------|
| 等待 | Not yet started |
| 執行中 | Running |
| 完成 | Successfully completed |
| 備援 | Failed but fallback data used — report continues |
| 失敗 | No fallback available (should never occur in normal flow) |

### PDF Chinese font priority (v0.6.3)

1. `assets/fonts/NotoSansTC-Regular.ttf` — bundled (cross-platform, Streamlit Cloud safe)
2. Auto-download from GitHub if bundled font missing (first run on cloud)
3. Windows system fonts (`C:\Windows\Fonts\msjh.ttc`) — local dev fallback
4. Helvetica — last resort (Chinese shows as □ — should never reach this)

---

## Version History

| Version | Date | Notes |
|---------|------|-------|
| v0.6.3 | 2026-05-28 | Session State + Cloud Runtime Fix Layer — safe pending ticker selection, Streamlit Cloud Python 3.11 runtime |
| v0.6.2 | 2026-05-28 | Sector Showcase Landing Layer — sector tabs, stock cards, enriched HK stock master data |
| v0.6.1 | 2026-05-28 | Mobile UX Entry Fix Layer — collapsed sidebar, main-page input panel, mobile hero/CTA layout fixes |
| v0.6.0 | 2026-05-28 | Client Conversion + SaaS Experience Layer — SaaS landing page, demo snapshots, workflow timeline, trust and source transparency layers |
| v0.5.1 | 2026-05-28 | PDF Layout + Symbol Fix Layer — plain-text PDF confidence labels, company analysis moved before executive summary |
| v0.5.0 | 2026-05-28 | Real Company Intelligence Layer — HK stock master metadata fallback, company profile UI, PDF company summary |
| v0.4.4 | 2026-05-28 | Client Trial QA + Production Guard Layer — agent error boundary, LLM timeout fallback, PDF protection, input validation |
| v0.3.0 | 2026-05-27 | Production Stability Layer — font auto-download, agent failsafe, stock code consistency |
| DEV v0.2 | 2026-05 | Phase 2.0 DEV client trial release |

---

© 2026 Buildway Tech (HK) Limited. All rights reserved.
 
---

## LLM Provider Roadmap

Phase 2.0 runtime uses **DeepSeek only** for optional narrative generation. All valuation, ratios, risk scoring, scenario analysis, and data processing remain Python-calculated.

Claude and OpenAI-compatible multi-model review are kept as future roadmap options only and are not called in the current Streamlit report flow.
