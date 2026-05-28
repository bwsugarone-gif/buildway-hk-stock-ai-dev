"""
Regression checks for the data confidence and company intelligence layers.

Run from buildway-hk-stock-ai/:
    python test_v041_data_confidence.py
"""

import os
import sys

os.chdir(os.path.dirname(os.path.abspath(__file__)))

from agents.ceo_agent import CEOAgent
from core.data_confidence import HIGH, INVALID, LOW
from core.report_builder import ReportBuilder


VALID = ["700", "9988", "0005"]
PARTIAL = ["3416", "0688"]
INVALID_TICKERS = ["12345", "99999", "ABCDE", "3896", "2638"]


def run_case(ticker: str):
    ceo = CEOAgent()
    ceo.market_agent._yfinance_available = False
    package = ceo.run_analysis(ticker=ticker, risk_preference="medium")
    sections = ReportBuilder().build(package)
    return package, sections


def assert_true(label: str, condition: bool) -> None:
    if not condition:
        raise AssertionError(label)
    print(f"[OK] {label}")


def cover_has_company_profile(cover: dict) -> bool:
    return all(
        str(cover.get(field, "")).strip()
        for field in ["company_name_zh", "company_name_en", "sector", "business", "market_type"]
    )


def main() -> int:
    for ticker in VALID:
        package, sections = run_case(ticker)
        confidence = package["report_metadata"]["data_confidence"]
        cover = sections["cover"]
        assert_true(f"{ticker} is HIGH confidence", confidence == HIGH)
        assert_true(f"{ticker} has confidence badge", bool(cover.get("data_confidence_label")))
        assert_true(f"{ticker} has company intelligence profile", cover_has_company_profile(cover))

    for ticker in PARTIAL:
        package, sections = run_case(ticker)
        confidence = package["report_metadata"]["data_confidence"]
        cover = sections["cover"]
        assert_true(f"{ticker} is LOW confidence", confidence == LOW)
        assert_true(f"{ticker} has fallback company metadata", cover_has_company_profile(cover))
        assert_true(
            f"{ticker} uses HK stock master fallback",
            cover.get("metadata_source") == "hk_stock_master_data",
        )

    for ticker in INVALID_TICKERS:
        package, sections = run_case(ticker)
        confidence = package["report_metadata"]["data_confidence"]
        cover = sections["cover"]
        rows_text = str(sections["company_intelligence"]["rows"])
        assert_true(f"{ticker} is INVALID", confidence == INVALID)
        assert_true(f"{ticker} has invalid badge", bool(cover.get("data_confidence_label")))
        assert_true(f"{ticker} has no Chinese company name", not cover.get("company_name_zh"))
        assert_true(f"{ticker} has no English company name", not cover.get("company_name_en"))
        assert_true(f"{ticker} has no business profile", not cover.get("business"))
        assert_true(f"{ticker} has no market category", not cover.get("market_type"))
        assert_true(f"{ticker} stops advanced analysis", cover.get("final_rating"))
        assert_true(
            f"{ticker} does not invent company narrative",
            "hk_stock_master_data" not in rows_text,
        )

    print("All v0.5.x data confidence and company intelligence tests passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
