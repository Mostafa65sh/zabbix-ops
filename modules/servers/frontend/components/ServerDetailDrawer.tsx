import React, { useEffect } from 'react';
import type { ServerItem, ServerDetailResponse } from '../types';

interface ServerDetailDrawerProps {
  server: ServerItem | null;
  detail: ServerDetailResponse | null;
  isLoading: boolean;
  onClose: () => void;
}

export const ServerDetailDrawer: React.FC<ServerDetailDrawerProps> = ({
  server,
  detail,
  isLoading,
  onClose,
}) => {
  // Close drawer on Escape key press
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onClose]);

  if (!server) return null;

  const currentServer = detail?.server || server;
  const inv = detail?.inventory || {};
  const activeProblems = detail?.active_problems || [];

  const formatBytes = (bytes?: number | null) => {
    if (bytes === undefined || bytes === null) return 'N/A';
    if (bytes >= 1099511627776) return `${(bytes / 1099511627776).toFixed(2)} TB`;
    if (bytes >= 1073741824) return `${(bytes / 1073741824).toFixed(1)} GB`;
    if (bytes >= 1048576) return `${(bytes / 1048576).toFixed(1)} MB`;
    return `${bytes} B`;
  };

  const getSeverityBadge = (sev: number) => {
    const map: Record<number, { label: string; cls: string }> = {
      5: { label: 'Disaster', cls: 'sev-disaster' },
      4: { label: 'High', cls: 'sev-high' },
      3: { label: 'Average', cls: 'sev-average' },
      2: { label: 'Warning', cls: 'sev-warning' },
      1: { label: 'Information', cls: 'sev-info' },
    };
    const s = map[sev] || { label: 'Not classified', cls: 'sev-none' };
    return <span className={`problem-sev-pill ${s.cls}`}>{s.label}</span>;
  };

  return (
    <div className="drawer-overlay" onClick={onClose}>
      <div className="server-detail-drawer" onClick={(e) => e.stopPropagation()}>
        {/* Drawer Header */}
        <div className="drawer-header">
          <div className="drawer-title-area">
            <div className="drawer-pre-title">
              <span className="dot-live"></span>
              <span>HOST 360 INSPECTION</span>
              <span className="separator">•</span>
              <span className="drawer-host-id">ID: {currentServer.id}</span>
            </div>
            <h2>{currentServer.name}</h2>
            <div className="drawer-sub-meta">
              <code>{currentServer.technical_name}</code>
              <span className="separator">•</span>
              <span>{currentServer.ip || 'No IP'}</span>
              {currentServer.datacenter && (
                <>
                  <span className="separator">•</span>
                  <span className="dc-tag-badge">{currentServer.datacenter}</span>
                </>
              )}
            </div>
          </div>
          <button type="button" className="drawer-close-btn" onClick={onClose} title="Close (ESC)">
            ✕
          </button>
        </div>

        {/* Drawer Body */}
        <div className="drawer-body">
          {isLoading && !detail && (
            <div className="drawer-loading-bar">
              <div className="loading-spinner"></div>
              <span>Fetching host metrics and telemetry from Zabbix...</span>
            </div>
          )}

          {/* 1. Status & Health Overview Banner */}
          <div className="drawer-section status-banner-section">
            <div className="banner-item">
              <span className="banner-label">STATUS</span>
              <span className={`status-pill ${currentServer.status === 'UP' ? 'status-pill-up' : currentServer.status === 'DOWN' ? 'status-pill-down' : 'status-pill-maint'}`}>
                {currentServer.status}
              </span>
            </div>
            <div className="banner-item">
              <span className="banner-label">AVAILABILITY</span>
              <span className={`avail-tag ${currentServer.overall_availability.toLowerCase()}`}>
                {currentServer.overall_availability}
              </span>
            </div>
            <div className="banner-item">
              <span className="banner-label">ACTIVE ALERTS</span>
              <span className={`alerts-tag ${currentServer.problems.total > 0 ? 'has-alerts' : 'clean'}`}>
                {currentServer.problems.total} Problems
              </span>
            </div>
            <div className="banner-item">
              <span className="banner-label">HOST GROUPS</span>
              <span className="groups-tag">{currentServer.groups.join(', ') || 'None'}</span>
            </div>
          </div>

          {/* 2. Hardware Resource Gauges */}
          <div className="drawer-section">
            <h3 className="section-title">Hardware Telemetry & Pressure</h3>
            <div className="hardware-metrics-grid">
              {/* CPU Card */}
              <div className="hw-card">
                <div className="hw-header">
                  <span className="hw-label">CPU UTILIZATION</span>
                  <span className={`hw-status-badge ${currentServer.hardware.cpu_utilization.status.toLowerCase()}`}>
                    {currentServer.hardware.cpu_utilization.status}
                  </span>
                </div>
                <div className="hw-value-row">
                  <span className="hw-big-num">{currentServer.hardware.cpu_utilization.formatted}</span>
                  {currentServer.hardware.cpu_cores && (
                    <span className="hw-sub">{currentServer.hardware.cpu_cores} Cores</span>
                  )}
                </div>
                {currentServer.hardware.cpu_utilization.value !== null && (
                  <div className="metric-bar-track">
                    <div
                      className={`metric-bar-fill ${currentServer.hardware.cpu_utilization.value >= 90 ? 'red' : currentServer.hardware.cpu_utilization.value >= 70 ? 'amber' : 'green'}`}
                      style={{ width: `${Math.min(currentServer.hardware.cpu_utilization.value, 100)}%` }}
                    ></div>
                  </div>
                )}
                {currentServer.hardware.cpu_load !== null && currentServer.hardware.cpu_load !== undefined && (
                  <div className="hw-meta-row">
                    <span>Load Avg (1m):</span>
                    <strong>{currentServer.hardware.cpu_load}</strong>
                  </div>
                )}
              </div>

              {/* Memory Card */}
              <div className="hw-card">
                <div className="hw-header">
                  <span className="hw-label">RAM / MEMORY</span>
                  <span className={`hw-status-badge ${currentServer.hardware.memory_utilization.status.toLowerCase()}`}>
                    {currentServer.hardware.memory_utilization.status}
                  </span>
                </div>
                <div className="hw-value-row">
                  <span className="hw-big-num">{currentServer.hardware.memory_utilization.formatted}</span>
                  {currentServer.hardware.memory_total_bytes && (
                    <span className="hw-sub">{formatBytes(currentServer.hardware.memory_total_bytes)}</span>
                  )}
                </div>
                {currentServer.hardware.memory_utilization.value !== null && (
                  <div className="metric-bar-track">
                    <div
                      className={`metric-bar-fill ${currentServer.hardware.memory_utilization.value >= 90 ? 'red' : currentServer.hardware.memory_utilization.value >= 70 ? 'amber' : 'green'}`}
                      style={{ width: `${Math.min(currentServer.hardware.memory_utilization.value, 100)}%` }}
                    ></div>
                  </div>
                )}
                {currentServer.hardware.memory_used_bytes && (
                  <div className="hw-meta-row">
                    <span>Used:</span>
                    <strong>{formatBytes(currentServer.hardware.memory_used_bytes)}</strong>
                  </div>
                )}
              </div>

              {/* Storage Card */}
              <div className="hw-card">
                <div className="hw-header">
                  <span className="hw-label">STORAGE / DISK</span>
                  <span className={`hw-status-badge ${currentServer.hardware.storage_utilization.status.toLowerCase()}`}>
                    {currentServer.hardware.storage_utilization.status}
                  </span>
                </div>
                <div className="hw-value-row">
                  <span className="hw-big-num">{currentServer.hardware.storage_utilization.formatted}</span>
                  {currentServer.hardware.storage_total_bytes && (
                    <span className="hw-sub">{formatBytes(currentServer.hardware.storage_total_bytes)}</span>
                  )}
                </div>
                {currentServer.hardware.storage_utilization.value !== null && (
                  <div className="metric-bar-track">
                    <div
                      className={`metric-bar-fill ${currentServer.hardware.storage_utilization.value >= 90 ? 'red' : currentServer.hardware.storage_utilization.value >= 70 ? 'amber' : 'green'}`}
                      style={{ width: `${Math.min(currentServer.hardware.storage_utilization.value, 100)}%` }}
                    ></div>
                  </div>
                )}
                {currentServer.hardware.storage_used_bytes && (
                  <div className="hw-meta-row">
                    <span>Used:</span>
                    <strong>{formatBytes(currentServer.hardware.storage_used_bytes)}</strong>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* 3. Network Interfaces */}
          <div className="drawer-section">
            <h3 className="section-title">Network Interfaces ({currentServer.interfaces.length})</h3>
            <table className="mini-data-table">
              <thead>
                <tr>
                  <th>TYPE</th>
                  <th>IP ADDRESS</th>
                  <th>PORT</th>
                  <th>ROLE</th>
                  <th>AVAILABILITY</th>
                </tr>
              </thead>
              <tbody>
                {currentServer.interfaces.map((iface) => (
                  <tr key={iface.interfaceid}>
                    <td>
                      <span className="iface-type-pill">{iface.type}</span>
                    </td>
                    <td>
                      <code>{iface.ip}</code>
                      {iface.dns && <span className="dns-subtext">({iface.dns})</span>}
                    </td>
                    <td>{iface.port}</td>
                    <td>
                      {iface.is_main ? (
                        <span className="main-iface-badge">Primary</span>
                      ) : (
                        <span className="sec-iface-badge">Secondary</span>
                      )}
                    </td>
                    <td>
                      <span className={`avail-tag ${iface.availability.toLowerCase()}`}>
                        {iface.availability}
                      </span>
                      {iface.error && (
                        <div className="iface-error-text" title={iface.error}>
                          {iface.error}
                        </div>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* 4. OS & Hardware Inventory */}
          <div className="drawer-section">
            <h3 className="section-title">Host Inventory & Specifications</h3>
            <div className="inventory-details-list">
              <div className="inv-row">
                <span className="inv-key">Operating System:</span>
                <span className="inv-val">{currentServer.os}</span>
              </div>
              <div className="inv-row">
                <span className="inv-key">Hardware Platform:</span>
                <span className="inv-val">{currentServer.hardware_summary}</span>
              </div>
              <div className="inv-row">
                <span className="inv-key">Datacenter / Location:</span>
                <span className="inv-val">{inv.datacenter || currentServer.datacenter || 'Unassigned'}</span>
              </div>
              <div className="inv-row">
                <span className="inv-key">Rack / Cabinet:</span>
                <span className="inv-val">{inv.rack || currentServer.rack || 'Unassigned'}</span>
              </div>
              <div className="inv-row">
                <span className="inv-key">Environment:</span>
                <span className="inv-val">{inv.environment || currentServer.environment || 'Unspecified'}</span>
              </div>
            </div>
          </div>

          {/* 5. Active Problems */}
          <div className="drawer-section">
            <h3 className="section-title">Active Host Incidents & Problems ({activeProblems.length})</h3>
            {activeProblems.length === 0 ? (
              <div className="clean-problems-box">
                <span className="clean-icon">✓</span>
                <span>No active alarms or triggers currently firing for this server.</span>
              </div>
            ) : (
              <div className="problems-drawer-list">
                {activeProblems.map((prob) => (
                  <div key={prob.eventid} className="problem-drawer-item">
                    <div className="prob-header-row">
                      {getSeverityBadge(prob.severity)}
                      <span className="prob-name">{prob.name}</span>
                    </div>
                    <div className="prob-meta-row">
                      <span>Event ID: #{prob.eventid}</span>
                      <span>•</span>
                      <span>Ack: {prob.acknowledged ? 'Yes' : 'No'}</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* 6. Tags */}
          {currentServer.tags.length > 0 && (
            <div className="drawer-section">
              <h3 className="section-title">Host Tags</h3>
              <div className="tags-container">
                {currentServer.tags.map((t, idx) => (
                  <span key={idx} className="tag-chip">
                    <strong>{t.tag}:</strong> {t.value}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* 7. Lineage & Native API Audit */}
          <div className="drawer-section lineage-audit-section">
            <div className="lineage-header">
              <span className="lineage-icon">🔒</span>
              <strong>Zabbix Native API Data Lineage:</strong>
            </div>
            <p className="lineage-desc">
              Data retrieved via non-invasive JSON-RPC 2.0 calls to <code>host.get</code>, <code>selectInterfaces</code>, <code>selectInventory</code>, and <code>item.get</code> without touching Zabbix core files or modifying database schemas.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
