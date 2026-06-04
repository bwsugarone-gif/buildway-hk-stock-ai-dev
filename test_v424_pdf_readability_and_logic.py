"""
FOS v4.2.4 PDF readability and report logic sync QA.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from reportlab.lib import colors
from reportlab.platypus import Table

from core.investment_conclusion_engine import build_investment_conclusion
from core.pdf_generator import FOOTER_FONT_SIZE, MUTED, PDFGenerator
from core.report_builder import ReportBuilder
from core.scenario_engine import build_scenario_analysis


PASSED: list[str] = []
FAILED: list[str] = []


def ok(name: str, msg: str = "") -> None:
    PASSED.append(name)
    print(f"  PASS  {name}" + (f" - {msg}" if msg else ""))


def fail(name: str, msg: str) -> None:
    FAILED.append(name)
    print(f"  FAIL  {name} - {msg}")


def _sample_market() -> dict:
    return {
        "ticker": "2638.HK",
        "company_name": "Hong Kong Electric Investments",
        "company_name_zh": "港燈",
        "sector": "Utilities",
        "current_price": 5.15,
        "price": 5.15,
        "market_cap": 25_000_000_000,
        "pe_ratio": 15.2,
        "pb_ratio": 1.1,
        "52w_high": 5.9,
        "52w_low": 4.4,
        "revenue_ttm": 11_300_000_000,
        "net_income_ttm": 2_900_000_000,
        "roe": 8.5,
        "net_margin": 25.0,
        "ebitda": 7_200_000_000,
    }


def _sample_risk() -> dict:
    items = [
        {"risk_name": "財務風險", "score": "4.2/10", "score_raw": 4.2, "weight": "20%", "level": "中等風險"},
        {"risk_name": "現金流風險", "score": "3.8/10", "score_raw": 3.8, "weight": "18%", "level": "中等風險"},
        {"risk_name": "流動性風險", "score": "4.0/10", "score_raw": 4.0, "weight": "15%", "level": "中等風險"},
        {"risk_name": "估值風險", "score": "4.8/10", "score_raw": 4.8, "weight": "17%", "level": "中等風險"},
        {"risk_name": "市場風險", "score": "5.1/10", "score_raw": 5.1, "weight": "15%", "level": "中等風險"},
        {"risk_name": "政策風險", "score": "3.5/10", "score_raw": 3.5, "weight": "10%", "level": "中等風險"},
        {"risk_name": "下行情景風險", "score": "4.5/10", "score_raw": 4.5, "weight": "5%", "level": "中等風險"},
    ]
    return {
        "risk_items": items,
        "composite_score": "4.3/10",
        "composite_score_raw": 4.3,
        "risk_label": "中等風險",
        "top_risks": items[:3],
        "total_weight": "100%",
    }


def _sample_registry(with_news: bool = False) -> dict:
    registry = {
        "company_metadata": {"verified": True, "verified_fields": ["name_zh", "sector"]},
        "market_data": {"verified": True, "verified_fields": ["price", "pe", "pb", "52w_high", "52w_low"]},
        "financial_statement": {"verified": True, "verified_fields": ["revenue", "net_income", "roe", "ebitda"]},
    }
    if with_news:
        registry["news"] = {"verified": True, "verified_fields": ["headline", "source"]}
    return registry


def test_no_old_neutral_fallback_phrase() -> None:
    text = "\n".join(
        Path(path).read_text(encoding="utf-8")
        for path in ("core/investment_conclusion_engine.py", "core/report_builder.py", "core/pdf_generator.py")
    )
    assert "採用中性評分" not in text
    ok("no-old-neutral-fallback")


def test_market_financial_risk_is_not_insufficient() -> None:
    market = _sample_market()
    result = build_investment_conclusion(
        {"_raw": market},
        market,
        _sample_risk(),
        {"agents": []},
        [],
        _sample_registry(with_news=False),
    )
    assert result.get("rating") != "資料不足", result
    assert result.get("data_coverage") == "PARTIAL", result
    assert result.get("data_coverage_label") == "部分資料覆蓋", result
    ok("partial-data-can-rate", f"{result.get('rating')} / {result.get('data_coverage_label')}")


def test_metadata_only_still_insufficient() -> None:
    market = {
        "ticker": "0006.HK",
        "company_name": "Power Assets Holdings",
        "sector": "Utilities",
        "price_unavailable": True,
        "current_price": 0,
    }
    result = build_investment_conclusion({"_raw": market}, market, {}, {}, [], _sample_registry(False))
    assert result.get("rating") == "資料不足", result
    assert result.get("data_coverage") == "INSUFFICIENT", result
    ok("metadata-only-insufficient")


def test_invalid_symbol_still_invalid() -> None:
    market = {"ticker": "12345.HK", "invalid_symbol": True, "data_confidence": "INVALID"}
    result = build_investment_conclusion({"_raw": market}, market, {}, {}, [], {})
    assert result.get("rating") == "無法評估", result
    assert result.get("invalid_symbol") is True, result
    assert result.get("data_coverage") == "INVALID", result
    ok("invalid-symbol-guard")


def test_pdf_style_minimums() -> None:
    pdf = PDFGenerator()
    assert pdf.styles["BodyTC"].fontSize >= 10.5
    assert pdf.styles["TableTC"].fontSize >= 9
    assert pdf.styles["TableHeaderTC"].fontSize >= 9.5
    assert pdf.styles["SmallTC"].fontSize >= 9
    assert pdf.styles["SectionTitle"].fontSize >= 16
    assert FOOTER_FONT_SIZE >= 8
    ok("pdf-font-size-minimums")


def test_pdf_english_legacy_terms_removed_from_payload() -> None:
    rows = build_scenario_analysis(_sample_market(), {}, {"composite_risk_score": 4.3}, {})["rows"]
    payload = str(rows) + str(ReportBuilder()._build_disclaimer())
    for banned in ("Bull Case", "Base Case", "Bear Case", "Bull case", "Base case", "Bear case", "Disclaimer"):
        assert banned not in payload, banned
    assert "樂觀情景" in payload and "基準情景" in payload and "保守情景" in payload
    assert "免責聲明" in payload
    ok("pdf-legacy-english-terms-removed")


def test_pdf_risk_section_has_dashboard_data() -> None:
    pdf = PDFGenerator()
    section = {
        "composite_score": "4.3/10",
        "risk_label": "中等風險",
        "risk_items": _sample_risk()["risk_items"],
        "risk_table": [
            {"dimension": item["risk_name"], "score": item["score"], "level": item["level"], "weight": item["weight"], "heat": item["level"]}
            for item in _sample_risk()["risk_items"]
        ],
        "top_risks": _sample_risk()["top_risks"],
    }
    dashboard = pdf._risk_dashboard(section)
    story = pdf._risk(section)
    assert isinstance(dashboard, Table)
    assert any(isinstance(item, Table) for item in story), "risk story should contain dashboard/table flowables"
    assert len(section["risk_items"]) == 7
    ok("pdf-risk-dashboard-data")


def test_pdf_muted_not_used_for_main_content() -> None:
    pdf = PDFGenerator()
    assert pdf.styles["BodyTC"].textColor != MUTED
    assert pdf.styles["TableTC"].textColor != MUTED
    assert pdf.styles["Notice"].textColor != MUTED
    assert MUTED == colors.HexColor("#374151")
    ok("muted-not-main-content")


def run_all() -> bool:
    print("=" * 60)
    print("FOS v4.2.4 PDF Readability and Logic Sync QA Suite")
    print("=" * 60)
    for test in (
        test_no_old_neutral_fallback_phrase,
        test_market_financial_risk_is_not_insufficient,
        test_metadata_only_still_insufficient,
        test_invalid_symbol_still_invalid,
        test_pdf_style_minimums,
        test_pdf_english_legacy_terms_removed_from_payload,
        test_pdf_risk_section_has_dashboard_data,
        test_pdf_muted_not_used_for_main_content,
    ):
        try:
            test()
        except Exception as exc:
            fail(test.__name__, str(exc))

    total = len(PASSED) + len(FAILED)
    print("\n" + "=" * 60)
    print(f"RESULT: {len(PASSED)}/{total} PASS")
    if FAILED:
        print(f"FAILED: {FAILED}")
    else:
        print("FOS v4.2.4 PDF Readability and Logic Sync QA: ALL PASS")
    print("=" * 60)
    return not FAILED


if __name__ == "__main__":
    sys.exit(0 if run_all() else 1)
