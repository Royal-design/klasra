"use client";

import * as React from "react";
import { Check, ChevronDown } from "lucide-react";
import { cn } from "@/lib/utils";

interface ParsedOption {
  value: string;
  label: string;
  disabled?: boolean;
}

export interface SelectFieldProps {
  id?: string;
  name?: string;
  value?: string;
  defaultValue?: string;
  required?: boolean;
  disabled?: boolean;
  hasError?: boolean;
  className?: string;
  placeholder?: string;
  "aria-label"?: string;
  onChange?: (event: { target: { value: string; name?: string } }) => void;
  children?: React.ReactNode;
}

function parseOptions(children: React.ReactNode): ParsedOption[] {
  const options: ParsedOption[] = [];
  React.Children.forEach(children, (child) => {
    if (!React.isValidElement(child)) return;
    const props = child.props as {
      value?: string | number;
      disabled?: boolean;
      children?: React.ReactNode;
    };
    if (child.type === "option") {
      const text =
        typeof props.children === "string" || typeof props.children === "number"
          ? String(props.children)
          : React.Children.toArray(props.children).join("");
      options.push({
        value: props.value !== undefined ? String(props.value) : text,
        label: text,
        disabled: Boolean(props.disabled),
      });
    } else if (props.children) {
      options.push(...parseOptions(props.children));
    }
  });
  return options;
}

/**
 * Modern custom Select dropdown (Linear/Raycast style) with keyboard navigation,
 * crisp charcoal dark-mode popover menu, checkmark indicator, and full
 * backwards-compatible `<option>` children API.
 */
export function SelectField({
  id,
  name,
  value,
  defaultValue,
  required,
  disabled = false,
  hasError = false,
  className,
  placeholder = "Select an option",
  "aria-label": ariaLabel,
  onChange,
  children,
}: SelectFieldProps) {
  const options = React.useMemo(() => parseOptions(children), [children]);
  const [internalValue, setInternalValue] = React.useState(defaultValue ?? "");
  const [open, setOpen] = React.useState(false);
  const [activeIndex, setActiveIndex] = React.useState<number>(-1);
  const containerRef = React.useRef<HTMLDivElement>(null);

  const currentValue = value !== undefined ? value : internalValue;
  const selectedOption = options.find((opt) => opt.value === currentValue);

  React.useEffect(() => {
    if (!open) return;
    function handleOutside(e: MouseEvent) {
      if (
        containerRef.current &&
        !containerRef.current.contains(e.target as Node)
      ) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", handleOutside);
    return () => document.removeEventListener("mousedown", handleOutside);
  }, [open]);

  function selectOption(opt: ParsedOption) {
    if (opt.disabled) return;
    if (value === undefined) {
      setInternalValue(opt.value);
    }
    onChange?.({ target: { value: opt.value, name } });
    setOpen(false);
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLButtonElement>) {
    if (disabled) return;
    if (e.key === "Escape") {
      setOpen(false);
      return;
    }
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      if (!open) {
        setOpen(true);
        const idx = options.findIndex((o) => o.value === currentValue);
        setActiveIndex(idx >= 0 ? idx : 0);
      } else if (activeIndex >= 0 && options[activeIndex]) {
        selectOption(options[activeIndex]);
      }
      return;
    }
    if (e.key === "ArrowDown") {
      e.preventDefault();
      if (!open) {
        setOpen(true);
        setActiveIndex(0);
      } else {
        setActiveIndex((prev) => (prev + 1) % Math.max(options.length, 1));
      }
      return;
    }
    if (e.key === "ArrowUp") {
      e.preventDefault();
      if (!open) {
        setOpen(true);
        setActiveIndex(Math.max(options.length - 1, 0));
      } else {
        setActiveIndex(
          (prev) => (prev - 1 + options.length) % Math.max(options.length, 1)
        );
      }
    }
  }

  return (
    <div ref={containerRef} className={cn("relative w-full", className)}>
      {name && (
        <input
          type="hidden"
          name={name}
          value={currentValue}
          required={required}
        />
      )}
      <button
        id={id}
        type="button"
        role="combobox"
        aria-expanded={open}
        aria-haspopup="listbox"
        aria-label={ariaLabel}
        aria-invalid={hasError || undefined}
        disabled={disabled}
        onClick={() => {
          if (disabled) return;
          setOpen((prev) => !prev);
          const idx = options.findIndex((o) => o.value === currentValue);
          setActiveIndex(idx >= 0 ? idx : 0);
        }}
        onKeyDown={handleKeyDown}
        className={cn(
          "flex h-11 w-full items-center justify-between gap-2 rounded-xl border border-transparent bg-zinc-100 px-3.5 py-2 text-left text-sm text-foreground transition-all duration-150 hover:bg-zinc-200/70 focus-visible:border-zinc-300 focus-visible:bg-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring/40 disabled:cursor-not-allowed disabled:opacity-50 cursor-pointer",
          "dark:bg-[#1B1B1F] dark:text-zinc-100 dark:hover:bg-[#222227] dark:focus-visible:border-white/15 dark:focus-visible:bg-[#1F1F24] dark:focus-visible:ring-primary/35",
          open && "border-zinc-300 bg-white dark:border-white/15 dark:bg-[#1F1F24]",
          hasError && "border-destructive/60"
        )}
      >
        <span
          className={cn(
            "truncate",
            !selectedOption?.value && "text-muted-foreground"
          )}
        >
          {selectedOption ? selectedOption.label : placeholder}
        </span>
        <ChevronDown
          className={cn(
            "h-4 w-4 shrink-0 text-muted-foreground transition-transform duration-150",
            open && "rotate-180 text-foreground"
          )}
        />
      </button>

      {open && (
        <div
          role="listbox"
          className="absolute left-0 right-0 z-50 mt-1.5 max-h-64 overflow-y-auto rounded-xl border border-border bg-popover p-1 text-popover-foreground shadow-xl shadow-black/15 dark:border-white/[0.1] dark:bg-[#16161A] dark:shadow-[0_18px_40px_rgba(0,0,0,0.75)]"
        >
          {options.length === 0 ? (
            <div className="px-3 py-2 text-xs text-muted-foreground">
              No options available
            </div>
          ) : (
            options.map((opt, idx) => {
              const isSelected = opt.value === currentValue;
              const isHighlighted = idx === activeIndex;
              return (
                <button
                  key={`${opt.value}-${idx}`}
                  type="button"
                  role="option"
                  aria-selected={isSelected}
                  disabled={opt.disabled}
                  onMouseEnter={() => setActiveIndex(idx)}
                  onClick={() => selectOption(opt)}
                  className={cn(
                    "flex w-full items-center justify-between gap-2 rounded-lg px-3 py-2 text-left text-sm transition-colors cursor-pointer",
                    isSelected
                      ? "bg-primary/12 font-semibold text-primary dark:bg-primary/15 dark:text-primary"
                      : isHighlighted
                      ? "bg-muted text-foreground dark:bg-white/[0.06]"
                      : "text-foreground/90 hover:bg-muted dark:hover:bg-white/[0.06]",
                    opt.disabled && "pointer-events-none opacity-40"
                  )}
                >
                  <span className="truncate">{opt.label}</span>
                  {isSelected && (
                    <Check className="h-3.5 w-3.5 shrink-0 text-primary" />
                  )}
                </button>
              );
            })
          )}
        </div>
      )}
    </div>
  );
}
