"""
core/intelligence_store.py

High-level intelligence store facade — v2.1.0

Wraps local_data_store for use in app.py.
Single call to record_analysis_complete() handles all JSONL writes.
All operations are safe — failures never crash the app.
"""

from __future__ import annotations

import os
from datetime import datetime
from typing import Any


def _make_session_id() -> str:
    """Generate a session-scoped ID without external dependencies."""
    import random
    suffix = "".join(str(random.randint(0, 9)) for _ in range(6))
    return f"{datetime.now().strftime('%Y%m%d%H%M%S')}{suffix}"


def record_analysis_complete(
    ticker: str,
    report_sections: dict[str, Any],
    report_package: dict[str, Any] | None = None,
    pdf_path: str | None = None,
    session_id: str = "",
) -> dict[str, bool]:
    """
    Record a completed analysis to the local data lake.

    Writes:
    - analysis_runs.jsonl
    - market_snapshots.jsonl (if snapshot data available)
    - report_metadata.jsonl

    Returns a dict of {file: success_bool} for logging.
    Never raises — all failures are caught internally.
    """
    results: dict[str, bool] = {}

    try:
        from core.local_data_store import (
            append_analysis_run,
            append_market_snapshot,
            append_report_metadata,
        )
        from core.config import APP_VERSION
    except Exception as exc:
        print(f"[IntelligenceStore] import failed: {exc}")
        return {}

    cover = (report_sections or {}).get("cover", {}) or {}
    snapshot = (report_sections or {}).get("market_snapshot", {}) or {}
    pdf_filename = os.path.basename(str(pdf_path)) if pdf_path else ""

    # 1. Analysis run
    results["analysis_run"] = append_analysis_run(
        ticker=ticker,
        cover=cover,
        report_package=report_package,
        pdf_path=pdf_path,
        session_id=session_id,
        app_version=APP_VERSION,
    )

    # 2. Market snapshot (only if valid data exists)
    if snapshot.get("is_valid"):
        results["market_snapshot"] = append_market_snapshot(
            ticker=ticker,
            snapshot=snapshot,
            session_id=session_id,
        )

    # 3. Report metadata
    results["report_metadata"] = append_report_metadata(
        ticker=ticker,
        cover=cover,
        pdf_filename=pdf_filename,
        app_version=APP_VERSION,
        session_id=session_id,
    )

    print(f"[IntelligenceStore] {ticker} recorded: {results}")
    return results


def record_user_event(
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
        from core.local_data_store import append_user_event
        return append_user_event(
            event_type=event_type,
            ticker=ticker,
            session_id=session_id,
            metadata=metadata,
        )
    except Exception as exc:
        print(f"[IntelligenceStore] record_user_event failed: {exc}")
        return False


def get_data_lake_status() -> dict[str, Any]:
    """
    Return data lake status for UI display.
    Returns safe defaults if data lake is unavailable.
    """
    try:
        from core.local_data_store import get_today_stats
        from core.config import LOCAL_DATA_MODE, DATA_LAKE_PATH
        stats = get_today_stats()
        return {
            "mode": "本地 Data Lake" if LOCAL_DATA_MODE else "Cloud DB",
            "today_runs": stats.get("analysis_runs", 0),
            "today_snapshots": stats.get("market_snapshots", 0),
            "today_events": stats.get("user_events", 0),
            "data_lake_path": stats.get("data_lake_path", str(DATA_LAKE_PATH)),
            "date": stats.get("date", ""),
            "available": True,
        }
    except Exception as exc:
        print(f"[IntelligenceStore] get_data_lake_status failed: {exc}")
        return {
            "mode": "本地 Data Lake",
            "today_runs": 0,
            "today_snapshots": 0,
            "today_events": 0,
            "data_lake_path": "",
            "date": datetime.now().strftime("%Y-%m-%d"),
            "available": False,
        }
