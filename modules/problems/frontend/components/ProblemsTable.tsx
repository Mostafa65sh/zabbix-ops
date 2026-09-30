import React from 'react';
import type { ProblemItem } from '../types';

interface ProblemsTableProps {
  problems: ProblemItem[];
  isLoading: boolean;
  selectedEventId: string | null;
  onSelectProblem: (eventId: string) => void;
  onNavigateHost?: (hostId: string) => void;
  onInspectRootCause: (causeEventId: string) => void;
}

const SEVERITY_BADGE_STYLE: Record<number, { bg: string; color: string; border: string }> = {
  5: { bg: 'rgba(220, 38, 38, 0.2)', color: '#ef4444', border: '#dc2626' },
  4: { bg: 'rgba(234, 88, 12, 0.2)', color: '#f97316', border: '#ea580c' },
  3: { bg: 'rgba(245, 158, 11, 0.2)', color: '#f59e0b', border: '#d97706' },
  2: { bg: 'rgba(234, 179, 8, 0.2)', color: '#eab308', border: '#ca8a04' },
  1: { bg: 'rgba(14, 165, 233, 0.2)', color: '#38bdf8', border: '#0284c7' },
  0: { bg: 'rgba(100, 116, 139, 0.2)', color: '#94a3b8', border: '#64748b' },
};

export const ProblemsTable: React.FC<ProblemsTableProps> = ({
  problems,
  isLoading,
  selectedEventId,
  onSelectProblem,
  onNavigateHost,
  onInspectRootCause,
}) => {
  if (isLoading && problems.length === 0) {
    return (
      <div className="table-loading-container">
        <div className="loading-spinner"></div>
        <span>Retrieving real-time problem feed from Zabbix 7.0.5...</span>
      </div>
    );
  }

  if (problems.length === 0) {
    return (
      <div className="table-empty-container">
        <div className="empty-state-icon">✓</div>
        <h3>No Active Problems Found</h3>
        <p>There are no incidents matching the current filter criteria.</p>
      </div>
    );
  }

  return (
    <div className="table-wrapper problems-table-wrapper">
      <table className="data-table problems-table">
        <thead>
          <tr>
            <th style={{ width: '120px' }}>Severity</th>
            <th style={{ width: '110px' }}>Time / Age</th>
            <th style={{ width: '180px' }}>Host</th>
            <th>Problem & Operational Data</th>
            <th style={{ width: '130px' }}>Status</th>
            <th style={{ width: '120px' }}>Relationship</th>
            <th style={{ width: '140px' }}>Tags</th>
            <th style={{ width: '80px', textAlign: 'center' }}>Action</th>
          </tr>
        </thead>
        <tbody>
          {problems.map((prob) => {
            const isSelected = selectedEventId === prob.eventid;
            const primaryHost = prob.hosts && prob.hosts.length > 0 ? prob.hosts[0] : null;
            const sevStyle = SEVERITY_BADGE_STYLE[prob.severity] || SEVERITY_BADGE_STYLE[0];

            return (
              <tr
                key={prob.eventid}
                className={`table-row ${isSelected ? 'row-selected' : ''}`}
                onClick={() => onSelectProblem(prob.eventid)}
              >
                {/* Severity Badge */}
                <td>
                  <span
                    className="severity-cell-badge"
                    style={{
                      backgroundColor: sevStyle.bg,
                      color: sevStyle.color,
                      borderColor: sevStyle.border,
                    }}
                  >
                    <span
                      className="sev-indicator-dot"
                      style={{ backgroundColor: sevStyle.color }}
                    ></span>
                    {prob.severity_name}
                  </span>
                </td>

                {/* Time / Age */}
                <td>
                  <div className="cell-time-wrapper">
                    <span className="cell-duration" title={`Active duration: ${prob.duration_human}`}>
                      {prob.duration_human}
                    </span>
                    <span className="cell-start-time" title={prob.start_time}>
                      {prob.start_time.split(' ')[1] || prob.start_time}
                    </span>
                  </div>
                </td>

                {/* Host Info */}
                <td>
                  {primaryHost ? (
                    <div className="cell-host-wrapper">
                      <span
                        className="cell-host-name"
                        title={`Visible Name: ${primaryHost.name}\nTechnical: ${primaryHost.host}`}
                        onClick={(e) => {
                          if (onNavigateHost && primaryHost.hostid) {
                            e.stopPropagation();
                            onNavigateHost(primaryHost.hostid);
                          }
                        }}
                      >
                        {primaryHost.name}
                      </span>
                      <span className="cell-host-sub">{primaryHost.host}</span>
                    </div>
                  ) : (
                    <span className="text-muted">NO_DATA</span>
                  )}
                </td>

                {/* Problem Name & OpData */}
                <td>
                  <div className="cell-problem-wrapper">
                    <div className="cell-problem-title" title={prob.name}>
                      {prob.name}
                    </div>
                    <div className="cell-problem-opdata">
                      <span className="opdata-tag">OPDATA:</span>
                      <span className={prob.opdata === 'NO_DATA' ? 'text-muted' : 'opdata-val'}>
                        {prob.opdata}
                      </span>
                    </div>
                  </div>
                </td>

                {/* Status: Acknowledged / Suppressed */}
                <td>
                  <div className="cell-status-indicators">
                    {prob.acknowledged ? (
                      <span className="status-badge ack-badge" title="Acknowledged by operator">
                        ✓ Ack ({prob.acknowledges.length})
                      </span>
                    ) : (
                      <span className="status-badge unack-badge" title="Unacknowledged incident">
                        ! Unack
                      </span>
                    )}

                    {prob.suppressed && (
                      <span className="status-badge supp-badge" title="Suppressed by maintenance">
                        ⏸ Suppressed
                      </span>
                    )}
                  </div>
                </td>

                {/* Cause / Symptom */}
                <td>
                  {prob.is_cause ? (
                    <span className="relationship-badge cause-badge" title="Root cause event">
                      ROOT CAUSE
                    </span>
                  ) : prob.cause_eventid ? (
                    <div className="symptom-wrapper">
                      <span className="relationship-badge symptom-badge" title="Symptom event">
                        SYMPTOM
                      </span>
                      <button
                        type="button"
                        className="inspect-cause-link"
                        onClick={(e) => {
                          e.stopPropagation();
                          onInspectRootCause(prob.cause_eventid!);
                        }}
                        title={`Inspect Root Cause event #${prob.cause_eventid}`}
                      >
                        Inspect Cause →
                      </button>
                    </div>
                  ) : (
                    <span className="text-muted">NO_DATA</span>
                  )}
                </td>

                {/* Tags */}
                <td>
                  <div className="cell-tags-wrapper">
                    {prob.tags && prob.tags.length > 0 ? (
                      prob.tags.slice(0, 2).map((t, i) => (
                        <span key={i} className="problem-tag-pill" title={`${t.tag}: ${t.value}`}>
                          {t.tag}={t.value}
                        </span>
                      ))
                    ) : (
                      <span className="text-muted">—</span>
                    )}
                    {prob.tags && prob.tags.length > 2 && (
                      <span className="problem-tag-more">+{prob.tags.length - 2}</span>
                    )}
                  </div>
                </td>

                {/* Actions */}
                <td style={{ textAlign: 'center' }}>
                  <button
                    type="button"
                    className="view-detail-btn"
                    onClick={(e) => {
                      e.stopPropagation();
                      onSelectProblem(prob.eventid);
                    }}
                    title="View Problem 360 Detail"
                  >
                    View
                  </button>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
};
