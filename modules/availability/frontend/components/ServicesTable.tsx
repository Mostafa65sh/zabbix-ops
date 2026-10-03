import React from 'react';
import type { ServiceAvailabilityItem, ServiceFilters } from '../types';
import { PaginationControls } from '../../../../frontend/src/components/PaginationControls';

interface ServicesTableProps {
  services: ServiceAvailabilityItem[];
  totalCount: number;
  totalPages: number;
  filters: ServiceFilters;
  onFilterChange: (newFilters: Partial<ServiceFilters>) => void;
  onSelectService: (service: ServiceAvailabilityItem) => void;
  isLoading: boolean;
}

export const ServicesTable: React.FC<ServicesTableProps> = ({
  services,
  totalCount,
  totalPages,
  filters,
  onFilterChange,
  onSelectService,
  isLoading,
}) => {
  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'OK':
        return <span className="badge badge-ok">OK</span>;
      case 'WARNING':
        return <span className="badge badge-warning">Warning</span>;
      case 'AVERAGE':
        return <span className="badge badge-average">Average</span>;
      case 'HIGH':
        return <span className="badge badge-high">High</span>;
      case 'DISASTER':
        return <span className="badge badge-disaster">Disaster</span>;
      default:
        return <span className="badge badge-nodata">{status}</span>;
    }
  };

  const getSlaStatusBadge = (slaStatus: string) => {
    switch (slaStatus) {
      case 'COMPLIANT':
        return <span className="badge badge-compliant">Compliant</span>;
      case 'BREACHED':
        return <span className="badge badge-breached">Breached</span>;
      case 'NOT_CONFIGURED':
        return <span className="badge badge-not-configured">No SLA</span>;
      case 'NO_DATA':
      default:
        return <span className="badge badge-nodata">NO_DATA</span>;
    }
  };

  return (
    <div className="table-container-card">
      {/* Filter and Search Bar */}
      <div className="table-filter-bar">
        <div className="search-box">
          <input
            type="text"
            className="filter-input search-input"
            placeholder="Search service by name..."
            value={filters.search || ''}
            onChange={(e) => onFilterChange({ search: e.target.value, page: 1 })}
            maxLength={100}
          />
        </div>

        <div className="filter-group">
          <label htmlFor="avail-srv-status" className="filter-label">Status:</label>
          <select
            id="avail-srv-status"
            className="filter-select"
            value={filters.status || ''}
            onChange={(e) => onFilterChange({ status: e.target.value || undefined, page: 1 })}
          >
            <option value="">All Statuses</option>
            <option value="OK">OK</option>
            <option value="WARNING">Warning</option>
            <option value="AVERAGE">Average</option>
            <option value="HIGH">High</option>
            <option value="DISASTER">Disaster</option>
          </select>
        </div>

        <div className="filter-group">
          <label htmlFor="avail-srv-sort" className="filter-label">Sort:</label>
          <select
            id="avail-srv-sort"
            className="filter-select"
            value={`${filters.sort_by || 'status'}_${filters.sort_order || 'desc'}`}
            onChange={(e) => {
              const [sb, so] = e.target.value.split('_');
              onFilterChange({ sort_by: sb, sort_order: so, page: 1 });
            }}
          >
            <option value="status_desc">Status (Critical first)</option>
            <option value="status_asc">Status (Healthy first)</option>
            <option value="sli_asc">SLI (Lowest first)</option>
            <option value="sli_desc">SLI (Highest first)</option>
            <option value="name_asc">Name (A-Z)</option>
            <option value="name_desc">Name (Z-A)</option>
            <option value="downtime_desc">Downtime (Highest first)</option>
          </select>
        </div>
      </div>

      {/* Services Table */}
      <div className="table-responsive">
        <table className="platform-table">
          <thead>
            <tr>
              <th>Service Name</th>
              <th>Status</th>
              <th>Linked SLA</th>
              <th>SLO Target</th>
              <th>Current SLI</th>
              <th>SLA Compliance</th>
              <th>Error Budget</th>
              <th>Active Problems</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {isLoading ? (
              <tr>
                <td colSpan={9} className="text-center py-8">
                  <div className="loading-spinner"></div>
                  <span className="ml-2">Loading business services...</span>
                </td>
              </tr>
            ) : services.length === 0 ? (
              <tr>
                <td colSpan={9} className="text-center py-8 empty-state">
                  <div className="empty-icon">📁</div>
                  <h3>No services found matching filters</h3>
                  <p className="text-muted">Adjust search keywords or status filter to see services.</p>
                </td>
              </tr>
            ) : (
              services.map((service) => (
                <tr key={service.service_id} className="table-row-hover">
                  <td className="font-semibold text-main">
                    {service.name}
                    {service.tags.length > 0 && (
                      <div className="service-tags-row">
                        {service.tags.slice(0, 3).map((t, idx) => (
                          <span key={idx} className="tag-pill">
                            {t.tag}: {t.value}
                          </span>
                        ))}
                      </div>
                    )}
                  </td>
                  <td>{getStatusBadge(service.status)}</td>
                  <td>
                    {service.sla_name ? (
                      <span className="text-main">{service.sla_name}</span>
                    ) : (
                      <span className="text-muted italic">Unassigned</span>
                    )}
                  </td>
                  <td>
                    {service.slo_target !== null ? `${service.slo_target.toFixed(2)}%` : '—'}
                  </td>
                  <td>
                    <span
                      className={`font-mono font-bold ${
                        service.sli_current === null
                          ? 'text-muted'
                          : service.sla_status === 'COMPLIANT'
                          ? 'text-ok'
                          : 'text-disaster'
                      }`}
                    >
                      {service.sli_formatted}
                    </span>
                  </td>
                  <td>{getSlaStatusBadge(service.sla_status)}</td>
                  <td>
                    <span
                      className={`font-mono ${
                        service.error_budget_seconds === null
                          ? 'text-muted'
                          : (service.error_budget_seconds || 0) >= 0
                          ? 'text-ok'
                          : 'text-disaster font-bold'
                      }`}
                    >
                      {service.error_budget_formatted}
                    </span>
                  </td>
                  <td>
                    {service.problem_count > 0 ? (
                      <span className="badge badge-problem-count">
                        ⚠ {service.problem_count} problem(s)
                      </span>
                    ) : (
                      <span className="text-muted">0</span>
                    )}
                  </td>
                  <td>
                    <button
                      type="button"
                      className="btn btn-sm btn-outline"
                      onClick={() => onSelectService(service)}
                      title="Inspect service telemetry and root cause events"
                    >
                      Inspect
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Shared Pagination Controls */}
      <PaginationControls
        page={filters.page || 1}
        pageSize={filters.page_size || 25}
        totalCount={totalCount}
        totalPages={totalPages}
        onPageChange={(p) => onFilterChange({ page: p })}
        onPageSizeChange={(s) => onFilterChange({ page_size: s, page: 1 })}
        itemLabel="services"
      />
    </div>
  );
};
