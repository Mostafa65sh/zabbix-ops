import type { TopNResponse, TopNOverviewResponse } from './types';

const API_BASE = '/api/v1/top_n';

export async function fetchTopNRankings(
  params?: {
    metric?: 'cpu' | 'memory' | 'storage' | 'problems';
    limit?: number;
    order?: 'desc' | 'asc';
    group?: string;
  },
  signal?: AbortSignal
): Promise<TopNResponse> {
  const qp = new URLSearchParams();
  if (params?.metric) qp.append('metric', params.metric);
  if (params?.limit !== undefined) qp.append('limit', String(params.limit));
  if (params?.order) qp.append('order', params.order);
  if (params?.group) qp.append('group', params.group);

  const url = `${API_BASE}/rankings?${qp.toString()}`;
  const response = await fetch(url, { signal });
  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Failed to load Top N rankings (${response.status}): ${errorText}`);
  }
  return response.json();
}

export async function fetchTopNOverview(
  params?: {
    limit?: number;
    group?: string;
  },
  signal?: AbortSignal
): Promise<TopNOverviewResponse> {
  const qp = new URLSearchParams();
  if (params?.limit !== undefined) qp.append('limit', String(params.limit));
  if (params?.group) qp.append('group', params.group);

  const url = `${API_BASE}/overview?${qp.toString()}`;
  const response = await fetch(url, { signal });
  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Failed to load Top N overview (${response.status}): ${errorText}`);
  }
  return response.json();
}
