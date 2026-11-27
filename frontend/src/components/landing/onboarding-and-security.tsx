import Link from "next/link";
import {
  ArrowRight,
  ClipboardCheck,
  FileKey2,
  Lock,
  MessageSquareQuote,
  ScrollText,
  ShieldAlert,
  UserCheck,
} from "lucide-react";
import { KlasraLogo } from "@/components/brand/klasra-logo";
import { Button } from "@/components/ui/button";

const steps = [
  {
    step: "01",
    title: "Configure School & Import Roster",
    description:
      "Set academic years, terms, and class groups, invite teachers by email, or validate and commit CSV/XLSX rosters.",
    icon: ClipboardCheck,
  },
  {
    step: "02",
    title: "Approve Students & Guardians",
    description:
      "Students self-register with short-lived school codes and wait for approval; parents verify email links prior to admin approval.",
    icon: UserCheck,
  },
  {
    step: "03",
    title: "Teach, Assess & Share Progress",
    description:
      "Publish lessons, assignments, quizzes, and exams, record attendance, and release verified results to students and approved parents.",
    icon: ScrollText,
  },
];

const securityPillars = [
  {
    icon: Lock,
    title: "School-Scoped Isolation",
    description:
      "Every query and mutation is filtered by school_id and verified server-side on every request.",
  },
  {
    icon: ShieldAlert,
    title: "Verified Guardian Access",
    description:
      "Parents view children only after email verification and School Admin approval, with instant revocation.",
  },
  {
    icon: FileKey2,
    title: "Private Signed Storage",
    description:
      "Uploaded videos and documents live in private object storage with magic-byte checks and short-lived signed URLs.",
  },
  {
    icon: ScrollText,
    title: "Immutable Audit Trail",
    description:
      "Every grade change, attendance edit, enrollment transfer, and admin decision is recorded with timestamps.",
  },
];

export function OnboardingAndSecurity() {
  return (
    <>
      {/* 3-Step Onboarding */}
      <section
        id="onboarding"
        className="border-t border-border bg-background py-20"
      >
        <div className="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8">
          <div className="max-w-xl">
            <p className="text-xs font-semibold uppercase tracking-[0.14em] text-primary">
              Getting Started
            </p>
            <h2 className="mt-2 font-display text-3xl font-bold tracking-tight text-foreground">
              From school onboarding to live classrooms in three clear steps.
            </h2>
          </div>

          <div className="mt-10 grid gap-5 md:grid-cols-3">
            {steps.map((item) => {
              const Icon = item.icon;
              return (
                <div
                  key={item.step}
                  className="rounded-2xl border border-border bg-card p-6"
                >
                  <div className="mb-4 flex items-center justify-between">
                    <div className="flex h-10 w-10 items-center justify-center rounded-xl border border-border bg-muted text-foreground">
                      <Icon className="h-4 w-4" />
                    </div>
                    <span className="font-mono text-xs font-semibold text-muted-foreground">
                      STEP {item.step}
                    </span>
                  </div>
                  <h3 className="font-display text-base font-semibold text-foreground">
                    {item.title}
                  </h3>
                  <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
                    {item.description}
                  </p>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* Security & Privacy Architecture */}
      <section
        id="security"
        className="border-y border-border bg-[#0F0F12] py-20 text-zinc-100 dark:bg-[#0E0E11]"
      >
        <div className="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8">
          <div className="max-w-2xl">
            <p className="text-xs font-semibold uppercase tracking-[0.14em] text-emerald-400">
              Security &amp; Child Privacy
            </p>
            <h2 className="mt-2 font-display text-3xl font-bold tracking-tight text-white">
              Engineered to protect student records across every school.
            </h2>
            <p className="mt-3 text-sm leading-relaxed text-zinc-400 sm:text-base">
              Argon2id password hashing, HttpOnly CSRF-protected sessions,
              private encrypted storage, and NDPA-aligned child-data safeguards
              are enforced by default.
            </p>
          </div>

          <div className="mt-10 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
            {securityPillars.map((pillar) => {
              const Icon = pillar.icon;
              return (
                <div
                  key={pillar.title}
                  className="rounded-2xl border border-white/[0.08] bg-[#16161A] p-6"
                >
                  <div className="mb-4 flex h-9 w-9 items-center justify-center rounded-lg border border-white/10 bg-white/[0.04] text-zinc-200">
                    <Icon className="h-4 w-4" />
                  </div>
                  <h3 className="font-display text-sm font-semibold text-white">
                    {pillar.title}
                  </h3>
                  <p className="mt-2 text-xs leading-relaxed text-zinc-400">
                    {pillar.description}
                  </p>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* Honest Pilot / Testimonial Placeholder (No Fabricated Claims) */}
      <section className="mx-auto max-w-6xl px-4 pt-20 sm:px-6 lg:px-8">
        <div className="rounded-2xl border border-dashed border-border bg-card/60 p-6 sm:p-8">
          <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
            <div className="max-w-2xl">
              <div className="inline-flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                <MessageSquareQuote className="h-4 w-4 text-primary" />
                <span>School Feedback &amp; Case Studies</span>
              </div>
              <h2 className="mt-2 font-display text-xl font-bold tracking-tight text-foreground">
                Verified stories from partner secondary schools will appear here.
              </h2>
              <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
                Placeholder section reserved for real testimonials, term-adoption
                outcomes, and principal or parent feedback once pilot schools
                complete onboarding.
              </p>
            </div>
            <span className="w-fit rounded-full border border-border bg-background px-3 py-1 font-mono text-[11px] font-medium text-muted-foreground">
              Pilot Ready
            </span>
          </div>
        </div>
      </section>

      {/* Final Call to Action */}
      <section className="mx-auto max-w-6xl px-4 py-16 sm:px-6 md:py-20 lg:px-8">
        <div className="flex flex-col items-start justify-between gap-6 rounded-2xl border border-border bg-card p-8 sm:flex-row sm:items-center sm:p-10">
          <div className="max-w-xl">
            <h2 className="font-display text-2xl font-bold tracking-tight text-foreground sm:text-3xl">
              Ready to enter your school portal?
            </h2>
            <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
              Sign in as a School Admin, Teacher, Student, or Parent — or use a
              school registration code to request student access.
            </p>
          </div>
          <div className="flex flex-col gap-3 sm:flex-row">
            <Button size="lg" asChild>
              <Link href="/login">
                Sign In to Klasra
                <ArrowRight className="h-4 w-4" />
              </Link>
            </Button>
            <Button size="lg" variant="outline" asChild>
              <Link href="/register/student">Student Registration</Link>
            </Button>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-border bg-background">
        <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-6 px-4 py-8 sm:flex-row sm:px-6 lg:px-8">
          <div className="flex items-center gap-3">
            <KlasraLogo markClassName="h-6 w-6" />
            <span className="text-xs text-muted-foreground">
              · Multi-School Secondary LMS
            </span>
          </div>

          <div className="flex flex-wrap items-center gap-6 text-xs font-medium text-muted-foreground">
            <Link href="/login" className="hover:text-foreground">
              Sign In
            </Link>
            <Link href="/register/student" className="hover:text-foreground">
              Student Registration
            </Link>
            <Link href="/staff/accept" className="hover:text-foreground">
              Staff Activation
            </Link>
            <Link href="/parent/verify" className="hover:text-foreground">
              Parent Verification
            </Link>
          </div>
        </div>
      </footer>
    </>
  );
}
