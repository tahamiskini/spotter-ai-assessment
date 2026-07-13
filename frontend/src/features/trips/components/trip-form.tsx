import { Controller } from 'react-hook-form';

import { Button } from '@/components/ui/button';
import { Form, Input } from '@/components/ui/form';
import { Trip } from '@/types/api';

import {
  CreateTripInput,
  createTripInputSchema,
  useCreateTrip,
} from '../api/create-trip';

import { DateTimePicker } from './date-time-picker';
import { LocationCombobox } from './location-combobox';

const LOCATION_FIELDS = [
  { name: 'current_location', label: 'Current location', placeholder: 'e.g. Los Angeles, CA' },
  { name: 'pickup_location', label: 'Pickup location', placeholder: 'e.g. Phoenix, AZ' },
  { name: 'dropoff_location', label: 'Dropoff location', placeholder: 'e.g. Dallas, TX' },
] as const;

type TripFormProps = {
  onPlanned?: (trip: Trip) => void;
  defaultValues?: Partial<CreateTripInput>;
};

export const TripForm = ({ onPlanned, defaultValues }: TripFormProps) => {
  const createTrip = useCreateTrip({
    mutationConfig: {
      onSuccess: (trip) => onPlanned?.(trip),
    },
  });

  return (
    <Form
      onSubmit={(values) => createTrip.mutate({ data: values })}
      schema={createTripInputSchema}
      options={{
        defaultValues: {
          current_location: '',
          pickup_location: '',
          dropoff_location: '',
          current_cycle_used_hours: 0,
          start_datetime: '',
          ...defaultValues,
        },
      }}
    >
      {({ control, register, formState }) => (
        <>
          {/* Location fields use type-ahead geocoding autocomplete. */}
          {LOCATION_FIELDS.map((f) => (
            <Controller
              key={f.name}
              name={f.name}
              control={control}
              render={({ field }) => (
                <LocationCombobox
                  label={f.label}
                  placeholder={f.placeholder}
                  value={field.value ?? ''}
                  onChange={field.onChange}
                  error={formState.errors[f.name]}
                />
              )}
            />
          ))}

          <Input
            type="number"
            step="0.5"
            label="Current cycle used (hrs)"
            placeholder="0"
            error={formState.errors['current_cycle_used_hours']}
            registration={register('current_cycle_used_hours')}
          />
          <Controller
            name="start_datetime"
            control={control}
            render={({ field }) => (
              <DateTimePicker
                label="Start date & time (optional)"
                value={field.value ?? ''}
                onChange={field.onChange}
                error={formState.errors['start_datetime']}
              />
            )}
          />

          <Button
            type="submit"
            className="w-full"
            isLoading={createTrip.isPending}
          >
            Plan trip
          </Button>
        </>
      )}
    </Form>
  );
};
