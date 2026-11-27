"use client";

import { motion } from "framer-motion";
import {
  BookOpenCheck,
  CalendarCheck2,
  FileSpreadsheet,
  FileUp,
  GraduationCap,
  HeartHandshake,
  Video,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

const features = [
  {
    title: "Lessons, Videos & Private Attachments",
    description:
      "Publish draft or live lessons with embedded YouTube, Vimeo, or Loom videos, 50 MB direct video uploads, and protected PDFs/slides served via short-lived signed URLs.",
    icon: Video,
    badge: "LEARN-01",
    span: "md:col-span-2",
    accent: "from-indigo-500/15 to-teal-500/10",
    preview: (
      <div className="mt-4 flex flex-wrap items-center gap-2">
        <span className="rounded-lg border border-indigo-500/20 bg-indigo-500/10 px-2.5 py-1 font-mono text-xs font-medium text-indigo-600 dark:text-indigo-300">
          lecture_week4.mp4 · 38 MB
        </span>
        <span className="rounded-lg border border-teal-500/20 bg-teal-500/10 px-2.5 py-1 font-mono text-xs font-medium text-teal-700 dark:text-teal-300">
          worksheet.pdf · 2.4 MB
        </span>
        <span className="rounded-lg border border-border bg-muted px-2.5 py-1 text-xs font-medium text-muted-foreground">
          Signed URL · 5 min TTL
        </span>
      </div>
    ),
  },
  {
    title: "Assignments & Versioned History",
    description:
      "Configure due dates, late-submission rules, and resubmissions per assignment. Students submit typed answers and files while every version (v1 → v2) stays preserved.",
    icon: FileUp,
    badge: "ASSIGN-01..03",
    span: "md:col-span-1",
    accent: "from-teal-500/15 to-emerald-500/10",
    preview: (
      <div className="mt-4 flex items-center gap-2 font-mono text-xs">
        <span className="rounded-md bg-muted px-2 py-1 text-muted-foreground">v1 · On time</span>
        <span className="text-muted-foreground">→</span>
        <span className="rounded-md bg-primary/15 px-2 py-1 font-semibold text-primary">
          v2 · Latest
        </span>
      </div>
    ),
  },
  {
    title: "Draft-to-Publish Grading",
    description:
      "Teachers review submissions, enter validated scores, letter grades, and constructive feedback in draft mode — then publish when ready for students and parents.",
    icon: BookOpenCheck,
    badge: "ASSIGN-04",
    span: "md:col-span-1",
    accent: "from-amber-500/15 to-orange-500/10",
    preview: (
      <div className="mt-4 space-y-1.5">
        <div className="flex justify-between text-xs font-semibold">
          <span className="text-muted-foreground">Mathematics Quiz</span>
          <span className="font-mono text-emerald-600 dark:text-emerald-400">92 / 100 (A)</span>
        </div>
        <div className="h-2 w-full overflow-hidden rounded-full bg-muted">
          <div className="h-full w-[92%] rounded-full bg-gradient-to-r from-indigo-500 to-teal-400" />
        </div>
      </div>
    ),
  },
  {
    title: "Multi-School Parent Visibility",
    description:
      "Parents with children in different schools use one single account. Email verification plus school admin approval ensures parents see only their approved children's grades, feedback, and attendance.",
    icon: HeartHandshake,
    badge: "AUTH-04 · PROG-02",
    span: "md:col-span-2",
    accent: "from-indigo-500/10 via-violet-500/10 to-amber-500/10",
    preview: (
      <div className="mt-4 grid gap-2 sm:grid-cols-2">
        <div className="flex items-center justify-between rounded-xl border border-border bg-background/80 px-3 py-2 text-xs">
          <div>
            <p className="font-semibold text-foreground">Tobi Adeyemi</p>
            <p className="text-[11px] text-muted-foreground">Greenfield High · SS2</p>
          </div>
          <Badge variant="success">Approved</Badge>
        </div>
        <div className="flex items-center justify-between rounded-xl border border-border bg-background/80 px-3 py-2 text-xs">
          <div>
            <p className="font-semibold text-foreground">Amara Adeyemi</p>
            <p className="text-[11px] text-muted-foreground">Oakridge Academy · JSS2</p>
          </div>
          <Badge variant="success">Approved</Badge>
        </div>
      </div>
    ),
  },
  {
    title: "One-Tap Attendance & Audit Trail",
    description:
      "Mark Present, Absent, Late, or Excused for an entire class offering in seconds. Every change records staff attribution, timestamp, and an immutable audit entry.",
    icon: CalendarCheck2,
    badge: "ATT-01..02",
    span: "md:col-span-1",
    accent: "from-emerald-500/15 to-teal-500/10",
    preview: (
      <div className="mt-4 flex flex-wrap gap-1.5 text-[11px] font-semibold">
        <span className="rounded-full bg-emerald-500/15 px-2.5 py-1 text-emerald-700 dark:text-emerald-300">
          Present
        </span>
        <span className="rounded-full bg-amber-500/15 px-2.5 py-1 text-amber-700 dark:text-amber-300">
          Late
        </span>
        <span className="rounded-full bg-sky-500/15 px-2.5 py-1 text-sky-700 dark:text-sky-300">
          Excused
        </span>
        <span className="rounded-full bg-rose-500/15 px-2.5 py-1 text-rose-700 dark:text-rose-300">
          Absent
        </span>
      </div>
    ),
  },
  {
    title: "Flexible Academic Structure & CSV/XLSX Import",
    description:
      "Adapt labels to your school (JSS/SS or Grade 7–12, Term or Semester), manage history-preserving transfers, and bulk-import rosters with dry-run validation before commit.",
    icon: FileSpreadsheet,
    badge: "SCH-02..05",
    span: "md:col-span-2",
    accent: "from-sky-500/10 to-indigo-500/10",
    preview: (
      <div className="mt-4 flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
        <span className="inline-flex items-center gap-1.5 rounded-lg border border-border bg-background/80 px-2.5 py-1 font-medium text-foreground">
          <GraduationCap className="h-3.5 w-3.5 text-primary" />
          Academic Year → Term → Class Group → Subject Offering
        </span>
        <span className="rounded-lg bg-emerald-500/10 px-2.5 py-1 font-mono text-emerald-700 dark:text-emerald-300">
          240 rows validated · 0 errors
        </span>
      </div>
    ),
  },
];

export function BentoFeatures() {
  return (
    <section id="features" className="mx-auto max-w-7xl px-4 py-20 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-2xl text-center">
        <Badge variant="secondary" className="mb-3">
          Built for Secondary Schools
        </Badge>
        <h2 className="font-display text-3xl font-extrabold tracking-tight text-foreground sm:text-4xl">
          Everything a school needs — without the clutter.
        </h2>
        <p className="mt-3 text-base text-muted-foreground">
          Every workflow is backed by server-enforced school isolation, clear role
          boundaries, and clean audit history.
        </p>
      </div>

      <div className="mt-12 grid gap-5 md:grid-cols-3">
        {features.map((feature, index) => {
          const Icon = feature.icon;
          return (
            <motion.div
              key={feature.title}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, amount: 0.2 }}
              transition={{ duration: 0.45, delay: index * 0.05 }}
              className={feature.span}
            >
              <Card className="group relative h-full overflow-hidden border-border/80 hover:-translate-y-1 hover:border-primary/40 hover:shadow-lg hover:shadow-indigo-500/10">
                <div
                  className={`pointer-events-none absolute inset-0 bg-gradient-to-br ${feature.accent} opacity-0 transition-opacity duration-300 group-hover:opacity-100`}
                />
                <CardHeader className="relative pb-3">
                  <div className="mb-3 flex items-center justify-between">
                    <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-primary/10 text-primary transition-colors group-hover:bg-primary group-hover:text-primary-foreground">
                      <Icon className="h-5 w-5" />
                    </div>
                    <span className="font-mono text-[11px] font-semibold text-muted-foreground">
                      {feature.badge}
                    </span>
                  </div>
                  <CardTitle className="text-xl">{feature.title}</CardTitle>
                </CardHeader>
                <CardContent className="relative">
                  <p className="text-sm leading-relaxed text-muted-foreground">
                    {feature.description}
                  </p>
                  {feature.preview}
                </CardContent>
              </Card>
            </motion.div>
          );
        })}
      </div>
    </section>
  );
}
