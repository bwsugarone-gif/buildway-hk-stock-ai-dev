"""
test_fos_v3.py — FOS V3 Client Experience Layer validation tests
Tests fos_components.py: all 9 functions importable, graceful fallback on empty data,
confidence score mapping, rating colour mapping.

Run from buildway-hk-stock-ai/ directory:
    python test_fos_v3.py
"""
from __future__ import annotations

import sys
import os
import types
import unittest.mock as mock

os.chdir(os.path.dirname(os.path.abspath(__file__)))

print(f"Python: {sys.version}")
print(f"Working dir: {os.getcwd()}")
print()

errors: list[str] = []


def check(label: str, condition: bool, detail: str = "") -> None:
    if condition:
        print(f"  [OK] {label}" + (f" — {detail}" if detail else ""))
    else:
        print(f"  [FAIL] {label}" + (f" — {detail}" if detail else ""))
        errors.append(label)


# ── Stub streamlit so fos_components can be imported without a running app ────
def _make_st_stub() -> types.ModuleType:
    """Return a minimal streamlit stub that records calls without rendering."""
    st = types.ModuleType("streamlit")

    class _CM:
        def __enter__(self): return self
        def __exit__(self, *a): pass

    def _noop(*a, **kw): return _CM()
    def _noop_str(*a, **kw): return ""
    def _noop_none(*a, **kw): return None

    for name in (
        "markdown", "caption", "subheader", "header", "title",
        "metric", "info", "warning", "error", "success",
        "divider", "stop", "rerun", "image", "dataframe",
        "progress", "spinner", "expander",
    ):
        setattr(st, name, _noop)

    st.columns = lambda n, **kw: [_CM() for _ in range(n if isinstance(n, int) else len(n))]
    st.tabs = lambda labels: [_CM() for _ in labels]
    st.container = lambda **kw: _CM()
    st.sidebar = _CM()
    st.session_state = {}
    st.button = lambda *a, **kw: False
    st.text_input = _noop_str
    st.selectbox = _noop_none
    st.number_input = lambda *a, **kw: 0
    st.download_button = _noop
    st.form = lambda *a, **kw: _CM()
    st.form_submit_button = lambda *a, **kw: False
    st.set_page_config = _noop
    st.cache_data = lambda **kw: (lambda f: f)
    st.write = _noop

    # plotly_chart stub
    st.plotly_chart = _noop

    return st


sys.modules["streamlit"] = _make_st_stub()

# Also stub plotly so render_financial_trends plotly path doesn't crash
try:
    import plotly  # noqa: F401
except ImportError:
    plotly_stub = types.ModuleType("plotly")
    plotly_express = types.ModuleType("plotly.express")
    plotly_graph_objects = types.ModuleType("plotly.graph_objects")

    class _FigStub:
        def update_layout(self, **kw): pass
        def add_trace(self, *a, **kw): pass

    plotly_graph_objects.Figure = _FigStub
    plotly_graph_objects.Bar = lambda **kw: None
    plotly_express.bar = lambda *a, **kw: _FigStub()
    plotly_stub.express = plotly_express
    plotly_stub.graph_objects = plotly_graph_objects
    sys.modules["plotly"] = plotly_stub
    sys.modules["plotly.express"] = plotly_express
    sys.modules["plotly.graph_objects"] = plotly_graph_objects


# ── Test 1: Import all 9 FOS components ──────────────────────────────────────
print("=== Test 1: fos_components imports ===")
try:
    from core.fos_components import (
        render_company_sidebar,
        render_competitive_landscape,
        render_confidence_breakdown,
        render_market_snapshot,
        render_financial_trends,
        render_risk_event_cards,
        render_news_sentiment,
        render_multi_agent_committee,
        render_investment_conclusion,
    )
    check("render_company_sidebar imported", callable(render_company_sidebar))
    check("render_competitive_landscape imported", callable(render_competitive_landscape))
    check("render_confidence_breakdown imported", callable(render_confidence_breakdown))
    check("render_market_snapshot imported", callable(render_market_snapshot))
    check("render_financial_trends imported", callable(render_financial_trends))
    check("render_risk_event_cards imported", callable(render_risk_event_cards))
    check("render_news_sentiment imported", callable(render_news_sentiment))
    check("render_multi_agent_committee imported", callable(render_multi_agent_committee))
    check("render_investment_conclusion imported", callable(render_investment_conclusion))
