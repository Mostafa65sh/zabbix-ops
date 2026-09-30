import type { ProblemListResponse, ProblemDetailResponse, ProblemListSummary, ProblemFilters } from './types';

const API_BASE = '/api/v1/problems';

export async function fetchProblemsList(filters: ProblemFilters): Promise<ProblemListResponse> {
  const params = new URLSearchParams();
  if (filters.page !== undefined) params.append('page', String(filters.page));
  if (filters.page_size !== undefined) params.append('page_size', String(filters.page_size));
  if (filters.time_from !== undefined) params.append('time_from', String(filters.time_from));
  if (filters.time_till !== undefined) params.append('time_till', String(filters.time_till));
  if (filters.severities && filters.severities.length > 0) {
    params.append('severities', filters.severities.join(','));
  }
  if (filters.acknowledged !== undefined) params.append('acknowledged', String(filters.acknowledged));
  if (filters.suppressed !== undefined) params.append('suppressed', String(filters.suppressed));
  if (filters.search) params.append('search', filters.search);
  if (filters.group) params.append('group', filters.group);
  if (filters.host) params.append('host', filters.host);
  if (filters.sort) params.append('sort', filters.sort);
  if (filters.sortorder) params.append('sortorder', filters.sortorder);

  const url = `${API_BASE}?${params.toString()}`;
  const response = await fetch(url);
  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Failed to load problems list (${response.status}): ${errorText}`);
  }
  return response.json();
}

export async function fetchProblemsSummary(params: {
  time_from?: number;
  time_till?: number;
  search?: string;
  group?: string;
  host?: string;
}): Promise<ProblemListSummary> {
  const qp = new URLSearchParams();
  if (params.time_from !== undefined) qp.append('time_from', String(params.time_from));
  if (params.time_till !== undefined) qp.append('time_till', String(params.time_till));
  if (params.search) qp.append('search', params.search);
  if (params.group) qp.append('group', params.group);
  if (params.host) qp.append('host', params.host);

  const url = `${API_BASE}/summary?${qp.toString()}`;
  const response = await fetch(url);
  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Failed to load problems summary (${response.status}): ${errorText}`);
  }
  return response.json();
}

export async function fetchProblemDetail(eventId: string): Promise<ProblemDetailResponse> {
  const url = `${API_BASE}/${encodeURIComponent(eventId)}`;
  const response = await fetch(url);
  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Failed to load problem detail (${response.status}): ${errorText}`);
  }
  return response.json();
}
