import { RouteStop, TripRoute } from '@/types/api';

import { STOP_META } from '../utils';

const dayKey = (iso: string) => iso.split('T')[0];
const timeOf = (iso: string) => (iso.split('T')[1] ?? '').slice(0, 5);

type DayStopsProps = {
  route: TripRoute;
};

export const DayStops = ({ route }: DayStopsProps) => {
  const byDay = new Map<string, RouteStop[]>();
  route.stops.forEach((s) => {
    const key = dayKey(s.arrival);
    if (!byDay.has(key)) byDay.set(key, []);
    byDay.get(key)!.push(s);
  });

  const days = [...byDay.entries()];

  return (
    <div className="space-y-4">
      {days.map(([date, stops], i) => (
        <div key={date}>
          <h3 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
            Day {i + 1} · {date}
          </h3>
          <ol className="mt-2 space-y-1.5">
            {stops.map((s, j) => (
              <li key={j} className="flex items-center gap-2 text-sm">
                <span
                  className="size-2.5 shrink-0 rounded-full"
                  style={{ backgroundColor: STOP_META[s.type].color }}
                  aria-hidden
                />
                <span className="font-medium">{STOP_META[s.type].label}</span>
                <span className="min-w-0 truncate text-muted-foreground">
                  {s.label}
                </span>
                <time className="ml-auto shrink-0 text-xs tabular-nums text-muted-foreground">
                  {timeOf(s.arrival)}
                </time>
              </li>
            ))}
          </ol>
        </div>
      ))}
    </div>
  );
};
