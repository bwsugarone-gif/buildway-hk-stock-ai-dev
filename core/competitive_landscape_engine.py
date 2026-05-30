"""
core/competitive_landscape_engine.py
Competitive Landscape Engine — peer comparison for HK stocks.
Never blank: if data is partial, show partial verified data with source labels.
No hallucinated company data. Uses hk_stock_master_data.json as peer reference.
"""
from __future__ import annotations
import json
import os
from typing import Any, Dict, List, Optional
from core.safe_math import safe_number

# Path to master data
_MASTER_DATA_PATH = os.path.join(
    os.path.dirname(__file__), "..", "data", "hk_stock_master_data.json"
)

# Sector peer groups (ticker -> list of peer tickers)
SECTOR_PEERS: Dict[str, List[str]] = {
    # Telecom
    "0941": ["0728", "0762"],
    "0728": ["0941", "0762"],
    "0762": ["0941", "0728"],
    # Banking
    "0005": ["0011", "0023", "2388"],
    "0011": ["0005", "0023", "2388"],
    "0023": ["0005", "0011", "2388"],
    "2388": ["0005", "0011", "0023"],
    # Tech / Internet
    "0700": ["9988", "9618", "3690"],
    "9988": ["0700", "9618", "3690"],
    "9618": ["0700", "9988", "3690"],
    "3690": ["0700", "9988", "9618"],
    # Insurance
    "0688": ["2318", "0945", "1336"],
    "2318": ["0688", "0945", "1336"],
    # Property
    "0016": ["0012", "0083", "0101"],
    "0012": ["0016", "0083", "0101"],
    # Energy
    "0857": ["0883", "0386"],
    "0883": ["0857", "0386"],
    "0386": ["0857", "0883"],
    # Default fallback — HSI blue chips
    "_default": ["0700", "0005", "0941", "0388", "1299"],
}

# Comparison metrics display names
METRIC_LABELS = {
    "pe_ratio":       "市盈率 (P/E)",
    "pb_ratio":       "市帳率 (P/B)",
    "dividend_yield": "股息率",
    "market_cap":     "市值",
    "roe":            "ROE",
    "net_margin":     "淨利率",
    "revenue":        "收入",
    "risk_score":     "風險評分",
}


