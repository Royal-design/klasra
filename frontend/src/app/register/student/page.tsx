"use client";

import * as React from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { CheckCircle2, Loader2, UserPlus } from "lucide-react";
import { toast } from "sonner";
import { AuthShell } from "@/components/auth/auth-shell";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ApiClientError, apiRequest } from "@/lib/api-client";

function StudentRegisterForm() {
  const searchParams = useSearchParams();
  const [codeOrToken, setCodeOrToken] = React.useState(
    searchParams.get("code") || searchParams.get("token") || ""
  );
  const [fullName, setFullName] = React.useState("");
  const [email, setEmail] = React.useState("");
  const [studentRef, setStudentRef] = React.useState("");
  const [password, setPassword] = React.useState("");
  const [submitting, setSubmitting] = React.useState(false);
  const [submitted, setSubmitted] = React.useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    try {
      await apiRequest("/registrations/students", {
        method: "POST",
        body: JSON.stringify({
          email: email.trim(),
          full_name: fullName.trim(),
          password,
          code_or_token: codeOrToken.trim(),
          student_reference: studentRef.trim() || null,
        }),
      });
      setSubmitted(true);
      toast.success("Registration submitted for school admin approval.");
    } catch (err) {
      toast.error(
        err instanceof ApiClientError
          ? err.message
          : "Could not submit student registration."
      );
    } finally {
      setSubmitting(false);
    }
  }

  if (submitted) {
    return (
      <div className="space-y-4 rounded-2xl border border-amber-500/25 bg-amber-500/10 p-5 text-center">
        <CheckCircle2 className="mx-auto h-10 w-10 text-amber-600 dark:text-amber-400" />
        <p className="text-sm font-bold text-foreground">
          Pending School Admin Approval
        </p>
        <p className="text-xs leading-relaxed text-muted-foreground">
          Your account has been created in <strong>pending</strong> status. Once
          your School Administrator approves your registration, you&apos;ll be
          notified by email and can sign in to view your classes.
        </p>
        <Button asChild variant="outline" className="w-full">
          <Link href="/login">Go to Sign In</Link>
        </Button>
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="space-y-1.5">
        <Label htmlFor="code">School registration code or invite token</Label>
        <Input
          id="code"
          required
          placeholder="e.g. SCH-2026-AB12"
          value={codeOrToken}
          onChange={(e) => setCodeOrToken(e.target.value)}
          className="font-mono text-xs"
        />
      </div>

      <div className="space-y-1.5">
        <Label htmlFor="fullName">Full name</Label>
        <Input
          id="fullName"
          required
          minLength={2}
          placeholder="e.g. Amara Okafor"
          value={fullName}
          onChange={(e) => setFullName(e.target.value)}
        />
      </div>

      <div className="space-y-1.5">
        <Label htmlFor="email">Student email</Label>
        <Input
          id="email"
          type="email"
          required
          placeholder="amara@school.edu"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
        />
      </div>

      <div className="space-y-1.5">
        <Label htmlFor="studentRef">Admission / Student ID (optional)</Label>
        <Input
          id="studentRef"
          placeholder="e.g. JSS2-041"
          value={studentRef}
          onChange={(e) => setStudentRef(e.target.value)}
          className="font-mono text-xs"
        />
      </div>

      <div className="space-y-1.5">
        <Label htmlFor="password">Create password (min 12 characters)</Label>
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
            Submitting request...
          </>
        ) : (
          <>
            <UserPlus className="h-4 w-4" />
            Submit Student Registration
          </>
        )}
      </Button>
    </form>
  );
}

export default function StudentRegisterPage() {
  return (
    <AuthShell
      badge="Student Self-Registration"
      title="Join your school"
      subtitle="Enter the registration code or invite link given by your school."
      footer={
        <p>
          Already approved?{" "}
          <Link href="/login" className="font-semibold text-primary hover:underline">
            Sign in here
          </Link>
        </p>
      }
    >
      <React.Suspense fallback={<div className="h-56 animate-pulse rounded-xl bg-muted" />}>
        <StudentRegisterForm />
      </React.Suspense>
    </AuthShell>
  );
}
