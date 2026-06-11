#!/usr/bin/env python3
"""
process_data.py
Normalizes GDELT CSVs and generates data/dashboard_data.json for the dashboard.

Run after collect_data.py. If BigQuery data is unavailable, produces
dashboard_data.json from whatever CSVs exist in data/.
"""

import os
import json
import numpy as np
import pandas as pd

os.makedirs("data", exist_ok=True)

EVENTS = [
    {"date": "2015-05", "year": 2015, "label": "Made in China 2025",    "type": "policy"},
    {"date": "2017-03", "year": 2017, "label": "THAAD / Lotte Boycott", "type": "boycott"},
    {"date": "2019-10", "year": 2019, "label": "NBA Controversy",       "type": "boycott"},
    {"date": "2021-03", "year": 2021, "label": "H&M / Xinjiang Cotton", "type": "boycott"},
    {"date": "2022-02", "year": 2022, "label": "Beijing Winter Olympics","type": "political"},
]

dashboard_data = {"annual": [], "brand_tone": [], "xi_monthly": [], "events": EVENTS}

# ---------------------------------------------------------------------------
# Annual keyword frequency — normalize per 100k articles
# ---------------------------------------------------------------------------
annual_path = "data/keyword_frequency_annual.csv"
if os.path.exists(annual_path):
    print("Processing keyword_frequency_annual.csv...")
    annual = pd.read_csv(annual_path)

    for col in ["patriotism_count", "china_dream_count", "nationalism_theme_count", "guochao_count"]:
        if col in annual.columns and "total_china_articles" in annual.columns:
            norm_col = col.replace("_count", "_norm")
            annual[norm_col] = (annual[col] / annual["total_china_articles"] * 100_000).round(1)

    annual.to_csv("data/keyword_frequency_annual_normalized.csv", index=False)
    print(f"  Saved: data/keyword_frequency_annual_normalized.csv")
    dashboard_data["annual"] = annual.fillna(0).to_dict("records")
else:
    print(f"  {annual_path} not found — skipping (run collect_data.py first)")

# ---------------------------------------------------------------------------
# Consumer nationalism — aggregate daily → monthly
# ---------------------------------------------------------------------------
consumer_path = "data/consumer_nationalism_daily.csv"
if os.path.exists(consumer_path):
    print("Processing consumer_nationalism_daily.csv...")
    consumer = pd.read_csv(consumer_path, parse_dates=["pub_date"])
    consumer["year_month"] = consumer["pub_date"].dt.to_period("M").astype(str)
    monthly = consumer.groupby("year_month").agg(
        foreign_brand_mentions=("foreign_brand_mentions", "sum"),
        domestic_brand_mentions=("domestic_brand_mentions", "sum"),
        foreign_brand_tone=("foreign_brand_tone", "mean"),
        domestic_brand_tone=("domestic_brand_tone", "mean"),
    ).reset_index()
    monthly.to_csv("data/consumer_nationalism_monthly.csv", index=False)
    print(f"  Saved: data/consumer_nationalism_monthly.csv ({len(monthly)} rows)")
    dashboard_data["brand_tone"] = monthly.fillna(0).to_dict("records")
else:
    print(f"  {consumer_path} not found — skipping")

# ---------------------------------------------------------------------------
# Xi rhetoric monthly — load as-is
# ---------------------------------------------------------------------------
xi_path = "data/xi_rhetoric_monthly.csv"
if os.path.exists(xi_path):
    print("Processing xi_rhetoric_monthly.csv...")
    xi = pd.read_csv(xi_path)
    dashboard_data["xi_monthly"] = xi.fillna(0).to_dict("records")
    print(f"  Loaded: {len(xi)} rows")
else:
    print(f"  {xi_path} not found — skipping")

# ---------------------------------------------------------------------------
# Event correlation — spike ratio per keyword for each event month
# ---------------------------------------------------------------------------
if os.path.exists(xi_path):
    print("Computing event correlation...")
    xi = pd.read_csv(xi_path)
    rows = []
    for event in EVENTS:
        month = event["date"]
        for kw in ["china_dream", "national_rejuvenation", "made_in_china_2025"]:
            if kw not in xi.columns:
                continue
            row = xi[xi["year_month"] == month]
            if row.empty:
                continue
            val = float(row[kw].values[0])
            baseline = float(xi[kw].mean())
            rows.append({
                "event": event["label"],
                "event_date": month,
                "keyword": kw,
                "count": val,
                "baseline": round(baseline, 2),
                "spike_ratio": round(val / baseline, 2) if baseline > 0 else 0,
            })
    event_df = pd.DataFrame(rows)
    event_df.to_csv("data/event_correlation.csv", index=False)
    print(f"  Saved: data/event_correlation.csv ({len(event_df)} rows)")

# ---------------------------------------------------------------------------
# Write dashboard_data.json
# ---------------------------------------------------------------------------
out_path = "data/dashboard_data.json"
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(dashboard_data, f, indent=2, default=str)
print(f"\nSaved: {out_path}")
print("Open dashboard/index.html in a browser to view the dashboard.")
