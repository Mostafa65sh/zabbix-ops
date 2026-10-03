import React from 'react';
import type { ServiceSearchResult, CategoryResult } from '../types';

interface ServiceResultsCardProps {
  data: CategoryResult<ServiceSearchResult>;
}

export const ServiceResultsCard: React.FC<ServiceResultsCardProps> = ({ data }) => {
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
          <span style={{ fontWeight: 600, color: '#f8fafc', fontSize: '1rem' }}>Business Services</span>
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
              <th style={{ padding: '0.65rem 1.25rem' }}>Service Name</th>
              <th style={{ padding: '0.65rem 1.25rem' }}>Description</th>
              <th style={{ padding: '0.65rem 1.25rem' }}>Tags</th>
            </tr>
          </thead>
          <tbody>
            {data.items.map((s) => {
              const isOk = s.status === 0;
              return (
                <tr
                  key={s.serviceid}
                  style={{
                    borderBottom: '1px solid #2d3748',
                  }}
                >
                  <td style={{ padding: '0.75rem 1.25rem' }}>
                    <span
                      style={{
                        padding: '0.2rem 0.5rem',
                        borderRadius: '4px',
                        fontSize: '0.75rem',
                        fontWeight: 600,
                        backgroundColor: isOk ? 'rgba(34, 197, 94, 0.15)' : 'rgba(239, 68, 68, 0.15)',
                        color: isOk ? '#4ade80' : '#f87171',
                      }}
                    >
                      {isOk ? 'Operational' : `Degraded (${s.status})`}
                    </span>
                  </td>
                  <td style={{ padding: '0.75rem 1.25rem', fontWeight: 600, color: '#f8fafc' }}>
                    {s.name}
                  </td>
                  <td style={{ padding: '0.75rem 1.25rem', color: '#94a3b8' }}>
                    {s.description || '—'}
                  </td>
                  <td style={{ padding: '0.75rem 1.25rem' }}>
                    <div style={{ display: 'flex', gap: '0.25rem', flexWrap: 'wrap' }}>
                      {s.tags.map((t, idx) => (
                        <span
                          key={idx}
                          style={{
                            backgroundColor: '#334155',
                            color: '#cbd5e1',
                            padding: '0.1rem 0.4rem',
                            borderRadius: '4px',
                            fontSize: '0.75rem',
                          }}
                        >
                          {t.tag}: {t.value}
                        </span>
                      ))}
                    </div>
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
