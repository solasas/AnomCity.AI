"""
detect_anomalies.py
-------------------
Trains an Isolation Forest on the merged city dataset to detect
anomalous hours — hours where the combination of crime, traffic,
and weather signals is unusually far from the typical pattern.

Outputs:
  - anomaly_score and anomaly_flag columns saved back to merged_city_data.csv
  - Top 10 anomalous hours printed to the terminal
  - anomaly_scores.png  — time-series plot of scores with flagged hours marked
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest  # the algorithm itself
import matplotlib.pyplot as plt               # for plotting


# ---------------------------------------------------------------------------
# STEP 1 — Load and prepare data
# ---------------------------------------------------------------------------

df = pd.read_csv("merged_city_data.csv", parse_dates=["timestamp"])
df = df.set_index("timestamp")  # use timestamp as the row label, not a column

# Select only the numeric feature columns the model will train on.
# We give the model ALL signals simultaneously — it finds hours that are
# unusual across the combination of crime, traffic, and weather together.
FEATURES = ["crime_count", "avg_speed", "total_volume",
            "avg_temperature", "avg_humidity", "total_rainfall"]

# Keep only the feature columns that actually exist in the file
FEATURES = [f for f in FEATURES if f in df.columns]

X = df[FEATURES].copy()

# Drop any rows that still have NaN — IsolationForest can't handle them
X = X.dropna()
df = df.loc[X.index]  # keep df aligned with X after dropping rows

print(f"Training on {len(X):,} hourly records with {len(FEATURES)} features.")
print(f"Features: {FEATURES}\n")


# ---------------------------------------------------------------------------
# STEP 2 — Train the Isolation Forest
# ---------------------------------------------------------------------------
# n_estimators : number of isolation trees; more = more stable, slower
# contamination: estimated fraction of anomalies in the data (5% here)
# random_state : fixes randomness so results are the same every run

model = IsolationForest(
    n_estimators=100,
    contamination=0.05,  # expect ~5% of hours to be anomalous
    random_state=42,
)

# fit() builds all 100 trees using only the feature matrix.
# No labels needed — the model learns "normal" purely from data structure.
model.fit(X)
print("Model trained.\n")


# ---------------------------------------------------------------------------
# STEP 3 — Score every hour and add result columns
# ---------------------------------------------------------------------------
# score_samples returns negative values; more negative = more anomalous.
# We negate so: higher positive score = more anomalous (more intuitive).
df["anomaly_score"] = -model.score_samples(X)

# predict returns -1 (anomaly) or +1 (normal) based on contamination threshold.
# We map to 1 / 0: 1 = anomaly, 0 = normal.
raw_predictions = model.predict(X)
df["anomaly_flag"] = (raw_predictions == -1).astype(int)

flagged = df["anomaly_flag"].sum()
print(f"Anomalies flagged: {flagged:,} out of {len(df):,} hours "
      f"({flagged / len(df) * 100:.1f}%)\n")


# ---------------------------------------------------------------------------
# STEP 4 — Print top 10 anomalies
# ---------------------------------------------------------------------------
# Sort by anomaly_score descending; head(10) takes the worst 10 rows.
display_cols = FEATURES + ["anomaly_score"]
top10 = (df[display_cols]
           .sort_values("anomaly_score", ascending=False)
           .head(10))

print("Top 10 anomalous hours:")
print(top10.to_string())  # to_string() prevents pandas from truncating columns
print()


# ---------------------------------------------------------------------------
# STEP 5 — Plot anomaly scores over time
# ---------------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(14, 5))

# Continuous line showing the anomaly score for every hour of the year
ax.plot(df.index, df["anomaly_score"],
        color="steelblue", linewidth=0.6, label="Anomaly score")

# Red dots on top of the line for every flagged hour
anomalies = df[df["anomaly_flag"] == 1]
ax.scatter(anomalies.index, anomalies["anomaly_score"],
           color="red", s=10, zorder=5,  # zorder=5 draws dots above the line
           label=f"Flagged anomaly ({len(anomalies):,})")

# Horizontal dashed line at the lowest flagged score = the decision threshold
threshold = anomalies["anomaly_score"].min()
ax.axhline(threshold, color="red", linestyle="--",
           linewidth=0.8, label=f"Threshold ({threshold:.3f})")

ax.set_title("Isolation Forest Anomaly Scores — Hourly City Data (2023)")
ax.set_xlabel("Time")
ax.set_ylabel("Anomaly Score  (higher = more anomalous)")
ax.legend()
plt.tight_layout()  # prevents axis labels from being clipped at edges
plt.savefig("anomaly_scores.png", dpi=150)
plt.show()
print("Plot saved to anomaly_scores.png")


# ---------------------------------------------------------------------------
# STEP 6 — Save results back to CSV
# ---------------------------------------------------------------------------
# Overwrite the merged file with the two new columns appended.
# index=True keeps the timestamp in the output.
df.to_csv("merged_city_data.csv", index=True)
print("Saved anomaly_score and anomaly_flag to merged_city_data.csv")
