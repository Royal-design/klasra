"use client";

import * as React from "react";
import { Calendar as CalendarIcon, ChevronLeft, ChevronRight } from "lucide-react";
import { cn } from "@/lib/utils";

const MONTHS = [
  "January",
  "February",
  "March",
  "April",
  "May",
  "June",
  "July",
  "August",
  "September",
  "October",
  "November",
  "December",
];

const SHORT_MONTHS = [
  "Jan",
  "Feb",
  "Mar",
  "Apr",
  "May",
  "Jun",
  "Jul",
  "Aug",
  "Sep",
  "Oct",
  "Nov",
  "Dec",
];

const WEEKDAYS = ["Su", "Mo", "Tu", "We", "Th", "Fr", "Sa"];

function parseIsoDate(value: string): { year: number; month: number; day: number } | null {
  const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(value.trim());
  if (!match) return null;
  const year = Number(match[1]);
  const month = Number(match[2]) - 1;
  const day = Number(match[3]);
  if (month < 0 || month > 11 || day < 1 || day > 31) return null;
  return { year, month, day };
}

function toIsoDate(year: number, month: number, day: number): string {
  const m = String(month + 1).padStart(2, "0");
  const d = String(day).padStart(2, "0");
  return `${year}-${m}-${d}`;
}

function formatDisplayDate(value: string): string {
  const parsed = parseIsoDate(value);
  if (!parsed) return "";
  return `${SHORT_MONTHS[parsed.month]} ${parsed.day}, ${parsed.year}`;
}

export interface DatePickerProps {
  id?: string;
  value: string;
  onChange: (nextIsoDate: string) => void;
  placeholder?: string;
  required?: boolean;
  disabled?: boolean;
  className?: string;
}

