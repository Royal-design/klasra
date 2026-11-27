"use client";

import * as React from "react";
import Image from "next/image";
import { AnimatePresence, motion } from "framer-motion";
import {
  Building2,
  CheckCircle2,
  GraduationCap,
  HeartHandshake,
  Presentation,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";

type RoleKey = "admin" | "teacher" | "student" | "parent";

const ROLES: Record<
  RoleKey,
  {
    label: string;
    icon: React.ComponentType<{ className?: string }>;
    headline: string;
    summary: string;
    bullets: string[];
    highlightStat: string;
    highlightLabel: string;
  }
> = {
  admin: {
    label: "School Admin",
    icon: Building2,
    headline: "Run your entire school structure from one clean hub.",
    summary:
      "Configure academic years, terms, class groups, and custom terminology. Onboard teachers via email invites, approve student registrations, and manage parent links.",
    bullets: [
      "Bulk import students & staff via CSV/XLSX with dry-run error previews",
      "Approve or reject student self-registrations before granting access",
      "Transfer or withdraw students while preserving full historical records",
      "Full audit trail on every role, enrollment, and guardian decision",
    ],
    highlightStat: "100%",
    highlightLabel: "School-scoped isolation",
  },
  teacher: {
    label: "Teacher",
    icon: Presentation,
    headline: "Focus on teaching — not fighting clunky spreadsheets.",
    summary:
      "See only your assigned subject offerings. Publish lessons with video and files, review versioned submissions in a split-screen drawer, and take roll call in seconds.",
    bullets: [
      "Upload lesson videos (up to 50 MB) or embed YouTube, Vimeo & Loom",
      "Per-assignment late submission & resubmission controls",
      "Draft grades privately and publish to students & parents when ready",
      "Fast batch attendance roll call with automatic staff attribution",
    ],
    highlightStat: "1 School",
    highlightLabel: "Focused teacher workspace",
  },
  student: {
    label: "Student",
    icon: GraduationCap,
    headline: "A calm, mobile-friendly classroom that keeps you on track.",
    summary:
      "Access published lessons and videos, submit assignments with clear version history, and review your own published grades, teacher feedback, and attendance.",
    bullets: [
      "Watch lesson videos and download materials securely on any device",
      "Submit typed responses and files with instant confirmation",
      "Track every resubmission version and read teacher feedback clearly",
      "Private by design — students never see classmates' submissions or marks",
    ],
    highlightStat: "360px+",
    highlightLabel: "Mobile-first student UX",
  },
  parent: {
    label: "Parent / Guardian",
    icon: HeartHandshake,
    headline: "Follow every child's progress — even across different schools.",
    summary:
      "One parent account links to all your approved children across participating schools. Check published grades, teacher feedback, and daily attendance anytime.",
    bullets: [
      "Single login across multiple schools with one-click child switcher",
      "Verified email + school admin approval protects every child's privacy",
      "View published grades, teacher comments, and full attendance history",
      "Instant access revocation handled cleanly by school administrators",
    ],
    highlightStat: "Multi-School",
    highlightLabel: "One unified parent login",
  },
};

export function RoleShowcase() {
  const [activeRole, setActiveRole] = React.useState<RoleKey>("parent");
  const current = ROLES[activeRole];

  return (
    <section
      id="roles"
      className="border-y border-border/60 bg-muted/40 py-20 dark:bg-muted/20"
    >
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-2xl text-center">
          <Badge variant="default" className="mb-3">
            Tailored Portals
          </Badge>
          <h2 className="font-display text-3xl font-extrabold tracking-tight text-foreground sm:text-4xl">
            Designed around every role in a secondary school.
          </h2>
          <p className="mt-3 text-base text-muted-foreground">
            Switch tabs to see how ScholarGrid adapts to administrators, teachers,
            students, and families.
          </p>
        </div>

        {/* Animated Role Tabs */}
        <div className="mt-10 flex flex-wrap justify-center gap-2">
          {(Object.keys(ROLES) as RoleKey[]).map((key) => {
            const role = ROLES[key];
            const Icon = role.icon;
            const isActive = activeRole === key;
            return (
              <button
                key={key}
                type="button"
                onClick={() => setActiveRole(key)}
                className={`relative flex items-center gap-2 rounded-full px-5 py-2.5 text-sm font-semibold transition-colors cursor-pointer ${
                  isActive
                    ? "text-primary-foreground"
                    : "text-muted-foreground hover:text-foreground"
                }`}
              >
                {isActive && (
                  <motion.span
                    layoutId="active-role-pill"
                    transition={{ type: "spring", stiffness: 380, damping: 30 }}
                    className="absolute inset-0 rounded-full bg-primary shadow-md shadow-primary/25"
                  />
                )}
                <Icon className="relative z-10 h-4 w-4" />
                <span className="relative z-10">{role.label}</span>
              </button>
            );
          })}
        </div>

        {/* Tab Content */}
        <div className="mt-10 grid items-center gap-8 rounded-3xl border border-border bg-card p-6 shadow-xl shadow-slate-900/5 dark:shadow-black/30 sm:p-10 lg:grid-cols-12">
          <div className="lg:col-span-7">
            <AnimatePresence mode="wait">
              <motion.div
                key={activeRole}
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -12 }}
                transition={{ duration: 0.25 }}
              >
                <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-secondary/25 bg-secondary/10 px-3 py-1 text-xs font-semibold text-secondary">
                  <span>{current.highlightStat}</span>
                  <span className="opacity-60">·</span>
                  <span>{current.highlightLabel}</span>
                </div>
                <h3 className="font-display text-2xl font-extrabold tracking-tight text-foreground sm:text-3xl">
                  {current.headline}
                </h3>
                <p className="mt-3 text-sm leading-relaxed text-muted-foreground sm:text-base">
                  {current.summary}
                </p>
                <ul className="mt-6 space-y-3">
                  {current.bullets.map((bullet) => (
                    <li
                      key={bullet}
                      className="flex items-start gap-3 text-sm text-foreground"
                    >
                      <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-secondary" />
                      <span>{bullet}</span>
                    </li>
                  ))}
                </ul>
              </motion.div>
            </AnimatePresence>
          </div>

          <div className="lg:col-span-5">
            <div className="relative overflow-hidden rounded-2xl border border-border bg-muted/50">
              <div className="relative aspect-[4/3] w-full">
                <Image
                  src="/images/parent-student.jpg"
                  alt="Parent and teenager reviewing school progress together on a laptop"
                  fill
                  sizes="(max-width: 1024px) 100vw, 40vw"
                  className="object-cover"
                />
                <div className="absolute inset-0 bg-gradient-to-t from-slate-950/65 via-transparent to-transparent" />
                <div className="absolute bottom-3 left-3 right-3 rounded-xl border border-white/15 bg-slate-950/70 px-3.5 py-2.5 text-white backdrop-blur-md">
                  <p className="text-xs font-semibold">
                    Verified Family &amp; Classroom Visibility
                  </p>
                  <p className="text-[11px] text-slate-300">
                    Real-time published grades, feedback &amp; attendance history.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
