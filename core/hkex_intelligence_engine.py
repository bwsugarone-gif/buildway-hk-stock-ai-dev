"""
core/hkex_intelligence_engine.py

v2.4 HKEX Intelligence Layer.

Placeholder architecture for verified HKEX announcement categories. Until a
real API/parser is connected, it returns an explicit no-data result and never
generates announcement content.
"""

from __future__ import annotations

from typing import Any


NO_VERIFIED_HKEX = "未取得已驗證 HKEX 公告資料"

HKEX_CATEGORIES = (
    "業績公告",
    "盈利警告",
    "回購",
    "配股",
    "供股",
    "特別股息",
    "董事變動",
)


class HKEXIntelligenceEngine:
    def fetch(self, ticker: str, **_: Any) -> dict[str, Any]:
        return self.no_data_result(ticker)

    def no_data_result(self, ticker: str) -> dict[str, Any]:
        return {
            "ticker": ticker,
            "title": "HKEX Intelligence",
            "status": NO_VERIFIED_HKEX,
            "status_summary": NO_VERIFIED_HKEX,
            "analysis_boundary": NO_VERIFIED_HKEX,
            "has_data": False,
            "is_placeholder": True,
            "categories": list(HKEX_CATEGORIES),
            "announcements": {
                "is_connected": False,
                "announcements": [],
                "categories": list(HKEX_CATEGORIES),
            },
            "earnings": {
                "has_earnings_data": False,
            },
        }


def build_hkex_intelligence(ticker: str, **kwargs: Any) -> dict[str, Any]:
    return HKEXIntelligenceEngine().fetch(ticker, **kwargs)

