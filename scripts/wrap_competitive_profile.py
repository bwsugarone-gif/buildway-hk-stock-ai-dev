"""
wrap_competitive_profile.py
Wraps the flat competitive_profile.json into {"stocks": {...}, "_meta": {...}}
so test_v420_fund_research_milestone.py can find data via data.get("stocks", {}).
"""
import json
from pathlib import Path

p = Path(__file__).resolve().parent.parent / "data" / "competitive_profile.json"
data = json.loads(p.read_text(encoding="utf-8"))

# Already wrapped? Skip.
if "stocks" in data:
    print(f"Already wrapped: {len(data['stocks'])} stocks present.")
else:
    wrapped = {
        "stocks": data,
        "_meta": {
            "version": "v4.2.0",
            "total": len(data),
            "note": "Wrapped by scripts/wrap_competitive_profile.py for v4.2.0 test compliance",
        },
    }
    p.write_text(json.dumps(wrapped, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Done: {len(data)} stocks wrapped into 'stocks' key.")
