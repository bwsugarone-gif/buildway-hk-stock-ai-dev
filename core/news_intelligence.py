"""
core/news_intelligence.py

Safe news and catalyst intelligence layer.

This module never fabricates headlines, announcements, or market events. If no
verified news source is connected, it returns an explicit not-connected result.
"""

from __future__ import annotations

from typing import Any

from core.config import NEWS_API_BASE_URL, NEWS_API_KEY, NEWS_API_PROVIDER


NEWS_NOT_CONNECTED = "暫未接入即時新聞資料"
NEWS_BOUNDARY = "暫未接入即時新聞資料，新聞催化分析會於後續版本啟用。"
NEWS_PDF_BOUNDARY = "暫未接入即時新聞資料，本節不生成未經驗證的新聞或事件。"


def empty_catalyst_structure() -> dict[str, Any]:
    return {
        "positive_catalysts": [],
        "negative_catalysts": [],
        "neutral_events": [],
        "risk_events": [],
        "news_confidence": "未接入",
    }


def not_connected_result(ticker: str, company_name: str | None = None, sector: str | None = None) -> dict[str, Any]:
    catalysts = empty_catalyst_structure()
    return {
        "ticker": ticker,
        "company_name": company_name or "",
        "sector": sector or "",
        "status": "未接入",
        "summary": NEWS_NOT_CONNECTED,
        "warning": NEWS_BOUNDARY,
        "news_items": [],
        "source": "none",
        "is_live_news": False,
        "has_news": False,
        "headlines": [],
        "recent_headlines": [],
        "positive_factors": [],
        "negative_factors": [],
        "neutral_signals": [],
        "market_signals": [],
        "sentiment_analysis": {
            "score": 0.5,
            "label": "未接入",
            "confidence": "未接入",
            "positive_count": 0,
            "negative_count": 0,
            "neutral_count": 0,
        },
        "news_summary": NEWS_NOT_CONNECTED,
        "monitor_items": [],
        **catalysts,
    }


class NewsIntelligenceEngine:
    """Fetch verified news and derive catalyst buckets without fabrication."""

    def fetch(
        self,
        ticker: str,
        company_name: str | None = None,
        sector: str | None = None,
    ) -> dict[str, Any]:
        provider = (NEWS_API_PROVIDER or "none").strip().lower()
        if provider != "none" and NEWS_API_KEY:
            api_result = self._fetch_news_api_placeholder(ticker, company_name, sector)
            if api_result.get("has_news"):
                return api_result

        yfinance_result = self._fetch_yfinance_news(ticker, company_name, sector)
        if yfinance_result.get("has_news"):
            return yfinance_result

        return not_connected_result(ticker, company_name, sector)

    def _fetch_news_api_placeholder(
        self,
        ticker: str,
        company_name: str | None,
        sector: str | None,
    ) -> dict[str, Any]:
        # Placeholder for a future verified News API integration. It intentionally
        # returns no headlines until a concrete provider parser is implemented.
        _ = (ticker, company_name, sector, NEWS_API_BASE_URL)
        return not_connected_result(ticker, company_name, sector)

    def _fetch_yfinance_news(
        self,
        ticker: str,
        company_name: str | None,
        sector: str | None,
    ) -> dict[str, Any]:
        try:
            import yfinance as yf

            raw_news = getattr(yf.Ticker(ticker), "news", None) or []
        except Exception:
            return not_connected_result(ticker, company_name, sector)

        items = []
        for item in raw_news[:8]:
            title = str(item.get("title") or "").strip()
            if not title:
                continue
            items.append({
                "title": title,
                "publisher": str(item.get("publisher") or "").strip(),
                "link": str(item.get("link") or "").strip(),
                "published_at": item.get("providerPublishTime") or "",
            })

        if not items:
            return not_connected_result(ticker, company_name, sector)

        return self._analyze_verified_items(ticker, company_name, sector, items, "yfinance")

    def _analyze_verified_items(
        self,
        ticker: str,
        company_name: str | None,
        sector: str | None,
        items: list[dict[str, Any]],
        source: str,
    ) -> dict[str, Any]:
        positive, negative, neutral, risk_events = [], [], [], []
        for item in items:
            title = item["title"]
            lowered = title.lower()
            if any(word in lowered for word in ["upgrade", "beat", "growth", "profit", "approval", "record"]):
                positive.append(title)
            elif any(word in lowered for word in ["downgrade", "miss", "loss", "probe", "fine", "risk", "falls"]):
                negative.append(title)
                risk_events.append(title)
            else:
                neutral.append(title)

        total = len(items)
        score = (len(positive) + 0.5 * len(neutral)) / total if total else 0.5
        if score >= 0.65:
            label = "偏正面"
        elif score <= 0.35:
            label = "偏負面"
        else:
            label = "中性"

        return {
            "ticker": ticker,
            "company_name": company_name or "",
            "sector": sector or "",
            "status": "已接入",
            "summary": f"已取得 {total} 則已驗證新聞來源。",
            "warning": "",
            "news_items": items,
            "source": source,
            "is_live_news": True,
            "has_news": True,
            "headlines": items,
            "recent_headlines": items,
            "positive_factors": positive,
            "negative_factors": negative,
            "neutral_signals": neutral,
            "positive_catalysts": positive,
            "negative_catalysts": negative,
            "neutral_events": neutral,
            "risk_events": risk_events,
            "news_confidence": "中" if total < 5 else "高",
            "news_summary": f"新聞情緒為{label}，分析只基於已取得的新聞標題。",
            "monitor_items": risk_events or neutral[:3],
            "market_signals": [],
            "sentiment_analysis": {
                "score": round(score, 2),
                "label": label,
                "confidence": "中" if total < 5 else "高",
                "positive_count": len(positive),
                "negative_count": len(negative),
                "neutral_count": len(neutral),
            },
        }
