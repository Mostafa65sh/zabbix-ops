import React from 'react';

interface TopNHeaderProps {
  totalEvaluated: number;
  lastUpdated: string;
  isRefreshing: boolean;
  onRefresh: () => void;
  selectedMetric: string;
  onMetricChange: (metric: 'cpu' | 'memory' | 'storage' | 'problems') => void;
  limit: number;
  onLimitChange: (limit: number) => void;
  group: string;
  onGroupChange: (group: string) => void;
}

export const TopNHeader: React.FC<TopNHeaderProps> = ({
  totalEvaluated,
  lastUpdated,
  isRefreshing,
  onRefresh,
  selectedMetric,
  onMetricChange,
  limit,
  onLimitChange,
  group,
  onGroupChange
}) => {
  return (
    <header className="overview-header topn-header">
      <div className="header-left">
        <div className="brand-badge">
          <span className="brand-dot"></span>
          <span className="brand-title">Zabbix Operations UI</span>
          <span className="module-title-separator">/</span>
          <span className="module-title">Top N Rankings</span>
          <span className="count-pill">{totalEvaluated} hosts evaluated</span>
        </div>
        <div className="env-pill">
          <span className="env-dot" style={{ backgroundColor: '#10b981' }}></span>
          <span className="env-name">ZABBIX 7.0.5 API (NATIVE)</span>
        </div>
      </div>

      <div className="header-right">
        {/* Metric Selector Chips */}
        <div style={{ display: 'flex', gap: '4px', background: 'rgba(255,255,255,0.05)', padding: '2px', borderRadius: '6px' }}>
          {(['cpu', 'memory', 'storage', 'problems'] as const).map((m) => (
            <button
              key={m}
              type="button"
              className={`filter-chip ${selectedMetric === m ? 'active' : ''}`}
              style={{
                padding: '4px 10px',
                fontSize: '12px',
                fontWeight: 600,
                background: selectedMetric === m ? '#3b82f6' : 'transparent',
                color: selectedMetric === m ? '#fff' : '#94a3b8',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer',
                textTransform: 'uppercase'
              }}
              onClick={() => onMetricChange(m)}
            >
              {m}
            </button>
          ))}
        </div>

        {/* Limit Selector */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <span style={{ fontSize: '12px', color: '#94a3b8' }}>Top:</span>
          <select
            value={limit}
            onChange={(e) => onLimitChange(Number(e.target.value))}
            style={{
              padding: '4px 8px',
              fontSize: '12px',
              background: '#1e293b',
              border: '1px solid #334155',
              borderRadius: '4px',
              color: '#f8fafc',
              cursor: 'pointer'
            }}
          >
            <option value={5}>5</option>
            <option value={10}>10</option>
            <option value={20}>20</option>
            <option value={50}>50</option>
          </select>
        </div>

        {/* Group Filter Input */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
          <input
            type="text"
            placeholder="Host group..."
            value={group}
            onChange={(e) => onGroupChange(e.target.value)}
            style={{
              padding: '4px 8px',
              fontSize: '12px',
              background: '#1e293b',
              border: '1px solid #334155',
              borderRadius: '4px',
              color: '#f8fafc',
              maxWidth: '120px'
            }}
          />
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
