import React, { useState, useEffect, useCallback, useRef } from 'react';
import type { TopNResponse, TopNOverviewResponse } from './types';
import { fetchTopNRankings, fetchTopNOverview } from './api';
import { TopNHeader } from './components/TopNHeader';
import { TopNTable } from './components/TopNTable';
import { TopNOverviewCards } from './components/TopNOverviewCards';

export const TopNPage: React.FC = () => {
  const [metric, setMetric] = useState<'cpu' | 'memory' | 'storage' | 'problems'>('cpu');
  const [limit, setLimit] = useState<number>(10);
  const [order, setOrder] = useState<'desc' | 'asc'>('desc');
  const [group, setGroup] = useState<string>('');

  const [rankingData, setRankingData] = useState<TopNResponse | null>(null);
  const [overviewData, setOverviewData] = useState<TopNOverviewResponse | null>(null);

  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isRefreshing, setIsRefreshing] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<string>('');

  // AbortController refs to protect against stale request races (FNT-01 pattern)
  const rankingAbortControllerRef = useRef<AbortController | null>(null);
  const overviewAbortControllerRef = useRef<AbortController | null>(null);

  // 1. Fetch Rankings for current metric
  const loadData = useCallback(async (isRefresh = false) => {
    if (rankingAbortControllerRef.current) {
      rankingAbortControllerRef.current.abort();
    }
    if (overviewAbortControllerRef.current) {
      overviewAbortControllerRef.current.abort();
    }

    const rankingCtrl = new AbortController();
    const overviewCtrl = new AbortController();
    rankingAbortControllerRef.current = rankingCtrl;
    overviewAbortControllerRef.current = overviewCtrl;

    if (isRefresh) {
      setIsRefreshing(true);
    } else {
      setIsLoading(true);
    }
    setError(null);

    try {
      const [rankingRes, overviewRes] = await Promise.all([
        fetchTopNRankings({ metric, limit, order, group: group || undefined }, rankingCtrl.signal),
        fetchTopNOverview({ limit: 5, group: group || undefined }, overviewCtrl.signal)
      ]);

      setRankingData(rankingRes);
      setOverviewData(overviewRes);
      setLastUpdated(new Date().toLocaleTimeString());
    } catch (err: any) {
      if (err.name !== 'AbortError') {
        setError(err.message || 'Failed to fetch Top N rankings');
      }
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  }, [metric, limit, order, group]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleRefresh = () => {
    loadData(true);
  };

  return (
    <div className="topn-container" style={{ padding: '20px', minHeight: '100vh', background: '#0f172a', color: '#f8fafc' }}>
      <TopNHeader
        totalEvaluated={rankingData?.total_evaluated_hosts || 0}
        lastUpdated={lastUpdated}
        isRefreshing={isRefreshing}
        onRefresh={handleRefresh}
        selectedMetric={metric}
        onMetricChange={setMetric}
        limit={limit}
        onLimitChange={setLimit}
        group={group}
        onGroupChange={setGroup}
      />

      {/* Truncation Notice Banner */}
      {rankingData?.is_truncated && (
        <div
          className="topn-truncation-banner"
          style={{
            padding: '10px 16px',
            background: 'rgba(245, 158, 11, 0.15)',
            border: '1px solid #f59e0b',
            borderRadius: '6px',
            color: '#f59e0b',
            margin: '16px 0',
            fontSize: '12px'
          }}
        >
          ⚠️ {rankingData.truncation_reason}
        </div>
      )}

      {error && (
        <div
          className="topn-error-banner"
          style={{
            padding: '12px 16px',
            background: 'rgba(239, 68, 68, 0.15)',
            border: '1px solid #ef4444',
            borderRadius: '6px',
            color: '#ef4444',
            margin: '16px 0',
            fontSize: '13px'
          }}
        >
          {error}
        </div>
      )}

      {/* Multi-Dimension Mini Leaderboards */}
      {overviewData && (
        <div style={{ marginTop: '16px' }}>
          <h3 style={{ fontSize: '14px', fontWeight: 600, color: '#94a3b8', marginBottom: '12px' }}>
            Resource Utilization Overview
          </h3>
          <TopNOverviewCards
            cpu={overviewData.cpu}
            memory={overviewData.memory}
            storage={overviewData.storage}
            problems={overviewData.problems}
            onSelectDimension={setMetric}
          />
        </div>
      )}

      {/* Main Leaderboard Table */}
      <div style={{ marginTop: '8px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
          <h3 style={{ fontSize: '14px', fontWeight: 600, color: '#f8fafc', margin: 0 }}>
            {rankingData?.metric_display_name || 'Rankings'} (Top {limit})
          </h3>

          <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
            {/* Sort Order Toggle */}
            <button
              type="button"
              onClick={() => setOrder(order === 'desc' ? 'asc' : 'desc')}
              style={{
                padding: '4px 10px',
                background: '#1e293b',
                border: '1px solid #334155',
                borderRadius: '4px',
                color: '#cbd5e1',
                fontSize: '12px',
                cursor: 'pointer'
              }}
            >
              Order: {order === 'desc' ? 'Highest First (DESC)' : 'Lowest First (ASC)'}
            </button>
          </div>
        </div>

        <TopNTable
          items={rankingData?.items || []}
          metricName={rankingData?.metric_display_name || metric}
          isLoading={isLoading}
        />
      </div>
    </div>
  );
};