export function DatePicker({
  id,
  value,
  onChange,
  placeholder = "Select date",
  required = false,
  disabled = false,
  className,
}: DatePickerProps) {
  const containerRef = React.useRef<HTMLDivElement>(null);
  const [open, setOpen] = React.useState(false);

  const today = React.useMemo(() => {
    const now = new Date();
    return {
      year: now.getFullYear(),
      month: now.getMonth(),
      day: now.getDate(),
    };
  }, []);

  const selected = React.useMemo(() => parseIsoDate(value), [value]);

  const [viewYear, setViewYear] = React.useState<number>(
    selected?.year ?? today.year
  );
  const [viewMonth, setViewMonth] = React.useState<number>(
    selected?.month ?? today.month
  );

  React.useEffect(() => {
    if (open && selected) {
      setViewYear(selected.year);
      setViewMonth(selected.month);
    }
  }, [open, selected]);

  React.useEffect(() => {
    if (!open) return;
    const handlePointerDown = (event: MouseEvent) => {
      if (
        containerRef.current &&
        !containerRef.current.contains(event.target as Node)
      ) {
        setOpen(false);
      }
    };
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", handlePointerDown);
    document.addEventListener("keydown", handleKeyDown);
    return () => {
      document.removeEventListener("mousedown", handlePointerDown);
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, [open]);

  const firstDayOfMonth = new Date(viewYear, viewMonth, 1).getDay();
  const daysInMonth = new Date(viewYear, viewMonth + 1, 0).getDate();
  const daysInPrevMonth = new Date(viewYear, viewMonth, 0).getDate();

  const cells: Array<{
    year: number;
    month: number;
    day: number;
    inCurrentMonth: boolean;
  }> = [];

  for (let i = firstDayOfMonth - 1; i >= 0; i--) {
    const prevMonth = viewMonth === 0 ? 11 : viewMonth - 1;
    const prevYear = viewMonth === 0 ? viewYear - 1 : viewYear;
    cells.push({
      year: prevYear,
      month: prevMonth,
      day: daysInPrevMonth - i,
      inCurrentMonth: false,
    });
  }
  for (let d = 1; d <= daysInMonth; d++) {
    cells.push({
      year: viewYear,
      month: viewMonth,
      day: d,
      inCurrentMonth: true,
    });
  }
  const trailing = cells.length % 7 === 0 ? 0 : 7 - (cells.length % 7);
  for (let d = 1; d <= trailing; d++) {
    const nextMonth = viewMonth === 11 ? 0 : viewMonth + 1;
    const nextYear = viewMonth === 11 ? viewYear + 1 : viewYear;
    cells.push({
      year: nextYear,
      month: nextMonth,
      day: d,
      inCurrentMonth: false,
    });
  }

  const yearOptions = React.useMemo(() => {
    const base = today.year;
    const min = Math.min(base - 10, viewYear - 5);
    const max = Math.max(base + 10, viewYear + 5);
    const list: number[] = [];
    for (let y = min; y <= max; y++) {
      list.push(y);
    }
    return list;
  }, [today.year, viewYear]);

  const goPrevMonth = () => {
    if (viewMonth === 0) {
      setViewMonth(11);
      setViewYear((y) => y - 1);
    } else {
      setViewMonth((m) => m - 1);
    }
  };

  const goNextMonth = () => {
    if (viewMonth === 11) {
      setViewMonth(0);
      setViewYear((y) => y + 1);
    } else {
      setViewMonth((m) => m + 1);
    }
  };

  const selectDay = (year: number, month: number, day: number) => {
    onChange(toIsoDate(year, month, day));
    setOpen(false);
  };

  const displayLabel = formatDisplayDate(value);

  return (
    <div ref={containerRef} className={cn("relative", className)}>
      {required && (
        <input
          tabIndex={-1}
          aria-hidden="true"
          required
          value={value}
          onChange={() => {}}
          className="pointer-events-none absolute inset-0 h-full w-full opacity-0"
        />
      )}
      <button
        id={id}
        type="button"
        disabled={disabled}
        aria-expanded={open}
        aria-haspopup="dialog"
        onClick={() => setOpen((prev) => !prev)}
        className={cn(
          "flex h-10 w-full items-center justify-between gap-2 rounded-xl border border-input bg-card px-3.5 py-2 text-left text-sm transition-colors",
          "hover:border-primary/50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
          "disabled:cursor-not-allowed disabled:opacity-50 cursor-pointer",
          displayLabel ? "text-foreground" : "text-muted-foreground"
        )}
      >
        <span className="truncate font-medium">
          {displayLabel || placeholder}
        </span>
        <CalendarIcon className="h-4 w-4 shrink-0 text-muted-foreground" />
      </button>

      {open && (
        <div
          role="dialog"
          aria-label="Choose date"
          className="absolute left-0 top-full z-50 mt-2 w-72 rounded-2xl border border-border bg-card p-3.5 text-card-foreground shadow-2xl"
        >
          {/* Month / Year Header */}
          <div className="mb-3 flex items-center justify-between gap-1.5">
            <button
              type="button"
              aria-label="Previous month"
              onClick={goPrevMonth}
              className="flex h-7 w-7 items-center justify-center rounded-lg text-muted-foreground transition-colors hover:bg-muted hover:text-foreground cursor-pointer"
            >
              <ChevronLeft className="h-4 w-4" />
            </button>

            <div className="flex items-center gap-1">
              <select
                aria-label="Month"
                value={viewMonth}
                onChange={(e) => setViewMonth(Number(e.target.value))}
                className="rounded-lg border border-transparent bg-muted/60 px-2 py-1 text-xs font-semibold text-foreground outline-none hover:border-border focus:border-primary cursor-pointer"
              >
                {MONTHS.map((m, idx) => (
                  <option key={m} value={idx} className="bg-card text-foreground">
                    {m}
                  </option>
                ))}
              </select>
              <select
                aria-label="Year"
                value={viewYear}
                onChange={(e) => setViewYear(Number(e.target.value))}
                className="rounded-lg border border-transparent bg-muted/60 px-2 py-1 font-mono text-xs font-semibold text-foreground outline-none hover:border-border focus:border-primary cursor-pointer"
              >
                {yearOptions.map((y) => (
                  <option key={y} value={y} className="bg-card text-foreground">
                    {y}
                  </option>
                ))}
              </select>
            </div>

            <button
              type="button"
              aria-label="Next month"
              onClick={goNextMonth}
              className="flex h-7 w-7 items-center justify-center rounded-lg text-muted-foreground transition-colors hover:bg-muted hover:text-foreground cursor-pointer"
            >
              <ChevronRight className="h-4 w-4" />
            </button>
          </div>

          {/* Weekday Labels */}
          <div className="mb-1 grid grid-cols-7 text-center">
            {WEEKDAYS.map((day) => (
              <span
                key={day}
                className="py-1 text-[11px] font-semibold text-muted-foreground"
              >
                {day}
              </span>
            ))}
          </div>

          {/* Day Grid */}
          <div className="grid grid-cols-7 gap-0.5">
            {cells.map((cell) => {
              const isSelected =
                selected !== null &&
                selected.year === cell.year &&
                selected.month === cell.month &&
                selected.day === cell.day;
              const isToday =
                today.year === cell.year &&
                today.month === cell.month &&
                today.day === cell.day;

              return (
                <button
                  key={`${cell.year}-${cell.month}-${cell.day}`}
                  type="button"
                  onClick={() => selectDay(cell.year, cell.month, cell.day)}
                  className={cn(
                    "flex h-8 w-8 items-center justify-center rounded-lg text-xs font-medium transition-colors cursor-pointer",
                    !cell.inCurrentMonth && "text-muted-foreground/45",
                    cell.inCurrentMonth &&
                      !isSelected &&
                      "text-foreground hover:bg-muted",
                    isToday &&
                      !isSelected &&
                      "ring-1 ring-primary/60 font-semibold text-primary",
                    isSelected &&
                      "bg-primary font-semibold text-primary-foreground shadow-sm"
                  )}
                >
                  {cell.day}
                </button>
              );
            })}
          </div>

          {/* Footer */}
          <div className="mt-3 flex items-center justify-between border-t border-border pt-2.5">
            <span className="font-mono text-[11px] text-muted-foreground">
              {value || "YYYY-MM-DD"}
            </span>
            <button
              type="button"
              onClick={() => selectDay(today.year, today.month, today.day)}
              className="rounded-lg px-2 py-1 text-xs font-semibold text-primary transition-colors hover:bg-primary/10 cursor-pointer"
            >
              Today
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
