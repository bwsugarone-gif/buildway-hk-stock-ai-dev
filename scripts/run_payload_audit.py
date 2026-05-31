"""
scripts/run_payload_audit.py
FOS V4.0.3 Payload Audit — generates debug_audit JSON files for 12345, 0941, 3416
Run from buildway-hk-stock-ai/ directory:
    python scripts/run_payload_audit.py
"""
import sys
import os
import json
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.source_registry import build_source_registry, get_verified_sources, compute_coverage_pct, compute_confidence_level
from core.source_transparency import build_source_transparency
from core.competitive_landscape_engine import build_competitive_landscape, _load_master_data, _normalize_ticker
from core.agent_opinion_engine import build_agent_opinions

OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "debug_audit")
os.makedirs(OUT_DIR, exist_ok=True)

NOW = datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# ─── Mock report packages ─────────────────────────────────────────────────────

def make_invalid_package():
    """12345 — completely invalid ticker, no real data should exist."""
    return {
        "report_metadata": {
            "stock_code": "12345",
            "ticker": "12345",
            "generated_at": NOW,
            "data_confidence": "INVALID",
        },
        "market_data": {
            "ticker": "12345",
            "current_price": None,
            "pe_ratio": None,
            "pb_ratio": None,
            "dividend_yield": None,
            "market_cap": None,
            "fifty_two_week_high": None,
            "fifty_two_week_low": None,
            "volume": None,
            "beta": None,
            "company_name": "",
            "company_name_zh": "",
            "company_name_en": "",
            "sector": "",
        },
        "company_metadata": {},
        "financial_analysis": {},
        "financial_history": {},
        "risk_analysis": {},
        "news_analysis": {},
        "investment_committee": {},
    }


def make_0941_package():
    """0941.HK — China Mobile, real HK telecom stock."""
    return {
        "report_metadata": {
            "stock_code": "0941",
            "ticker": "0941.HK",
            "generated_at": NOW,
            "data_confidence": "HIGH",
        },
        "market_data": {
            "ticker": "0941.HK",
            "current_price": 72.5,
            "pe_ratio": 11.2,
            "pb_ratio": 1.3,
            "dividend_yield": 6.8,
            "market_cap": 1450000000000,
            "fifty_two_week_high": 82.0,
            "fifty_two_week_low": 58.0,
            "volume": 25000000,
            "beta": 0.75,
            "company_name": "中國移動",
            "company_name_zh": "中國移動有限公司",
            "company_name_en": "China Mobile Limited",
            "sector": "電訊",
        },
        "company_metadata": {
            "name_zh": "中國移動有限公司",
            "name_en": "China Mobile Limited",
            "sector": "電訊",
            "business_profile": "中國最大移動電話服務供應商",
            "market_category": "主板",
        },
        "financial_analysis": {
            "revenue": 938000000000,
            "net_profit": 125000000000,
            "roe": 11.5,
            "net_margin": 13.3,
            "gross_margin": 58.0,
            "ebitda": 380000000000,
            "free_cash_flow": 95000000000,
            "total_assets": 2100000000000,
            "total_debt": 450000000000,
        },
        "financial_history": {},
        "risk_analysis": {
            "composite_score_raw": 4.2,
            "risk_label": "中等風險",
            "risk_items": [
                {"risk_name": "監管風險", "score_raw": 5.0, "score": "5.0/10", "level": "中等風險"},
                {"risk_name": "競爭風險", "score_raw": 4.5, "score": "4.5/10", "level": "中等風險"},
            ],
        },
        "news_analysis": {
            "items": [
                {"title": "中國移動5G用戶突破5億", "source": "Reuters"},
                {"title": "中移動派息增加", "source": "Bloomberg"},
            ],
            "news_sentiment": "positive",
        },
        "investment_committee": {
            "bull_score": 68,
            "bear_score": 42,
        },
    }


