import React, { useState, useEffect, useRef } from 'react';
import type { GlobalSearchResponse, CategoryFilterKey } from './types';
import { fetchGlobalSearch } from './api';
import { SearchInputBar } from './components/SearchInputBar';
import { HostResultsCard } from './components/HostResultsCard';
import { ProblemResultsCard } from './components/ProblemResultsCard';
import { ServiceResultsCard } from './components/ServiceResultsCard';
import { ItemResultsCard } from './components/ItemResultsCard';

export const GlobalSearchPage: React.FC = () => {
  const [query, setQuery] = useState('');
  const [activeCategory, setActiveCategory] = useState<CategoryFilterKey>('all');
  const [data, setData] = useState<GlobalSearchResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [permissionDenied, setPermissionDenied] = useState(false);

  const abortControllerRef = useRef<AbortController | null>(null);

  // Debounced search effect
  useEffect(() => {
    const trimmed = query.trim();

    if (!trimmed) {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
      setData(null);
      setLoading(false);
      setError(null);
      return;
    }

    setLoading(true);
    setError(null);
    setPermissionDenied(false);

    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    const controller = new AbortController();
    abortControllerRef.current = controller;

    const timer = setTimeout(() => {
      const categoriesParam = activeCategory === 'all' ? undefined : [activeCategory];

      fetchGlobalSearch(trimmed, categoriesParam, 20, controller.signal)
        .then((resp) => {
          setData(resp);
          setLoading(false);
        })
        .catch((err: unknown) => {
          if (controller.signal.aborted) return;
          const msg = err instanceof Error ? err.message : String(err);
          if (msg.includes('403')) {
            setPermissionDenied(true);
          } else {
            setError(msg);
          }
          setLoading(false);
        });
    }, 250);

    return () => {
      clearTimeout(timer);
      controller.abort();
    };
  }, [query, activeCategory]);

  const handleRetry = () => {
    if (!query.trim()) return;
    setLoading(true);
    setError(null);
    const categoriesParam = activeCategory === 'all' ? undefined : [activeCategory];
    fetchGlobalSearch(query.trim(), categoriesParam, 20)
      .then((resp) => {
        setData(resp);
        setLoading(false);
      })
      .catch((err: unknown) => {
        const msg = err instanceof Error ? err.message : String(err);
        setError(msg);
        setLoading(false);
      });
  };

  const isIdle = !query.trim();
  const isEmpty = !isIdle && !loading && !error && data && data.total_results === 0;

  return (
    <div style={{ padding: '1.5rem', maxWidth: '1400px', margin: '0 auto' }}>
      {/* Module Title Header */}
      <div style={{ marginBottom: '1.25rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <h2 style={{ fontSize: '1.5rem', fontWeight: 700, color: '#f8fafc', margin: 0 }}>
            Global Search
          </h2>
          <span
            style={{
              backgroundColor: '#0284c7',
              color: '#f8fafc',
              fontSize: '0.75rem',
              fontWeight: 600,
              padding: '0.2rem 0.5rem',
              borderRadius: '4px',
            }}
          >
            v1.0.0
          </span>
        </div>
        <p style={{ color: '#94a3b8', fontSize: '0.875rem', marginTop: '0.25rem' }}>
          Unified cross-platform lookup across Monitored Hosts, Active Problems, Business Services, and Metric Items.
        </p>
      </div>

      {/* Permission Denied Banner */}
      {permissionDenied && (
        <div
          style={{
            backgroundColor: 'rgba(239, 68, 68, 0.15)',
            border: '1px solid #ef4444',
            color: '#fca5a5',
            padding: '1rem',
            borderRadius: '8px',
            marginBottom: '1.5rem',
          }}
        >
          <strong>Access Denied:</strong> You lack the required permission (
          <code>module.global_search.view</code>) to perform global searches.
        </div>
      )}

      {/* Search Input and Category Filter Bar */}
      <SearchInputBar
        query={query}
        onQueryChange={setQuery}
        activeCategory={activeCategory}
        onCategoryChange={setActiveCategory}
        categoriesData={data?.categories}
        loading={loading}
      />

      {/* Error Banner with Retry */}
      {error && (
        <div
          style={{
            backgroundColor: 'rgba(239, 68, 68, 0.15)',
            border: '1px solid #ef4444',
            color: '#fca5a5',
            padding: '1rem',
            borderRadius: '8px',
            marginBottom: '1.5rem',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}
        >
          <div>
            <strong>Search Error:</strong> {error}
          </div>
          <button
            type="button"
            onClick={handleRetry}
            style={{
              backgroundColor: '#ef4444',
              color: '#ffffff',
              border: 'none',
              borderRadius: '4px',
              padding: '0.4rem 0.85rem',
              cursor: 'pointer',
              fontWeight: 600,
            }}
          >
            Retry
          </button>
        </div>
      )}

      {/* Idle Guidance State */}
      {isIdle && (
        <div
          style={{
            backgroundColor: '#1e293b',
            border: '1px dashed #334155',
            borderRadius: '8px',
            padding: '3rem 2rem',
            textAlign: 'center',
            color: '#94a3b8',
          }}
        >
          <div style={{ fontSize: '2.5rem', marginBottom: '1rem' }}>🔍</div>
          <h3 style={{ color: '#f8fafc', fontSize: '1.25rem', marginBottom: '0.5rem' }}>
            Instant Infrastructure Discovery
          </h3>
          <p style={{ maxWidth: '600px', margin: '0 auto', fontSize: '0.9rem', lineHeight: '1.5' }}>
            Type any host name, IP address, problem description, business service, or metric key to query across all Zabbix 7.0.5 entities simultaneously.
          </p>
          <div
            style={{
              display: 'flex',
              gap: '0.5rem',
              justifyContent: 'center',
              marginTop: '1.5rem',
              flexWrap: 'wrap',
            }}
          >
            {['server-app', '192.168', 'cpu', 'disk', 'gateway'].map((hint) => (
              <button
                key={hint}
                type="button"
                onClick={() => setQuery(hint)}
                style={{
                  backgroundColor: '#334155',
                  color: '#38bdf8',
                  border: 'none',
                  borderRadius: '4px',
                  padding: '0.3rem 0.75rem',
                  fontSize: '0.8rem',
                  cursor: 'pointer',
                  fontFamily: 'monospace',
                }}
              >
                {hint}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Loading Skeleton */}
      {loading && !data && (
        <div style={{ padding: '2rem 0' }}>
          <div
            style={{
              height: '48px',
              backgroundColor: '#1e293b',
              borderRadius: '6px',
              marginBottom: '1rem',
              animation: 'pulse 1.5s infinite',
            }}
          />
          <div
            style={{
              height: '180px',
              backgroundColor: '#1e293b',
              borderRadius: '6px',
              animation: 'pulse 1.5s infinite',
            }}
          />
        </div>
      )}

      {/* Empty State */}
      {isEmpty && (
        <div
          style={{
            backgroundColor: '#1e293b',
            border: '1px solid #334155',
            borderRadius: '8px',
            padding: '3rem 2rem',
            textAlign: 'center',
            color: '#94a3b8',
          }}
        >
          <div style={{ fontSize: '2rem', marginBottom: '0.75rem' }}>📂</div>
          <h3 style={{ color: '#f8fafc', fontSize: '1.1rem', marginBottom: '0.25rem' }}>
            No Matching Records Found
          </h3>
          <p style={{ fontSize: '0.875rem' }}>
            No hosts, problems, services, or metric items matched the search term "{query}".
          </p>
        </div>
      )}

      {/* Results Rendering */}
      {data && data.total_results > 0 && (
        <div>
          {(activeCategory === 'all' || activeCategory === 'hosts') && (
            <HostResultsCard data={data.categories.hosts} />
          )}

          {(activeCategory === 'all' || activeCategory === 'problems') && (
            <ProblemResultsCard data={data.categories.problems} />
          )}

          {(activeCategory === 'all' || activeCategory === 'services') && (
            <ServiceResultsCard data={data.categories.services} />
          )}

          {(activeCategory === 'all' || activeCategory === 'items') && (
            <ItemResultsCard data={data.categories.items} />
          )}
        </div>
      )}
    </div>
  );
};
