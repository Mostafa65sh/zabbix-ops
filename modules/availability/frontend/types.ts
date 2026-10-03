export interface LinkedProblem {
  eventid: string;
  severity: number;
  severity_name: string;
  name: string;
  clock: number;
}

export interface ExcludedDowntime {
  name: string;
  period_from: number;
  period_to: number;
  duration_seconds: number;
}

export interface AvailabilityOverview {
  overall_status: 'OK' | 'DEGRADED' | 'CRITICAL' | 'NO_DATA';
  average_sli: number | null;
  average_sli_formatted: string;
  sla_compliance_rate: number | null;
  service_compliance_rate: number | null;
  total_services: number;
  services_ok: number;
  services_problem: number;
  services_no_data: number;
  services_compliant: number;
  services_breached: number;
  total_slas: number;
  slas_compliant: number;
  slas_breached: number;
  total_downtime_seconds: number;
  total_excluded_downtime_seconds: number;
  measured_period: string;
  data_lineage: Record<string, unknown>;
  generated_at: string;
}

export interface ServiceSlaMembership {
  sla_id: string;
  sla_name: string;
  slo_target: number;
  sli_current: number | null;
  sli_formatted: string;
  sla_status: 'COMPLIANT' | 'BREACHED' | 'NO_DATA';
  uptime_seconds: number;
  downtime_seconds: number;
  error_budget_seconds: number | null;
  error_budget_formatted: string;
}

export interface ServiceAvailabilityItem {
  service_id: string;
  name: string;
  status: string;
  status_int: number;
  sla_id: string | null;
  sla_name: string | null;
  slo_target: number | null;
  sli_current: number | null;
  sli_formatted: string;
  sla_status: 'COMPLIANT' | 'BREACHED' | 'NO_DATA' | 'NOT_CONFIGURED';
  uptime_seconds: number;
  downtime_seconds: number;
  error_budget_seconds: number | null;
  error_budget_formatted: string;
  problem_count: number;
  problem_events: LinkedProblem[];
  tags: Array<{ tag: string; value: string }>;
  slas?: ServiceSlaMembership[];
}

export interface ServiceAvailabilityList {
  items: ServiceAvailabilityItem[];
  total_count: number;
  page: number;
  page_size: number;
  total_pages: number;
  summary: {
    total_services: number;
    compliant_count: number;
    breached_count: number;
    unconfigured_count: number;
    bounded_ceiling?: number;
    candidate_limit?: number;
    is_truncated?: boolean;
  };
}

export interface SLADefinitionItem {
  sla_id: string;
  name: string;
  period: string;
  slo_target: number;
  timezone: string;
  status: string;
  service_count: number;
  current_sli: number | null;
  sli_formatted: string;
  compliance_status: string;
  error_budget_seconds: number | null;
  error_budget_human: string;
  excluded_downtimes: ExcludedDowntime[];
}

export interface SLAListResponse {
  items: SLADefinitionItem[];
  total_count: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface AvailabilityTrendPoint {
  period_from: number;
  period_to: number;
  period_label: string;
  sli_percent: number | null;
  sli_formatted: string;
  uptime_seconds: number;
  downtime_seconds: number;
  error_budget_seconds: number | null;
  excluded_downtime_seconds: number;
  is_compliant: boolean | null;
}

export interface AvailabilityTrendResponse {
  sla_id: string;
  sla_name: string;
  slo_target: number;
  service_id: string | null;
  service_name: string | null;
  period_type: string;
  points: AvailabilityTrendPoint[];
  generated_at: string;
}

export interface ServiceFilters {
  page?: number;
  page_size?: number;
  sla_id?: string;
  status?: string;
  search?: string;
  sort_by?: string;
  sort_order?: string;
}
