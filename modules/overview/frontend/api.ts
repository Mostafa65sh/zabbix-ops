import type { OverviewData, OverviewFilters } from './types';

const API_BASE = '/api/v1/overview';

export async function fetchOverviewData(filters: OverviewFilters): Promise<OverviewData> {
  const params = new URLSearchParams();
  if (filters.time_range) params.append('time_range', filters.time_range);
  if (filters.group) params.append('group', filters.group);
  if (filters.severity !== undefined) params.append('severity', String(filters.severity));
  if (filters.status) params.append('status', filters.status);
  if (filters.host) params.append('host', filters.host);

  const url = `${API_BASE}?${params.toString()}`;
  const response = await fetch(url);
  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Failed to load overview data (${response.status}): ${errorText}`);
  }
  return response.json();
}
