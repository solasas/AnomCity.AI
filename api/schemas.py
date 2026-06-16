"""
schemas.py
----------
Pydantic models that define the shape of API requests and responses.

Pydantic reads the type annotations and automatically:
  - Parses incoming JSON into the correct Python types
  - Rejects requests with missing or wrong-type fields (returns HTTP 422)
  - Generates the API's interactive documentation at /docs

Think of these classes as contracts:
  CityDataInput  = "here is what the client must send"
  PredictionResponse = "here is what the server will return"
"""

from pydantic import BaseModel, Field


class CityDataInput(BaseModel):
    """
    The JSON body the client sends to POST /predict.
    Every field is required unless a default is provided.
    Field(...) marks a field as required and lets us attach a description.
    """
    crime_count: float = Field(..., description="Number of crimes recorded in this hour", ge=0)
    avg_speed: float   = Field(..., description="Average road speed in km/h", ge=0)
    total_volume: float = Field(..., description="Total vehicle count in this hour", ge=0)
    avg_temperature: float = Field(..., description="Average temperature in °C")
    avg_humidity: float    = Field(..., description="Average humidity percentage", ge=0, le=100)
    total_rainfall: float  = Field(..., description="Total rainfall in mm", ge=0)

    # model_config tells Pydantic to show an example in /docs
    model_config = {
        "json_schema_extra": {
            "example": {
                "crime_count": 12.0,
                "avg_speed": 35.5,
                "total_volume": 8400.0,
                "avg_temperature": 18.2,
                "avg_humidity": 72.0,
                "total_rainfall": 5.3,
            }
        }
    }


class PredictionResponse(BaseModel):
    """What the server sends back after scoring a request."""
    anomaly_score: float  # higher = more anomalous
    is_anomaly: bool      # True if the hour is flagged as anomalous
    message: str          # human-readable interpretation


class HealthResponse(BaseModel):
    """Response body for GET /health."""
    status: str           # "ok" when everything is running
    model_loaded: bool    # False if model failed to load at startup


class AnomalyRecord(BaseModel):
    """One hour of city data with its anomaly score."""
    timestamp: str
    anomaly_score: float
    is_anomaly: bool
    crime_count: float
    avg_speed: float
    total_volume: float
    avg_temperature: float
    avg_humidity: float
    total_rainfall: float
    avg_latitude: float   # geographic center of crimes that hour (0.0 if no crimes)
    avg_longitude: float


class AnomaliesResponse(BaseModel):
    """Response body for GET /anomalies."""
    records: list[AnomalyRecord]   # all records (anomalies + normals) for the chart
    total_anomalies: int           # how many hours were flagged
