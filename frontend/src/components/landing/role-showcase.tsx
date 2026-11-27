"use client";

import * as React from "react";
import Image from "next/image";
import {
  Building2,
  CheckCircle2,
  GraduationCap,
  HeartHandshake,
  Presentation,
} from "lucide-react";
import { cn } from "@/lib/utils";

type RoleKey = "admin" | "teacher" | "student" | "parent";

const ROLES: Record<
  RoleKey,
  {
    label: string;
    icon: React.ComponentType<{ className?: string }>;
    headline: string;
    summary: string;
    bullets: string[];
  }
> = {
  admin: {
    label: "School Admin",
    icon: Building2,
    headline: "Configure academic structure and govern access with clarity.",
    summary:
      "Manage academic years, terms, year levels, class groups, and subject offerings. Onboard staff via email invitations and review student or parent requests before granting access.",
    bullets: [
      "CSV and XLSX roster import with dry-run error validation before commit",
      "Pending student self-registration queue with one-click approve or reject",
      "History-preserving student transfers and withdrawals across terms",
      "Audit trail for every role change, enrollment, and guardian approval",
    ],
  },
  teacher: {
    label: "Teacher",
    icon: Presentation,
    headline: "A focused workspace scoped strictly to your assigned classes.",
    summary:
      "Publish lessons with videos and materials, build assignments, quizzes, and timed exams, grade submissions privately in draft mode, and record daily attendance.",
    bullets: [
      "Upload lesson videos up to 50 MB or embed YouTube, Vimeo, and Loom",
      "Combine auto-graded objective questions with manually graded essays",
      "Control late submissions, resubmissions, and score release timing",
      "Record batch attendance with automatic staff attribution and timestamps",
    ],
  },
  student: {
    label: "Student",
    icon: GraduationCap,
    headline: "Clear coursework, timed assessments, and private progress.",
    summary:
      "Review published lessons, submit assignments with version history, take timed quizzes and exams, and track your published grades and attendance.",
    bullets: [
      "Responsive 360px+ layout designed for phones, tablets, and laptops",
      "Track submission versions and read teacher feedback in one place",
      "Take timed quizzes and exams with automatic server deadline checks",
      "Strict privacy — students only ever see their own submissions and marks",
    ],
  },
  parent: {
    label: "Parent / Guardian",
    icon: HeartHandshake,
    headline: "Verified visibility across every child and every school.",
    summary:
      "Use a single parent account to follow approved children across different schools, viewing published grades, quiz and exam scores, teacher feedback, and attendance.",
    bullets: [
      "One parent login across multiple participating secondary schools",
      "Email verification plus School Admin approval before any record is visible",
      "Published grades, assessment results, teacher comments, and attendance",
      "Immediate access revocation managed by school administrators",
    ],
  },
};

export function RoleShowcase() {
  const [activeRole, setActiveRole] = React.useState<RoleKey>("parent");
  const current = ROLES[activeRole];

  return (
    <section
      id="roles"
      className="border-y border-border bg-card/50 py-20 dark:bg-[#0E0E10]"
    >
      <div className="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8">
        <div className="flex flex-col justify-between gap-6 md:flex-row md:items-end">
          <div className="max-w-xl">
            <p className="text-xs font-semibold uppercase tracking-wider text-primary">
              Role-Based Portals
            </p>
            <h2 className="mt-2 font-display text-3xl font-bold tracking-tight text-foreground">
              Purpose-built for every person in the school community.
            </h2>
          </div>

          <div
            role="tablist"
            aria-label="LMS user roles"
            className="inline-flex flex-wrap gap-1 rounded-xl border border-border bg-background p-1"
          >
            {(Object.keys(ROLES) as RoleKey[]).map((key) => {
              const role = ROLES[key];
              const Icon = role.icon;
              const isActive = activeRole === key;
              return (
                <button
                  key={key}
                  type="button"
                  role="tab"
                  aria-selected={isActive}
                  onClick={() => setActiveRole(key)}
                  className={cn(
                    "inline-flex items-center gap-2 rounded-lg px-3.5 py-2 text-xs font-semibold transition-colors cursor-pointer",
                    isActive
                      ? "bg-primary text-primary-foreground"
                      : "text-muted-foreground hover:text-foreground"
                  )}
                >
                  <Icon className="h-3.5 w-3.5" />
                  <span>{role.label}</span>
                </button>
              );
            })}
          </div>
        </div>

        <div className="mt-10 grid items-center gap-8 rounded-2xl border border-border bg-card p-6 sm:p-8 lg:grid-cols-12">
          <div className="lg:col-span-7">
            <h3 className="font-display text-2xl font-bold tracking-tight text-foreground">
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
                  <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-emerald-500" />
                  <span>{bullet}</span>
                </li>
              ))}
            </ul>
          </div>

          <div className="lg:col-span-5">
            <div className="overflow-hidden rounded-xl border border-border bg-muted">
              <div className="relative aspect-[4/3] w-full">
                <Image
                  src="/images/parent-student.jpg"
                  alt="Parent and secondary school student reviewing academic progress together"
                  fill
                  sizes="(max-width: 1024px) 100vw, 40vw"
                  className="object-cover"
                />
              </div>
              <div className="border-t border-border bg-card px-4 py-3">
                <p className="text-xs font-semibold text-foreground">
                  Transparent Family &amp; Classroom Progress
                </p>
                <p className="mt-0.5 text-xs text-muted-foreground">
                  Published grades, quiz &amp; exam results, and daily attendance.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
