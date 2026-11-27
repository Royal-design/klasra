import * as React from "react";
import { cn } from "@/lib/utils";

export interface SelectFieldProps
  extends React.SelectHTMLAttributes<HTMLSelectElement> {
  hasError?: boolean;
}

const SelectField = React.forwardRef<HTMLSelectElement, SelectFieldProps>(
  ({ className, hasError = false, children, ...props }, ref) => (
    <select
      ref={ref}
      aria-invalid={hasError || undefined}
      className={cn(
        "flex h-11 w-full rounded-xl border border-transparent bg-zinc-100 px-3.5 py-2 text-sm text-foreground transition-all duration-150 hover:bg-zinc-200/70 focus-visible:border-zinc-300 focus-visible:bg-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring/40 disabled:cursor-not-allowed disabled:opacity-50",
        "dark:bg-[#1B1B1F] dark:text-zinc-100 dark:hover:bg-[#222227] dark:focus-visible:border-white/15 dark:focus-visible:bg-[#1F1F24] dark:focus-visible:ring-primary/35",
        hasError && "border-destructive/60",
        className
      )}
      {...props}
    >
      {children}
    </select>
  )
);
SelectField.displayName = "SelectField";

export { SelectField };
