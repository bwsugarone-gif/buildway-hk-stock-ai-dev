"""
Fresh PDF path helpers for the Streamlit report flow.
"""

from __future__ import annotations

import os
from datetime import datetime

from core.utils import normalize_hk_ticker


def pdf_version_token(version: str) -> str:
    return str(version or "").replace(".", "_").replace(" ", "_")


def build_fresh_pdf_path(ticker: str, version: str, reports_dir: str = "reports", timestamp: str | None = None) -> str:
    normalized = normalize_hk_ticker(ticker).replace(".", "_")
    stamp = timestamp or datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    filename = f"Buildway_HK_Investment_Report_{normalized}_{pdf_version_token(version)}_{stamp}.pdf"
    return os.path.join(reports_dir, filename)


def pdf_path_matches_active_report(pdf_path: str | None, ticker: str, version: str) -> bool:
    if not pdf_path:
        return False
    name = os.path.basename(str(pdf_path))
    normalized = normalize_hk_ticker(ticker).replace(".", "_")
    return normalized in name and pdf_version_token(version) in name


def should_regenerate_pdf(pdf_path: str | None, ticker: str, version: str) -> bool:
    return not pdf_path_matches_active_report(pdf_path, ticker, version) or not os.path.exists(str(pdf_path or ""))
