import type { GlobalSearchResponse } from './types';

const API_BASE = '/api/v1/global_search';

export async function fetchGlobalSearch(
  query: string,
  categories?: string[],
  limit = 20,
  signal?: AbortSignal
): Promise<GlobalSearchResponse> {
  const qp = new URLSearchParams();
  qp.append('q', query);
  if (categories && categories.length > 0) {
    qp.append('categories', categories.join(','));
  }
  qp.append('limit', limit.toString());

  const url = `${API_BASE}/query?${qp.toString()}`;
  const response = await fetch(url, { signal });
  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Global search query failed (${response.status}): ${errorText}`);
  }
  return response.json();
}
