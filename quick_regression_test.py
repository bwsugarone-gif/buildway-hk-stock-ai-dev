"""
Quick regression smoke test for Buildway HK Stock AI.

Runs the core agent pipeline, report builder, PDF generator, and invalid ticker
guard for the main QA tickers. This script is intentionally local and does not
call external services.
"""

from __future__ import annotations

from pathlib import Path

from agents.ceo_agent import CEOAgent
from core.pdf_generator import PDFGenerator
from core.report_builder import ReportBuilder


TICKERS = ["0700", "9988", "0005", "0941", "0688", "3416", "12345"]
BAD_TOKENS = ["HK$0.00", "0.0%", "0.00x", "0.0x", "資料待補充", "暫無資料"]


def _extract_pdf_text(path: Path) -> tuple[int | str, str]:
    try:
        from pypdf import PdfReader
    except Exception:
        return "未安裝 pypdf", ""

    reader = PdfReader(str(path))
    text = "\n".join((page.extract_text() or "") for page in reader.pages)
    return len(reader.pages), text


def main() -> None:
    reports_dir = Path("reports")
    reports_dir.mkdir(exist_ok=True)

    for ticker in TICKERS:
        package = CEOAgent().run_analysis(ticker=ticker, portfolio_size_hkd=1_000_000)
        sections = ReportBuilder().build(package)
        market_data = package.get("market_data", {}) or {}
        confidence = market_data.get("data_confidence", "")

        pdf_path = reports_dir / f"quick_regression_{ticker}.pdf"
        PDFGenerator().generate(sections, str(pdf_path))
        pages, pdf_text = _extract_pdf_text(pdf_path)

        bad_tokens = [token for token in BAD_TOKENS if token in pdf_text]
        invalid_hallucination = ticker == "12345" and any(
            market_data.get(key) for key in ["company_name", "company_name_en", "business_profile"]
        )

        if bad_tokens:
            raise AssertionError(f"{ticker} PDF contains placeholder tokens: {bad_tokens}")
        if invalid_hallucination:
            raise AssertionError("12345 generated invalid company narrative")

        print(f"[OK] {ticker} confidence={confidence} pdf_pages={pages}")
        pdf_path.unlink(missing_ok=True)

    print("[OK] quick regression completed")


if __name__ == "__main__":
    main()
