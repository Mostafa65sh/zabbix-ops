export interface GraphPoint {
  clock: number;
  timestamp_iso: string;
  value: number | null;
}

export interface GraphMetricSeries {
  series_id: string;
  host_id: string;
  host_name: string;
  metric_name: string;
  metric_label: string;
  unit: string;
  color?: string | null;
  points: GraphPoint[];
  latest_value?: number | null;
  min_value?: number | null;
  max_value?: number | null;
  avg_value?: number | null;
}

export interface MultiSeriesGraphResponse {
  time_range: string;
  time_from: number;
  time_till: number;
  series: GraphMetricSeries[];
  total_series: number;
  is_truncated: boolean;
  truncation_reason?: string | null;
  generated_at: string;
}

export interface GraphTarget {
  host_id: string;
  host_name: string;
  technical_name: string;
  primary_ip: string;
  status: string;
  groups: string[];
  available_metrics: string[];
}

export interface GraphTargetsResponse {
  targets: GraphTarget[];
  total_targets: number;
  is_truncated: boolean;
  truncation_reason?: string | null;
  generated_at: string;
}
