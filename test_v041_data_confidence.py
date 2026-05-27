"""
test_v041_data_confidence.py

Validation for v0.4.1 Data Confidence + Invalid Ticker Control Layer.
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
PARTIAL = ["3416"]
INVALID_TICKERS = ["12345", "99999", "ABCDE", "3896", "2638"]


def run_case(ticker: str):
    ceo = CEOAgent()
    ceo.market_agent._yfinance_available = False
    package = ceo.run_analysis(ticker=ticker, risk_preference="中等")
    sections = ReportBuilder().build(package)
    return package, sections


def assert_true(label: str, condition: bool) -> None:
    if not condition:
        raise AssertionError(label)
    print(f"[OK] {label}")


def main() -> int:
    for ticker in VALID:
        package, sections = run_case(ticker)
        confidence = package["report_metadata"]["data_confidence"]
        assert_true(f"{ticker} is HIGH confidence", confidence == HIGH)
        assert_true(f"{ticker} has confidence badge", bool(sections["cover"].get("data_confidence_label")))

    for ticker in PARTIAL:
        package, sections = run_case(ticker)
        confidence = package["report_metadata"]["data_confidence"]
        rows = sections["company_intelligence"]["rows"]
        assert_true(f"{ticker} is LOW confidence", confidence == LOW)
        assert_true(f"{ticker} has partial warning", any("保守假設" in str(row) for row in rows))

    forbidden_invalid_phrases = ["為香港上市公司", "收入主要來自", "公司主要業務與", "核心產品或服務包括"]
    for ticker in INVALID_TICKERS:
        package, sections = run_case(ticker)
        confidence = package["report_metadata"]["data_confidence"]
        rows_text = str(sections["company_intelligence"]["rows"])
        assert_true(f"{ticker} is INVALID", confidence == INVALID)
        assert_true(f"{ticker} has invalid badge", "資料驗證未完成" in sections["cover"].get("data_confidence_label", ""))
        assert_true(
            f"{ticker} has no fake company descriptions",
            not any(phrase in rows_text for phrase in forbidden_invalid_phrases),
        )
        assert_true(f"{ticker} stops advanced analysis", sections["cover"].get("final_rating") == "無法評估")

    print("All v0.4.4 data confidence tests passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