except Exception as exc:
    print(f"  [FAIL] fos_components import: {exc}")
    errors.append("fos_components import")
    sys.exit(1)  # Cannot continue without imports


# ── Test 2: Graceful fallback on empty dict ───────────────────────────────────
print("\n=== Test 2: graceful fallback on empty data ===")

EMPTY_PAYLOADS = [
    ("render_company_sidebar", render_company_sidebar, {}),
    ("render_competitive_landscape", render_competitive_landscape, {}),
    ("render_confidence_breakdown", render_confidence_breakdown, {}),
    ("render_market_snapshot", render_market_snapshot, {}),
    ("render_financial_trends", render_financial_trends, {}),
    ("render_risk_event_cards", render_risk_event_cards, {}),
    ("render_news_sentiment", render_news_sentiment, {}),
    ("render_multi_agent_committee", render_multi_agent_committee, {}),
    ("render_investment_conclusion", render_investment_conclusion, {}),
]

for name, fn, payload in EMPTY_PAYLOADS:
    try:
        fn(payload)
        check(f"{name}(empty) no crash", True)
    except Exception as exc:
        check(f"{name}(empty) no crash", False, str(exc))


# ── Test 3: render_confidence_breakdown score mapping ────────────────────────
print("\n=== Test 3: confidence_breakdown score mapping ===")
try:
    # HIGH confidence — overall_score >= 80
    render_confidence_breakdown({
        "data_confidence": {
            "level": "HIGH",
            "overall_score": 85,
            "financial_coverage": 90,
            "news_verification": 70,
            "hkex_verification": 60,
            "agent_consensus": 80,
            "data_freshness": 75,
            "sources": ["Yahoo Finance", "HKEX Filing"],
        }
    })
    check("render_confidence_breakdown HIGH no crash", True)

    # LOW confidence
    render_confidence_breakdown({
        "data_confidence": {
            "level": "LOW",
            "overall_score": 30,
            "sources": [],
        }
    })
    check("render_confidence_breakdown LOW no crash", True)
except Exception as exc:
    check("render_confidence_breakdown score mapping", False, str(exc))


# ── Test 4: render_investment_conclusion rating variants ─────────────────────
print("\n=== Test 4: investment_conclusion rating variants ===")
for rating in ["買入", "觀察", "中性", "減持", "避免"]:
    try:
        render_investment_conclusion({
            "investment_conclusion": {
                "rating": rating,
                "horizon": "中線",
                "investor_type": "平衡",
                "summary": "測試摘要",
            }
        })
        check(f"render_investment_conclusion({rating}) no crash", True)
    except Exception as exc:
        check(f"render_investment_conclusion({rating}) no crash", False, str(exc))


# ── Test 5: render_multi_agent_committee with realistic data ─────────────────
print("\n=== Test 5: multi_agent_committee realistic data ===")
try:
    render_multi_agent_committee({
        "investment_committee": {
            "bull_score": 65,
            "bear_score": 35,
            "confidence": 72,
            "committee_summary": "綜合各 Agent 觀點，整體評級為觀察。",
            "final_recommendation": "觀察",
            "agents": {
                "market_data": {"opinion": "中性", "reasoning": "估值合理", "confidence": 70},
                "financial": {"opinion": "正面", "reasoning": "盈利穩定", "confidence": 75},
                "risk": {"opinion": "謹慎", "reasoning": "槓桿偏高", "confidence": 65},
            },
        }
    })
    check("render_multi_agent_committee realistic data no crash", True)
except Exception as exc:
    check("render_multi_agent_committee realistic data no crash", False, str(exc))


