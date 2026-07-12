import { useMutation, useQueryClient } from '@tanstack/react-query';
import { z } from 'zod';

import { api } from '@/lib/api-client';
import { MutationConfig } from '@/lib/react-query';
import { Trip } from '@/types/api';

import { getTripQueryOptions } from './get-trip';

export const createTripInputSchema = z.object({
  current_location: z.string().min(1, 'Required'),
  pickup_location: z.string().min(1, 'Required'),
  dropoff_location: z.string().min(1, 'Required'),
  current_cycle_used_hours: z.coerce
    .number({ invalid_type_error: 'Enter a number' })
    .min(0, 'Must be 0 or more')
    .max(70, 'Cannot exceed 70'),
  start_datetime: z.string().optional(),
});

export type CreateTripInput = z.infer<typeof createTripInputSchema>;

export const createTrip = ({
  data,
}: {
  data: CreateTripInput;
}): Promise<Trip> => {
  return api.post('/trips/', data);
};

type UseCreateTripOptions = {
  mutationConfig?: MutationConfig<typeof createTrip>;
};

export const useCreateTrip = ({
  mutationConfig,
}: UseCreateTripOptions = {}) => {
  const queryClient = useQueryClient();

  const { onSuccess, ...restConfig } = mutationConfig || {};

  return useMutation({
    onSuccess: (trip, ...args) => {
      // Seed the detail cache so the result page renders instantly.
      queryClient.setQueryData(
        getTripQueryOptions(trip.id).queryKey,
        trip,
      );
      onSuccess?.(trip, ...args);
    },
    ...restConfig,
    mutationFn: createTrip,
  });
};
