"""
core/local_data_store.py

Local Data Moat Foundation Layer — v2.1.0

Folder-based JSONL data lake for analysis runs, market snapshots,
user events, report metadata, and manual notes.

Design rules:
- All writes are wrapped in try/except — failures never crash the app.
- No API keys or sensitive personal data are stored.
- INVALID tickers are recorded with data_confidence="INVALID", no fake data.
- ensure_ascii=False for all JSONL output.
- Future-compatible: DATABASE_URL upgrade path preserved in config.
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any


# ─── Path helpers ─────────────────────────────────────────────────────────────

def _data_lake_root() -> Path:
    """Return the data_lake root path from config, or default."""
    try:
        from core.config import DATA_LAKE_PATH
        return Path(DATA_LAKE_PATH)
    except Exception:
        return Path(__file__).resolve().parent.parent / "data_lake"


def _today_str() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def _daily_dir() -> Path:
    root = _data_lake_root()
    daily = root / "daily" / _today_str()
    daily.mkdir(parents=True, exist_ok=True)
    return daily


def _reports_dir() -> Path:
    root = _data_lake_root()
    d = root / "reports" / _today_str()
    d.mkdir(parents=True, exist_ok=True)
    return d


def _exports_dir() -> Path:
    root = _data_lake_root()
    d = root / "exports"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _ensure_data_lake() -> None:
    """Ensure all top-level data_lake folders exist."""
    root = _data_lake_root()
    for sub in ("daily", "reports", "exports", "backups"):
        (root / sub).mkdir(parents=True, exist_ok=True)


# ─── JSONL writer ─────────────────────────────────────────────────────────────

def _append_jsonl(filepath: Path, record: dict[str, Any]) -> bool:
    """
    Append a single JSON record to a JSONL file.
    Returns True on success, False on failure (never raises).
    """
    try:
        with open(filepath, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
        return True
    except Exception as exc:
        print(f"[DataStore] JSONL write failed ({filepath.name}): {exc}")
        return False


def _count_jsonl_lines(filepath: Path) -> int:
    """Count records in a JSONL file. Returns 0 if file doesn't exist."""
    try:
        if not filepath.exists():
            return 0
        with open(filepath, "r", encoding="utf-8") as f:
            return sum(1 for line in f if line.strip())
    except Exception:
        return 0


# ─── Public write functions ───────────────────────────────────────────────────

def append_analysis_run(
    ticker: str,
    cover: dict[str, Any],
    report_package: dict[str, Any] | None = None,
    pdf_path: str | None = None,
    session_id: str = "",
    app_version: str = "",
) -> bool:
    """
    Record a completed analysis run.
    Safe for INVALID tickers — only stores verified fields.
    """
    try:
        _ensure_data_lake()
        filepath = _daily_dir() / "analysis_runs.jsonl"

        market = (report_package or {}).get("market_data", {}) or {}
        confidence = str(cover.get("data_confidence") or market.get("data_confidence") or "UNKNOWN")

        # For INVALID tickers, only store minimal verified fields
        if "INVALID" in confidence.upper():
            record = {
                "created_at": datetime.now().isoformat(),
                "ticker": str(ticker),
                "data_confidence": "INVALID",
                "summary": "資料驗證未完成，系統已停止深度分析。",
                "pdf_generated": False,
                "session_id": str(session_id),
                "app_version": str(app_version),
            }
        else:
            record = {
                "created_at": datetime.now().isoformat(),
                "ticker": str(ticker),
                "company_name": str(cover.get("company_name_zh") or cover.get("company_name") or ""),
                "data_confidence": confidence,
                "risk_score": str(cover.get("risk_score") or ""),
                "final_rating": str(cover.get("final_rating") or ""),
                "summary": str(cover.get("data_confidence_label") or ""),
                "pdf_generated": bool(pdf_path and os.path.exists(str(pdf_path))),
                "pdf_filename": os.path.basename(str(pdf_path)) if pdf_path else "",
                "session_id": str(session_id),
                "app_version": str(app_version),
            }

        return _append_jsonl(filepath, record)
    except Exception as exc:
        print(f"[DataStore] append_analysis_run failed: {exc}")
        return False


