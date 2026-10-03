import React from 'react';
import type { HostSearchResult, CategoryResult } from '../types';

interface HostResultsCardProps {
  data: CategoryResult<HostSearchResult>;
}

export const HostResultsCard: React.FC<HostResultsCardProps> = ({ data }) => {
  if (data.items.length === 0) return null;

  return (
    <div
      style={{
        backgroundColor: '#1e293b',
        borderRadius: '8px',
        border: '1px solid #334155',
        marginBottom: '1.5rem',
        overflow: 'hidden',
      }}
    >
      <div
        style={{
          padding: '0.85rem 1.25rem',
          borderBottom: '1px solid #334155',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          backgroundColor: '#0f172a',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <span style={{ fontWeight: 600, color: '#f8fafc', fontSize: '1rem' }}>Hosts</span>
          <span
            style={{
              backgroundColor: '#334155',
              color: '#94a3b8',
              fontSize: '0.75rem',
              padding: '0.1rem 0.5rem',
              borderRadius: '999px',
            }}
          >
            {data.total_matched} found
          </span>
        </div>
        {data.is_truncated && (
          <span style={{ color: '#f59e0b', fontSize: '0.8rem' }}>
            Showing first {data.items.length} of {data.total_matched} (truncated)
          </span>
        )}
      </div>

      <div style={{ overflowX: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.875rem' }}>
          <thead>
            <tr style={{ borderBottom: '1px solid #334155', color: '#94a3b8' }}>
              <th style={{ padding: '0.65rem 1.25rem' }}>Status</th>
              <th style={{ padding: '0.65rem 1.25rem' }}>Host Name</th>
              <th style={{ padding: '0.65rem 1.25rem' }}>IP Address</th>
              <th style={{ padding: '0.65rem 1.25rem' }}>Groups</th>
              <th style={{ padding: '0.65rem 1.25rem' }}>Operating System</th>
              <th style={{ padding: '0.65rem 1.25rem' }}>Active Problems</th>
            </tr>
          </thead>
          <tbody>
            {data.items.map((h) => {
              const isUp = h.status === 'UP';
              const isDown = h.status === 'DOWN';
              return (
                <tr
                  key={h.id}
                  style={{
                    borderBottom: '1px solid #2d3748',
                    transition: 'background-color 0.15s ease',
                  }}
                >
                  <td style={{ padding: '0.75rem 1.25rem' }}>
                    <span
                      style={{
                        padding: '0.2rem 0.5rem',
                        borderRadius: '4px',
                        fontSize: '0.75rem',
                        fontWeight: 600,
                        backgroundColor: isUp ? 'rgba(34, 197, 94, 0.15)' : isDown ? 'rgba(239, 68, 68, 0.15)' : 'rgba(245, 158, 11, 0.15)',
                        color: isUp ? '#4ade80' : isDown ? '#f87171' : '#fbbf24',
                      }}
                    >
                      {h.status}
                    </span>
                  </td>
                  <td style={{ padding: '0.75rem 1.25rem', fontWeight: 600, color: '#f8fafc' }}>
                    {h.name}
                    {h.host && h.host !== h.name && (
                      <span style={{ display: 'block', fontSize: '0.75rem', color: '#64748b', fontWeight: 400 }}>
                        {h.host}
                      </span>
                    )}
                  </td>
                  <td style={{ padding: '0.75rem 1.25rem', color: '#cbd5e1', fontFamily: 'monospace' }}>
                    {h.ip || '—'}
                  </td>
                  <td style={{ padding: '0.75rem 1.25rem', color: '#94a3b8' }}>
                    {h.groups.join(', ') || '—'}
                  </td>
                  <td style={{ padding: '0.75rem 1.25rem', color: '#94a3b8', fontSize: '0.8rem' }}>
                    {h.os || '—'}
                  </td>
                  <td style={{ padding: '0.75rem 1.25rem' }}>
                    {h.problems_count > 0 ? (
                      <span
                        style={{
                          backgroundColor: 'rgba(239, 68, 68, 0.2)',
                          color: '#f87171',
                          padding: '0.2rem 0.5rem',
                          borderRadius: '4px',
                          fontSize: '0.75rem',
                          fontWeight: 600,
                        }}
                      >
                        {h.problems_count} open
                      </span>
                    ) : (
                      <span style={{ color: '#4ade80', fontSize: '0.75rem' }}>Clean</span>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};
