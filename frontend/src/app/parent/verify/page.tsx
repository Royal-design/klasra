"use client";

import * as React from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { CheckCircle2, HeartHandshake, Loader2 } from "lucide-react";
import { toast } from "sonner";
import { AuthShell } from "@/components/auth/auth-shell";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ApiClientError, apiRequest } from "@/lib/api-client";

function ParentVerifyForm() {
  const searchParams = useSearchParams();
  const [token, setToken] = React.useState(searchParams.get("token") || "");
  const [password, setPassword] = React.useState("");
  const [submitting, setSubmitting] = React.useState(false);
  const [verified, setVerified] = React.useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    try {
      await apiRequest("/guardian-links/verify", {
        method: "POST",
        body: JSON.stringify({ token: token.trim(), password }),
      });
      setVerified(true);
      toast.success("Email verified! Waiting for school admin approval.");
    } catch (err) {
      toast.error(
        err instanceof ApiClientError
          ? err.message
          : "Verification token is invalid or expired."
      );
    } finally {
      setSubmitting(false);
    }
  }

  if (verified) {
    return (
      <div className="space-y-4 rounded-2xl border border-teal-500/25 bg-teal-500/10 p-5 text-center">
        <CheckCircle2 className="mx-auto h-10 w-10 text-teal-600 dark:text-teal-400" />
        <p className="text-sm font-bold text-foreground">
          Guardian email verified
        </p>
        <p className="text-xs leading-relaxed text-muted-foreground">
          Your parent account is linked and awaiting final approval from the
          School Administrator. Once approved, your child&apos;s published
          grades and attendance will appear in your Parent Portal.
        </p>
        <Button asChild className="w-full">
          <Link href="/login">Go to Sign In</Link>
        </Button>
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="space-y-1.5">
        <Label htmlFor="token">Parent verification token</Label>
        <Input
          id="token"
          required
          placeholder="Paste verification token from email"
          value={token}
          onChange={(e) => setToken(e.target.value)}
          className="font-mono text-xs"
        />
      </div>

      <div className="space-y-1.5">
        <Label htmlFor="password">
          Account password (create new or enter existing)
        </Label>
        <Input
          id="password"
          type="password"
          required
          minLength={12}
          placeholder="Min 12 characters"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />
        <p className="text-[11px] text-muted-foreground">
          Already have a parent account from another school? Enter your existing
          password to link this child to the same login.
        </p>
      </div>

      <Button type="submit" size="lg" className="w-full" disabled={submitting}>
        {submitting ? (
          <>
            <Loader2 className="h-4 w-4 animate-spin" />
            Verifying...
          </>
        ) : (
          <>
            <HeartHandshake className="h-4 w-4" />
            Verify Parent Link
          </>
        )}
      </Button>
    </form>
  );
}

export default function ParentVerifyPage() {
  return (
    <AuthShell
      badge="Parent / Guardian Verification"
      title="Verify your parent invitation"
      subtitle="Confirm your email and link your parent account securely."
      footer={
        <Link href="/login" className="font-semibold text-primary hover:underline">
          Back to Sign In
        </Link>
      }
    >
      <React.Suspense fallback={<div className="h-44 animate-pulse rounded-xl bg-muted" />}>
        <ParentVerifyForm />
      </React.Suspense>
    </AuthShell>
  );
}
