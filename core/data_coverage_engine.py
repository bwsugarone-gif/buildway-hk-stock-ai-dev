"""
core/data_coverage_engine.py

v2.2 Data Coverage Layer.

Normalizes market-data fields through explicit fallback mappings. Missing
values remain None so renderers can skip them instead of showing placeholders.
"""

from __future__ import annotations

from typing import Any

from core.data_confidence import HIGH, INVALID, LOW, MEDIUM, confidence_label
from core.data_normalizer import normalize_market_data
from core.safe_math import safe_number


COVERAGE_FIELDS = (
    "pe_ratio",
    "pb_ratio",
    "dividend_yield",
    "beta",
    "market_cap",
    "revenue_ttm",
    "ebitda",
    "net_income_ttm",
    "52w_high",
    "52w_low",
    "volume",
)


FIELD_ALIASES: dict[str, tuple[str, ...]] = {
    "pe_ratio": ("pe_ratio", "trailingPE", "forwardPE", "priceEarningsRatio"),
    "pb_ratio": ("pb_ratio", "priceToBook", "priceToBookRatio"),
    "dividend_yield": ("dividend_yield", "dividendYield", "trailingAnnualDividendYield"),
    "beta": ("beta", "beta3Year"),
    "market_cap": ("market_cap", "marketCap"),
    "revenue_ttm": ("revenue_ttm", "totalRevenue", "annualRevenue"),
    "ebitda": ("ebitda", "EBITDA"),
    "net_income_ttm": ("net_income_ttm", "netIncomeToCommon", "netIncome"),
    "52w_high": ("52w_high", "fiftyTwoWeekHigh", "52WeekHigh", "yearHigh"),
    "52w_low": ("52w_low", "fiftyTwoWeekLow", "52WeekLow", "yearLow"),
    "volume": ("volume", "regularMarketVolume", "averageVolume", "averageVolume10days"),
}


class DataCoverageEngine:
    """Apply deterministic fallback mapping and score data completeness."""

    def enhance(self, data: dict[str, Any], raw_info: dict[str, Any] | None = None) -> dict[str, Any]:
        if not data:
            return data
        if data.get("data_confidence") == INVALID or data.get("invalid_symbol"):
            data["coverage_score"] = INVALID
            return data

        raw = {**(raw_info or {}), **data}
        normalized = normalize_market_data(raw)
        enhanced = dict(data)

        for field in COVERAGE_FIELDS:
            value = self._first_valid(raw, FIELD_ALIASES[field])
            if value is None:
                value = normalized.get(field)
            enhanced[field] = self._clean_field(field, value)

        missing = list(enhanced.get("missing_data_flags", []) or [])
        for field in COVERAGE_FIELDS:
            if enhanced.get(field) is None:
                missing.append(f"{field} unavailable")
        enhanced["missing_data_flags"] = sorted(set(missing))
        enhanced["coverage_score"] = self.coverage_score(enhanced)
        enhanced["data_confidence"] = enhanced["coverage_score"]
        enhanced["data_confidence_label"] = confidence_label(enhanced["coverage_score"])
        return enhanced

    def coverage_score(self, data: dict[str, Any]) -> str:
        if data.get("invalid_symbol") or data.get("data_confidence") == INVALID:
            return INVALID
        has_identity = bool(str(data.get("ticker") or "").strip())
        has_price_or_cap = self._positive(data.get("current_price")) or self._positive(data.get("market_cap"))
        if not has_identity or not has_price_or_cap:
            return INVALID

        present = sum(1 for field in COVERAGE_FIELDS if self._valid(data.get(field)))
        ratio = present / len(COVERAGE_FIELDS)
        if ratio >= 0.82:
            return HIGH
        if ratio >= 0.55:
            return MEDIUM
        return LOW

    def _first_valid(self, data: dict[str, Any], aliases: tuple[str, ...]) -> float | None:
        for alias in aliases:
            value = self._to_number(data.get(alias))
            if value is not None and value != 0:
                return value
        return None

    def _clean_field(self, field: str, value: Any) -> float | None:
        number = self._to_number(value)
        if number is None or number == 0:
            return None
        if field == "dividend_yield" and number > 1:
            return number / 100.0
        return number

    def _to_number(self, value: Any) -> float | None:
        if value in (None, "", "N/A", "None"):
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    def _positive(self, value: Any) -> bool:
        return safe_number(value, 0.0) > 0

    def _valid(self, value: Any) -> bool:
        number = self._to_number(value)
        return number is not None and number != 0

