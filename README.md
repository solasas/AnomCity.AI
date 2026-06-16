# AnomCity.AI — Smart City Anomaly Detection Dashboard

AnomCity.AI is a full-stack data science learning project that ingests real Chicago city data (crime reports, traffic readings, weather measurements), detects unusual patterns using machine learning, and visualizes the results on a live interactive dashboard.

The goal is not just to build something that works — it's to understand every layer: how raw public data becomes a trained model, how a model becomes an API, and how an API becomes a dashboard a real user can read.

---

## What the project does

Every hour of a city generates dozens of signals — how many crimes were reported, how fast traffic is moving, whether it's raining. Most hours are ordinary. A few are not: a sudden spike in crimes during a storm with gridlocked roads is unusual in a way that no single signal reveals on its own.

This project:
1. Pulls real 2023 crime data from the City of Chicago's open data portal
2. Combines it with simulated traffic and weather readings into a single hourly dataset
3. Trains an Isolation Forest model to score each hour by how anomalous it is
4. Serves those scores through a REST API
5. Displays them on a React dashboard with a live map, time-series chart, and alert panel

---

## Architecture

```
Chicago Open Data API
        ↓
  explore_crimes.py        ← downloads + cleans crime records
        ↓
  merge_city_data.py       ← resamples + merges crime / traffic / weather
        ↓
  detect_anomalies.py      ← trains Isolation Forest, scores every hour
        ↓
  merged_city_data.csv     ← 8,760 rows (one per hour of 2023) with anomaly scores
        ↓
  FastAPI backend           ← serves /health, /predict, /anomalies
        ↓
  React frontend            ← map + chart + alert panel, polls every 30 seconds
```

---

## Project structure

```
AnomCity.AI/
├── api/
│   ├── __init__.py          ← makes api/ a Python package
│   ├── main.py              ← FastAPI app: startup, CORS, endpoints
│   └── schemas.py           ← Pydantic request/response models
├── frontend/
│   └── src/
│       ├── App.jsx               ← data fetching, state, layout
│       └── components/
│           ├── AnomalyMap.jsx    ← Leaflet map with red anomaly markers
│           ├── AnomalyChart.jsx  ← Recharts time-series of anomaly scores
│           └── AlertPanel.jsx    ← scrollable list of flagged hours
├── explore_crimes.py        ← Step 1: download + clean crime data
├── merge_city_data.py       ← Step 2: standardize + merge all datasets
├── generate_sample_data.py  ← generates sample traffic + weather CSVs for testing
├── detect_anomalies.py      ← Step 3: train model, score data, save model
├── anomaly_model.pkl        ← saved Isolation Forest (joblib)
├── merged_city_data.csv     ← final dataset with anomaly_score + anomaly_flag
└── requirements.txt
```

---

## Stack

| Layer | Technology | Purpose |
|---|---|---|
| Data collection | Python, `requests`, `pandas` | Download and clean public datasets |
| ML model | `scikit-learn` IsolationForest | Unsupervised anomaly detection |
| Model persistence | `joblib` | Save/load trained model |
| Backend | Python, FastAPI, Pydantic | REST API with validation |
| Frontend | React, Vite | Interactive dashboard UI |
| Map | react-leaflet, Leaflet, OpenStreetMap | Geographic anomaly visualization |
| Chart | Recharts | Time-series score plot |
| Data source | Chicago Open Data Portal (Socrata API) | Real crime records |

---

## Core concepts

### Socrata API & HTTP requests
The City of Chicago publishes datasets through Socrata, a platform that exposes every dataset as a queryable API endpoint. `requests.get(url, params={...})` sends an HTTP GET request — the same thing a browser does — and returns the raw CSV text. Query parameters like `$limit` and `$where` let you filter data at the source before downloading, which matters when the full dataset has 8 million rows.

