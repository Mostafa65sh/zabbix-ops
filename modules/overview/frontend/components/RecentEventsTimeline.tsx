import React from 'react';
import type { RecentIncidentEvent } from '../types';

interface RecentEventsTimelineProps {
  events: RecentIncidentEvent[];
}

export const RecentEventsTimeline: React.FC<RecentEventsTimelineProps> = ({ events }) => {
  return (
    <div className="operational-panel">
      <div className="panel-header">
        <div className="panel-title-area">
          <span className="panel-title">RECENT OPERATIONAL EVENTS</span>
          <span className="panel-count-badge">Chronological Audit</span>
        </div>
      </div>

      <div className="events-timeline">
        {events.length === 0 ? (
          <div className="table-empty-row">
            <span>No recent operational events</span>
          </div>
        ) : (
          events.map((ev) => (
            <div key={ev.eventid} className={`event-item ${ev.event_type.toLowerCase()}`}>
              <div className="event-time-col">
                <span className="event-time">{ev.timestamp_human}</span>
              </div>

              <div className="event-type-badge-col">
                <span
                  className={`event-type-badge ${
                    ev.event_type === 'PROBLEM_STARTED' ? 'type-problem' : 'type-recovery'
                  }`}
                >
                  {ev.event_type === 'PROBLEM_STARTED' ? 'PROBLEM STARTED' : 'RECOVERED'}
                </span>
              </div>

              <div className="event-details-col">
                <strong className="event-host">{ev.host_name}</strong>
                <span className="event-desc">{ev.description}</span>
              </div>

              <div className="event-sev-col">
                <span className={`sev-tag sev-${ev.severity}`}>
                  {ev.severity_name}
                </span>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};
