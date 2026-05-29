"""
core/hkex_parser.py

Backward-compatible entrypoint for the v2.4 HKEX Intelligence Layer.
"""

from __future__ import annotations

from typing import Any

from core.hkex_intelligence_engine import (
    HKEX_CATEGORIES,
    NO_VERIFIED_HKEX,
    HKEXIntelligenceEngine,
    build_hkex_intelligence,
)


NOT_CONNECTED = NO_VERIFIED_HKEX
BOUNDARY_NOTE = NO_VERIFIED_HKEX


def fetch_hkex_announcements(ticker: str, max_items: int = 5) -> dict[str, Any]:
    result = HKEXIntelligenceEngine().no_data_result(ticker)
    announcements = dict(result["announcements"])
    announcements["announcement_count"] = 0
    announcements["latest_announcement"] = NO_VERIFIED_HKEX
    announcements["boundary_note"] = NO_VERIFIED_HKEX
    announcements["not_connected_message"] = NO_VERIFIED_HKEX
    return announcements


def fetch_earnings_summary(ticker: str, financial_data: dict[str, Any] | None = None) -> dict[str, Any]:
    _ = financial_data
    return {
        "ticker": ticker,
        "has_earnings_data": False,
        "status": NO_VERIFIED_HKEX,
        "boundary_note": NO_VERIFIED_HKEX,
        "not_connected_message": NO_VERIFIED_HKEX,
        "categories": list(HKEX_CATEGORIES),
    }

