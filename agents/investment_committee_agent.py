"""
agents/investment_committee_agent.py
Buildway Tech (HK) Limited — Investment Committee Agent
Role: Combine all agent outputs into a final investment committee verdict
Must not give guaranteed buy/sell signals — educational only
"""

from typing import Dict, Any, List
from core.utils import get_risk_label, get_risk_color, get_timestamp


class InvestmentCommitteeAgent:
    """
    Investment Committee Agent
    Synthesizes all agent outputs into a final IC-style verdict.
    Verdicts: 觀察名單 | 高風險 | 中性 | 正面 | 避免
    All output includes mandatory risk warnings.
    """

    AGENT_NAME = "投資委員會代理"
    AGENT_ROLE = "綜合所有代理分析，給出投資委員會風格的最終評估意見"

    VERDICTS = {
        "正面":   {"icon": "🟢", "color": "#27AE60", "description": "基本面及風險評估相對正面，可納入研究名單"},
        "觀察名單": {"icon": "🔵", "color": "#2980B9", "description": "具備一定投資價值，建議持續觀察等待更佳入場時機"},
        "中性":   {"icon": "🟡", "color": "#F39C12", "description": "正負因素相當，建議中性看待，等待更多數據"},
        "高風險": {"icon": "🟠", "color": "#E67E22", "description": "風險因素顯著，需謹慎評估，嚴格控制倉位"},
        "避免":   {"icon": "🔴", "color": "#C0392B", "description": "風險過高或基本面偏弱，建議暫時迴避"},
    }

    def deliberate(
        self,
        market_data: Dict[str, Any],
        financial_analysis: Dict[str, Any],
        risk_analysis: Dict[str, Any],
        news_analysis: Dict[str, Any],
        portfolio_analysis: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Main entry point. Run IC deliberation and produce final verdict.
        """
        ticker = market_data.get("ticker", "N/A")
        company_name = market_data.get("company_name", ticker)

        # Score each dimension for IC vote
        ic_scores = self._compute_ic_scores(
            market_data, financial_analysis, risk_analysis, news_analysis
        )

        # Determine verdict
        verdict = self._determine_verdict(ic_scores, risk_analysis)

        # Build investment thesis
        thesis = self._build_investment_thesis(
            market_data, financial_analysis, risk_analysis, news_analysis, verdict
        )

        # Key risks
        key_risks = self._identify_key_risks(risk_analysis, financial_analysis)

        # Key catalysts
        catalysts = self._identify_catalysts(news_analysis, financial_analysis)

        # Executive summary
        exec_summary = self._build_executive_summary(
            market_data, financial_analysis, risk_analysis, verdict, thesis
        )

        return {
            "ticker": ticker,
            "company_name": company_name,
            "is_demo": market_data.get("is_demo", True),
            "timestamp": get_timestamp(),
            "verdict": verdict,
            "verdict_meta": self.VERDICTS[verdict],
            "ic_scores": ic_scores,
            "investment_thesis": thesis,
            "key_risks": key_risks,
            "key_catalysts": catalysts,
            "executive_summary": exec_summary,
            "risk_warning": self._get_risk_warning(),
            "data_quality_note": self._data_quality_note(market_data),
        }

    def _compute_ic_scores(
        self,
        market_data: Dict[str, Any],
        financial_analysis: Dict[str, Any],
        risk_analysis: Dict[str, Any],
        news_analysis: Dict[str, Any],
    ) -> Dict[str, float]:
        """
        Score each IC dimension from 1 (very negative) to 10 (very positive).
        Note: higher = more positive/attractive here (opposite of risk score).
        """
        scores = {}

        # 1. Valuation attractiveness (10 = very cheap, 1 = very expensive)
        vr = financial_analysis.get("valuation_range", {})
        upside = vr.get("upside_to_mid", 0)
        if upside >= 0.30:
            scores["估值吸引力"] = 9
        elif upside >= 0.15:
            scores["估值吸引力"] = 7
        elif upside >= 0:
            scores["估值吸引力"] = 5
        elif upside >= -0.15:
            scores["估值吸引力"] = 3
        else:
            scores["估值吸引力"] = 1

        # 2. Financial health
        health = financial_analysis.get("health_score", {})
        scores["財務健康度"] = health.get("overall_score", 5)

        # 3. Risk level (inverted: low risk = high score)
        risk_score = risk_analysis.get("composite_risk_score", 5)
        scores["風險水平"] = 11 - risk_score  # invert: risk 1 -> score 10

        # 4. News sentiment
        sentiment = news_analysis.get("sentiment_analysis", {})
        sent_score = sentiment.get("score", 0.5)
        scores["市場情緒"] = round(sent_score * 10, 1)

        # 5. Dividend/income attractiveness
        dy = market_data.get("dividend_yield", 0) or 0
        if dy >= 0.07:
            scores["股息吸引力"] = 9
        elif dy >= 0.05:
            scores["股息吸引力"] = 7
        elif dy >= 0.03:
            scores["股息吸引力"] = 5
        elif dy > 0:
            scores["股息吸引力"] = 3
        else:
            scores["股息吸引力"] = 2

        return scores

    def _determine_verdict(
        self,
        ic_scores: Dict[str, float],
        risk_analysis: Dict[str, Any],
    ) -> str:
        """Determine IC verdict based on composite scores."""
        avg_score = sum(ic_scores.values()) / len(ic_scores)
        risk_score = risk_analysis.get("composite_risk_score", 5)

        # Override rules
        if risk_score >= 8.5:
            return "避免"
        if risk_score >= 7.5:
            return "高風險"

        # Score-based verdict
        if avg_score >= 7.5:
            return "正面"
        elif avg_score >= 6.0:
            return "觀察名單"
        elif avg_score >= 4.5:
            return "中性"
        elif avg_score >= 3.0:
            return "高風險"
        else:
            return "避免"

    def _build_investment_thesis(
        self,
        market_data: Dict[str, Any],
        financial_analysis: Dict[str, Any],
        risk_analysis: Dict[str, Any],
        news_analysis: Dict[str, Any],
        verdict: str,
    ) -> List[str]:
        """Build 3-5 point investment thesis."""
        thesis = []
        ticker = market_data.get("ticker", "N/A")
        sector = market_data.get("sector", "")

        # Valuation point
        vr = financial_analysis.get("valuation_range", {})
        upside = vr.get("upside_to_mid", 0)
        if upside > 0.10:
            thesis.append(
                f"估值：基於多種估值方法，目標價中位數較現價有約 {upside*100:.0f}% 上行空間，"
                f"估值具備一定吸引力。"
            )
        elif upside < -0.10:
            thesis.append(
                f"估值：目前股價相對估值區間偏高，上行空間有限，需等待更佳入場時機。"
            )
        else:
            thesis.append(f"估值：目前股價處於合理估值區間，上行下行空間相對均衡。")

        # Financial health point
        health = financial_analysis.get("health_score", {})
        grade = health.get("grade", "C（一般）")
        thesis.append(f"財務健康：財務健康評級為 {grade}，" +
                      ("資產負債表穩健，現金流充裕。" if "A" in grade or "B" in grade else
                       "財務狀況一般，需關注盈利趨勢。"))

        # Risk point
        risk_score = risk_analysis.get("composite_risk_score", 5)
        risk_label = get_risk_label(int(risk_score))
        thesis.append(f"風險評估：綜合風險評分 {risk_score}/10（{risk_label}），" +
                      ("主要風險可控，適合風險承受能力匹配的投資者。" if risk_score <= 6 else
                       "風險因素較多，需嚴格控制倉位及設定止損。"))

        # Sector/macro point
        thesis.append(
            f"行業前景：{sector}行業在香港市場的中期展望，"
            f"需持續關注宏觀政策、利率環境及地緣政治因素的影響。"
        )

        # Sentiment point
        sentiment = news_analysis.get("sentiment_analysis", {})
        sent_label = sentiment.get("label", "中性")
        thesis.append(f"市場情緒：當前市場情緒偏向{sent_label}，" +
                      ("短期催化劑有望支撐股價。" if sent_label == "正面" else
                       "建議等待情緒改善後再考慮建倉。" if sent_label == "負面" else
                       "缺乏明顯短期催化劑，以基本面為主要考量。"))

        return thesis

    def _identify_key_risks(
        self,
        risk_analysis: Dict[str, Any],
        financial_analysis: Dict[str, Any],
    ) -> List[Dict[str, str]]:
        """Identify and rank top 5 key risks."""
        dimension_scores = risk_analysis.get("dimension_scores", {})
        narratives = risk_analysis.get("narratives", {})

        # Sort by risk score (highest first)
        sorted_risks = sorted(
            dimension_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]

        risks = []
        for dim, score in sorted_risks:
            risks.append({
                "dimension": dim,
                "score": score,
                "level": get_risk_label(score),
                "narrative": narratives.get(dim, ""),
                "mitigation": self._get_mitigation(dim),
            })

        return risks

    def _get_mitigation(self, risk_dimension: str) -> str:
        """Return mitigation strategy for each risk dimension."""
        mitigations = {
            "流動性風險": "關注公司現金流報告，確保短期債務有充足覆蓋",
            "債務風險": "監控利率變化對利息支出的影響，關注再融資計劃",
            "現金流風險": "追蹤季度自由現金流趨勢，關注資本開支計劃",
            "市場風險": "設定止損位，考慮分批建倉以降低時機風險",
            "政策風險": "密切關注監管公告，分散行業配置以降低集中風險",
            "香港行業風險": "關注港股市場流動性及南向資金動向",
            "下行情景風險": "設定嚴格止損，控制單一倉位不超過建議比例",
        }
        return mitigations.get(risk_dimension, "持續監控相關風險因素")

    def _identify_catalysts(
        self,
        news_analysis: Dict[str, Any],
        financial_analysis: Dict[str, Any],
    ) -> List[str]:
        """Identify key positive catalysts."""
        catalysts = []

        # From news positive factors
        for factor in news_analysis.get("positive_factors", [])[:3]:
            catalysts.append(f"📰 {factor}")

        # From financial analysis
        vr = financial_analysis.get("valuation_range", {})
        if vr.get("upside_to_high", 0) > 0.20:
            catalysts.append("📊 估值重估空間：若業績超預期，估值倍數有望擴張")

        health = financial_analysis.get("health_score", {})
        if health.get("overall_score", 0) >= 7:
            catalysts.append("💰 強勁財務基礎：健康的資產負債表支持股息增長或回購")

        if not catalysts:
            catalysts.append("⏳ 目前缺乏明顯短期催化劑，以長期基本面為主要考量")

        return catalysts[:5]

    def _build_executive_summary(
        self,
        market_data: Dict[str, Any],
        financial_analysis: Dict[str, Any],
        risk_analysis: Dict[str, Any],
        verdict: str,
        thesis: List[str],
    ) -> str:
        """Build a 3-paragraph executive summary."""
        ticker = market_data.get("ticker", "N/A")
        name = market_data.get("company_name", ticker)
        price = market_data.get("current_price", 0)
        sector = market_data.get("sector", "")
        risk_score = risk_analysis.get("composite_risk_score", 5)
        verdict_meta = self.VERDICTS[verdict]

        vr = financial_analysis.get("valuation_range", {})
        low = vr.get("low", 0)
        high = vr.get("high", 0)

        para1 = (
            f"{name}（{ticker}）是一家在香港交易所上市的{sector}企業，"
            f"現價 HK${price:.2f}。"
            f"本次分析基於多代理系統對其市場數據、財務狀況、風險因素及市場情緒的綜合評估。"
        )

        para2 = (
            f"財務分析顯示，估值區間約為 HK${low:.2f} 至 HK${high:.2f}，"
            f"財務健康評級為 {financial_analysis.get('health_score', {}).get('grade', 'N/A')}。"
            f"綜合風險評分為 {risk_score}/10（{get_risk_label(int(risk_score))}）。"
        )

        para3 = (
            f"投資委員會綜合評估結論：{verdict_meta['icon']} {verdict} — "
            f"{verdict_meta['description']}。"
            f"本報告僅供教育及參考用途，不構成任何投資建議。"
            f"投資者在作出任何投資決定前，應諮詢持牌財務顧問。"
        )

        return f"{para1}\n\n{para2}\n\n{para3}"

    def _get_risk_warning(self) -> str:
        return (
            "⚠️ 重要風險警告：\n"
            "本報告由 AI 系統生成，僅供教育及參考用途。\n"
            "• 本報告不構成投資建議、買賣邀請或財務意見\n"
            "• 投資涉及風險，股票價格可升可跌，投資者可能損失全部投資\n"
            "• 過往表現不代表未來回報\n"
            "• DEV版本數據可能包含示範數據，並非實時市場數據\n"
            "• 請在作出任何投資決定前諮詢持牌財務顧問"
        )

    def _data_quality_note(self, market_data: Dict[str, Any]) -> str:
        if market_data.get("is_demo"):
            return "⚠️ 本報告使用示範數據（DEV版本）。實際分析需使用實時市場數據。"
        return "✅ 本報告使用實時市場數據（Yahoo Finance）。"
