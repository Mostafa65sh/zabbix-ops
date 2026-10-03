import React from 'react';
import type { CategoryFilterKey, SearchCategories } from '../types';

interface SearchInputBarProps {
  query: string;
  onQueryChange: (q: string) => void;
  activeCategory: CategoryFilterKey;
  onCategoryChange: (cat: CategoryFilterKey) => void;
  categoriesData?: SearchCategories;
  loading: boolean;
}

export const SearchInputBar: React.FC<SearchInputBarProps> = ({
  query,
  onQueryChange,
  activeCategory,
  onCategoryChange,
  categoriesData,
  loading,
}) => {
  const getBadgeCount = (key: CategoryFilterKey): number | null => {
    if (!categoriesData) return null;
    switch (key) {
      case 'all':
        return (
          categoriesData.hosts.total_matched +
          categoriesData.problems.total_matched +
          categoriesData.services.total_matched +
          categoriesData.items.total_matched
        );
      case 'hosts':
        return categoriesData.hosts.total_matched;
      case 'problems':
        return categoriesData.problems.total_matched;
      case 'services':
        return categoriesData.services.total_matched;
      case 'items':
        return categoriesData.items.total_matched;
      default:
        return null;
    }
  };

  const categories: Array<{ key: CategoryFilterKey; label: string }> = [
    { key: 'all', label: 'All Categories' },
    { key: 'hosts', label: 'Hosts' },
    { key: 'problems', label: 'Problems' },
    { key: 'services', label: 'Services' },
    { key: 'items', label: 'Metrics / Items' },
  ];

  return (
    <div style={{ marginBottom: '1.5rem' }}>
      <div style={{ position: 'relative', display: 'flex', alignItems: 'center' }}>
        <input
          type="text"
          value={query}
          onChange={(e) => onQueryChange(e.target.value)}
          placeholder="Search hosts, IP addresses, problems, business services, or metric items..."
          style={{
            width: '100%',
            padding: '0.85rem 3rem 0.85rem 1rem',
            borderRadius: '8px',
            border: '1px solid #334155',
            backgroundColor: '#0f172a',
            color: '#f8fafc',
            fontSize: '1rem',
            outline: 'none',
            boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
          }}
          autoFocus
        />
        {query && (
          <button
            type="button"
            onClick={() => onQueryChange('')}
            style={{
              position: 'absolute',
              right: '1rem',
              background: 'none',
              border: 'none',
              color: '#94a3b8',
              cursor: 'pointer',
              fontSize: '1.1rem',
              padding: '0.2rem',
            }}
            title="Clear search"
          >
            ✕
          </button>
        )}
      </div>

      <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.85rem', flexWrap: 'wrap' }}>
        {categories.map((cat) => {
          const isActive = activeCategory === cat.key;
          const count = getBadgeCount(cat.key);
          return (
            <button
              key={cat.key}
              type="button"
              onClick={() => onCategoryChange(cat.key)}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '0.5rem',
                padding: '0.4rem 0.85rem',
                borderRadius: '6px',
                border: isActive ? '1px solid #38bdf8' : '1px solid #334155',
                backgroundColor: isActive ? 'rgba(56, 189, 248, 0.15)' : '#1e293b',
                color: isActive ? '#38bdf8' : '#94a3b8',
                cursor: 'pointer',
                fontSize: '0.875rem',
                fontWeight: isActive ? 600 : 400,
                transition: 'all 0.15s ease',
              }}
            >
              <span>{cat.label}</span>
              {count !== null && count > 0 && (
                <span
                  style={{
                    backgroundColor: isActive ? '#0284c7' : '#334155',
                    color: '#f8fafc',
                    padding: '0.1rem 0.45rem',
                    borderRadius: '10px',
                    fontSize: '0.75rem',
                  }}
                >
                  {count}
                </span>
              )}
            </button>
          );
        })}
        {loading && (
          <span style={{ color: '#94a3b8', fontSize: '0.85rem', alignSelf: 'center', marginLeft: 'auto' }}>
            Searching...
          </span>
        )}
      </div>
    </div>
  );
};
