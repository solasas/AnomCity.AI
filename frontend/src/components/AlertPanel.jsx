/**
 * AlertPanel.jsx
 *
 * Props:
 *   anomalies    — array of AnomalyRecord objects where is_anomaly === true
 *   totalCount   — total number of flagged hours (from the backend)
 *   lastUpdated  — Date object set by App each time it fetches
 */

export default function AlertPanel({ anomalies, totalCount, lastUpdated }) {
  // Show the 20 most recent anomalies, sorted newest first
  const sorted = [...anomalies]
    .sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp))
    .slice(0, 20);

  return (
    <div style={styles.panel}>
      <h3 style={styles.heading}>Anomaly Alerts</h3>

      <div style={styles.summary}>
        <span style={styles.badge}>{totalCount}</span> flagged hours total
      </div>

      {lastUpdated && (
        <p style={styles.lastUpdated}>
          Updated: {lastUpdated.toLocaleTimeString()}
        </p>
      )}

      {/* Scrollable list of alert cards */}
      <div style={styles.list}>
        {sorted.length === 0 && (
          <p style={{ color: '#888', fontSize: '13px' }}>No anomalies in current window.</p>
        )}

        {sorted.map((a) => (
          /*
            Each card is keyed by timestamp (unique per hour).
            The red left border reinforces the "alert" visual metaphor.
            Score brightness encodes severity — higher score = deeper red border.
          */
          <div key={a.timestamp} style={styles.card}>
            <p style={styles.time}>{new Date(a.timestamp).toLocaleString()}</p>
            <p style={styles.score}>
              Score: <strong style={{ color: scoreColor(a.anomaly_score) }}>
                {a.anomaly_score.toFixed(4)}
              </strong>
            </p>
            <p style={styles.detail}>
              Crimes: {a.crime_count} &nbsp;|&nbsp;
              Rain: {a.total_rainfall.toFixed(1)} mm
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}

// Maps an anomaly score (roughly 0.5–0.7) to a red shade.
// Higher score → more saturated red so severe alerts stand out visually.
function scoreColor(score) {
  const intensity = Math.min(255, Math.round(score * 380));
  return `rgb(${intensity}, 60, 60)`;
}

// All styles in one object — no external CSS file needed for a simple panel
const styles = {
  panel: {
    background: '#1a1a2e',
    border: '1px solid #2a2a4a',
    borderRadius: '8px',
    padding: '16px',
    height: '100%',
    display: 'flex',
    flexDirection: 'column',
    color: '#eee',
    fontFamily: 'monospace',
  },
  heading: {
    margin: '0 0 12px 0',
    fontSize: '16px',
    color: '#fff',
    borderBottom: '1px solid #2a2a4a',
    paddingBottom: '8px',
  },
  summary: {
    fontSize: '13px',
    marginBottom: '4px',
    color: '#aaa',
  },
  badge: {
    background: 'red',
    color: '#fff',
    borderRadius: '4px',
    padding: '1px 6px',
    fontSize: '12px',
    fontWeight: 'bold',
    marginRight: '6px',
  },
  lastUpdated: {
    fontSize: '11px',
    color: '#666',
    margin: '4px 0 12px 0',
  },
  list: {
    overflowY: 'auto',    // scroll when content exceeds panel height
    flex: 1,              // take remaining vertical space in the flex column
  },
  card: {
    borderLeft: '3px solid red',
    paddingLeft: '10px',
    marginBottom: '12px',
    background: '#12122a',
    borderRadius: '0 4px 4px 0',
    padding: '8px 8px 8px 12px',
  },
  time: {
    fontSize: '11px',
    color: '#aaa',
    margin: '0 0 4px 0',
  },
  score: {
    fontSize: '13px',
    margin: '0 0 2px 0',
  },
  detail: {
    fontSize: '11px',
    color: '#888',
    margin: 0,
  },
};
