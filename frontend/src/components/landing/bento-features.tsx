"use client";

import {
  BookOpenCheck,
  CalendarCheck2,
  ClipboardCheck,
  FileSpreadsheet,
  FileUp,
  HeartHandshake,
  Video,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

const features = [
  {
    title: "Lessons, Video & Private Materials",
    description:
      "Publish structured lessons with YouTube, Vimeo, or Loom embeds, direct 50 MB lesson video uploads, and protected PDFs or slides via short-lived signed URLs.",
    icon: Video,
    meta: "MP4 / WebM / PDF / DOCX",
  },
  {
    title: "Timed Quizzes, Tests & Exams",
    description:
      "Create auto-graded multiple-choice, true/false, and multi-select questions alongside manually graded short-answer essays with availability windows and attempt limits.",
    icon: ClipboardCheck,
    meta: "Auto + Manual Grading",
  },
  {
    title: "Assignments & Version History",
    description:
      "Configure due dates, late-submission rules, and resubmissions per assignment. Students submit text and files while every version stays preserved.",
    icon: FileUp,
    meta: "Versioned Submissions",
  },
  {
    title: "Draft-to-Publish Gradebook",
    description:
      "Review submissions and exam responses in draft mode before publishing scores and written feedback to students and approved parents.",
    icon: BookOpenCheck,
    meta: "Controlled Visibility",
  },
  {
    title: "Multi-School Parent Portal",
    description:
      "Parents with children in different schools use one verified account. Email verification plus school admin approval protects every child's records.",
    icon: HeartHandshake,
    meta: "Approved Links Only",
  },
  {
    title: "Attendance & Academic Setup",
    description:
      "Record Present, Absent, Late, or Excused with staff attribution, adapt school terminology, and bulk-import rosters via CSV/XLSX with dry-run validation.",
    icon: CalendarCheck2,
    meta: "Full Audit Trail",
  },
];

export function BentoFeatures() {
  return (
    <section
      id="features"
      className="mx-auto max-w-6xl px-4 py-20 sm:px-6 lg:px-8"
    >
      <div className="max-w-2xl">
        <p className="text-xs font-semibold uppercase tracking-wider text-primary">
          Core Capabilities
        </p>
        <h2 className="mt-2 font-display text-3xl font-bold tracking-tight text-foreground">
          Everything a secondary school runs on, organized clearly.
        </h2>
        <p className="mt-3 text-base text-muted-foreground">
          Built with server-enforced school separation, predictable workflows,
          and clear audit history across every academic term.
        </p>
      </div>

      <div className="mt-12 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
        {features.map((feature) => {
          const Icon = feature.icon;
          return (
            <Card
              key={feature.title}
              className="flex h-full flex-col justify-between hover:border-foreground/20 dark:hover:border-white/15"
            >
              <CardHeader className="pb-3">
                <div className="mb-3 flex h-10 w-10 items-center justify-center rounded-xl border border-border bg-muted text-foreground">
                  <Icon className="h-4 w-4" />
                </div>
                <CardTitle className="text-base font-semibold">
                  {feature.title}
                </CardTitle>
              </CardHeader>
              <CardContent className="flex flex-1 flex-col justify-between gap-4">
                <p className="text-sm leading-relaxed text-muted-foreground">
                  {feature.description}
                </p>
                <div className="flex items-center gap-2 border-t border-border pt-3 font-mono text-[11px] text-muted-foreground">
                  <FileSpreadsheet className="h-3.5 w-3.5 opacity-60" />
                  <span>{feature.meta}</span>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>
    </section>
  );
}
