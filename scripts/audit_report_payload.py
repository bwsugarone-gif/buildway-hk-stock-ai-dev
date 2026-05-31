"""
scripts/audit_report_payload.py
v4.0.3 — Full Report Payload Audit

Generates a report package for each test ticker and saves a JSON audit file
to debug_audit/{ticker}_payload_audit.json

Also performs a UI key audit on app.py and core/fos_components.py.

Usage:
    python scripts/audit_report_payload.py
"""

import sys
import os
import json
import re
from pathlib import Path

# Add project root to path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

AUDIT_DIR = ROOT / "debug_audit"
AUDIT_DIR.mkdir(exist_ok=True)

TICKERS = ["12345", "0941", "3416", "0688"]

# 52-week key variants to check
WEEK52_KEYS = [
    "fifty_two_week_high",
    "fifty_two_week_low",
    "fifty_two_week_position",
    "week_52_high",
    "week_52_low",
    "fiftyTwoWeekHigh",
    "fiftyTwoWeekLow",
]

CANONICAL_KEYS = {
    "source_registry",
    "market_snapshot",
    "competitive_landscape",
    "peer_comparison",
    "agent_opinions",
    "risk_assessment_v2",
    "investment_conclusion",
    "hkex_status",
    "news_localized",
}

LEGACY_KEYS = {
    "data_confidence",
    "source_transparency",
    "market_snapshot_v4",
    "competitive_landscape_v4",
    "investment_conclusion_v4",
    "risk_analysis",
    "agent_status",
    "committee_status",
    "report_sections",
    "confidence_score",
    "verified_sources",
}


def _safe_str(val):
    """Convert value to JSON-safe string summary."""
    if val is None:
        return None
    if isinstance(val, (str, int, float, bool)):
        return val
    if isinstance(val, list):
        return f"[list len={len(val)}]"
    if isinstance(val, dict):
        return f"{{dict keys={list(val.keys())[:8]}}}"
    return str(val)[:120]


