import React, { useState } from 'react';
import type { ActiveProblem } from '../types';

interface ActiveProblemsTableProps {
  problems: ActiveProblem[];
  isLoading: boolean;
  onSelectProblem?: (prob: ActiveProblem) => void;
}

export const ActiveProblemsTable: React.FC<ActiveProblemsTableProps> = ({
  problems,
  isLoading,
  onSelectProblem,
}) => {
  const [sortField, setSortField] = useState<'severity' | 'started_clock' | 'duration_seconds'>('severity');
  const [sortAsc, setSortAsc] = useState<boolean>(false);
  const [tableSearch, setTableSearch] = useState<string>('');

  const getSeverityBadgeClass = (severity: number) => {
    switch (severity) {
      case 5:
        return 'sev-badge disaster';
      case 4:
        return 'sev-badge high';
      case 3:
        return 'sev-badge average';
      case 2:
        return 'sev-badge warning';
      case 1:
        return 'sev-badge info';
      default:
        return 'sev-badge not-classified';
    }
  };

  const handleSort = (field: 'severity' | 'started_clock' | 'duration_seconds') => {
    if (sortField === field) {
      setSortAsc(!sortAsc);
    } else {
      setSortField(field);
      setSortAsc(false); // default descending
    }
  };

  const filteredProblems = problems.filter((p) => {
    if (!tableSearch) return true;
    const q = tableSearch.toLowerCase();
    return (
      p.name.toLowerCase().includes(q) ||
      (p.host_name && p.host_name.toLowerCase().includes(q)) ||
      p.severity_name.toLowerCase().includes(q)
    );
  });

  const sortedProblems = [...filteredProblems].sort((a, b) => {
    let comparison = 0;
    if (sortField === 'severity') {
      comparison = a.severity - b.severity;
    } else if (sortField === 'started_clock') {
      comparison = a.started_clock - b.started_clock;
    } else if (sortField === 'duration_seconds') {
      comparison = a.duration_seconds - b.duration_seconds;
    }
    return sortAsc ? comparison : -comparison;
  });

  return (
    <div className="operational-panel">
      <div className="panel-header">
        <div className="panel-title-area">
          <span className="panel-title">ACTIVE INCIDENTS & PROBLEMS</span>
          <span className="panel-count-badge">{problems.length} Unresolved</span>
        </div>

        <div className="panel-actions">
          <input
            type="text"
            className="table-search-input"
            placeholder="Search problems table..."
            value={tableSearch}
            onChange={(e) => setTableSearch(e.target.value)}
          />
        </div>
      </div>

      <div className="table-responsive">
        <table className="ops-table">
          <thead>
            <tr>
              <th
                className="sortable"
                onClick={() => handleSort('severity')}
                title="Sort by Severity"
              >
                Severity {sortField === 'severity' ? (sortAsc ? '▲' : '▼') : ''}
              </th>
              <th>Host</th>
              <th>Problem Description</th>
              <th
                className="sortable"
                onClick={() => handleSort('duration_seconds')}
                title="Sort by Duration"
              >
                Duration {sortField === 'duration_seconds' ? (sortAsc ? '▲' : '▼') : ''}
              </th>
              <th>Ack</th>
              <th
                className="sortable"
                onClick={() => handleSort('started_clock')}
                title="Sort by Started Time"
              >
                Started (UTC) {sortField === 'started_clock' ? (sortAsc ? '▲' : '▼') : ''}
              </th>
            </tr>
          </thead>
          <tbody>
            {isLoading ? (
              <tr>
                <td colSpan={6} className="table-empty-row">
                  <div className="table-loading-spinner"></div>
                  <span>Loading active incidents...</span>
                </td>
              </tr>
            ) : sortedProblems.length === 0 ? (
              <tr>
                <td colSpan={6} className="table-empty-row">
                  <span className="empty-check">✓</span>
                  <strong>No Active Problems</strong>
                  <p>All monitored infrastructure systems report normal operating telemetry.</p>
                </td>
              </tr>
            ) : (
              sortedProblems.map((prob) => (
                <tr
                  key={prob.eventid}
                  className="ops-table-row clickable"
                  onClick={() => onSelectProblem && onSelectProblem(prob)}
                >
                  <td>
                    <span className={getSeverityBadgeClass(prob.severity)}>
                      <span className="sev-dot"></span>
                      <span className="sev-name">{prob.severity_name}</span>
                    </span>
                  </td>
                  <td className="host-cell">
                    <strong>{prob.host_name || 'N/A'}</strong>
                  </td>
                  <td className="problem-name-cell">
                    <span className="problem-text">{prob.name}</span>
                  </td>
                  <td className="duration-cell">
                    <span className="duration-pill">{prob.duration_human}</span>
                  </td>
                  <td>
                    <span className={`ack-badge ${prob.acknowledged ? 'ack-yes' : 'ack-no'}`}>
                      {prob.acknowledged ? 'ACKNOWLEDGED' : 'UNACKNOWLEDGED'}
                    </span>
                  </td>
                  <td className="started-cell">
                    <span>{prob.started_human}</span>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};
