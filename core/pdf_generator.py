"""
core/pdf_generator.py

Institutional-grade PDF report generator with Traditional Chinese font support.
"""

from __future__ import annotations

import os
from typing import Any, Dict, Iterable, List, Sequence

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Image as RLImage,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


NAVY = colors.HexColor("#102A43")
NAVY_2 = colors.HexColor("#173A5E")
LIGHT_GREY = colors.HexColor("#F3F6F8")
MID_GREY = colors.HexColor("#D9E2EC")
TEXT = colors.HexColor("#1F2933")
MUTED = colors.HexColor("#52616B")
GREEN = colors.HexColor("#1B7F5A")
AMBER = colors.HexColor("#B7791F")
RED = colors.HexColor("#B42318")


class FontManager:
    """Register a Unicode-compatible Traditional Chinese font for ReportLab."""

    CANDIDATES = [
        ("MicrosoftJhengHei", r"C:\Windows\Fonts\msjh.ttc"),
        ("MicrosoftJhengHeiUI", r"C:\Windows\Fonts\msjhl.ttc"),
        ("MicrosoftJhengHeiBold", r"C:\Windows\Fonts\msjhbd.ttc"),
        ("NotoSansCJKTC", r"C:\Windows\Fonts\NotoSansCJKtc-Regular.otf"),
        ("SourceHanSansTC", r"C:\Windows\Fonts\SourceHanSansTC-Regular.otf"),
        ("MingLiU", r"C:\Windows\Fonts\mingliu.ttc"),
    ]

    @classmethod
    def setup(cls) -> tuple[str, str]:
        primary = None
        bold = None

        for name, path in cls.CANDIDATES:
            if not os.path.exists(path):
                continue
            try:
                pdfmetrics.registerFont(TTFont(name, path))
                if "Bold" in name:
                    bold = name
                elif primary is None:
                    primary = name
            except Exception:
                continue

        if primary is None:
            primary = "Helvetica"
        if bold is None:
            bold = primary
        return primary, bold


