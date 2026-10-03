import React, { useState, useEffect, useCallback, useRef } from 'react';
import type { GraphTarget, MultiSeriesGraphResponse } from './types';
import { fetchGraphTargets, fetchGraphSeries } from './api';
import { GraphHeader } from './components/GraphHeader';
import { TargetSelector } from './components/TargetSelector';
import { MultiSeriesChart } from './components/MultiSeriesChart';

export const GraphExplorerPage: React.FC = () => {
  const [targets, setTargets] = useState<GraphTarget[]>([]);
  const [selectedHostIds, setSelectedHostIds] = useState<string[]>([]);
  const [selectedMetrics, setSelectedMetrics] = useState<string[]>(['cpu', 'memory']);
  const [timeRange, setTimeRange] = useState<string>('24h');
  const [searchTerm, setSearchTerm] = useState<string>('');

  const [graphData, setGraphData] = useState<MultiSeriesGraphResponse | null>(null);

  const [isLoadingTargets, setIsLoadingTargets] = useState<boolean>(true);
  const [isLoadingSeries, setIsLoadingSeries] = useState<boolean>(false);
  const [isRefreshing, setIsRefreshing] = useState<boolean>(false);

  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<string>('');

  // AbortController refs to protect against stale request races (FNT-01 pattern)
  const targetsAbortControllerRef = useRef<AbortController | null>(null);
  const seriesAbortControllerRef = useRef<AbortController | null>(null);

  // 1. Load candidate targets
  const loadTargets = useCallback(async () => {
    if (targetsAbortControllerRef.current) {
      targetsAbortControllerRef.current.abort();
    }
    const ctrl = new AbortController();
    targetsAbortControllerRef.current = ctrl;

    setIsLoadingTargets(true);
    setError(null);

    try {
      const res = await fetchGraphTargets({ search: searchTerm }, ctrl.signal);
      setTargets(res.targets);
      // Auto-select first two hosts initially if none selected
      if (res.targets.length > 0 && selectedHostIds.length === 0) {
        setSelectedHostIds(res.targets.slice(0, 2).map((t) => t.host_id));
      }
    } catch (err: any) {
      if (err.name !== 'AbortError') {
        setError(err.message || 'Failed to load graph targets');
      }
    } finally {
      setIsLoadingTargets(false);
    }
  }, [searchTerm, selectedHostIds.length]);

  // 2. Load series data
  const loadSeries = useCallback(async (isRefresh = false) => {
    if (selectedHostIds.length === 0 || selectedMetrics.length === 0) {
      setGraphData(null);
      return;
    }

    if (seriesAbortControllerRef.current) {
      seriesAbortControllerRef.current.abort();
    }
    const ctrl = new AbortController();
    seriesAbortControllerRef.current = ctrl;

    if (isRefresh) {
      setIsRefreshing(true);
    } else {
      setIsLoadingSeries(true);
    }
    setError(null);

    try {
      const res = await fetchGraphSeries(
        {
          host_ids: selectedHostIds,
          metrics: selectedMetrics,
          time_range: timeRange
        },
        ctrl.signal
      );
      setGraphData(res);
      setLastUpdated(new Date().toLocaleTimeString());
    } catch (err: any) {
      if (err.name !== 'AbortError') {
        setError(err.message || 'Failed to fetch graph series telemetry');
      }
    } finally {
      setIsLoadingSeries(false);
      setIsRefreshing(false);
    }
  }, [selectedHostIds, selectedMetrics, timeRange]);

  useEffect(() => {
    loadTargets();
  }, [loadTargets]);

  useEffect(() => {
    loadSeries();
  }, [loadSeries]);

  const handleToggleHost = (hostId: string) => {
    setSelectedHostIds((prev) => {
      if (prev.includes(hostId)) {
        return prev.filter((id) => id !== hostId);
      }
      if (prev.length >= 10) return prev; // Cap at 10
      return [...prev, hostId];
    });
  };

  const handleToggleMetric = (metric: string) => {
    setSelectedMetrics((prev) => {
      if (prev.includes(metric)) {
        return prev.filter((m) => m !== metric);
      }
      return [...prev, metric];
    });
  };

  const handleRefresh = () => {
    loadTargets();
    loadSeries(true);
  };

  return (
    <div className="graph-explorer-container" style={{ padding: '20px', minHeight: '100vh', background: '#0f172a', color: '#f8fafc' }}>
      <GraphHeader
        totalSeries={graphData?.total_series || 0}
        timeRange={timeRange}
        onTimeRangeChange={setTimeRange}
        lastUpdated={lastUpdated}
        isRefreshing={isRefreshing}
        onRefresh={handleRefresh}
      />

      <TargetSelector
        targets={targets}
        selectedHostIds={selectedHostIds}
        onToggleHost={handleToggleHost}
        selectedMetrics={selectedMetrics}
        onToggleMetric={handleToggleMetric}
        searchTerm={searchTerm}
        onSearchChange={setSearchTerm}
        isLoading={isLoadingTargets}
      />

      {/* Truncation Notice Banner */}
      {graphData?.is_truncated && (
        <div
          className="graph-truncation-banner"
          style={{
            padding: '10px 16px',
            background: 'rgba(245, 158, 11, 0.15)',
            border: '1px solid #f59e0b',
            borderRadius: '6px',
            color: '#f59e0b',
            marginBottom: '16px',
            fontSize: '12px'
          }}
        >
          ⚠️ {graphData.truncation_reason}
        </div>
      )}

      {error && (
        <div
          className="graph-error-banner"
          style={{
            padding: '12px 16px',
            background: 'rgba(239, 68, 68, 0.15)',
            border: '1px solid #ef4444',
            borderRadius: '6px',
            color: '#ef4444',
            marginBottom: '16px',
            fontSize: '13px'
          }}
        >
          {error}
        </div>
      )}

      {/* Interactive Graph Chart */}
      <MultiSeriesChart
        series={graphData?.series || []}
        isLoading={isLoadingSeries}
      />
    </div>
  );
};
