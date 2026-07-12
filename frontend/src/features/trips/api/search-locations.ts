import { queryOptions, useQuery } from '@tanstack/react-query';

import { api } from '@/lib/api-client';
import { GeocodeResult } from '@/types/api';

export const searchLocations = (query: string): Promise<GeocodeResult[]> => {
  return api.get('/geocode', { params: { q: query } });
};

export const getSearchLocationsQueryOptions = (query: string) => {
  return queryOptions({
    queryKey: ['geocode', query],
    queryFn: () => searchLocations(query),
    // Suggestions are stable for a given query; keep them briefly.
    staleTime: 5 * 60 * 1000,
    // Only hit the API once the query is meaningful (matches the backend's
    // 2-char minimum), and keep the last results visible while typing.
    enabled: query.trim().length >= 2,
    placeholderData: (prev) => prev,
  });
};

export const useSearchLocations = (query: string) => {
  return useQuery(getSearchLocationsQueryOptions(query));
};
