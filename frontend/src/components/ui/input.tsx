import * as React from "react";
import { cn } from "@/lib/utils";

export interface InputProps
  extends React.InputHTMLAttributes<HTMLInputElement> {
  hasError?: boolean;
}

const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, type, hasError = false, ...props }, ref) => {
    return (
      <input
        type={type}
        aria-invalid={hasError || undefined}
        className={cn(
          "flex h-11 w-full rounded-xl border border-transparent bg-zinc-100 px-4 py-2.5 text-sm text-foreground transition-all duration-150 placeholder:text-zinc-400 hover:bg-zinc-200/70 focus-visible:border-zinc-300 focus-visible:bg-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring/40 disabled:cursor-not-allowed disabled:opacity-50",
          "dark:bg-[#1B1B1F] dark:text-zinc-100 dark:placeholder:text-zinc-500 dark:hover:bg-[#222227] dark:focus-visible:border-white/15 dark:focus-visible:bg-[#1F1F24] dark:focus-visible:ring-primary/35",
          hasError &&
            "border-destructive/60 bg-destructive/5 focus-visible:border-destructive focus-visible:ring-destructive/30 dark:border-destructive/60 dark:bg-destructive/10",
          className
        )}
        ref={ref}
        {...props}
      />
    );
  }
);
Input.displayName = "Input";

export { Input };
