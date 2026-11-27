"use client";

import * as React from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { CheckCircle2, Loader2, ShieldCheck } from "lucide-react";
import { toast } from "sonner";
import { AuthShell } from "@/components/auth/auth-shell";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ApiClientError, apiRequest } from "@/lib/api-client";

function StaffAcceptForm() {
  const searchParams = useSearchParams();
  const [token, setToken] = React.useState(searchParams.get("token") || "");
  const [password, setPassword] = React.useState("");
  const [submitting, setSubmitting] = React.useState(false);
  const [activated, setActivated] = React.useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    try {
      await apiRequest("/staff-invitations/accept", {
        method: "POST",
        body: JSON.stringify({ token: token.trim(), password }),
      });
      setActivated(true);
      toast.success("Staff account activated! You can now sign in.");
    } catch (err) {
      toast.error(
        err instanceof ApiClientError
          ? err.message
          : "Invitation token is invalid or expired."
      );
    } finally {
      setSubmitting(false);
    }
  }

  if (activated) {
    return (
      <div className="space-y-4 rounded-2xl border border-emerald-500/25 bg-emerald-500/10 p-5 text-center">
        <CheckCircle2 className="mx-auto h-10 w-10 text-emerald-600 dark:text-emerald-400" />
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
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="space-y-1.5">
        <Label htmlFor="token">Staff invitation token</Label>
        <Input
          id="token"
          required
          placeholder="Paste invitation token from email"
          value={token}
          onChange={(e) => setToken(e.target.value)}
          className="font-mono text-xs"
        />
      </div>

      <div className="space-y-1.5">
        <Label htmlFor="password">Set your password (min 12 characters)</Label>
        <Input
          id="password"
          type="password"
          required
          minLength={12}
          placeholder="Choose a strong password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />
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
