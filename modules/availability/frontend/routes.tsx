import React, { useState, useEffect } from 'react';
import type {
  AvailabilityOverview,
  ServiceAvailabilityItem,
  SLADefinitionItem,
  ServiceFilters
} from './types';
import {
  fetchAvailabilityOverview,
  fetchServicesList,
  fetchSLAsList
} from './api';

import { AvailabilityHeader } from './components/AvailabilityHeader';
import { AvailabilitySummaryCards } from './components/AvailabilitySummaryCards';
import { ServicesTable } from './components/ServicesTable';
import { SLAsTable } from './components/SLAsTable';
import { AvailabilityTrendChart } from './components/AvailabilityTrendChart';
import { ServiceDetailDrawer } from './components/ServiceDetailDrawer';

export const AvailabilityPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'services' | 'slas' | 'trend'>('services');
  const [timeRange, setTimeRange] = useState<string>('30d');

  // Overview state
  const [overview, setOverview] = useState<AvailabilityOverview | null>(null);
  const [isOverviewLoading, setIsOverviewLoading] = useState<boolean>(true);

  // Services state
  // Services state
  const [services, setServices] = useState<ServiceAvailabilityItem[]>([]);
  const [totalServicesCount, setTotalServicesCount] = useState<number>(0);
  const [totalServicesPages, setTotalServicesPages] = useState<number>(1);
  const [isServicesTruncated, setIsServicesTruncated] = useState<boolean>(false);
  const [candidateLimit, setCandidateLimit] = useState<number>(500);
  const [serviceFilters, setServiceFilters] = useState<ServiceFilters>({
    page: 1,
    page_size: 25,
    sort_by: 'status',
    sort_order: 'desc'
  });
  const [isServicesLoading, setIsServicesLoading] = useState<boolean>(true);

  // SLAs state
  const [slas, setSlas] = useState<SLADefinitionItem[]>([]);
  const [totalSlasCount, setTotalSlasCount] = useState<number>(0);
  const [totalSlasPages, setTotalSlasPages] = useState<number>(1);
  const [slaPage, setSlaPage] = useState<number>(1);
  const [slaPageSize, setSlaPageSize] = useState<number>(25);
  const [isSlasLoading, setIsSlasLoading] = useState<boolean>(true);

  // Drawer state
  const [selectedService, setSelectedService] = useState<ServiceAvailabilityItem | null>(null);

  // Global Error state
  const [error, setError] = useState<string | null>(null);

  const [refreshTrigger, setRefreshTrigger] = useState<number>(0);

  // FNT-01: Cancellation-safe data fetching with AbortController
  useEffect(() => {
    const controller = new AbortController();
    setIsOverviewLoading(true);

    fetchAvailabilityOverview({ time_range: timeRange, signal: controller.signal })
      .then((data) => setOverview(data))
      .catch((err) => {
        if (err.name !== 'AbortError') {
          setError(err.message || 'Failed to load availability overview');
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) {
          setIsOverviewLoading(false);
        }
      });

    return () => controller.abort();
  }, [timeRange, refreshTrigger]);

  useEffect(() => {
    const controller = new AbortController();
    setIsServicesLoading(true);

    fetchServicesList(serviceFilters, controller.signal)
      .then((data) => {
        setServices(data.items);
        setTotalServicesCount(data.total_count);
        setTotalServicesPages(data.total_pages);
        setIsServicesTruncated(Boolean(data.summary?.is_truncated));
        if (data.summary?.candidate_limit) {
          setCandidateLimit(data.summary.candidate_limit);
        }
      })
      .catch((err) => {
        if (err.name !== 'AbortError') {
          setError(err.message || 'Failed to load business services');
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) {
          setIsServicesLoading(false);
        }
      });

    return () => controller.abort();
  }, [serviceFilters, refreshTrigger]);

  useEffect(() => {
    const controller = new AbortController();
    setIsSlasLoading(true);

    fetchSLAsList({ page: slaPage, page_size: slaPageSize }, controller.signal)
      .then((data) => {
        setSlas(data.items);
        setTotalSlasCount(data.total_count);
        setTotalSlasPages(data.total_pages);
      })
      .catch((err) => {
        if (err.name !== 'AbortError') {
          setError(err.message || 'Failed to load SLAs');
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) {
          setIsSlasLoading(false);
        }
      });

    return () => controller.abort();
  }, [slaPage, slaPageSize, refreshTrigger]);

  const handleRefreshAll = () => {
    setError(null);
    setRefreshTrigger((prev) => prev + 1);
  };

  const handleServiceFilterChange = (newFilters: Partial<ServiceFilters>) => {
    setServiceFilters((prev) => ({ ...prev, ...newFilters }));
  };

  return (
    <div className="module-page-container">
      {/* Header */}
      <AvailabilityHeader
        timeRange={timeRange}
        onTimeRangeChange={setTimeRange}
        onRefresh={handleRefreshAll}
        isLoading={isOverviewLoading || isServicesLoading || isSlasLoading}
        generatedAt={overview?.generated_at}
      />

      {/* Error Banner */}
      {error && (
        <div className="alert-banner alert-error">
          <div className="alert-message">
            <strong>Operational Telemetry Warning:</strong> {error}
          </div>
          <button type="button" className="btn btn-sm btn-secondary" onClick={handleRefreshAll}>
            Retry
          </button>
        </div>
      )}

      {/* Summary KPI Cards */}
      <AvailabilitySummaryCards
        overview={overview}
        isLoading={isOverviewLoading}
      />

      {/* Module Navigation Tabs */}
      <div className="module-tabs-bar">
        <button
          type="button"
          className={`tab-btn ${activeTab === 'services' ? 'active' : ''}`}
          onClick={() => setActiveTab('services')}
        >
          Business Services ({totalServicesCount})
        </button>
        <button
          type="button"
          className={`tab-btn ${activeTab === 'slas' ? 'active' : ''}`}
          onClick={() => setActiveTab('slas')}
        >
          SLA Registry ({totalSlasCount})
        </button>
        <button
          type="button"
          className={`tab-btn ${activeTab === 'trend' ? 'active' : ''}`}
          onClick={() => setActiveTab('trend')}
        >
          Availability & SLI Trends
        </button>
      </div>

      {/* Active Tab Content */}
      <div className="tab-content-area">
        {activeTab === 'services' && (
          <ServicesTable
            services={services}
            totalCount={totalServicesCount}
            totalPages={totalServicesPages}
            filters={serviceFilters}
            onFilterChange={handleServiceFilterChange}
            onSelectService={setSelectedService}
            isLoading={isServicesLoading}
            isTruncated={isServicesTruncated}
            candidateLimit={candidateLimit}
          />
        )}

        {activeTab === 'slas' && (
          <SLAsTable
            slas={slas}
            totalCount={totalSlasCount}
            totalPages={totalSlasPages}
            page={slaPage}
            pageSize={slaPageSize}
            onPageChange={setSlaPage}
            onPageSizeChange={(s) => {
              setSlaPageSize(s);
              setSlaPage(1);
            }}
            isLoading={isSlasLoading}
          />
        )}

        {activeTab === 'trend' && (
          <AvailabilityTrendChart slas={slas} />
        )}
      </div>

      {/* Service Detail Drawer */}
      <ServiceDetailDrawer
        service={selectedService}
        onClose={() => setSelectedService(null)}
      />
    </div>
  );
};
