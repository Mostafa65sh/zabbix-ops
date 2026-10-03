import React from 'react';
import type { TopNItem } from '../types';

interface TopNTableProps {
  items: TopNItem[];
  metricName: string;
  isLoading: boolean;
}

export const TopNTable: React.FC<TopNTableProps> = ({ items, metricName, isLoading }) => {
  if (isLoading) {
    return (
      <div style={{ textAlign: 'center', padding: '60px 0', color: '#94a3b8' }}>
        Loading Top N rankings...
      </div>
    );
  }

  if (items.length === 0) {
    return (
      <div
        style={{
          textAlign: 'center',
          padding: '60px 0',
          background: '#1e293b',
          borderRadius: '8px',
          border: '1px dashed #334155',
          color: '#94a3b8'
        }}
      >
        <h3>No Monitored Hosts Found</h3>
        <p style={{ fontSize: '13px', marginTop: '8px' }}>
          No hosts match the selected metric or group criteria.
        </p>
      </div>
    );
  }

  const getRankBadgeStyle = (rank: number) => {
    if (rank === 1) return { bg: '#ef4444', color: '#fff' };
    if (rank === 2) return { bg: '#f97316', color: '#fff' };
    if (rank === 3) return { bg: '#f59e0b', color: '#000' };
    return { bg: '#334155', color: '#cbd5e1' };
  };

  const getMetricColor = (status: string) => {
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

  return (
    <div
      className="top-n-table-wrapper"
      style={{
        background: '#1e293b',
        border: '1px solid #334155',
        borderRadius: '8px',
        overflow: 'hidden',
        marginBottom: '24px'
      }}
    >
      <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '13px' }}>
        <thead>
          <tr style={{ background: 'rgba(15, 23, 42, 0.6)', borderBottom: '1px solid #334155', color: '#94a3b8' }}>
            <th style={{ padding: '12px 16px', width: '60px', textAlign: 'center' }}>Rank</th>
            <th style={{ padding: '12px 16px' }}>Host</th>
            <th style={{ padding: '12px 16px' }}>IP Address</th>
            <th style={{ padding: '12px 16px' }}>Groups</th>
            <th style={{ padding: '12px 16px', width: '220px' }}>{metricName.toUpperCase()}</th>
            <th style={{ padding: '12px 16px', textAlign: 'right' }}>Active Incidents</th>
          </tr>
        </thead>
        <tbody>
          {items.map((item) => {
            const rankStyle = getRankBadgeStyle(item.rank);
            const metricColor = getMetricColor(item.metric_value.status);
            const pct = item.raw_value !== null ? Math.min(100, Math.max(0, item.raw_value)) : 0;

            return (
              <tr
                key={item.host_id}
                style={{
                  borderBottom: '1px solid rgba(51, 65, 85, 0.5)',
                  transition: 'background 0.2s ease'
                }}
              >
                {/* Rank Badge */}
                <td style={{ padding: '12px 16px', textAlign: 'center' }}>
                  <span
                    style={{
                      display: 'inline-block',
                      width: '24px',
                      height: '24px',
                      lineHeight: '24px',
                      borderRadius: '50%',
                      fontSize: '11px',
                      fontWeight: 700,
                      background: rankStyle.bg,
                      color: rankStyle.color,
                      textAlign: 'center'
                    }}
                  >
                    {item.rank}
                  </span>
                </td>

                {/* Host Info */}
                <td style={{ padding: '12px 16px' }}>
                  <div style={{ fontWeight: 600, color: '#f8fafc' }}>{item.host_name}</div>
                  <div style={{ fontSize: '11px', color: '#64748b' }}>{item.technical_name}</div>
                </td>

                {/* IP Address */}
                <td style={{ padding: '12px 16px', color: '#94a3b8' }}>
                  {item.primary_ip || '—'}
                </td>

                {/* Host Groups */}
                <td style={{ padding: '12px 16px', color: '#cbd5e1' }}>
                  {item.groups.slice(0, 2).join(', ') || 'Unassigned'}
                  {item.groups.length > 2 && (
                    <span style={{ fontSize: '10px', color: '#64748b' }}> +{item.groups.length - 2}</span>
                  )}
                </td>

                {/* Metric Bar & Formatted Value */}
                <td style={{ padding: '12px 16px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                    <span style={{ fontWeight: 700, color: metricColor }}>
                      {item.metric_value.formatted}
                    </span>
                    <span
                      style={{
                        fontSize: '10px',
                        padding: '1px 5px',
                        borderRadius: '3px',
                        background: `${metricColor}20`,
                        color: metricColor,
                        fontWeight: 600
                      }}
                    >
                      {item.metric_value.status}
                    </span>
                  </div>

                  {item.metric_name !== 'problems' && (
                    <div style={{ height: '6px', width: '100%', background: '#0f172a', borderRadius: '3px', overflow: 'hidden' }}>
                      {item.raw_value !== null && (
                        <div
                          style={{
                            height: '100%',
                            width: `${pct}%`,
                            background: metricColor,
                            borderRadius: '3px'
                          }}
                        />
                      )}
                    </div>
                  )}
                </td>

                {/* Incidents Count */}
                <td style={{ padding: '12px 16px', textAlign: 'right' }}>
                  {item.active_problems_count > 0 ? (
                    <span
                      style={{
                        padding: '2px 8px',
                        borderRadius: '12px',
                        fontSize: '11px',
                        fontWeight: 700,
                        background: 'rgba(239, 68, 68, 0.15)',
                        color: '#ef4444'
                      }}
                    >
                      ⚠️ {item.active_problems_count}
                    </span>
                  ) : (
                    <span style={{ color: '#10b981', fontSize: '12px' }}>✓ 0</span>
                  )}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
};
