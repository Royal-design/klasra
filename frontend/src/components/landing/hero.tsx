"use client";

import Image from "next/image";
import Link from "next/link";
import { motion } from "framer-motion";
import { ArrowRight, KeyRound } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ProductPreview } from "@/components/landing/product-preview";

export function LandingHero() {
  return (
    <section className="relative overflow-hidden border-b border-border bg-background">
      {/* Architectural Campus Backdrop (Upper Hero Canvas) */}
      <div className="pointer-events-none absolute inset-x-0 top-0 h-[560px] sm:h-[620px]">
        <Image
          src="/images/hero-backdrop.jpg"
          alt=""
          fill
          priority
          sizes="100vw"
          className="object-cover object-center opacity-30 dark:opacity-35"
        />
        {/* Radial center clarity + smooth bottom fade into page canvas */}
        <div className="absolute inset-0 bg-gradient-to-b from-background/65 via-background/78 to-background dark:from-[#0A0A0B]/55 dark:via-[#0A0A0B]/75 dark:to-[#0A0A0B]" />
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,rgba(250,250,250,0.72)_0%,transparent_70%)] dark:bg-[radial-gradient(ellipse_at_center,rgba(10,10,11,0.68)_0%,transparent_72%)]" />
      </div>

      <div className="relative z-10 mx-auto max-w-6xl px-4 pb-20 pt-16 sm:px-6 md:pb-24 md:pt-22 lg:px-8">
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, ease: [0.22, 1, 0.36, 1] }}
          className="mx-auto max-w-3xl text-center"
        >
          <span className="inline-flex items-center rounded-full border border-border bg-card/85 px-3.5 py-1 text-xs font-semibold uppercase tracking-[0.12em] text-primary backdrop-blur-xs">
            Multi-School Secondary LMS
          </span>

          <h1 className="mt-5 font-display text-4xl font-bold leading-[1.08] tracking-[-0.03em] text-foreground sm:text-5xl md:text-[3.35rem]">
            One structured system for teaching, assessment, and verified parent visibility.
          </h1>

          <p className="mx-auto mt-5 max-w-2xl text-base leading-relaxed text-muted-foreground sm:text-lg">
            Built for secondary schools, teachers, students, and families.
            Deliver lessons and videos, run assignments, timed quizzes, and
            exams, record attendance, and keep every school&apos;s data strictly
            isolated.
          </p>

          <div className="mt-8 flex flex-col justify-center gap-3 sm:flex-row">
            <Button size="lg" asChild>
              <Link href="/login">
                Sign In to Your School
                <ArrowRight className="h-4 w-4" />
              </Link>
            </Button>
            <Button
              size="lg"
              variant="outline"
              asChild
              className="bg-card/80 backdrop-blur-xs"
            >
              <Link href="/register/student">
                <KeyRound className="h-4 w-4 text-muted-foreground" />
                Register with School Code
              </Link>
            </Button>
          </div>
        </motion.div>

        {/* Tangible Interactive Product Preview */}
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.45, delay: 0.1, ease: [0.22, 1, 0.36, 1] }}
          className="mt-12 md:mt-16"
        >
          <ProductPreview />
        </motion.div>
      </div>
    </section>
  );
}
