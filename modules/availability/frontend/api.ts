import type {
  AvailabilityOverview,
  ServiceAvailabilityList,
  SLAListResponse,
  AvailabilityTrendResponse,
  ServiceFilters
} from './types';

const API_BASE = '/api/v1/availability';

export async function fetchAvailabilityOverview(params?: {
  time_range?: string;
  time_from?: number;
  time_till?: number;
  sla_id?: string;
}): Promise<AvailabilityOverview> {
  const qp = new URLSearchParams();
  if (params?.time_range) qp.append('time_range', params.time_range);
  if (params?.time_from !== undefined) qp.append('time_from', String(params.time_from));
  if (params?.time_till !== undefined) qp.append('time_till', String(params.time_till));
  if (params?.sla_id) qp.append('sla_id', params.sla_id);

  const url = `${API_BASE}?${qp.toString()}`;
  const response = await fetch(url);
  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Failed to load availability overview (${response.status}): ${errorText}`);
  }
  return response.json();
}

export async function fetchServicesList(filters: ServiceFilters): Promise<ServiceAvailabilityList> {
  const qp = new URLSearchParams();
  if (filters.page !== undefined) qp.append('page', String(filters.page));
  if (filters.page_size !== undefined) qp.append('page_size', String(filters.page_size));
  if (filters.sla_id) qp.append('sla_id', filters.sla_id);
  if (filters.status) qp.append('status', filters.status);
  if (filters.search) qp.append('search', filters.search);
  if (filters.sort_by) qp.append('sort_by', filters.sort_by);
  if (filters.sort_order) qp.append('sort_order', filters.sort_order);

  const url = `${API_BASE}/services?${qp.toString()}`;
  const response = await fetch(url);
  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Failed to load services list (${response.status}): ${errorText}`);
  }
  return response.json();
}

export async function fetchSLAsList(params?: {
  page?: number;
  page_size?: number;
  search?: string;
  sort_by?: string;
  sort_order?: string;
}): Promise<SLAListResponse> {
  const qp = new URLSearchParams();
  if (params?.page !== undefined) qp.append('page', String(params.page));
  if (params?.page_size !== undefined) qp.append('page_size', String(params.page_size));
  if (params?.search) qp.append('search', params.search);
  if (params?.sort_by) qp.append('sort_by', params.sort_by);
  if (params?.sort_order) qp.append('sort_order', params.sort_order);

  const url = `${API_BASE}/slas?${qp.toString()}`;
  const response = await fetch(url);
  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Failed to load SLAs list (${response.status}): ${errorText}`);
  }
  return response.json();
}

export async function fetchAvailabilityTrend(
  slaId: string,
  serviceId?: string,
  periods: number = 12
): Promise<AvailabilityTrendResponse> {
  const qp = new URLSearchParams();
  qp.append('sla_id', slaId);
  if (serviceId) qp.append('service_id', serviceId);
  qp.append('periods', String(periods));

  const url = `${API_BASE}/trend?${qp.toString()}`;
  const response = await fetch(url);
  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Failed to load availability trend (${response.status}): ${errorText}`);
  }
  return response.json();
}
