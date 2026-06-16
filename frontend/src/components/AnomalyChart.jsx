/**
 * AnomalyChart.jsx
 *
 * Props:
 *   records — full array of AnomalyRecord objects (anomalies + normals)
 *
 * Renders a time-series line chart of anomaly_score across all hours.
 * Red dots mark flagged hours so you can see spikes in context.
 */

import {
  ResponsiveContainer, // auto-sizes the chart to its container's width
  LineChart,           // the chart type (vs BarChart, AreaChart, etc.)
  Line,                // one data series drawn as a line
  XAxis,               // horizontal axis
  YAxis,               // vertical axis
  CartesianGrid,       // background grid lines
  Tooltip,             // popup showing values on hover
  ReferenceLine,       // horizontal line we draw at the anomaly threshold
  Legend,              // color key below the chart
} from 'recharts';

// Custom dot: render a red dot only on anomaly hours, nothing on normal hours.
// Recharts calls this function for every data point and renders what you return.
function AnomalyDot(props) {
  const { cx, cy, payload } = props; // cx/cy = pixel coords; payload = the data object
  if (!payload.is_anomaly) return null; // return null = render nothing for normal hours
  return <circle cx={cx} cy={cy} r={4} fill="red" stroke="none" />;
}

// Formats the timestamp for the X axis label — show only month/day to save space
function formatTick(timestamp) {
  const d = new Date(timestamp);
  return `${d.getMonth() + 1}/${d.getDate()}`; // e.g. "1/7"
}

export default function AnomalyChart({ records }) {
  if (!records.length) {
    return <p style={{ textAlign: 'center', color: '#888' }}>No data yet.</p>;
  }

  // The threshold is the minimum score among flagged hours (same cutoff the model uses)
  const flaggedScores = records
    .filter((r) => r.is_anomaly)
    .map((r) => r.anomaly_score);
  const threshold = flaggedScores.length ? Math.min(...flaggedScores) : null;

  return (
    /*
      ResponsiveContainer takes width/height as % of the parent.
      height={260} is the fixed pixel height; width="100%" fills the container.
    */
    <ResponsiveContainer width="100%" height={260}>
      <LineChart
        data={records}
        margin={{ top: 10, right: 20, left: 0, bottom: 0 }}
      >
        <CartesianGrid strokeDasharray="3 3" stroke="#2a2a3a" />

        {/*
          dataKey="timestamp" tells XAxis which field to use for labels.
          tickFormatter formats each tick label — we show only month/day.
          interval="preserveStartEnd" only renders first + last ticks
          plus a few in between, avoiding crowding on small screens.
        */}
        <XAxis
          dataKey="timestamp"
          tickFormatter={formatTick}
          interval="preserveStartEnd"
          tick={{ fill: '#aaa', fontSize: 11 }}
        />
        <YAxis
          domain={['auto', 'auto']}   // auto-scales to the data range
          tick={{ fill: '#aaa', fontSize: 11 }}
          label={{ value: 'Score', angle: -90, position: 'insideLeft', fill: '#aaa', fontSize: 11 }}
        />

        {/* Tooltip shows all field values for the hovered data point */}
        <Tooltip
          contentStyle={{ background: '#1a1a2e', border: '1px solid #444', borderRadius: '6px' }}
          labelStyle={{ color: '#eee' }}
          itemStyle={{ color: '#8884d8' }}
          labelFormatter={(v) => new Date(v).toLocaleString()}
          formatter={(value) => [value.toFixed(4), 'Anomaly Score']}
        />

        <Legend wrapperStyle={{ color: '#aaa' }} />

        {/* Red dashed line at the threshold — everything above is an anomaly */}
        {threshold && (
          <ReferenceLine
            y={threshold}
            stroke="red"
            strokeDasharray="4 2"
            label={{ value: 'Threshold', fill: 'red', fontSize: 11 }}
          />
        )}

        {/*
          The main line. dot={<AnomalyDot />} replaces the default dot renderer
          with our custom one that only draws a red dot for anomaly hours.
          isAnimationActive={false} disables the draw animation on re-fetch
          so the chart doesn't flash every 30 seconds.
        */}
        <Line
          type="monotone"        // smooth curve connecting points
          dataKey="anomaly_score"
          stroke="#8884d8"
          strokeWidth={1.5}
          dot={<AnomalyDot />}
          isAnimationActive={false}
          name="Anomaly Score"
        />
      </LineChart>
    </ResponsiveContainer>
  );
}
