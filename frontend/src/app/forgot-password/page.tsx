"use client";

import * as React from "react";
import Link from "next/link";
import { CheckCircle2, Loader2, Mail } from "lucide-react";
import { toast } from "sonner";
import { AuthShell } from "@/components/auth/auth-shell";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ApiClientError, apiRequest } from "@/lib/api-client";
import type { MessageResponse } from "@/lib/types";
import { extractFieldErrors, forgotPasswordSchema } from "@/lib/validation";

export default function ForgotPasswordPage() {
  const [email, setEmail] = React.useState("");
  const [fieldErrors, setFieldErrors] = React.useState<Record<string, string>>({});
  const [submitting, setSubmitting] = React.useState(false);
  const [sent, setSent] = React.useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const parsed = forgotPasswordSchema.safeParse({ email });
    if (!parsed.success) {
      setFieldErrors(extractFieldErrors(parsed.error));
      return;
    }
    setFieldErrors({});
    setSubmitting(true);
    try {
      await apiRequest<MessageResponse>("/auth/forgot-password", {
        method: "POST",
        body: JSON.stringify({ email: parsed.data.email }),
      });
      setSent(true);
      toast.success("If an account exists, a reset link has been sent.");
    } catch (err) {
      toast.error(
        err instanceof ApiClientError
          ? err.message
          : "Unable to request password reset."
      );
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <AuthShell
      badge="Account Recovery"
      title="Reset your password"
      subtitle="Enter your email address and we will send a single-use password reset link."
      footer={
        <p>
          Remembered your password?{" "}
          <Link href="/login" className="font-semibold text-primary hover:underline">
            Back to Sign In
          </Link>
        </p>
      }
    >
      {sent ? (
        <div className="space-y-4 rounded-2xl border border-emerald-500/25 bg-emerald-500/10 p-5 text-center">
          <CheckCircle2 className="mx-auto h-10 w-10 text-emerald-500" />
          <p className="text-sm font-semibold text-foreground">
            Check your inbox
          </p>
          <p className="text-xs leading-relaxed text-muted-foreground">
            If an active account matches <strong>{email}</strong>, a 30-minute
            password reset link has been sent.
          </p>
          <Button variant="outline" asChild className="w-full">
            <Link href="/login">Return to Sign In</Link>
          </Button>
        </div>
      ) : (
        <form onSubmit={handleSubmit} noValidate className="space-y-4">
          <div className="space-y-1.5">
            <Label htmlFor="email">Email address</Label>
            <Input
              id="email"
              type="email"
              placeholder="you@school.edu"
              value={email}
              hasError={Boolean(fieldErrors.email)}
              onChange={(e) => setEmail(e.target.value)}
            />
            {fieldErrors.email && (
              <p className="text-xs text-destructive">{fieldErrors.email}</p>
            )}
          </div>
          <Button type="submit" size="lg" className="w-full" disabled={submitting}>
            {submitting ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                Sending reset link...
              </>
            ) : (
              <>
                <Mail className="h-4 w-4" />
                Send Reset Link
              </>
            )}
          </Button>
        </form>
      )}
    </AuthShell>
  );
}
