"use client";

import * as React from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Building2,
  Loader2,
  Plus,
  Search,
  ShieldAlert,
  ShieldCheck,
} from "lucide-react";
import { toast } from "sonner";
import { z } from "zod";
import { PortalShell } from "@/components/layout/portal-shell";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { EmptyState } from "@/components/ui/empty-state";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { PaginationBar } from "@/components/ui/pagination-bar";
import { PasswordInput } from "@/components/ui/password-input";
import { SelectField } from "@/components/ui/select-field";
import { ApiClientError, apiRequest } from "@/lib/api-client";
import { useAuth } from "@/lib/auth-context";
import type { PaginatedResponse, School } from "@/lib/types";
import { slugify } from "@/lib/utils";
import { extractFieldErrors, strongPasswordSchema } from "@/lib/validation";

const createSchoolSchema = z
  .object({
    name: z.string().trim().min(2, "School name must be at least 2 characters."),
    slug: z
      .string()
      .trim()
      .toLowerCase()
      .regex(
        /^[a-z0-9]+(?:-[a-z0-9]+)*$/,
        "Slug must use lowercase letters, numbers, and hyphens only."
      ),
    adminName: z.string().trim().min(2, "Admin full name is required."),
    adminEmail: z.string().trim().email("Enter a valid admin email."),
    adminPassword: strongPasswordSchema,
    confirmPassword: z.string().min(1, "Please confirm the password."),
  })
  .refine((d) => d.adminPassword === d.confirmPassword, {
    path: ["confirmPassword"],
    message: "Passwords do not match.",
  });

