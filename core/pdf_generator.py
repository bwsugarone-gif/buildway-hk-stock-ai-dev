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

PDF_SYMBOL_STRIP = ("🟢", "🟡", "🔴", "✅", "❌", "⚠️", "⚠")


def _pdf_text(value: Any) -> str:
    text = str(value if value not in (None, "") else "N/A")
    for symbol in PDF_SYMBOL_STRIP:
        text = text.replace(symbol, "")
    return text.strip()


def _pdf_confidence_label(value: Any, level: Any = "") -> str:
    text = _pdf_text(value)
    level_text = str(level or "").upper()
    if "HIGH" in level_text or "高可信度" in text:
        return "高可信度"
    if "INVALID" in level_text or "資料驗證未完成" in text or "無法確認" in text:
        return "資料驗證未完成"
    if "MEDIUM" in level_text or "LOW" in level_text or "部分資料缺失" in text:
        return "部分資料缺失"
    return text or "部分資料缺失"


class FontManager:
    """Register a Unicode-compatible Traditional Chinese font for ReportLab.

    Font search order:
    1. assets/fonts/ bundled TTF files (highest priority — cross-platform)
    2. Auto-download NotoSansTC from Google Fonts CDN (Streamlit Cloud / any platform)
    3. Windows system fonts (local Windows fallback)
    4. Last resort: Helvetica (no CJK — shows boxes for Chinese)
    """

    # Resolved path for bundled fonts (relative to this file's package root)
    _BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    _FONTS_DIR = os.path.join(_BASE_DIR, "assets", "fonts")

    # Google Fonts CDN URLs for NotoSansTC (subset with Traditional Chinese coverage)
    # These are stable static URLs that work without an API key
    NOTO_URLS = {
        "NotoSansTC-Regular.ttf": (
            "https://github.com/google/fonts/raw/main/ofl/notosanstc/NotoSansTC%5Bwght%5D.ttf"
        ),
        "NotoSansTC-Bold.ttf": (
            "https://github.com/google/fonts/raw/main/ofl/notosanstc/NotoSansTC%5Bwght%5D.ttf"
        ),
    }

    # (font_name, filename_under_assets_fonts, is_bold)
    BUNDLED = [
        ("NotoSansTC",     "NotoSansTC-Regular.ttf", False),
        ("NotoSansTCBold", "NotoSansTC-Bold.ttf",    True),
    ]

    # Windows system fonts (fallback for local dev without bundled fonts)
    WINDOWS_CANDIDATES = [
        ("MicrosoftJhengHei",     r"C:\Windows\Fonts\msjh.ttc",   False),
        ("MicrosoftJhengHeiUI",   r"C:\Windows\Fonts\msjhl.ttc",  False),
        ("MicrosoftJhengHeiBold", r"C:\Windows\Fonts\msjhbd.ttc", True),
        ("NotoSansCJKTC",         r"C:\Windows\Fonts\NotoSansCJKtc-Regular.otf", False),
        ("SourceHanSansTC",       r"C:\Windows\Fonts\SourceHanSansTC-Regular.otf", False),
        ("MingLiU",               r"C:\Windows\Fonts\mingliu.ttc", False),
    ]

    @classmethod
    def _ensure_fonts_dir(cls) -> None:
        os.makedirs(cls._FONTS_DIR, exist_ok=True)

    @classmethod
    def _try_download_noto(cls) -> bool:
        """Attempt to download NotoSansTC variable font from GitHub.
        Returns True if at least the regular font is available after download."""
        import urllib.request
        cls._ensure_fonts_dir()
        # The variable font file serves as both regular and bold
        vf_filename = "NotoSansTC-Regular.ttf"
        vf_path = os.path.join(cls._FONTS_DIR, vf_filename)
        bold_path = os.path.join(cls._FONTS_DIR, "NotoSansTC-Bold.ttf")

        if os.path.exists(vf_path) and os.path.getsize(vf_path) > 100_000:
            print(f"[FontManager] Bundled font already present: {vf_path}")
            # Also ensure bold symlink/copy exists
            if not os.path.exists(bold_path):
                import shutil
                shutil.copy2(vf_path, bold_path)
            return True

        url = cls.NOTO_URLS[vf_filename]
        try:
            print(f"[FontManager] Downloading NotoSansTC from GitHub...")
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = resp.read()
            if len(data) < 100_000:
                print(f"[FontManager] Download too small ({len(data)} bytes), skipping.")
                return False
            with open(vf_path, "wb") as f:
                f.write(data)
            # Use same file for bold (variable font covers all weights)
            import shutil
            shutil.copy2(vf_path, bold_path)
            print(f"[FontManager] Downloaded NotoSansTC ({len(data)//1024}KB) → {vf_path}")
            return True
        except Exception as exc:
            print(f"[FontManager] Download failed: {exc}")
            return False

    @classmethod
    def setup(cls) -> tuple[str, str]:
        primary = None
        bold = None

        # ── 1. Try bundled fonts ──────────────────────────────────────────────
        for name, filename, is_bold in cls.BUNDLED:
            path = os.path.join(cls._FONTS_DIR, filename)
            if not os.path.exists(path) or os.path.getsize(path) < 100_000:
                continue
            try:
                pdfmetrics.registerFont(TTFont(name, path))
                print(f"[FontManager] Registered bundled font: {name}")
                if is_bold and bold is None:
                    bold = name
                elif not is_bold and primary is None:
                    primary = name
            except Exception as e:
                print(f"[FontManager] Failed to register {name}: {e}")

        # ── 2. Auto-download if still missing ────────────────────────────────
        if primary is None:
            downloaded = cls._try_download_noto()
            if downloaded:
                for name, filename, is_bold in cls.BUNDLED:
                    path = os.path.join(cls._FONTS_DIR, filename)
                    if not os.path.exists(path):
                        continue
                    try:
                        pdfmetrics.registerFont(TTFont(name, path))
                        print(f"[FontManager] Registered downloaded font: {name}")
                        if is_bold and bold is None:
                            bold = name
                        elif not is_bold and primary is None:
                            primary = name
                    except Exception as e:
                        print(f"[FontManager] Failed to register downloaded {name}: {e}")

        # ── 3. Windows system fonts ───────────────────────────────────────────
        if primary is None:
            for name, path, is_bold in cls.WINDOWS_CANDIDATES:
                if not os.path.exists(path):
                    continue
                try:
                    pdfmetrics.registerFont(TTFont(name, path))
                    print(f"[FontManager] Registered Windows font: {name}")
                    if is_bold and bold is None:
                        bold = name
                    elif not is_bold and primary is None:
                        primary = name
                except Exception as e:
                    print(f"[FontManager] Failed to register {name}: {e}")
                if primary is not None and bold is not None:
                    break

        # ── 4. Last resort ────────────────────────────────────────────────────
        if primary is None:
            print("[FontManager] WARNING: No CJK font available. Chinese text will show as boxes in PDF.")
            primary = "Helvetica"
        if bold is None:
            bold = primary

        print(f"[FontManager] Using primary={primary}, bold={bold}")
        return primary, bold

    @classmethod
    def setup_traditional_chinese_fonts(cls) -> tuple[str, str]:
        """Backward-compatible alias for older font verification tests."""
        return cls.setup()