class PDFGenerator:
    """Render a nine-page institutional investment report."""

    def __init__(self, logo_path: str | None = None):
        self.logo_path = str(logo_path) if logo_path else None
        self.font_name, self.bold_font_name = FontManager.setup()
        self.styles = self._styles()

    def generate(self, report_sections: Dict[str, Any], output_path: str) -> str:
        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            leftMargin=1.55 * cm,
            rightMargin=1.55 * cm,
            topMargin=1.55 * cm,
            bottomMargin=1.7 * cm,
            title="Buildway Tech HK Stock Report",
            author="Buildway Tech (HK) Limited",
        )

        story: List[Any] = []
        story.extend(self._cover(report_sections.get("cover", {})))
        story.append(PageBreak())
        story.extend(self._executive_summary(report_sections.get("executive_summary", {})))
        story.append(PageBreak())
        story.extend(self._company_intelligence(report_sections.get("company_intelligence", {})))
        story.append(PageBreak())
        story.extend(self._multi_agent(report_sections.get("multi_agent_discussion", {})))
        story.append(PageBreak())
        story.extend(self._financial(report_sections.get("financial_analysis", {})))
        story.append(PageBreak())
        story.extend(self._risk(report_sections.get("risk_analysis", {})))
        story.append(PageBreak())
        story.extend(self._scenario(report_sections.get("scenario_analysis", {})))
        story.append(PageBreak())
        story.extend(self._portfolio(report_sections.get("portfolio_view", {})))
        story.append(PageBreak())
        story.extend(self._conclusion(report_sections.get("ic_conclusion", {}), report_sections.get("disclaimer", {})))

        doc.build(story, onFirstPage=self._footer, onLaterPages=self._footer)
        return output_path

    def _styles(self):
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(
            name="CoverBrand",
            parent=styles["Normal"],
            fontName=self.bold_font_name,
            fontSize=15,
            leading=20,
            alignment=TA_CENTER,
            textColor=NAVY,
        ))
        styles.add(ParagraphStyle(
            name="CoverTitle",
            parent=styles["Title"],
            fontName=self.bold_font_name,
            fontSize=25,
            leading=34,
            alignment=TA_CENTER,
            textColor=NAVY,
            spaceAfter=12,
        ))
        styles.add(ParagraphStyle(
            name="SectionTitle",
            parent=styles["Heading1"],
            fontName=self.bold_font_name,
            fontSize=15,
            leading=20,
            textColor=colors.white,
            backColor=NAVY,
            borderPadding=(7, 8, 7),
            spaceAfter=14,
        ))
        styles.add(ParagraphStyle(
            name="SubTitle",
            parent=styles["Heading2"],
            fontName=self.bold_font_name,
            fontSize=11.5,
            leading=16,
            textColor=NAVY_2,
            spaceBefore=6,
            spaceAfter=7,
        ))
        styles.add(ParagraphStyle(
            name="BodyTC",
            parent=styles["BodyText"],
            fontName=self.font_name,
            fontSize=9.5,
            leading=14,
            textColor=TEXT,
            spaceAfter=6,
        ))
        styles.add(ParagraphStyle(
            name="SmallTC",
            parent=styles["BodyText"],
            fontName=self.font_name,
            fontSize=8,
            leading=11,
            textColor=MUTED,
            spaceAfter=4,
        ))
        styles.add(ParagraphStyle(
            name="TableTC",
            parent=styles["BodyText"],
            fontName=self.font_name,
            fontSize=8,
            leading=10.5,
            textColor=TEXT,
        ))
        styles.add(ParagraphStyle(
            name="TableHeaderTC",
            parent=styles["BodyText"],
            fontName=self.bold_font_name,
            fontSize=8.2,
            leading=10.5,
            textColor=colors.white,
            alignment=TA_CENTER,
        ))
        styles.add(ParagraphStyle(
            name="Metric",
            parent=styles["BodyText"],
            fontName=self.bold_font_name,
            fontSize=12,
            leading=16,
            alignment=TA_CENTER,
            textColor=NAVY,
        ))
        return styles

    def _footer(self, canvas, doc):
        canvas.saveState()
        canvas.setFont(self.font_name, 8)
        canvas.setFillColor(MUTED)
        canvas.drawString(1.55 * cm, 1.0 * cm, "Buildway Tech (HK) Limited")
        canvas.drawRightString(A4[0] - 1.55 * cm, 1.0 * cm, f"Page {doc.page}")
        canvas.setStrokeColor(MID_GREY)
        canvas.line(1.55 * cm, 1.25 * cm, A4[0] - 1.55 * cm, 1.25 * cm)
        canvas.restoreState()

    def _cover(self, cover: Dict[str, Any]) -> List[Any]:
        elements: List[Any] = [Spacer(1, 0.5 * cm)]
        if self.logo_path and os.path.exists(self.logo_path):
            try:
                logo = RLImage(self.logo_path, width=3.2 * cm, height=3.2 * cm)
                logo.hAlign = "CENTER"
                elements.extend([logo, Spacer(1, 0.35 * cm)])
            except Exception:
                pass

        elements.extend([
            Paragraph(cover.get("brand", "Buildway Tech (HK) Limited"), self.styles["CoverBrand"]),
            Paragraph(cover.get("system", "AI Multi-Agent Financial Intelligence System"), self.styles["BodyTC"]),
            Spacer(1, 1.0 * cm),
            Paragraph(cover.get("title", "香港股票智能分析報告"), self.styles["CoverTitle"]),
            Spacer(1, 0.55 * cm),
        ])

        rows = [
            ["Stock code", cover.get("ticker", "N/A")],
            ["Company name", cover.get("company_name", "N/A")],
            ["Report date", cover.get("report_date", "N/A")],
            ["Final committee rating", cover.get("final_rating", "N/A")],
            ["Risk score", f"{cover.get('risk_score', 'N/A')} - {cover.get('risk_label', '')}"],
        ]
        elements.append(self._table(rows, [5.0 * cm, 10.2 * cm], header=False))
        elements.append(Spacer(1, 1.0 * cm))
        elements.append(Paragraph("Professional client trial report generated by a Python-calculated multi-agent framework.", self.styles["SmallTC"]))
        return elements

    def _executive_summary(self, section: Dict[str, Any]) -> List[Any]:
        elements = [self._title("Executive Summary")]
        metric_rows = [
            ["Final rating", section.get("final_rating", "N/A")],
            ["Key risk", section.get("key_risk", "N/A")],
            ["Key opportunity", section.get("key_opportunity", "N/A")],
            ["Recommended action category", section.get("recommended_action", "N/A")],
        ]
        elements.append(self._table(metric_rows, [5.2 * cm, 10.2 * cm]))
        elements.append(Spacer(1, 0.35 * cm))
        elements.append(Paragraph("重點摘要", self.styles["SubTitle"]))
        for bullet in section.get("bullets", []):
            elements.append(Paragraph(f"- {bullet}", self.styles["BodyTC"]))
        if section.get("llm_narrative"):
            elements.extend([Spacer(1, 0.2 * cm), Paragraph(section["llm_narrative"], self.styles["BodyTC"])])
        return elements

    def _company_intelligence(self, section: Dict[str, Any]) -> List[Any]:
        elements = [self._title(section.get("title", "公司基本面與業務分析"))]
        rows = [[label, value] for label, value in section.get("rows", [])]
        elements.append(self._table(rows, [4.0 * cm, 11.4 * cm]))
        return elements

    def _multi_agent(self, section: Dict[str, Any]) -> List[Any]:
        elements = [self._title(section.get("title", "Multi-Agent 投資委員會討論摘要"))]
        rows = [["Agent", "核心觀點", "風險提醒", "對最終評級影響"]]
        for item in section.get("table", []):
            rows.append([
                item.get("agent", ""),
                item.get("core_view", ""),
                item.get("risk_warning", ""),
                item.get("impact", ""),
            ])
        elements.append(self._table(rows, [2.7 * cm, 5.0 * cm, 4.5 * cm, 3.2 * cm], header=True))
        elements.extend([
            Spacer(1, 0.3 * cm),
            Paragraph("共識與分歧", self.styles["SubTitle"]),
            Paragraph(section.get("consensus", ""), self.styles["BodyTC"]),
            Spacer(1, 0.2 * cm),
            Paragraph(f"<b>{section.get('final_statement', '')}</b>", self.styles["BodyTC"]),
        ])
        return elements

    def _financial(self, section: Dict[str, Any]) -> List[Any]:
        elements = [self._title("Financial Analysis")]
        elements.append(Paragraph("財務與估值觀察", self.styles["SubTitle"]))
        for line in section.get("commentary", []):
            elements.append(Paragraph(f"- {line}", self.styles["BodyTC"]))
        elements.append(Spacer(1, 0.2 * cm))
        elements.append(Paragraph("Python-calculated ratios", self.styles["SubTitle"]))
        rows = [["Metric", "Value"]] + [[a, b] for a, b in section.get("metrics", [])]
        elements.append(self._table(rows, [6.0 * cm, 9.4 * cm], header=True))
        history = section.get("history", [])
        if history:
            elements.extend([Spacer(1, 0.3 * cm), Paragraph("Historical financials", self.styles["SubTitle"])])
            elements.append(self._table([["Year", "Revenue", "EBITDA", "Free cash flow"]] + history, [3.0 * cm, 4.1 * cm, 4.1 * cm, 4.2 * cm], header=True))
        return elements

    def _risk(self, section: Dict[str, Any]) -> List[Any]:
        elements = [self._title("Risk Analysis")]
        elements.append(Paragraph(f"Weighted risk score: <b>{section.get('composite_score')}</b> - {section.get('risk_label')}", self.styles["BodyTC"]))
        rows = [["風險項目", "分數", "風險評級", "權重", "Heatmap"]]
        for item in section.get("risk_table", []):
            rows.append([item["dimension"], item["score"], item["level"], item["weight"], item["heat"]])
        elements.append(self._risk_table(rows))
        elements.extend([Spacer(1, 0.3 * cm), Paragraph("Top 5 risks", self.styles["SubTitle"])])
        for item in section.get("top_risks", [])[:5]:
            elements.append(Paragraph(f"- {item['dimension']}: {item['score']}/10, {item['level']}", self.styles["BodyTC"]))
        return elements

    def _scenario(self, section: Dict[str, Any]) -> List[Any]:
        elements = [self._title("Scenario Analysis")]
        rows = [["Scenario", "Key assumptions", "Implied price / impact", "Downside trigger or catalyst"]]
        rows.extend(section.get("rows", []))
        elements.append(self._table(rows, [2.8 * cm, 5.0 * cm, 3.5 * cm, 4.1 * cm], header=True))
        elements.extend([Spacer(1, 0.35 * cm), Paragraph("Downside trigger points", self.styles["SubTitle"])])
        for trigger in section.get("triggers", []):
            elements.append(Paragraph(f"- {trigger}", self.styles["BodyTC"]))
        return elements

    def _portfolio(self, section: Dict[str, Any]) -> List[Any]:
        elements = [self._title("Portfolio & Risk Control View")]
        rows = [
            ["Investor suitability", section.get("investor_suitability", "")],
            ["Position sizing logic", section.get("position_sizing", "")],
            ["Stop-loss / review trigger concept", section.get("risk_control", "")],
            ["Action category", section.get("action_category", "")],
        ]
        elements.append(self._table(rows, [5.0 * cm, 10.4 * cm]))
        elements.extend([Spacer(1, 0.35 * cm), Paragraph(section.get("no_advice", ""), self.styles["SmallTC"])])
        return elements

    def _conclusion(self, section: Dict[str, Any], disclaimer: Dict[str, Any]) -> List[Any]:
        elements = [self._title("Investment Committee Final Conclusion")]
        elements.append(Paragraph(f"Final committee decision: <b>{section.get('final_decision', 'N/A')}</b>", self.styles["BodyTC"]))
        elements.append(Paragraph(section.get("multi_agent_statement", ""), self.styles["BodyTC"]))
        elements.extend([Spacer(1, 0.2 * cm), Paragraph("Why this rating", self.styles["SubTitle"]), Paragraph(section.get("why", ""), self.styles["BodyTC"])])
        elements.append(Paragraph("What to monitor next", self.styles["SubTitle"]))
        for item in section.get("monitor_next", []):
            elements.append(Paragraph(f"- {item}", self.styles["BodyTC"]))
        elements.extend([
            Spacer(1, 0.2 * cm),
            Paragraph("Data limitations", self.styles["SubTitle"]),
            Paragraph(section.get("data_limitations", ""), self.styles["SmallTC"]),
        ])
        if section.get("llm_warning"):
            elements.append(Paragraph(section["llm_warning"], self.styles["SmallTC"]))
        elements.extend([
            Spacer(1, 0.25 * cm),
            Paragraph(disclaimer.get("title", "Disclaimer"), self.styles["SubTitle"]),
            Paragraph(disclaimer.get("content", ""), self.styles["SmallTC"]),
        ])
        return elements

    def _title(self, text: str) -> Paragraph:
        return Paragraph(text, self.styles["SectionTitle"])

    def _p(self, value: Any, header: bool = False) -> Paragraph:
        style = self.styles["TableHeaderTC"] if header else self.styles["TableTC"]
        return Paragraph(str(value).replace("\n", "<br/>"), style)

    def _table(
        self,
        rows: Sequence[Sequence[Any]],
        widths: Sequence[float],
        header: bool = False,
    ) -> Table:
        data = []
        for row_index, row in enumerate(rows):
            data.append([self._p(cell, header and row_index == 0) for cell in row])
        table = Table(data, colWidths=list(widths), repeatRows=1 if header else 0)
        style = [
            ("FONTNAME", (0, 0), (-1, -1), self.font_name),
            ("GRID", (0, 0), (-1, -1), 0.35, MID_GREY),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("BACKGROUND", (0, 0), (-1, -1), colors.white),
            ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.white, LIGHT_GREY]),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]
        if header:
            style.extend([
                ("BACKGROUND", (0, 0), (-1, 0), NAVY),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT_GREY]),
            ])
        else:
            style.append(("BACKGROUND", (0, 0), (0, -1), LIGHT_GREY))
        table.setStyle(TableStyle(style))
        return table

    def _risk_table(self, rows: Sequence[Sequence[Any]]) -> Table:
        table = self._table(rows, [4.6 * cm, 2.0 * cm, 3.0 * cm, 2.0 * cm, 3.8 * cm], header=True)
        for row_index, row in enumerate(rows[1:], start=1):
            heat = str(row[-1])
            if heat in {"高", "極高"}:
                color = RED
            elif heat == "中":
                color = AMBER
            else:
                color = GREEN
            table.setStyle(TableStyle([
                ("BACKGROUND", (4, row_index), (4, row_index), color),
                ("TEXTCOLOR", (4, row_index), (4, row_index), colors.white),
            ]))
        return table
