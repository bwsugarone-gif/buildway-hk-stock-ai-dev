"""
agents/news_intelligence_agent.py
Buildway Tech (HK) Limited — News Intelligence Agent
Role: News sentiment analysis and market signal aggregation
DEV version uses structured placeholder with manual input support
Phase 2.5: Connect to real news APIs (NewsAPI, Bloomberg, HKEX announcements)
"""

from typing import Dict, Any, List, Optional
from data.sample_data import get_sample_news_sentiment


class NewsIntelligenceAgent:
    """
    News Intelligence Agent
    Aggregates news sentiment, identifies positive/negative/neutral signals.
    DEV version uses demo data with structure ready for live API integration.
    """

    AGENT_NAME = "新聞情報代理"
    AGENT_ROLE = "分析市場新聞情緒，識別正面、負面及中性市場信號"

    def analyze(
        self,
        ticker: str,
        company_name: Optional[str] = None,
        manual_news: Optional[List[Dict]] = None,
    ) -> Dict[str, Any]:
        """
        Main entry point. Analyze news sentiment for a ticker.
        manual_news: Optional list of manually entered news items for DEV use.
        """
        # Try live news fetch (Phase 2.5 placeholder)
        live_result = self._try_live_news(ticker, company_name)

        if live_result:
            result = live_result
        else:
            result = get_sample_news_sentiment(ticker)

        # Override with manual news if provided
        if manual_news:
            result = self._process_manual_news(result, manual_news)

        # Add sentiment analysis
        result["sentiment_analysis"] = self._analyze_sentiment(result)
        result["market_signals"] = self._extract_market_signals(result)

        return result

    def _try_live_news(
        self,
        ticker: str,
        company_name: Optional[str],
    ) -> Optional[Dict[str, Any]]:
        """
        Attempt to fetch live news. Returns None if unavailable.
        Phase 2.5: Implement NewsAPI, HKEX announcement feed, Bloomberg.
        """
        # DEV: Live news API not yet connected
        # Future implementation:
        # - NewsAPI.org for general news
        # - HKEX EDIS for company announcements
        # - Bloomberg Terminal API (if available)
        # - Refinitiv Eikon API
        return None

    def _process_manual_news(
        self,
        base_result: Dict[str, Any],
        manual_news: List[Dict],
    ) -> Dict[str, Any]:
        """Process manually entered news items and merge with base result."""
        positive = []
        negative = []
        neutral = []
        headlines = []

        for item in manual_news:
            title = item.get("title", "")
            sentiment = item.get("sentiment", "中性")
            date = item.get("date", "")

            headlines.append({"title": title, "sentiment": sentiment, "date": date})

            if sentiment == "正面":
                positive.append(title)
            elif sentiment == "負面":
                negative.append(title)
            else:
                neutral.append(title)

        # Merge with demo data
        result = dict(base_result)
        if positive:
            result["positive_factors"] = positive + result.get("positive_factors", [])
        if negative:
            result["negative_factors"] = negative + result.get("negative_factors", [])
        if neutral:
            result["neutral_signals"] = neutral + result.get("neutral_signals", [])
        if headlines:
            result["recent_headlines"] = headlines + result.get("recent_headlines", [])

        result["has_manual_input"] = True
        return result

    def _analyze_sentiment(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Compute overall sentiment score and classification."""
        positive_count = len(data.get("positive_factors", []))
        negative_count = len(data.get("negative_factors", []))
        neutral_count = len(data.get("neutral_signals", []))
        total = positive_count + negative_count + neutral_count

        if total == 0:
            return {"score": 0.5, "label": "中性", "confidence": "低"}

        # Weighted score: positive=1, neutral=0.5, negative=0
        score = (positive_count * 1.0 + neutral_count * 0.5) / total

        if score >= 0.65:
            label = "正面"
        elif score >= 0.45:
            label = "中性"
        else:
            label = "負面"

        confidence = "高" if total >= 5 else "中" if total >= 3 else "低"

        return {
            "score": round(score, 2),
            "label": label,
            "confidence": confidence,
            "positive_count": positive_count,
            "negative_count": negative_count,
            "neutral_count": neutral_count,
        }

    def _extract_market_signals(self, data: Dict[str, Any]) -> List[Dict[str, str]]:
        """Extract key market signals from news data."""
        signals = []

        for factor in data.get("positive_factors", []):
            signals.append({"signal": factor, "type": "正面", "icon": "🟢"})

        for factor in data.get("negative_factors", []):
            signals.append({"signal": factor, "type": "負面", "icon": "🔴"})

        for signal in data.get("neutral_signals", []):
            signals.append({"signal": signal, "type": "中性", "icon": "🟡"})

        return signals

    def get_dev_placeholder_note(self) -> str:
        """Return a note about DEV placeholder status."""
        return (
            "【DEV版本】新聞情報模組目前使用示範數據。\n"
            "Phase 2.5 將接入實時新聞API（NewsAPI、港交所公告、彭博資訊）。\n"
            "如需分析特定新聞，可在下方手動輸入新聞標題及情緒分類。"
        )
