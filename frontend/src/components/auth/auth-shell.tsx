"use client";

import * as React from "react";
import Image from "next/image";
import Link from "next/link";
import { ArrowLeft, ShieldCheck } from "lucide-react";
import { KlasraLogo } from "@/components/brand/klasra-logo";
import { ThemeToggle } from "@/components/theme-toggle";

interface AuthShellProps {
  title: string;
  subtitle: string;
  badge?: string;
  imageSrc?: string;
  imageAlt?: string;
  asideHeading?: string;
  asideDescription?: string;
  children: React.ReactNode;
  footer?: React.ReactNode;
}

export function AuthShell({
  title,
  subtitle,
  badge,
  imageSrc = "/images/hero-classroom.jpg",
  imageAlt = "Secondary school classroom using Klasra",
  asideHeading = "One calm, structured workspace for every secondary school.",
  asideDescription = "Lessons, video learning, timed quizzes and exams, attendance, and verified multi-school parent access — strictly isolated per school.",
  children,
  footer,
}: AuthShellProps) {
  return (
    <div className="grid min-h-screen bg-background lg:grid-cols-12">
      {/* Left Editorial Visual Column (Desktop lg+) */}
      <aside className="relative hidden overflow-hidden border-r border-border bg-[#0C0C0E] lg:col-span-6 lg:flex lg:flex-col lg:justify-between xl:col-span-7">
        <Image
          src={imageSrc}
          alt={imageAlt}
          fill
          priority
          sizes="50vw"
          className="object-cover opacity-55"
        />
        <div className="pointer-events-none absolute inset-0 bg-gradient-to-t from-[#0A0A0B] via-[#0A0A0B]/55 to-[#0A0A0B]/35" />

        {/* Top Brand Mark */}
        <div className="relative z-10 flex items-center justify-between p-8">
          <Link href="/" aria-label="Klasra Home">
            <KlasraLogo inverted />
          </Link>
        </div>

        {/* Bottom Editorial Copy */}
        <div className="relative z-10 max-w-lg p-8 pb-10">
          <div className="mb-3 inline-flex items-center gap-2 rounded-full border border-white/15 bg-black/40 px-3 py-1 text-xs font-medium text-zinc-200 backdrop-blur-sm">
            <ShieldCheck className="h-3.5 w-3.5 text-emerald-400" />
            <span>School-Scoped &amp; Audited</span>
          </div>
          <h2 className="font-display text-2xl font-bold leading-snug tracking-tight text-white">
            {asideHeading}
          </h2>
          <p className="mt-2.5 text-sm leading-relaxed text-zinc-300">
            {asideDescription}
          </p>
        </div>
      </aside>

      {/* Right Form Column */}
      <div className="flex flex-col lg:col-span-6 xl:col-span-5">
        <header className="flex items-center justify-between px-4 py-5 sm:px-8">
          <Link href="/" className="lg:invisible" aria-label="Klasra Home">
            <KlasraLogo />
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

        <main className="flex flex-1 items-center justify-center px-4 py-6 sm:px-8 lg:px-8 xl:px-10">
          <div className="w-full max-w-[500px]">
            <div className="rounded-2xl border border-border bg-card p-6 shadow-sm dark:border-white/[0.08] dark:bg-[#141416] sm:p-7">
              {badge && (
                <p className="mb-2 text-xs font-semibold uppercase tracking-wider text-primary">
                  {badge}
                </p>
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
          </div>
        </main>
      </div>
    </div>
  );
}
