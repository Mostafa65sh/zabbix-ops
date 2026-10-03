import React from 'react';
import type { HostInterface } from '../types';

interface HostInterfacesTableProps {
  interfaces: HostInterface[];
}

export const HostInterfacesTable: React.FC<HostInterfacesTableProps> = ({ interfaces }) => {
  return (
    <div
      className="interfaces-card"
      style={{
        background: '#1e293b',
        border: '1px solid #334155',
        borderRadius: '8px',
        padding: '16px',
        marginBottom: '24px'
      }}
    >
      <h3 style={{ fontSize: '14px', fontWeight: 600, color: '#f8fafc', marginBottom: '12px' }}>
        Network Interfaces ({interfaces.length})
      </h3>

      {interfaces.length === 0 ? (
        <div style={{ color: '#64748b', fontSize: '13px' }}>No configured interfaces found.</div>
      ) : (
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '13px' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid #334155', color: '#94a3b8' }}>
                <th style={{ padding: '8px' }}>Type</th>
                <th style={{ padding: '8px' }}>IP Address</th>
                <th style={{ padding: '8px' }}>DNS</th>
                <th style={{ padding: '8px' }}>Port</th>
                <th style={{ padding: '8px' }}>Role</th>
                <th style={{ padding: '8px' }}>Availability</th>
              </tr>
            </thead>
            <tbody>
              {interfaces.map((iface) => (
                <tr key={iface.interfaceid} style={{ borderBottom: '1px solid #1e293b' }}>
                  <td style={{ padding: '8px' }}>
                    <span
                      style={{
                        padding: '2px 6px',
                        borderRadius: '4px',
                        fontSize: '11px',
                        fontWeight: 600,
                        background: '#334155',
                        color: '#cbd5e1'
                      }}
                    >
                      {iface.type}
                    </span>
                  </td>
                  <td style={{ padding: '8px', color: '#f8fafc', fontWeight: 500 }}>{iface.ip || '—'}</td>
                  <td style={{ padding: '8px', color: '#94a3b8' }}>{iface.dns || '—'}</td>
                  <td style={{ padding: '8px', color: '#94a3b8' }}>{iface.port}</td>
                  <td style={{ padding: '8px' }}>
                    {iface.is_main ? (
                      <span style={{ color: '#38bdf8', fontSize: '11px', fontWeight: 600 }}>PRIMARY</span>
                    ) : (
                      <span style={{ color: '#64748b', fontSize: '11px' }}>SECONDARY</span>
                    )}
                  </td>
                  <td style={{ padding: '8px' }}>
                    <span
                      style={{
                        padding: '2px 8px',
                        borderRadius: '12px',
                        fontSize: '11px',
                        fontWeight: 600,
                        background:
                          iface.availability === 'AVAILABLE'
                            ? 'rgba(16, 185, 129, 0.15)'
                            : iface.availability === 'UNAVAILABLE'
                            ? 'rgba(239, 68, 68, 0.15)'
                            : 'rgba(100, 116, 139, 0.15)',
                        color:
                          iface.availability === 'AVAILABLE'
                            ? '#10b981'
                            : iface.availability === 'UNAVAILABLE'
                            ? '#ef4444'
                            : '#94a3b8'
                      }}
                    >
                      {iface.availability}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};
