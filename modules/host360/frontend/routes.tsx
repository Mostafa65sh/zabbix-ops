import React, { useState, useEffect, useCallback, useRef } from 'react';
import type {
  Host360ListItem,
  Host360Detail,
  Host360TelemetryResponse
} from './types';
import {
  fetchHost360List,
  fetchHost360Detail,
  fetchHostTelemetry
} from './api';
import { Host360Header } from './components/Host360Header';
import { HostSelector } from './components/HostSelector';
import { HostTelemetryGauges } from './components/HostTelemetryGauges';
import { HostTelemetryCharts } from './components/HostTelemetryCharts';
import { HostInterfacesTable } from './components/HostInterfacesTable';
import { HostProblemsList } from './components/HostProblemsList';

export const Host360Page: React.FC = () => {
  const [hosts, setHosts] = useState<Host360ListItem[]>([]);
  const [selectedHostId, setSelectedHostId] = useState<string>('');
  const [hostDetail, setHostDetail] = useState<Host360Detail | null>(null);
  const [telemetry, setTelemetry] = useState<Host360TelemetryResponse | null>(null);

  const [searchTerm, setSearchTerm] = useState<string>('');
  const [timeRange, setTimeRange] = useState<string>('24h');

  const [isLoadingHosts, setIsLoadingHosts] = useState<boolean>(true);
  const [isLoadingDetail, setIsLoadingDetail] = useState<boolean>(false);
  const [isLoadingTelemetry, setIsLoadingTelemetry] = useState<boolean>(false);
  const [isRefreshing, setIsRefreshing] = useState<boolean>(false);

  const [error, setError] = useState<string | null>(null);
  const [truncationNotice, setTruncationNotice] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<string>('');

  // AbortController refs to protect against stale request races (FNT-01 pattern)
  const hostsAbortControllerRef = useRef<AbortController | null>(null);
  const detailAbortControllerRef = useRef<AbortController | null>(null);
  const telemetryAbortControllerRef = useRef<AbortController | null>(null);

  // 1. Load Hosts List
  const loadHosts = useCallback(async () => {
    if (hostsAbortControllerRef.current) {
      hostsAbortControllerRef.current.abort();
    }
    const controller = new AbortController();
    hostsAbortControllerRef.current = controller;

    setIsLoadingHosts(true);
    setError(null);

    try {
      const res = await fetchHost360List({ search: searchTerm, page: 1, page_size: 50 }, controller.signal);
      setHosts(res.items);
      setTruncationNotice(res.is_truncated ? res.truncation_reason || 'Host list capped at 1000 nodes.' : null);
      // Auto-select first host if none selected or selected host disappeared
      if (res.items.length > 0) {
        if (!selectedHostId || !res.items.some((h) => h.host_id === selectedHostId)) {
          setSelectedHostId(res.items[0].host_id);
        }
      } else {
        setSelectedHostId('');
        setHostDetail(null);
        setTelemetry(null);
      }
    } catch (err: any) {
      if (err.name !== 'AbortError') {
        setError(err.message || 'Failed to fetch host inventory');
      }
    } finally {
      setIsLoadingHosts(false);
    }
  }, [searchTerm, selectedHostId]);

  // 2. Load Selected Host Detail & Telemetry
  const loadHostData = useCallback(async (hostId: string, range: string) => {
    if (!hostId) return;

    // Abort previous inflight calls
    if (detailAbortControllerRef.current) {
      detailAbortControllerRef.current.abort();
    }
    if (telemetryAbortControllerRef.current) {
      telemetryAbortControllerRef.current.abort();
    }

    const detailController = new AbortController();
    const telemetryController = new AbortController();
    detailAbortControllerRef.current = detailController;
    telemetryAbortControllerRef.current = telemetryController;

    setIsLoadingDetail(true);
    setIsLoadingTelemetry(true);
    setError(null);

    try {
      const [detailRes, telemetryRes] = await Promise.all([
        fetchHost360Detail(hostId, detailController.signal),
        fetchHostTelemetry(hostId, range, telemetryController.signal)
      ]);

      setHostDetail(detailRes);
      setTelemetry(telemetryRes);
      setLastUpdated(new Date().toLocaleTimeString());
    } catch (err: any) {
      if (err.name !== 'AbortError') {
        setError(err.message || 'Failed to fetch host telemetry details');
      }
    } finally {
      setIsLoadingDetail(false);
      setIsLoadingTelemetry(false);
    }
  }, []);

  // Initial fetch and on search change
  useEffect(() => {
    loadHosts();
  }, [loadHosts]);

  // When selected host or time range changes
  useEffect(() => {
    if (selectedHostId) {
      loadHostData(selectedHostId, timeRange);
    }
  }, [selectedHostId, timeRange, loadHostData]);

  // Manual Refresh
  const handleRefresh = async () => {
    setIsRefreshing(true);
    await loadHosts();
    if (selectedHostId) {
      await loadHostData(selectedHostId, timeRange);
    }
    setIsRefreshing(false);
  };

  return (
    <div className="host360-container" style={{ padding: '20px', minHeight: '100vh', background: '#0f172a', color: '#f8fafc' }}>
      <Host360Header
        hostName={hostDetail?.name}
        hostStatus={hostDetail?.status}
        availability={hostDetail?.overall_availability}
        lastUpdated={lastUpdated}
        isRefreshing={isRefreshing}
        onRefresh={handleRefresh}
        timeRange={timeRange}
        onTimeRangeChange={setTimeRange}
      />

      <HostSelector
        hosts={hosts}
        selectedHostId={selectedHostId}
        onSelectHost={setSelectedHostId}
        searchTerm={searchTerm}
        onSearchChange={setSearchTerm}
        isLoading={isLoadingHosts}
      />

      {error && (
        <div
          className="host360-error-banner"
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

      {truncationNotice && (
        <div
          className="host360-truncation-banner"
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
          ⚠️ {truncationNotice}
        </div>
      )}

      {isLoadingHosts && !hostDetail ? (
        <div style={{ textAlign: 'center', padding: '60px 0', color: '#94a3b8' }}>
          Loading Host 360 Inventory...
        </div>
      ) : isLoadingDetail && !hostDetail ? (
        <div style={{ textAlign: 'center', padding: '60px 0', color: '#94a3b8' }}>
          Loading Host Profile & Telemetry...
        </div>
      ) : !selectedHostId || !hostDetail ? (
        <div
          style={{
            textAlign: 'center',
            padding: '60px 0',
            background: '#1e293b',
            borderRadius: '8px',
            border: '1px dashed #334155',
            color: '#94a3b8'
          }}
        >
          <h3>No Host Selected</h3>
          <p style={{ fontSize: '13px', marginTop: '8px' }}>
            Choose a monitored host above to inspect 360-degree telemetry, hardware pressure, and incidents.
          </p>
        </div>
      ) : (
        <div className="host360-content">
          {/* Metadata Bar */}
          <div
            style={{
              display: 'flex',
              gap: '24px',
              padding: '12px 16px',
              background: '#1e293b',
              border: '1px solid #334155',
              borderRadius: '8px',
              marginBottom: '16px',
              fontSize: '13px',
              flexWrap: 'wrap'
            }}
          >
            <div>
              <span style={{ color: '#64748b' }}>Technical Name: </span>
              <strong>{hostDetail.technical_name}</strong>
            </div>
            <div>
              <span style={{ color: '#64748b' }}>Host ID: </span>
              <code>{hostDetail.host_id}</code>
            </div>
            <div>
              <span style={{ color: '#64748b' }}>Groups: </span>
              <span>{hostDetail.groups.join(', ') || 'Unassigned'}</span>
            </div>
            {hostDetail.inventory?.location && (
              <div>
                <span style={{ color: '#64748b' }}>Site: </span>
                <span>{hostDetail.inventory.location}</span>
              </div>
            )}
            {hostDetail.maintenance?.active && (
              <div>
                <span style={{ color: '#f59e0b', fontWeight: 600 }}>🛠️ Maintenance Active</span>
              </div>
            )}
          </div>

          {/* Telemetry Gauges */}
          <HostTelemetryGauges telemetry={hostDetail.telemetry} />

          {/* Historical Telemetry Charts */}
          {telemetry && (
            <HostTelemetryCharts series={telemetry.series} isLoading={isLoadingTelemetry} />
          )}

          {/* Interfaces Breakdown */}
          <HostInterfacesTable interfaces={hostDetail.interfaces} />

          {/* Active Problems / Incidents */}
          <HostProblemsList problems={hostDetail.active_problems} />
        </div>
      )}
    </div>
  );
};