def make_3416_package():
    """3416.HK — partial data scenario."""
    return {
        "report_metadata": {
            "stock_code": "3416",
            "ticker": "3416.HK",
            "generated_at": NOW,
            "data_confidence": "MEDIUM",
        },
        "market_data": {
            "ticker": "3416.HK",
            "current_price": 3.2,
            "pe_ratio": None,
            "pb_ratio": 0.8,
            "dividend_yield": None,
            "market_cap": 850000000,
            "fifty_two_week_high": 4.5,
            "fifty_two_week_low": 2.8,
            "volume": 1200000,
            "beta": 1.1,
            "company_name": "保利協鑫能源",
            "company_name_zh": "保利協鑫能源控股有限公司",
            "company_name_en": "GCL-Poly Energy Holdings",
            "sector": "能源",
        },
        "company_metadata": {
            "name_zh": "保利協鑫能源控股有限公司",
            "name_en": "GCL-Poly Energy Holdings",
            "sector": "能源",
            "business_profile": "多晶矽及太陽能產品製造商",
            "market_category": "主板",
        },
        "financial_analysis": {
            "revenue": 28000000000,
            "net_profit": -2500000000,
            "roe": -8.5,
            "net_margin": -8.9,
            "gross_margin": 12.0,
            "ebitda": None,
            "free_cash_flow": -1800000000,
            "total_assets": 95000000000,
            "total_debt": 68000000000,
        },
        "financial_history": {},
        "risk_analysis": {
            "composite_score_raw": 7.8,
            "risk_label": "高風險",
            "risk_items": [
                {"risk_name": "財務風險", "score_raw": 8.5, "score": "8.5/10", "level": "高風險"},
                {"risk_name": "行業週期風險", "score_raw": 7.2, "score": "7.2/10", "level": "高風險"},
            ],
        },
        "news_analysis": {
            "items": [],
            "news_sentiment": "negative",
        },
        "investment_committee": {
            "bull_score": 28,
            "bear_score": 72,
        },
    }


# ─── Audit runner ─────────────────────────────────────────────────────────────

def audit_ticker(ticker: str, package: dict) -> dict:
    """Run all engines and capture raw payloads for audit."""
    audit = {
        "audit_meta": {
            "ticker": ticker,
            "audit_time": NOW,
            "audit_version": "FOS_V4.0.3",
        },
        "input_report_package_keys": list(package.keys()),
        "payloads": {},
        "ui_render_keys": {},
        "bugs_found": [],
    }

    # ── 1. source_registry payload ────────────────────────────────────────────
    try:
        sr = build_source_registry(package)
        verified_sources = get_verified_sources(sr)
        coverage_pct = compute_coverage_pct(sr)
        confidence_level = compute_confidence_level(sr)
        audit["payloads"]["source_registry"] = sr
        audit["ui_render_keys"]["source_registry"] = {
            "verified_sources": verified_sources,
            "coverage_pct": coverage_pct,
            "confidence_level": confidence_level,
            "market_data.verified": sr.get("market_data", {}).get("verified"),
            "company_metadata.verified": sr.get("company_metadata", {}).get("verified"),
            "financial_statement.verified": sr.get("financial_statement", {}).get("verified"),
            "news.verified": sr.get("news", {}).get("verified"),
        }
    except Exception as e:
        audit["payloads"]["source_registry"] = {"error": str(e)}
        audit["bugs_found"].append(f"source_registry CRASH: {e}")

    # ── 2. source_transparency payload ────────────────────────────────────────
    try:
        st = build_source_transparency(package)
        audit["payloads"]["source_transparency"] = st
        audit["ui_render_keys"]["source_transparency"] = {
            "coverage_pct": st.get("coverage_pct"),
            "confidence_level": st.get("confidence_level"),
            "sources_present": st.get("sources_present"),
            "sources_missing": st.get("sources_missing"),
            "data_gaps": st.get("data_gaps"),
        }
    except Exception as e:
        audit["payloads"]["source_transparency"] = {"error": str(e)}
        audit["bugs_found"].append(f"source_transparency CRASH: {e}")

    # ── 3. competitive_landscape payload ─────────────────────────────────────
    try:
        cl = build_competitive_landscape(ticker, package)
        audit["payloads"]["competitive_landscape"] = cl
        # Extract peer names for UI render check
        peer_names = []
        for p in cl.get("peers", []):
            peer_names.append({
                "ticker": p.get("ticker"),
                "company_name": p.get("company_name"),
                "metrics_count": p.get("metrics_count"),
                "data_quality": p.get("data_quality"),
            })
        audit["ui_render_keys"]["competitive_landscape"] = {
            "peer_tickers": cl.get("peer_tickers"),
            "peer_names": peer_names,
            "subject_company_name": cl.get("subject", {}).get("company_name"),
            "peer_count": cl.get("peer_count"),
            "data_note": cl.get("data_note"),
        }
        # Check if peer names are raw ticker codes (bug)
        for p in peer_names:
            name = p.get("company_name", "")
            t = p.get("ticker", "")
            if name == f"{t}.HK" or name == t:
                audit["bugs_found"].append(
                    f"PEER_NAME_BUG: peer {t} shows raw ticker '{name}' instead of company name"
                )
    except Exception as e:
        audit["payloads"]["competitive_landscape"] = {"error": str(e)}
        audit["bugs_found"].append(f"competitive_landscape CRASH: {e}")

    # ── 4. agent_opinions payload ─────────────────────────────────────────────
    try:
        ao = build_agent_opinions(package)
        audit["payloads"]["agent_opinions"] = ao
        opinions_summary = []
        for op in ao.get("opinions", []):
            opinions_summary.append({
                "agent_name": op.get("agent_name"),
                "stance": op.get("stance"),
                "confidence": op.get("confidence"),
                "data_points_used": op.get("data_points_used"),
                "key_points_count": len(op.get("key_points", [])),
            })
        audit["ui_render_keys"]["agent_opinions"] = {
            "committee_verdict": ao.get("committee_verdict"),
            "overall_confidence": ao.get("overall_confidence"),
            "bull_score": ao.get("bull_score"),
            "bear_score": ao.get("bear_score"),
            "agent_count": ao.get("agent_count"),
            "opinions_summary": opinions_summary,
        }
        # Check for 0% confidence or "觀點待整合" (bug)
        for op in ao.get("opinions", []):
            if op.get("confidence", 0) == 0:
                audit["bugs_found"].append(
                    f"ZERO_CONFIDENCE_BUG: {op.get('agent_name')} has 0% confidence"
                )
            stance = op.get("stance", "")
            if stance in ("觀點待整合", "", None):
                audit["bugs_found"].append(
                    f"EMPTY_STANCE_BUG: {op.get('agent_name')} has stance='{stance}'"
                )
    except Exception as e:
        audit["payloads"]["agent_opinions"] = {"error": str(e)}
        audit["bugs_found"].append(f"agent_opinions CRASH: {e}")

    # ── 5. fos_components UI render key check ─────────────────────────────────
    # Simulate what fos_components.render_source_transparency reads
    st_payload = audit["payloads"].get("source_transparency", {})
    cover_sim = {
        "data_confidence": package.get("report_metadata", {}).get("data_confidence", "LOW"),
    }
    audit["ui_render_keys"]["fos_render_source_transparency"] = {
        "level_read_from": "source_transparency.confidence_level",
        "level_value": st_payload.get("confidence_level"),
        "coverage_read_from": "source_transparency.coverage_pct",
        "coverage_value": st_payload.get("coverage_pct"),
        "sources_read_from": "source_transparency.sources_present",
        "sources_value": st_payload.get("sources_present"),
    }

    # Simulate what fos_components.render_multi_agent_committee reads
    ic_data = package.get("investment_committee", {})
    audit["ui_render_keys"]["fos_render_multi_agent_committee"] = {
        "ic_key_in_report_package": "investment_committee",
        "ic_agents_subkey": "agents",
        "ic_agents_value": ic_data.get("agents"),
        "NOTE": "render_multi_agent_committee reads ic['agents'][agent_key] — if 'agents' subkey missing, all show '觀點待整合'",
        "agents_key_present": "agents" in ic_data,
        "ic_keys_present": list(ic_data.keys()) if ic_data else [],
    }

    # ── 6. Bug summary for this ticker ────────────────────────────────────────
    audit["bug_summary"] = {
        "total_bugs": len(audit["bugs_found"]),
        "bugs": audit["bugs_found"],
    }

    return audit


