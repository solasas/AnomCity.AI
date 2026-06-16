/**
 * AnomalyMap.jsx
 *
 * Props:
 *   anomalies  — array of AnomalyRecord objects where is_anomaly === true
 *
 * Renders a Leaflet map centered on Chicago with a red CircleMarker
 * for each anomaly that has valid coordinates.
 */

import { MapContainer, TileLayer, CircleMarker, Tooltip } from 'react-leaflet';
import 'leaflet/dist/leaflet.css'; // Leaflet's own styles — required or the map breaks visually

const CHICAGO_CENTER = [41.8781, -87.6298]; // lat, lng of Chicago city center

export default function AnomalyMap({ anomalies }) {
  // Filter to only anomalies with real Chicago coordinates.
  // avg_latitude=0 means the hour had no crimes (we filled it with 0 on the backend).
  const mappable = anomalies.filter(
    (a) => a.avg_latitude !== 0 && a.avg_longitude !== 0
  );

  return (
    <div style={{ height: '100%', width: '100%', borderRadius: '8px', overflow: 'hidden' }}>
      {/*
        MapContainer sets up the Leaflet map.
        center      — initial [lat, lng] to focus on
        zoom        — initial zoom level (10 shows most of Chicago)
        style       — must give the container explicit height or the map renders blank
        scrollWheelZoom — let users zoom with the mouse wheel
      */}
      <MapContainer
        center={CHICAGO_CENTER}
        zoom={11}
        style={{ height: '100%', width: '100%' }}
        scrollWheelZoom={true}
      >
        {/*
          TileLayer loads the actual map imagery from OpenStreetMap.
          {s}, {z}, {x}, {y} are placeholders Leaflet fills in per tile request.
          attribution is legally required when using OpenStreetMap tiles.
        */}
        <TileLayer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        />

        {/* Render one CircleMarker per mappable anomaly */}
        {mappable.map((anomaly) => (
          <CircleMarker
            key={anomaly.timestamp}          // unique key so React can track each marker
            center={[anomaly.avg_latitude, anomaly.avg_longitude]}
            radius={8}                       // circle size in pixels (screen space, not map units)
            pathOptions={{
              color: 'red',                  // border color
              fillColor: 'red',
              fillOpacity: 0.5 + anomaly.anomaly_score * 0.4, // more opaque = more anomalous
            }}
          >
            {/*
              Tooltip appears on hover over the marker.
              permanent={false} means it only shows on hover, not always.
            */}
            <Tooltip>
              <div>
                <strong>{new Date(anomaly.timestamp).toLocaleString()}</strong>
                <br />Score: {anomaly.anomaly_score.toFixed(3)}
                <br />Crimes: {anomaly.crime_count}
                <br />Rainfall: {anomaly.total_rainfall.toFixed(1)} mm
              </div>
            </Tooltip>
          </CircleMarker>
        ))}
      </MapContainer>
    </div>
  );
}
