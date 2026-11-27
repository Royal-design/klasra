"use client";

import * as React from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Loader2, LogIn } from "lucide-react";
import { toast } from "sonner";
import { AuthShell } from "@/components/auth/auth-shell";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { PasswordInput } from "@/components/ui/password-input";
import { ApiClientError } from "@/lib/api-client";
import { useAuth } from "@/lib/auth-context";
import { extractFieldErrors, loginSchema } from "@/lib/validation";

export default function LoginPage() {
  const router = useRouter();
  const { login, user, isLoading } = useAuth();
  const [email, setEmail] = React.useState("");
  const [password, setPassword] = React.useState("");
  const [fieldErrors, setFieldErrors] = React.useState<Record<string, string>>({});
  const [submitting, setSubmitting] = React.useState(false);
  const [errorMsg, setErrorMsg] = React.useState<string | null>(null);

  React.useEffect(() => {
    if (!isLoading && user) {
      router.replace("/dashboard");
    }
  }, [isLoading, user, router]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setErrorMsg(null);

    const parsed = loginSchema.safeParse({ email, password });
    if (!parsed.success) {
      setFieldErrors(extractFieldErrors(parsed.error));
      return;
    }
    setFieldErrors({});
    setSubmitting(true);
    try {
      const profile = await login(parsed.data.email, parsed.data.password);
      toast.success(`Welcome back, ${profile.full_name}`);
      router.push("/dashboard");
    } catch (err) {
      const msg =
        err instanceof ApiClientError
          ? err.message
          : "Unable to sign in. Check your credentials and try again.";
      setErrorMsg(msg);
      toast.error(msg);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <AuthShell
      badge="Secure Portal Access"
      title="Sign in to Klasra"
      subtitle="Use your school email and password to access your portal."
      footer={
        <div className="space-y-2">
          <p>
            New student with a school code?{" "}
            <Link
              href="/register/student"
              className="font-semibold text-primary hover:underline"
            >
              Register here
            </Link>
          </p>
          <p className="text-xs">
            Have an invitation link?{" "}
            <Link href="/staff/accept" className="text-primary hover:underline">
              Staff activation
            </Link>{" "}
            ·{" "}
            <Link href="/parent/verify" className="text-primary hover:underline">
              Parent verification
            </Link>
          </p>
        </div>
      }
    >
      <form onSubmit={handleSubmit} noValidate className="space-y-4">
        {errorMsg && (
          <div
            role="alert"
            className="rounded-xl border border-destructive/30 bg-destructive/10 px-3.5 py-2.5 text-xs font-medium text-destructive"
          >
            {errorMsg}
          </div>
        )}

        <div className="space-y-1.5">
          <Label htmlFor="email">Email address</Label>
          <Input
            id="email"
            type="email"
            autoComplete="email"
            placeholder="you@school.edu"
            value={email}
            hasError={Boolean(fieldErrors.email)}
            onChange={(e) => setEmail(e.target.value)}
          />
          {fieldErrors.email && (
            <p className="text-xs text-destructive">{fieldErrors.email}</p>
          )}
        </div>

        <div className="space-y-1.5">
          <div className="flex items-center justify-between">
            <Label htmlFor="password">Password</Label>
            <Link
              href="/forgot-password"
              className="text-xs font-medium text-muted-foreground transition-colors hover:text-primary"
            >
              Forgot password?
            </Link>
          </div>
          <PasswordInput
            id="password"
            autoComplete="current-password"
            placeholder="Enter your password"
            value={password}
            hasError={Boolean(fieldErrors.password)}
            onChange={(e) => setPassword(e.target.value)}
          />
          {fieldErrors.password && (
            <p className="text-xs text-destructive">{fieldErrors.password}</p>
          )}
        </div>

        <Button type="submit" className="w-full" size="lg" disabled={submitting}>
          {submitting ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" />
              Signing in...
            </>
          ) : (
            <>
              <LogIn className="h-4 w-4" />
              Sign In
            </>
          )}
        </Button>
      </form>
    </AuthShell>
  );
}