def audit_ticker(ticker: str) -> dict:
    """Run full analysis for a ticker and extract audit data."""
    print(f"\n{'='*60}")
    print(f"Auditing ticker: {ticker}")
    print('='*60)

    result = {
        "ticker": ticker,
        "audit_version": "v4.0.3",
        "error": None,
    }

    try:
        from agents.ceo_agent import CEOAgent
        agent = CEOAgent()
        pkg = agent.run_analysis(ticker)
    except Exception as e:
        result["error"] = str(e)
        print(f"  ERROR running analysis: {e}")
        return result

    # ── A. Top-level keys ─────────────────────────────────────────────────────
    result["A_top_level_keys"] = list(pkg.keys())

    # ── B. Source registry ────────────────────────────────────────────────────
    sr = pkg.get("source_registry", {}) or {}
    result["B_source_registry"] = {
        "exists": bool(sr),
        "keys": list(sr.keys()) if sr else [],
        "coverage_pct": pkg.get("data_coverage_pct"),
        "confidence_level": pkg.get("confidence_level"),
        "verified_sources": [
            k for k, v in sr.items()
            if isinstance(v, dict) and v.get("verified") is True
        ],
        "missing_sources": [
            k for k, v in sr.items()
            if isinstance(v, dict) and v.get("verified") is not True
        ],
        "hkex_verified": sr.get("hkex", {}).get("verified") if isinstance(sr.get("hkex"), dict) else False,
        "raw_sample": {k: _safe_str(v) for k, v in list(sr.items())[:5]},
    }

    # ── C. Market snapshot ────────────────────────────────────────────────────
    mkt = pkg.get("market_data", {}) or {}
    snap_v4 = pkg.get("market_snapshot_v4", {}) or {}
    snap_legacy = pkg.get("market_snapshot", {}) or {}

    week52_found = {}
    for key in WEEK52_KEYS:
        val_mkt = mkt.get(key)
        val_v4 = snap_v4.get(key)
        val_leg = snap_legacy.get(key)
        if val_mkt is not None or val_v4 is not None or val_leg is not None:
            week52_found[key] = {
                "market_data": val_mkt,
                "market_snapshot_v4": val_v4,
                "market_snapshot": val_leg,
            }

    result["C_market_snapshot"] = {
        "market_snapshot_exists": bool(snap_legacy),
        "market_snapshot_v4_exists": bool(snap_v4),
        "current_price": mkt.get("current_price"),
        "week52_keys_found": week52_found,
        "week52_keys_missing": [k for k in WEEK52_KEYS if k not in week52_found],
        "snap_v4_keys": list(snap_v4.keys()) if snap_v4 else [],
    }

    # ── D. Competitive landscape ──────────────────────────────────────────────
    cl = pkg.get("competitive_landscape", {}) or {}
    cl_v4 = pkg.get("competitive_landscape_v4", {}) or {}
    pc = pkg.get("peer_comparison", {}) or {}

    peers = cl.get("peers", []) or []
    peer_rows = []
    for p in peers[:6]:
        if isinstance(p, dict):
            peer_rows.append({
                "ticker": p.get("ticker"),
                "name": p.get("name") or p.get("company_name"),
                "pe": p.get("pe_ratio") or p.get("pe"),
                "pb": p.get("pb_ratio") or p.get("pb"),
            })

    result["D_competitive_landscape"] = {
        "competitive_landscape_exists": bool(cl),
        "competitive_landscape_v4_exists": bool(cl_v4),
        "peer_comparison_exists": bool(pc),
        "cl_keys": list(cl.keys()) if cl else [],
        "peer_count": len(peers),
        "peer_rows": peer_rows,
        "subject_ticker": cl.get("subject", {}).get("ticker") if isinstance(cl.get("subject"), dict) else cl.get("ticker"),
    }

    # ── E. Agent opinions ─────────────────────────────────────────────────────
    ao = pkg.get("agent_opinions", []) or []
    ao_v2 = pkg.get("agent_opinions_v2", []) or []
    committee = pkg.get("investment_committee", {}) or {}
    ic_result = pkg.get("ic_result", {}) or {}

    zero_pct_agents = []
    for op in ao:
        if isinstance(op, dict):
            conf_str = str(op.get("信心分數", ""))
            if conf_str.startswith("0/"):
                zero_pct_agents.append(op.get("Agent", "unknown"))

    result["E_agent_opinions"] = {
        "agent_opinions_count": len(ao),
        "agent_opinions_v2_count": len(ao_v2),
        "investment_committee_exists": bool(committee),
        "ic_result_verdict": ic_result.get("verdict"),
        "zero_confidence_agents": zero_pct_agents,
        "agent_names": [op.get("Agent") for op in ao if isinstance(op, dict)],
        "old_agent_status_keys": list(pkg.get("agent_status", {}).keys()) if pkg.get("agent_status") else [],
    }

    # ── F. Investment conclusion ──────────────────────────────────────────────
    ic = pkg.get("investment_conclusion", {}) or {}
    ic_v4 = pkg.get("investment_conclusion_v4", {}) or {}

    result["F_investment_conclusion"] = {
        "investment_conclusion_exists": bool(ic),
        "investment_conclusion_v4_exists": bool(ic_v4),
        "rating": ic.get("rating"),
        "target_price": ic.get("target_price"),
        "suitable_investor": ic.get("suitable_investor"),
        "investment_horizon": ic.get("investment_horizon"),
        "decision_basis_count": len(ic.get("decision_basis", []) or []),
        "final_summary_exists": bool(ic.get("final_summary")),
        "ic_keys": list(ic.keys()) if ic else [],
    }

    # ── G. Risk payload ───────────────────────────────────────────────────────
    risk = pkg.get("risk_analysis", {}) or {}
    risk_v2 = pkg.get("risk_assessment_v2", {}) or {}

    risk_table = risk.get("risk_table", []) or []
    dim_scores = risk.get("dimension_scores", {}) or {}
    categories = [r.get("dimension") for r in risk_table if isinstance(r, dict)]
    duplicates = [c for c in set(categories) if categories.count(c) > 1]

    result["G_risk"] = {
        "risk_analysis_exists": bool(risk),
        "risk_assessment_v2_exists": bool(risk_v2),
        "composite_risk_score": risk.get("composite_risk_score"),
        "risk_label": risk.get("risk_label"),
        "dimension_scores_keys": list(dim_scores.keys()),
        "risk_table_rows": len(risk_table),
        "duplicated_categories": duplicates,
        "risk_v2_keys": list(risk_v2.keys()) if risk_v2 else [],
    }

    # ── H. News payload ───────────────────────────────────────────────────────
    news = pkg.get("news_analysis", {}) or {}
    news_loc = pkg.get("news_localized", []) or []
    news_cat = pkg.get("news_catalyst", {}) or {}

    items = news.get("news_items", []) or []
    raw_titles = [i.get("title") for i in items if isinstance(i, dict)]
    loc_titles = [i.get("title_zh") or i.get("display_title") for i in items if isinstance(i, dict)]

    result["H_news"] = {
        "news_analysis_exists": bool(news),
        "news_localized_exists": bool(news_loc),
        "news_catalyst_exists": bool(news_cat),
        "news_items_count": len(items),
        "raw_titles_sample": raw_titles[:3],
        "localized_titles_sample": loc_titles[:3],
        "sentiment_label": news.get("sentiment_analysis", {}).get("label") if isinstance(news.get("sentiment_analysis"), dict) else None,
        "news_status": news.get("status"),
    }

    # ── Legacy key presence check ─────────────────────────────────────────────
    legacy_present = [k for k in LEGACY_KEYS if k in pkg]
    canonical_present = [k for k in CANONICAL_KEYS if k in pkg]

    result["Z_key_audit"] = {
        "canonical_keys_present": canonical_present,
        "canonical_keys_missing": [k for k in CANONICAL_KEYS if k not in pkg],
        "legacy_keys_present": legacy_present,
    }

    return result