export default function PlatformSchoolsPage() {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const [page, setPage] = React.useState(1);
  const [q, setQ] = React.useState("");
  const [statusFilter, setStatusFilter] = React.useState("");
  const [createOpen, setCreateOpen] = React.useState(false);

  // Create form state
  const [name, setName] = React.useState("");
  const [slug, setSlug] = React.useState("");
  const [slugTouched, setSlugTouched] = React.useState(false);
  const [adminName, setAdminName] = React.useState("");
  const [adminEmail, setAdminEmail] = React.useState("");
  const [adminPassword, setAdminPassword] = React.useState("");
  const [confirmPassword, setConfirmPassword] = React.useState("");
  const [fieldErrors, setFieldErrors] = React.useState<Record<string, string>>({});

  const { data, isLoading } = useQuery<PaginatedResponse<School>>({
    queryKey: ["platform", "schools", page, q, statusFilter],
    queryFn: () => {
      const params = new URLSearchParams({
        page: String(page),
        page_size: "12",
      });
      if (q.trim()) params.set("q", q.trim());
      if (statusFilter) params.set("status", statusFilter);
      return apiRequest<PaginatedResponse<School>>(`/schools?${params.toString()}`);
    },
    enabled: Boolean(user?.is_platform_admin),
  });

  const createMutation = useMutation({
    mutationFn: (payload: z.infer<typeof createSchoolSchema>) =>
      apiRequest("/schools", {
        method: "POST",
        body: JSON.stringify({
          name: payload.name,
          slug: payload.slug,
          initial_admin: {
            full_name: payload.adminName,
            email: payload.adminEmail,
            password: payload.adminPassword,
          },
        }),
      }),
    onSuccess: () => {
      toast.success("School created with its initial administrator.");
      setCreateOpen(false);
      setName("");
      setSlug("");
      setSlugTouched(false);
      setAdminName("");
      setAdminEmail("");
      setAdminPassword("");
      setConfirmPassword("");
      setFieldErrors({});
      queryClient.invalidateQueries({ queryKey: ["platform", "schools"] });
    },
    onError: (err) => {
      toast.error(
        err instanceof ApiClientError ? err.message : "Failed to create school."
      );
    },
  });

  const toggleStatusMutation = useMutation({
    mutationFn: ({ schoolId, nextStatus }: { schoolId: string; nextStatus: string }) =>
      apiRequest<School>(`/schools/${schoolId}`, {
        method: "PATCH",
        body: JSON.stringify({ status: nextStatus }),
      }),
    onSuccess: (updated) => {
      toast.success(
        `${updated.name} is now ${updated.status}.`
      );
      queryClient.invalidateQueries({ queryKey: ["platform", "schools"] });
    },
    onError: (err) => {
      toast.error(
        err instanceof ApiClientError ? err.message : "Could not update school."
      );
    },
  });

  function handleCreateSubmit(e: React.FormEvent) {
    e.preventDefault();
    const parsed = createSchoolSchema.safeParse({
      name,
      slug,
      adminName,
      adminEmail,
      adminPassword,
      confirmPassword,
    });
    if (!parsed.success) {
      setFieldErrors(extractFieldErrors(parsed.error));
      return;
    }
    setFieldErrors({});
    createMutation.mutate(parsed.data);
  }

  return (
    <PortalShell>
      {!user?.is_platform_admin ? (
        <EmptyState
          icon={ShieldAlert}
          title="Platform Administrator access required"
          description="Only platform administrators can onboard and manage schools."
        />
      ) : (
        <div className="space-y-6">
          <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <p className="text-xs font-semibold uppercase tracking-wider text-primary">
                Platform Operations
              </p>
              <h1 className="mt-1 font-display text-2xl font-bold tracking-tight text-foreground">
                Schools Directory
              </h1>
              <p className="mt-1 text-sm text-muted-foreground">
                Onboard isolated secondary schools and manage their platform status.
              </p>
            </div>
            <Button onClick={() => setCreateOpen(true)}>
              <Plus className="h-4 w-4" />
              Onboard School
            </Button>
          </div>

          {/* Filters */}
          <Card>
            <CardContent className="flex flex-col gap-3 p-4 sm:flex-row">
              <div className="relative flex-1">
                <Search className="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                <Input
                  placeholder="Search by school name or slug..."
                  value={q}
                  onChange={(e) => {
                    setQ(e.target.value);
                    setPage(1);
                  }}
                  className="pl-10"
                />
              </div>
              <SelectField
                value={statusFilter}
                onChange={(e) => {
                  setStatusFilter(e.target.value);
                  setPage(1);
                }}
                className="sm:w-44"
                aria-label="Filter by status"
              >
                <option value="">All statuses</option>
                <option value="active">Active</option>
                <option value="suspended">Suspended</option>
              </SelectField>
            </CardContent>
          </Card>

          {/* Schools List */}
          {isLoading ? (
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {[1, 2, 3].map((i) => (
                <div
                  key={i}
                  className="h-36 animate-pulse rounded-2xl border border-border bg-card"
                />
              ))}
            </div>
          ) : !data || data.items.length === 0 ? (
            <EmptyState
              icon={Building2}
              title="No schools found"
              description="Create your first secondary school to provision an isolated tenant and initial School Administrator."
              action={
                <Button onClick={() => setCreateOpen(true)}>
                  <Plus className="h-4 w-4" />
                  Onboard School
                </Button>
              }
            />
          ) : (
            <div className="space-y-4">
              <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                {data.items.map((school) => (
                  <Card key={school.id} className="flex flex-col justify-between">
                    <CardHeader className="pb-3">
                      <div className="flex items-start justify-between gap-2">
                        <div className="min-w-0">
                          <CardTitle className="truncate text-base">
                            {school.name}
                          </CardTitle>
                          <p className="mt-0.5 font-mono text-xs text-muted-foreground">
                            /{school.slug}
                          </p>
                        </div>
                        <Badge
                          variant={
                            school.status === "active" ? "success" : "accent"
                          }
                        >
                          {school.status}
                        </Badge>
                      </div>
                    </CardHeader>
                    <CardContent className="flex items-center justify-between border-t border-border pt-3">
                      <span className="font-mono text-[11px] text-muted-foreground">
                        {new Date(school.created_at).toLocaleDateString()}
                      </span>
                      <Button
                        variant="outline"
                        size="sm"
                        disabled={toggleStatusMutation.isPending}
                        onClick={() =>
                          toggleStatusMutation.mutate({
                            schoolId: school.id,
                            nextStatus:
                              school.status === "active" ? "suspended" : "active",
                          })
                        }
                      >
                        {school.status === "active" ? (
                          <>
                            <ShieldAlert className="h-3.5 w-3.5" />
                            Suspend
                          </>
                        ) : (
                          <>
                            <ShieldCheck className="h-3.5 w-3.5" />
                            Reactivate
                          </>
                        )}
                      </Button>
                    </CardContent>
                  </Card>
                ))}
              </div>

              <PaginationBar meta={data.meta} onPageChange={setPage} />
            </div>
          )}

          {/* Create School Modal */}
          <Dialog open={createOpen} onOpenChange={setCreateOpen}>
            <DialogContent className="max-w-lg">
              <DialogHeader>
                <DialogTitle>Onboard a new school</DialogTitle>
                <DialogDescription>
                  Provision an isolated school workspace and its first School
                  Administrator account.
                </DialogDescription>
              </DialogHeader>

              <form onSubmit={handleCreateSubmit} noValidate className="mt-4 space-y-4">
                <div className="grid gap-4 sm:grid-cols-2">
                  <div className="space-y-1.5">
                    <Label htmlFor="school-name">School name</Label>
                    <Input
                      id="school-name"
                      placeholder="e.g. Greenfield High"
                      value={name}
                      hasError={Boolean(fieldErrors.name)}
                      onChange={(e) => {
                        const nextName = e.target.value;
                        setName(nextName);
                        if (!slugTouched) {
                          setSlug(slugify(nextName));
                        }
                      }}
                    />
                    {fieldErrors.name && (
                      <p className="text-xs text-destructive">{fieldErrors.name}</p>
                    )}
                  </div>
                  <div className="space-y-1.5">
                    <Label htmlFor="school-slug">URL slug</Label>
                    <Input
                      id="school-slug"
                      placeholder="greenfield-high"
                      value={slug}
                      hasError={Boolean(fieldErrors.slug)}
                      onChange={(e) => {
                        const val = e.target.value;
                        setSlug(val);
                        setSlugTouched(val.trim().length > 0);
                      }}
                      className="font-mono text-xs"
                    />
                    {fieldErrors.slug && (
                      <p className="text-xs text-destructive">{fieldErrors.slug}</p>
                    )}
                  </div>
                </div>

                <div className="border-t border-border pt-3">
                  <p className="mb-3 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                    Initial School Administrator
                  </p>
                  <div className="grid gap-4 sm:grid-cols-2">
                    <div className="space-y-1.5">
                      <Label htmlFor="admin-name">Full name</Label>
                      <Input
                        id="admin-name"
                        placeholder="Principal name"
                        value={adminName}
                        hasError={Boolean(fieldErrors.adminName)}
                        onChange={(e) => setAdminName(e.target.value)}
                      />
                      {fieldErrors.adminName && (
                        <p className="text-xs text-destructive">
                          {fieldErrors.adminName}
                        </p>
                      )}
                    </div>
                    <div className="space-y-1.5">
                      <Label htmlFor="admin-email">Email</Label>
                      <Input
                        id="admin-email"
                        type="email"
                        placeholder="admin@school.edu"
                        value={adminEmail}
                        hasError={Boolean(fieldErrors.adminEmail)}
                        onChange={(e) => setAdminEmail(e.target.value)}
                      />
                      {fieldErrors.adminEmail && (
                        <p className="text-xs text-destructive">
                          {fieldErrors.adminEmail}
                        </p>
                      )}
                    </div>
                  </div>
                </div>

                <div className="grid gap-4 sm:grid-cols-2">
                  <div className="space-y-1.5">
                    <Label htmlFor="admin-pw">Password (min 12 chars)</Label>
                    <PasswordInput
                      id="admin-pw"
                      value={adminPassword}
                      hasError={Boolean(fieldErrors.adminPassword)}
                      onChange={(e) => setAdminPassword(e.target.value)}
                    />
                    {fieldErrors.adminPassword && (
                      <p className="text-xs text-destructive">
                        {fieldErrors.adminPassword}
                      </p>
                    )}
                  </div>
                  <div className="space-y-1.5">
                    <Label htmlFor="admin-confirm">Confirm password</Label>
                    <PasswordInput
                      id="admin-confirm"
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

                <div className="flex justify-end gap-2 pt-2">
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => setCreateOpen(false)}
                  >
                    Cancel
                  </Button>
                  <Button type="submit" disabled={createMutation.isPending}>
                    {createMutation.isPending ? (
                      <>
                        <Loader2 className="h-4 w-4 animate-spin" />
                        Creating...
                      </>
                    ) : (
                      "Create School"
                    )}
                  </Button>
                </div>
              </form>
            </DialogContent>
          </Dialog>
        </div>
      )}
    </PortalShell>
  );
}
