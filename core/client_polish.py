"""
Client-facing output polish helpers for Web/PDF/report payloads.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from core.config import LOGO_PATH
from core.utils import normalize_hk_ticker


PLACEHOLDER_VALUES = {
    "",
    "??",
    "????",
    "-",
    "N/A",
    "None",
    "資料待補充",
    "數據不足，採用中性評分",
    "中性持有",
}

PLACEHOLDER_SUBSTRINGS = (
    "????",
    "??",
    "數據不足，採用中性評分",
    "資料待補充",
    "中性持有",
)

LEGACY_TEXT_REPLACEMENTS = {
    "Bull Case": "樂觀情景",
    "Base Case": "基準情景",
    "Bear Case": "保守情景",
    "Investment Conclusion Engine composite score": "投資委員會綜合分",
    "Disclaimer heading": "免責聲明",
    "Disclaimer": "免責聲明",
}

DEFAULT_DECISION_BASIS = "暫無足夠決策依據，請補充市場、財務或新聞資料。"
TARGET_PRICE_NOT_PROVIDED = "目標價：未提供"
UPSIDE_NOT_PROVIDED = "潛在升幅：未提供"
TARGET_PRICE_EXPLANATION = "原因：目前未接入分析師共識或完整 DCF 模型，因此不提供目標價。"
INVALID_TICKER_MESSAGE = "股票代碼無效或未收錄，無法評估"
INSUFFICIENT_RATING_TEXT = "資料不足，暫不評級"
NEUTRAL_CLIENT_SUMMARY = "估值與風險暫時相對平衡，建議觀察後續盈利、政策及市場情緒變化。"


def clean_client_text(value: Any, fallback: str = "") -> str:
    text = str(value if value is not None else "").strip()
    if text in PLACEHOLDER_VALUES:
        return fallback
    for old, new in LEGACY_TEXT_REPLACEMENTS.items():
        text = text.replace(old, new)
    for token in PLACEHOLDER_SUBSTRINGS:
        text = text.replace(token, "")
    text = " ".join(text.split()).strip()
    return text or fallback


def _clean_basis_item(item: Any) -> dict[str, str] | None:
    if isinstance(item, dict):
        factor = clean_client_text(item.get("factor"))
        weight = clean_client_text(item.get("weight"))
        score = clean_client_text(item.get("score"))
        summary = clean_client_text(item.get("summary"))
        if not any((factor, weight, score, summary)):
            return None
        return {
            "factor": factor or "主要依據",
            "weight": weight or "參考",
            "score": score or "未量化",
            "summary": summary or factor or DEFAULT_DECISION_BASIS,
        }
    text = clean_client_text(item)
    if not text:
        return None
    return {"factor": "主要依據", "weight": "參考", "score": "未量化", "summary": text}


def sanitize_decision_basis(items: Any) -> list[dict[str, str]]:
    cleaned: list[dict[str, str]] = []
    seen: set[tuple[str, str, str, str]] = set()
    raw_items = items if isinstance(items, list) else [items]
    for item in raw_items:
        cleaned_item = _clean_basis_item(item)
        if not cleaned_item:
            continue
        key = (
            cleaned_item["factor"],
            cleaned_item["weight"],
            cleaned_item["score"],
            cleaned_item["summary"],
        )
        if key in seen:
            continue
        seen.add(key)
        cleaned.append(cleaned_item)
    if cleaned:
        return cleaned
    return [{"factor": "主要依據", "weight": "參考", "score": "未量化", "summary": DEFAULT_DECISION_BASIS}]


def sanitize_text_list(items: Any, fallback: str = DEFAULT_DECISION_BASIS) -> list[str]:
    raw_items = items if isinstance(items, list) else [items]
    cleaned: list[str] = []
    seen: set[str] = set()
    for item in raw_items:
        text = clean_client_text(item)
        if not text or text in seen:
            continue
        seen.add(text)
        cleaned.append(text)
    return cleaned or [fallback]


def sanitize_report_payload(value: Any) -> Any:
    if isinstance(value, dict):
        cleaned = {key: sanitize_report_payload(item) for key, item in value.items()}
        if "decision_basis" in cleaned:
            cleaned["decision_basis"] = sanitize_decision_basis(cleaned.get("decision_basis"))
        if "monitor_next" in cleaned:
            cleaned["monitor_next"] = sanitize_text_list(cleaned.get("monitor_next"))
        if "risk_items" in cleaned and isinstance(cleaned["risk_items"], list):
            cleaned["risk_items"] = [item for item in cleaned["risk_items"] if item not in ({}, None)]
        return cleaned
    if isinstance(value, list):
        return [sanitize_report_payload(item) for item in value]
    if isinstance(value, tuple):
        return tuple(sanitize_report_payload(item) for item in value)
    if isinstance(value, str):
        return clean_client_text(value, "")
    return value


def _is_valid_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def _fallback_logo() -> str:
    candidates = [
        Path(LOGO_PATH),
        Path(__file__).resolve().parent.parent / "Logo.png",
        Path(__file__).resolve().parent.parent / "logo.png",
    ]
    for candidate in candidates:
        if candidate.exists():
            return str(candidate)
    return ""


def resolve_logo_path_or_url(report_data: dict[str, Any] | None = None, ticker: str = "") -> str:
    data = report_data or {}
    cover = data.get("cover", data) if isinstance(data, dict) else {}
    market = data.get("market_data", {}) if isinstance(data, dict) else {}
    metadata = data.get("company_metadata", {}) if isinstance(data, dict) else {}
    normalized = normalize_hk_ticker(ticker or str(cover.get("ticker") or market.get("ticker") or ""))
    candidates = [
        cover.get("logo_path"),
        cover.get("logo_url"),
        market.get("logo_path"),
        market.get("logo_url"),
        metadata.get("logo_path"),
        metadata.get("logo_url"),
    ]
    if normalized:
        candidates.extend([
            Path("assets") / f"{normalized.replace('.', '_')}.png",
            Path("assets") / f"{normalized}.png",
        ])
    for candidate in candidates:
        text = str(candidate or "").strip()
        if not text:
            continue
        if _is_valid_url(text):
            return text
        path = Path(text)
        if path.exists():
            return str(path)
    return _fallback_logo()


def is_local_logo(value: str) -> bool:
    return bool(value) and not _is_valid_url(value) and os.path.exists(value)
