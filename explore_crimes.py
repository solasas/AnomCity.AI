"""
explore_crimes.py
-----------------
Downloads a slice of the Chicago Crime dataset, inspects it,
filters for 2023 records, and saves the result to CSV.

Libraries used:
  - requests : makes HTTP requests (like a browser, but in Python)
  - pandas   : loads and manipulates tabular data (think: Python Excel)
  - io       : lets us treat a string as a file so pandas can read it
"""

import requests
import pandas as pd
import io  # part of Python's standard library — no pip install needed


# ---------------------------------------------------------------------------
# STEP 1 — Define the download helper
# ---------------------------------------------------------------------------
# The City of Chicago uses Socrata to publish open data.
# Socrata exposes every dataset as an API you can query with URL params.
#
# Dataset ID for Chicago Crime: ijzp-q8t2
# Base URL pattern: https://data.cityofchicago.org/resource/<id>.csv
#
# Why fetch two years separately instead of one request with both?
# Chicago has ~300,000 crimes per year. If we ask for 2022 OR 2023 in one
# request with $limit=100000, we fill all slots with 2022 records first
# (they come first in sort order) and never reach 2023.
# Fetching each year independently guarantees we get records from both,
# so Step 5's pandas filter actually has two years to choose between.

BASE_URL = "https://data.cityofchicago.org/resource/ijzp-q8t2.csv"
ROWS_PER_YEAR = 50_000  # 50k rows × 2 years = 100k total; manageable in memory


def fetch_year(year: int) -> pd.DataFrame:
    """Download up to ROWS_PER_YEAR crime records for a single year."""
    params = {
        "$where": f"year={year}",   # Socrata SQL-style filter; f-string injects the year
        "$limit": ROWS_PER_YEAR,    # cap how many rows the server sends back
        "$order": "date ASC",       # oldest-first within the year (arbitrary; just consistent)
    }
    print(f"  Fetching {year} data...")
    response = requests.get(BASE_URL, params=params, timeout=180)
    response.raise_for_status()     # crash loudly if the server returned an error status

    # io.StringIO makes the CSV string look like an open file so pd.read_csv accepts it
    return pd.read_csv(io.StringIO(response.text))


# ---------------------------------------------------------------------------
# STEP 2 — Download 2022 and 2023, then combine into one DataFrame
# ---------------------------------------------------------------------------

print("Downloading dataset...")
df_2022 = fetch_year(2022)
df_2023_raw = fetch_year(2023)

# pd.concat() stacks DataFrames vertically (row-wise).
# ignore_index=True renumbers the rows from 0 instead of keeping each
# sub-frame's original index — prevents duplicate index values after merging.
df = pd.concat([df_2022, df_2023_raw], ignore_index=True)

print(f"Download complete. Total rows combined: {len(df):,}\n")


# ---------------------------------------------------------------------------
# STEP 3 — Inspect the combined DataFrame
# ---------------------------------------------------------------------------

print("=" * 50)
print("SHAPE  (rows, columns)")
print("=" * 50)
# df.shape is a tuple — (number_of_rows, number_of_columns)
print(df.shape)

print("\n" + "=" * 50)
print("COLUMN NAMES")
print("=" * 50)
# df.columns is a pandas Index object; .tolist() converts it to a plain Python list
# Note: Socrata API returns column names in lowercase (e.g. "year", not "Year")
print(df.columns.tolist())

print("\n" + "=" * 50)
print("DATA TYPES  (per column)")
print("=" * 50)
# df.dtypes tells you how pandas stored each column:
#   object  = string / mixed types
#   int64   = integer (64-bit)
#   float64 = decimal number (64-bit)
#   bool    = True / False
print(df.dtypes)

print("\n" + "=" * 50)
print("NULL COUNTS  (missing values per column)")
print("=" * 50)
# df.isnull() returns a True/False DataFrame — True wherever a value is missing.
# .sum() counts True values per column (True == 1, False == 0 in Python).
print(df.isnull().sum())

# Show how many rows we have per year — confirms the concat worked as intended
print("\n" + "=" * 50)
print("ROWS PER YEAR  (pre-filter)")
print("=" * 50)
# .value_counts() counts occurrences of each unique value in a column
print(df["year"].value_counts().sort_index())


# ---------------------------------------------------------------------------
# STEP 4 — Filter for 2023 records
# ---------------------------------------------------------------------------
# Boolean indexing: df[condition] keeps only the rows where condition is True.
#
# df["year"] == 2023  creates a Series of True/False values, one per row.
# Passing that Series into df[...] selects only the rows marked True.
#
# We use lowercase "year" because the Socrata API lowercases all column names.

df_2023 = df[df["year"] == 2023]

print("\n" + "=" * 50)
print(f"RECORDS FROM 2023: {len(df_2023):,}")  # :, adds thousands separator (e.g. 12,345)
print("=" * 50)

# Sanity check — confirm only 2023 appears in the filtered frame
print("Unique years in filtered data:", df_2023["year"].unique())


# ---------------------------------------------------------------------------
# STEP 5 — Save the cleaned file
# ---------------------------------------------------------------------------
OUTPUT_FILE = "crime_clean.csv"

# to_csv() writes the DataFrame to a CSV file.
# index=False prevents pandas from writing the row numbers (0, 1, 2…)
# as an extra unnamed column — you almost never want those in output files.
df_2023.to_csv(OUTPUT_FILE, index=False)

print(f"\nSaved {len(df_2023):,} rows to '{OUTPUT_FILE}'.")
print("Done!")
