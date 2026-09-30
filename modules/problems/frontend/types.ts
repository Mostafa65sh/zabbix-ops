export interface ProblemHost {
  hostid: string;
  host: string;
  name: string;
}

export interface ProblemTag {
  tag: string;
  value: string;
}

export interface ProblemAcknowledge {
  acknowledgeid: string;
  userid: string;
  clock: number;
  time: string;
  message: string;
  action: string;
}

export interface ProblemAlert {
  alertid: string;
  mediatypeid: string;
  clock: number;
  time: string;
  sendto: string;
  status: string;
  error: string;
}

export interface ProblemItem {
  eventid: string;
  severity: number;
  severity_name: string;
  name: string;
  clock: number;
  start_time: string;
  duration_seconds: number;
  duration_human: string;
  acknowledged: boolean;
  suppressed: boolean;
  suppression_data: Array<Record<string, any>>;
  opdata: string;
  cause_eventid?: string | null;
  is_cause: boolean;
  is_symptom: boolean;
  hosts: ProblemHost[];
  host_groups: string[];
  tags: ProblemTag[];
  acknowledges: ProblemAcknowledge[];
}

export interface ProblemDetailResponse extends ProblemItem {
  alerts: ProblemAlert[];
}

export interface ProblemSeveritySummary {
  disaster: number;
  high: number;
  average: number;
  warning: number;
  information: number;
  unclassified: number;
}

export interface ProblemListSummary {
  total_problems: number;
  by_severity: ProblemSeveritySummary;
  acknowledged_count: number;
  unacknowledged_count: number;
  suppressed_count: number;
  mtta_seconds: number | null;
  mtta_human: string;
  generated_at: string;
}

export type TimeRangePreset = '15m' | '1h' | '6h' | '24h' | '7d' | '30d' | 'all';

export interface ProblemFilters {
  page?: number;
  page_size?: number;
  time_from?: number;
  time_till?: number;
  time_preset?: TimeRangePreset;
  severities?: number[];
  acknowledged?: boolean;
  suppressed?: boolean;
  search?: string;
  group?: string;
  host?: string;
  sort?: string;
  sortorder?: 'ASC' | 'DESC';
}

export interface ProblemListResponse {
  items: ProblemItem[];
  total_count: number;
  page: number;
  page_size: number;
  total_pages: number;
  summary: ProblemListSummary;
}