# ─── Master data check ────────────────────────────────────────────────────────

def check_master_data_peers():
    """Check if 0728 and 0762 have company names in master data."""
    master = _load_master_data()
    result = {}
    for t in ["0941", "0728", "0762", "3416", "12345"]:
        entry = master.get(t) or master.get(_normalize_ticker(t)) or {}
        result[t] = {
            "found_in_master": bool(entry),
            "name_zh": entry.get("name_zh"),
            "name_en": entry.get("name_en"),
            "pe_ratio": entry.get("pe_ratio"),
            "pb_ratio": entry.get("pb_ratio"),
        }
    return result


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    print(f"[AUDIT] Starting FOS V4.0.3 Payload Audit at {NOW}")
    print(f"[AUDIT] Output dir: {OUT_DIR}")

    # Master data check
    master_check = check_master_data_peers()
    print(f"\n[MASTER DATA CHECK]")
    for t, info in master_check.items():
        print(f"  {t}: found={info['found_in_master']}, name_zh={info['name_zh']}, name_en={info['name_en']}")

    # Run audits
    cases = [
        ("12345", make_invalid_package()),
        ("0941", make_0941_package()),
        ("3416", make_3416_package()),
    ]

    all_results = {}
    for ticker, package in cases:
        print(f"\n[AUDIT] Running audit for ticker: {ticker}")
        result = audit_ticker(ticker, package)
        result["master_data_check"] = master_check.get(ticker, {})
        all_results[ticker] = result

        # Save individual JSON
        fname = f"{ticker}_payload_audit.json"
        fpath = os.path.join(OUT_DIR, fname)
        with open(fpath, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"  -> Saved: {fpath}")
        print(f"  -> Bugs found: {result['bug_summary']['total_bugs']}")
        for bug in result["bugs_found"]:
            print(f"     BUG: {bug}")

    print(f"\n[AUDIT] All audits complete.")
    return all_results


if __name__ == "__main__":
    main()
