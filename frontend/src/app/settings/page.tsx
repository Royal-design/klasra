"use client";

import * as React from "react";
import { useMutation } from "@tanstack/react-query";
import { CheckCircle2, KeyRound, Loader2, Save, User } from "lucide-react";
import { toast } from "sonner";
import { ChangePasswordDialog } from "@/components/layout/change-password-dialog";
import { PortalShell } from "@/components/layout/portal-shell";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ApiClientError, apiRequest } from "@/lib/api-client";
import { useAuth } from "@/lib/auth-context";
import type { UserProfile } from "@/lib/types";

export default function PersonalSettingsPage() {
  const { user, refreshUser } = useAuth();
  const [fullName, setFullName] = React.useState(user?.full_name || "");
  const [pwOpen, setPwOpen] = React.useState(false);

  React.useEffect(() => {
    if (user?.full_name) {
      setFullName(user.full_name);
    }
  }, [user?.full_name]);

  const updateMutation = useMutation({
    mutationFn: () =>
      apiRequest<UserProfile>("/auth/me", {
        method: "PATCH",
        body: JSON.stringify({ full_name: fullName.trim() }),
      }),
    onSuccess: async () => {
      await refreshUser();
      toast.success("Your profile has been updated.");
    },
    onError: (err) => {
      toast.error(
        err instanceof ApiClientError ? err.message : "Could not update profile."
      );
    },
  });

  return (
    <PortalShell>
      <div className="space-y-6">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wider text-primary">
            Personal Account
          </p>
          <h1 className="mt-1 font-display text-2xl font-bold tracking-tight text-foreground">
            Profile &amp; Settings
          </h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Manage your display name, security settings, and active memberships.
          </p>
        </div>

        <div className="grid gap-6 lg:grid-cols-12">
          <Card className="lg:col-span-7">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base">
                <User className="h-4 w-4 text-primary" />
                Personal Information
              </CardTitle>
              <CardDescription>
                Your display name appears across classes, feedback, and audit records.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  if (fullName.trim().length < 2) {
                    toast.error("Full name must be at least 2 characters.");
                    return;
                  }
                  updateMutation.mutate();
                }}
                className="space-y-4"
              >
                <div className="space-y-1.5">
                  <Label htmlFor="prof-name">Full name</Label>
                  <Input
                    id="prof-name"
                    required
                    minLength={2}
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                  />
                </div>
                <div className="space-y-1.5">
                  <Label htmlFor="prof-email">Email address</Label>
                  <Input id="prof-email" value={user?.email || ""} disabled />
                  <p className="text-[11px] text-muted-foreground">
                    Email changes are managed by your school administrator.
                  </p>
                </div>
                <Button type="submit" disabled={updateMutation.isPending}>
                  {updateMutation.isPending ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Save className="h-4 w-4" />
                  )}
                  Save Profile
                </Button>
              </form>
            </CardContent>
          </Card>

          <Card className="lg:col-span-5">
            <CardHeader>
              <CardTitle className="text-base">Security &amp; Roles</CardTitle>
              <CardDescription>
                Update your password or review your assigned roles.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between rounded-xl border border-border bg-muted/40 px-4 py-3 text-sm">
                <div>
                  <p className="font-semibold text-foreground">Password</p>
                  <p className="text-xs text-muted-foreground">
                    Argon2id hashed · min 12 characters
                  </p>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPwOpen(true)}
                >
                  <KeyRound className="h-3.5 w-3.5" />
                  Change
                </Button>
              </div>

              <div className="space-y-2">
                <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  Assigned Memberships
                </p>
                {user?.is_platform_admin && (
                  <div className="flex items-center justify-between rounded-xl border border-border bg-muted/40 px-3.5 py-2.5 text-xs">
                    <span className="font-semibold text-foreground">
                      Platform Administrator
                    </span>
                    <Badge variant="success">
                      <CheckCircle2 className="h-3 w-3" />
                      Active
                    </Badge>
                  </div>
                )}
                {(user?.memberships || []).map((m) => (
                  <div
                    key={m.id}
                    className="flex items-center justify-between rounded-xl border border-border bg-muted/40 px-3.5 py-2.5 text-xs"
                  >
                    <div className="min-w-0">
                      <p className="truncate font-semibold text-foreground">
                        {m.school_name || m.school_id}
                      </p>
                      <p className="font-mono text-muted-foreground">{m.role}</p>
                    </div>
                    <Badge variant={m.status === "active" ? "success" : "accent"}>
                      {m.status}
                    </Badge>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>

      <ChangePasswordDialog open={pwOpen} onOpenChange={setPwOpen} />
    </PortalShell>
  );
}
