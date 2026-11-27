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
import { PasswordInput } from "@/components/ui/password-input";
import { ApiClientError, apiRequest } from "@/lib/api-client";
import { extractFieldErrors, studentRegisterSchema } from "@/lib/validation";

function StudentRegisterForm() {
  const searchParams = useSearchParams();
  const [codeOrToken, setCodeOrToken] = React.useState(
    searchParams.get("code") || searchParams.get("token") || ""
  );
  const [fullName, setFullName] = React.useState("");
  const [email, setEmail] = React.useState("");
  const [studentRef, setStudentRef] = React.useState("");
  const [password, setPassword] = React.useState("");
  const [confirmPassword, setConfirmPassword] = React.useState("");
  const [fieldErrors, setFieldErrors] = React.useState<Record<string, string>>({});
  const [submitting, setSubmitting] = React.useState(false);
  const [submitted, setSubmitted] = React.useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const parsed = studentRegisterSchema.safeParse({
      codeOrToken,
      fullName,
      email,
      studentRef,
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
      await apiRequest("/registrations/students", {
        method: "POST",
        body: JSON.stringify({
          email: parsed.data.email,
          full_name: parsed.data.fullName,
          password: parsed.data.password,
          code_or_token: parsed.data.codeOrToken,
          student_reference: parsed.data.studentRef || null,
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
        <CheckCircle2 className="mx-auto h-10 w-10 text-amber-500" />
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
    <form onSubmit={handleSubmit} noValidate className="space-y-4">
      <div className="space-y-1.5">
        <Label htmlFor="code">School registration code or invite token</Label>
        <Input
          id="code"
          placeholder="e.g. SCH-2026-AB12"
          value={codeOrToken}
          hasError={Boolean(fieldErrors.codeOrToken)}
          onChange={(e) => setCodeOrToken(e.target.value)}
          className="font-mono text-xs"
        />
        {fieldErrors.codeOrToken && (
          <p className="text-xs text-destructive">{fieldErrors.codeOrToken}</p>
        )}
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
      <div className="space-y-1.5">
        <Label htmlFor="fullName">Full name</Label>
        <Input
          id="fullName"
          placeholder="e.g. Amara Okafor"
          value={fullName}
          hasError={Boolean(fieldErrors.fullName)}
          onChange={(e) => setFullName(e.target.value)}
        />
        {fieldErrors.fullName && (
          <p className="text-xs text-destructive">{fieldErrors.fullName}</p>
        )}
      </div>

      <div className="space-y-1.5">
        <Label htmlFor="email">Student email</Label>
        <Input
          id="email"
          type="email"
          placeholder="amara@school.edu"
          value={email}
          hasError={Boolean(fieldErrors.email)}
          onChange={(e) => setEmail(e.target.value)}
        />
        {fieldErrors.email && (
          <p className="text-xs text-destructive">{fieldErrors.email}</p>
        )}
      </div>
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

      <div className="grid gap-4 sm:grid-cols-2">
      <div className="space-y-1.5">
        <Label htmlFor="password">Create password</Label>
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
