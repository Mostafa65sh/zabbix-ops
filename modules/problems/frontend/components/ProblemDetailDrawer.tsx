import React, { useEffect, useState } from 'react';
import type { ProblemDetailResponse } from '../types';
import { fetchProblemDetail } from '../api';

interface ProblemDetailDrawerProps {
  eventId: string | null;
  onClose: () => void;
  onNavigateHost?: (hostId: string) => void;
  onInspectRootCause?: (causeEventId: string) => void;
}

export const ProblemDetailDrawer: React.FC<ProblemDetailDrawerProps> = ({
  eventId,
  onClose,
  onNavigateHost,
  onInspectRootCause,
}) => {
  const [detail, setDetail] = useState<ProblemDetailResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!eventId) {
      setDetail(null);
      return;
    }

    let isMounted = true;
    setIsLoading(true);
    setError(null);

    fetchProblemDetail(eventId)
      .then((data) => {
        if (isMounted) {
          setDetail(data);
          setIsLoading(false);
        }
      })
      .catch((err) => {
        if (isMounted) {
          setError(err.message || 'Failed to load problem detail');
          setIsLoading(false);
        }
      });

    return () => {
      isMounted = false;
    };
  }, [eventId]);

  if (!eventId) return null;

  const primaryHost = detail?.hosts && detail.hosts.length > 0 ? detail.hosts[0] : null;

  return (
    <div className="drawer-overlay" onClick={onClose}>
      <div className="drawer-container problem-detail-drawer" onClick={(e) => e.stopPropagation()}>
        {/* Drawer Header */}
        <div className="drawer-header">
          <div className="drawer-header-left">
            <span className="drawer-badge">EVENT #{eventId}</span>
            <h3 className="drawer-title">{detail?.name || 'Problem Detail'}</h3>
          </div>
          <button type="button" className="drawer-close-btn" onClick={onClose} title="Close Drawer">
            ✕
          </button>
        </div>

        {/* Drawer Body */}
        <div className="drawer-body">
          {isLoading && (
            <div className="drawer-loading">
              <div className="loading-spinner"></div>
              <span>Fetching incident context and alert history...</span>
            </div>
          )}

          {error && (
            <div className="drawer-error">
              <span className="error-icon">⚠️</span>
              <p>{error}</p>
            </div>
          )}

          {detail && !isLoading && (
            <div className="drawer-sections">
              {/* Incident Key Metrics Grid */}
              <div className="detail-meta-grid">
                <div className="meta-card">
                  <span className="meta-label">Severity</span>
                  <span className={`meta-value sev-${detail.severity}`}>{detail.severity_name}</span>
                </div>
                <div className="meta-card">
                  <span className="meta-label">Active Duration</span>
                  <span className="meta-value">{detail.duration_human}</span>
                </div>
                <div className="meta-card">
                  <span className="meta-label">Start Time (UTC)</span>
                  <span className="meta-value text-small">{detail.start_time}</span>
                </div>
                <div className="meta-card">
                  <span className="meta-label">Relationship</span>
                  <span className="meta-value">
                    {detail.is_cause ? 'ROOT CAUSE' : `SYMPTOM (#${detail.cause_eventid})`}
                  </span>
                </div>
              </div>

              {/* Host Context */}
              <div className="drawer-section">
                <h4 className="section-title">Host Context</h4>
                {primaryHost ? (
                  <div className="host-detail-card">
                    <div className="host-detail-info">
                      <div className="host-title-line">
                        <strong className="host-visible-name">{primaryHost.name}</strong>
                        <span className="host-tech-name">({primaryHost.host})</span>
                      </div>
                      <span className="host-id-tag">Host ID: {primaryHost.hostid}</span>
                    </div>

                    {onNavigateHost && primaryHost.hostid && (
                      <button
                        type="button"
                        className="navigate-host-btn"
                        onClick={() => onNavigateHost(primaryHost.hostid)}
                      >
                        Open Host 360 →
                      </button>
                    )}
                  </div>
                ) : (
                  <div className="text-muted">NO_DATA</div>
                )}
              </div>

              {/* Operational Data */}
              <div className="drawer-section">
                <h4 className="section-title">Operational Data (OpData)</h4>
                <div className="opdata-box">
                  <code>{detail.opdata}</code>
                </div>
              </div>

              {/* Cause / Symptom Correlation */}
              {detail.is_symptom && detail.cause_eventid && (
                <div className="drawer-section">
                  <h4 className="section-title">Root Cause Correlation</h4>
                  <div className="correlation-box">
                    <span>This event is correlated as a symptom of root cause event:</span>
                    <strong> #{detail.cause_eventid}</strong>
                    {onInspectRootCause && (
                      <button
                        type="button"
                        className="inspect-cause-action-btn"
                        onClick={() => onInspectRootCause(detail.cause_eventid!)}
                      >
                        Inspect Cause Event
                      </button>
                    )}
                  </div>
                </div>
              )}

              {/* Suppression / Maintenance Info */}
              <div className="drawer-section">
                <h4 className="section-title">Suppression & Maintenance</h4>
                {detail.suppressed ? (
                  <div className="suppression-info-box">
                    <span className="supp-active-badge">Incident is Suppressed</span>
                    {detail.suppression_data && detail.suppression_data.length > 0 ? (
                      <ul className="supp-data-list">
                        {detail.suppression_data.map((sd, idx) => (
                          <li key={idx}>
                            Maintenance ID: <strong>{sd.maintenanceid || 'N/A'}</strong> — Suppress Until: <strong>{sd.suppress_until || 'Indefinite'}</strong>
                          </li>
                        ))}
                      </ul>
                    ) : (
                      <p>Suppressed by active maintenance period.</p>
                    )}
                  </div>
                ) : (
                  <span className="text-muted">Incident is active (not suppressed).</span>
                )}
              </div>

              {/* Acknowledgment Trail */}
              <div className="drawer-section">
                <h4 className="section-title">Acknowledgment History ({detail.acknowledges.length})</h4>
                {detail.acknowledges.length > 0 ? (
                  <div className="ack-timeline">
                    {detail.acknowledges.map((ack) => (
                      <div key={ack.acknowledgeid} className="ack-timeline-item">
                        <div className="ack-item-header">
                          <span className="ack-author">User ID: {ack.userid}</span>
                          <span className="ack-time">{ack.time}</span>
                        </div>
                        <div className="ack-message">{ack.message || '(No comment provided)'}</div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <span className="text-muted">No acknowledgments recorded for this incident.</span>
                )}
              </div>

              {/* Notification Alerts Chronology */}
              <div className="drawer-section">
                <h4 className="section-title">Alert & Notification Log ({detail.alerts?.length || 0})</h4>
                {detail.alerts && detail.alerts.length > 0 ? (
                  <div className="alerts-table-wrapper">
                    <table className="alerts-subtable">
                      <thead>
                        <tr>
                          <th>Time</th>
                          <th>Recipient</th>
                          <th>Status</th>
                          <th>Error</th>
                        </tr>
                      </thead>
                      <tbody>
                        {detail.alerts.map((al) => (
                          <tr key={al.alertid}>
                            <td>{al.time}</td>
                            <td><code>{al.sendto}</code></td>
                            <td>
                              <span className={`alert-status-pill ${al.status === '1' ? 'sent' : 'failed'}`}>
                                {al.status === '1' ? 'SENT' : 'NOT SENT'}
                              </span>
                            </td>
                            <td>{al.error ? al.error : '—'}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <span className="text-muted">No automated alert actions triggered for this event.</span>
                )}
              </div>

              {/* Tags */}
              <div className="drawer-section">
                <h4 className="section-title">Tags</h4>
                {detail.tags && detail.tags.length > 0 ? (
                  <div className="detail-tags-list">
                    {detail.tags.map((t, idx) => (
                      <span key={idx} className="drawer-tag-pill">
                        <strong>{t.tag}</strong>: {t.value}
                      </span>
                    ))}
                  </div>
                ) : (
                  <span className="text-muted">No tags defined.</span>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
