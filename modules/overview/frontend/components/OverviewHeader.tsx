import React from 'react';

interface OverviewHeaderProps {
  lastUpdated: string;
  isRefreshing: boolean;
  onRefresh: () => void;
  theme: 'dark' | 'light';
  onToggleTheme: () => void;
}

export const OverviewHeader: React.FC<OverviewHeaderProps> = ({
  lastUpdated,
  isRefreshing,
  onRefresh,
  theme,
  onToggleTheme,
}) => {
  return (
    <header className="overview-header">
      <div className="header-left">
        <div className="brand-badge">
          <span className="brand-dot"></span>
          <span className="brand-title">Zabbix Operations UI</span>
          <span className="module-title-separator">/</span>
          <span className="module-title">Overview</span>
        </div>
        <div className="env-pill">
          <span className="env-dot"></span>
          <span className="env-name">LOCAL DEV (MOCK ADAPTER)</span>
        </div>
      </div>

      <div className="header-right">
        <div className="last-updated-text">
          <span>Last updated:</span>
          <strong>{lastUpdated || 'Loading...'}</strong>
        </div>

        <button
          type="button"
          className={`refresh-btn ${isRefreshing ? 'spinning' : ''}`}
          onClick={onRefresh}
          disabled={isRefreshing}
          title="Manual Refresh"
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2">
            <path d="M21.5 2v6h-6M21.34 15.57a10 10 0 1 1-.57-8.38l5.67-5.19"/>
          </svg>
          <span>{isRefreshing ? 'Refreshing...' : 'Refresh'}</span>
        </button>

        <button
          type="button"
          className="theme-toggle-btn"
          onClick={onToggleTheme}
          title={`Switch to ${theme === 'dark' ? 'Light' : 'Dark'} Mode`}
        >
          {theme === 'dark' ? (
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="5"/>
              <path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/>
            </svg>
          ) : (
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>
            </svg>
          )}
          <span>{theme === 'dark' ? 'Light' : 'Dark'}</span>
        </button>

        <div className="user-profile-badge" title="Authenticated User">
          <span className="user-avatar">AD</span>
          <span className="user-name">admin (Core)</span>
        </div>
      </div>
    </header>
  );
};
