"use client";

import * as React from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { AlertCircle, CheckCircle2, HeartHandshake, Loader2 } from "lucide-react";
import { toast } from "sonner";
import { AuthShell } from "@/components/auth/auth-shell";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { PasswordInput } from "@/components/ui/password-input";
import { ApiClientError, apiRequest } from "@/lib/api-client";
import { extractFieldErrors, parentVerifySchema } from "@/lib/validation";

function ParentVerifyForm() {
  const searchParams = useSearchParams();
  const token = (searchParams.get("token") || "").trim();
  const [password, setPassword] = React.useState("");
  const [confirmPassword, setConfirmPassword] = React.useState("");
  const [fieldErrors, setFieldErrors] = React.useState<Record<string, string>>({});
  const [submitting, setSubmitting] = React.useState(false);
  const [verified, setVerified] = React.useState(false);

  if (!token) {
    return (
      <div className="space-y-4 rounded-2xl border border-destructive/25 bg-destructive/5 p-5 text-center">
        <AlertCircle className="mx-auto h-10 w-10 text-destructive" />
        <p className="text-sm font-semibold text-foreground">
          Invalid or missing verification link
        </p>
        <p className="text-xs leading-relaxed text-muted-foreground">
          Please open the verification link directly from your parent invitation
          email, or ask your child&apos;s school to resend it.
        </p>
        <Button asChild variant="outline" className="w-full">
          <Link href="/login">Back to Sign In</Link>
        </Button>
      </div>
    );
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const parsed = parentVerifySchema.safeParse({
      token,
      password,
      confirmPassword,
    });
    if (!parsed.success) {
      setFieldErrors(extractFieldErrors(parsed.error));
      return;
    }
    setFieldErrors({});
    setSubmitting(true);
    try {
      await apiRequest("/guardian-links/verify", {
        method: "POST",
        body: JSON.stringify({
          token: parsed.data.token,
          password: parsed.data.password,
        }),
      });
      setVerified(true);
      toast.success("Email verified! Waiting for school admin approval.");
    } catch (err) {
      toast.error(
        err instanceof ApiClientError
          ? err.message
          : "Verification link is invalid or expired."
      );
    } finally {
      setSubmitting(false);
    }
  }

  if (verified) {
    return (
      <div className="space-y-4 rounded-2xl border border-emerald-500/25 bg-emerald-500/10 p-5 text-center">
        <CheckCircle2 className="mx-auto h-10 w-10 text-emerald-500" />
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
    <form onSubmit={handleSubmit} noValidate className="space-y-4">
      <div className="space-y-1.5">
        <Label htmlFor="password">
          Account password (create new or enter existing)
        </Label>
        <PasswordInput
          id="password"
          autoComplete="new-password"
          placeholder="At least 12 characters"
          value={password}
          hasError={Boolean(fieldErrors.password)}
          onChange={(e) => setPassword(e.target.value)}
        />
        {fieldErrors.password && (
          <p className="text-xs text-destructive">{fieldErrors.password}</p>
        )}
        <p className="text-[11px] text-muted-foreground">
          Already have a parent account from another school? Enter your existing
          password to link this child to the same login.
        </p>
      </div>

      <div className="space-y-1.5">
        <Label htmlFor="confirmPassword">Confirm password</Label>
        <PasswordInput
          id="confirmPassword"
          autoComplete="new-password"
          placeholder="Re-enter your password"
          value={confirmPassword}
          hasError={Boolean(fieldErrors.confirmPassword)}
          onChange={(e) => setConfirmPassword(e.target.value)}
        />
        {fieldErrors.confirmPassword && (
          <p className="text-xs text-destructive">
            {fieldErrors.confirmPassword}
          </p>
        )}
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
      imageSrc="/images/parent-student.jpg"
      imageAlt="Parent and teenager reviewing school progress together"
      asideHeading="Follow every child's progress across multiple schools."
      asideDescription="One verified parent login connects you to published grades, quiz and exam scores, teacher feedback, and attendance for your approved children."
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
