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

type RoleKey = "student" | "teacher" | "parent" | "admin";

const ROLES: Record<
  RoleKey,
  {
    label: string;
    icon: React.ComponentType<{ className?: string }>;
    headline: string;
    summary: string;
    bullets: string[];
    imageSrc: string;
    imageAlt: string;
    captionTitle: string;
    captionSub: string;
  }
> = {
  student: {
    label: "Learners",
    icon: GraduationCap,
    headline: "Clear lessons, timed assessments, and private progress.",
    summary:
      "Students see only the classes they are actively enrolled in — making it effortless to watch lessons, submit assignments, complete quizzes and exams, and track published grades.",
    bullets: [
      "Watch lesson videos and download materials securely on phone, tablet, or laptop",
      "Submit typed work and files with clear version history when resubmissions are allowed",
      "Take timed quizzes, tests, and exams with server-enforced deadlines",
      "Private by design — students never see classmates' submissions or marks",
    ],
    imageSrc: "/images/hero-classroom.jpg",
    imageAlt: "Secondary school students collaborating with tablets and laptops",
    captionTitle: "Focused Learner Workspace",
    captionSub: "Enrolled subject offerings, lessons, submissions, and own progress.",
  },
  teacher: {
    label: "Instructors",
    icon: Presentation,
    headline: "Teach, assess, and grade without fighting spreadsheets.",
    summary:
      "Each teacher belongs to one school and sees only their assigned subject offerings — keeping lesson publishing, quiz creation, grading, and daily attendance fast and predictable.",
    bullets: [
      "Publish lessons with YouTube, Vimeo, or Loom embeds or direct 50 MB video uploads",
      "Build auto-graded objective quizzes alongside manually graded short-answer exams",
      "Review submissions and exam answers in draft mode before publishing scores",
      "Record Present, Absent, Late, or Excused attendance with automatic attribution",
    ],
    imageSrc: "/images/hero-classroom.jpg",
    imageAlt: "Teacher guiding secondary school students in a modern classroom",
    captionTitle: "Assigned-Offering Control",
    captionSub: "Draft-to-publish lessons, assessments, gradebook, and roll call.",
  },
  parent: {
    label: "Parents & Guardians",
    icon: HeartHandshake,
    headline: "Verified progress across every child — even across different schools.",
    summary:
      "One parent account links to all approved children across participating schools, showing published grades, quiz and exam scores, teacher feedback, and attendance.",
    bullets: [
      "Single parent login with a clear child and school switcher",
      "Email verification plus School Admin approval before any child record is shown",
      "View published grades, assessment scores, teacher comments, and attendance history",
      "School administrators can review or revoke guardian links immediately",
    ],
    imageSrc: "/images/parent-student.jpg",
    imageAlt: "Parent and secondary school student reviewing academic progress at home",
    captionTitle: "Verified Multi-School Visibility",
    captionSub: "Only approved children's published grades, feedback, and attendance.",
  },
  admin: {
    label: "School Admins",
    icon: Building2,
    headline: "Structure the academic year and govern access with confidence.",
    summary:
      "Configure academic years, terms, class groups, and school terminology. Import rosters with dry-run validation and approve student registrations and guardian links.",
    bullets: [
      "Validate CSV and XLSX student/staff spreadsheets before committing changes",
      "Review and approve pending student self-registrations before granting access",
      "Transfer or withdraw students while retaining complete historical records",
      "Full audit trail across role changes, enrollments, grades, and guardian links",
    ],
    imageSrc: "/images/hero-classroom.jpg",
    imageAlt: "Modern secondary school classroom environment",
    captionTitle: "Governed School Administration",
    captionSub: "School-scoped setup, roster imports, approvals, and audit logging.",
  },
};

export function RoleShowcase() {
  const [activeRole, setActiveRole] = React.useState<RoleKey>("student");
  const current = ROLES[activeRole];

  return (
    <section
      id="roles"
      className="border-y border-border bg-card/50 py-20 dark:bg-[#0E0E10]"
    >
      <div className="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8">
        <div className="flex flex-col justify-between gap-6 md:flex-row md:items-end">
          <div className="max-w-xl">
            <p className="text-xs font-semibold uppercase tracking-[0.14em] text-primary">
              The Klasra Experience
            </p>
            <h2 className="mt-2 font-display text-3xl font-bold tracking-tight text-foreground">
              Designed around every role in a secondary school.
            </h2>
          </div>

          <div
            role="tablist"
            aria-label="Klasra role perspectives"
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
                    "inline-flex items-center gap-2 rounded-lg px-3.5 py-2 text-xs font-semibold transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring cursor-pointer",
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
                  className="flex items-start gap-3 text-sm leading-relaxed text-foreground"
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
                  src={current.imageSrc}
                  alt={current.imageAlt}
                  fill
                  sizes="(max-width: 1024px) 100vw, 40vw"
                  className="object-cover"
                />
              </div>
              <div className="border-t border-border bg-card px-4 py-3">
                <p className="text-xs font-semibold text-foreground">
                  {current.captionTitle}
                </p>
                <p className="mt-0.5 text-xs text-muted-foreground">
                  {current.captionSub}
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