class PDFGenerator:
    """Render a nine-page institutional investment report."""

    def __init__(self, logo_path: str | None = None, build_version: str = ""):
        self.logo_path = str(logo_path) if logo_path else None
        self.font_name, self.bold_font_name = FontManager.setup()
        self.styles = self._styles()
        # Build version shown in PDF footer for cross-platform consistency checks
        try:
            from core.config import BUILD_VERSION
            self.build_version = BUILD_VERSION
        except Exception:
            self.build_version = build_version or ""

    def generate(self, report_sections: Dict[str, Any], output_path: str) -> str:
        cover = report_sections.get("cover", {})
        print(f"[PDF] stock_code = {cover.get('ticker', 'N/A')} | font = {self.font_name}")
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
        snapshot = report_sections.get("market_snapshot", {})
        if snapshot.get("is_valid"):
            story.extend(self._market_snapshot(snapshot))
            story.append(PageBreak())
        story.extend(self._company_intelligence(report_sections.get("company_intelligence", {})))
        story.append(PageBreak())
        story.extend(self._executive_summary(report_sections.get("executive_summary", {})))
        story.append(PageBreak())
        stability = report_sections.get("system_stability", {})
        if stability.get("has_failures"):
            story.extend(self._system_stability(stability))
            story.append(PageBreak())
        story.extend(self._multi_agent(report_sections.get("multi_agent_discussion", {})))
        story.append(PageBreak())
        story.extend(self._financial(report_sections.get("financial_analysis", {})))
        story.append(PageBreak())
        story.extend(self._risk(report_sections.get("risk_analysis", {})))
        story.append(PageBreak())
        story.extend(self._news_catalyst(report_sections.get("news_catalyst_analysis", {})))
        story.append(PageBreak())
        story.extend(self._scenario(report_sections.get("scenario_analysis", {})))
        story.append(PageBreak())
        story.extend(self._portfolio(report_sections.get("portfolio_view", {})))
        story.append(PageBreak())
        story.extend(self._conclusion(report_sections.get("ic_conclusion", {}), report_sections.get("disclaimer", {})))

        try:
            doc.build(story, onFirstPage=self._footer, onLaterPages=self._footer)
        except Exception as exc:
            print(f"[PDF] generation failed: {exc}")
            raise RuntimeError("PDF generation failed") from exc
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
        styles.add(ParagraphStyle(
            name="Notice",
            parent=styles["BodyText"],
            fontName=self.bold_font_name,
            fontSize=9,
            leading=13,
            textColor=TEXT,
            backColor=colors.HexColor("#FFF8E6"),
            borderColor=colors.HexColor("#E8C36A"),
            borderWidth=0.8,
            borderPadding=(7, 8, 7),
            spaceBefore=6,
            spaceAfter=9,
        ))
        return styles

    def _footer(self, canvas, doc):
        canvas.saveState()
        canvas.setFont(self.font_name, 8)
        canvas.setFillColor(MUTED)
        canvas.drawString(1.55 * cm, 1.0 * cm, "Buildway Tech (HK) Limited")
        # Centre: build version for cross-platform consistency verification
        if self.build_version:
            canvas.drawCentredString(A4[0] / 2, 1.0 * cm, self.build_version)
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

        confidence = _pdf_confidence_label(
            cover.get("data_confidence_label"),
            cover.get("data_confidence"),
        )
        rows = [
            ["Stock code", cover.get("ticker", "N/A")],
            ["Data confidence", confidence],
            ["Company name", cover.get("company_name", "N/A")],
            ["Industry", cover.get("sector", "N/A")],
            ["Core business", cover.get("business", "N/A")],
            ["Final committee rating", cover.get("final_rating", "N/A")],
            ["Risk score", f"{cover.get('risk_score', 'N/A')} - {cover.get('risk_label', '')}"],
            ["Report date", cover.get("report_date", "N/A")],
        ]
        if cover.get("data_completeness_note"):
            rows.append(["Data completeness", cover.get("data_completeness_note")])
        elements.append(self._table(rows, [5.0 * cm, 10.2 * cm], header=False))
        if cover.get("data_completeness_note"):
            elements.append(Spacer(1, 0.28 * cm))
            elements.append(self._notice(cover.get("data_completeness_note")))
        elements.append(Spacer(1, 1.0 * cm))
        elements.append(Paragraph("Client trial report generated by a Python-calculated multi-agent framework. DeepSeek is used only for optional narrative wording when enabled.", self.styles["SmallTC"]))
        return elements

    def _market_snapshot(self, section: Dict[str, Any]) -> List[Any]:
        elements = [self._title("市場快照 Market Snapshot")]
        ticker = _pdf_text(section.get("ticker", "N/A"))
        conf = _pdf_text(section.get("snapshot_confidence", ""))
        source = _pdf_text(section.get("data_source", ""))
        is_demo = section.get("is_demo", True)
        demo_tag = "示範數據" if is_demo else "實時數據"
        elements.append(Paragraph(
            f"{ticker} | 快照可信度：{conf} | 資料來源：{source} ({demo_tag})",
            self.styles["BodyTC"],
        ))
        elements.append(Spacer(1, 0.25 * cm))

        # Price section
        price_sec = section.get("price_section", {})
        if price_sec:
            elements.append(Paragraph("價格資料", self.styles["SubTitle"]))
            rows = [[k, v] for k, v in price_sec.items()]
            elements.append(self._table(rows, [4.5 * cm, 11.0 * cm]))
            elements.append(Spacer(1, 0.2 * cm))

        # Valuation section
        val_sec = section.get("valuation_section", {})
        if val_sec:
            elements.append(Paragraph("估值指標", self.styles["SubTitle"]))
            rows = [[k, v] for k, v in val_sec.items()]
            elements.append(self._table(rows, [4.5 * cm, 11.0 * cm]))
            elements.append(Spacer(1, 0.2 * cm))

        # Range section
        range_sec = section.get("range_section", {})
        if range_sec:
            elements.append(Paragraph("價格區間", self.styles["SubTitle"]))
            rows = [[k, v] for k, v in range_sec.items()]
            elements.append(self._table(rows, [4.5 * cm, 11.0 * cm]))

        elements.append(Spacer(1, 0.2 * cm))
        elements.append(Paragraph(
            "市場快照數值由 Python 從市場資料供應商提取，不由 LLM 生成。",
            self.styles["SmallTC"],
        ))
        return elements

    def _executive_summary(self, section: Dict[str, Any]) -> List[Any]:
        elements = [self._title("Executive Summary")]
        confidence = _pdf_confidence_label(section.get("data_confidence_label"))
        metric_rows = [
            ["Final rating", section.get("final_rating", "N/A")],
            ["Data confidence", confidence],
            ["Key risk", section.get("key_risk", "N/A")],
            ["Key opportunity", section.get("key_opportunity", "N/A")],
            ["Recommended action category", section.get("recommended_action", "N/A")],
        ]
        elements.append(self._table(metric_rows, [5.2 * cm, 10.2 * cm]))
        elements.append(Spacer(1, 0.35 * cm))
        if section.get("data_confidence_label"):
            elements.append(self._notice(f"資料可信度：{confidence}"))
        elements.append(Paragraph("重點摘要", self.styles["SubTitle"]))
        for bullet in section.get("bullets", []):
            elements.append(Paragraph(f"- {bullet}", self.styles["BodyTC"]))
        if section.get("llm_narrative"):
            elements.extend([Spacer(1, 0.2 * cm), Paragraph(section["llm_narrative"], self.styles["BodyTC"])])
        return elements

    def _company_intelligence(self, section: Dict[str, Any]) -> List[Any]:
        elements = [self._title(section.get("title", "公司基本面與業務分析"))]
        rows = []
        for label, value in section.get("rows", []):
            clean_label = _pdf_text(label)
            clean_value = _pdf_text(value)
            if "資料可信度" in clean_label:
                clean_value = _pdf_confidence_label(clean_value)
            rows.append([clean_label, clean_value])
        if not rows:
            rows = [["公司資料", "未能取得有效公司資料，系統已停止公司基本面敘述。"]]
        elements.append(self._table(rows, [4.0 * cm, 11.4 * cm]))
        return elements

    def _system_stability(self, section: Dict[str, Any]) -> List[Any]:
        elements = [self._title(section.get("title", "系統穩定性提示"))]
        elements.append(Paragraph(section.get("message", ""), self.styles["BodyTC"]))
        failed_agents = section.get("failed_agents", [])
        if failed_agents:
            rows = [["受影響模組"]] + [[agent] for agent in failed_agents]
            elements.append(self._table(rows, [15.4 * cm], header=True))
            elements.append(Spacer(1, 0.25 * cm))
            elements.append(Paragraph("部分分析結果可能受限制。", self.styles["SmallTC"]))
        return elements

    def _multi_agent(self, section: Dict[str, Any]) -> List[Any]:
        elements = [self._title(section.get("title", "Multi-Agent 投資委員會討論摘要"))]
        rows = [["Agent", "性格定位", "核心觀點", "正面因素", "主要憂慮", "信心分數", "對評級影響"]]
        for item in section.get("table", []):
            rows.append([
                item.get("Agent", item.get("agent", "")),
                item.get("性格定位", ""),
                item.get("核心觀點", item.get("core_view", "")),
                item.get("正面因素", ""),
                item.get("主要憂慮", item.get("risk_warning", "")),
                item.get("信心分數", ""),
                item.get("對評級影響", item.get("impact", "")),
            ])
        elements.append(self._table(rows, [1.8 * cm, 2.2 * cm, 3.2 * cm, 2.4 * cm, 2.7 * cm, 1.4 * cm, 1.7 * cm], header=True))
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
        if len(rows) > 1:
            elements.append(self._risk_table(rows))
        else:
            elements.append(self._notice("資料驗證未完成，風險維度評分已停止。"))
        elements.extend([Spacer(1, 0.3 * cm), Paragraph("Top 5 risks", self.styles["SubTitle"])])
        top_risks = section.get("top_risks", [])[:5]
        if top_risks:
            for item in top_risks:
                elements.append(Paragraph(f"- {item['dimension']}: {item['score']}/10, {item['level']}", self.styles["BodyTC"]))
        else:
            elements.append(Paragraph("無可用風險項目。", self.styles["BodyTC"]))
        return elements

    def _news_catalyst(self, section: Dict[str, Any]) -> List[Any]:
        elements = [self._title(section.get("title", "新聞與事件催化分析"))]
        rows = [
            ["新聞資料狀態", section.get("status", "暫未接入即時新聞資料")],
            ["新聞可信度", section.get("news_confidence", "未接入")],
            ["分析邊界", section.get("analysis_boundary", "暫未接入即時新聞資料，本節不生成未經驗證的新聞或事件。")],
        ]
        elements.append(self._table(rows, [4.2 * cm, 11.2 * cm]))
        if not section.get("has_news"):
            elements.append(Spacer(1, 0.3 * cm))
            elements.append(self._notice("暫未接入即時新聞資料，本節不生成未經驗證的新聞或事件。"))

        groups = [
            ("正面催化", section.get("positive_catalysts", [])),
            ("負面催化", section.get("negative_catalysts", [])),
            ("監察事項", section.get("risk_events", []) or section.get("monitor_items", [])),
        ]
        for title, items in groups:
            elements.append(Spacer(1, 0.25 * cm))
            elements.append(Paragraph(title, self.styles["SubTitle"]))
            if items:
                for item in items[:6]:
                    elements.append(Paragraph(f"- {item}", self.styles["BodyTC"]))
            else:
                elements.append(Paragraph("暫無已驗證資料。", self.styles["BodyTC"]))
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
        if section.get("data_completeness_note"):
            elements.append(self._notice(section["data_completeness_note"]))
        if section.get("llm_warning"):
            elements.append(Paragraph(section["llm_warning"], self.styles["SmallTC"]))
        elements.extend([
            Spacer(1, 0.25 * cm),
            Paragraph(disclaimer.get("title", "Disclaimer"), self.styles["SubTitle"]),
            Paragraph(disclaimer.get("content", ""), self.styles["SmallTC"]),
        ])
        return elements

    def _title(self, text: str) -> Paragraph:
        return Paragraph(_pdf_text(text), self.styles["SectionTitle"])

    def _notice(self, text: Any) -> Paragraph:
        return Paragraph(_pdf_text(text).replace("\n", "<br/>"), self.styles["Notice"])

    def _p(self, value: Any, header: bool = False) -> Paragraph:
        style = self.styles["TableHeaderTC"] if header else self.styles["TableTC"]
        return Paragraph(_pdf_text(value).replace("\n", "<br/>"), style)

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
