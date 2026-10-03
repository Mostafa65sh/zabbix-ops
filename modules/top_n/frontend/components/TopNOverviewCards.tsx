import React from 'react';
import type { TopNItem } from '../types';

interface TopNOverviewCardsProps {
  cpu: TopNItem[];
  memory: TopNItem[];
  storage: TopNItem[];
  problems: TopNItem[];
  onSelectDimension: (dim: 'cpu' | 'memory' | 'storage' | 'problems') => void;
}

export const TopNOverviewCards: React.FC<TopNOverviewCardsProps> = ({
  cpu,
  memory,
  storage,
  problems,
  onSelectDimension
}) => {
  const renderCard = (
    title: string,
    dimension: 'cpu' | 'memory' | 'storage' | 'problems',
    items: TopNItem[],
    accentColor: string
  ) => {
    return (
      <div
        className="top-n-mini-card"
        style={{
          background: '#1e293b',
          border: '1px solid #334155',
          borderRadius: '8px',
          padding: '16px',
          flex: '1',
          minWidth: '240px',
          display: 'flex',
          flexDirection: 'column',
          gap: '12px'
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span style={{ fontSize: '13px', fontWeight: 700, color: '#f8fafc', textTransform: 'uppercase' }}>
            {title}
          </span>
          <button
            type="button"
            onClick={() => onSelectDimension(dimension)}
            style={{
              background: 'transparent',
              border: 'none',
              color: '#38bdf8',
              fontSize: '11px',
              cursor: 'pointer',
              fontWeight: 600
            }}
          >
            View All →
          </button>
        </div>

        {items.length === 0 ? (
          <div style={{ fontSize: '12px', color: '#64748b', padding: '16px 0', textAlign: 'center' }}>
            No data available
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {items.slice(0, 5).map((item) => (
              <div
                key={item.host_id}
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  fontSize: '12px',
                  padding: '4px 0',
                  borderBottom: '1px solid rgba(51, 65, 85, 0.3)'
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', overflow: 'hidden' }}>
                  <span style={{ fontSize: '11px', color: '#94a3b8', width: '14px' }}>#{item.rank}</span>
                  <span
                    style={{
                      color: '#e2e8f0',
                      whiteSpace: 'nowrap',
                      textOverflow: 'ellipsis',
                      overflow: 'hidden',
                      maxWidth: '120px'
                    }}
                    title={item.host_name}
                  >
                    {item.host_name}
                  </span>
                </div>
                <span style={{ fontWeight: 700, color: accentColor }}>
                  {item.metric_value.formatted}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    );
  };

  return (
    <div
      className="top-n-overview-grid"
      style={{
        display: 'flex',
        gap: '16px',
        flexWrap: 'wrap',
        marginBottom: '24px'
      }}
    >
      {renderCard('Top CPU Util', 'cpu', cpu, '#38bdf8')}
      {renderCard('Top Memory Util', 'memory', memory, '#a855f7')}
      {renderCard('Top Storage Util', 'storage', storage, '#3b82f6')}
      {renderCard('Top Incidents', 'problems', problems, '#ef4444')}
    </div>
  );
};
