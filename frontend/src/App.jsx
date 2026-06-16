/**
 * App.jsx — root component and single source of truth for all data.
 *
 * Data flow:
 *   fetch() → useState → props → AnomalyMap / AnomalyChart / AlertPanel
 *
 * Nothing fetches data except App. Children only render what they receive.
 */

import { useState, useEffect } from 'react';
import AnomalyMap from './components/AnomalyMap';
import AnomalyChart from './components/AnomalyChart';
import AlertPanel from './components/AlertPanel';
import 'leaflet/dist/leaflet.css';

const API_URL = 'http://localhost:8000/anomalies?limit=200';
const POLL_INTERVAL = 30_000; // 30 seconds in milliseconds

export default function App() {
  // useState returns [currentValue, setterFunction].
  // React re-renders this component (and its children) whenever a setter is called.
  const [records, setRecords]         = useState([]);   // all hourly records (for chart)
  const [anomalies, setAnomalies]     = useState([]);   // only flagged records (for map + panel)
  const [totalCount, setTotalCount]   = useState(0);
  const [lastUpdated, setLastUpdated] = useState(null);
  const [error, setError]             = useState(null);
  const [loading, setLoading]         = useState(true);

  async function fetchData() {
    try {
      // fetch() is the browser's built-in HTTP client — no library needed.
      const res = await fetch(API_URL);
      if (!res.ok) throw new Error(`Server returned ${res.status}`);

      // res.json() parses the response body as JSON, also returns a Promise.
      const data = await res.json();

      setRecords(data.records);
      setAnomalies(data.records.filter((r) => r.is_anomaly));
      setTotalCount(data.total_anomalies);
      setLastUpdated(new Date());
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      // finally runs whether try succeeded or catch ran — always clear loading state
      setLoading(false);
    }
  }

  useEffect(() => {
    fetchData(); // fetch immediately when the component first mounts

    // setInterval calls fetchData every POLL_INTERVAL ms after that.
    const interval = setInterval(fetchData, POLL_INTERVAL);

    // Cleanup: when App unmounts, stop the interval.
    // Without this, the interval keeps firing after the component is gone (memory leak).
    return () => clearInterval(interval);
  }, []); // empty [] = run this effect only once, on mount

  return (
    <div style={styles.root}>
      <header style={styles.header}>
        <h1 style={styles.title}>AnomCity.AI — Smart City Anomaly Dashboard</h1>
        <span style={styles.subtitle}>
          {loading
            ? 'Loading…'
            : error
            ? `Error: ${error}`
            : `${anomalies.length} anomalies in view · auto-refreshes every 30s`}
        </span>
      </header>

      <main style={styles.main}>
        {/* Top row: map on the left, alert panel on the right */}
        <div style={styles.topRow}>
          <div style={styles.mapWrapper}>
            {/* Pass only flagged records — the map only needs to place red markers */}
            <AnomalyMap anomalies={anomalies} />
          </div>

          <div style={styles.panelWrapper}>
            <AlertPanel
              anomalies={anomalies}
              totalCount={totalCount}
              lastUpdated={lastUpdated}
            />
          </div>
        </div>

        {/* Bottom row: full-width time-series chart */}
        <div style={styles.chartWrapper}>
          <h2 style={styles.chartTitle}>Anomaly Score Over Time</h2>
          {/* Pass all records so the chart shows full context, not just spikes */}
          <AnomalyChart records={records} />
        </div>
      </main>
    </div>
  );
}

const styles = {
  root: {
    background: '#0d0d1a',
    minHeight: '100vh',
    color: '#eee',
    fontFamily: 'Inter, system-ui, sans-serif',
  },
  header: {
    padding: '16px 24px',
    borderBottom: '1px solid #2a2a4a',
    display: 'flex',
    alignItems: 'baseline',
    gap: '16px',
    flexWrap: 'wrap',
  },
  title: {
    margin: 0,
    fontSize: '20px',
    color: '#fff',
  },
  subtitle: {
    fontSize: '13px',
    color: '#888',
  },
  main: {
    padding: '16px',
    display: 'flex',
    flexDirection: 'column',
    gap: '16px',
  },
  topRow: {
    display: 'flex',
    gap: '16px',
    height: '420px',  // must be explicit so Leaflet has a pixel height to render into
  },
  mapWrapper: {
    flex: 3,          // map takes 3/4 of the row width
    borderRadius: '8px',
    overflow: 'hidden',
    border: '1px solid #2a2a4a',
  },
  panelWrapper: {
    flex: 1,          // alert panel takes 1/4
    minWidth: '220px',
  },
  chartWrapper: {
    background: '#12122a',
    borderRadius: '8px',
    padding: '16px',
    border: '1px solid #2a2a4a',
  },
  chartTitle: {
    margin: '0 0 12px 0',
    fontSize: '15px',
    color: '#ccc',
  },
};