def _load_master_data() -> Dict[str, Any]:
    try:
        with open(_MASTER_DATA_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _get_peer_tickers(ticker: str) -> List[str]:
    """Return up to 3 peer tickers for the given ticker."""
    t = ticker.lstrip("0").zfill(4)
    peers = SECTOR_PEERS.get(t) or SECTOR_PEERS.get(ticker)
    if not peers:
        peers = SECTOR_PEERS["_default"]
    # Exclude self
    peers = [p for p in peers if p != t and p != ticker]
    return peers[:3]


def _fmt_metric(value: Any, metric: str) -> str:
    """Format a metric value for display."""
    n = safe_number(value)
    if n == 0:
        return "N/A"
    if metric == "pe_ratio":
        return f"{n:.1f}x"
    if metric == "pb_ratio":
        return f"{n:.2f}x"
    if metric == "dividend_yield":
        return f"{n:.1f}%"
    if metric == "market_cap":
        if n >= 1e12:
            return f"HK${n/1e12:.1f}兆"
        if n >= 1e8:
            return f"HK${n/1e8:.0f}億"
        return f"HK${n:,.0f}"
    if metric in ("roe", "net_margin"):
        return f"{n:.1f}%"
    if metric == "revenue":
        if n >= 1e8:
            return f"HK${n/1e8:.0f}億"
        return f"HK${n:,.0f}"
    if metric == "risk_score":
        return f"{n:.1f}/10"
    return str(n)


def _build_peer_record(ticker: str, master: Dict[str, Any], report_data: Dict[str, Any]) -> Dict:
    """Build a peer comparison record for one ticker."""
    # Try master data first
    stock_info = master.get(ticker) or master.get(ticker.lstrip("0").zfill(4)) or {}

    record: Dict[str, Any] = {
        "ticker": ticker,
        "company_name": stock_info.get("name") or stock_info.get("company_name") or f"股票 {ticker}",
        "source": "公司基本資料",
        "metrics": {},
        "data_quality": "partial",
    }

    metrics_found = 0
    for metric in METRIC_LABELS:
        val = stock_info.get(metric)
        if val is not None and safe_number(val) != 0:
            record["metrics"][metric] = {
                "value": safe_number(val),
                "display": _fmt_metric(val, metric),
                "label": METRIC_LABELS[metric],
            }
            metrics_found += 1

    record["data_quality"] = "full" if metrics_found >= 5 else ("partial" if metrics_found >= 2 else "minimal")
    record["metrics_count"] = metrics_found
    return record


def _build_subject_record(ticker: str, report_data: Dict[str, Any]) -> Dict:
    """Build the subject stock record from live report_data."""
    flat: Dict[str, Any] = {}
    for key in ("report_metadata", "market_data", "financial_analysis",
                "financial_history", "risk_analysis"):
        sub = report_data.get(key)
        if isinstance(sub, dict):
            flat.update(sub)
    flat.update({k: v for k, v in report_data.items() if not isinstance(v, dict)})

    company_name = (
        flat.get("company_name")
        or flat.get("name")
        or f"股票 {ticker}"
    )

    record: Dict[str, Any] = {
        "ticker": ticker,
        "company_name": company_name,
        "source": "即時分析數據",
        "metrics": {},
        "data_quality": "live",
    }

    metrics_found = 0
    for metric in METRIC_LABELS:
        val = flat.get(metric)
        if val is not None and safe_number(val) != 0:
            record["metrics"][metric] = {
                "value": safe_number(val),
                "display": _fmt_metric(val, metric),
                "label": METRIC_LABELS[metric],
            }
            metrics_found += 1

    # Also try risk_score from risk_analysis
    risk_raw = safe_number(flat.get("composite_score_raw"))
    if risk_raw > 0 and "risk_score" not in record["metrics"]:
        record["metrics"]["risk_score"] = {
            "value": risk_raw,
            "display": _fmt_metric(risk_raw, "risk_score"),
            "label": METRIC_LABELS["risk_score"],
        }
        metrics_found += 1

    record["metrics_count"] = metrics_found
    return record


def _compute_advantages(subject: Dict, peers: List[Dict]) -> Dict[str, List[str]]:
    """Compare subject vs peers and identify advantages/disadvantages."""
    advantages = []
    disadvantages = []

    for metric in ["pe_ratio", "pb_ratio", "dividend_yield", "roe", "net_margin"]:
        subj_val = subject["metrics"].get(metric, {}).get("value", 0)
        if subj_val == 0:
            continue

        peer_vals = [
            p["metrics"].get(metric, {}).get("value", 0)
            for p in peers
            if p["metrics"].get(metric, {}).get("value", 0) != 0
        ]
        if not peer_vals:
            continue

        peer_avg = sum(peer_vals) / len(peer_vals)
        label = METRIC_LABELS.get(metric, metric)

        # Lower is better for pe, pb, risk_score
        if metric in ("pe_ratio", "pb_ratio", "risk_score"):
            if subj_val < peer_avg * 0.85:
                advantages.append(f"{label} {_fmt_metric(subj_val, metric)} 低於同業均值 {_fmt_metric(peer_avg, metric)}，估值較具吸引力")
            elif subj_val > peer_avg * 1.15:
                disadvantages.append(f"{label} {_fmt_metric(subj_val, metric)} 高於同業均值 {_fmt_metric(peer_avg, metric)}，估值偏貴")
        # Higher is better for dividend_yield, roe, net_margin
        else:
            if subj_val > peer_avg * 1.15:
                advantages.append(f"{label} {_fmt_metric(subj_val, metric)} 優於同業均值 {_fmt_metric(peer_avg, metric)}")
            elif subj_val < peer_avg * 0.85:
                disadvantages.append(f"{label} {_fmt_metric(subj_val, metric)} 低於同業均值 {_fmt_metric(peer_avg, metric)}")

    if not advantages:
        advantages = ["同業比較數據不足，無法確認明顯優勢"]
    if not disadvantages:
        disadvantages = ["同業比較數據不足，無法確認明顯劣勢"]

    return {"advantages": advantages[:3], "disadvantages": disadvantages[:3]}


def build_competitive_landscape(ticker: str, report_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build a competitive landscape comparison for the given ticker.
    Never returns blank — always shows at least partial verified data.
    """
    master = _load_master_data()
    peer_tickers = _get_peer_tickers(ticker)

    subject = _build_subject_record(ticker, report_data)
    peers = [_build_peer_record(pt, master, report_data) for pt in peer_tickers]

    # Filter out peers with zero metrics
    peers_with_data = [p for p in peers if p["metrics_count"] > 0]
    peers_minimal = [p for p in peers if p["metrics_count"] == 0]

    # For peers with no data, still show them with N/A
    for p in peers_minimal:
        p["note"] = "數據待補充"

    all_peers = peers_with_data + peers_minimal

    comparison_table = []
    for metric in ["pe_ratio", "pb_ratio", "dividend_yield", "market_cap", "roe", "risk_score"]:
        row = {
            "metric": METRIC_LABELS.get(metric, metric),
            "metric_id": metric,
            "subject": subject["metrics"].get(metric, {}).get("display", "N/A"),
        }
        for p in all_peers:
            row[p["ticker"]] = p["metrics"].get(metric, {}).get("display", "N/A")
        comparison_table.append(row)

    adv = _compute_advantages(subject, peers_with_data) if peers_with_data else {
        "advantages": ["同業數據不足，無法比較"],
        "disadvantages": ["同業數據不足，無法比較"],
    }

    return {
        "subject": subject,
        "peers": all_peers,
        "peer_tickers": peer_tickers,
        "comparison_table": comparison_table,
        "advantages": adv["advantages"],
        "disadvantages": adv["disadvantages"],
        "data_note": (
            "同業數據來源：公司基本資料庫"
            if peers_with_data
            else "同業數據不足，顯示部分已驗證資料"
        ),
        "peer_count": len(all_peers),
    }
