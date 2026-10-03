import React from 'react';
import type { GraphTarget } from '../types';

interface TargetSelectorProps {
  targets: GraphTarget[];
  selectedHostIds: string[];
  onToggleHost: (hostId: string) => void;
  selectedMetrics: string[];
  onToggleMetric: (metric: string) => void;
  searchTerm: string;
  onSearchChange: (term: string) => void;
  isLoading: boolean;
}

export const TargetSelector: React.FC<TargetSelectorProps> = ({
  targets,
  selectedHostIds,
  onToggleHost,
  selectedMetrics,
  onToggleMetric,
  searchTerm,
  onSearchChange,
  isLoading
}) => {
  return (
    <div
      className="target-selector-card"
      style={{
        background: '#1e293b',
        border: '1px solid #334155',
        borderRadius: '8px',
        padding: '16px',
        marginBottom: '20px'
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px', flexWrap: 'wrap', gap: '12px' }}>
        {/* Metric checkboxes */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <span style={{ fontSize: '13px', fontWeight: 600, color: '#94a3b8' }}>Metrics:</span>
          {(['cpu', 'memory', 'storage'] as const).map((m) => {
            const isChecked = selectedMetrics.includes(m);
            return (
              <label key={m} style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '13px', color: '#f8fafc', cursor: 'pointer' }}>
                <input
                  type="checkbox"
                  checked={isChecked}
                  onChange={() => onToggleMetric(m)}
                  style={{ cursor: 'pointer' }}
                />
                <span style={{ textTransform: 'uppercase', fontWeight: 600 }}>{m}</span>
              </label>
            );
          })}
        </div>

        {/* Search input for hosts */}
        <div style={{ maxWidth: '280px', width: '100%' }}>
          <input
            type="text"
            placeholder="Search host by name or IP..."
            value={searchTerm}
            onChange={(e) => onSearchChange(e.target.value)}
            style={{
              width: '100%',
              padding: '6px 10px',
              fontSize: '12px',
              background: '#0f172a',
              border: '1px solid #334155',
              borderRadius: '4px',
              color: '#f8fafc'
            }}
          />
        </div>
      </div>

      {/* Host pills selection */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
        <span style={{ fontSize: '12px', color: '#94a3b8', whiteSpace: 'nowrap' }}>
          Select Hosts (max 10):
        </span>
        {isLoading ? (
          <span style={{ fontSize: '12px', color: '#64748b' }}>Loading candidate targets...</span>
        ) : targets.length === 0 ? (
          <span style={{ fontSize: '12px', color: '#64748b' }}>No matching hosts found</span>
        ) : (
          targets.map((tgt) => {
            const isSelected = selectedHostIds.includes(tgt.host_id);
            return (
              <button
                key={tgt.host_id}
                type="button"
                onClick={() => onToggleHost(tgt.host_id)}
                style={{
                  padding: '4px 10px',
                  borderRadius: '16px',
                  fontSize: '12px',
                  fontWeight: 500,
                  border: isSelected ? '1px solid #38bdf8' : '1px solid #334155',
                  background: isSelected ? 'rgba(56, 189, 248, 0.15)' : '#0f172a',
                  color: isSelected ? '#38bdf8' : '#cbd5e1',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px'
                }}
              >
                <span>{tgt.host_name}</span>
                {isSelected && <span style={{ fontSize: '10px' }}>✕</span>}
              </button>
            );
          })
        )}
      </div>
    </div>
  );
};
