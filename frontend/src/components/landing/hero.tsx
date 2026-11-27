"use client";

import Image from "next/image";
import Link from "next/link";
import { motion } from "framer-motion";
import {
  ArrowRight,
  CheckCircle2,
  KeyRound,
  PlayCircle,
  ShieldCheck,
  Sparkles,
  Users,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.1 },
  },
};

const itemVariants = {
  hidden: { opacity: 0, y: 18 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.5, ease: [0.22, 1, 0.36, 1] as const },
  },
};

export function LandingHero() {
  return (
    <section className="relative overflow-hidden border-b border-border/60">
      {/* Ambient Indigo + Teal glow + subtle dot grid */}
      <div className="pointer-events-none absolute inset-0 bg-scholarly-grid opacity-55 dark:opacity-35" />
      <div className="pointer-events-none absolute -top-32 left-1/2 h-[420px] w-[720px] -translate-x-1/2 rounded-full bg-gradient-to-r from-indigo-500/20 via-teal-400/15 to-amber-400/15 blur-3xl dark:from-indigo-500/25 dark:via-teal-500/15" />

      <div className="relative mx-auto grid max-w-7xl items-center gap-12 px-4 py-16 sm:px-6 md:py-24 lg:grid-cols-12 lg:px-8">
        {/* Left Copy */}
        <motion.div
          variants={containerVariants}
          initial="hidden"
          animate="visible"
          className="lg:col-span-6"
        >
          <motion.div variants={itemVariants}>
            <Badge variant="default" className="mb-5 px-3.5 py-1.5 text-xs">
              <Sparkles className="h-3.5 w-3.5" />
              Multi-School Learning &amp; Parent Portal
            </Badge>
          </motion.div>

          <motion.h1
            variants={itemVariants}
            className="font-display text-4xl font-extrabold leading-[1.08] tracking-tight text-foreground sm:text-5xl lg:text-[3.35rem]"
          >
            One Modern Classroom for{" "}
            <span className="bg-gradient-to-r from-indigo-600 via-indigo-500 to-teal-500 bg-clip-text text-transparent dark:from-indigo-400 dark:via-sky-400 dark:to-teal-300">
              Schools, Teachers, Students &amp; Parents.
            </span>
          </motion.h1>

          <motion.p
            variants={itemVariants}
            className="mt-6 max-w-xl text-base leading-relaxed text-muted-foreground sm:text-lg"
          >
            Publish rich lessons and videos, collect versioned assignments, record
            transparent grades and attendance, and give parents verified visibility
            across multiple schools — all with strict school-level data isolation.
          </motion.p>

          <motion.div
            variants={itemVariants}
            className="mt-8 flex flex-col gap-3 sm:flex-row sm:items-center"
          >
            <Button size="lg" asChild className="group">
              <Link href="/login">
                Sign In to Your School
                <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
              </Link>
            </Button>
            <Button size="lg" variant="outline" asChild>
              <Link href="/register/student">
                <KeyRound className="h-4 w-4 text-primary" />
                Register with School Code
              </Link>
            </Button>
          </motion.div>

          <motion.div
            variants={itemVariants}
            className="mt-8 grid grid-cols-2 gap-3 pt-4 sm:grid-cols-3"
          >
            {[
              { icon: ShieldCheck, label: "Strict School Isolation" },
              { icon: Users, label: "Multi-School Parents" },
              { icon: PlayCircle, label: "Video & PDF Lessons" },
            ].map(({ icon: Icon, label }) => (
              <div
                key={label}
                className="flex items-center gap-2 text-xs font-medium text-muted-foreground sm:text-sm"
              >
                <Icon className="h-4 w-4 shrink-0 text-secondary" />
                <span>{label}</span>
              </div>
            ))}
          </motion.div>
        </motion.div>

        {/* Right Visual Showcase */}
        <motion.div
          initial={{ opacity: 0, scale: 0.96, y: 20 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          transition={{ duration: 0.65, ease: [0.22, 1, 0.36, 1] }}
          className="relative lg:col-span-6"
        >
          <div className="relative overflow-hidden rounded-3xl border border-border/80 bg-card p-2 shadow-2xl shadow-indigo-500/10 dark:shadow-black/50">
            <div className="relative aspect-[16/10] w-full overflow-hidden rounded-2xl">
              <Image
                src="/images/hero-classroom.jpg"
                alt="Secondary school students and teacher collaborating in a bright modern classroom"
                fill
                priority
                sizes="(max-width: 1024px) 100vw, 50vw"
                className="object-cover"
              />
              <div className="absolute inset-0 bg-gradient-to-t from-slate-950/60 via-slate-950/10 to-transparent" />

              {/* Bottom caption inside hero photo */}
              <div className="absolute bottom-4 left-4 right-4 flex items-center justify-between gap-3 rounded-xl border border-white/15 bg-slate-950/65 px-4 py-3 text-white backdrop-blur-md">
                <div className="flex items-center gap-3">
                  <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-teal-500/20 text-teal-300">
                    <PlayCircle className="h-5 w-5" />
                  </div>
                  <div>
                    <p className="text-xs font-semibold text-white">
                      PHY10 · Kinematics &amp; Motion Video Lesson
                    </p>
                    <p className="text-[11px] text-slate-300">
                      Published to SS2 Science · 2 Attachments (MP4 + PDF)
                    </p>
                  </div>
                </div>
                <span className="hidden rounded-full bg-emerald-500/20 px-2.5 py-1 font-mono text-[11px] font-semibold text-emerald-300 sm:inline-block">
                  Live
                </span>
              </div>
            </div>
          </div>

          {/* Floating Grade Preview Card */}
          <motion.div
            animate={{ y: [0, -6, 0] }}
            transition={{ duration: 4.5, repeat: Infinity, ease: "easeInOut" }}
            className="absolute -left-4 -top-5 hidden rounded-2xl border border-border bg-card/95 p-3.5 shadow-xl backdrop-blur-md sm:block"
          >
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-indigo-500/15 font-mono text-sm font-bold text-indigo-600 dark:text-indigo-300">
                A+
              </div>
              <div>
                <p className="text-xs font-bold text-foreground">
                  Published Grade · 94/100
                </p>
                <p className="text-[11px] text-muted-foreground">
                  Visible to Student &amp; Approved Parent
                </p>
              </div>
            </div>
          </motion.div>

          {/* Floating Attendance Snapshot Card */}
          <motion.div
            animate={{ y: [0, 6, 0] }}
            transition={{ duration: 5.2, repeat: Infinity, ease: "easeInOut" }}
            className="absolute -bottom-5 -right-3 hidden rounded-2xl border border-border bg-card/95 p-3.5 shadow-xl backdrop-blur-md sm:block"
          >
            <div className="flex items-center gap-2.5">
              <CheckCircle2 className="h-5 w-5 text-emerald-500" />
              <div>
                <p className="text-xs font-bold text-foreground">
                  Roll Call Recorded · 98% Present
                </p>
                <p className="font-mono text-[11px] text-muted-foreground">
                  Audited · Ms. Okafor · 08:15 AM
                </p>
              </div>
            </div>
          </motion.div>
        </motion.div>
      </div>
    </section>
  );
}
