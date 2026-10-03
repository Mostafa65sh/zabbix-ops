export interface HostMetricValue {
  value: number | null;
  formatted: string;
  status: 'NORMAL' | 'WARNING' | 'CRITICAL' | 'NO_DATA';
  unit: string;
}

export interface HostHardwareTelemetry {
  cpu_utilization: HostMetricValue;
  cpu_cores?: number | null;
  cpu_load_1m?: number | null;
  cpu_load_5m?: number | null;
  cpu_load_15m?: number | null;
  memory_utilization: HostMetricValue;
  memory_total_bytes?: number | null;
  memory_used_bytes?: number | null;
  memory_free_bytes?: number | null;
  storage_utilization: HostMetricValue;
  storage_total_bytes?: number | null;
  storage_used_bytes?: number | null;
  network_rx_rate?: string | null;
  network_tx_rate?: string | null;
}

export interface HostInterface {
  interfaceid: string;
  ip: string;
  dns: string;
  port: string;
  type: string;
  is_main: boolean;
  availability: 'AVAILABLE' | 'UNAVAILABLE' | 'UNKNOWN';
  error?: string | null;
}

export interface HostProblemEvent {
  eventid: string;
  name: string;
  severity: number;
  severity_name: string;
  clock: number;
  acknowledged: boolean;
  opdata?: string | null;
}

export interface Host360ListItem {
  host_id: string;
  name: string;
  technical_name: string;
  status: string;
  availability: 'AVAILABLE' | 'UNAVAILABLE' | 'UNKNOWN';
  primary_ip: string;
  groups: string[];
  datacenter?: string | null;
  rack?: string | null;
  os?: string | null;
  active_problems_count: number;
  cpu_util?: number | null;
  memory_util?: number | null;
  storage_util?: number | null;
  interfaces: HostInterface[];
}

export interface Host360ListResponse {
  items: Host360ListItem[];
  total_count: number;
  page: number;
  page_size: number;
  total_pages: number;
  generated_at: string;
}

export interface Host360Detail {
  host_id: string;
  name: string;
  technical_name: string;
  status: string;
  overall_availability: 'AVAILABLE' | 'UNAVAILABLE' | 'UNKNOWN';
  groups: string[];
  interfaces: HostInterface[];
  telemetry: HostHardwareTelemetry;
  inventory: Record<string, any>;
  tags: Array<{ tag: string; value: string }>;
  active_problems: HostProblemEvent[];
  maintenance?: { active: boolean; name: string } | null;
  data_lineage: Record<string, any>;
  generated_at: string;
}

export interface TelemetrySeriesPoint {
  clock: number;
  timestamp_iso: string;
  value: number | null;
}

export interface Host360TelemetryResponse {
  host_id: string;
  host_name: string;
  time_range: string;
  time_from: number;
  time_till: number;
  series: {
    cpu: TelemetrySeriesPoint[];
    memory: TelemetrySeriesPoint[];
    storage: TelemetrySeriesPoint[];
  };
  generated_at: string;
}
