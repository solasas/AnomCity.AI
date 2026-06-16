"""
merge_city_data.py
------------------
Standardizes, resamples, merges, and cleans three city datasets
(crime, traffic, weather) into a single hourly time series.

Input files expected:
  crime_clean.csv   — columns: date, latitude, longitude, crime_type
  traffic_data.csv  — columns: timestamp, road_id, speed, volume
  weather_data.csv  — columns: datetime, temperature, humidity, rainfall

Output:
  merged_city_data.csv — one row per hour, columns from all three sources
"""

import pandas as pd


# ---------------------------------------------------------------------------
# STEP 1 — Load the raw CSV files
# ---------------------------------------------------------------------------

crime_df   = pd.read_csv("crime_clean.csv")
traffic_df = pd.read_csv("traffic_data.csv")
weather_df = pd.read_csv("weather_data.csv")

print("Raw shapes:")
print(f"  Crime:   {crime_df.shape}")
print(f"  Traffic: {traffic_df.shape}")
print(f"  Weather: {weather_df.shape}\n")


# ---------------------------------------------------------------------------
# STEP 2 — Standardize datetime columns
# ---------------------------------------------------------------------------
# Why: Each file uses a different column name and possibly a different
# string format (e.g. "2023-01-15 14:32" vs "01/15/2023 2:32 PM").
# pd.to_datetime() parses most common formats automatically.
# After this, each column is a DatetimeIndex-compatible dtype instead of a
# plain string — only then can we do operations like "floor to the hour".

crime_df["date"]        = pd.to_datetime(crime_df["date"])
traffic_df["timestamp"] = pd.to_datetime(traffic_df["timestamp"])
weather_df["datetime"]  = pd.to_datetime(weather_df["datetime"])

# Rename all three to "timestamp" so the rest of the script uses one name
crime_df   = crime_df.rename(columns={"date": "timestamp"})
weather_df = weather_df.rename(columns={"datetime": "timestamp"})

# Set timestamp as the DataFrame index.
# resample() requires a DatetimeIndex — it cannot operate on a regular column.
crime_df   = crime_df.set_index("timestamp")
traffic_df = traffic_df.set_index("timestamp")
weather_df = weather_df.set_index("timestamp")

print("Datetime ranges after standardization:")
print(f"  Crime:   {crime_df.index.min()}  →  {crime_df.index.max()}")
print(f"  Traffic: {traffic_df.index.min()}  →  {traffic_df.index.max()}")
print(f"  Weather: {weather_df.index.min()}  →  {weather_df.index.max()}\n")


# ---------------------------------------------------------------------------
# STEP 3 — Resample each dataset to hourly intervals
# ---------------------------------------------------------------------------
# Why: Crime events, traffic readings, and weather readings are captured at
# different cadences. To merge them, we need a shared time grid.
# resample("h") groups rows into 1-hour buckets (e.g. all rows between
# 14:00:00 and 14:59:59 become one row labelled 14:00:00).
# We then choose an aggregation function for each column:
#   "count" / "size" → how many events occurred in that hour
#   "mean"           → average value across the hour
#   "sum"            → total accumulated value (e.g. rainfall in mm)

# -- Crime --
# Named aggregation syntax: new_col_name=("source_column", "function")
# We count rows to get crimes-per-hour; average lat/lon gives the
# geographic center of that hour's criminal activity.
crime_hourly = crime_df.resample("h").agg(
    crime_count   = ("latitude", "count"),  # counts non-null rows = number of crimes
    avg_latitude  = ("latitude", "mean"),
    avg_longitude = ("longitude", "mean"),
)

# -- Traffic --
# road_id is categorical — we drop it and average across all roads.
# avg_speed captures congestion level; total_volume captures how busy roads are.
traffic_hourly = traffic_df.resample("h").agg(
    avg_speed    = ("speed", "mean"),
    total_volume = ("volume", "sum"),   # sum because volume is a count of vehicles
)

# -- Weather --
# Rainfall is summed (total mm that fell in the hour).
# Temperature and humidity are averaged (they're continuous measurements).
weather_hourly = weather_df.resample("h").agg(
    avg_temperature = ("temperature", "mean"),
    avg_humidity    = ("humidity", "mean"),
    total_rainfall  = ("rainfall", "sum"),
)

print("Shapes after resampling to hourly:")
print(f"  Crime:   {crime_hourly.shape}")
print(f"  Traffic: {traffic_hourly.shape}")
print(f"  Weather: {weather_hourly.shape}\n")


# ---------------------------------------------------------------------------
# STEP 4 — Merge all three on the shared hourly timestamp index
# ---------------------------------------------------------------------------
# Why: We want one wide table where each row is one hour and every column
# from every source is present. This lets the anomaly detector later ask:
# "Was there a crime spike during heavy rain AND slow traffic?"
#
# pd.concat(axis=1) joins DataFrames side-by-side, aligning rows by index.
# join="outer" keeps ALL timestamps that appear in any dataset —
# even hours where one dataset has no data (those cells become NaN,
# which we handle in Step 5).

merged = pd.concat(
    [crime_hourly, traffic_hourly, weather_hourly],
    axis=1,       # stack columns, not rows
    join="outer", # keep all hours from all three datasets
)

print(f"Shape after merge: {merged.shape}")
print("\nNull counts right after merge (before filling):")
print(merged.isnull().sum(), "\n")


# ---------------------------------------------------------------------------
# STEP 5 — Handle missing values
# ---------------------------------------------------------------------------
# Why: After an outer merge, hours that existed in one dataset but not
# another will have NaN in those columns. We treat each type differently:
#
# crime_count  → NaN means no crimes recorded that hour → fill with 0
# avg_lat/lon  → NaN when crime_count is 0; fill with 0 (no center point)
# sensor cols  → NaN means the sensor missed a reading; forward fill
#                ("last known reading is still valid")

# Crime columns: absence of crime events = zero, not unknown
merged["crime_count"]   = merged["crime_count"].fillna(0)
merged["avg_latitude"]  = merged["avg_latitude"].fillna(0)
merged["avg_longitude"] = merged["avg_longitude"].fillna(0)

# Sensor columns: propagate the last known reading forward in time
# ffill() = forward fill: replace NaN with the nearest non-NaN above it
merged = merged.ffill()

# bfill() = backward fill: catches NaNs at the very start of the table
# where ffill has no prior value to copy from
merged = merged.bfill()

print("Null counts after filling:")
print(merged.isnull().sum(), "\n")


# ---------------------------------------------------------------------------
# STEP 6 — Save the merged dataset
# ---------------------------------------------------------------------------
OUTPUT_FILE = "merged_city_data.csv"

# index=True because the timestamp IS meaningful data here —
# it's the primary key every downstream analysis will join on
merged.to_csv(OUTPUT_FILE, index=True)

print(f"Saved '{OUTPUT_FILE}'")
print(f"Final shape: {merged.shape}")
print(f"\nFirst 3 rows:\n{merged.head(3)}")
