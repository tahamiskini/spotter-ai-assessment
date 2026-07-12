import { DutyStatus, StopType } from '@/types/api';

/** Display metadata for each duty status — order matches the log-grid rows. */
export const DUTY_STATUS_META: Record<
  DutyStatus,
  { label: string; row: number; color: string }
> = {
  OFF_DUTY: { label: 'Off Duty', row: 0, color: '#94a3b8' },
  SLEEPER: { label: 'Sleeper Berth', row: 1, color: '#6366f1' },
  DRIVING: { label: 'Driving', row: 2, color: '#16a34a' },
  ON_DUTY_NOT_DRIVING: { label: 'On Duty (ND)', row: 3, color: '#f59e0b' },
};

export const DUTY_STATUS_ORDER: DutyStatus[] = [
  'OFF_DUTY',
  'SLEEPER',
  'DRIVING',
  'ON_DUTY_NOT_DRIVING',
];

export const STOP_META: Record<StopType, { label: string; color: string }> = {
  start: { label: 'Start', color: '#0ea5e9' },
  pickup: { label: 'Pickup', color: '#16a34a' },
  dropoff: { label: 'Dropoff', color: '#dc2626' },
  fuel: { label: 'Fuel', color: '#f59e0b' },
  break: { label: '30-min Break', color: '#38bdf8' },
  rest: { label: '10-hr Rest', color: '#6366f1' },
  restart: { label: '34-hr Restart', color: '#8b5cf6' },
};

/**
 * Hour-of-day (0–24) from an ISO timestamp, read from its wall-clock portion.
 * The backend emits times already in the driver's local timezone, so parsing
 * the "HH:MM:SS" after the "T" is timezone-agnostic and avoids drift.
 */
export const hoursFromIso = (iso: string): number => {
  const timePart = iso.split('T')[1] ?? '00:00:00';
  const [h, m = '0', s = '0'] = timePart.replace('Z', '').split(/[:+-]/);
  return Number(h) + Number(m) / 60 + Number(s) / 3600;
};

export const formatHours = (hours: number): string => {
  const h = Math.floor(hours);
  const m = Math.round((hours - h) * 60);
  return `${h}h ${m.toString().padStart(2, '0')}m`;
};
