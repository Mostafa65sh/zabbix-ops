import React from 'react';
import type { TopProblemHost } from '../types';

interface TopProblemHostsProps {
  hosts: TopProblemHost[];
}

export const TopProblemHosts: React.FC<TopProblemHostsProps> = ({ hosts }) => {
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
      default:
        return 'sev-badge info';
    }
  };

  const formatDuration = (seconds: number) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    if (hours > 0) return `${hours}h ${minutes}m`;
    return `${minutes}m`;
  };

  return (
    <div className="operational-panel">
      <div className="panel-header">
        <div className="panel-title-area">
          <span className="panel-title">TOP PROBLEM HOSTS</span>
          <span className="panel-count-badge">Ranked by Severity</span>
        </div>
      </div>

      <div className="table-responsive">
        <table className="ops-table">
          <thead>
            <tr>
              <th>Host</th>
              <th>Highest Severity</th>
              <th>Active Problems</th>
              <th>Oldest Problem Age</th>
              <th>Host State</th>
            </tr>
          </thead>
          <tbody>
            {hosts.length === 0 ? (
              <tr>
                <td colSpan={5} className="table-empty-row">
                  <span>No problem hosts recorded</span>
                </td>
              </tr>
            ) : (
              hosts.map((h) => (
                <tr key={h.host_id} className="ops-table-row">
                  <td className="host-cell">
                    <strong>{h.host_name}</strong>
                  </td>
                  <td>
                    <span className={getSeverityBadgeClass(h.highest_severity)}>
                      {h.highest_severity_name}
                    </span>
                  </td>
                  <td>
                    <span className="count-chip">{h.problem_count}</span>
                  </td>
                  <td>
                    <span className="duration-pill">
                      {formatDuration(h.oldest_problem_duration_seconds)}
                    </span>
                  </td>
                  <td>
                    <span className={`status-pill ${h.availability_status.toLowerCase()}`}>
                      {h.availability_status}
                    </span>
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
