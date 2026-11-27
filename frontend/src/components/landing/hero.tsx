"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { ArrowRight, KeyRound } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ProductPreview } from "@/components/landing/product-preview";

export function LandingHero() {
  return (
    <section className="border-b border-border bg-background">
      <div className="mx-auto max-w-6xl px-4 pb-20 pt-14 sm:px-6 md:pb-24 md:pt-20 lg:px-8">
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, ease: [0.22, 1, 0.36, 1] }}
          className="mx-auto max-w-3xl text-center"
        >
          <p className="text-xs font-semibold uppercase tracking-[0.14em] text-primary">
            Multi-School Secondary Learning Management System
          </p>

          <h1 className="mt-4 font-display text-4xl font-bold leading-[1.08] tracking-[-0.03em] text-foreground sm:text-5xl md:text-[3.25rem]">
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
            <Button size="lg" variant="outline" asChild>
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
