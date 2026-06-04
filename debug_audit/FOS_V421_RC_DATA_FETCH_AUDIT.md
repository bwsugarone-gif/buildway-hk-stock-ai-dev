# FOS v4.2.1 RC Data Fetch Failure Audit

Generated: 2026-06-04T00:35:38

## Executive Summary

Both `0006.HK` and `1810.HK` normalize correctly, exist in `hk_stock_master_data.json`, and are valid yfinance symbols. They are not present in `SAMPLE_HK_STOCKS`. Under normal yfinance/cache access, the existing `MarketDataAgent` returns live Yahoo Finance data and `source_registry` computes `HIGH`. In the restricted probe, yfinance failed with `unable to open database file`, after which the fallback path had no sample price/market cap and finalized as `INVALID`.

## Per Ticker Findings

### 0006.HK

- Normalize: `0006.HK` -> `0006.HK`.
- Master data: contains=`True`, name_zh=`電能實業`, name_en=`Power Assets Holdings`, sector=`公用事業`.
- Sample data: in `SAMPLE_HK_STOCKS`=`False`, usable sample price/cap=`False`.
- yfinance normal access: exception=`None`, price=`56.85`, marketCap=`121153323008`, history_rows=`5`.
- Agent normal access: confidence=`HIGH`, price=`56.85`, market_cap=`121153323008.0`, company=`Power Assets Holdings Limited`, sector=`Utilities`.
- Registry normal access: level=`HIGH`, coverage=`44.0%`, market_data.verified=`True`, company_metadata.verified=`True`, financial_statement.verified=`True`.

### 1810.HK

- Normalize: `1810.HK` -> `1810.HK`.
- Master data: contains=`True`, name_zh=`小米集團`, name_en=`Xiaomi Corporation`, sector=`科技 / 消費電子`.
- Sample data: in `SAMPLE_HK_STOCKS`=`False`, usable sample price/cap=`False`.
- yfinance normal access: exception=`None`, price=`28.58`, marketCap=`737447247872`, history_rows=`5`.
- Agent normal access: confidence=`HIGH`, price=`28.58`, market_cap=`737447247872.0`, company=`Xiaomi Corporation`, sector=`Technology`.
- Registry normal access: level=`HIGH`, coverage=`40.0%`, market_data.verified=`True`, company_metadata.verified=`True`, financial_statement.verified=`True`.

## Root Cause

Primary root cause is environment-dependent yfinance failure, not invalid tickers. When yfinance cannot open its cache/database or cannot reach Yahoo, `0006.HK` and `1810.HK` are outside `SAMPLE_HK_STOCKS`, so the fallback cannot provide price/market cap. `DataCoverageEngine.coverage_score()` then marks the payload `INVALID` because it requires identity plus price or market cap.

## Source Registry Notes

`source_registry.market_data.verified` is based on `current_price` or `price`. If yfinance fails and fallback only has metadata, it becomes `False`. `company_metadata.verified` can become `False` if the registry is built from an `invalid_market_data()` payload, because that payload discards embedded master metadata and leaves company name fields blank. Coverage can display `0%` when UI applies the INVALID guard, even if raw registry field coverage is non-zero.

## Secrets And Keys

- LLM only: `DEEPSEEK_API_KEY` for default `LLM_PROVIDER=deepseek`; `OPENAI_API_KEY` only if `LLM_PROVIDER=openai`; `CLAUDE_API_KEY` only if `LLM_PROVIDER=claude`. Current code search found no active `GEMINI_API_KEY` usage.
- Market data: current `MarketDataAgent` uses yfinance only. It does not read `ALPHA_VANTAGE_KEY`, `FINNHUB_API_KEY`, or `NEWS_API_KEY` for stock price/company market data.
- News: `NEWS_API_KEY` is configured but current news aggregation path uses RSS templates, not the stock price pipeline.
- `USE_LIVE_MARKET_DATA` exists but is not wired into `MarketDataAgent.fetch()`.

## Recommended Fixes

1. Add `0006.HK` and `1810.HK` to the validated sample universe or provide non-fabricated metadata-only handling that does not label a master-data hit as an invalid ticker.
2. Preserve master-data metadata when live market data fails, and distinguish `VALID_TICKER_PRICE_UNAVAILABLE` from `INVALID`.
3. Make yfinance cache location explicit/writable in Streamlit Cloud, or disable problematic yfinance cache behavior if supported by the installed version.
4. Surface yfinance exceptions/timeouts in debug output instead of swallowing them into generic invalid status.
5. Wire `USE_LIVE_MARKET_DATA` intentionally, or remove/rename it so the RC does not imply live mode is controlled when it is not.
6. Keep LLM key failures separate from market data validation; missing LLM keys should degrade narrative generation only, not ticker/company/source validation.
