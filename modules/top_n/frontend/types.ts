export interface TopNMetricValue {
  value: number | null;
  formatted: string;
  status: 'NORMAL' | 'WARNING' | 'CRITICAL' | 'NO_DATA';
  unit: string;
}

export interface TopNItem {
  rank: number;
  host_id: string;
  host_name: string;
  technical_name: string;
  primary_ip: string;
  status: string;
  availability: 'AVAILABLE' | 'UNAVAILABLE' | 'UNKNOWN';
  groups: string[];
  metric_name: string;
  metric_value: TopNMetricValue;
  raw_value: number | null;
  active_problems_count: number;
  highest_severity: number | null;
  tags: Array<{ tag: string; value: string }>;
}

export interface TopNResponse {
  metric: string;
  metric_display_name: string;
  order: 'desc' | 'asc';
  items: TopNItem[];
  total_evaluated_hosts: number;
  is_truncated: boolean;
  truncation_reason?: string | null;
  generated_at: string;
}

export interface TopNOverviewResponse {
  cpu: TopNItem[];
  memory: TopNItem[];
  storage: TopNItem[];
  problems: TopNItem[];
  total_evaluated_hosts: number;
  is_truncated: boolean;
  truncation_reason?: string | null;
  generated_at: string;
}
