import { DailyLog } from '@/types/api';

import { DUTY_STATUS_META, DUTY_STATUS_ORDER, hoursFromIso } from '../utils';

// SVG geometry for the 24-hour grid.
const W = 1000;
const GUTTER_L = 132;
const GUTTER_R = 78;
const TOP = 28;
const ROW_H = 34;
const GRID_R = W - GUTTER_R;
const GRID_W = GRID_R - GUTTER_L;
const HEIGHT = TOP + DUTY_STATUS_ORDER.length * ROW_H + 24;

const xForHour = (hour: number) => GUTTER_L + (hour / 24) * GRID_W;
const rowCenter = (row: number) => TOP + row * ROW_H + ROW_H / 2;

type LogSheetProps = {
  log: DailyLog;
};

export const LogSheet = ({ log }: LogSheetProps) => {
  // Build ordered timeline points from the day's segments.
  const segs = [...log.segments].sort(
    (a, b) => hoursFromIso(a.start) - hoursFromIso(b.start),
  );

  const lines: JSX.Element[] = [];
  let prev: { x: number; y: number } | null = null;

  segs.forEach((seg, i) => {
    const start = hoursFromIso(seg.start);
    let end = hoursFromIso(seg.end);
    if (end <= start) end = 24; // segment runs to (next) midnight
    const meta = DUTY_STATUS_META[seg.status];
    const y = rowCenter(meta.row);
    const x1 = xForHour(start);
    const x2 = xForHour(end);

    // vertical connector from previous status to this one
    if (prev) {
      lines.push(
        <line
          key={`v-${i}`}
          x1={x1}
          y1={prev.y}
          x2={x1}
          y2={y}
          stroke="#1e293b"
          strokeWidth={2}
        />,
      );
    }
    // horizontal status line
    lines.push(
      <line
        key={`h-${i}`}
        x1={x1}
        y1={y}
        x2={x2}
        y2={y}
        stroke={meta.color}
        strokeWidth={4}
        strokeLinecap="round"
      />,
    );
    prev = { x: x2, y };
  });

  const hourTicks = Array.from({ length: 25 }, (_, h) => h);

  return (
    <div className="rounded-lg border bg-card p-4">
      <div className="mb-2 flex items-baseline justify-between">
        <h3 className="text-sm font-semibold text-foreground">{log.date}</h3>
        <span className="text-xs text-muted-foreground">
          {log.miles.toFixed(0)} mi driven
        </span>
      </div>

      <div className="overflow-x-auto">
        <svg
          viewBox={`0 0 ${W} ${HEIGHT}`}
          className="w-full min-w-[720px]"
          role="img"
          aria-label={`Duty status log for ${log.date}`}
        >
          {/* hour gridlines + labels */}
          {hourTicks.map((h) => {
            const x = xForHour(h);
            const major = h % 6 === 0;
            return (
              <g key={`t-${h}`}>
                <line
                  x1={x}
                  y1={TOP}
                  x2={x}
                  y2={TOP + DUTY_STATUS_ORDER.length * ROW_H}
                  stroke={major ? '#cbd5e1' : '#e2e8f0'}
                  strokeWidth={major ? 1 : 0.5}
                />
                {h % 3 === 0 && (
                  <text
                    x={x}
                    y={TOP - 8}
                    textAnchor="middle"
                    className="fill-slate-500"
                    fontSize={11}
                  >
                    {h === 24 ? '24' : h.toString().padStart(2, '0')}
                  </text>
                )}
              </g>
            );
          })}

          {/* rows: labels, separators, total */}
          {DUTY_STATUS_ORDER.map((status, row) => {
            const yTop = TOP + row * ROW_H;
            const meta = DUTY_STATUS_META[status];
            return (
              <g key={status}>
                <line
                  x1={GUTTER_L}
                  y1={yTop + ROW_H}
                  x2={GRID_R}
                  y2={yTop + ROW_H}
                  stroke="#e2e8f0"
                  strokeWidth={1}
                />
                <line
                  x1={GUTTER_L}
                  y1={yTop}
                  x2={GUTTER_L}
                  y2={yTop + ROW_H}
                  stroke="#e2e8f0"
                />
                <text
                  x={GUTTER_L - 10}
                  y={rowCenter(row) + 4}
                  textAnchor="end"
                  className="fill-slate-700"
                  fontSize={12}
                >
                  {meta.label}
                </text>
                <text
                  x={GRID_R + 10}
                  y={rowCenter(row) + 4}
                  className="fill-slate-500"
                  fontSize={11}
                >
                  {(log.totals[status] ?? 0).toFixed(1)}h
                </text>
              </g>
            );
          })}

          {/* top border of grid */}
          <line
            x1={GUTTER_L}
            y1={TOP}
            x2={GRID_R}
            y2={TOP}
            stroke="#cbd5e1"
          />

          {/* the duty-status timeline */}
          {lines}
        </svg>
      </div>
    </div>
  );
};
