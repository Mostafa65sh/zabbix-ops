import React from 'react';
import type { AvailabilityOverview } from '../types';

interface AvailabilitySummaryCardsProps {
  overview: AvailabilityOverview | null;
  isLoading: boolean;
}

function formatDuration(seconds: number): string {
  if (seconds <= 0) return '0s';
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  if (hours >= 24) {
    const days = Math.floor(hours / 24);
    const remHours = hours % 24;
    return `${days}d ${remHours}h`;
  }
  if (hours > 0) return `${hours}h ${minutes}m`;
  if (minutes > 0) return `${minutes}m`;
  return `${seconds}s`;
}

export const AvailabilitySummaryCards: React.FC<AvailabilitySummaryCardsProps> = ({
  overview,
  isLoading,
}) => {
  if (isLoading && !overview) {
    return (
      <div className="summary-cards-grid">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="kpi-card loading-card">
            <div className="skeleton-line shimmer"></div>
            <div className="skeleton-line shimmer short"></div>
          </div>
        ))}
      </div>
    );
  }

  if (!overview) return null;

  const getStatusBadgeClass = (status: string) => {
    switch (status) {
      case 'OK':
        return 'badge-ok';
      case 'DEGRADED':
        return 'badge-warning';
      case 'CRITICAL':
        return 'badge-disaster';
      default:
        return 'badge-nodata';
    }
  };

  return (
    <div className="summary-cards-grid">
      {/* 1. System Availability Status */}
      <div className="kpi-card">
        <div className="kpi-header">
          <span className="kpi-title">System Status</span>
          <span className={`badge ${getStatusBadgeClass(overview.overall_status)}`}>
            {overview.overall_status}
          </span>
        </div>
        <div className="kpi-value-row">
          <span className="kpi-main-value">
            {overview.services_ok} / {overview.total_services}
          </span>
          <span className="kpi-sub-text">Services Operational</span>
        </div>
        <div className="kpi-footer">
          {overview.services_problem > 0 ? (
            <span className="text-warning">
              ⚠ {overview.services_problem} service(s) reporting problems
            </span>
          ) : (
            <span className="text-ok">✓ All monitored services healthy</span>
          )}
        </div>
      </div>

      {/* 2. SLA Compliance Rate */}
      <div className="kpi-card">
        <div className="kpi-header">
          <span className="kpi-title">SLA Compliance Rate</span>
          <span className="badge badge-info">
            {overview.total_slas} Active SLAs
          </span>
        </div>
        <div className="kpi-value-row">
          <span className="kpi-main-value">
            {overview.sla_compliance_rate !== null ? `${overview.sla_compliance_rate.toFixed(1)}%` : 'NO_DATA'}
          </span>
          <span className="kpi-sub-text">Compliance Target Met</span>
        </div>
        <div className="kpi-footer">
          <span className={overview.slas_breached > 0 ? 'text-disaster' : 'text-ok'}>
            {overview.slas_compliant} compliant, {overview.slas_breached} breached
          </span>
        </div>
      </div>

      {/* 3. Average Measured SLI */}
      <div className="kpi-card">
        <div className="kpi-header">
          <span className="kpi-title">Average Measured SLI</span>
          <span className="badge badge-secondary">
            {overview.measured_period}
          </span>
        </div>
        <div className="kpi-value-row">
          <span className={`kpi-main-value ${overview.average_sli === null ? 'text-muted' : ''}`}>
            {overview.average_sli_formatted}
          </span>
          <span className="kpi-sub-text">Operational Service Level</span>
        </div>
        <div className="kpi-footer">
          <span className="text-muted">
            Calculated via native Zabbix 7.0.5 SLA engine
          </span>
        </div>
      </div>

      {/* 4. Total Outage & Maintenance */}
      <div className="kpi-card">
        <div className="kpi-header">
          <span className="kpi-title">Downtime & Maintenance</span>
          <span className="badge badge-maintenance">
            Period Total
          </span>
        </div>
        <div className="kpi-value-row">
          <span className="kpi-main-value">
            {formatDuration(overview.total_downtime_seconds)}
          </span>
          <span className="kpi-sub-text">Unplanned Outage</span>
        </div>
        <div className="kpi-footer">
          <span className="text-info">
            🛡 {formatDuration(overview.total_excluded_downtime_seconds)} planned maintenance excluded
          </span>
        </div>
      </div>
    </div>
  );
};
