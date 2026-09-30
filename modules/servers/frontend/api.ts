import type { ServerListResponse, ServerDetailResponse, ServerFilters } from './types';

const API_BASE = '/api/v1/servers';

export async function fetchServersList(filters: ServerFilters): Promise<ServerListResponse> {
  const params = new URLSearchParams();
  if (filters.search) params.append('search', filters.search);
  if (filters.group) params.append('group', filters.group);
  if (filters.status) params.append('status', filters.status);
  if (filters.availability) params.append('availability', filters.availability);
  if (filters.os_type) params.append('os_type', filters.os_type);
  if (filters.datacenter) params.append('datacenter', filters.datacenter);
  if (filters.has_problems !== undefined) params.append('has_problems', String(filters.has_problems));
  if (filters.severity !== undefined) params.append('severity', String(filters.severity));
  if (filters.page !== undefined) params.append('page', String(filters.page));
  if (filters.page_size !== undefined) params.append('page_size', String(filters.page_size));
  if (filters.sort_by) params.append('sort_by', filters.sort_by);
  if (filters.sort_order) params.append('sort_order', filters.sort_order);

  const url = `${API_BASE}?${params.toString()}`;
  const response = await fetch(url);
  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Failed to load servers list (${response.status}): ${errorText}`);
  }
  return response.json();
}

export async function fetchServerDetail(serverId: string): Promise<ServerDetailResponse> {
  const url = `${API_BASE}/${encodeURIComponent(serverId)}`;
  const response = await fetch(url);
  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Failed to load server details (${response.status}): ${errorText}`);
  }
  return response.json();
}
