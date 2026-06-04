"""
FOS v4.3.1 PDF risk readability QA.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from reportlab.lib import colors

from core.config import APP_VERSION, BUILD_STAGE
from core.investment_conclusion_engine import build_investment_conclusion
from core.pdf_generator import (
    PDFGenerator,
    RISK_BAR_BG,
    RISK_BAR_EXTREME,
    RISK_BAR_HIGH,
    RISK_BAR_LOW,
    RISK_BAR_MEDIUM,
    RISK_HEAT_PALETTE,
)


PASSED: list[str] = []
FAILED: list[str] = []


def ok(name: str, msg: str = "") -> None:
    PASSED.append(name)
    print(f"  PASS  {name}" + (f" - {msg}" if msg else ""))


def fail(name: str, msg: str) -> None:
    FAILED.append(name)
    print(f"  FAIL  {name} - {msg}")


def _hex(color) -> str:
    return color.hexval().upper()


def _risk_section() -> dict:
    items = [
        {"risk_name": "低風險", "score": "2.0/10", "score_raw": 2.0, "weight": "10%", "level": "低風險"},
        {"risk_name": "中等風險", "score": "4.5/10", "score_raw": 4.5, "weight": "20%", "level": "中等風險"},
        {"risk_name": "高風險", "score": "7.0/10", "score_raw": 7.0, "weight": "25%", "level": "高風險"},
        {"risk_name": "極高風險", "score": "9.0/10", "score_raw": 9.0, "weight": "30%", "level": "極高風險"},
    ]
    return {
        "composite_score": "5.8/10",
        "risk_label": "中等風險",
        "risk_items": items,
        "risk_table": [
            {"dimension": item["risk_name"], "score": item["score"], "level": item["level"], "weight": item["weight"], "heat": item["level"]}
            for item in items
        ],
        "top_risks": items[:3],
    }


def _market_payload() -> dict:
    return {
        "ticker": "9988.HK",
        "company_name": "Alibaba Group",
        "current_price": 82.35,
        "pe_ratio": 14.8,
        "pb_ratio": 1.6,
        "revenue_ttm": 941_000_000_000,
        "net_income_ttm": 79_000_000_000,
        "roe": 8.6,
        "net_margin": 8.4,
        "ebitda": 170_000_000_000,
    }


def _registry(with_news: bool = True) -> dict:
    registry = {
        "company_metadata": {"verified": True},
        "market_data": {"verified": True},
        "financial_statement": {"verified": True},
    }
    if with_news:
        registry["news"] = {"verified": True}
    return registry


def _news_summary(result: dict) -> str:
    for item in result.get("decision_basis", []):
        if "新聞" in str(item.get("factor", "")):
            return str(item.get("summary", ""))
    return ""


def test_app_version() -> None:
    assert APP_VERSION == "v4.3.1", APP_VERSION
    assert BUILD_STAGE == "PDF Risk Readability Patch", BUILD_STAGE
    ok("app-version")


def test_risk_bar_palette() -> None:
    assert _hex(RISK_BAR_BG) == "0XE5E7EB"
    assert _hex(RISK_BAR_LOW) == "0X14B8A6"
    assert _hex(RISK_BAR_MEDIUM) == "0XF59E0B"
    assert _hex(RISK_BAR_HIGH) == "0XEF4444"
    assert _hex(RISK_BAR_EXTREME) == "0XDC2626"
    pdf = PDFGenerator()
    drawing = pdf._risk_bar(4.5)
    assert _hex(drawing.contents[0].fillColor) == "0XE5E7EB"
    assert _hex(drawing.contents[1].fillColor) == "0XF59E0B"
    ok("risk-bar-palette")


def test_heat_palette_uses_light_backgrounds() -> None:
    expected = {
        "LOW": ("0XCCFBF1", "0X134E4A"),
        "MEDIUM": ("0XFEF3C7", "0X92400E"),
        "HIGH": ("0XFEE2E2", "0X991B1B"),
        "EXTREME": ("0XFECACA", "0X7F1D1D"),
    }
    for bucket, (bg, text) in expected.items():
        actual_bg, actual_text = RISK_HEAT_PALETTE[bucket]
        assert _hex(actual_bg) == bg, bucket
        assert _hex(actual_text) == text, bucket
    dark_backgrounds = {"0X92400E", "0X991B1B"}
    actual_backgrounds = {_hex(pair[0]) for pair in RISK_HEAT_PALETTE.values()}
    assert not actual_backgrounds.intersection(dark_backgrounds), actual_backgrounds
    ok("heat-palette-light-backgrounds")


def test_risk_table_heat_text_readable_and_bold() -> None:
    pdf = PDFGenerator()
    rows = [["風險項目", "分數", "風險級別", "權重", "風險熱度"]]
    for item in _risk_section()["risk_table"]:
        rows.append([item["dimension"], item["score"], item["level"], item["weight"], item["heat"]])
    table = pdf._risk_table(rows)
    heat_cell = table._cellvalues[1][4]
    assert heat_cell.style.fontSize >= 9
    assert heat_cell.style.fontName == pdf.bold_font_name
    assert heat_cell.style.textColor != colors.black
    ok("risk-table-heat-text-readable")


def test_risk_dashboard_and_table_present() -> None:
    pdf = PDFGenerator()
    section = _risk_section()
    dashboard = pdf._risk_dashboard(section)
    story = pdf._risk(section)
    assert dashboard is not None
    assert any(item.__class__.__name__ == "Table" for item in story), "risk story should include dashboard/table"
    assert pdf.styles["TableTC"].fontSize >= 9
    ok("risk-dashboard-and-table-present")


def test_news_decision_basis_high_coverage() -> None:
    market = _market_payload()
    result = build_investment_conclusion(
        {"_raw": market},
        market,
        _risk_section(),
        {"news_count": 9, "news_confidence": "HIGH", "agents": []},
        [],
        _registry(True),
    )
    summary = _news_summary(result)
    assert "新聞資料已取得" in summary, summary
    assert "新聞資料有限" not in summary and "新聞資料不足" not in summary, summary
    ok("news-high-coverage-decision-basis")


def test_news_decision_basis_zero_and_limited() -> None:
    market = _market_payload()
    zero = build_investment_conclusion(
        {"_raw": market},
        market,
        _risk_section(),
        {"news_count": 0, "news_confidence": "", "agents": []},
        [],
        _registry(False),
    )
    limited = build_investment_conclusion(
        {"_raw": market},
        market,
        _risk_section(),
        {"news_count": 3, "news_confidence": "MEDIUM", "agents": []},
        [],
        _registry(True),
    )
    assert "新聞資料不足" in _news_summary(zero), zero.get("decision_basis")
    assert "新聞資料有限" in _news_summary(limited), limited.get("decision_basis")
    ok("news-zero-and-limited-decision-basis")


def run_all() -> bool:
    print("=" * 60)
    print("FOS v4.3.1 PDF Risk Readability QA Suite")
    print("=" * 60)
    for test in (
        test_app_version,
        test_risk_bar_palette,
        test_heat_palette_uses_light_backgrounds,
        test_risk_table_heat_text_readable_and_bold,
        test_risk_dashboard_and_table_present,
        test_news_decision_basis_high_coverage,
        test_news_decision_basis_zero_and_limited,
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
        print("FOS v4.3.1 PDF Risk Readability QA: ALL PASS")
    print("=" * 60)
    return not FAILED


if __name__ == "__main__":
    sys.exit(0 if run_all() else 1)
