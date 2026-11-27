"use client";

import * as React from "react";
import {
  BookOpen,
  CalendarCheck2,
  CheckCircle2,
  ClipboardCheck,
  Clock,
  FileText,
  HeartHandshake,
  Lock,
  Play,
} from "lucide-react";
import { cn } from "@/lib/utils";

type PreviewTab = "classroom" | "assessment" | "parent";

const TABS: Array<{
  id: PreviewTab;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
}> = [
  { id: "classroom", label: "Lessons & Video", icon: BookOpen },
  { id: "assessment", label: "Quizzes & Grading", icon: ClipboardCheck },
  { id: "parent", label: "Parent & Attendance", icon: HeartHandshake },
];

export function ProductPreview() {
  const [activeTab, setActiveTab] = React.useState<PreviewTab>("classroom");

  return (
    <div className="overflow-hidden rounded-2xl border border-border bg-card shadow-[0_20px_50px_-24px_rgba(0,0,0,0.22)] dark:border-white/[0.09] dark:bg-[#121215] dark:shadow-[0_28px_64px_-24px_rgba(0,0,0,0.85),inset_0_1px_0_0_rgba(255,255,255,0.05)]">
      {/* Window Chrome + Interactive View Switcher */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border bg-muted/60 px-4 py-3 dark:bg-[#17171B]">
        <div className="flex items-center gap-2">
          <span className="h-2.5 w-2.5 rounded-full bg-zinc-300 dark:bg-zinc-700" />
          <span className="h-2.5 w-2.5 rounded-full bg-zinc-300 dark:bg-zinc-700" />
          <span className="h-2.5 w-2.5 rounded-full bg-zinc-300 dark:bg-zinc-700" />
          <span className="ml-2 font-mono text-[11px] font-medium text-muted-foreground">
            Interactive Workspace Preview
          </span>
        </div>

        <div
          role="tablist"
          aria-label="Klasra workspace preview views"
          className="inline-flex rounded-lg border border-border bg-background p-0.5 dark:bg-[#0E0E11]"
        >
          {TABS.map((tab) => {
            const Icon = tab.icon;
            const selected = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                type="button"
                role="tab"
                aria-selected={selected}
                onClick={() => setActiveTab(tab.id)}
                className={cn(
                  "inline-flex items-center gap-1.5 rounded-md px-2.5 py-1.5 text-xs font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring cursor-pointer",
                  selected
                    ? "bg-card text-foreground shadow-xs dark:bg-[#222228]"
                    : "text-muted-foreground hover:text-foreground"
                )}
              >
                <Icon className="h-3.5 w-3.5" />
                <span className="hidden sm:inline">{tab.label}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Preview Canvas */}
      <div className="p-5 sm:p-6">
        {activeTab === "classroom" && (
          <div className="grid gap-5 md:grid-cols-12">
            {/* Left Lesson Pathway */}
            <div className="space-y-3 md:col-span-5">
              <div className="flex items-center justify-between">
                <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  PHY201 · Term 1 Pathway
                </p>
                <span className="rounded-full bg-emerald-500/12 px-2 py-0.5 font-mono text-[11px] font-medium text-emerald-700 dark:text-emerald-300">
                  Published
                </span>
              </div>

              {[
                {
                  week: "Unit 01",
                  title: "Kinematics & Velocity Graphs",
                  meta: "Video (14 min) · Worksheet PDF",
                  active: true,
                },
                {
                  week: "Unit 02",
                  title: "Newton's Laws of Motion",
                  meta: "Lesson Notes · Practice Quiz",
                  active: false,
                },
                {
                  week: "Unit 03",
                  title: "Work, Energy & Power",
                  meta: "Draft · Teacher Only",
                  active: false,
                },
              ].map((unit) => (
                <div
                  key={unit.week}
                  className={cn(
                    "rounded-xl border p-3.5 transition-colors",
                    unit.active
                      ? "border-primary/40 bg-primary/[0.04] dark:bg-primary/[0.08]"
                      : "border-border bg-background/60 dark:bg-[#17171B]"
                  )}
                >
                  <div className="flex items-center justify-between text-[11px] font-mono text-muted-foreground">
                    <span>{unit.week}</span>
                    {unit.active && (
                      <span className="text-primary font-semibold">Current</span>
                    )}
                  </div>
                  <p className="mt-1 text-sm font-semibold text-foreground">
                    {unit.title}
                  </p>
                  <p className="mt-0.5 text-xs text-muted-foreground">
                    {unit.meta}
                  </p>
                </div>
              ))}
            </div>

            {/* Right Active Lesson & Private Materials */}
            <div className="flex flex-col justify-between rounded-xl border border-border bg-background/70 p-4 dark:bg-[#17171B] md:col-span-7">
              <div>
                <div className="flex items-center justify-between gap-2">
                  <span className="font-mono text-xs text-primary">
                    UNIT 01 · LESSON
                  </span>
                  <span className="inline-flex items-center gap-1 text-xs text-muted-foreground">
                    <Lock className="h-3 w-3" />
                    Private Signed Stream
                  </span>
                </div>
                <h3 className="mt-1.5 font-display text-lg font-bold text-foreground">
                  Kinematics &amp; Velocity-Time Graphs
                </h3>
                <p className="mt-1 text-xs leading-relaxed text-muted-foreground">
                  Watch the recorded classroom walkthrough, review the worked
                  examples, and download the practice sheet before Friday&apos;s
                  timed quiz.
                </p>

                {/* Video Player Mock */}
                <div className="mt-4 flex items-center justify-between rounded-xl border border-border bg-[#0D0D10] p-4 text-zinc-100">
                  <div className="flex items-center gap-3">
                    <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary text-white">
                      <Play className="h-4 w-4 fill-current" />
                    </div>
                    <div>
                      <p className="text-xs font-semibold text-white">
                        kinematics_walkthrough.mp4
                      </p>
                      <p className="font-mono text-[11px] text-zinc-400">
                        14:20 · 38 MB · Direct Playback URL
                      </p>
                    </div>
                  </div>
                  <span className="hidden rounded-md border border-white/10 bg-white/[0.06] px-2 py-1 font-mono text-[10px] text-zinc-300 sm:inline-block">
                    HD
                  </span>
                </div>
              </div>

              <div className="mt-4 flex flex-wrap items-center justify-between gap-2 border-t border-border pt-3">
                <div className="inline-flex items-center gap-2 text-xs font-medium text-foreground">
                  <FileText className="h-3.5 w-3.5 text-muted-foreground" />
                  <span>velocity_problems.pdf</span>
                  <span className="font-mono text-[11px] text-muted-foreground">
                    1.8 MB
                  </span>
                </div>
                <span className="rounded-md border border-border bg-card px-2.5 py-1 text-[11px] font-medium text-muted-foreground">
                  Enrolled Students Only
                </span>
              </div>
            </div>
          </div>
        )}

        {activeTab === "assessment" && (
          <div className="grid gap-5 md:grid-cols-12">
            <div className="space-y-3 md:col-span-7">
              <div className="flex items-center justify-between">
                <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  Timed Assessment · Term 1 CA
                </p>
                <span className="inline-flex items-center gap-1 font-mono text-xs text-amber-600 dark:text-amber-400">
                  <Clock className="h-3.5 w-3.5" />
                  30 min limit · 1 attempt
                </span>
              </div>

              <div className="rounded-xl border border-border bg-background/70 p-4 dark:bg-[#17171B]">
                <div className="flex items-center justify-between text-xs text-muted-foreground">
                  <span className="font-mono">Q1 · Multiple Choice</span>
                  <span className="font-mono text-emerald-600 dark:text-emerald-400">
                    Auto-graded · 5 pts
                  </span>
                </div>
                <p className="mt-2 text-sm font-medium text-foreground">
                  The gradient of a velocity-time graph represents which
                  physical quantity?
                </p>
                <div className="mt-3 grid grid-cols-2 gap-2 text-xs">
                  <div className="rounded-lg border border-border bg-card px-3 py-2 text-muted-foreground">
                    A. Displacement
                  </div>
                  <div className="rounded-lg border border-primary/50 bg-primary/10 px-3 py-2 font-medium text-foreground">
                    B. Acceleration
                  </div>
                </div>
              </div>

              <div className="rounded-xl border border-border bg-background/70 p-4 dark:bg-[#17171B]">
                <div className="flex items-center justify-between text-xs text-muted-foreground">
                  <span className="font-mono">Q2 · Short Answer</span>
                  <span className="font-mono text-primary">
                    Teacher-graded · 10 pts
                  </span>
                </div>
                <p className="mt-2 text-sm font-medium text-foreground">
                  Explain the difference between uniform velocity and uniform
                  acceleration.
                </p>
              </div>
            </div>

            <div className="flex flex-col justify-between rounded-xl border border-border bg-background/70 p-4 dark:bg-[#17171B] md:col-span-5">
              <div>
                <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  Draft-to-Publish Grading
                </p>
                <h3 className="mt-1.5 font-display text-base font-bold text-foreground">
                  Release results only when ready
                </h3>
                <p className="mt-1 text-xs leading-relaxed text-muted-foreground">
                  Objective questions score automatically on submission. Essay
                  answers stay in teacher review until you publish final marks
                  and comments.
                </p>
              </div>

              <div className="mt-5 space-y-2.5 border-t border-border pt-4 text-xs">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Auto-graded</span>
                  <span className="font-mono font-semibold text-foreground">
                    15 / 15
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Manual review</span>
                  <span className="font-mono font-semibold text-foreground">
                    9 / 10
                  </span>
                </div>
                <div className="flex items-center justify-between border-t border-border pt-2.5">
                  <span className="font-semibold text-foreground">
                    Published Total
                  </span>
                  <span className="rounded-md bg-emerald-500/12 px-2 py-0.5 font-mono font-bold text-emerald-700 dark:text-emerald-300">
                    24 / 25
                  </span>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === "parent" && (
          <div className="grid gap-5 md:grid-cols-12">
            <div className="space-y-3 md:col-span-5">
              <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                Approved Linked Children
              </p>
              <div className="rounded-xl border border-primary/40 bg-primary/[0.04] p-3.5 dark:bg-primary/[0.08]">
                <div className="flex items-center justify-between">
                  <p className="text-sm font-semibold text-foreground">
                    Child A · Senior Secondary
                  </p>
                  <span className="rounded-full bg-emerald-500/12 px-2 py-0.5 text-[11px] font-medium text-emerald-700 dark:text-emerald-300">
                    Approved
                  </span>
                </div>
                <p className="mt-0.5 text-xs text-muted-foreground">
                  School Campus 1 · Guardian Link Verified
                </p>
              </div>
              <div className="rounded-xl border border-border bg-background/60 p-3.5 dark:bg-[#17171B]">
                <div className="flex items-center justify-between">
                  <p className="text-sm font-semibold text-foreground">
                    Child B · Junior Secondary
                  </p>
                  <span className="rounded-full bg-emerald-500/12 px-2 py-0.5 text-[11px] font-medium text-emerald-700 dark:text-emerald-300">
                    Approved
                  </span>
                </div>
                <p className="mt-0.5 text-xs text-muted-foreground">
                  School Campus 2 · Same Parent Account
                </p>
              </div>
            </div>

            <div className="flex flex-col justify-between rounded-xl border border-border bg-background/70 p-4 dark:bg-[#17171B] md:col-span-7">
              <div>
                <div className="flex items-center justify-between">
                  <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                    Recent Attendance &amp; Feedback
                  </p>
                  <CalendarCheck2 className="h-4 w-4 text-muted-foreground" />
                </div>

                <div className="mt-3 grid grid-cols-4 gap-2 text-center text-xs">
                  {[
                    { day: "Mon", status: "Present", tone: "text-emerald-600 dark:text-emerald-400" },
                    { day: "Tue", status: "Present", tone: "text-emerald-600 dark:text-emerald-400" },
                    { day: "Wed", status: "Late", tone: "text-amber-600 dark:text-amber-400" },
                    { day: "Thu", status: "Present", tone: "text-emerald-600 dark:text-emerald-400" },
                  ].map((d) => (
                    <div
                      key={d.day}
                      className="rounded-lg border border-border bg-card px-2 py-2.5"
                    >
                      <p className="font-mono text-[11px] text-muted-foreground">
                        {d.day}
                      </p>
                      <p className={cn("mt-1 font-semibold", d.tone)}>
                        {d.status}
                      </p>
                    </div>
                  ))}
                </div>
              </div>

              <div className="mt-4 flex items-start gap-2.5 rounded-lg border border-border bg-card p-3 text-xs">
                <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-emerald-500" />
                <div>
                  <p className="font-semibold text-foreground">
                    Published Teacher Feedback
                  </p>
                  <p className="mt-0.5 text-muted-foreground">
                    Consistent progress on lab worksheets; ready for end-of-term
                    assessment.
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
