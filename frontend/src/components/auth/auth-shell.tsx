"use client";

import * as React from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import { ArrowLeft, GraduationCap } from "lucide-react";
import { ThemeToggle } from "@/components/theme-toggle";

interface AuthShellProps {
  title: string;
  subtitle: string;
  badge?: string;
  children: React.ReactNode;
  footer?: React.ReactNode;
}

export function AuthShell({
  title,
  subtitle,
  badge,
  children,
  footer,
}: AuthShellProps) {
  return (
    <div className="relative flex min-h-screen flex-col overflow-hidden bg-background">
      {/* Subtle neutral radial highlight — Linear/Raycast restraint */}
      <div className="pointer-events-none absolute inset-0 bg-scholarly-grid opacity-30 dark:opacity-20" />
      <div className="pointer-events-none absolute -top-40 left-1/2 h-[340px] w-[540px] -translate-x-1/2 rounded-full bg-primary/10 blur-3xl dark:bg-primary/12" />

      <header className="relative z-10 mx-auto flex w-full max-w-5xl items-center justify-between px-4 py-5 sm:px-6">
        <Link href="/" className="group flex items-center gap-2.5">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-primary text-primary-foreground shadow-sm">
            <GraduationCap className="h-5 w-5" />
          </div>
          <span className="font-display text-base font-bold tracking-tight text-foreground">
            ScholarGrid
          </span>
        </Link>

        <div className="flex items-center gap-3">
          <Link
            href="/"
            className="inline-flex items-center gap-1.5 text-xs font-medium text-muted-foreground transition-colors hover:text-foreground"
          >
            <ArrowLeft className="h-3.5 w-3.5" />
            Home
          </Link>
          <ThemeToggle />
        </div>
      </header>

      <main className="relative z-10 flex flex-1 items-center justify-center px-4 py-8 sm:px-6">
        <motion.div
          initial={{ opacity: 0, y: 14 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.35, ease: [0.22, 1, 0.36, 1] }}
          className="w-full max-w-md"
        >
          <div className="rounded-3xl border border-border bg-card p-6 shadow-xl shadow-black/[0.04] dark:border-white/[0.08] dark:bg-[#141416] dark:shadow-[0_24px_64px_rgba(0,0,0,0.65),inset_0_1px_0_0_rgba(255,255,255,0.05)] sm:p-8">
            {badge && (
              <span className="mb-3 inline-flex items-center rounded-full border border-border bg-muted px-3 py-1 text-[11px] font-semibold tracking-wide text-muted-foreground dark:border-white/10 dark:bg-white/[0.04] dark:text-zinc-300">
                {badge}
              </span>
            )}
            <h1 className="font-display text-2xl font-bold tracking-tight text-foreground">
              {title}
            </h1>
            <p className="mt-1.5 text-sm leading-relaxed text-muted-foreground">
              {subtitle}
            </p>

            <div className="mt-6">{children}</div>
          </div>

          {footer && (
            <div className="mt-5 text-center text-sm text-muted-foreground">
              {footer}
            </div>
          )}
        </motion.div>
      </main>
    </div>
  );
}
