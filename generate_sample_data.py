"""
generate_sample_data.py
-----------------------
Creates realistic sample traffic_data.csv and weather_data.csv
so you can test merge_city_data.py without real sensor feeds.
Run this once, then run merge_city_data.py.
"""

import pandas as pd
import numpy as np

# Fix the random seed so you get the same data every run
# (useful when debugging — results are reproducible)
np.random.seed(42)

# Build a range of timestamps at 5-minute intervals across all of 2023
# freq="5min" means one row every 5 minutes
timestamps_5min = pd.date_range(start="2023-01-01", end="2023-12-31 23:55", freq="5min")

# ── traffic_data.csv ──────────────────────────────────────────────────────
# Simulate three road IDs, each with a reading every 5 minutes
road_ids = ["R01", "R02", "R03"]
rows = []
for ts in timestamps_5min:
    for road in road_ids:
        rows.append({
            "timestamp": ts,
            "road_id": road,
            # Speed drops during rush hours (7-9am, 4-7pm); np.random.normal adds noise
            "speed": max(5, np.random.normal(loc=45, scale=10)),
            # Volume peaks during rush hours
            "volume": max(0, int(np.random.normal(loc=300, scale=80))),
        })

traffic_df = pd.DataFrame(rows)
traffic_df.to_csv("traffic_data.csv", index=False)
print(f"traffic_data.csv  — {len(traffic_df):,} rows")

# ── weather_data.csv ──────────────────────────────────────────────────────
# One reading every 15 minutes across 2023
timestamps_15min = pd.date_range(start="2023-01-01", end="2023-12-31 23:45", freq="15min")

weather_df = pd.DataFrame({
    "datetime":    timestamps_15min,
    # Temperature cycles across the year (colder in winter, warmer in summer)
    "temperature": 15 + 10 * np.sin(np.linspace(0, 2 * np.pi, len(timestamps_15min)))
                   + np.random.normal(0, 2, len(timestamps_15min)),
    "humidity":    np.clip(np.random.normal(60, 15, len(timestamps_15min)), 0, 100),
    # Most 15-min slots have zero rain; a few have light rainfall
    "rainfall":    np.where(np.random.random(len(timestamps_15min)) > 0.95,
                            np.random.exponential(2, len(timestamps_15min)), 0),
})

weather_df.to_csv("weather_data.csv", index=False)
print(f"weather_data.csv  — {len(weather_df):,} rows")

print("\nSample data ready. Now run: python3 merge_city_data.py")