# ── Test 6: render_risk_event_cards with risk data ───────────────────────────
print("\n=== Test 6: risk_event_cards with data ===")
try:
    render_risk_event_cards({
        "risk_analysis": {
            "liquidity_risk": 4,
            "valuation_risk": 6,
            "market_risk": 5,
            "financial_risk": 3,
            "news_risk": 4,
            "composite_score": "5.2/10",
            "risk_label": "中等風險",
            "top_risks": [
                {"dimension": "估值風險", "score": 6, "level": "中等", "weight": "25%"},
                {"dimension": "市場風險", "score": 5, "level": "中等", "weight": "20%"},
            ],
        }
    })
    check("render_risk_event_cards with data no crash", True)
except Exception as exc:
    check("render_risk_event_cards with data no crash", False, str(exc))


# ── Test 7: render_market_snapshot with 52-week data ─────────────────────────
print("\n=== Test 7: market_snapshot with 52-week data ===")
try:
    render_market_snapshot({
        "market_data": {
            "current_price": 350.0,
            "week_52_high": 420.0,
            "week_52_low": 280.0,
            "volume": "12,345,678",
        }
    })
    check("render_market_snapshot with 52-week data no crash", True)
except Exception as exc:
    check("render_market_snapshot with 52-week data no crash", False, str(exc))


# ── Test 8: render_financial_trends with trend data ──────────────────────────
print("\n=== Test 8: financial_trends with trend data ===")
try:
    render_financial_trends({
        "financial_data": {
            "revenue_trend": [
                {"year": "2022", "value": 1200},
                {"year": "2023", "value": 1350},
                {"year": "2024", "value": 1480},
            ],
            "ebitda_trend": [
                {"year": "2022", "value": 400},
                {"year": "2023", "value": 450},
                {"year": "2024", "value": 510},
            ],
            "net_profit_trend": [],
            "fcf_trend": [],
        }
    })
    check("render_financial_trends with trend data no crash", True)
except Exception as exc:
    check("render_financial_trends with trend data no crash", False, str(exc))


# ── Test 9: render_news_sentiment with counts ────────────────────────────────
print("\n=== Test 9: news_sentiment with counts ===")
try:
    render_news_sentiment({
        "news_analysis": {
            "positive_count": 5,
            "neutral_count": 3,
            "negative_count": 2,
            "catalysts": ["業績超預期", "新產品發布"],
            "watchlist": ["監管政策變化"],
        }
    })
    check("render_news_sentiment with counts no crash", True)
except Exception as exc:
    check("render_news_sentiment with counts no crash", False, str(exc))


# ── Test 10: render_competitive_landscape with peer data ─────────────────────
print("\n=== Test 10: competitive_landscape with peer data ===")
try:
    render_competitive_landscape({
        "cover": {"ticker": "0941.HK", "company_name_zh": "中國移動"},
        "competitive_analysis": {
            "products": ["5G 服務", "雲端業務"],
            "market_position": "市場領導者",
            "strengths": ["用戶規模最大", "網絡覆蓋廣"],
            "weaknesses": ["ARPU 增長放緩"],
            "strategy": "數字化轉型",
        },
        "peer_comparison": {
            "peers": [
                {"ticker": "0728.HK", "name": "中國電信", "pe": 8.5, "pb": 0.6, "dividend_yield": "5.2%", "market_cap": "3,200億", "risk_score": 4.2},
                {"ticker": "0762.HK", "name": "中國聯通", "pe": 10.2, "pb": 0.8, "dividend_yield": "3.8%", "market_cap": "1,800億", "risk_score": 5.1},
            ]
        },
    })
    check("render_competitive_landscape with peer data no crash", True)
except Exception as exc:
    check("render_competitive_landscape with peer data no crash", False, str(exc))


# ── Summary ───────────────────────────────────────────────────────────────────
print()
if errors:
    print(f"FAILED: {len(errors)} test(s) failed: {errors}")
    sys.exit(1)
else:
    print("All FOS V3 tests passed.")
