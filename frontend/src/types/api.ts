// API types for the HOS Trip Planner.
// These mirror the Django REST Framework payloads (snake_case) so no
// case-transform layer is needed between the backend and the client.

export type BaseEntity = {
  id: string;
  created_at: string;
};

export type Entity<T> = {
  [K in keyof T]: T[K];
} & BaseEntity;

/** The four FMCSA duty statuses — the rows of a daily log grid. */
export type DutyStatus =
  | 'OFF_DUTY'
  | 'SLEEPER'
  | 'DRIVING'
  | 'ON_DUTY_NOT_DRIVING';

/** The kinds of stop we render on the map / stops list. */
export type StopType =
  | 'start'
  | 'pickup'
  | 'dropoff'
  | 'fuel'
  | 'break'
  | 'rest'
  | 'restart';

/** A single continuous duty-status segment on the timeline. */
export type Segment = {
  status: DutyStatus;
  start: string; // ISO datetime
  end: string; // ISO datetime
  location: string;
  remark: string;
};

/** [latitude, longitude] pair (Leaflet ordering). */
export type LatLng = [number, number];

/** A geocoding autocomplete suggestion from GET /geocode?q=. */
export type GeocodeResult = {
  label: string;
  lat: number;
  lng: number;
};

export type RouteLeg = {
  from_label: string;
  to_label: string;
  distance_miles: number;
  duration_hours: number;
  geometry: LatLng[];
};

export type RouteStop = {
  type: StopType;
  label: string;
  lat: number;
  lng: number;
  arrival: string; // ISO datetime
};

export type TripRoute = {
  geometry: LatLng[];
  legs: RouteLeg[];
  stops: RouteStop[];
};

/** Per-status totals (hours) for a single calendar day. */
export type DailyTotals = Record<DutyStatus, number>;

export type DailyLog = {
  date: string; // YYYY-MM-DD (driver's local day)
  segments: Segment[];
  totals: DailyTotals;
  miles: number;
};

export type TripSummary = {
  total_distance_miles: number;
  total_driving_hours: number;
  total_on_duty_hours: number;
  total_off_duty_hours: number;
  num_days: number;
  num_breaks: number;
  num_rest_periods: number;
  num_fuel_stops: number;
  used_34h_restart: boolean;
  cycle_hours_added: number;
};

export type Trip = Entity<{
  current_location: string;
  pickup_location: string;
  dropoff_location: string;
  current_cycle_used_hours: number;
  start_datetime: string;
  timezone: string;
  summary: TripSummary;
  route: TripRoute;
  segments: Segment[];
  daily_logs: DailyLog[];
}>;
