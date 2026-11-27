"use client";

import * as React from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { AlertCircle, CheckCircle2, Loader2, ShieldCheck } from "lucide-react";
import { toast } from "sonner";
import { AuthShell } from "@/components/auth/auth-shell";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { PasswordInput } from "@/components/ui/password-input";
import { ApiClientError, apiRequest } from "@/lib/api-client";
import { extractFieldErrors, staffAcceptSchema } from "@/lib/validation";

function StaffAcceptForm() {
  const searchParams = useSearchParams();
  const token = (searchParams.get("token") || "").trim();
  const [password, setPassword] = React.useState("");
  const [confirmPassword, setConfirmPassword] = React.useState("");
  const [fieldErrors, setFieldErrors] = React.useState<Record<string, string>>({});
  const [submitting, setSubmitting] = React.useState(false);
  const [activated, setActivated] = React.useState(false);

  if (!token) {
    return (
      <div className="space-y-4 rounded-2xl border border-destructive/25 bg-destructive/5 p-5 text-center">
        <AlertCircle className="mx-auto h-10 w-10 text-destructive" />
        <p className="text-sm font-semibold text-foreground">
          Invalid or missing invitation link
        </p>
        <p className="text-xs leading-relaxed text-muted-foreground">
          Please open the activation link directly from your school invitation
          email, or ask your School Administrator to resend it.
        </p>
        <Button asChild variant="outline" className="w-full">
          <Link href="/login">Back to Sign In</Link>
        </Button>
      </div>
    );
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const parsed = staffAcceptSchema.safeParse({
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
      await apiRequest("/staff-invitations/accept", {
        method: "POST",
        body: JSON.stringify({
          token: parsed.data.token,
          password: parsed.data.password,
        }),
      });
      setActivated(true);
      toast.success("Staff account activated! You can now sign in.");
    } catch (err) {
      toast.error(
        err instanceof ApiClientError
          ? err.message
          : "Invitation link is invalid or expired."
      );
    } finally {
      setSubmitting(false);
    }
  }

  if (activated) {
    return (
      <div className="space-y-4 rounded-2xl border border-emerald-500/25 bg-emerald-500/10 p-5 text-center">
        <CheckCircle2 className="mx-auto h-10 w-10 text-emerald-500" />
        <p className="text-sm font-bold text-foreground">
          Staff account activated
        </p>
        <p className="text-xs text-muted-foreground">
          Your school membership is now active. Sign in to access your classes.
        </p>
        <Button asChild className="w-full">
          <Link href="/login">Sign In Now</Link>
        </Button>
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit} noValidate className="space-y-4">
      <div className="space-y-1.5">
        <Label htmlFor="password">Set your password</Label>
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
            Activating account...
          </>
        ) : (
          <>
            <ShieldCheck className="h-4 w-4" />
            Activate Staff Account
          </>
        )}
      </Button>
    </form>
  );
}

export default function StaffAcceptPage() {
  return (
    <AuthShell
      badge="Staff & Teacher Activation"
      title="Accept your school invitation"
      subtitle="Set your password to activate your teacher or school administrator account."
      footer={
        <Link href="/login" className="font-semibold text-primary hover:underline">
          Back to Sign In
        </Link>
      }
    >
      <React.Suspense fallback={<div className="h-40 animate-pulse rounded-xl bg-muted" />}>
        <StaffAcceptForm />
      </React.Suspense>
    </AuthShell>
  );
}
