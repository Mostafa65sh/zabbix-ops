import React from 'react';
import type { ItemSearchResult, CategoryResult } from '../types';

interface ItemResultsCardProps {
  data: CategoryResult<ItemSearchResult>;
}

export const ItemResultsCard: React.FC<ItemResultsCardProps> = ({ data }) => {
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
          <span style={{ fontWeight: 600, color: '#f8fafc', fontSize: '1rem' }}>Metrics & Items</span>
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
              <th style={{ padding: '0.65rem 1.25rem' }}>Metric Name</th>
              <th style={{ padding: '0.65rem 1.25rem' }}>Item Key</th>
              <th style={{ padding: '0.65rem 1.25rem' }}>Host</th>
              <th style={{ padding: '0.65rem 1.25rem' }}>Latest Value</th>
            </tr>
          </thead>
          <tbody>
            {data.items.map((it) => {
              const hasVal = it.lastvalue !== null && it.lastvalue !== undefined;
              return (
                <tr
                  key={it.itemid}
                  style={{
                    borderBottom: '1px solid #2d3748',
                  }}
                >
                  <td style={{ padding: '0.75rem 1.25rem', fontWeight: 600, color: '#f8fafc' }}>
                    {it.name}
                  </td>
                  <td style={{ padding: '0.75rem 1.25rem', color: '#38bdf8', fontFamily: 'monospace', fontSize: '0.8rem' }}>
                    {it.key_}
                  </td>
                  <td style={{ padding: '0.75rem 1.25rem', color: '#cbd5e1' }}>
                    {it.host_name}
                  </td>
                  <td style={{ padding: '0.75rem 1.25rem' }}>
                    {hasVal ? (
                      <span style={{ color: '#f8fafc', fontWeight: 600 }}>
                        {typeof it.lastvalue === 'number' ? it.lastvalue.toFixed(1) : it.lastvalue} {it.units}
                      </span>
                    ) : (
                      <span
                        style={{
                          backgroundColor: 'rgba(100, 116, 139, 0.2)',
                          color: '#94a3b8',
                          padding: '0.15rem 0.45rem',
                          borderRadius: '4px',
                          fontSize: '0.75rem',
                          fontFamily: 'monospace',
                        }}
                      >
                        NO_DATA
                      </span>
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
