import React, { useState, useEffect, useCallback } from 'react';
import type { ServerListResponse, ServerDetailResponse, ServerFilters, ServerItem } from './types';
import { fetchServersList, fetchServerDetail } from './api';
import { ServersHeader } from './components/ServersHeader';
import { ServersSummaryCards } from './components/ServersSummaryCards';
import { ServersFilterBar } from './components/ServersFilterBar';
import { ServersTable } from './components/ServersTable';
import { ServerDetailDrawer } from './components/ServerDetailDrawer';
import { PaginationControls } from './components/PaginationControls';

export const ServersPage: React.FC = () => {
  const [data, setData] = useState<ServerListResponse | null>(null);
  const [filters, setFilters] = useState<ServerFilters>({
    page: 1,
    page_size: 25,
    sort_by: 'name',
    sort_order: 'asc',
  });
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isRefreshing, setIsRefreshing] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [autoRefreshInterval, setAutoRefreshInterval] = useState<number>(30);
  const [theme, setTheme] = useState<'dark' | 'light'>('dark');

  // Drawer state
  const [selectedServer, setSelectedServer] = useState<ServerItem | null>(null);
  const [selectedDetail, setSelectedDetail] = useState<ServerDetailResponse | null>(null);
  const [isLoadingDetail, setIsLoadingDetail] = useState<boolean>(false);

  const loadData = useCallback(
    async (isInitial = false) => {
      if (isInitial) {
        setIsLoading(true);
      } else {
        setIsRefreshing(true);
      }

      try {
        const result = await fetchServersList(filters);
        setData(result);
        setError(null);
      } catch (err: any) {
        console.error('[Servers] Error fetching servers list:', err);
        setError(err.message || 'Failed to sync servers inventory from backend API');
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

  const handleSelectServer = async (server: ServerItem) => {
    setSelectedServer(server);
    setSelectedDetail(null);
    setIsLoadingDetail(true);

    try {
      const detail = await fetchServerDetail(server.id);
      setSelectedDetail(detail);
    } catch (err: any) {
      console.error(`[Servers] Error loading details for server ${server.id}:`, err);
    } finally {
      setIsLoadingDetail(false);
    }
  };

  const handleCloseDrawer = () => {
    setSelectedServer(null);
    setSelectedDetail(null);
  };

  const handleFilterStatus = (status: string | undefined) => {
    setFilters({
      ...filters,
      status,
      page: 1,
    });
  };

  return (
    <div className={`overview-module-container servers-module-container theme-${theme}`}>
      {/* 1. Global Header */}
      <ServersHeader
        totalServers={data?.total_count || 0}
        lastUpdated={data?.generated_at || ''}
        isRefreshing={isRefreshing}
        onRefresh={() => loadData(false)}
        theme={theme}
        onToggleTheme={toggleTheme}
      />

      {/* 2. Top Summary KPI Cards */}
      {data && (
        <ServersSummaryCards
          summary={data.summary}
          onFilterStatus={handleFilterStatus}
        />
      )}

      {/* 3. Comprehensive Filter Bar */}
      <ServersFilterBar
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
            <strong>Inventory Sync Notice:</strong> {error}. Retaining prior valid operational state.
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
          <p>Connecting to Zabbix API and assembling server telemetry...</p>
        </div>
      ) : (
        <div className="servers-content-card">
          <ServersTable
            servers={data?.items || []}
            filters={filters}
            onFilterChange={setFilters}
            onSelectServer={handleSelectServer}
          />

          {data && (
            <PaginationControls
              page={data.page}
              pageSize={data.page_size}
              totalCount={data.total_count}
              totalPages={data.total_pages}
              onPageChange={(p) => setFilters({ ...filters, page: p })}
              onPageSizeChange={(s) => setFilters({ ...filters, page_size: s, page: 1 })}
            />
          )}
        </div>
      )}

      {/* Server Detail Drawer */}
      <ServerDetailDrawer
        server={selectedServer}
        detail={selectedDetail}
        isLoading={isLoadingDetail}
        onClose={handleCloseDrawer}
      />
    </div>
  );
};
