import React from 'react';
import type { InfrastructureGroup } from '../types';

interface InfrastructureStatusProps {
  infrastructure: InfrastructureGroup[];
}

export const InfrastructureStatus: React.FC<InfrastructureStatusProps> = ({ infrastructure }) => {
  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'OPERATIONAL':
        return <span className="infra-pill operational">OPERATIONAL</span>;
      case 'DEGRADED':
        return <span className="infra-pill degraded">DEGRADED</span>;
      case 'CRITICAL':
        return <span className="infra-pill critical">CRITICAL</span>;
      case 'MAINTENANCE':
        return <span className="infra-pill maint">MAINTENANCE</span>;
      case 'NO_DATA':
      default:
        return <span className="infra-pill no-data">NO SOURCE CONFIGURED</span>;
    }
  };

  return (
    <div className="operational-panel">
      <div className="panel-header">
        <div className="panel-title-area">
          <span className="panel-title">INFRASTRUCTURE DOMAIN HEALTH</span>
          <span className="panel-count-badge">Evidence-Backed</span>
        </div>
      </div>

      <div className="infra-grid">
        {infrastructure.map((group) => (
          <div
            key={group.category}
            className={`infra-card ${group.status.toLowerCase().replace(/_/g, '-')}`}
          >
            <div className="infra-card-header">
              <span className="infra-category-name">{group.category}</span>
              {getStatusBadge(group.status)}
            </div>

            {group.has_telemetry ? (
              <div className="infra-card-body">
                <div className="infra-stat-row">
                  <span>Monitored Hosts:</span>
                  <strong>{group.hosts_count}</strong>
                </div>
                <div className="infra-stat-row">
                  <span>Healthy:</span>
                  <strong className="text-success">{group.healthy_count}</strong>
                </div>
                <div className="infra-stat-row">
                  <span>Active Problems:</span>
                  <strong className={group.problem_count > 0 ? 'text-danger' : 'text-muted'}>
                    {group.problem_count}
                  </strong>
                </div>
              </div>
            ) : (
              <div className="infra-no-data-box">
                <span className="no-data-icon">ℹ</span>
                <p className="no-data-text">No telemetry source configured for this domain.</p>
                <span className="no-data-sub">Status not fabricated as healthy</span>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};
