export interface TimeRange {
  range_code: string;
  start_time: number;
  end_time: number;
}

export interface HealthSummary {
  status: 'HEALTHY' | 'DEGRADED' | 'CRITICAL' | 'UNKNOWN';
  reason: string;
  evidence: string[];
}

export interface HostStatusSummary {
  total: number;
  available: number;
  unavailable: number;
  unknown: number;
  maintenance: number;
}

export interface ProblemSeveritySummary {
  total: number;
  disaster: number;
  high: number;
  average: number;
  warning: number;
  information: number;
}

export interface AvailabilitySummary {
  percent: number | null;
  planned_downtime_seconds: number;
  unplanned_downtime_seconds: number;
  unknown_seconds: number;
  lineage: Record<string, string>;
}

export interface ActiveProblem {
  eventid: string;
  severity: number;
  severity_name: string;
  name: string;
  host_id?: string;
  host_name: string;
  duration_seconds: number;
  duration_human: string;
  acknowledged: boolean;
  started_clock: number;
  started_human: string;
}

export interface TopProblemHost {
  host_id: string;
  host_name: string;
  problem_count: number;
  highest_severity: number;
  highest_severity_name: string;
  oldest_problem_duration_seconds: number;
  availability_status: string;
}

export interface RecentIncidentEvent {
  eventid: string;
  clock: number;
  timestamp_human: string;
  event_type: string;
  severity: number;
  severity_name: string;
  host_name: string;
  description: string;
  acknowledged: boolean;
}

export interface InfrastructureGroup {
  category: string;
  hosts_count: number;
  has_telemetry: boolean;
  telemetry_source: string;
  healthy_count: number;
  problem_count: number;
  status: 'OPERATIONAL' | 'DEGRADED' | 'CRITICAL' | 'MAINTENANCE' | 'NO_DATA';
}

export interface TrendIndicator {
  direction: 'improving' | 'stable' | 'degrading' | 'unknown';
  description: string;
  lineage: string;
}

export interface OverviewData {
  generated_at: string;
  time_range: TimeRange;
  health: HealthSummary;
  hosts: HostStatusSummary;
  problems: ProblemSeveritySummary;
  availability: AvailabilitySummary;
  active_problems: ActiveProblem[];
  top_problem_hosts: TopProblemHost[];
  recent_events: RecentIncidentEvent[];
  infrastructure: InfrastructureGroup[];
  trend: TrendIndicator;
  data_lineage: Record<string, any>;
}

export interface OverviewFilters {
  time_range: string;
  group?: string;
  severity?: number;
  status?: string;
  host?: string;
}
