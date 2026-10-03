import React from 'react';
import type { ServiceAvailabilityItem } from '../types';

interface ServiceDetailDrawerProps {
  service: ServiceAvailabilityItem | null;
  onClose: () => void;
}

export const ServiceDetailDrawer: React.FC<ServiceDetailDrawerProps> = ({ service, onClose }) => {
  if (!service) return null;

  return (
    <div className="drawer-overlay" onClick={onClose}>
      <div className="drawer-panel" onClick={(e) => e.stopPropagation()}>
        <div className="drawer-header">
          <div className="drawer-title-group">
            <h3>{service.name}</h3>
            <span className="text-dim text-xs">ID: {service.service_id}</span>
          </div>
          <button type="button" className="drawer-close-btn" onClick={onClose}>
            ✕
          </button>
        </div>

        <div className="drawer-body">
          {/* Status & SLI Highlights */}
          <div className="drawer-section">
            <h4 className="drawer-section-title">Service Level Overview</h4>
            <div className="drawer-grid-2">
              <div className="detail-item">
                <span className="detail-label">Status</span>
                <span className="detail-value font-bold">{service.status}</span>
              </div>
              <div className="detail-item">
                <span className="detail-label">SLA Compliance</span>
                <span className="detail-value font-bold">{service.sla_status}</span>
              </div>
              <div className="detail-item">
                <span className="detail-label">Current SLI</span>
                <span className="detail-value font-mono font-bold text-ok">
                  {service.sli_formatted}
                </span>
              </div>
              <div className="detail-item">
                <span className="detail-label">Target SLO</span>
                <span className="detail-value font-mono">
                  {service.slo_target !== null ? `${service.slo_target.toFixed(2)}%` : 'None'}
                </span>
              </div>
              <div className="detail-item">
                <span className="detail-label">Remaining Error Budget</span>
                <span className="detail-value font-mono font-bold">
                  {service.error_budget_formatted}
                </span>
              </div>
              <div className="detail-item">
                <span className="detail-label">Total Outage Time</span>
                <span className="detail-value font-mono">
                  {Math.round(service.downtime_seconds / 60)} minutes
                </span>
              </div>
            </div>
          </div>

          {/* Linked Root-Cause Problems */}
          <div className="drawer-section">
            <h4 className="drawer-section-title">
              Active Root-Cause Problem Events ({service.problem_count})
            </h4>
            {service.problem_events.length === 0 ? (
              <p className="text-ok text-sm">✓ No active problems affecting this service.</p>
            ) : (
              <div className="problem-events-list">
                {service.problem_events.map((prob) => (
                  <div key={prob.eventid} className="problem-event-card">
                    <div className="problem-event-header">
                      <span className={`badge badge-disaster`}>{prob.severity_name}</span>
                      <span className="text-dim text-xs font-mono">Event #{prob.eventid}</span>
                    </div>
                    <p className="problem-event-title">{prob.name}</p>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Service Tags & Metadata */}
          <div className="drawer-section">
            <h4 className="drawer-section-title">Service Tags & Attributes</h4>
            {service.tags.length === 0 ? (
              <p className="text-muted text-sm">No tags defined for this service.</p>
            ) : (
              <div className="tags-chips-container">
                {service.tags.map((t, idx) => (
                  <div key={idx} className="tag-chip">
                    <span className="tag-chip-key">{t.tag}</span>
                    <span className="tag-chip-val">{t.value}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        <div className="drawer-footer">
          <button type="button" className="btn btn-secondary w-full" onClick={onClose}>
            Close Inspector
          </button>
        </div>
      </div>
    </div>
  );
};
