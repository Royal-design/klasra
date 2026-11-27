"use client";

import * as React from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { AlertCircle, CheckCircle2, KeyRound, Loader2 } from "lucide-react";
import { toast } from "sonner";
import { AuthShell } from "@/components/auth/auth-shell";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { PasswordInput } from "@/components/ui/password-input";
import { ApiClientError, apiRequest } from "@/lib/api-client";
import type { MessageResponse } from "@/lib/types";
import { extractFieldErrors, resetPasswordSchema } from "@/lib/validation";

function ResetPasswordForm() {
  const searchParams = useSearchParams();
  const token = (searchParams.get("token") || "").trim();
  const [newPassword, setNewPassword] = React.useState("");
  const [confirmPassword, setConfirmPassword] = React.useState("");
  const [fieldErrors, setFieldErrors] = React.useState<Record<string, string>>({});
  const [submitting, setSubmitting] = React.useState(false);
  const [done, setDone] = React.useState(false);

  if (!token) {
    return (
      <div className="space-y-4 rounded-2xl border border-destructive/25 bg-destructive/5 p-5 text-center">
        <AlertCircle className="mx-auto h-10 w-10 text-destructive" />
        <p className="text-sm font-semibold text-foreground">
          Invalid or missing reset link
        </p>
        <p className="text-xs leading-relaxed text-muted-foreground">
          Open the password reset link directly from your email, or request a
          fresh reset link below.
        </p>
        <Button asChild variant="outline" className="w-full">
          <Link href="/forgot-password">Request New Reset Link</Link>
        </Button>
      </div>
    );
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const parsed = resetPasswordSchema.safeParse({
      token,
      newPassword,
      confirmPassword,
    });
    if (!parsed.success) {
      setFieldErrors(extractFieldErrors(parsed.error));
      return;
    }
    setFieldErrors({});
    setSubmitting(true);
    try {
      await apiRequest<MessageResponse>("/auth/reset-password", {
        method: "POST",
        body: JSON.stringify({
          token: parsed.data.token,
          new_password: parsed.data.newPassword,
        }),
      });
      setDone(true);
      toast.success("Password updated! You can now sign in.");
    } catch (err) {
      toast.error(
        err instanceof ApiClientError
          ? err.message
          : "Reset link may be invalid or expired."
      );
    } finally {
      setSubmitting(false);
    }
  }

  if (done) {
    return (
      <div className="space-y-4 rounded-2xl border border-emerald-500/25 bg-emerald-500/10 p-5 text-center">
        <CheckCircle2 className="mx-auto h-10 w-10 text-emerald-500" />
        <p className="text-sm font-semibold text-foreground">
          Password updated successfully
        </p>
        <p className="text-xs text-muted-foreground">
          All previous sessions were signed out for your security.
        </p>
        <Button asChild className="w-full">
          <Link href="/login">Sign In with New Password</Link>
        </Button>
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit} noValidate className="space-y-4">
      <div className="space-y-1.5">
        <Label htmlFor="newPassword">New password</Label>
        <PasswordInput
          id="newPassword"
          autoComplete="new-password"
          placeholder="At least 12 characters"
          value={newPassword}
          hasError={Boolean(fieldErrors.newPassword)}
          onChange={(e) => setNewPassword(e.target.value)}
        />
        {fieldErrors.newPassword && (
          <p className="text-xs text-destructive">{fieldErrors.newPassword}</p>
        )}
      </div>

      <div className="space-y-1.5">
        <Label htmlFor="confirmPassword">Confirm new password</Label>
        <PasswordInput
          id="confirmPassword"
          autoComplete="new-password"
          placeholder="Re-enter your new password"
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
            Updating password...
          </>
        ) : (
          <>
            <KeyRound className="h-4 w-4" />
            Update Password
          </>
        )}
      </Button>
    </form>
  );
}

export default function ResetPasswordPage() {
  return (
    <AuthShell
      badge="Set New Password"
      title="Create a new password"
      subtitle="Choose a strong password of at least 12 characters."
      footer={
        <Link href="/login" className="font-semibold text-primary hover:underline">
          Back to Sign In
        </Link>
      }
    >
      <React.Suspense fallback={<div className="h-40 animate-pulse rounded-xl bg-muted" />}>
        <ResetPasswordForm />
      </React.Suspense>
    </AuthShell>
  );
}
