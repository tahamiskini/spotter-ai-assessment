import { format } from 'date-fns';
import { CalendarIcon } from 'lucide-react';
import * as React from 'react';
import { type FieldError } from 'react-hook-form';

import { Button } from '@/components/ui/button';
import { Calendar } from '@/components/ui/calendar';
import { FieldWrapper } from '@/components/ui/form/field-wrapper';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { cn } from '@/utils/cn';

type DateTimePickerProps = {
  label: string;
  /** ISO-ish local value "YYYY-MM-DDTHH:mm", or "" when unset. */
  value: string;
  onChange: (value: string) => void;
  error?: FieldError;
};

const DEFAULT_TIME = '08:00';

const parseDate = (value: string): Date | undefined => {
  const datePart = value.split('T')[0];
  if (!datePart) return undefined;
  const [y, m, d] = datePart.split('-').map(Number);
  if (!y || !m || !d) return undefined;
  return new Date(y, m - 1, d);
};

const parseTime = (value: string): string =>
  value.split('T')[1]?.slice(0, 5) || DEFAULT_TIME;

export const DateTimePicker = ({
  label,
  value,
  onChange,
  error,
}: DateTimePickerProps) => {
  const [open, setOpen] = React.useState(false);
  const selectedDate = parseDate(value);
  const time = parseTime(value);

  const compose = (date: Date | undefined, t: string) => {
    if (!date) return '';
    return `${format(date, 'yyyy-MM-dd')}T${t}`;
  };

  return (
    <FieldWrapper label={label} error={error}>
      <Popover open={open} onOpenChange={setOpen}>
        <PopoverTrigger asChild>
          <Button
            type="button"
            variant="outline"
            className={cn(
              'w-full justify-start px-3 font-normal',
              !selectedDate && 'text-muted-foreground',
            )}
            icon={<CalendarIcon className="size-4" />}
          >
            {selectedDate
              ? `${format(selectedDate, 'PPP')} · ${time}`
              : 'Pick a date & time'}
          </Button>
        </PopoverTrigger>
        <PopoverContent className="w-auto p-0" align="start">
          <Calendar
            mode="single"
            selected={selectedDate}
            defaultMonth={selectedDate}
            onSelect={(date) => onChange(compose(date, time))}
            autoFocus
          />
          <div className="flex items-center justify-between gap-2 border-t p-3">
            <input
              type="time"
              aria-label="Start time"
              value={time}
              disabled={!selectedDate}
              onChange={(e) =>
                onChange(compose(selectedDate, e.target.value || DEFAULT_TIME))
              }
              className="h-9 rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50"
            />
            <div className="flex gap-2">
              <Button
                type="button"
                variant="ghost"
                size="sm"
                onClick={() => {
                  onChange('');
                  setOpen(false);
                }}
              >
                Clear
              </Button>
              <Button
                type="button"
                size="sm"
                onClick={() => setOpen(false)}
              >
                Done
              </Button>
            </div>
          </div>
        </PopoverContent>
      </Popover>
    </FieldWrapper>
  );
};
