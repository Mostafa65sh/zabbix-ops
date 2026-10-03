export interface HostSearchResult {
  id: string;
  name: string;
  host: string;
  ip: string;
  status: string;
  groups: string[];
  os?: string | null;
  problems_count: number;
}

export interface ProblemSearchResult {
  eventid: string;
  name: string;
  severity: number;
  clock: number;
  acknowledged: boolean;
  host_name: string;
  host_id: string;
  opdata?: string | null;
}

export interface ServiceSearchResult {
  serviceid: string;
  name: string;
  status: number;
  description?: string | null;
  tags: Array<{ tag: string; value: string }>;
}

export interface ItemSearchResult {
  itemid: string;
  name: string;
  key_: string;
  host_name: string;
  host_id: string;
  lastvalue?: number | string | null;
  units: string;
}

export interface CategoryResult<T> {
  items: T[];
  total_matched: number;
  is_truncated: boolean;
}

export interface SearchCategories {
  hosts: CategoryResult<HostSearchResult>;
  problems: CategoryResult<ProblemSearchResult>;
  services: CategoryResult<ServiceSearchResult>;
  items: CategoryResult<ItemSearchResult>;
}

export interface GlobalSearchResponse {
  query: string;
  timestamp: number;
  categories: SearchCategories;
  total_results: number;
}

export type CategoryFilterKey = 'all' | 'hosts' | 'problems' | 'services' | 'items';
