"""
agents/news_intelligence_agent.py

Buildway Tech (HK) Limited - News Intelligence Agent.

The agent consumes verified news only. It does not fabricate headlines,
announcements, catalysts, or market events.
"""

from __future__ import annotations

from typing import Any

from core.news_intelligence import NewsIntelligenceEngine, not_connected_result


class NewsIntelligenceAgent:
    """Aggregate verified news and derive sentiment/catalyst buckets."""

    AGENT_NAME = "新聞情報代理"
    AGENT_ROLE = "分析已驗證新聞、事件催化與需要監察的風險訊號"

    def __init__(self) -> None:
        self.engine = NewsIntelligenceEngine()

    def analyze(
        self,
        ticker: str,
        company_name: str | None = None,
        manual_news: list[dict[str, Any]] | None = None,
        analysis_context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        stock_code = (analysis_context or {}).get("stock_code") or ticker
        sector = (analysis_context or {}).get("sector")
        print(f"[News Intelligence Agent] Received stock_code = {stock_code}")

        if manual_news:
            return self._process_manual_news(stock_code, company_name, sector, manual_news)

        result = self.engine.fetch(stock_code, company_name, sector)
        result["ticker"] = stock_code
        return result

    def _process_manual_news(
        self,
        ticker: str,
        company_name: str | None,
        sector: str | None,
        manual_news: list[dict[str, Any]],
    ) -> dict[str, Any]:
        # Manual news is treated as user-supplied verified input for internal testing.
        items = []
        for item in manual_news:
            title = str(item.get("title") or "").strip()
            if not title:
                continue
            items.append({
                "title": title,
                "publisher": str(item.get("publisher") or "手動輸入").strip(),
                "link": str(item.get("link") or "").strip(),
                "published_at": item.get("date") or item.get("published_at") or "",
                "sentiment": str(item.get("sentiment") or "中性").strip(),
            })

        if not items:
            return not_connected_result(ticker, company_name, sector)

        positive, negative, neutral, risk_events = [], [], [], []
        for item in items:
            sentiment = item.get("sentiment", "中性")
            title = item["title"]
            if "正" in sentiment or "positive" in sentiment.lower():
                positive.append(title)
            elif "負" in sentiment or "negative" in sentiment.lower():
                negative.append(title)
                risk_events.append(title)
            else:
                neutral.append(title)

        total = len(items)
        score = (len(positive) + 0.5 * len(neutral)) / total if total else 0.5
        return {
            "ticker": ticker,
            "company_name": company_name or "",
            "sector": sector or "",
            "status": "手動輸入",
            "summary": f"已接收 {total} 則手動新聞資料。",
            "warning": "",
            "news_items": items,
            "source": "manual",
            "is_live_news": False,
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
            "news_confidence": "中",
            "news_summary": "新聞分析基於手動輸入資料，不會補寫不存在的標題。",
            "monitor_items": risk_events or neutral[:3],
            "market_signals": [],
            "sentiment_analysis": {
                "score": round(score, 2),
                "label": "偏正面" if score >= 0.65 else "偏負面" if score <= 0.35 else "中性",
                "confidence": "中",
                "positive_count": len(positive),
                "negative_count": len(negative),
                "neutral_count": len(neutral),
            },
        }

    def get_dev_placeholder_note(self) -> str:
        return "未接入即時新聞資料前，系統不會生成假新聞或未經驗證事件。"
