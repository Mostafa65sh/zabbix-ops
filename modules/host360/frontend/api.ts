import type {
  Host360ListResponse,
  Host360Detail,
  Host360TelemetryResponse
} from './types';

const API_BASE = '/api/v1/host360';

export async function fetchHost360List(
  params?: {
    search?: string;
    group?: string;
    page?: number;
    page_size?: number;
  },
  signal?: AbortSignal
): Promise<Host360ListResponse> {
  const qp = new URLSearchParams();
  if (params?.search) qp.append('search', params.search);
  if (params?.group) qp.append('group', params.group);
  if (params?.page !== undefined) qp.append('page', String(params.page));
  if (params?.page_size !== undefined) qp.append('page_size', String(params.page_size));

  const url = `${API_BASE}/hosts?${qp.toString()}`;
  const response = await fetch(url, { signal });
  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Failed to load hosts list (${response.status}): ${errorText}`);
  }
  return response.json();
}

export async function fetchHost360Detail(
  hostId: string,
  signal?: AbortSignal
): Promise<Host360Detail> {
  const url = `${API_BASE}/${encodeURIComponent(hostId)}`;
  const response = await fetch(url, { signal });
  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Failed to load host detail (${response.status}): ${errorText}`);
  }
  return response.json();
}

export async function fetchHostTelemetry(
  hostId: string,
  timeRange: string = '24h',
  signal?: AbortSignal
): Promise<Host360TelemetryResponse> {
  const qp = new URLSearchParams();
  qp.append('time_range', timeRange);

  const url = `${API_BASE}/${encodeURIComponent(hostId)}/telemetry?${qp.toString()}`;
  const response = await fetch(url, { signal });
  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Failed to load host telemetry (${response.status}): ${errorText}`);
  }
  return response.json();
}
