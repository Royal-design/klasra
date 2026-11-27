"use client";

import Image from "next/image";
import Link from "next/link";
import { motion } from "framer-motion";
import { ArrowRight, CheckCircle2, KeyRound, ShieldCheck } from "lucide-react";
import { Button } from "@/components/ui/button";

export function LandingHero() {
  return (
    <section className="border-b border-border bg-background">
      <div className="mx-auto max-w-6xl px-4 py-16 sm:px-6 md:py-24 lg:px-8">
        <div className="grid items-center gap-12 lg:grid-cols-12">
          {/* Left Column: Clear Hierarchy & Restraint */}
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, ease: [0.22, 1, 0.36, 1] }}
            className="lg:col-span-6"
          >
            <div className="mb-5 inline-flex items-center gap-2 rounded-full border border-border bg-card px-3 py-1 text-xs font-medium text-muted-foreground">
              <ShieldCheck className="h-3.5 w-3.5 text-primary" />
              <span>Multi-School Secondary LMS &amp; Parent Portal</span>
            </div>

            <h1 className="font-display text-4xl font-bold leading-[1.1] tracking-tight text-foreground sm:text-5xl">
              Structured learning management for secondary schools.
            </h1>

            <p className="mt-5 max-w-xl text-base leading-relaxed text-muted-foreground">
              Klasra brings lessons, video materials, assignments, timed quizzes
              and exams, grading, attendance, and verified multi-school parent
              access into one disciplined workspace.
            </p>

            <div className="mt-8 flex flex-col gap-3 sm:flex-row sm:items-center">
              <Button size="lg" asChild>
                <Link href="/login">
                  Sign In to Your School
                  <ArrowRight className="h-4 w-4" />
                </Link>
              </Button>
              <Button size="lg" variant="outline" asChild>
                <Link href="/register/student">
                  <KeyRound className="h-4 w-4 text-muted-foreground" />
                  Register with School Code
                </Link>
              </Button>
            </div>

            <div className="mt-10 grid grid-cols-3 gap-6 border-t border-border pt-6">
              <div>
                <p className="font-display text-lg font-bold text-foreground">
                  100%
                </p>
                <p className="mt-0.5 text-xs text-muted-foreground">
                  School-isolated data
                </p>
              </div>
              <div>
                <p className="font-display text-lg font-bold text-foreground">
                  5 Roles
                </p>
                <p className="mt-0.5 text-xs text-muted-foreground">
                  Admin to multi-school parent
                </p>
              </div>
              <div>
                <p className="font-display text-lg font-bold text-foreground">
                  Audited
                </p>
                <p className="mt-0.5 text-xs text-muted-foreground">
                  Grades, attendance &amp; access
                </p>
              </div>
            </div>
          </motion.div>

          {/* Right Column: Grounded Editorial Frame */}
          <motion.div
            initial={{ opacity: 0, y: 14 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.45, delay: 0.08, ease: [0.22, 1, 0.36, 1] }}
            className="lg:col-span-6"
          >
            <div className="overflow-hidden rounded-2xl border border-border bg-card shadow-sm">
              <div className="relative aspect-[16/10] w-full overflow-hidden bg-muted">
                <Image
                  src="/images/hero-classroom.jpg"
                  alt="Secondary school students and teacher collaborating in a modern classroom"
                  fill
                  priority
                  sizes="(max-width: 1024px) 100vw, 50vw"
                  className="object-cover"
                />
              </div>

              <div className="grid divide-y divide-border border-t border-border sm:grid-cols-2 sm:divide-x sm:divide-y-0">
                <div className="flex items-start gap-3 p-4">
                  <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-emerald-500" />
                  <div>
                    <p className="text-xs font-semibold text-foreground">
                      Lessons, Quizzes &amp; Exams
                    </p>
                    <p className="mt-0.5 text-xs text-muted-foreground">
                      Video lessons, auto-graded quizzes, and draft-to-publish
                      grades.
                    </p>
                  </div>
                </div>
                <div className="flex items-start gap-3 p-4">
                  <ShieldCheck className="mt-0.5 h-4 w-4 shrink-0 text-primary" />
                  <div>
                    <p className="text-xs font-semibold text-foreground">
                      Verified Parent Access
                    </p>
                    <p className="mt-0.5 text-xs text-muted-foreground">
                      One parent login for approved children across multiple
                      schools.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </motion.div>
        </div>
      </div>
    </section>
  );
}
