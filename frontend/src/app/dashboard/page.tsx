"use client";

import {
  Building2,
  CheckCircle2,
  Clock,
  GraduationCap,
  Shield,
} from "lucide-react";
import { PortalShell } from "@/components/layout/portal-shell";
import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { useAuth } from "@/lib/auth-context";

export default function DashboardPage() {
  const { user, activeMembership } = useAuth();

  const pendingMemberships = (user?.memberships || []).filter(
    (m) => m.status === "pending"
  );

  return (
    <PortalShell>
      <div className="space-y-6">
        {/* Clean, Restrained Header Card */}
        <div className="rounded-2xl border border-border bg-card p-6 sm:p-7">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <p className="text-xs font-semibold uppercase tracking-wider text-primary">
                Workspace Overview
              </p>
              <h1 className="mt-1 font-display text-2xl font-bold tracking-tight text-foreground">
                Welcome back, {user?.full_name}
              </h1>
              <p className="mt-1 text-sm text-muted-foreground">
                {user?.is_platform_admin
                  ? "Platform Administrator — manage schools and platform operations."
                  : activeMembership
                  ? `${activeMembership.school_name || "Your school"} · ${activeMembership.role.replace("_", " ")}`
                  : "Your account is active. Review your school memberships below."}
              </p>
            </div>
            <Badge variant="success" className="w-fit">
              <CheckCircle2 className="h-3.5 w-3.5" />
              Session Verified
            </Badge>
          </div>
        </div>

        {/* Pending approval notice if any */}
        {pendingMemberships.length > 0 && (
          <Card className="border-amber-500/30 bg-amber-500/5">
            <CardHeader className="pb-2">
              <CardTitle className="flex items-center gap-2 text-base text-amber-700 dark:text-amber-300">
                <Clock className="h-4 w-4" />
                Pending School Approval
              </CardTitle>
              <CardDescription>
                One or more school memberships are awaiting approval from your
                School Administrator before learning records become visible.
              </CardDescription>
            </CardHeader>
          </Card>
        )}

        {/* Account & School Memberships */}
        <div className="grid gap-5 md:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base">
                <Shield className="h-4 w-4 text-primary" />
                Account Overview
              </CardTitle>
              <CardDescription>
                Authenticated via HttpOnly session cookie and CSRF protection.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3 text-sm">
              <div className="flex items-center justify-between border-b border-border pb-2.5">
                <span className="text-muted-foreground">Email</span>
                <span className="font-medium text-foreground">{user?.email}</span>
              </div>
              <div className="flex items-center justify-between border-b border-border pb-2.5">
                <span className="text-muted-foreground">Platform Admin</span>
                <Badge variant={user?.is_platform_admin ? "default" : "outline"}>
                  {user?.is_platform_admin ? "Yes" : "No"}
                </Badge>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-muted-foreground">Account Status</span>
                <Badge variant="success">Active</Badge>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-base">
                <Building2 className="h-4 w-4 text-primary" />
                School Memberships
              </CardTitle>
              <CardDescription>
                Every membership is strictly scoped to its school.
              </CardDescription>
            </CardHeader>
            <CardContent>
              {user && user.memberships.length > 0 ? (
                <div className="space-y-2.5">
                  {user.memberships.map((m) => (
                    <div
                      key={m.id}
                      className="flex items-center justify-between rounded-xl border border-border bg-muted/50 px-3.5 py-2.5"
                    >
                      <div className="min-w-0">
                        <p className="truncate text-sm font-semibold text-foreground">
                          {m.school_name || m.school_id}
                        </p>
                        <p className="font-mono text-xs text-muted-foreground">
                          {m.role}
                        </p>
                      </div>
                      <Badge
                        variant={
                          m.status === "active"
                            ? "success"
                            : m.status === "pending"
                            ? "accent"
                            : "outline"
                        }
                      >
                        {m.status}
                      </Badge>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="flex items-center gap-3 rounded-xl border border-dashed border-border p-4 text-xs text-muted-foreground">
                  <GraduationCap className="h-5 w-5 shrink-0 text-muted-foreground" />
                  <span>
                    {user?.is_platform_admin
                      ? "Platform Admins manage schools without belonging to school learning records."
                      : "No school memberships linked yet."}
                  </span>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </PortalShell>
  );
}
