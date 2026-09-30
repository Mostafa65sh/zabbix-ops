import React from 'react';
import type { ServerListSummary } from '../types';

interface ServersSummaryCardsProps {
  summary: ServerListSummary;
  onFilterStatus?: (status: string | undefined) => void;
}

export const ServersSummaryCards: React.FC<ServersSummaryCardsProps> = ({
  summary,
  onFilterStatus,
}) => {
  return (
    <div className="servers-summary-grid">
      {/* 1. Total Compute Nodes */}
      <div
        className="kpi-card total-card clickable"
        onClick={() => onFilterStatus?.(undefined)}
        title="View All Servers"
      >
        <div className="kpi-header">
          <span className="kpi-label">TOTAL SERVERS</span>
          <span className="kpi-icon">🖥</span>
        </div>
        <div className="kpi-value">{summary.total_servers}</div>
        <div className="kpi-subtext">
          <span>{summary.available_count} Available</span>
          <span className="dot-divider">•</span>
          <span>{summary.unavailable_count} Unavailable</span>
        </div>
      </div>

      {/* 2. UP Nodes */}
      <div
        className="kpi-card up-card clickable"
        onClick={() => onFilterStatus?.('UP')}
        title="Filter UP Servers"
      >
        <div className="kpi-header">
          <span className="kpi-label">HEALTHY / ONLINE</span>
          <span className="status-pulse-dot green"></span>
        </div>
        <div className="kpi-value green-text">{summary.servers_up}</div>
        <div className="kpi-subtext">Operating normally</div>
      </div>

      {/* 3. DOWN Nodes */}
      <div
        className="kpi-card down-card clickable"
        onClick={() => onFilterStatus?.('DOWN')}
        title="Filter DOWN Servers"
      >
        <div className="kpi-header">
          <span className="kpi-label">OFFLINE / UNREACHABLE</span>
          <span className={`status-pulse-dot ${summary.servers_down > 0 ? 'red' : 'gray'}`}></span>
        </div>
        <div className={`kpi-value ${summary.servers_down > 0 ? 'red-text' : ''}`}>
          {summary.servers_down}
        </div>
        <div className="kpi-subtext">
          {summary.servers_down > 0 ? 'Requires immediate triage' : 'No unreachable servers'}
        </div>
      </div>

      {/* 4. Maintenance */}
      <div
        className="kpi-card maint-card clickable"
        onClick={() => onFilterStatus?.('MAINTENANCE')}
        title="Filter Maintenance Servers"
      >
        <div className="kpi-header">
          <span className="kpi-label">IN MAINTENANCE</span>
          <span className="kpi-icon">🔧</span>
        </div>
        <div className="kpi-value amber-text">{summary.servers_maintenance}</div>
        <div className="kpi-subtext">Planned operational windows</div>
      </div>

      {/* 5. Resource Pressures */}
      <div className="kpi-card metrics-pressure-card">
        <div className="kpi-header">
          <span className="kpi-label">FLEET RESOURCE PRESSURES</span>
          <span className="kpi-icon">⚡</span>
        </div>
        <div className="mini-pressure-bars">
          <div className="pressure-item">
            <div className="pressure-label">
              <span>Avg CPU:</span>
              <strong>{summary.avg_cpu_percent !== null ? `${summary.avg_cpu_percent}%` : 'NO DATA'}</strong>
            </div>
            <div className="pressure-bar-track">
              <div
                className={`pressure-bar-fill ${
                  summary.avg_cpu_percent && summary.avg_cpu_percent > 80 ? 'critical' : 'normal'
                }`}
                style={{ width: `${summary.avg_cpu_percent || 0}%` }}
              ></div>
            </div>
          </div>

          <div className="pressure-item">
            <div className="pressure-label">
              <span>Avg RAM:</span>
              <strong>{summary.avg_memory_percent !== null ? `${summary.avg_memory_percent}%` : 'NO DATA'}</strong>
            </div>
            <div className="pressure-bar-track">
              <div
                className={`pressure-bar-fill ${
                  summary.avg_memory_percent && summary.avg_memory_percent > 80 ? 'critical' : 'normal'
                }`}
                style={{ width: `${summary.avg_memory_percent || 0}%` }}
              ></div>
            </div>
          </div>

          <div className="pressure-item">
            <div className="pressure-label">
              <span>Avg Disk:</span>
              <strong>{summary.avg_storage_percent !== null ? `${summary.avg_storage_percent}%` : 'NO DATA'}</strong>
            </div>
            <div className="pressure-bar-track">
              <div
                className={`pressure-bar-fill ${
                  summary.avg_storage_percent && summary.avg_storage_percent > 80 ? 'critical' : 'normal'
                }`}
                style={{ width: `${summary.avg_storage_percent || 0}%` }}
              ></div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
