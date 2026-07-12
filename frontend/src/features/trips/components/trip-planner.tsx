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
    <div className="space-y-6">
      {trip && <TripSummary summary={trip.summary} />}

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Left panel: inputs + per-day stops */}
        <aside className="space-y-6 lg:col-span-1">
          <div className="rounded-lg border bg-card p-5">
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
            <div className="rounded-lg border bg-card p-5">
              <h2 className="mb-3 text-sm font-semibold">Planned stops</h2>
              <DayStops route={trip.route} />
            </div>
          )}
        </aside>

        {/* Right: map / logs tabs */}
        <section className="lg:col-span-2">
          {trip ? (
            <Tabs defaultValue="route">
              <TabsList>
                <TabsTrigger value="route">Route &amp; stops</TabsTrigger>
                <TabsTrigger value="logs">
                  Daily logs ({trip.daily_logs.length})
                </TabsTrigger>
              </TabsList>
              <TabsContent value="route">
                <RouteMap route={trip.route} />
              </TabsContent>
              <TabsContent value="logs">
                <div className="space-y-6">
                  {trip.daily_logs.map((log) => (
                    <LogSheet key={log.date} log={log} />
                  ))}
                </div>
              </TabsContent>
            </Tabs>
          ) : (
            <div className="flex h-[420px] items-center justify-center rounded-lg border border-dashed p-6 text-center text-sm text-muted-foreground">
              Enter trip details and click &ldquo;Plan trip&rdquo; to see the
              route, stops, and daily log sheets.
            </div>
          )}
        </section>
      </div>
    </div>
  );
};
