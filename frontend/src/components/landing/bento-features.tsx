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
    title: "Lessons, Video & Private Files",
    description:
      "Deliver structured lessons with YouTube, Vimeo, or Loom embeds, 50 MB direct video uploads, and protected PDFs or slides served via short-lived signed URLs.",
    icon: Video,
    meta: "MP4 · WebM · PDF · DOCX · PPTX",
  },
  {
    title: "Timed Quizzes, Tests & Exams",
    description:
      "Combine auto-graded multiple-choice, true/false, and multi-select questions with teacher-graded essays, availability windows, and attempt limits.",
    icon: ClipboardCheck,
    meta: "Auto + Manual Grading",
  },
  {
    title: "Assignments & Version History",
    description:
      "Set due dates, late-submission rules, and resubmissions per assignment. Students upload files or typed responses with full version history preserved.",
    icon: FileUp,
    meta: "Versioned Submissions",
  },
  {
    title: "Draft-to-Publish Gradebook",
    description:
      "Grade submissions and assessments privately in draft state and release scores with written feedback when review is complete.",
    icon: BookOpenCheck,
    meta: "Controlled Release",
  },
  {
    title: "Multi-School Parent Access",
    description:
      "Parents verify once and link approved children across participating schools — viewing only published grades, assessment scores, and attendance.",
    icon: HeartHandshake,
    meta: "Approved Links Only",
  },
  {
    title: "Attendance & Roster Imports",
    description:
      "Record Present, Absent, Late, or Excused with staff attribution, adapt school terminology, and validate CSV/XLSX rosters before import.",
    icon: CalendarCheck2,
    meta: "Audited Records",
  },
];

export function BentoFeatures() {
  return (
    <section
      id="features"
      className="mx-auto max-w-6xl px-4 py-20 sm:px-6 lg:px-8"
    >
      <div className="max-w-2xl">
        <p className="text-xs font-semibold uppercase tracking-[0.14em] text-primary">
          Standout Capabilities
        </p>
        <h2 className="mt-2 font-display text-3xl font-bold tracking-tight text-foreground">
          Practical tools built for daily secondary-school work.
        </h2>
        <p className="mt-3 text-base leading-relaxed text-muted-foreground">
          Every feature is backed by server-enforced school separation,
          predictable role permissions, and clear audit history.
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
