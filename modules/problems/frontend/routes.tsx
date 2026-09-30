import React, { useState, useEffect, useCallback } from 'react';
import type { ProblemListResponse, ProblemFilters, TimeRangePreset } from './types';
import { fetchProblemsList } from './api';
import { ProblemsHeader } from './components/ProblemsHeader';
import { ProblemsSeverityBar } from './components/ProblemsSeverityBar';
import { ProblemsFilterBar } from './components/ProblemsFilterBar';
import { ProblemsTable } from './components/ProblemsTable';
import { ProblemDetailDrawer } from './components/ProblemDetailDrawer';
import { PaginationControls } from './components/PaginationControls';

function getTimestampsForPreset(preset: TimeRangePreset): { time_from?: number; time_till?: number } {
  if (preset === 'all') return {};
  const now = Math.floor(Date.now() / 1000);
  const secondsMap: Record<string, number> = {
    '15m': 15 * 60,
    '1h': 60 * 60,
    '6h': 6 * 3600,
    '24h': 24 * 3600,
    '7d': 7 * 86400,
    '30d': 30 * 86400,
  };
  const diff = secondsMap[preset] || 86400;
  return {
    time_from: now - diff,
    time_till: now,
  };
}

export const ProblemsPage: React.FC = () => {
  const [data, setData] = useState<ProblemListResponse | null>(null);
  const [filters, setFilters] = useState<ProblemFilters>({
    page: 1,
    page_size: 25,
    sort: 'clock',
    sortorder: 'DESC',
    time_preset: 'all',
  });
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isRefreshing, setIsRefreshing] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [refreshInterval, setRefreshInterval] = useState<number>(30);
  const [theme, setTheme] = useState<'dark' | 'light'>('dark');
  const [selectedEventId, setSelectedEventId] = useState<string | null>(null);

  const loadData = useCallback(
    async (isInitial = false) => {
      if (isInitial) {
        setIsLoading(true);
      } else {
        setIsRefreshing(true);
      }

      try {
        const timeBounds = getTimestampsForPreset(filters.time_preset || 'all');
        const queryFilters: ProblemFilters = {
          ...filters,
          time_from: timeBounds.time_from,
          time_till: timeBounds.time_till,
        };
        const result = await fetchProblemsList(queryFilters);
        setData(result);
        setError(null);
      } catch (err: any) {
        console.error('[Problems] Error fetching problems list:', err);
        setError(err.message || 'Failed to sync problems feed from backend API');
      } finally {
        setIsLoading(false);
        setIsRefreshing(false);
      }
    },
    [filters]
  );

  useEffect(() => {
    loadData(true);
  }, [loadData]);

  useEffect(() => {
    if (refreshInterval <= 0) return;
    const timer = setInterval(() => {
      loadData(false);
    }, refreshInterval * 1000);
    return () => clearInterval(timer);
  }, [refreshInterval, loadData]);

  const toggleTheme = () => {
    const nextTheme = theme === 'dark' ? 'light' : 'dark';
    setTheme(nextTheme);
    document.documentElement.setAttribute('data-theme', nextTheme);
  };

  // Severity toggle
  const handleToggleSeverity = (sev: number) => {
    setFilters((prev) => {
      const current = prev.severities || [];
      const next = current.includes(sev)
        ? current.filter((s) => s !== sev)
        : [...current, sev];
      return { ...prev, severities: next, page: 1 };
    });
  };

  const handleClearSeverities = () => {
    setFilters((prev) => ({ ...prev, severities: [], page: 1 }));
  };

  // Ack & Suppressed toggles
  const handleToggleAcknowledged = () => {
    setFilters((prev) => ({
      ...prev,
      acknowledged: prev.acknowledged === undefined ? true : prev.acknowledged ? false : undefined,
      page: 1,
    }));
  };

  const handleToggleSuppressed = () => {
    setFilters((prev) => ({
      ...prev,
      suppressed: prev.suppressed === undefined ? true : prev.suppressed ? false : undefined,
      page: 1,
    }));
  };

  const handleNavigateHost = (hostId: string) => {
    window.location.hash = `/servers?hostid=${encodeURIComponent(hostId)}`;
  };

  const handleInspectRootCause = (causeEventId: string) => {
    setSelectedEventId(causeEventId);
  };

  const handleResetFilters = () => {
    setFilters({
      page: 1,
      page_size: 25,
      sort: 'clock',
      sortorder: 'DESC',
      time_preset: 'all',
      severities: [],
      acknowledged: undefined,
      suppressed: undefined,
      search: '',
      group: '',
      host: '',
    });
  };

  const hasActiveFilters = Boolean(
    (filters.severities && filters.severities.length > 0) ||
    filters.acknowledged !== undefined ||
    filters.suppressed !== undefined ||
    filters.search ||
    filters.group ||
    filters.host ||
    (filters.time_preset && filters.time_preset !== 'all')
  );

  const summary = data?.summary || {
    total_problems: 0,
    by_severity: { disaster: 0, high: 0, average: 0, warning: 0, information: 0, unclassified: 0 },
    acknowledged_count: 0,
    unacknowledged_count: 0,
    suppressed_count: 0,
    mtta_seconds: null,
    mtta_human: 'NO_DATA',
    generated_at: '',
  };

  return (
    <div className="overview-container problems-module-container">
      {/* Top Header */}
      <ProblemsHeader
        totalProblems={summary.total_problems}
        mttaHuman={summary.mtta_human}
        lastUpdated={summary.generated_at ? new Date(summary.generated_at).toLocaleTimeString() : ''}
        isRefreshing={isRefreshing}
        onRefresh={() => loadData(false)}
        refreshInterval={refreshInterval}
        onIntervalChange={setRefreshInterval}
        theme={theme}
        onToggleTheme={toggleTheme}
      />

      {/* Main Content Body */}
      <main className="overview-main">
        {/* Severity Command Bar */}
        <ProblemsSeverityBar
          summary={summary.by_severity}
          acknowledgedCount={summary.acknowledged_count}
          unacknowledgedCount={summary.unacknowledged_count}
          suppressedCount={summary.suppressed_count}
          selectedSeverities={filters.severities || []}
          onToggleSeverity={handleToggleSeverity}
          onClearSeverities={handleClearSeverities}
          acknowledgedFilter={filters.acknowledged}
          onToggleAcknowledged={handleToggleAcknowledged}
          suppressedFilter={filters.suppressed}
          onToggleSuppressed={handleToggleSuppressed}
        />

        {/* Filter Bar */}
        <ProblemsFilterBar
          search={filters.search || ''}
          onSearchChange={(search) => setFilters((p) => ({ ...p, search, page: 1 }))}
          timePreset={filters.time_preset || 'all'}
          onTimePresetChange={(time_preset) => setFilters((p) => ({ ...p, time_preset, page: 1 }))}
          host={filters.host || ''}
          onHostChange={(host) => setFilters((p) => ({ ...p, host, page: 1 }))}
          group={filters.group || ''}
          onGroupChange={(group) => setFilters((p) => ({ ...p, group, page: 1 }))}
          acknowledged={filters.acknowledged}
          onAcknowledgedChange={(acknowledged) => setFilters((p) => ({ ...p, acknowledged, page: 1 }))}
          suppressed={filters.suppressed}
          onSuppressedChange={(suppressed) => setFilters((p) => ({ ...p, suppressed, page: 1 }))}
          sortBy={filters.sort || 'clock'}
          onSortByChange={(sort) => setFilters((p) => ({ ...p, sort, page: 1 }))}
          sortOrder={filters.sortorder || 'DESC'}
          onSortOrderToggle={() =>
            setFilters((p) => ({ ...p, sortorder: p.sortorder === 'DESC' ? 'ASC' : 'DESC', page: 1 }))
          }
          onResetFilters={handleResetFilters}
          hasActiveFilters={hasActiveFilters}
        />

        {/* Non-blocking Error Banner */}
        {error && (
          <div className="error-banner">
            <span className="error-icon">⚠️</span>
            <div className="error-content">
              <strong>Telemetry Sync Issue:</strong> {error}
            </div>
            <button type="button" className="retry-btn" onClick={() => loadData(false)}>
              Retry Sync
            </button>
          </div>
        )}

        {/* Problems Table */}
        <ProblemsTable
          problems={data?.items || []}
          isLoading={isLoading}
          selectedEventId={selectedEventId}
          onSelectProblem={(id) => setSelectedEventId(id)}
          onNavigateHost={handleNavigateHost}
          onInspectRootCause={handleInspectRootCause}
        />

        {/* Pagination Controls */}
        {data && (
          <PaginationControls
            page={data.page}
            pageSize={data.page_size}
            totalCount={data.total_count}
            totalPages={data.total_pages}
            onPageChange={(newPage) => setFilters((p) => ({ ...p, page: newPage }))}
            onPageSizeChange={(newSize) => setFilters((p) => ({ ...p, page_size: newSize, page: 1 }))}
          />
        )}
      </main>

      {/* Problem Detail Drawer */}
      <ProblemDetailDrawer
        eventId={selectedEventId}
        onClose={() => setSelectedEventId(null)}
        onNavigateHost={handleNavigateHost}
        onInspectRootCause={handleInspectRootCause}
      />
    </div>
  );
};
