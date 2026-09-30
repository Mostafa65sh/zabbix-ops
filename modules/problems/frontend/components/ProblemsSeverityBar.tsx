import React from 'react';
import type { ProblemSeveritySummary } from '../types';

interface ProblemsSeverityBarProps {
  summary: ProblemSeveritySummary;
  acknowledgedCount: number;
  unacknowledgedCount: number;
  suppressedCount: number;
  selectedSeverities: number[];
  onToggleSeverity: (severity: number) => void;
  onClearSeverities: () => void;
  acknowledgedFilter?: boolean;
  onToggleAcknowledged: () => void;
  suppressedFilter?: boolean;
  onToggleSuppressed: () => void;
}

export const ProblemsSeverityBar: React.FC<ProblemsSeverityBarProps> = ({
  summary,
  acknowledgedCount,
  unacknowledgedCount,
  suppressedCount,
  selectedSeverities,
  onToggleSeverity,
  onClearSeverities,
  acknowledgedFilter,
  onToggleAcknowledged,
  suppressedFilter,
  onToggleSuppressed,
}) => {
  const severitiesConfig = [
    { level: 5, key: 'disaster' as const, label: 'Disaster', color: '#dc2626', bg: 'rgba(220, 38, 38, 0.15)', border: 'rgba(220, 38, 38, 0.4)' },
    { level: 4, key: 'high' as const, label: 'High', color: '#ea580c', bg: 'rgba(234, 88, 12, 0.15)', border: 'rgba(234, 88, 12, 0.4)' },
    { level: 3, key: 'average' as const, label: 'Average', color: '#f59e0b', bg: 'rgba(245, 158, 11, 0.15)', border: 'rgba(245, 158, 11, 0.4)' },
    { level: 2, key: 'warning' as const, label: 'Warning', color: '#eab308', bg: 'rgba(234, 179, 8, 0.15)', border: 'rgba(234, 179, 8, 0.4)' },
    { level: 1, key: 'information' as const, label: 'Information', color: '#0ea5e9', bg: 'rgba(14, 165, 233, 0.15)', border: 'rgba(14, 165, 233, 0.4)' },
    { level: 0, key: 'unclassified' as const, label: 'Unclassified', color: '#64748b', bg: 'rgba(100, 116, 139, 0.15)', border: 'rgba(100, 116, 139, 0.4)' },
  ];

  return (
    <div className="problems-severity-command-bar">
      <div className="severity-bar-left">
        {severitiesConfig.map((s) => {
          const count = summary[s.key] || 0;
          const isSelected = selectedSeverities.includes(s.level);
          return (
            <button
              key={s.level}
              type="button"
              className={`severity-command-pill ${isSelected ? 'active' : ''} ${count === 0 ? 'empty' : ''}`}
              style={{
                borderColor: isSelected ? s.color : s.border,
                backgroundColor: isSelected ? s.color : s.bg,
                color: isSelected ? '#ffffff' : s.color,
              }}
              onClick={() => onToggleSeverity(s.level)}
              title={`Click to filter by ${s.label} (${count})`}
            >
              <span className="severity-pill-label">{s.label}</span>
              <span className="severity-pill-count">{count}</span>
            </button>
          );
        })}

        {selectedSeverities.length > 0 && (
          <button
            type="button"
            className="clear-severity-btn"
            onClick={onClearSeverities}
            title="Reset severity filters"
          >
            Clear
          </button>
        )}
      </div>

      <div className="severity-bar-right">
        <button
          type="button"
          className={`operational-state-pill ack ${acknowledgedFilter === true ? 'active' : ''}`}
          onClick={onToggleAcknowledged}
          title="Filter Acknowledged vs Unacknowledged"
        >
          <span className="state-pill-icon">✓</span>
          <span className="state-pill-text">Ack: <strong>{acknowledgedCount}</strong></span>
          <span className="state-pill-separator">/</span>
          <span className="state-pill-text unack">Unack: <strong>{unacknowledgedCount}</strong></span>
        </button>

        <button
          type="button"
          className={`operational-state-pill supp ${suppressedFilter === true ? 'active' : ''}`}
          onClick={onToggleSuppressed}
          title="Filter Maintenance/Suppressed incidents"
        >
          <span className="state-pill-icon">⏸</span>
          <span className="state-pill-text">Suppressed: <strong>{suppressedCount}</strong></span>
        </button>
      </div>
    </div>
  );
};
