import React from 'react';
import type { TimeRangePreset } from '../types';

interface ProblemsFilterBarProps {
  search: string;
  onSearchChange: (search: string) => void;
  timePreset: TimeRangePreset;
  onTimePresetChange: (preset: TimeRangePreset) => void;
  host: string;
  onHostChange: (host: string) => void;
  group: string;
  onGroupChange: (group: string) => void;
  acknowledged?: boolean;
  onAcknowledgedChange: (val?: boolean) => void;
  suppressed?: boolean;
  onSuppressedChange: (val?: boolean) => void;
  sortBy: string;
  onSortByChange: (sort: string) => void;
  sortOrder: 'ASC' | 'DESC';
  onSortOrderToggle: () => void;
  onResetFilters: () => void;
  hasActiveFilters: boolean;
}

export const ProblemsFilterBar: React.FC<ProblemsFilterBarProps> = ({
  search,
  onSearchChange,
  timePreset,
  onTimePresetChange,
  host,
  onHostChange,
  group,
  onGroupChange,
  acknowledged,
  onAcknowledgedChange,
  suppressed,
  onSuppressedChange,
  sortBy,
  onSortByChange,
  sortOrder,
  onSortOrderToggle,
  onResetFilters,
  hasActiveFilters,
}) => {
  const timePresets: { id: TimeRangePreset; label: string }[] = [
    { id: '15m', label: '15m' },
    { id: '1h', label: '1h' },
    { id: '6h', label: '6h' },
    { id: '24h', label: '24h' },
    { id: '7d', label: '7d' },
    { id: '30d', label: '30d' },
    { id: 'all', label: 'All' },
  ];

  return (
    <div className="filter-bar problems-filter-bar">
      {/* Search Input */}
      <div className="filter-group search-group">
        <div className="search-input-wrapper">
          <svg className="search-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="11" cy="11" r="8" />
            <line x1="21" y1="21" x2="16.65" y2="16.65" />
          </svg>
          <input
            type="text"
            className="search-input"
            placeholder="Search problems, hosts, opdata, tags..."
            value={search}
            onChange={(e) => onSearchChange(e.target.value)}
          />
          {search && (
            <button type="button" className="clear-search-btn" onClick={() => onSearchChange('')}>
              ×
            </button>
          )}
        </div>
      </div>

      {/* Time Range Preset Buttons */}
      <div className="filter-group time-preset-group">
        <label className="filter-label">Time Window:</label>
        <div className="time-preset-buttons">
          {timePresets.map((tp) => (
            <button
              key={tp.id}
              type="button"
              className={`time-preset-btn ${timePreset === tp.id ? 'active' : ''}`}
              onClick={() => onTimePresetChange(tp.id)}
            >
              {tp.label}
            </button>
          ))}
        </div>
      </div>

      {/* Host Filter */}
      <div className="filter-group">
        <input
          type="text"
          className="filter-input-text"
          placeholder="Filter host..."
          value={host}
          onChange={(e) => onHostChange(e.target.value)}
          style={{ width: '130px' }}
        />
      </div>

      {/* Host Group Filter */}
      <div className="filter-group">
        <input
          type="text"
          className="filter-input-text"
          placeholder="Filter group..."
          value={group}
          onChange={(e) => onGroupChange(e.target.value)}
          style={{ width: '130px' }}
        />
      </div>

      {/* Acknowledgment Dropdown */}
      <div className="filter-group">
        <select
          className="filter-select"
          value={acknowledged === undefined ? 'all' : acknowledged ? 'ack' : 'unack'}
          onChange={(e) => {
            const val = e.target.value;
            if (val === 'ack') onAcknowledgedChange(true);
            else if (val === 'unack') onAcknowledgedChange(false);
            else onAcknowledgedChange(undefined);
          }}
        >
          <option value="all">Ack: All</option>
          <option value="unack">Unacknowledged Only</option>
          <option value="ack">Acknowledged Only</option>
        </select>
      </div>

      {/* Suppressed Dropdown */}
      <div className="filter-group">
        <select
          className="filter-select"
          value={suppressed === undefined ? 'all' : suppressed ? 'supp' : 'unsupp'}
          onChange={(e) => {
            const val = e.target.value;
            if (val === 'supp') onSuppressedChange(true);
            else if (val === 'unsupp') onSuppressedChange(false);
            else onSuppressedChange(undefined);
          }}
        >
          <option value="all">Suppressed: All</option>
          <option value="unsupp">Active (Unsuppressed)</option>
          <option value="supp">Suppressed Only</option>
        </select>
      </div>

      {/* Sort Field & Order */}
      <div className="filter-group sort-group">
        <select
          className="filter-select"
          value={sortBy}
          onChange={(e) => onSortByChange(e.target.value)}
        >
          <option value="clock">Sort: Time</option>
          <option value="severity">Sort: Severity</option>
          <option value="name">Sort: Problem Name</option>
          <option value="eventid">Sort: Event ID</option>
        </select>

        <button
          type="button"
          className="sort-order-btn"
          onClick={onSortOrderToggle}
          title={`Order: ${sortOrder === 'DESC' ? 'Descending (Newest first)' : 'Ascending (Oldest first)'}`}
        >
          {sortOrder === 'DESC' ? '↓' : '↑'}
        </button>
      </div>

      {/* Reset Filter Button */}
      {hasActiveFilters && (
        <button
          type="button"
          className="reset-filters-btn"
          onClick={onResetFilters}
          title="Reset all filters"
        >
          Reset Filters
        </button>
      )}
    </div>
  );
};
