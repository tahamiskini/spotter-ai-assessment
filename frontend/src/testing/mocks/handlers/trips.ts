import { HttpResponse, http } from 'msw';

import { env } from '@/config/env';
import { createTrip } from '@/testing/data-generators';
import { GeocodeResult } from '@/types/api';

import { networkDelay } from '../utils';

// A small offline gazetteer mirroring the backend's fallback, so geocode
// autocomplete works in mock mode.
const MOCK_CITIES: GeocodeResult[] = [
  { label: 'Los Angeles', lat: 34.0522, lng: -118.2437 },
  { label: 'Phoenix', lat: 33.4484, lng: -112.074 },
  { label: 'Dallas', lat: 32.7767, lng: -96.797 },
  { label: 'Houston', lat: 29.7604, lng: -95.3698 },
  { label: 'San Antonio', lat: 29.4241, lng: -98.4936 },
  { label: 'San Francisco', lat: 37.7749, lng: -122.4194 },
  { label: 'Las Vegas', lat: 36.1699, lng: -115.1398 },
  { label: 'Denver', lat: 39.7392, lng: -104.9903 },
  { label: 'Chicago', lat: 41.8781, lng: -87.6298 },
  { label: 'New York', lat: 40.7128, lng: -74.006 },
];

export const tripsHandlers = [
  http.get(`${env.API_URL}/geocode`, async ({ request }) => {
    await networkDelay();
    const q = (new URL(request.url).searchParams.get('q') || '')
      .trim()
      .toLowerCase();
    if (q.length < 2) {
      return HttpResponse.json([]);
    }
    const matches = MOCK_CITIES.filter((c) =>
      c.label.toLowerCase().includes(q),
    )
      .sort(
        (a, b) =>
          Number(!a.label.toLowerCase().startsWith(q)) -
          Number(!b.label.toLowerCase().startsWith(q)),
      )
      .slice(0, 5);
    return HttpResponse.json(matches);
  }),

  http.post(`${env.API_URL}/trips/`, async ({ request }) => {
    await networkDelay();
    const body = (await request.json().catch(() => ({}))) as Record<
      string,
      unknown
    >;
    const trip = createTrip(body as any);
    return HttpResponse.json(trip, { status: 201 });
  }),

  http.get(`${env.API_URL}/trips/:tripId/`, async ({ params }) => {
    await networkDelay();
    const trip = createTrip({ id: params.tripId as string });
    return HttpResponse.json(trip);
  }),
];
