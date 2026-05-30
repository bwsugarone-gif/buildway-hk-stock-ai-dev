"""
core/news_localizer.py
News Traditional Chinese Localizer — v4.0 Hardening Layer

Rules:
- Display Traditional Chinese title first
- Original title in secondary position
- Never fabricate news content
- Rule-based translation for common financial terms
- Label replacements: Bull Case→樂觀情景, etc.
"""

import re

# ── Label Replacements ────────────────────────────────────────────────────────
LABEL_MAP = {
    "Bull Case":            "樂觀情景",
    "Bear Case":            "悲觀情景",
    "Base Case":            "基準情景",
    "Bull Market":          "牛市",
    "Bear Market":          "熊市",
    "Risk Analysis":        "風險分析",
    "Weighted Risk Score":  "加權風險評分",
    "Top 5 risks":          "主要風險",
    "Top 5 Risks":          "主要風險",
    "Heatmap":              "風險熱度",
    "HIGH":                 "高",
    "MEDIUM":               "中",
    "LOW":                  "低",
    "INVALID":              "無效",
    "Buy":                  "買入",
    "Hold":                 "持有",
    "Sell":                 "賣出",
    "Neutral":              "中性",
    "Outperform":           "跑贏大市",
    "Underperform":         "跑輸大市",
    "Strong Buy":           "強力買入",
    "Strong Sell":          "強力賣出",
    "Overweight":           "增持",
    "Underweight":          "減持",
    "Market Perform":       "與大市同步",
    "Price Target":         "目標價",
    "Earnings":             "業績",
    "Revenue":              "收入",
    "Profit":               "利潤",
    "Loss":                 "虧損",
    "Dividend":             "股息",
    "Buyback":              "回購",
    "IPO":                  "首次公開招股",
    "Merger":               "合併",
    "Acquisition":          "收購",
    "Analyst":              "分析師",
    "Upgrade":              "上調評級",
    "Downgrade":            "下調評級",
    "Guidance":             "業績指引",
    "Outlook":              "前景展望",
    "Q1": "第一季", "Q2": "第二季", "Q3": "第三季", "Q4": "第四季",
    "FY": "全年", "H1": "上半年", "H2": "下半年",
    "YoY": "按年", "QoQ": "按季", "MoM": "按月",
    "EPS": "每股盈利", "PE": "市盈率", "PB": "市帳率",
    "ROE": "股本回報率", "ROA": "資產回報率",
    "EBITDA": "息稅折舊攤銷前利潤",
    "FCF": "自由現金流",
    "GDP": "本地生產總值",
    "CPI": "消費物價指數",
    "Fed": "美聯儲",
    "PBOC": "中國人民銀行",
    "HKMA": "香港金融管理局",
    "SFC": "證監會",
    "CSRC": "中國證監會",
}

# ── Company Name Map (common HK stocks) ──────────────────────────────────────
COMPANY_NAME_MAP = {
    "Tencent":              "騰訊",
    "Alibaba":              "阿里巴巴",
    "HSBC":                 "匯豐控股",
    "China Mobile":         "中國移動",
    "AIA":                  "友邦保險",
    "Meituan":              "美團",
    "JD.com":               "京東",
    "JD":                   "京東",
    "China Overseas":       "中國海外發展",
    "China Resources Land": "華潤置地",
    "Longfor":              "龍湖集團",
    "CK Hutchison":         "長和",
    "Sun Hung Kai":         "新鴻基地產",
    "Henderson Land":       "恒基地產",
    "Hang Seng Bank":       "恒生銀行",
    "Bank of China":        "中國銀行",
    "ICBC":                 "工商銀行",
    "CCB":                  "建設銀行",
    "China Construction Bank": "建設銀行",
    "Agricultural Bank":    "農業銀行",
    "Ping An":              "平安保險",
    "China Life":           "中國人壽",
    "CNOOC":                "中海油",
    "PetroChina":           "中石油",
    "Sinopec":              "中石化",
    "BYD":                  "比亞迪",
    "Xiaomi":               "小米",
    "NetEase":              "網易",
    "Baidu":                "百度",
    "China Telecom":        "中國電信",
    "China Unicom":         "中國聯通",
    "CLP":                  "中電控股",
    "HK Electric":          "香港電燈",
    "MTR":                  "港鐵",
    "Cathay Pacific":       "國泰航空",
    "Galaxy Entertainment": "銀河娛樂",
    "Sands China":          "金沙中國",
    "Wynn Macau":           "永利澳門",
    "SJM":                  "澳博控股",
    "Melco":                "新濠博亞",
}

