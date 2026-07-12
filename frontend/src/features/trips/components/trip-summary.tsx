import { TripSummary as TripSummaryType } from '@/types/api';

type Stat = { label: string; value: string };

type TripSummaryProps = {
  summary: TripSummaryType;
};

export const TripSummary = ({ summary }: TripSummaryProps) => {
  const stats: Stat[] = [
    {
      label: 'Total distance',
      value: `${summary.total_distance_miles.toFixed(0)} mi`,
    },
    {
      label: 'Driving hours',
      value: `${summary.total_driving_hours.toFixed(1)} h`,
    },
    {
      label: 'On-duty hours',
      value: `${summary.total_on_duty_hours.toFixed(1)} h`,
    },
    { label: 'Days', value: `${summary.num_days}` },
    { label: 'Breaks', value: `${summary.num_breaks}` },
    { label: 'Rest periods', value: `${summary.num_rest_periods}` },
    { label: 'Fuel stops', value: `${summary.num_fuel_stops}` },
    {
      label: 'Cycle hrs added',
      value: `${summary.cycle_hours_added.toFixed(1)} h`,
    },
    {
      label: '34-hr restart',
      value: summary.used_34h_restart ? 'Yes' : 'No',
    },
  ];

  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
      {stats.map((s) => (
        <div key={s.label} className="rounded-lg border bg-card p-4">
          <div className="text-xs uppercase tracking-wide text-muted-foreground">
            {s.label}
          </div>
          <div className="mt-1 text-xl font-semibold text-foreground">
            {s.value}
          </div>
        </div>
      ))}
    </div>
  );
};
