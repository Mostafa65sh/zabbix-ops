import React from 'react';
import type { HostHardwareTelemetry } from '../types';

interface HostTelemetryGaugesProps {
  telemetry: HostHardwareTelemetry;
}

export const HostTelemetryGauges: React.FC<HostTelemetryGaugesProps> = ({ telemetry }) => {
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'CRITICAL':
        return '#ef4444';
      case 'WARNING':
        return '#f59e0b';
      case 'NORMAL':
        return '#10b981';
      default:
        return '#64748b';
    }
  };

  const renderGaugeCard = (
    title: string,
    metric: { value: number | null; formatted: string; status: string; unit: string },
    subtext: string
  ) => {
    const color = getStatusColor(metric.status);
    const pct = metric.value !== null ? Math.min(100, Math.max(0, metric.value)) : 0;

    return (
      <div
        className="metric-card"
        style={{
          background: '#1e293b',
          border: '1px solid #334155',
          borderRadius: '8px',
          padding: '16px',
          display: 'flex',
          flexDirection: 'column',
          gap: '8px',
          flex: '1',
          minWidth: '220px'
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span style={{ fontSize: '13px', fontWeight: 600, color: '#94a3b8' }}>{title}</span>
          <span
            style={{
              fontSize: '11px',
              padding: '2px 6px',
              borderRadius: '4px',
              fontWeight: 600,
              background: metric.status === 'NO_DATA' ? '#334155' : `${color}20`,
              color: metric.status === 'NO_DATA' ? '#94a3b8' : color
            }}
          >
            {metric.status}
          </span>
        </div>

        <div style={{ fontSize: '24px', fontWeight: 700, color: metric.value !== null ? '#f8fafc' : '#64748b' }}>
          {metric.formatted}
        </div>

        {/* Visual Progress Bar */}
        <div style={{ height: '6px', width: '100%', background: '#0f172a', borderRadius: '3px', overflow: 'hidden' }}>
          {metric.value !== null && (
            <div
              style={{
                height: '100%',
                width: `${pct}%`,
                background: color,
                borderRadius: '3px',
                transition: 'width 0.3s ease'
              }}
            />
          )}
        </div>

        <div style={{ fontSize: '11px', color: '#64748b', marginTop: '2px' }}>{subtext}</div>
      </div>
    );
  };

  const cpuSubtext = telemetry.cpu_cores ? `${telemetry.cpu_cores} Cores` : 'Cores: NO_DATA';
  const memTotalGB = telemetry.memory_total_bytes ? (telemetry.memory_total_bytes / (1024 ** 3)).toFixed(1) : null;
  const memUsedGB = telemetry.memory_used_bytes ? (telemetry.memory_used_bytes / (1024 ** 3)).toFixed(1) : null;
  const memSubtext = memTotalGB && memUsedGB ? `${memUsedGB} GB / ${memTotalGB} GB` : 'RAM Capacity: NO_DATA';

  const storTotalGB = telemetry.storage_total_bytes ? (telemetry.storage_total_bytes / (1024 ** 3)).toFixed(1) : null;
  const storUsedGB = telemetry.storage_used_bytes ? (telemetry.storage_used_bytes / (1024 ** 3)).toFixed(1) : null;
  const storSubtext = storTotalGB && storUsedGB ? `${storUsedGB} GB / ${storTotalGB} GB` : 'Storage Capacity: NO_DATA';

  return (
    <div className="host-telemetry-gauges" style={{ display: 'flex', gap: '16px', flexWrap: 'wrap', marginBottom: '20px' }}>
      {renderGaugeCard('CPU UTILIZATION', telemetry.cpu_utilization, cpuSubtext)}
      {renderGaugeCard('MEMORY UTILIZATION', telemetry.memory_utilization, memSubtext)}
      {renderGaugeCard('STORAGE UTILIZATION', telemetry.storage_utilization, storSubtext)}
    </div>
  );
};