# ── Keyword-based title translation patterns ──────────────────────────────────
_PATTERNS = [
    # Earnings / Results
    (r"(?i)(reports?|posts?|announces?)\s+(record\s+)?(quarterly|annual|full.year|half.year)?\s*(earnings|results|profit|revenue|loss)",
     "公佈業績"),
    (r"(?i)(beats?|misses?|exceeds?)\s+(earnings|revenue|profit|estimates?|expectations?)",
     "業績超預期" if "beat" in "beats" else "業績遜預期"),
    (r"(?i)(earnings|revenue|profit)\s+(beat|miss|surprise)",
     "業績表現"),
    # Analyst actions
    (r"(?i)(upgrades?|raises?)\s+(to\s+)?(buy|outperform|overweight|strong buy)",
     "分析師上調評級"),
    (r"(?i)(downgrades?|cuts?|lowers?)\s+(to\s+)?(sell|underperform|underweight|neutral)",
     "分析師下調評級"),
    (r"(?i)(raises?|increases?|lifts?)\s+price\s+target",
     "分析師上調目標價"),
    (r"(?i)(cuts?|lowers?|reduces?)\s+price\s+target",
     "分析師下調目標價"),
    # Corporate actions
    (r"(?i)(announces?|launches?|completes?)\s+(share\s+)?(buyback|repurchase)",
     "宣佈股份回購"),
    (r"(?i)(declares?|announces?|raises?)\s+(special\s+|interim\s+|final\s+)?dividend",
     "宣佈派息"),
    (r"(?i)(merger|acquisition|takeover|deal|agreement)",
     "企業併購消息"),
    # Market / macro
    (r"(?i)(surges?|jumps?|soars?|rallies?|gains?)\s+(\d+%|\d+\s+percent)",
     "股價大幅上升"),
    (r"(?i)(falls?|drops?|slides?|plunges?|declines?)\s+(\d+%|\d+\s+percent)",
     "股價大幅下跌"),
    (r"(?i)(52.week|all.time)\s+(high|record)",
     "創52週新高"),
    (r"(?i)(52.week|all.time)\s+(low)",
     "創52週新低"),
    # Regulatory
    (r"(?i)(regulatory|regulator|investigation|probe|fine|penalty)",
     "監管動態"),
    (r"(?i)(approved?|approval|license|permit)",
     "獲批准許可"),
]


def _apply_company_names(text: str) -> str:
    """Replace English company names with Chinese equivalents."""
    for en, zh in COMPANY_NAME_MAP.items():
        text = re.sub(r'\b' + re.escape(en) + r'\b', zh, text, flags=re.IGNORECASE)
    return text


def _rule_translate(title: str) -> str:
    """
    Apply rule-based translation to generate a Chinese title.
    Returns a best-effort Chinese title, never fabricates content.
    """
    if not title or not title.strip():
        return "原文標題"

    # Try pattern matching
    for pattern, zh_label in _PATTERNS:
        if re.search(pattern, title):
            # Extract company name if present (first capitalized word sequence)
            company_match = re.match(r'^([A-Z][A-Za-z\s&\.]+?)[\s:,]', title)
            company_zh = ""
            if company_match:
                en_name = company_match.group(1).strip()
                company_zh = COMPANY_NAME_MAP.get(en_name, en_name)
            if company_zh:
                return f"{company_zh}：{zh_label}"
            return zh_label

    # Fallback: apply company name substitution and label map
    result = title
    result = _apply_company_names(result)
    for en, zh in LABEL_MAP.items():
        result = re.sub(r'\b' + re.escape(en) + r'\b', zh, result)

    # If still mostly English, prefix with "原文："
    english_ratio = len(re.findall(r'[a-zA-Z]', result)) / max(len(result), 1)
    if english_ratio > 0.5:
        return f"原文標題"

    return result


def localize_news_item(item: dict) -> dict:
    """
    Localize a single news item.
    Adds 'title_zh' field with Traditional Chinese title.
    Preserves original 'title' as 'title_original'.
    Never fabricates content.
    """
    original_title = item.get("title", "").strip()
    title_zh = item.get("title_zh", "").strip()

    # If already has Chinese title, use it
    if not title_zh:
        title_zh = _rule_translate(original_title)

    return {
        **item,
        "title_zh": title_zh,
        "title_original": original_title,
        # Display title: Chinese first
        "display_title": title_zh if title_zh and title_zh != "原文標題" else original_title,
    }


def localize_news_list(news_items: list) -> list:
    """Localize a list of news items."""
    if not news_items:
        return []
    return [localize_news_item(item) for item in news_items]


def replace_labels(text: str) -> str:
    """
    Replace English labels in any text string with Traditional Chinese equivalents.
    Used for UI labels, section headers, etc.
    """
    if not text:
        return text
    result = text
    for en, zh in LABEL_MAP.items():
        result = re.sub(r'\b' + re.escape(en) + r'\b', zh, result)
    return result
