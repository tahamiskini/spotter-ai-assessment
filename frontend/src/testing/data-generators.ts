import { nanoid } from 'nanoid';

import { Trip } from '@/types/api';

/**
 * A small, HOS-plausible sample trip used by the MSW mocks and tests.
 * Not computed by the real engine — just enough to render the UI.
 */
const generateTrip = (): Trip => ({
  id: nanoid(),
  created_at: '2026-07-10T15:00:00Z',
  current_location: 'Los Angeles, CA',
  pickup_location: 'Phoenix, AZ',
  dropoff_location: 'Dallas, TX',
  current_cycle_used_hours: 10,
  start_datetime: '2026-07-10T08:00:00-07:00',
  timezone: 'America/Los_Angeles',
  summary: {
    total_distance_miles: 1435,
    total_driving_hours: 22.5,
    total_on_duty_hours: 24.5,
    total_off_duty_hours: 20,
    num_days: 3,
    num_breaks: 2,
    num_rest_periods: 2,
    num_fuel_stops: 1,
    used_34h_restart: false,
    cycle_hours_added: 24.5,
  },
  route: {
    geometry: [
      [34.0522, -118.2437],
      [33.4484, -112.074],
      [32.7767, -96.797],
    ],
    legs: [
      {
        from_label: 'Los Angeles, CA',
        to_label: 'Phoenix, AZ',
        distance_miles: 373,
        duration_hours: 5.8,
        geometry: [
          [34.0522, -118.2437],
          [33.4484, -112.074],
        ],
      },
      {
        from_label: 'Phoenix, AZ',
        to_label: 'Dallas, TX',
        distance_miles: 1062,
        duration_hours: 16.7,
        geometry: [
          [33.4484, -112.074],
          [32.7767, -96.797],
        ],
      },
    ],
    stops: [
      {
        type: 'start',
        label: 'Los Angeles, CA',
        lat: 34.0522,
        lng: -118.2437,
        arrival: '2026-07-10T08:00:00-07:00',
      },
      {
        type: 'pickup',
        label: 'Phoenix, AZ',
        lat: 33.4484,
        lng: -112.074,
        arrival: '2026-07-10T13:48:00-07:00',
      },
      {
        type: 'dropoff',
        label: 'Dallas, TX',
        lat: 32.7767,
        lng: -96.797,
        arrival: '2026-07-12T16:00:00-05:00',
      },
    ],
  },
  segments: [
    {
      status: 'DRIVING',
      start: '2026-07-10T08:00:00-07:00',
      end: '2026-07-10T13:48:00-07:00',
      location: 'en route to Phoenix, AZ',
      remark: 'Driving',
    },
    {
      status: 'ON_DUTY_NOT_DRIVING',
      start: '2026-07-10T13:48:00-07:00',
      end: '2026-07-10T14:48:00-07:00',
      location: 'Phoenix, AZ',
      remark: 'Pickup / loading',
    },
  ],
  daily_logs: [
    {
      date: '2026-07-10',
      miles: 373,
      totals: {
        OFF_DUTY: 0,
        SLEEPER: 0,
        DRIVING: 5.8,
        ON_DUTY_NOT_DRIVING: 1,
      },
      segments: [
        {
          status: 'DRIVING',
          start: '2026-07-10T08:00:00-07:00',
          end: '2026-07-10T13:48:00-07:00',
          location: 'en route to Phoenix, AZ',
          remark: 'Driving',
        },
        {
          status: 'ON_DUTY_NOT_DRIVING',
          start: '2026-07-10T13:48:00-07:00',
          end: '2026-07-10T14:48:00-07:00',
          location: 'Phoenix, AZ',
          remark: 'Pickup / loading',
        },
      ],
    },
  ],
});

export const createTrip = (overrides?: Partial<Trip>): Trip => {
  return { ...generateTrip(), ...overrides };
};
