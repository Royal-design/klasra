"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import {
  ArrowRight,
  ClipboardCheck,
  FileKey2,
  GraduationCap,
  Lock,
  ScrollText,
  ShieldAlert,
  UserCheck,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

const steps = [
  {
    step: "01",
    title: "School Configures & Imports",
    description:
      "School Admins set academic years, terms, and class groups, invite teachers by email, or bulk-import rosters via CSV/XLSX.",
    icon: ClipboardCheck,
  },
  {
    step: "02",
    title: "Students & Parents Verify Safely",
    description:
      "Students register with a short-lived school code and wait for approval; parents verify email links before admin approval.",
    icon: UserCheck,
  },
  {
    step: "03",
    title: "Teach, Submit, Grade & Track",
    description:
      "Teachers publish lessons and assignments, students submit work, and published grades and attendance flow to approved parents.",
    icon: GraduationCap,
  },
];

const securityPillars = [
  {
    icon: Lock,
    title: "Strict School Isolation",
    description:
      "Every query and mutation is scoped by school_id and verified server-side — never trusted from the browser.",
  },
  {
    icon: ShieldAlert,
    title: "Verified Guardian Access",
    description:
      "Parents only see children after email verification and School Admin approval, with instant revocation support.",
  },
  {
    icon: FileKey2,
    title: "Private Signed Storage",
    description:
      "Uploaded videos and documents live in private object storage with magic-byte checks and 5-minute signed URLs.",
  },
  {
    icon: ScrollText,
    title: "Immutable Audit Trail",
    description:
      "Every grade change, attendance edit, enrollment transfer, role update, and admin decision is logged with timestamps.",
  },
];

export function OnboardingAndSecurity() {
  return (
    <>
      {/* 3-Step Onboarding */}
      <section id="onboarding" className="mx-auto max-w-7xl px-4 py-20 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-2xl text-center">
          <Badge variant="accent" className="mb-3">
            Fast School Onboarding
          </Badge>
          <h2 className="font-display text-3xl font-extrabold tracking-tight text-foreground sm:text-4xl">
            From setup to first published lesson in minutes.
          </h2>
        </div>

        <div className="mt-12 grid gap-6 md:grid-cols-3">
          {steps.map((item, idx) => {
            const Icon = item.icon;
            return (
              <motion.div
                key={item.step}
                initial={{ opacity: 0, y: 18 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, amount: 0.2 }}
                transition={{ duration: 0.45, delay: idx * 0.08 }}
                className="relative rounded-2xl border border-border bg-card p-6 shadow-sm"
              >
                <div className="mb-4 flex items-center justify-between">
                  <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-primary/10 text-primary">
                    <Icon className="h-5 w-5" />
                  </div>
                  <span className="font-mono text-2xl font-bold text-primary/25">
                    {item.step}
                  </span>
                </div>
                <h3 className="font-display text-lg font-bold text-foreground">
                  {item.title}
                </h3>
                <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
                  {item.description}
                </p>
              </motion.div>
            );
          })}
        </div>
      </section>

      {/* Security & Privacy Strip */}
      <section
        id="security"
        className="border-y border-border bg-[#0F0F12] py-20 text-zinc-100 dark:bg-[#0E0E11]"
      >
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="max-w-2xl">
            <span className="inline-flex items-center gap-1.5 rounded-full border border-emerald-400/25 bg-emerald-500/10 px-3 py-1 text-xs font-semibold text-emerald-300">
              Security &amp; Child Privacy First
            </span>
            <h2 className="mt-4 font-display text-3xl font-extrabold tracking-tight text-white sm:text-4xl">
              Built to protect student records across every school.
            </h2>
            <p className="mt-3 text-sm leading-relaxed text-zinc-400 sm:text-base">
              Argon2id password hashing, HttpOnly CSRF-protected sessions, private
              encrypted storage, and NDPA-aligned child-data safeguards are built in
              from day one.
            </p>
          </div>

          <div className="mt-12 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
            {securityPillars.map((pillar) => {
              const Icon = pillar.icon;
              return (
                <div
                  key={pillar.title}
                  className="rounded-2xl border border-white/[0.08] bg-[#16161A] p-6 shadow-[inset_0_1px_0_0_rgba(255,255,255,0.04)] transition-colors hover:border-white/15"
                >
                  <div className="mb-4 flex h-10 w-10 items-center justify-center rounded-xl bg-white/[0.06] text-zinc-200">
                    <Icon className="h-5 w-5" />
                  </div>
                  <h3 className="font-display text-base font-bold text-white">
                    {pillar.title}
                  </h3>
                  <p className="mt-2 text-sm leading-relaxed text-zinc-400">
                    {pillar.description}
                  </p>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* Closing CTA */}
      <section className="mx-auto max-w-7xl px-4 py-20 sm:px-6 lg:px-8">
        <div className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-indigo-600 via-indigo-700 to-teal-600 px-6 py-14 text-center text-white shadow-2xl shadow-indigo-600/20 sm:px-12">
          <div className="pointer-events-none absolute -right-24 -top-24 h-64 w-64 rounded-full bg-white/10 blur-3xl" />
          <div className="pointer-events-none absolute -bottom-24 -left-24 h-64 w-64 rounded-full bg-teal-300/20 blur-3xl" />

          <div className="relative mx-auto max-w-2xl">
            <h2 className="font-display text-3xl font-extrabold tracking-tight sm:text-4xl">
              Ready to step into your school portal?
            </h2>
            <p className="mt-4 text-base text-indigo-100">
              Sign in as a School Admin, Teacher, Student, or Parent — or register
              with your school&apos;s cohort code.
            </p>
            <div className="mt-8 flex flex-col justify-center gap-3 sm:flex-row">
              <Button
                size="lg"
                asChild
                className="bg-white text-indigo-700 hover:bg-indigo-50"
              >
                <Link href="/login">
                  Sign In Now
                  <ArrowRight className="h-4 w-4" />
                </Link>
              </Button>
              <Button
                size="lg"
                variant="outline"
                asChild
                className="border-white/30 bg-white/10 text-white hover:bg-white/20 hover:text-white"
              >
                <Link href="/register/student">Student Self-Registration</Link>
              </Button>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-border bg-card">
        <div className="mx-auto flex max-w-7xl flex-col items-center justify-between gap-6 px-4 py-10 sm:flex-row sm:px-6 lg:px-8">
          <div className="flex items-center gap-2.5">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-indigo-600 to-teal-500 text-white">
              <GraduationCap className="h-4 w-4" />
            </div>
            <div>
              <p className="font-display text-sm font-bold text-foreground">
                ScholarGrid LMS
              </p>
              <p className="text-xs text-muted-foreground">
                Multi-School Secondary Learning Platform
              </p>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-6 text-xs font-medium text-muted-foreground">
            <Link href="/login" className="hover:text-primary">
              Sign In
            </Link>
            <Link href="/register/student" className="hover:text-primary">
              Student Registration
            </Link>
            <Link href="/staff/accept" className="hover:text-primary">
              Staff Activation
            </Link>
            <Link href="/parent/verify" className="hover:text-primary">
              Parent Verification
            </Link>
          </div>
        </div>
      </footer>
    </>
  );
}
