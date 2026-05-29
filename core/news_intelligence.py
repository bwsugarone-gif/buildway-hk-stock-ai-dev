"""
core/news_intelligence.py

Compatibility wrapper for the v2.3 verified news aggregation engine.
"""

from __future__ import annotations

from typing import Any

from core.news_aggregation_engine import NO_VERIFIED_NEWS, NewsAggregationEngine


NEWS_NOT_CONNECTED = NO_VERIFIED_NEWS
NEWS_BOUNDARY = NO_VERIFIED_NEWS
NEWS_PDF_BOUNDARY = NO_VERIFIED_NEWS


def empty_catalyst_structure() -> dict[str, Any]:
    return {
        "positive_catalysts": [],
        "negative_catalysts": [],
        "neutral_events": [],
        "risk_events": [],
        "news_confidence": "NONE",
    }


def not_connected_result(ticker: str, company_name: str | None = None, sector: str | None = None) -> dict[str, Any]:
    return NewsAggregationEngine().no_news_result(ticker, company_name, sector)


class NewsIntelligenceEngine:
    """Fetch verified RSS/news items and derive catalyst buckets."""

    def __init__(self) -> None:
        self.engine = NewsAggregationEngine()

    def fetch(
        self,
        ticker: str,
        company_name: str | None = None,
        sector: str | None = None,
    ) -> dict[str, Any]:
        return self.engine.fetch(ticker, company_name, sector)
