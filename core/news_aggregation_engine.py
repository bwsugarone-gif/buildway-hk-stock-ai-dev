"""
core/news_aggregation_engine.py

v2.3 News Intelligence Layer.

Fetches verified RSS items only. If no feed can be reached or no matching item
is found, it returns an explicit no-news result and never fabricates content.
"""

from __future__ import annotations

import email.utils
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from typing import Any


NO_VERIFIED_NEWS = "未取得已驗證新聞資料"


class NewsAggregationEngine:
    SOURCES = (
        ("Yahoo Finance RSS", "https://feeds.finance.yahoo.com/rss/2.0/headline?s={ticker}&region=US&lang=en-US"),
        ("Google Finance RSS", "https://news.google.com/rss/search?q={query}"),
        ("Investing RSS", "https://www.investing.com/rss/news_25.rss"),
    )

    def fetch(self, ticker: str, company_name: str | None = None, sector: str | None = None) -> dict[str, Any]:
        query = self._query(ticker, company_name)
        all_items: list[dict[str, Any]] = []
        for source, template in self.SOURCES:
            url = template.format(ticker=urllib.parse.quote(ticker), query=urllib.parse.quote(query))
            all_items.extend(self._fetch_source(source, url, ticker, company_name))

        deduped = self._dedupe(all_items)
        if not deduped:
            return self.no_news_result(ticker, company_name, sector)
        return self._analyze(ticker, company_name, sector, deduped[:10])

    def no_news_result(self, ticker: str, company_name: str | None = None, sector: str | None = None) -> dict[str, Any]:
        return {
            "ticker": ticker,
            "company_name": company_name or "",
            "sector": sector or "",
            "status": NO_VERIFIED_NEWS,
            "summary": NO_VERIFIED_NEWS,
            "warning": NO_VERIFIED_NEWS,
            "news_items": [],
            "recent_news": [],
            "source": "none",
            "is_live_news": False,
            "has_news": False,
            "headlines": [],
            "recent_headlines": [],
            "positive_factors": [],
            "negative_factors": [],
            "neutral_signals": [],
            "positive_catalysts": [],
            "negative_catalysts": [],
            "neutral_events": [],
            "risk_events": [],
            "market_focus": [],
            "monitor_items": [],
            "news_confidence": "NONE",
            "news_credibility": "NONE",
            "news_summary": NO_VERIFIED_NEWS,
            "market_signals": [],
            "sentiment_analysis": {
                "score": 0.5,
                "label": "NONE",
                "confidence": "NONE",
                "positive_count": 0,
                "negative_count": 0,
                "neutral_count": 0,
            },
        }

    def _fetch_source(self, source: str, url: str, ticker: str, company_name: str | None) -> list[dict[str, Any]]:
        try:
            request = urllib.request.Request(url, headers={"User-Agent": "BuildwayHKStockAI/2.4"})
            with urllib.request.urlopen(request, timeout=8) as response:
                body = response.read()
        except Exception:
            return []

        try:
            root = ET.fromstring(body)
        except ET.ParseError:
            return []

        items = []
        for node in root.findall(".//item")[:20]:
            title = self._text(node, "title")
            link = self._text(node, "link")
            published = self._text(node, "pubDate")
            if not title or not self._matches(title, ticker, company_name):
                continue
            items.append({
                "title": title,
                "publisher": source,
                "source": source,
                "link": link,
                "published_at": self._date(published),
                "news_date": self._date(published),
            })
        return items

    def _analyze(
        self,
        ticker: str,
        company_name: str | None,
        sector: str | None,
        items: list[dict[str, Any]],
    ) -> dict[str, Any]:
        positive, negative, neutral, focus = [], [], [], []
        for item in items:
            title = item["title"]
            lowered = title.lower()
            if any(word in lowered for word in ("profit", "growth", "buyback", "dividend", "upgrade", "beat", "approval")):
                positive.append(title)
            elif any(word in lowered for word in ("warning", "loss", "downgrade", "probe", "fine", "lawsuit", "miss", "risk")):
                negative.append(title)
            else:
                neutral.append(title)
            focus.append(title)

        total = len(items)
        score = (len(positive) + 0.5 * len(neutral)) / total if total else 0.5
        credibility = "HIGH" if total >= 5 else "MEDIUM"
        return {
            "ticker": ticker,
            "company_name": company_name or "",
            "sector": sector or "",
            "status": f"取得 {total} 則已驗證新聞",
            "summary": f"取得 {total} 則已驗證新聞",
            "warning": "",
            "news_items": items,
            "recent_news": items,
            "source": ", ".join(sorted({item["source"] for item in items})),
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
            "risk_events": negative,
            "market_focus": focus[:5],
            "monitor_items": (negative or neutral)[:5],
            "news_confidence": credibility,
            "news_credibility": credibility,
            "news_summary": f"News sentiment score: {score:.2f}",
            "market_signals": [],
            "sentiment_analysis": {
                "score": round(score, 2),
                "label": "positive" if score >= 0.65 else "negative" if score <= 0.35 else "neutral",
                "confidence": credibility,
                "positive_count": len(positive),
                "negative_count": len(negative),
                "neutral_count": len(neutral),
            },
        }

    def _query(self, ticker: str, company_name: str | None) -> str:
        code = ticker.replace(".HK", "")
        parts = [ticker, code, "Hong Kong stock"]
        if company_name:
            parts.insert(0, company_name)
        return " ".join(parts)

    def _matches(self, title: str, ticker: str, company_name: str | None) -> bool:
        lowered = title.lower()
        code = ticker.replace(".HK", "").lstrip("0")
        if ticker.lower() in lowered or re.search(rf"\b0*{re.escape(code)}\.hk\b", lowered):
            return True
        if company_name:
            name = company_name.lower()
            tokens = [part for part in re.split(r"\W+", name) if len(part) >= 4]
            return any(token in lowered for token in tokens[:3])
        return False

    def _text(self, node: ET.Element, tag: str) -> str:
        found = node.find(tag)
        return (found.text or "").strip() if found is not None else ""

    def _date(self, value: str) -> str:
        if not value:
            return ""
        try:
            parsed = email.utils.parsedate_to_datetime(value)
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            return parsed.astimezone(timezone.utc).date().isoformat()
        except Exception:
            try:
                return datetime.fromisoformat(value).date().isoformat()
            except Exception:
                return value

    def _dedupe(self, items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        seen: set[str] = set()
        result = []
        for item in items:
            key = (item.get("title") or "").strip().lower()
            if not key or key in seen:
                continue
            seen.add(key)
            result.append(item)
        return result

