import React from 'react';
import type { ServerItem, ServerMetricValue, ServerFilters } from '../types';

interface ServersTableProps {
  servers: ServerItem[];
  filters: ServerFilters;
  onFilterChange: (filters: ServerFilters) => void;
  onSelectServer: (server: ServerItem) => void;
}

export const ServersTable: React.FC<ServersTableProps> = ({
  servers,
  filters,
  onFilterChange,
  onSelectServer,
}) => {
  const handleSort = (field: string) => {
    const isCurrent = filters.sort_by === field;
    const nextOrder = isCurrent && filters.sort_order === 'asc' ? 'desc' : 'asc';
    onFilterChange({
      ...filters,
      sort_by: field,
      sort_order: nextOrder,
    });
  };

  const renderSortIndicator = (field: string) => {
    if (filters.sort_by !== field) return <span className="sort-hint">↕</span>;
    return <span className="sort-active">{filters.sort_order === 'asc' ? '▲' : '▼'}</span>;
  };

  const renderMetricCell = (metric: ServerMetricValue, label: string) => {
    if (metric.status === 'NO_DATA' || metric.value === null) {
      return (
        <div className="metric-cell no-data" title={`${label}: Telemetry not collected / agent unreachable`}>
          <span className="no-data-tag">NO DATA</span>
        </div>
      );
    }

    const val = metric.value;
    let barClass = 'green';
    if (val >= 90) barClass = 'red';
    else if (val >= 70) barClass = 'amber';

    return (
      <div className="metric-cell">
        <div className="metric-header-row">
          <span className={`metric-num ${barClass}`}>{metric.formatted}</span>
        </div>
        <div className="metric-bar-track">
          <div className={`metric-bar-fill ${barClass}`} style={{ width: `${Math.min(val, 100)}%` }}></div>
        </div>
      </div>
    );
  };

  const getStatusBadge = (status: string, avail: string) => {
    let statClass = 'status-pill-up';
    let label = 'ONLINE';
    if (status === 'DOWN') {
      statClass = 'status-pill-down';
      label = 'OFFLINE';
    } else if (status === 'MAINTENANCE') {
      statClass = 'status-pill-maint';
      label = 'MAINT';
    }

    return (
      <div className="status-cell-wrapper">
        <span className={`status-pill ${statClass}`}>{label}</span>
        <span
          className={`avail-indicator ${avail.toLowerCase()}`}
          title={`Interface Availability: ${avail}`}
        ></span>
      </div>
    );
  };

  const getOsBadge = (osType: string, osName: string) => {
    let icon = '🐧';
    let badgeClass = 'os-linux';
    if (osType === 'windows') {
      icon = '🪟';
      badgeClass = 'os-windows';
    } else if (osType === 'network') {
      icon = '🌐';
      badgeClass = 'os-network';
    } else if (osType === 'other') {
      icon = '⚙';
      badgeClass = 'os-other';
    }

    return (
      <div className="os-badge-wrapper" title={osName}>
        <span className="os-icon">{icon}</span>
        <span className={`os-tag ${badgeClass}`}>{osType.toUpperCase()}</span>
      </div>
    );
  };

  return (
    <div className="servers-table-wrapper">
      <table className="enterprise-data-table servers-table">
        <thead>
          <tr>
            <th className="sortable-th" onClick={() => handleSort('name')}>
              <span>SERVER NAME & DETAILS</span>
              {renderSortIndicator('name')}
            </th>
            <th className="sortable-th" onClick={() => handleSort('status')}>
              <span>STATUS</span>
              {renderSortIndicator('status')}
            </th>
            <th className="sortable-th" onClick={() => handleSort('ip')}>
              <span>PRIMARY IP & PORT</span>
              {renderSortIndicator('ip')}
            </th>
            <th>
              <span>OS / PLATFORM</span>
            </th>
            <th className="sortable-th metric-th" onClick={() => handleSort('cpu')}>
              <span>CPU UTIL</span>
              {renderSortIndicator('cpu')}
            </th>
            <th className="sortable-th metric-th" onClick={() => handleSort('memory')}>
              <span>RAM UTIL</span>
              {renderSortIndicator('memory')}
            </th>
            <th className="sortable-th metric-th" onClick={() => handleSort('storage')}>
              <span>STORAGE</span>
              {renderSortIndicator('storage')}
            </th>
            <th className="sortable-th" onClick={() => handleSort('problems')}>
              <span>ALERTS</span>
              {renderSortIndicator('problems')}
            </th>
            <th className="action-th">
              <span>ACTION</span>
            </th>
          </tr>
        </thead>
        <tbody>
          {servers.length === 0 ? (
            <tr className="empty-row">
              <td colSpan={9} className="empty-table-cell">
                <div className="empty-state-card">
                  <span className="empty-icon">🔍</span>
                  <h3>No Servers Found</h3>
                  <p>No compute nodes match the active filter criteria.</p>
                </div>
              </td>
            </tr>
          ) : (
            servers.map((server) => (
              <tr
                key={server.id}
                className={`server-row ${server.status === 'DOWN' ? 'row-down' : ''}`}
                onClick={() => onSelectServer(server)}
              >
                {/* 1. Name & Tags */}
                <td className="server-name-cell">
                  <div className="server-title-row">
                    <span className="server-name-strong">{server.name}</span>
                    {server.datacenter && (
                      <span className="dc-tag-badge" title={`Datacenter: ${server.datacenter}`}>
                        {server.datacenter}
                      </span>
                    )}
                    {server.rack && (
                      <span className="rack-tag-badge" title={`Rack: ${server.rack}`}>
                        {server.rack}
                      </span>
                    )}
                  </div>
                  <div className="server-sub-row">
                    <code className="tech-name">{server.technical_name}</code>
                    <span className="groups-text">{server.groups.join(', ') || 'Default'}</span>
                  </div>
                </td>

                {/* 2. Status & Availability */}
                <td>{getStatusBadge(server.status, server.overall_availability)}</td>

                {/* 3. IP Address */}
                <td className="ip-cell">
                  <div className="ip-wrapper">
                    <code className="ip-code">{server.ip || 'No IP'}</code>
                    {server.interfaces.length > 1 && (
                      <span className="if-count-pill" title={`${server.interfaces.length} network interfaces configured`}>
                        +{server.interfaces.length - 1} IF
                      </span>
                    )}
                  </div>
                </td>

                {/* 4. OS */}
                <td>
                  <div className="os-cell">
                    {getOsBadge(server.os_type, server.os)}
                    <span className="os-text-truncate" title={server.os}>
                      {server.os}
                    </span>
                  </div>
                </td>

                {/* 5. CPU */}
                <td className="metric-td">{renderMetricCell(server.hardware.cpu_utilization, 'CPU')}</td>

                {/* 6. RAM */}
                <td className="metric-td">{renderMetricCell(server.hardware.memory_utilization, 'RAM')}</td>

                {/* 7. Storage */}
                <td className="metric-td">{renderMetricCell(server.hardware.storage_utilization, 'Storage')}</td>

                {/* 8. Problems */}
                <td className="alerts-cell">
                  {server.problems.total === 0 ? (
                    <span className="clean-pill">Clean</span>
                  ) : (
                    <div className="active-alerts-badges">
                      {server.problems.disaster > 0 && (
                        <span className="badge-sev-disaster" title="Disaster problems">
                          {server.problems.disaster} DIS
                        </span>
                      )}
                      {server.problems.high > 0 && (
                        <span className="badge-sev-high" title="High severity problems">
                          {server.problems.high} HIGH
                        </span>
                      )}
                      {server.problems.warning > 0 && (
                        <span className="badge-sev-warning" title="Warning problems">
                          {server.problems.warning} WARN
                        </span>
                      )}
                    </div>
                  )}
                </td>

                {/* 9. Action */}
                <td className="action-cell" onClick={(e) => e.stopPropagation()}>
                  <button
                    type="button"
                    className="inspect-btn"
                    onClick={() => onSelectServer(server)}
                    title="Inspect Server 360"
                  >
                    <span>Inspect</span>
                    <span className="arrow-icon">→</span>
                  </button>
                </td>
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
};
