import React from 'react';
import type { Host360ListItem } from '../types';

interface HostSelectorProps {
  hosts: Host360ListItem[];
  selectedHostId: string;
  onSelectHost: (hostId: string) => void;
  searchTerm: string;
  onSearchChange: (term: string) => void;
  isLoading: boolean;
}

export const HostSelector: React.FC<HostSelectorProps> = ({
  hosts,
  selectedHostId,
  onSelectHost,
  searchTerm,
  onSearchChange,
  isLoading
}) => {
  return (
    <div className="host360-selector-bar" style={{ display: 'flex', gap: '12px', alignItems: 'center', margin: '16px 0' }}>
      <div className="search-box" style={{ flex: '1', maxWidth: '320px', position: 'relative' }}>
        <input
          type="text"
          className="search-input"
          placeholder="Filter host by name, IP, OS..."
          value={searchTerm}
          onChange={(e) => onSearchChange(e.target.value)}
          style={{
            width: '100%',
            padding: '8px 12px',
            background: '#1e293b',
            border: '1px solid #334155',
            borderRadius: '6px',
            color: '#f8fafc',
            fontSize: '13px'
          }}
        />
      </div>

      <div className="host-dropdown-wrapper" style={{ flex: '2', display: 'flex', alignItems: 'center', gap: '8px' }}>
        <label style={{ fontSize: '13px', color: '#94a3b8', whiteSpace: 'nowrap' }}>Target Host:</label>
        <select
          value={selectedHostId}
          onChange={(e) => onSelectHost(e.target.value)}
          disabled={isLoading || hosts.length === 0}
          style={{
            width: '100%',
            maxWidth: '450px',
            padding: '8px 12px',
            background: '#1e293b',
            border: '1px solid #334155',
            borderRadius: '6px',
            color: '#f8fafc',
            fontSize: '13px',
            cursor: 'pointer'
          }}
        >
          {hosts.length === 0 ? (
            <option value="">No matching hosts found</option>
          ) : (
            hosts.map((h) => (
              <option key={h.host_id} value={h.host_id}>
                {h.name} ({h.primary_ip || 'No IP'}) — [{h.status}] {h.active_problems_count > 0 ? `⚠️ ${h.active_problems_count} problems` : '✓ Healthy'}
              </option>
            ))
          )}
        </select>
      </div>
    </div>
  );
};
