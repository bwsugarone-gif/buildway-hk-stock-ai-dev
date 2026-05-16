# Buildway Tech (HK) Limited
## 香港股票智能分析系統 — DEV Client Trial Version

Multi-Agent Stock Analysis & Risk Report System for Hong Kong equities.

---

## Overview

This is the **DEV client trial version** of the Buildway Tech HK stock intelligence platform. It uses a multi-agent architecture to analyze Hong Kong-listed stocks and generate professional PDF risk reports in Traditional Chinese.

**Current Phase:** DEV (Demo data, no live API required)  
**Next Phase:** 2.5 — Live market data + news API integration  
**Final Phase:** 3.0 — Full production deployment

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
├── app.py                          # Main Streamlit application
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

## Version History

| Version | Date | Notes |
|---------|------|-------|
| 1.0.0-dev | 2026-05 | Initial DEV client trial release |

---

© 2026 Buildway Tech (HK) Limited. All rights reserved.
 
---

## LLM Provider Roadmap

Phase 2.0 runtime uses **DeepSeek only** for optional narrative generation. All valuation, ratios, risk scoring, scenario analysis, and data processing remain Python-calculated.

Claude and OpenAI-compatible multi-model review are kept as future roadmap options only and are not called in the current Streamlit report flow.