def append_market_snapshot(
    ticker: str,
    snapshot: dict[str, Any],
    session_id: str = "",
) -> bool:
    """Record a market snapshot for a ticker."""
    try:
        _ensure_data_lake()
        filepath = _daily_dir() / "market_snapshots.jsonl"

        record = {
            "created_at": datetime.now().isoformat(),
            "ticker": str(ticker),
            "snapshot_confidence": str(snapshot.get("snapshot_confidence") or ""),
            "is_demo": bool(snapshot.get("is_demo", True)),
            "session_id": str(session_id),
        }

        # Only store valid numeric fields — no 0.0 placeholders
        price_sec = snapshot.get("price_section", {}) or {}
        val_sec = snapshot.get("valuation_section", {}) or {}
        range_sec = snapshot.get("range_section", {}) or {}

        for key, value in {**price_sec, **val_sec, **range_sec}.items():
            text = str(value or "").strip()
            if text and text not in {"資料待補充", "N/A", "0", "0.0"}:
                record[key] = text

        return _append_jsonl(filepath, record)
    except Exception as exc:
        print(f"[DataStore] append_market_snapshot failed: {exc}")
        return False


def append_news_intelligence(
    ticker: str,
    news: dict[str, Any],
    session_id: str = "",
) -> bool:
    """Record verified news intelligence. Empty/no-news state is recorded explicitly."""
    try:
        _ensure_data_lake()
        filepath = _daily_dir() / "news_intelligence.jsonl"
        record = {
            "created_at": datetime.now().isoformat(),
            "ticker": str(ticker),
            "has_news": bool(news.get("has_news")),
            "status": str(news.get("summary") or news.get("status") or ""),
            "news_confidence": str(news.get("news_confidence") or ""),
            "news_source": str(news.get("source") or ""),
            "session_id": str(session_id),
        }
        items = news.get("news_items") or news.get("recent_news") or []
        if items:
            record["news_count"] = len(items)
            record["latest_news_date"] = str((items[0] or {}).get("news_date") or (items[0] or {}).get("published_at") or "")
        return _append_jsonl(filepath, record)
    except Exception as exc:
        print(f"[DataStore] append_news_intelligence failed: {exc}")
        return False


def append_hkex_intelligence(
    ticker: str,
    hkex: dict[str, Any],
    session_id: str = "",
) -> bool:
    """Record HKEX intelligence status without fabricating announcement content."""
    try:
        _ensure_data_lake()
        filepath = _daily_dir() / "hkex_intelligence.jsonl"
        announcements = hkex.get("announcements") or {}
        record = {
            "created_at": datetime.now().isoformat(),
            "ticker": str(ticker),
            "has_data": bool(hkex.get("has_data")),
            "status": str(hkex.get("status_summary") or hkex.get("status") or ""),
            "is_connected": bool(announcements.get("is_connected")),
            "announcement_count": len(announcements.get("announcements") or []),
            "session_id": str(session_id),
        }
        return _append_jsonl(filepath, record)
    except Exception as exc:
        print(f"[DataStore] append_hkex_intelligence failed: {exc}")
        return False


def append_user_event(
    event_type: str,
    ticker: str = "",
    session_id: str = "",
    metadata: dict[str, Any] | None = None,
) -> bool:
    """
    Record a user interaction event.
    event_type: search_ticker | generate_report | download_pdf |
                add_watchlist | rerun_analysis
    """
    try:
        _ensure_data_lake()
        filepath = _daily_dir() / "user_events.jsonl"

        record = {
            "created_at": datetime.now().isoformat(),
            "event_type": str(event_type),
            "ticker": str(ticker),
            "session_id": str(session_id),
        }
        if metadata:
            # Only store safe, non-sensitive metadata keys
            safe_keys = {"confidence", "rating", "risk_score", "source"}
            for k, v in metadata.items():
                if k in safe_keys:
                    record[k] = str(v)

        return _append_jsonl(filepath, record)
    except Exception as exc:
        print(f"[DataStore] append_user_event failed: {exc}")
        return False


