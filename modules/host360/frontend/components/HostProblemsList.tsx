import React from 'react';
import type { HostProblemEvent } from '../types';

interface HostProblemsListProps {
  problems: HostProblemEvent[];
}

export const HostProblemsList: React.FC<HostProblemsListProps> = ({ problems }) => {
  const getSeverityStyle = (sev: number) => {
    switch (sev) {
      case 5:
        return { bg: 'rgba(239, 68, 68, 0.2)', color: '#ef4444', label: 'Disaster' };
      case 4:
        return { bg: 'rgba(249, 115, 22, 0.2)', color: '#f97316', label: 'High' };
      case 3:
        return { bg: 'rgba(245, 158, 11, 0.2)', color: '#f59e0b', label: 'Average' };
      case 2:
        return { bg: 'rgba(59, 130, 246, 0.2)', color: '#3b82f6', label: 'Warning' };
      case 1:
        return { bg: 'rgba(100, 116, 139, 0.2)', color: '#94a3b8', label: 'Information' };
      default:
        return { bg: 'rgba(100, 116, 139, 0.2)', color: '#94a3b8', label: 'Not Classified' };
    }
  };

  return (
    <div
      className="problems-card"
      style={{
        background: '#1e293b',
        border: '1px solid #334155',
        borderRadius: '8px',
        padding: '16px'
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
        <h3 style={{ fontSize: '14px', fontWeight: 600, color: '#f8fafc', margin: 0 }}>
          Active Problems & Event Overlays ({problems.length})
        </h3>
        {problems.length === 0 ? (
          <span style={{ fontSize: '12px', color: '#10b981', fontWeight: 600 }}>✓ All Services Healthy</span>
        ) : (
          <span style={{ fontSize: '12px', color: '#ef4444', fontWeight: 600 }}>⚠️ Active Incidents</span>
        )}
      </div>

      {problems.length === 0 ? (
        <div style={{ color: '#64748b', fontSize: '13px', padding: '12px 0' }}>
          No unresolved problem events recorded for this host.
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          {problems.map((prob) => {
            const sevInfo = getSeverityStyle(prob.severity);
            const dateStr = new Date(prob.clock * 1000).toLocaleString();

            return (
              <div
                key={prob.eventid}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  padding: '10px 12px',
                  background: '#0f172a',
                  border: '1px solid #334155',
                  borderRadius: '6px'
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <span
                    style={{
                      padding: '2px 8px',
                      borderRadius: '4px',
                      fontSize: '11px',
                      fontWeight: 700,
                      background: sevInfo.bg,
                      color: sevInfo.color
                    }}
                  >
                    {sevInfo.label.toUpperCase()}
                  </span>
                  <div>
                    <div style={{ fontSize: '13px', fontWeight: 500, color: '#f8fafc' }}>{prob.name}</div>
                    <div style={{ fontSize: '11px', color: '#64748b' }}>
                      Event ID: {prob.eventid} • {dateStr}
                    </div>
                  </div>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  {prob.acknowledged ? (
                    <span style={{ fontSize: '11px', color: '#10b981', fontWeight: 600 }}>ACK</span>
                  ) : (
                    <span style={{ fontSize: '11px', color: '#f59e0b', fontWeight: 600 }}>UNACK</span>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
