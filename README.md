# AnomCity.AI

A Smart City Anomaly Detection Dashboard — a learning project built with Python + FastAPI (backend) and React (frontend).

---

## What's been built so far

### 1. Project setup
- `CLAUDE.md` — gives future Claude Code sessions context about this project (stack, goals, etc.)
- Installed Python libraries: `requests` and `pandas`

---

### 2. `explore_crimes.py` — data pipeline script

This script does five things in sequence:

**Downloads real crime data from the internet**
The City of Chicago publishes its crime database publicly via an API (called Socrata). We use `requests.get()` to fetch CSV data — the same way a browser loads a webpage, except we get raw text back instead of a rendered page. We make two separate requests (one for 2022, one for 2023) because the dataset has ~300,000 crimes per year and a single request with both years would fill its row limit entirely with 2022 data, leaving no room for 2023.

**Combines the two downloads into one table**
`pd.concat()` stacks the two DataFrames vertically — like stacking two spreadsheets on top of each other — giving us 100,000 rows total (50k per year).

**Inspects the data**
We print four things:
- **Shape** `(100000, 22)` — 100,000 rows, 22 columns
- **Column names** — the 22 fields available (case number, date, block, crime type, arrest status, coordinates, etc.)
- **Data types** — how pandas stored each column (`int64`, `float64`, `object`, `bool`)
- **Null counts** — how many missing values each column has. Key finding: `latitude`, `longitude`, `x_coordinate`, and `location` are all missing 1,939 values *together* — they blank out as a group whenever an address can't be geocoded

**Filters for 2023 using boolean indexing**
```python
df_2023 = df[df["year"] == 2023]
```
`df["year"] == 2023` produces a column of `True`/`False` values. Wrapping it in `df[...]` keeps only the rows marked `True`. This dropped the 50,000 2022 rows and kept the 50,000 2023 rows.

**Saves the result**
`df_2023.to_csv("crime_clean.csv", index=False)` writes the filtered data to disk. `index=False` prevents pandas from adding an unwanted row-number column to the file.

---

## Project structure

```
Smart City Anomaly Detection/
├── CLAUDE.md           ← project guidance for Claude Code
├── explore_crimes.py   ← data pipeline script
└── crime_clean.csv     ← 50,000 cleaned 2023 crime records
```

---

## How the pieces fit together

```
[explore_crimes.py]  →  crime_clean.csv
                              ↓
                       FastAPI backend  →  React dashboard
```

`crime_clean.csv` is the raw material for everything that comes next.

---

## Stack

| Layer    | Technology       |
|----------|-----------------|
| Backend  | Python + FastAPI |
| Frontend | React            |
| Data     | Chicago Open Data Portal (Socrata API) |

---

## Roadmap

- [x] Data collection and cleaning (`explore_crimes.py`)
- [ ] Anomaly detection — find unusual patterns in crime type, location, and time
- [ ] FastAPI backend — serve data and anomaly results as a JSON API
- [ ] React frontend — visualize as an interactive dashboard