def append_report_metadata(
    ticker: str,
    cover: dict[str, Any],
    pdf_filename: str = "",
    app_version: str = "",
    session_id: str = "",
) -> bool:
    """Record report metadata (no PDF binary, just metadata)."""
    try:
        _ensure_data_lake()
        filepath = _daily_dir() / "report_metadata.jsonl"

        record = {
            "created_at": datetime.now().isoformat(),
            "ticker": str(ticker),
            "report_title": "香港股票智能分析報告",
            "report_version": str(app_version),
            "company_name": str(cover.get("company_name_zh") or cover.get("company_name") or ""),
            "data_confidence": str(cover.get("data_confidence") or ""),
            "final_rating": str(cover.get("final_rating") or ""),
            "pdf_filename": str(pdf_filename),
            "session_id": str(session_id),
        }

        return _append_jsonl(filepath, record)
    except Exception as exc:
        print(f"[DataStore] append_report_metadata failed: {exc}")
        return False


def append_manual_note(
    ticker: str,
    note_type: str,
    note_text: str,
    created_by: str = "user",
    session_id: str = "",
) -> bool:
    """
    Record a manual note (placeholder for future analyst notes feature).
    note_type: observation | risk_flag | catalyst | follow_up
    """
    try:
        _ensure_data_lake()
        filepath = _daily_dir() / "manual_notes.jsonl"

        record = {
            "created_at": datetime.now().isoformat(),
            "ticker": str(ticker),
            "note_type": str(note_type),
            "note_text": str(note_text)[:2000],  # Cap at 2000 chars
            "created_by": str(created_by),
            "session_id": str(session_id),
        }

        return _append_jsonl(filepath, record)
    except Exception as exc:
        print(f"[DataStore] append_manual_note failed: {exc}")
        return False


# ─── Read / stats functions ───────────────────────────────────────────────────

def get_today_stats() -> dict[str, Any]:
    """Return today's record counts for each JSONL file."""
    try:
        daily = _daily_dir()
        return {
            "date": _today_str(),
            "analysis_runs": _count_jsonl_lines(daily / "analysis_runs.jsonl"),
            "market_snapshots": _count_jsonl_lines(daily / "market_snapshots.jsonl"),
            "news_intelligence": _count_jsonl_lines(daily / "news_intelligence.jsonl"),
            "hkex_intelligence": _count_jsonl_lines(daily / "hkex_intelligence.jsonl"),
            "user_events": _count_jsonl_lines(daily / "user_events.jsonl"),
            "report_metadata": _count_jsonl_lines(daily / "report_metadata.jsonl"),
            "manual_notes": _count_jsonl_lines(daily / "manual_notes.jsonl"),
            "data_lake_path": str(_data_lake_root()),
        }
    except Exception as exc:
        print(f"[DataStore] get_today_stats failed: {exc}")
        return {
            "date": _today_str(),
            "analysis_runs": 0,
            "market_snapshots": 0,
            "news_intelligence": 0,
            "hkex_intelligence": 0,
            "user_events": 0,
            "report_metadata": 0,
            "manual_notes": 0,
            "data_lake_path": str(_data_lake_root()),
        }


def get_today_export_bytes(file_type: str = "analysis_runs") -> bytes | None:
    """
    Return today's JSONL file as bytes for Streamlit download_button.
    file_type: analysis_runs | market_snapshots | user_events | report_metadata
    Returns None if file doesn't exist or is empty.
    """
    try:
        filepath = _daily_dir() / f"{file_type}.jsonl"
        if not filepath.exists() or filepath.stat().st_size == 0:
            return None
        with open(filepath, "rb") as f:
            return f.read()
    except Exception as exc:
        print(f"[DataStore] get_today_export_bytes failed: {exc}")
        return None
