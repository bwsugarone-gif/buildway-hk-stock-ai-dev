"""
core/client_profile.py

Real SaaS Client Layer — v1.5

Session-based client profile, usage tracking, and report persistence placeholder.
No real database connected — all state is session-local.
Architecture is designed for future DB integration without breaking changes.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any


# ─── Default Profile ──────────────────────────────────────────────────────────

DEFAULT_PROFILE: dict[str, Any] = {
    "client_id": "guest",
    "display_name": "訪客用戶",
    "investment_style": "中等",          # 保守 / 中等 / 進取
    "preferred_sectors": [],
    "preferred_currency": "HKD",
    "report_language": "zh-HK",
    "created_at": "",
    "last_active": "",
    "usage": {
        "reports_generated": 0,
        "tickers_analyzed": [],
        "total_tokens_used": 0,
        "session_count": 0,
    },
    "preferences": {
        "show_market_snapshot": True,
        "show_scenario_analysis": True,
        "show_hkex_section": True,
        "show_compare_mode": True,
        "default_portfolio_size": 0,
    },
}


def create_guest_profile() -> dict[str, Any]:
    """Create a fresh guest profile for a new session."""
    profile = dict(DEFAULT_PROFILE)
    profile["created_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")
    profile["last_active"] = profile["created_at"]
    profile["usage"] = dict(DEFAULT_PROFILE["usage"])
    profile["usage"]["tickers_analyzed"] = []
    profile["preferences"] = dict(DEFAULT_PROFILE["preferences"])
    return profile


def update_profile_activity(
    profile: dict[str, Any],
    ticker: str | None = None,
    tokens_used: int = 0,
) -> dict[str, Any]:
    """
    Update profile usage stats after an analysis.
    Session-local only — no DB write.
    """
    profile = dict(profile)
    usage = dict(profile.get("usage", {}))

    profile["last_active"] = datetime.now().strftime("%Y-%m-%d %H:%M")

    if ticker:
        analyzed = list(usage.get("tickers_analyzed", []))
        if ticker not in analyzed:
            analyzed.insert(0, ticker)
        usage["tickers_analyzed"] = analyzed[:20]  # Keep last 20
        usage["reports_generated"] = usage.get("reports_generated", 0) + 1

    if tokens_used > 0:
        usage["total_tokens_used"] = usage.get("total_tokens_used", 0) + tokens_used

    profile["usage"] = usage
    return profile


def get_usage_summary(profile: dict[str, Any]) -> dict[str, Any]:
    """Return a display-ready usage summary."""
    usage = profile.get("usage", {})
    return {
        "reports_generated": usage.get("reports_generated", 0),
        "tickers_analyzed_count": len(usage.get("tickers_analyzed", [])),
        "recent_tickers": usage.get("tickers_analyzed", [])[:5],
        "total_tokens_used": usage.get("total_tokens_used", 0),
        "last_active": profile.get("last_active", "未記錄"),
    }


def update_preferences(
    profile: dict[str, Any],
    **kwargs: Any,
) -> dict[str, Any]:
    """
    Update profile preferences.
    Accepted keys: show_market_snapshot, show_scenario_analysis,
    show_hkex_section, show_compare_mode, default_portfolio_size,
    investment_style, preferred_sectors.
    """
    profile = dict(profile)
    prefs = dict(profile.get("preferences", {}))

    pref_keys = {
        "show_market_snapshot", "show_scenario_analysis",
        "show_hkex_section", "show_compare_mode", "default_portfolio_size",
    }
    for key, value in kwargs.items():
        if key in pref_keys:
            prefs[key] = value
        elif key == "investment_style" and value in ("保守", "中等", "進取"):
            profile["investment_style"] = value
        elif key == "preferred_sectors" and isinstance(value, list):
            profile["preferred_sectors"] = value[:10]

    profile["preferences"] = prefs
    return profile


def build_sharable_link_placeholder(
    ticker: str,
    report_id: str,
) -> str:
    """
    Placeholder for sharable report link generation.
    Returns a placeholder URL — real implementation requires a backend.
    """
    safe_ticker = ticker.replace(".", "_").replace("/", "_")
    return f"https://app.buildway.ai/reports/{safe_ticker}/{report_id}"


def build_email_delivery_placeholder(
    recipient_email: str,
    ticker: str,
    report_id: str,
) -> dict[str, Any]:
    """
    Placeholder for email delivery.
    Returns a structured payload — real implementation requires an email service.
    """
    return {
        "status": "placeholder",
        "recipient": recipient_email,
        "subject": f"Buildway AI 分析報告 — {ticker}",
        "report_id": report_id,
        "note": "電郵發送功能將於後續版本啟用，目前為架構佔位符。",
    }
