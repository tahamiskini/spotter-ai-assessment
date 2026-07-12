import { queryOptions, useQuery } from '@tanstack/react-query';

import { api } from '@/lib/api-client';
import { QueryConfig } from '@/lib/react-query';
import { Trip } from '@/types/api';

export const getTrip = (tripId: string): Promise<Trip> => {
  return api.get(`/trips/${tripId}/`);
};

export const getTripQueryOptions = (tripId: string) => {
  return queryOptions({
    queryKey: ['trips', tripId],
    queryFn: () => getTrip(tripId),
  });
};

type UseTripOptions = {
  tripId: string;
  queryConfig?: QueryConfig<typeof getTripQueryOptions>;
};

export const useTrip = ({ tripId, queryConfig }: UseTripOptions) => {
  return useQuery({
    ...getTripQueryOptions(tripId),
    ...queryConfig,
  });
};