### Pandas DataFrames
A DataFrame is a 2D table — rows are observations, columns are variables. Key operations used here:
- **`pd.read_csv()`** — parses CSV text into a DataFrame
- **`pd.concat()`** — stacks DataFrames vertically (row-wise) or horizontally (column-wise)
- **`resample("h").agg(...)`** — groups rows into hourly buckets and summarizes each column (mean, sum, count)
- **Boolean indexing** — `df[df["year"] == 2023]` creates a True/False mask and keeps only True rows
- **`ffill()` / `bfill()`** — forward/backward fill to propagate the last known value into missing gaps

### Time-series resampling and merging
Crime events, traffic readings, and weather measurements are recorded at different frequencies. To merge them, they must all live on the same time grid. `resample("h")` collapses every observation within a one-hour window into a single summary row. After resampling, `pd.concat(axis=1)` aligns the three DataFrames by their shared hourly index into one wide table.

### Isolation Forest (unsupervised anomaly detection)
Isolation Forest works by building random decision trees and measuring how many cuts it takes to isolate each data point from all others. Points that are isolated quickly (few cuts needed) are anomalies — they sit far from the crowd. Points that require many cuts are normal — they cluster with others. The model never needs labelled training data; it infers "normal" purely from the structure of the dataset. The output is an anomaly score per row: higher = more anomalous.

### FastAPI and Pydantic
FastAPI is a Python web framework that turns annotated Python functions into HTTP endpoints. Pydantic models define the shape of request and response bodies using Python type annotations. When a request arrives, FastAPI automatically parses the JSON, validates every field's type, and returns a structured 422 error if anything is missing or wrong — with no manual validation code required. The `lifespan` context manager handles startup logic (loading the model) and shutdown cleanup.

### CORS (Cross-Origin Resource Sharing)
Browsers block JavaScript from making HTTP requests to a different origin (domain + port) than the page itself. The React app runs on `localhost:5173` and the API on `localhost:8000` — different origins. The FastAPI CORS middleware adds response headers that tell the browser those cross-origin requests are allowed.

### React state and props
State is data that lives inside a component and causes it to re-render when it changes. Props are values passed from a parent component to a child. In this project, `App.jsx` owns all state (the fetched data) and passes slices down to `AnomalyMap`, `AnomalyChart`, and `AlertPanel` as props. Children never fetch data — they only render what they receive. This pattern (one owner, many renderers) keeps data flow predictable.

### Polling with `useEffect` and `setInterval`
`useEffect(() => { ... }, [])` runs once after the component mounts — used here to start a 30-second polling interval. `setInterval(fetchData, 30000)` calls `fetchData` repeatedly. The cleanup function returned from `useEffect` (`return () => clearInterval(interval)`) stops the interval when the component unmounts, preventing memory leaks.

### react-leaflet and Recharts
`react-leaflet` wraps the Leaflet.js mapping library in React components. `MapContainer` sets up the map, `TileLayer` loads OpenStreetMap tiles, and `CircleMarker` places a styled circle at a lat/lng coordinate. `Recharts` wraps SVG charts in React components — you pass your data array and declare which fields map to which axis using `dataKey`. `ResponsiveContainer` auto-sizes the chart to its parent element's width.

---

## Running locally

**Backend**
```bash
pip install -r requirements.txt

# One-time setup: build the dataset and train the model
python explore_crimes.py
python generate_sample_data.py
python merge_city_data.py
python detect_anomalies.py

# Start the API
uvicorn api.main:app --reload --port 8000
```

**Frontend**
```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`.  
API docs available at `http://localhost:8000/docs`.

---

## Roadmap

- [x] Data collection and cleaning (`explore_crimes.py`)
- [x] Multi-source data merge and resampling (`merge_city_data.py`)
- [x] Isolation Forest anomaly detection (`detect_anomalies.py`)
- [x] FastAPI backend with `/health`, `/predict`, `/anomalies`
- [x] React dashboard — Leaflet map, Recharts time-series, alert panel
- [ ] Resident notification system (email / SMS on anomaly detection)
- [ ] Deployment (backend on Render/Railway, frontend on Vercel)
