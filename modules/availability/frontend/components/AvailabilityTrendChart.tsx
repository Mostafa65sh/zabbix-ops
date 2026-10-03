import React, { useState, useEffect } from 'react';
import type { SLADefinitionItem, AvailabilityTrendResponse } from '../types';
import { fetchAvailabilityTrend } from '../api';

interface AvailabilityTrendChartProps {
  slas: SLADefinitionItem[];
}

export const AvailabilityTrendChart: React.FC<AvailabilityTrendChartProps> = ({ slas }) => {
  const [selectedSlaId, setSelectedSlaId] = useState<string>(slas[0]?.sla_id || 'sla_01');
  const [periods, setPeriods] = useState<number>(12);
  const [trendData, setTrendData] = useState<AvailabilityTrendResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!selectedSlaId && slas.length > 0) {
      setSelectedSlaId(slas[0].sla_id);
    }
  }, [slas, selectedSlaId]);

  useEffect(() => {
    if (!selectedSlaId) return;

    let isMounted = true;
    setIsLoading(true);
    setError(null);

    fetchAvailabilityTrend(selectedSlaId, undefined, periods)
      .then((data) => {
        if (isMounted) setTrendData(data);
      })
      .catch((err) => {
        if (isMounted) setError(err.message || 'Failed to load trend data');
      })
      .finally(() => {
        if (isMounted) setIsLoading(false);
      });

    return () => {
      isMounted = false;
    };
  }, [selectedSlaId, periods]);

  return (
    <div className="trend-container-card">
      <div className="trend-controls-bar">
        <div className="control-item">
          <label htmlFor="trend-sla-select" className="control-label">Select SLA:</label>
          <select
            id="trend-sla-select"
            className="filter-select"
            value={selectedSlaId}
            onChange={(e) => setSelectedSlaId(e.target.value)}
          >
            {slas.map((s) => (
              <option key={s.sla_id} value={s.sla_id}>
                {s.name} (SLO: {s.slo_target.toFixed(2)}%)
              </option>
            ))}
          </select>
        </div>

        <div className="control-item">
          <label htmlFor="trend-periods-select" className="control-label">Periods:</label>
          <select
            id="trend-periods-select"
            className="filter-select"
            value={periods}
            onChange={(e) => setPeriods(Number(e.target.value))}
          >
            <option value={6}>Last 6 Periods</option>
            <option value={12}>Last 12 Periods</option>
            <option value={24}>Last 24 Periods</option>
          </select>
        </div>
      </div>

      {isLoading ? (
        <div className="trend-loading-container">
          <div className="loading-spinner"></div>
          <p>Calculating SLA periods and SLI values...</p>
        </div>
      ) : error ? (
        <div className="alert-banner alert-error">
          <p>{error}</p>
        </div>
      ) : !trendData || trendData.points.length === 0 ? (
        <div className="empty-state">
          <p>No historical reporting periods available for this SLA.</p>
        </div>
      ) : (
        <>
          {/* SVG Visual Representation */}
          <div className="trend-chart-wrapper">
            <div className="trend-chart-header">
              <h4>{trendData.sla_name} — Historical SLI Performance</h4>
              <span className="slo-reference-badge">
                Target SLO: <strong>{trendData.slo_target.toFixed(2)}%</strong>
              </span>
            </div>

            <div className="trend-bars-container">
              {trendData.points.map((pt, idx) => {
                const sliVal = pt.sli_percent !== null ? pt.sli_percent : 0;
                const isNoData = pt.sli_percent === null;
                const isCompliant = pt.is_compliant === true;
                const heightPct = isNoData ? 20 : Math.max(15, Math.min(100, (sliVal - 90) * 10));

                let barColor = 'var(--accent-green)';
                if (isNoData) {
                  barColor = 'var(--text-dim)';
                } else if (!isCompliant) {
                  barColor = 'var(--accent-red)';
                }

                return (
                  <div key={idx} className="trend-bar-column" title={`${pt.period_label}: ${pt.sli_formatted}`}>
                    <div className="trend-bar-value">{pt.sli_formatted}</div>
                    <div className="trend-bar-track">
                      <div
                        className="trend-bar-fill"
                        style={{
                          height: `${heightPct}%`,
                          backgroundColor: barColor,
                        }}
                      ></div>
                    </div>
                    <div className="trend-bar-label">{pt.period_label}</div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Periods Breakdown Table */}
          <div className="table-responsive mt-6">
            <table className="platform-table">
              <thead>
                <tr>
                  <th>Period</th>
                  <th>Measured SLI</th>
                  <th>SLO Target</th>
                  <th>Uptime</th>
                  <th>Downtime</th>
                  <th>Error Budget</th>
                  <th>Compliance</th>
                </tr>
              </thead>
              <tbody>
                {trendData.points.map((pt, idx) => (
                  <tr key={idx} className="table-row-hover">
                    <td className="font-semibold text-main">{pt.period_label}</td>
                    <td>
                      <span
                        className={`font-mono font-bold ${
                          pt.sli_percent === null
                            ? 'text-muted'
                            : pt.is_compliant
                            ? 'text-ok'
                            : 'text-disaster'
                        }`}
                      >
                        {pt.sli_formatted}
                      </span>
                    </td>
                    <td>{trendData.slo_target.toFixed(2)}%</td>
                    <td className="font-mono text-muted">{Math.round(pt.uptime_seconds / 3600)}h</td>
                    <td className="font-mono text-muted">{Math.round(pt.downtime_seconds / 60)}m</td>
                    <td>
                      <span
                        className={`font-mono ${
                          pt.error_budget_seconds === null
                            ? 'text-muted'
                            : (pt.error_budget_seconds || 0) >= 0
                            ? 'text-ok'
                            : 'text-disaster font-bold'
                        }`}
                      >
                        {pt.error_budget_seconds !== null
                          ? `${pt.error_budget_seconds >= 0 ? '+' : ''}${Math.round(
                              pt.error_budget_seconds / 60
                            )}m`
                          : 'NO_DATA'}
                      </span>
                    </td>
                    <td>
                      {pt.is_compliant === true ? (
                        <span className="badge badge-compliant">Met</span>
                      ) : pt.is_compliant === false ? (
                        <span className="badge badge-breached">Breached</span>
                      ) : (
                        <span className="badge badge-nodata">NO_DATA</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
};
