import React from 'react';

interface AvailabilityHeaderProps {
  timeRange: string;
  onTimeRangeChange: (newRange: string) => void;
  onRefresh: () => void;
  isLoading: boolean;
  generatedAt?: string;
}

export const AvailabilityHeader: React.FC<AvailabilityHeaderProps> = ({
  timeRange,
  onTimeRangeChange,
  onRefresh,
  isLoading,
  generatedAt,
}) => {
  return (
    <div className="module-header-card">
      <div className="header-top-row">
        <div className="header-title-group">
          <h2>Availability & SLA Operations</h2>
          <span className="badge badge-primary">Module 04</span>
        </div>
        <div className="header-controls">
          <div className="control-group">
            <label htmlFor="avail-time-range" className="control-label">Period:</label>
            <select
              id="avail-time-range"
              className="filter-select"
              value={timeRange}
              onChange={(e) => onTimeRangeChange(e.target.value)}
              disabled={isLoading}
            >
              <option value="24h">Last 24 Hours</option>
              <option value="7d">Last 7 Days</option>
              <option value="30d">Last 30 Days (Standard)</option>
              <option value="90d">Last 90 Days (Quarterly)</option>
              <option value="365d">Last 365 Days (Annual)</option>
            </select>
          </div>

          <button
            type="button"
            className="btn btn-secondary refresh-btn"
            onClick={onRefresh}
            disabled={isLoading}
            title="Refresh availability and SLA metrics"
          >
            {isLoading ? 'Refreshing...' : '↻ Refresh'}
          </button>
        </div>
      </div>
      <div className="header-meta-row">
        <span className="meta-text">
          Enterprise Business Services & Service Level Agreements (SLA) Engine
        </span>
        {generatedAt && (
          <span className="meta-timestamp">
            Last evaluated: <strong>{generatedAt}</strong>
          </span>
        )}
      </div>
    </div>
  );
};
