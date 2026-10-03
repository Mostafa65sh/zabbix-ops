import type { MultiSeriesGraphResponse, GraphTargetsResponse } from './types';

const API_BASE = '/api/v1/graph_explorer';

export async function fetchGraphTargets(
  params?: {
    search?: string;
    group?: string;
  },
  signal?: AbortSignal
): Promise<GraphTargetsResponse> {
  const qp = new URLSearchParams();
  if (params?.search) qp.append('search', params.search);
  if (params?.group) qp.append('group', params.group);

  const url = `${API_BASE}/targets?${qp.toString()}`;
  const response = await fetch(url, { signal });
  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Failed to load graph targets (${response.status}): ${errorText}`);
  }
  return response.json();
}

export async function fetchGraphSeries(
  params: {
    host_ids: string[];
    metrics: string[];
    time_range?: string;
  },
  signal?: AbortSignal
): Promise<MultiSeriesGraphResponse> {
  const qp = new URLSearchParams();
  qp.append('host_ids', params.host_ids.join(','));
  qp.append('metrics', params.metrics.join(','));
  if (params.time_range) qp.append('time_range', params.time_range);

  const url = `${API_BASE}/series?${qp.toString()}`;
  const response = await fetch(url, { signal });
  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Failed to load graph series (${response.status}): ${errorText}`);
  }
  return response.json();
}
