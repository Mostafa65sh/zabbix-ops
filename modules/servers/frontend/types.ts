export interface ServerMetricValue {
  value: number | null;
  formatted: string;
  status: 'NORMAL' | 'WARNING' | 'CRITICAL' | 'NO_DATA';
  unit: string;
}

export interface ServerHardware {
  cpu_utilization: ServerMetricValue;
  cpu_cores?: number | null;
  cpu_load?: number | null;
  memory_utilization: ServerMetricValue;
  memory_total_bytes?: number | null;
  memory_used_bytes?: number | null;
  storage_utilization: ServerMetricValue;
  storage_total_bytes?: number | null;
  storage_used_bytes?: number | null;
}

export interface ServerNetworkInterface {
  interfaceid: string;
  ip: string;
  dns: string;
  port: string;
  type: 'AGENT' | 'SNMP' | 'IPMI' | 'JMX';
  is_main: boolean;
  availability: 'AVAILABLE' | 'UNAVAILABLE' | 'UNKNOWN';
  error?: string | null;
  traffic_in?: string | null;
  traffic_out?: string | null;
}

export interface ServerProblemSummary {
  total: number;
  disaster: number;
  high: number;
  average: number;
  warning: number;
  information: number;
  highest_severity?: number | null;
}

export interface ServerItem {
  id: string;
  name: string;
  technical_name: string;
  status: 'UP' | 'DOWN' | 'MAINTENANCE' | 'UNKNOWN';
  overall_availability: 'AVAILABLE' | 'UNAVAILABLE' | 'UNKNOWN';
  ip: string;
  os: string;
  os_type: 'linux' | 'windows' | 'network' | 'other' | 'unknown';
  hardware_summary: string;
  hardware: ServerHardware;
  interfaces: ServerNetworkInterface[];
  groups: string[];
  tags: Array<{ tag: string; value: string }>;
  datacenter?: string | null;
  rack?: string | null;
  environment?: string | null;
  maintenance_name?: string | null;
  problems: ServerProblemSummary;
  last_updated: string;
  data_lineage: Record<string, string>;
}

export interface ServerListSummary {
  total_servers: number;
  servers_up: number;
  servers_down: number;
  servers_maintenance: number;
  available_count: number;
  unavailable_count: number;
  unknown_count: number;
  avg_cpu_percent: number | null;
  avg_memory_percent: number | null;
  avg_storage_percent: number | null;
}

export interface ServerFilters {
  search?: string;
  group?: string;
  status?: string;
  availability?: string;
  os_type?: string;
  datacenter?: string;
  has_problems?: boolean;
  severity?: number;
  page?: number;
  page_size?: number;
  sort_by?: string;
  sort_order?: 'asc' | 'desc';
}

export interface ServerListResponse {
  items: ServerItem[];
  total_count: number;
  page: number;
  page_size: number;
  total_pages: number;
  summary: ServerListSummary;
  applied_filters: Record<string, any>;
  generated_at: string;
}

export interface ServerDetailResponse {
  server: ServerItem;
  inventory: Record<string, any>;
  active_problems: Array<{
    eventid: string;
    name: string;
    severity: number;
    clock: number;
    acknowledged: boolean;
  }>;
  metrics_breakdown: Record<string, any>;
  generated_at: string;
}
