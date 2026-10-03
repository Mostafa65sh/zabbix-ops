import React from 'react';
import type { TelemetrySeriesPoint } from '../types';

interface HostTelemetryChartsProps {
  series: {
    cpu: TelemetrySeriesPoint[];
    memory: TelemetrySeriesPoint[];
    storage: TelemetrySeriesPoint[];
  };
  isLoading: boolean;
}

export const HostTelemetryCharts: React.FC<HostTelemetryChartsProps> = ({ series, isLoading }) => {
  const renderSparkline = (points: TelemetrySeriesPoint[], color: string, title: string) => {
    if (isLoading) {
      return (
        <div style={{ height: '140px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#94a3b8' }}>
          Loading telemetry series...
        </div>
      );
    }

    if (!points || points.length === 0) {
      return (
        <div style={{ height: '140px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#64748b' }}>
          NO_DATA in selected interval
        </div>
      );
    }

    const validPoints = points.filter((p) => p.value !== null);
    if (validPoints.length === 0) {
      return (
        <div style={{ height: '140px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#64748b' }}>
          NO_DATA in selected interval
        </div>
      );
    }

    const minVal = 0;
    const maxVal = 100;
    const width = 500;
    const height = 120;
    const padding = 15;

    const coords = points.map((pt, idx) => {
      const x = padding + (idx / Math.max(1, points.length - 1)) * (width - 2 * padding);
      const val = pt.value !== null ? pt.value : 0;
      const y = height - padding - (val / (maxVal - minVal)) * (height - 2 * padding);
      return { x, y, pt };
    });

    const pathD = coords.reduce((acc, c, idx) => {
      return idx === 0 ? `M ${c.x} ${c.y}` : `${acc} L ${c.x} ${c.y}`;
    }, '');

    const areaD = `${pathD} L ${coords[coords.length - 1].x} ${height - padding} L ${coords[0].x} ${height - padding} Z`;

    const latestVal = validPoints[validPoints.length - 1].value;

    return (
      <div
        className="telemetry-chart-card"
        style={{
          background: '#1e293b',
          border: '1px solid #334155',
          borderRadius: '8px',
          padding: '16px',
          flex: '1',
          minWidth: '300px'
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
          <span style={{ fontSize: '13px', fontWeight: 600, color: '#cbd5e1' }}>{title}</span>
          <span style={{ fontSize: '14px', fontWeight: 700, color }}>
            {latestVal !== null ? `${latestVal.toFixed(1)}%` : 'NO_DATA'}
          </span>
        </div>

        <svg viewBox={`0 0 ${width} ${height}`} style={{ width: '100%', height: '120px', overflow: 'visible' }}>
          <defs>
            <linearGradient id={`grad-${title}`} x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={color} stopOpacity="0.3" />
              <stop offset="100%" stopColor={color} stopOpacity="0.0" />
            </linearGradient>
          </defs>

          {/* Grid lines */}
          <line x1={padding} y1={padding} x2={width - padding} y2={padding} stroke="#334155" strokeDasharray="3 3" />
          <line x1={padding} y1={height / 2} x2={width - padding} y2={height / 2} stroke="#334155" strokeDasharray="3 3" />
          <line x1={padding} y1={height - padding} x2={width - padding} y2={height - padding} stroke="#334155" />

          {/* Area and Line */}
          <path d={areaD} fill={`url(#grad-${title})`} />
          <path d={pathD} fill="none" stroke={color} strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />

          {/* Latest Point Dot */}
          {coords.length > 0 && (
            <circle
              cx={coords[coords.length - 1].x}
              cy={coords[coords.length - 1].y}
              r="4"
              fill={color}
              stroke="#0f172a"
              strokeWidth="2"
            />
          )}
        </svg>

        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '10px', color: '#64748b', marginTop: '4px' }}>
          <span>{points[0]?.timestamp_iso?.slice(11, 16) || ''}</span>
          <span>{points[points.length - 1]?.timestamp_iso?.slice(11, 16) || ''}</span>
        </div>
      </div>
    );
  };

  return (
    <div className="host-telemetry-charts" style={{ display: 'flex', gap: '16px', flexWrap: 'wrap', marginBottom: '24px' }}>
      {renderSparkline(series.cpu, '#38bdf8', 'CPU History')}
      {renderSparkline(series.memory, '#a855f7', 'Memory History')}
      {renderSparkline(series.storage, '#3b82f6', 'Storage History')}
    </div>
  );
};
