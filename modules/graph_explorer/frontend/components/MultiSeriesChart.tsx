import React from 'react';
import type { GraphMetricSeries } from '../types';

interface MultiSeriesChartProps {
  series: GraphMetricSeries[];
  isLoading: boolean;
}

export const MultiSeriesChart: React.FC<MultiSeriesChartProps> = ({ series, isLoading }) => {
  if (isLoading) {
    return (
      <div
        style={{
          height: '360px',
          background: '#1e293b',
          borderRadius: '8px',
          border: '1px solid #334155',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: '#94a3b8'
        }}
      >
        Loading multi-series telemetry graph...
      </div>
    );
  }

  if (series.length === 0) {
    return (
      <div
        style={{
          padding: '60px 0',
          textAlign: 'center',
          background: '#1e293b',
          borderRadius: '8px',
          border: '1px dashed #334155',
          color: '#94a3b8'
        }}
      >
        <h3>No Series Selected</h3>
        <p style={{ fontSize: '13px', marginTop: '8px' }}>
          Choose at least one host and one metric dimension above to plot comparative telemetry.
        </p>
      </div>
    );
  }

  // Dimension properties for SVG
  const width = 800;
  const height = 300;
  const paddingLeft = 45;
  const paddingRight = 20;
  const paddingTop = 20;
  const paddingBottom = 35;

  const minVal = 0;
  const maxVal = 100;

  // Find common time bounds across series
  const allClocks = series.flatMap((s) => s.points.map((p) => p.clock)).filter(Boolean);
  const minClock = allClocks.length > 0 ? Math.min(...allClocks) : 0;
  const maxClock = allClocks.length > 0 ? Math.max(...allClocks) : 1;
  const timeSpan = Math.max(1, maxClock - minClock);

  const getX = (clock: number) => {
    return paddingLeft + ((clock - minClock) / timeSpan) * (width - paddingLeft - paddingRight);
  };

  const getY = (val: number | null) => {
    const v = val !== null ? Math.min(maxVal, Math.max(minVal, val)) : 0;
    return height - paddingBottom - (v / (maxVal - minVal)) * (height - paddingTop - paddingBottom);
  };

  return (
    <div
      className="multi-series-chart-card"
      style={{
        background: '#1e293b',
        border: '1px solid #334155',
        borderRadius: '8px',
        padding: '16px',
        marginBottom: '20px'
      }}
    >
      {/* SVG Canvas */}
      <svg viewBox={`0 0 ${width} ${height}`} style={{ width: '100%', height: 'auto', overflow: 'visible' }}>
        {/* Horizontal grid lines & Y-axis labels */}
        {[0, 25, 50, 75, 100].map((tick) => {
          const y = getY(tick);
          return (
            <g key={tick}>
              <line
                x1={paddingLeft}
                y1={y}
                x2={width - paddingRight}
                y2={y}
                stroke="#334155"
                strokeDasharray={tick === 0 ? undefined : '3 3'}
              />
              <text
                x={paddingLeft - 8}
                y={y + 4}
                textAnchor="end"
                fontSize="10"
                fill="#64748b"
              >
                {tick}%
              </text>
            </g>
          );
        })}

        {/* Render each series path */}
        {series.map((s) => {
          const validPoints = s.points.filter((p) => p.value !== null);
          if (validPoints.length === 0) return null;

          const color = s.color || '#38bdf8';
          const pathD = validPoints.reduce((acc, p, idx) => {
            const x = getX(p.clock);
            const y = getY(p.value);
            return idx === 0 ? `M ${x} ${y}` : `${acc} L ${x} ${y}`;
          }, '');

          return (
            <g key={s.series_id}>
              <path
                d={pathD}
                fill="none"
                stroke={color}
                strokeWidth="2.2"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
              {/* Dot for latest point */}
              {validPoints.length > 0 && (
                <circle
                  cx={getX(validPoints[validPoints.length - 1].clock)}
                  cy={getY(validPoints[validPoints.length - 1].value)}
                  r="3.5"
                  fill={color}
                  stroke="#0f172a"
                  strokeWidth="1.5"
                />
              )}
            </g>
          );
        })}
      </svg>

      {/* X-axis time labels */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          paddingLeft: `${paddingLeft}px`,
          paddingRight: `${paddingRight}px`,
          fontSize: '11px',
          color: '#64748b',
          marginTop: '6px'
        }}
      >
        <span>{allClocks.length > 0 ? new Date(minClock * 1000).toLocaleTimeString() : ''}</span>
        <span>{allClocks.length > 0 ? new Date(maxClock * 1000).toLocaleTimeString() : ''}</span>
      </div>

      {/* Series Legend & Statistics Table */}
      <div style={{ marginTop: '16px', borderTop: '1px solid #334155', paddingTop: '12px' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '12px', textAlign: 'left' }}>
          <thead>
            <tr style={{ color: '#94a3b8', borderBottom: '1px solid #334155' }}>
              <th style={{ padding: '6px' }}>Series</th>
              <th style={{ padding: '6px' }}>Latest</th>
              <th style={{ padding: '6px' }}>Min</th>
              <th style={{ padding: '6px' }}>Max</th>
              <th style={{ padding: '6px' }}>Avg</th>
            </tr>
          </thead>
          <tbody>
            {series.map((s) => (
              <tr key={s.series_id} style={{ borderBottom: '1px solid rgba(51, 65, 85, 0.4)' }}>
                <td style={{ padding: '6px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span
                    style={{
                      width: '10px',
                      height: '10px',
                      borderRadius: '50%',
                      backgroundColor: s.color || '#38bdf8'
                    }}
                  />
                  <span style={{ fontWeight: 600, color: '#f8fafc' }}>{s.metric_label}</span>
                </td>
                <td style={{ padding: '6px', fontWeight: 600, color: s.color || '#38bdf8' }}>
                  {s.latest_value !== null && s.latest_value !== undefined ? `${s.latest_value.toFixed(1)}%` : 'NO_DATA'}
                </td>
                <td style={{ padding: '6px', color: '#94a3b8' }}>
                  {s.min_value !== null && s.min_value !== undefined ? `${s.min_value.toFixed(1)}%` : 'NO_DATA'}
                </td>
                <td style={{ padding: '6px', color: '#94a3b8' }}>
                  {s.max_value !== null && s.max_value !== undefined ? `${s.max_value.toFixed(1)}%` : 'NO_DATA'}
                </td>
                <td style={{ padding: '6px', color: '#94a3b8' }}>
                  {s.avg_value !== null && s.avg_value !== undefined ? `${s.avg_value.toFixed(1)}%` : 'NO_DATA'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
