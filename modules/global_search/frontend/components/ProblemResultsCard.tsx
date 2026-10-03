import React from 'react';
import type { ProblemSearchResult, CategoryResult } from '../types';

interface ProblemResultsCardProps {
  data: CategoryResult<ProblemSearchResult>;
}

const SEVERITY_MAP: Record<number, { label: string; bg: string; color: string }> = {
  5: { label: 'Disaster', bg: 'rgba(239, 68, 68, 0.25)', color: '#ef4444' },
  4: { label: 'High', bg: 'rgba(249, 115, 22, 0.25)', color: '#f97316' },
  3: { label: 'Average', bg: 'rgba(245, 158, 11, 0.25)', color: '#f59e0b' },
  2: { label: 'Warning', bg: 'rgba(234, 179, 8, 0.25)', color: '#eab308' },
  1: { label: 'Information', bg: 'rgba(59, 130, 246, 0.25)', color: '#3b82f6' },
  0: { label: 'Not Classified', bg: 'rgba(100, 116, 139, 0.25)', color: '#94a3b8' },
};

export const ProblemResultsCard: React.FC<ProblemResultsCardProps> = ({ data }) => {
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
          <span style={{ fontWeight: 600, color: '#f8fafc', fontSize: '1rem' }}>Active Problems</span>
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
              <th style={{ padding: '0.65rem 1.25rem' }}>Severity</th>
              <th style={{ padding: '0.65rem 1.25rem' }}>Problem Description</th>
              <th style={{ padding: '0.65rem 1.25rem' }}>Host</th>
              <th style={{ padding: '0.65rem 1.25rem' }}>Ack</th>
              <th style={{ padding: '0.65rem 1.25rem' }}>Triggered Time</th>
            </tr>
          </thead>
          <tbody>
            {data.items.map((p) => {
              const sev = SEVERITY_MAP[p.severity] || SEVERITY_MAP[0];
              const dateStr = p.clock ? new Date(p.clock * 1000).toLocaleString() : '—';
              return (
                <tr
                  key={p.eventid}
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
                        backgroundColor: sev.bg,
                        color: sev.color,
                      }}
                    >
                      {sev.label}
                    </span>
                  </td>
                  <td style={{ padding: '0.75rem 1.25rem', color: '#f8fafc', fontWeight: 500 }}>
                    {p.name}
                    {p.opdata && (
                      <span style={{ display: 'block', fontSize: '0.75rem', color: '#94a3b8', marginTop: '0.2rem' }}>
                        Operational Data: {p.opdata}
                      </span>
                    )}
                  </td>
                  <td style={{ padding: '0.75rem 1.25rem', color: '#cbd5e1' }}>
                    {p.host_name || '—'}
                  </td>
                  <td style={{ padding: '0.75rem 1.25rem' }}>
                    {p.acknowledged ? (
                      <span style={{ color: '#4ade80', fontSize: '0.75rem' }}>Yes</span>
                    ) : (
                      <span style={{ color: '#94a3b8', fontSize: '0.75rem' }}>No</span>
                    )}
                  </td>
                  <td style={{ padding: '0.75rem 1.25rem', color: '#94a3b8', fontSize: '0.8rem' }}>
                    {dateStr}
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
