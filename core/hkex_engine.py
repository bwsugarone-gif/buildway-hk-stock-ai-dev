"""
core/hkex_engine.py
HKEX Module — v4.0 Hardening Layer

Three-state HKEX module:
  ENABLED_WITH_DATA  — connected and has announcements
  ENABLED_EMPTY      — connected but no recent announcements
  DISABLED           — not connected (current state)

Rules:
- DISABLED: never show "已驗證", never show HKEX Filing as verified source
- ENABLED_EMPTY: show "最近90日未發現重大公告"
- ENABLED_WITH_DATA: show real announcement data
"""

from datetime import datetime

# ── Status Constants ──────────────────────────────────────────────────────────
HKEX_STATUS_ENABLED_WITH_DATA = "ENABLED_WITH_DATA"
HKEX_STATUS_ENABLED_EMPTY     = "ENABLED_EMPTY"
HKEX_STATUS_DISABLED          = "DISABLED"

# Current system state — no real HKEX API connected
_CURRENT_HKEX_STATUS = HKEX_STATUS_DISABLED


def get_hkex_status() -> str:
    """Return current HKEX module status."""
    return _CURRENT_HKEX_STATUS


def build_hkex_module(stock_code: str, report_package: dict = None) -> dict:
    """
    Build HKEX module output for a given stock.

    Returns a dict with status, message, source_verified, and data fields.
    Never returns fake verified data when DISABLED.
    """
    status = get_hkex_status()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")

    if status == HKEX_STATUS_DISABLED:
        return {
            "status": HKEX_STATUS_DISABLED,
            "source_name": "HKEX 披露易",
            "last_checked": now_str,
            "announcements": [],
            "earnings": [],
            "profit_warnings": [],
            "source_verified": False,
            "message": "HKEX 公告模組尚未啟用",
            "detail": "系統尚未接入 HKEX 披露易公告資料源，因此不會生成公告分析。如需查閱最新公告，請直接瀏覽 HKEX 披露易網站。",
            "hkex_url": f"https://www.hkexnews.hk/listedco/listconews/advancedsearch/search_active_main.aspx",
        }

    if status == HKEX_STATUS_ENABLED_EMPTY:
        return {
            "status": HKEX_STATUS_ENABLED_EMPTY,
            "source_name": "HKEX 披露易",
            "last_checked": now_str,
            "announcements": [],
            "earnings": [],
            "profit_warnings": [],
            "source_verified": True,
            "message": "最近90日未發現重大公告",
            "detail": "資料來源：HKEX 披露易。系統已查詢最近90日公告，未發現重大業績、盈利警告或重大交易公告。",
            "hkex_url": f"https://www.hkexnews.hk/listedco/listconews/advancedsearch/search_active_main.aspx",
        }

    # ENABLED_WITH_DATA — would use real data from API/scraper
    # This path is reserved for future HKEX API integration
    announcements = (report_package or {}).get("hkex_announcements", [])
    return {
        "status": HKEX_STATUS_ENABLED_WITH_DATA,
        "source_name": "HKEX 披露易",
        "last_checked": now_str,
        "announcements": announcements,
        "earnings": (report_package or {}).get("hkex_earnings", []),
        "profit_warnings": (report_package or {}).get("hkex_profit_warnings", []),
        "source_verified": True,
        "message": f"已取得 {len(announcements)} 項公告",
        "detail": "資料來源：HKEX 披露易。以下為最新公告摘要。",
        "hkex_url": f"https://www.hkexnews.hk/listedco/listconews/advancedsearch/search_active_main.aspx",
    }


def get_hkex_source_registry_entry() -> dict:
    """
    Return the source_registry entry for HKEX.
    If DISABLED, verified=False — never claim HKEX is verified when not connected.
    """
    status = get_hkex_status()
    is_verified = status != HKEX_STATUS_DISABLED
    return {
        "enabled": status != HKEX_STATUS_DISABLED,
        "verified": is_verified,
        "source": "HKEX 披露易" if is_verified else "未接入",
        "status": status,
        "last_updated": datetime.now().strftime("%Y-%m-%d"),
        "verified_fields": ["公告日期", "公告類型", "摘要"] if is_verified else [],
        "missing_fields": [] if status == HKEX_STATUS_ENABLED_WITH_DATA else (
            ["公告內容"] if status == HKEX_STATUS_ENABLED_EMPTY else
            ["全部 HKEX 公告資料"]
        ),
        "note": "" if is_verified else "HKEX 公告模組尚未啟用，不計入資料可信度評分。",
    }
