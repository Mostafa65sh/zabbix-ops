import { useState } from 'react';
import { moduleRegistry } from './modules';
import type { NavigationItem } from './modules';
import './App.css';

function App() {
  const navItems = moduleRegistry.getNavigationItems();
  const [activeTab, setActiveTab] = useState<string>(navItems[0]?.path || '/overview');

  const activeModule = moduleRegistry.getAll().find((m) => m.navItem?.path === activeTab) || moduleRegistry.getAll()[0];

  return (
    <div className="platform-container">
      {/* Platform Header */}
      <header className="platform-header">
        <div className="brand">
          <span className="logo-dot"></span>
          <h1>Zabbix Operations UI</h1>
          <span className="core-badge">Core v0.2.0</span>
        </div>
        <div className="header-status">
          <span className="status-indicator online"></span>
          <span>Core Engine: Ready (Mock Adapter)</span>
        </div>
      </header>

      {/* Main Layout */}
      <div className="platform-body">
        {/* Module Sidebar Navigation */}
        <aside className="platform-sidebar">
          <div className="sidebar-section-title">PLATFORM MODULES ({navItems.length})</div>
          <nav className="module-nav">
            {navItems.map((item: NavigationItem) => (
              <button
                key={item.path}
                type="button"
                className={`nav-btn ${activeTab === item.path ? 'active' : ''}`}
                onClick={() => setActiveTab(item.path)}
              >
                <span className="order-badge">{item.order.toString().padStart(2, '0')}</span>
                <span className="nav-label">{item.label}</span>
              </button>
            ))}
          </nav>
        </aside>

        {/* Module Content Area */}
        <main className="platform-content">
          <div className="module-header-card">
            <div className="title-row">
              <h2>{activeModule?.name}</h2>
              <span className="badge skeleton-badge">Phase 0.2 Skeleton</span>
            </div>
            <p className="module-description">{activeModule?.description}</p>
            <div className="module-meta">
              <span><strong>ID:</strong> {activeModule?.id}</span>
              <span><strong>Version:</strong> {activeModule?.version}</span>
              <span><strong>API Namespace:</strong> /api/v1/{activeModule?.id}</span>
              <span><strong>Permissions:</strong> {activeModule?.permissions?.join(', ')}</span>
            </div>
          </div>

          <div className="module-body-card">
            <div className="skeleton-placeholder">
              <div className="pulse-circle"></div>
              <h3>Module Skeleton Registered</h3>
              <p>
                This module interface is defined in <code>modules/{activeModule?.id}/</code> and is ready for business feature implementation in subsequent phases.
              </p>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}

export default App;
