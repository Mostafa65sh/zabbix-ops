import React from 'react';
import type {
  HealthSummary as HealthSummaryType,
  HostStatusSummary,
  ProblemSeveritySummary,
  AvailabilitySummary,
  TrendIndicator,
} from '../types';

interface HealthSummaryProps {
  health: HealthSummaryType;
  hosts: HostStatusSummary;
  problems: ProblemSeveritySummary;
  availability: AvailabilitySummary;
  trend: TrendIndicator;
  onFilterSeverity?: (sev: number) => void;
  onFilterStatus?: (status: string) => void;
}

export const HealthSummary: React.FC<HealthSummaryProps> = ({
  health,
  hosts,
  problems,
  availability,
  trend,
  onFilterSeverity,
  onFilterStatus,
}) => {
  const getHealthBadgeClass = (status: string) => {
    switch (status) {
      case 'HEALTHY':
        return 'badge-healthy';
      case 'DEGRADED':
        return 'badge-degraded';
      case 'CRITICAL':
        return 'badge-critical';
      default:
        return 'badge-unknown';
    }
  };

  const getTrendIcon = (dir: string) => {
    switch (dir) {
      case 'improving':
        return '↗ Improving';
      case 'degrading':
        return '↘ Degrading';
      case 'stable':
        return '→ Stable';
      default:
        return '? Unknown';
    }
  };

  return (
    <section className="kpi-summary-grid">
      {/* 1. Infrastructure Health KPI Card */}
      <div className={`kpi-card health-kpi-card ${health.status.toLowerCase()}`}>
        <div className="kpi-header">
          <span className="kpi-title">INFRASTRUCTURE HEALTH</span>
          <span className={`kpi-badge ${getHealthBadgeClass(health.status)}`}>
            {health.status}
          </span>
        </div>

        <div className="kpi-main-stat">
          <span className="health-status-text">{health.status}</span>
          <span className="health-reason-tag">{health.reason.replace(/_/g, ' ')}</span>
        </div>

        <div className="health-evidence-box">
          <span className="evidence-header">EVIDENCE-BASED CAUSE:</span>
          <ul className="evidence-list">
            {health.evidence.map((ev, idx) => (
              <li key={idx}>{ev}</li>
            ))}
          </ul>
        </div>

        <div className="kpi-footer-note">
          <span className="trend-tag" title={trend.lineage}>
            Trend: <strong>{getTrendIcon(trend.direction)}</strong>
          </span>
        </div>
      </div>

      {/* 2. Monitored Hosts KPI Card */}
      <div className="kpi-card hosts-kpi-card">
        <div className="kpi-header">
          <span className="kpi-title">MONITORED HOSTS</span>
          <span className="kpi-total-pill">{hosts.total} Total</span>
        </div>

        <div className="kpi-main-stat">
          <span className="hosts-total-count">{hosts.total}</span>
          <span className="stat-unit">Hosts Monitored</span>
        </div>

        <div className="hosts-breakdown-row">
          <button
            type="button"
            className="host-stat-chip up"
            onClick={() => onFilterStatus && onFilterStatus('UP')}
            title="Filter Available Hosts"
          >
            <span className="chip-indicator"></span>
            <span className="chip-label">Available</span>
            <strong className="chip-value">{hosts.available}</strong>
          </button>

          <button
            type="button"
            className="host-stat-chip down"
            onClick={() => onFilterStatus && onFilterStatus('DOWN')}
            title="Filter Unavailable Hosts"
          >
            <span className="chip-indicator"></span>
            <span className="chip-label">Unavailable</span>
            <strong className="chip-value">{hosts.unavailable}</strong>
          </button>

          <button
            type="button"
            className="host-stat-chip maint"
            onClick={() => onFilterStatus && onFilterStatus('MAINTENANCE')}
            title="Filter In-Maintenance Hosts"
          >
            <span className="chip-indicator"></span>
            <span className="chip-label">Maintenance</span>
            <strong className="chip-value">{hosts.maintenance}</strong>
          </button>

          {hosts.unknown > 0 && (
            <div className="host-stat-chip unknown">
              <span className="chip-indicator"></span>
              <span className="chip-label">Unknown</span>
              <strong className="chip-value">{hosts.unknown}</strong>
            </div>
          )}
        </div>

        <div className="kpi-footer-note">
          <span>Click any state above to filter active inventory</span>
        </div>
      </div>

      {/* 3. Problem Center KPI Card */}
      <div className="kpi-card problems-kpi-card">
        <div className="kpi-header">
          <span className="kpi-title">ACTIVE PROBLEMS</span>
          <span className={`kpi-total-pill ${problems.total > 0 ? 'has-problems' : 'clean'}`}>
            {problems.total} Active
          </span>
        </div>

        <div className="kpi-main-stat">
          <span className="problems-total-count">{problems.total}</span>
          <span className="stat-unit">Incidents Unresolved</span>
        </div>

        <div className="severity-chips-grid">
          <button
            type="button"
            className={`sev-chip disaster ${problems.disaster > 0 ? 'active-pulse' : ''}`}
            onClick={() => onFilterSeverity && onFilterSeverity(5)}
            title="Filter Disaster (Severity 5)"
          >
            <span className="sev-label">Disaster</span>
            <span className="sev-count">{problems.disaster}</span>
          </button>

          <button
            type="button"
            className={`sev-chip high ${problems.high > 0 ? 'active' : ''}`}
            onClick={() => onFilterSeverity && onFilterSeverity(4)}
            title="Filter High (Severity 4)"
          >
            <span className="sev-label">High</span>
            <span className="sev-count">{problems.high}</span>
          </button>

          <button
            type="button"
            className="sev-chip average"
            onClick={() => onFilterSeverity && onFilterSeverity(3)}
            title="Filter Average (Severity 3)"
          >
            <span className="sev-label">Average</span>
            <span className="sev-count">{problems.average}</span>
          </button>

          <button
            type="button"
            className="sev-chip warning"
            onClick={() => onFilterSeverity && onFilterSeverity(2)}
            title="Filter Warning (Severity 2)"
          >
            <span className="sev-label">Warning</span>
            <span className="sev-count">{problems.warning}</span>
          </button>

          <button
            type="button"
            className="sev-chip info"
            onClick={() => onFilterSeverity && onFilterSeverity(1)}
            title="Filter Information (Severity 1)"
          >
            <span className="sev-label">Info</span>
            <span className="sev-count">{problems.information}</span>
          </button>
        </div>

        <div className="kpi-footer-note">
          <span>Click severity to drill down into problem list</span>
        </div>
      </div>

      {/* 4. Measured Availability KPI Card */}
      <div className="kpi-card availability-kpi-card">
        <div className="kpi-header">
          <span className="kpi-title">MEASURED AVAILABILITY</span>
          <span className="kpi-total-pill lineage-pill" title={availability.lineage?.method}>
            Lineage Verified
          </span>
        </div>

        <div className="kpi-main-stat">
          <span className="availability-percent">
            {availability.percent !== null ? `${availability.percent.toFixed(1)}%` : 'N/A'}
          </span>
          <span className="stat-unit">Operational SLA</span>
        </div>

        <div className="availability-metrics">
          <div className="avail-row">
            <span>Planned Maintenance:</span>
            <strong>
              {availability.planned_downtime_seconds > 0
                ? `${Math.round(availability.planned_downtime_seconds / 60)} min`
                : '0s'}
            </strong>
          </div>
          <div className="avail-row">
            <span>Unplanned Downtime:</span>
            <strong className={availability.unplanned_downtime_seconds > 0 ? 'text-danger' : ''}>
              {availability.unplanned_downtime_seconds > 0
                ? `${Math.round(availability.unplanned_downtime_seconds / 60)} min`
                : '0s'}
            </strong>
          </div>
        </div>

        <div className="kpi-footer-note lineage-note" title={availability.lineage?.calculation}>
          <span>Calc: {availability.lineage?.calculation || 'Host operational ratio'}</span>
        </div>
      </div>
    </section>
  );
};
