import React from 'react';
import type { OverviewFilters } from '../types';

interface OverviewFilterBarProps {
  filters: OverviewFilters;
  onFilterChange: (newFilters: OverviewFilters) => void;
  autoRefreshInterval: number; // in seconds (0 = off)
  onAutoRefreshChange: (interval: number) => void;
}

const TIME_RANGES = [
  { label: '5m', value: '5m' },
  { label: '15m', value: '15m' },
  { label: '1h', value: '1h' },
  { label: '6h', value: '6h' },
  { label: '24h', value: '24h' },
  { label: '7d', value: '7d' },
  { label: '30d', value: '30d' },
];

const HOST_GROUPS = [
  { label: 'All Groups', value: '' },
  { label: 'Linux Servers', value: 'Linux Servers' },
  { label: 'Database Cluster', value: 'Database Cluster' },
  { label: 'Network Devices', value: 'Network Devices' },
  { label: 'Storage Systems', value: 'Storage Systems' },
];

const SEVERITIES = [
  { label: 'All Severities', value: '' },
  { label: '5 - Disaster', value: '5' },
  { label: '4 - High', value: '4' },
  { label: '3 - Average', value: '3' },
  { label: '2 - Warning', value: '2' },
  { label: '1 - Information', value: '1' },
];

const STATUSES = [
  { label: 'All Statuses', value: '' },
  { label: 'UP (Available)', value: 'UP' },
  { label: 'DOWN (Unavailable)', value: 'DOWN' },
  { label: 'MAINTENANCE', value: 'MAINTENANCE' },
];

export const OverviewFilterBar: React.FC<OverviewFilterBarProps> = ({
  filters,
  onFilterChange,
  autoRefreshInterval,
  onAutoRefreshChange,
}) => {
  return (
    <div className="overview-filter-bar">
      {/* Time Range Selector */}
      <div className="filter-group">
        <span className="filter-label">TIME WINDOW</span>
        <div className="time-btn-group">
          {TIME_RANGES.map((r) => (
            <button
              key={r.value}
              type="button"
              className={`time-btn ${filters.time_range === r.value ? 'active' : ''}`}
              onClick={() => onFilterChange({ ...filters, time_range: r.value })}
            >
              {r.label}
            </button>
          ))}
        </div>
      </div>

      {/* Host Group Filter */}
      <div className="filter-group">
        <span className="filter-label">GROUP</span>
        <select
          className="filter-select"
          value={filters.group || ''}
          onChange={(e) => onFilterChange({ ...filters, group: e.target.value || undefined })}
        >
          {HOST_GROUPS.map((g) => (
            <option key={g.value} value={g.value}>
              {g.label}
            </option>
          ))}
        </select>
      </div>

      {/* Severity Filter */}
      <div className="filter-group">
        <span className="filter-label">SEVERITY</span>
        <select
          className="filter-select"
          value={filters.severity !== undefined ? String(filters.severity) : ''}
          onChange={(e) =>
            onFilterChange({
              ...filters,
              severity: e.target.value ? Number(e.target.value) : undefined,
            })
          }
        >
          {SEVERITIES.map((s) => (
            <option key={s.value} value={s.value}>
              {s.label}
            </option>
          ))}
        </select>
      </div>

      {/* Host Status Filter */}
      <div className="filter-group">
        <span className="filter-label">STATUS</span>
        <select
          className="filter-select"
          value={filters.status || ''}
          onChange={(e) => onFilterChange({ ...filters, status: e.target.value || undefined })}
        >
          {STATUSES.map((st) => (
            <option key={st.value} value={st.value}>
              {st.label}
            </option>
          ))}
        </select>
      </div>

      {/* Host Search Filter */}
      <div className="filter-group search-filter-group">
        <span className="filter-label">SEARCH HOST</span>
        <div className="search-input-wrapper">
          <input
            type="text"
            className="filter-search-input"
            placeholder="Filter by host..."
            value={filters.host || ''}
            onChange={(e) => onFilterChange({ ...filters, host: e.target.value || undefined })}
          />
          {filters.host && (
            <button
              type="button"
              className="clear-search-btn"
              onClick={() => onFilterChange({ ...filters, host: undefined })}
            >
              ×
            </button>
          )}
        </div>
      </div>

      {/* Auto-Refresh Control */}
      <div className="filter-group right-align">
        <span className="filter-label">AUTO REFRESH</span>
        <select
          className="filter-select auto-refresh-select"
          value={autoRefreshInterval}
          onChange={(e) => onAutoRefreshChange(Number(e.target.value))}
        >
          <option value={0}>Off</option>
          <option value={30}>Every 30s</option>
          <option value={60}>Every 60s</option>
          <option value={300}>Every 5m</option>
        </select>
      </div>
    </div>
  );
};
