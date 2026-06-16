"""
main.py
-------
FastAPI application for the Smart City Anomaly Detection API.

Endpoints:
  GET  /health   — confirms the server and model are ready
  POST /predict  — accepts city sensor data, returns anomaly score and flag

Run with:
  uvicorn api.main:app --reload
"""

import joblib
import numpy as np
import pandas as pd
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from api.schemas import CityDataInput, PredictionResponse, HealthResponse, AnomaliesResponse, AnomalyRecord


# ---------------------------------------------------------------------------
# Model loading via lifespan
# ---------------------------------------------------------------------------
# 'lifespan' is a context manager that wraps the entire server lifetime.
# Code before 'yield' → runs once on startup (before the first request).
# Code after 'yield'  → runs once on shutdown (server is stopping).
#
# We store the model in a plain dict called 'state' so the endpoint
# functions can access it. Using a dict (not a global variable) is safer
# because it avoids subtle bugs with Python's module-level scope.

state: dict = {}

MODEL_PATH = Path(__file__).parent.parent / "anomaly_model.pkl"
# Path(__file__) is this file's path (api/main.py).
# .parent       → the api/ directory
# .parent.parent → the project root (where anomaly_model.pkl lives)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── STARTUP ──────────────────────────────────────────────────────────
    print(f"Loading model from: {MODEL_PATH}")
    if not MODEL_PATH.exists():
        # Server still starts, but /predict will return 503 until model is present
        print("WARNING: model file not found. /predict will be unavailable.")
        state["model"] = None
        state["features"] = []
    else:
        payload = joblib.load(MODEL_PATH)   # loads the dict we saved in detect_anomalies.py
        state["model"]    = payload["model"]
        state["features"] = payload["features"]
        print(f"Model loaded. Features: {state['features']}")

    yield  # server is now running and accepting requests

    # ── SHUTDOWN ─────────────────────────────────────────────────────────
    state.clear()   # release memory; nothing else needed here
    print("Server shutting down.")


# ---------------------------------------------------------------------------
# App instance
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Smart City Anomaly Detection API",
    description="Detects anomalous hours in city sensor data using Isolation Forest.",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS: browsers block requests from a different origin (port counts as different).
# React runs on :5173, FastAPI on :8000 — without this, every fetch() would fail.
# allow_origins lists which frontends are allowed to talk to us.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# GET /health
# ---------------------------------------------------------------------------

@app.get("/health", response_model=HealthResponse)
def health_check():
    """Returns 200 OK with model status. Use this to verify the server is up."""
    return HealthResponse(
        status="ok",
        model_loaded=state.get("model") is not None,
    )


# ---------------------------------------------------------------------------
# POST /predict
# ---------------------------------------------------------------------------

@app.post("/predict", response_model=PredictionResponse)
def predict(data: CityDataInput):
    """
    Accepts one hour of city sensor data and returns an anomaly score.

    Pydantic (via the CityDataInput type hint) has already validated the
    request by the time this function runs — all fields are present and
    correctly typed. If validation failed, FastAPI returned a 422 before
    ever calling this function.
    """

    # Guard: model must be loaded
    if state.get("model") is None:
        raise HTTPException(
            status_code=503,   # 503 = Service Unavailable
            detail="Model is not loaded. Check server logs.",
        )

    model    = state["model"]
    features = state["features"]

    # Build the feature vector in the same order the model was trained on.
    # data is a CityDataInput object; model_dump() converts it to a plain dict.
    data_dict = data.model_dump()

    try:
        # model.predict/score_samples expect a 2D array: shape (n_samples, n_features)
        # We send one sample at a time, so shape is (1, n_features).
        # np.array([[v1, v2, ...]]) creates that shape.
        feature_vector = np.array([[data_dict[f] for f in features]])

        # score_samples returns a negative score; we negate so higher = more anomalous
        score = float(-model.score_samples(feature_vector)[0])

        # predict returns -1 (anomaly) or 1 (normal)
        prediction = model.predict(feature_vector)[0]
        is_anomaly = prediction == -1

    except Exception as e:
        raise HTTPException(
            status_code=500,   # 500 = Internal Server Error
            detail=f"Prediction failed: {str(e)}",
        )

    message = (
        "Anomaly detected: this hour shows unusual patterns."
        if is_anomaly
        else "Normal: this hour is within expected ranges."
    )

    return PredictionResponse(
        anomaly_score=round(score, 6),
        is_anomaly=is_anomaly,
        message=message,
    )


# ---------------------------------------------------------------------------
# GET /anomalies
# ---------------------------------------------------------------------------
DATA_PATH = Path(__file__).parent.parent / "merged_city_data.csv"

@app.get("/anomalies", response_model=AnomaliesResponse)
def get_anomalies(limit: int = 200):
    """
    Returns recent city data records for the dashboard.
    'limit' controls how many hours of history to return (default 200).
    The chart shows all records; the map shows only flagged ones.
    """
    if not DATA_PATH.exists():
        raise HTTPException(status_code=404, detail="merged_city_data.csv not found.")

    df = pd.read_csv(DATA_PATH, parse_dates=["timestamp"])

    # Ensure required columns exist (anomaly columns added by detect_anomalies.py)
    required = {"anomaly_score", "anomaly_flag"}
    if not required.issubset(df.columns):
        raise HTTPException(
            status_code=500,
            detail="Run detect_anomalies.py first to generate anomaly scores.",
        )

    # Fill coordinate columns if missing (they may not exist if crime data had no lat/lon)
    for col in ["avg_latitude", "avg_longitude"]:
        if col not in df.columns:
            df[col] = 0.0

    # Take the most recent `limit` rows for the chart
    df = df.tail(limit).fillna(0)

    records = [
        AnomalyRecord(
            timestamp=str(row["timestamp"]),
            anomaly_score=round(row["anomaly_score"], 6),
            is_anomaly=bool(row["anomaly_flag"]),
            crime_count=row.get("crime_count", 0),
            avg_speed=row.get("avg_speed", 0),
            total_volume=row.get("total_volume", 0),
            avg_temperature=row.get("avg_temperature", 0),
            avg_humidity=row.get("avg_humidity", 0),
            total_rainfall=row.get("total_rainfall", 0),
            avg_latitude=row.get("avg_latitude", 0),
            avg_longitude=row.get("avg_longitude", 0),
        )
        for _, row in df.iterrows()
    ]

    return AnomaliesResponse(
        records=records,
        total_anomalies=int(df["anomaly_flag"].sum()),
    )
