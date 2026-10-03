import React from 'react';

interface GraphHeaderProps {
  totalSeries: number;
  timeRange: string;
  onTimeRangeChange: (range: string) => void;
  lastUpdated: string;
  isRefreshing: boolean;
  onRefresh: () => void;
}

export const GraphHeader: React.FC<GraphHeaderProps> = ({
  totalSeries,
  timeRange,
  onTimeRangeChange,
  lastUpdated,
  isRefreshing,
  onRefresh
}) => {
  return (
    <header className="overview-header graph-header">
      <div className="header-left">
        <div className="brand-badge">
          <span className="brand-dot"></span>
          <span className="brand-title">Zabbix Operations UI</span>
          <span className="module-title-separator">/</span>
          <span className="module-title">Graph Explorer</span>
          <span className="count-pill">{totalSeries} active series</span>
        </div>
        <div className="env-pill">
          <span className="env-dot" style={{ backgroundColor: '#10b981' }}></span>
          <span className="env-name">ZABBIX 7.0.5 API (NATIVE)</span>
        </div>
      </div>

      <div className="header-right">
        {/* Time range buttons */}
        <div style={{ display: 'flex', gap: '4px', background: 'rgba(255,255,255,0.05)', padding: '2px', borderRadius: '6px' }}>
          {['1h', '6h', '12h', '24h', '7d', '30d'].map((rng) => (
            <button
              key={rng}
              type="button"
              className={`filter-chip ${timeRange === rng ? 'active' : ''}`}
              style={{
                padding: '4px 8px',
                fontSize: '12px',
                background: timeRange === rng ? '#3b82f6' : 'transparent',
                color: timeRange === rng ? '#fff' : '#94a3b8',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer'
              }}
              onClick={() => onTimeRangeChange(rng)}
            >
              {rng}
            </button>
          ))}
        </div>

        <div className="last-updated-text">
          <span>Sync:</span>
          <strong>{lastUpdated || 'Syncing...'}</strong>
        </div>

        <button
          type="button"
          className={`refresh-btn ${isRefreshing ? 'spinning' : ''}`}
          onClick={onRefresh}
          disabled={isRefreshing}
          title="Manual Refresh"
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2">
            <path d="M21.5 2v6h-6M21.34 15.57a10 10 0 1 1-.57-8.38l5.67-5.19" />
          </svg>
          <span>{isRefreshing ? 'Refreshing...' : 'Refresh'}</span>
        </button>
      </div>
    </header>
  );
};
