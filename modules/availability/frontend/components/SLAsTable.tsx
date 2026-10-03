import React from 'react';
import type { SLADefinitionItem } from '../types';
import { PaginationControls } from '../../../../frontend/src/components/PaginationControls';

interface SLAsTableProps {
  slas: SLADefinitionItem[];
  totalCount: number;
  totalPages: number;
  page: number;
  pageSize: number;
  onPageChange: (newPage: number) => void;
  onPageSizeChange: (newSize: number) => void;
  isLoading: boolean;
}

export const SLAsTable: React.FC<SLAsTableProps> = ({
  slas,
  totalCount,
  totalPages,
  page,
  pageSize,
  onPageChange,
  onPageSizeChange,
  isLoading,
}) => {
  return (
    <div className="table-container-card">
      <div className="table-header-title">
        <h3>Configured Service Level Agreements (SLAs)</h3>
        <span className="text-muted">Defined in Zabbix 7.0.5 SLA Management</span>
      </div>

      <div className="table-responsive">
        <table className="platform-table">
          <thead>
            <tr>
              <th>SLA Name</th>
              <th>Period</th>
              <th>SLO Target</th>
              <th>Current SLI</th>
              <th>Compliance</th>
              <th>Error Budget</th>
              <th>Services</th>
              <th>Timezone</th>
              <th>Maintenance / Exclusions</th>
            </tr>
          </thead>
          <tbody>
            {isLoading ? (
              <tr>
                <td colSpan={9} className="text-center py-8">
                  <div className="loading-spinner"></div>
                  <span className="ml-2">Loading SLAs...</span>
                </td>
              </tr>
            ) : slas.length === 0 ? (
              <tr>
                <td colSpan={9} className="text-center py-8 empty-state">
                  <div className="empty-icon">📋</div>
                  <h3>No SLAs configured</h3>
                  <p className="text-muted">Define SLAs in Zabbix to monitor Service Level Objectives.</p>
                </td>
              </tr>
            ) : (
              slas.map((sla) => (
                <tr key={sla.sla_id} className="table-row-hover">
                  <td>
                    <span className="font-semibold text-main">{sla.name}</span>
                    <div className="text-dim text-xs">ID: {sla.sla_id}</div>
                  </td>
                  <td>
                    <span className="badge badge-secondary capitalize">{sla.period}</span>
                  </td>
                  <td>
                    <strong className="font-mono">{sla.slo_target.toFixed(2)}%</strong>
                  </td>
                  <td>
                    <span
                      className={`font-mono font-bold ${
                        sla.current_sli === null
                          ? 'text-muted'
                          : sla.compliance_status === 'COMPLIANT'
                          ? 'text-ok'
                          : 'text-disaster'
                      }`}
                    >
                      {sla.sli_formatted}
                    </span>
                  </td>
                  <td>
                    {sla.compliance_status === 'COMPLIANT' ? (
                      <span className="badge badge-compliant">Compliant</span>
                    ) : sla.compliance_status === 'BREACHED' ? (
                      <span className="badge badge-breached">Breached</span>
                    ) : (
                      <span className="badge badge-nodata">NO_DATA</span>
                    )}
                  </td>
                  <td>
                    <span
                      className={`font-mono ${
                        sla.error_budget_seconds === null
                          ? 'text-muted'
                          : (sla.error_budget_seconds || 0) >= 0
                          ? 'text-ok'
                          : 'text-disaster font-bold'
                      }`}
                    >
                      {sla.error_budget_human}
                    </span>
                  </td>
                  <td>
                    <span className="badge badge-info">{sla.service_count} service(s)</span>
                  </td>
                  <td>
                    <span className="text-muted font-mono">{sla.timezone}</span>
                  </td>
                  <td>
                    {sla.excluded_downtimes.length > 0 ? (
                      <span className="text-info text-xs">
                        🛡 {sla.excluded_downtimes.length} scheduled exclusion(s)
                      </span>
                    ) : (
                      <span className="text-dim text-xs">None</span>
                    )}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      <PaginationControls
        page={page}
        pageSize={pageSize}
        totalCount={totalCount}
        totalPages={totalPages}
        onPageChange={onPageChange}
        onPageSizeChange={onPageSizeChange}
        itemLabel="SLAs"
      />
    </div>
  );
};
