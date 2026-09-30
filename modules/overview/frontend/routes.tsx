import React, { useState, useEffect, useCallback } from 'react';
import type { OverviewData, OverviewFilters } from './types';
import { fetchOverviewData } from './api';
import { OverviewHeader } from './components/OverviewHeader';
import { OverviewFilterBar } from './components/OverviewFilterBar';
import { HealthSummary } from './components/HealthSummary';
import { ActiveProblemsTable } from './components/ActiveProblemsTable';
import { InfrastructureStatus } from './components/InfrastructureStatus';
import { TopProblemHosts } from './components/TopProblemHosts';
import { RecentEventsTimeline } from './components/RecentEventsTimeline';

export const OverviewPage: React.FC = () => {
  const [data, setData] = useState<OverviewData | null>(null);
  const [filters, setFilters] = useState<OverviewFilters>({ time_range: '24h' });
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isRefreshing, setIsRefreshing] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [autoRefreshInterval, setAutoRefreshInterval] = useState<number>(30); // 30s default
  const [theme, setTheme] = useState<'dark' | 'light'>('dark');

  const loadData = useCallback(
    async (isInitial = false) => {
      if (isInitial) {
        setIsLoading(true);
      } else {
        setIsRefreshing(true);
      }

      try {
        const result = await fetchOverviewData(filters);
        setData(result);
        setError(null);
      } catch (err: any) {
        console.error('[Overview] Error fetching data:', err);
        // Non-blocking: keep prior data if available
        setError(err.message || 'Failed to refresh telemetry from backend API');
      } finally {
        setIsLoading(false);
        setIsRefreshing(false);
      }
    },
    [filters]
  );

  // Initial load and filter change
  useEffect(() => {
    loadData(true);
  }, [loadData]);

  // Auto-refresh interval
  useEffect(() => {
    if (autoRefreshInterval <= 0) return;
    const timer = setInterval(() => {
      loadData(false);
    }, autoRefreshInterval * 1000);
    return () => clearInterval(timer);
  }, [autoRefreshInterval, loadData]);

  const toggleTheme = () => {
    const nextTheme = theme === 'dark' ? 'light' : 'dark';
    setTheme(nextTheme);
    document.documentElement.setAttribute('data-theme', nextTheme);
  };

  return (
    <div className={`overview-module-container theme-${theme}`}>
      {/* 1. Global Header */}
      <OverviewHeader
        lastUpdated={data?.generated_at || ''}
        isRefreshing={isRefreshing}
        onRefresh={() => loadData(false)}
        theme={theme}
        onToggleTheme={toggleTheme}
      />

      {/* 2. Global Filter Bar */}
      <OverviewFilterBar
        filters={filters}
        onFilterChange={setFilters}
        autoRefreshInterval={autoRefreshInterval}
        onAutoRefreshChange={setAutoRefreshInterval}
      />

      {/* Non-blocking Error Banner */}
      {error && (
        <div className="non-blocking-error-banner">
          <span className="error-icon">⚠</span>
          <span className="error-text">
            <strong>Telemetry Sync Notice:</strong> {error}. Retaining prior valid operational state.
          </span>
          <button type="button" className="retry-btn" onClick={() => loadData(false)}>
            Retry Now
          </button>
        </div>
      )}

      {/* Main Content Area */}
      {isLoading && !data ? (
        <div className="overview-loading-state">
          <div className="loading-spinner"></div>
          <h2>Loading Infrastructure Overview...</h2>
          <p>Connecting to Operations Core and Zabbix Adapter telemetry engine.</p>
        </div>
      ) : !data ? (
        <div className="overview-error-state">
          <h2>Unable to Load Overview Telemetry</h2>
          <p>{error || 'No response received from the backend service.'}</p>
          <button type="button" className="retry-btn" onClick={() => loadData(true)}>
            Retry Connection
          </button>
        </div>
      ) : (
        <div className="overview-content-layout">
          {/* 3. Operational KPI & Health Summary */}
          <HealthSummary
            health={data.health}
            hosts={data.hosts}
            problems={data.problems}
            availability={data.availability}
            trend={data.trend}
            onFilterSeverity={(sev: number) =>
              setFilters((prev: OverviewFilters) => ({ ...prev, severity: sev }))
            }
            onFilterStatus={(st: string) =>
              setFilters((prev: OverviewFilters) => ({ ...prev, status: st }))
            }
          />


          {/* 4. Active Problems Table (Main Operational View) */}
          <ActiveProblemsTable
            problems={data.active_problems}
            isLoading={isRefreshing}
          />

          {/* 5. Infrastructure Domain Status & Top Problem Hosts */}
          <div className="overview-two-col-grid">
            <InfrastructureStatus infrastructure={data.infrastructure} />
            <TopProblemHosts hosts={data.top_problem_hosts} />
          </div>

          {/* 6. Recent Incidents & Operational Event Timeline */}
          <RecentEventsTimeline events={data.recent_events} />
        </div>
      )}
    </div>
  );
};
