import React from 'react';
import type { ServerFilters } from '../types';

interface ServersFilterBarProps {
  filters: ServerFilters;
  onFilterChange: (newFilters: ServerFilters) => void;
  autoRefreshInterval: number;
  onAutoRefreshChange: (interval: number) => void;
}

export const ServersFilterBar: React.FC<ServersFilterBarProps> = ({
  filters,
  onFilterChange,
  autoRefreshInterval,
  onAutoRefreshChange,
}) => {
  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    onFilterChange({
      ...filters,
      search: e.target.value || undefined,
      page: 1, // reset page on search
    });
  };

  const handleStatusChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    onFilterChange({
      ...filters,
      status: e.target.value || undefined,
      page: 1,
    });
  };

  const handleAvailabilityChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    onFilterChange({
      ...filters,
      availability: e.target.value || undefined,
      page: 1,
    });
  };

  const handleOsChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    onFilterChange({
      ...filters,
      os_type: e.target.value || undefined,
      page: 1,
    });
  };

  const handleDcChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    onFilterChange({
      ...filters,
      datacenter: e.target.value || undefined,
      page: 1,
    });
  };

  const handleProblemsToggle = () => {
    onFilterChange({
      ...filters,
      has_problems: filters.has_problems ? undefined : true,
      page: 1,
    });
  };

  const handleReset = () => {
    onFilterChange({
      page: 1,
      page_size: filters.page_size || 25,
      sort_by: 'name',
      sort_order: 'asc',
    });
  };

  const hasActiveFilters = Boolean(
    filters.search ||
    filters.status ||
    filters.availability ||
    filters.os_type ||
    filters.datacenter ||
    filters.has_problems ||
    filters.group
  );

  return (
    <div className="servers-filter-bar">
      {/* 1. Keyword Search */}
      <div className="filter-item search-input-box">
        <span className="search-icon">🔍</span>
        <input
          type="text"
          className="search-input"
          placeholder="Filter by name, IP, OS, tag, rack..."
          value={filters.search || ''}
          onChange={handleSearchChange}
        />
        {filters.search && (
          <button
            type="button"
            className="clear-search-btn"
            onClick={() => onFilterChange({ ...filters, search: undefined, page: 1 })}
          >
            ×
          </button>
        )}
      </div>

      {/* 2. Status Dropdown */}
      <div className="filter-item">
        <label className="filter-label">Status:</label>
        <select
          className="filter-select"
          value={filters.status || ''}
          onChange={handleStatusChange}
        >
          <option value="">All Statuses</option>
          <option value="UP">Online (UP)</option>
          <option value="DOWN">Offline (DOWN)</option>
          <option value="MAINTENANCE">In Maintenance</option>
        </select>
      </div>

      {/* 3. Availability Dropdown */}
      <div className="filter-item">
        <label className="filter-label">Availability:</label>
        <select
          className="filter-select"
          value={filters.availability || ''}
          onChange={handleAvailabilityChange}
        >
          <option value="">All Availability</option>
          <option value="AVAILABLE">Available</option>
          <option value="UNAVAILABLE">Unavailable</option>
          <option value="UNKNOWN">Unknown</option>
        </select>
      </div>

      {/* 4. OS Family Dropdown */}
      <div className="filter-item">
        <label className="filter-label">OS Family:</label>
        <select
          className="filter-select"
          value={filters.os_type || ''}
          onChange={handleOsChange}
        >
          <option value="">All Operating Systems</option>
          <option value="linux">Linux</option>
          <option value="windows">Windows</option>
          <option value="network">Network OS</option>
          <option value="other">Other</option>
        </select>
      </div>

      {/* 5. Datacenter Dropdown */}
      <div className="filter-item">
        <label className="filter-label">Datacenter:</label>
        <select
          className="filter-select"
          value={filters.datacenter || ''}
          onChange={handleDcChange}
        >
          <option value="">All Datacenters</option>
          <option value="DC-EAST-01">DC-EAST-01</option>
          <option value="DC-EAST-02">DC-EAST-02</option>
          <option value="DC-WEST-01">DC-WEST-01</option>
          <option value="DC-WEST-02">DC-WEST-02</option>
          <option value="DC-EDGE-01">DC-EDGE-01</option>
          <option value="DC-DEV-LAB">DC-DEV-LAB</option>
        </select>
      </div>

      {/* 6. Active Problems Only Toggle */}
      <button
        type="button"
        className={`filter-toggle-btn ${filters.has_problems ? 'active' : ''}`}
        onClick={handleProblemsToggle}
        title="Show only nodes with active problems"
      >
        <span className="alert-dot"></span>
        <span>With Alerts Only</span>
      </button>

      {/* 7. Reset Button */}
      {hasActiveFilters && (
        <button
          type="button"
          className="filter-reset-btn"
          onClick={handleReset}
          title="Clear all active filters"
        >
          Reset Filters
        </button>
      )}

      {/* 8. Auto-Refresh Interval Selector */}
      <div className="filter-item auto-refresh-box">
        <label className="filter-label">Auto-Refresh:</label>
        <select
          className="filter-select auto-refresh-select"
          value={autoRefreshInterval}
          onChange={(e) => onAutoRefreshChange(Number(e.target.value))}
        >
          <option value={0}>Off</option>
          <option value={15}>15s</option>
          <option value={30}>30s</option>
          <option value={60}>60s</option>
          <option value={300}>5m</option>
        </select>
      </div>
    </div>
  );
};
