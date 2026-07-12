import * as React from 'react';
import { type FieldError } from 'react-hook-form';

import { FieldWrapper } from '@/components/ui/form/field-wrapper';
import { Spinner } from '@/components/ui/spinner';
import { useDebouncedValue } from '@/hooks/use-debounced-value';
import { cn } from '@/utils/cn';

import { useSearchLocations } from '../api/search-locations';

const inputClasses =
  'flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm transition-colors placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50';

type LocationComboboxProps = {
  label: string;
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  error?: FieldError;
  id?: string;
};

/**
 * Autocomplete input for a location. The form value always tracks the typed
 * text, so a free-typed value still submits (the backend geocodes it); picking
 * a suggestion simply fills in its label.
 */
export const LocationCombobox = ({
  label,
  value,
  onChange,
  placeholder,
  error,
  id,
}: LocationComboboxProps) => {
  const [open, setOpen] = React.useState(false);
  const [activeIndex, setActiveIndex] = React.useState(-1);
  const listId = React.useId();

  const debounced = useDebouncedValue(value, 250);
  const { data: results = [], isFetching } = useSearchLocations(debounced);

  // Only show suggestions the user hasn't already exactly picked.
  const suggestions =
    open && results.length && !(results.length === 1 && results[0].label === value)
      ? results
      : [];

  const select = (labelValue: string) => {
    onChange(labelValue);
    setOpen(false);
    setActiveIndex(-1);
  };

  const onKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (!suggestions.length) return;
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setActiveIndex((i) => (i + 1) % suggestions.length);
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setActiveIndex((i) => (i <= 0 ? suggestions.length - 1 : i - 1));
    } else if (e.key === 'Enter' && activeIndex >= 0) {
      e.preventDefault();
      select(suggestions[activeIndex].label);
    } else if (e.key === 'Escape') {
      setOpen(false);
      setActiveIndex(-1);
    }
  };

  return (
    <FieldWrapper label={label} error={error}>
      <div className="relative">
        <input
          id={id}
          type="text"
          role="combobox"
          aria-expanded={suggestions.length > 0}
          aria-controls={listId}
          aria-autocomplete="list"
          autoComplete="off"
          className={cn(inputClasses, isFetching && 'pr-8')}
          placeholder={placeholder}
          value={value}
          onChange={(e) => {
            onChange(e.target.value);
            setOpen(true);
            setActiveIndex(-1);
          }}
          onFocus={() => setOpen(true)}
          onBlur={() => setOpen(false)}
          onKeyDown={onKeyDown}
        />
        {isFetching && (
          <span className="absolute right-2 top-1/2 -translate-y-1/2">
            <Spinner size="sm" />
          </span>
        )}
        {suggestions.length > 0 && (
          <ul
            id={listId}
            role="listbox"
            className="absolute z-20 mt-1 max-h-60 w-full overflow-auto rounded-md border bg-popover p-1 text-sm shadow-md"
            // Keep focus on the input so onBlur doesn't fire before the click.
            onMouseDown={(e) => e.preventDefault()}
          >
            {suggestions.map((s, i) => (
              <li
                key={`${s.label}-${i}`}
                role="option"
                aria-selected={i === activeIndex}
                className={cn(
                  'cursor-pointer rounded-sm px-2 py-1.5',
                  i === activeIndex
                    ? 'bg-accent text-accent-foreground'
                    : 'hover:bg-accent hover:text-accent-foreground',
                )}
                onMouseEnter={() => setActiveIndex(i)}
                onClick={() => select(s.label)}
              >
                {s.label}
              </li>
            ))}
          </ul>
        )}
      </div>
    </FieldWrapper>
  );
};