def audit_ui_keys() -> dict:
    """Scan app.py and fos_components.py for render functions and key usage."""
    files_to_scan = [
        ROOT / "app.py",
        ROOT / "core" / "fos_components.py",
    ]

    render_map = {}

    for fpath in files_to_scan:
        if not fpath.exists():
            continue
        src = fpath.read_text(encoding="utf-8", errors="replace")
        lines = src.splitlines()

        current_fn = None
        fn_keys = {}

        for line in lines:
            # Detect function definition
            fn_match = re.match(r"^def (render_\w+|_render_\w+)\s*\(", line)
            if fn_match:
                current_fn = fn_match.group(1)
                fn_keys[current_fn] = {"reads": [], "canonical": [], "legacy": []}

            if current_fn:
                # Find .get("key") patterns
                for m in re.finditer(r'\.get\(["\'](\w+)["\']', line):
                    key = m.group(1)
                    if key not in fn_keys[current_fn]["reads"]:
                        fn_keys[current_fn]["reads"].append(key)
                    if key in CANONICAL_KEYS:
                        if key not in fn_keys[current_fn]["canonical"]:
                            fn_keys[current_fn]["canonical"].append(key)
                    if key in LEGACY_KEYS:
                        if key not in fn_keys[current_fn]["legacy"]:
                            fn_keys[current_fn]["legacy"].append(key)

        for fn, data in fn_keys.items():
            render_map[f"{fpath.name}::{fn}"] = data

    return render_map


def main():
    all_audits = {}

    for ticker in TICKERS:
        audit = audit_ticker(ticker)
        all_audits[ticker] = audit

        out_path = AUDIT_DIR / f"{ticker}_payload_audit.json"
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(audit, f, ensure_ascii=False, indent=2, default=str)
        print(f"  Saved: {out_path}")

    # UI key audit
    print(f"\n{'='*60}")
    print("UI Key Audit (app.py + fos_components.py)")
    print('='*60)
    ui_audit = audit_ui_keys()

    ui_out = AUDIT_DIR / "ui_key_audit.json"
    with open(ui_out, "w", encoding="utf-8") as f:
        json.dump(ui_audit, f, ensure_ascii=False, indent=2)
    print(f"  Saved: {ui_out}")

    # Print summary
    print(f"\n{'='*60}")
    print("AUDIT SUMMARY")
    print('='*60)
    for ticker, audit in all_audits.items():
        if audit.get("error"):
            print(f"  {ticker}: ERROR — {audit['error']}")
            continue
        cov = audit.get("B_source_registry", {}).get("coverage_pct", "?")
        conf = audit.get("B_source_registry", {}).get("confidence_level", "?")
        peers = audit.get("D_competitive_landscape", {}).get("peer_count", 0)
        zero_agents = audit.get("E_agent_opinions", {}).get("zero_confidence_agents", [])
        rating = audit.get("F_investment_conclusion", {}).get("rating", "?")
        legacy = audit.get("Z_key_audit", {}).get("legacy_keys_present", [])
        print(f"  {ticker}: coverage={cov}% conf={conf} peers={peers} rating={rating} zero_agents={zero_agents} legacy_keys={legacy}")

    # Functions using legacy keys
    legacy_fns = {fn: d for fn, d in ui_audit.items() if d.get("legacy")}
    if legacy_fns:
        print(f"\n  UI functions using legacy keys:")
        for fn, d in legacy_fns.items():
            print(f"    {fn}: {d['legacy']}")

    print(f"\nAll audit files saved to: {AUDIT_DIR}")
    print("Run test_v403_payload_audit.py to validate findings.")


if __name__ == "__main__":
    main()
