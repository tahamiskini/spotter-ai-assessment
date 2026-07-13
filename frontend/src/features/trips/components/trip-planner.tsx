import { useState } from 'react';

import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from '@/components/ui/tabs';
import { Trip } from '@/types/api';

import { DayStops } from './day-stops';
import { LogSheet } from './log-sheet';
import { RouteMap } from './route-map';
import { TripForm } from './trip-form';
import { TripSummary } from './trip-summary';

type TripPlannerProps = {
  initialTrip?: Trip;
};

export const TripPlanner = ({ initialTrip }: TripPlannerProps) => {
  const [trip, setTrip] = useState<Trip | undefined>(initialTrip);

  return (
    // Fill the viewport below the header on large screens so the two panes can
    // scroll independently; fall back to natural stacked height on mobile.
    <div className="flex flex-col gap-4 lg:h-[calc(100dvh-11rem)]">
      {trip && (
        <div className="shrink-0">
          <TripSummary summary={trip.summary} />
        </div>
      )}

      <div className="grid min-h-0 flex-1 gap-6 lg:grid-cols-[minmax(320px,380px)_1fr]">
        {/* Left pane: inputs + per-day stops (scrolls independently) */}
        <aside className="flex min-h-0 flex-col gap-6 lg:overflow-y-auto lg:pr-1">
          <div className="shrink-0 rounded-lg border bg-card p-5 shadow-xs">
            <TripForm
              onPlanned={setTrip}
              defaultValues={
                trip && {
                  current_location: trip.current_location,
                  pickup_location: trip.pickup_location,
                  dropoff_location: trip.dropoff_location,
                  current_cycle_used_hours: trip.current_cycle_used_hours,
                }
              }
            />
          </div>

          {trip && (
            <div className="rounded-lg border bg-card p-5 shadow-xs">
              <h2 className="mb-3 text-sm font-semibold">Planned stops</h2>
              <DayStops route={trip.route} />
            </div>
          )}
        </aside>

        {/* Right pane: map / logs (fills the remaining height) */}
        <section className="flex min-h-0 flex-col">
          {trip ? (
            <Tabs
              defaultValue="route"
              className="flex min-h-0 flex-1 flex-col"
            >
              <TabsList className="shrink-0 self-start">
                <TabsTrigger value="route">Route &amp; stops</TabsTrigger>
                <TabsTrigger value="logs">
                  Daily logs ({trip.daily_logs.length})
                </TabsTrigger>
              </TabsList>
              <TabsContent value="route" className="min-h-0 flex-1">
                <RouteMap route={trip.route} />
              </TabsContent>
              <TabsContent
                value="logs"
                className="min-h-0 flex-1 overflow-y-auto"
              >
                <div className="space-y-6">
                  {trip.daily_logs.map((log) => (
                    <LogSheet key={log.date} log={log} />
                  ))}
                </div>
              </TabsContent>
            </Tabs>
          ) : (
            <div className="flex h-full min-h-90 items-center justify-center rounded-lg border border-dashed p-6 text-center text-sm text-muted-foreground">
              Enter trip details and click &ldquo;Plan trip&rdquo; to see the
              route, stops, and daily log sheets.
            </div>
          )}
        </section>
      </div>
    </div>
  );
};
