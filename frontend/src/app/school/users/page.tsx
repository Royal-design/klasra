"use client";

import * as React from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  CheckCircle2,
  Copy,
  FileSpreadsheet,
  KeyRound,
  Loader2,
  Mail,
  Plus,
  Search,
  Upload,
  UserCheck,
  Users,
  XCircle,
} from "lucide-react";
import { toast } from "sonner";
import { z } from "zod";
import { PortalShell } from "@/components/layout/portal-shell";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { PaginationBar } from "@/components/ui/pagination-bar";
import { PasswordInput } from "@/components/ui/password-input";
import { SelectField } from "@/components/ui/select-field";
import { ApiClientError, apiRequest } from "@/lib/api-client";
import { useAuth } from "@/lib/auth-context";
import type {
  ImportCommitResponse,
  ImportValidationResponse,
  PaginatedResponse,
  RegistrationCodeResponse,
  SchoolUser,
  StaffInvitation,
  StudentRegistrationRequest,
} from "@/lib/types";
import { cn } from "@/lib/utils";
import { extractFieldErrors, strongPasswordSchema } from "@/lib/validation";

type TabKey = "directory" | "staff-invites" | "registrations" | "imports";

const createUserSchema = z
  .object({
    fullName: z.string().trim().min(2, "Full name is required."),
    email: z.string().trim().email("Enter a valid email address."),
    role: z.enum(["teacher", "student", "school_admin"]),
    password: strongPasswordSchema,
    confirmPassword: z.string().min(1, "Please confirm the password."),
  })
  .refine((d) => d.password === d.confirmPassword, {
    path: ["confirmPassword"],
    message: "Passwords do not match.",
  });

export default function SchoolUsersPage() {
  const { activeMembership } = useAuth();
  const schoolId = activeMembership?.school_id;
  const isSchoolAdmin = activeMembership?.role === "school_admin";
  const queryClient = useQueryClient();

  const [tab, setTab] = React.useState<TabKey>("directory");
  const [page, setPage] = React.useState(1);
  const [q, setQ] = React.useState("");
  const [roleFilter, setRoleFilter] = React.useState("");

  // Create user form
  const [fullName, setFullName] = React.useState("");
  const [email, setEmail] = React.useState("");
  const [role, setRole] = React.useState<"teacher" | "student" | "school_admin">("teacher");
  const [password, setPassword] = React.useState("");
  const [confirmPassword, setConfirmPassword] = React.useState("");
  const [fieldErrors, setFieldErrors] = React.useState<Record<string, string>>({});

  // Staff invite form
  const [inviteName, setInviteName] = React.useState("");
  const [inviteEmail, setInviteEmail] = React.useState("");
  const [inviteRole, setInviteRole] = React.useState<"teacher" | "school_admin">("teacher");

  // Cohort code state
  const [codeLabel, setCodeLabel] = React.useState("2026 Intake");
  const [generatedCode, setGeneratedCode] = React.useState<RegistrationCodeResponse | null>(null);

  // Import state
  const [importFile, setImportFile] = React.useState<File | null>(null);
  const [validationResult, setValidationResult] =
    React.useState<ImportValidationResponse | null>(null);

  const enabled = Boolean(schoolId && isSchoolAdmin);

  const usersQuery = useQuery<PaginatedResponse<SchoolUser>>({
    queryKey: ["school", schoolId, "users", page, q, roleFilter],
    queryFn: () => {
      const params = new URLSearchParams({ page: String(page), page_size: "15" });
      if (q.trim()) params.set("q", q.trim());
      if (roleFilter) params.set("role", roleFilter);
      return apiRequest(`/schools/${schoolId}/users?${params.toString()}`);
    },
    enabled: enabled && tab === "directory",
  });

  const staffInvitesQuery = useQuery<PaginatedResponse<StaffInvitation>>({
    queryKey: ["school", schoolId, "staff-invitations"],
    queryFn: () => apiRequest(`/schools/${schoolId}/staff-invitations?page_size=50`),
    enabled: enabled && tab === "staff-invites",
  });

  const registrationsQuery = useQuery<PaginatedResponse<StudentRegistrationRequest>>({
    queryKey: ["school", schoolId, "registrations"],
    queryFn: () => apiRequest(`/schools/${schoolId}/registrations/students?page_size=50`),
    enabled: enabled && tab === "registrations",
  });

  const createUserMutation = useMutation({
    mutationFn: (payload: z.infer<typeof createUserSchema>) =>
      apiRequest(`/schools/${schoolId}/users`, {
        method: "POST",
        body: JSON.stringify({
          full_name: payload.fullName,
          email: payload.email,
          role: payload.role,
          password: payload.password,
        }),
      }),
    onSuccess: () => {
      toast.success("School user created.");
      setFullName("");
      setEmail("");
      setPassword("");
      setConfirmPassword("");
      setFieldErrors({});
      queryClient.invalidateQueries({ queryKey: ["school", schoolId, "users"] });
    },
    onError: (err) => {
      toast.error(err instanceof ApiClientError ? err.message : "Could not create user.");
    },
  });

  const updateMembershipMutation = useMutation({
    mutationFn: ({ membershipId, status }: { membershipId: string; status: string }) =>
      apiRequest(`/schools/${schoolId}/memberships/${membershipId}`, {
        method: "PATCH",
        body: JSON.stringify({ status }),
      }),
    onSuccess: () => {
      toast.success("Membership status updated.");
      queryClient.invalidateQueries({ queryKey: ["school", schoolId, "users"] });
    },
    onError: (err) => {
      toast.error(err instanceof ApiClientError ? err.message : "Could not update membership.");
    },
  });

  const sendStaffInviteMutation = useMutation({
    mutationFn: () =>
      apiRequest(`/schools/${schoolId}/staff-invitations`, {
        method: "POST",
        body: JSON.stringify({
          full_name: inviteName,
          email: inviteEmail,
          role: inviteRole,
        }),
      }),
    onSuccess: () => {
      toast.success("Staff invitation sent by email.");
      setInviteName("");
      setInviteEmail("");
      queryClient.invalidateQueries({ queryKey: ["school", schoolId, "staff-invitations"] });
    },
    onError: (err) => {
      toast.error(err instanceof ApiClientError ? err.message : "Could not send invite.");
    },
  });

  const createCodeMutation = useMutation({
    mutationFn: () =>
      apiRequest<RegistrationCodeResponse>(`/schools/${schoolId}/registrations/codes`, {
        method: "POST",
        body: JSON.stringify({ label: codeLabel, max_uses: 100, expires_in_hours: 168 }),
      }),
    onSuccess: (res) => {
      setGeneratedCode(res);
      toast.success("Student registration cohort code generated.");
    },
    onError: (err) => {
      toast.error(err instanceof ApiClientError ? err.message : "Could not generate code.");
    },
  });

  const decideRegistrationMutation = useMutation({
    mutationFn: ({ id, decision }: { id: string; decision: "approve" | "reject" }) =>
      apiRequest(`/schools/${schoolId}/registrations/students/${id}/${decision}`, {
        method: "POST",
        body: JSON.stringify({}),
      }),
    onSuccess: (_res, vars) => {
      toast.success(`Registration ${vars.decision === "approve" ? "approved" : "rejected"}.`);
      queryClient.invalidateQueries({ queryKey: ["school", schoolId, "registrations"] });
      queryClient.invalidateQueries({ queryKey: ["school", schoolId, "users"] });
    },
    onError: (err) => {
      toast.error(err instanceof ApiClientError ? err.message : "Action failed.");
    },
  });

  const validateImportMutation = useMutation({
    mutationFn: (file: File) => {
      const form = new FormData();
      form.append("file", file);
      return apiRequest<ImportValidationResponse>(`/schools/${schoolId}/imports/validate`, {
        method: "POST",
        body: form,
      });
    },
    onSuccess: (res) => {
      setValidationResult(res);
      if (res.error_count === 0) {
        toast.success(`All ${res.valid_rows} rows validated with zero errors.`);
      } else {
        toast.warning(`${res.error_count} validation errors found.`);
      }
    },
    onError: (err) => {
      toast.error(err instanceof ApiClientError ? err.message : "Validation failed.");
    },
  });

  const commitImportMutation = useMutation({
    mutationFn: (file: File) => {
      const form = new FormData();
      form.append("file", file);
      return apiRequest<ImportCommitResponse>(`/schools/${schoolId}/imports/commit`, {
        method: "POST",
        body: form,
      });
    },
    onSuccess: (res) => {
      toast.success(
        `Import committed: ${res.created_users} users, ${res.created_enrollments} enrollments.`
      );
      setImportFile(null);
      setValidationResult(null);
      queryClient.invalidateQueries({ queryKey: ["school", schoolId] });
    },
    onError: (err) => {
      toast.error(err instanceof ApiClientError ? err.message : "Import commit failed.");
    },
  });

  return (
    <PortalShell>
      {!isSchoolAdmin || !schoolId ? (
        <EmptyState
          icon={Users}
          title="School Administrator access required"
          description="Only School Administrators can manage users, invitations, registrations, and imports."
        />
      ) : (
        <div className="space-y-6">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wider text-primary">
              People &amp; Onboarding
            </p>
            <h1 className="mt-1 font-display text-2xl font-bold tracking-tight text-foreground">
              Users, Invitations &amp; Bulk Imports
            </h1>
            <p className="mt-1 text-sm text-muted-foreground">
              Manage staff and student accounts, approve student registrations, and
              import spreadsheets safely.
            </p>
          </div>

          <div className="flex flex-wrap gap-1.5 rounded-xl border border-border bg-card p-1.5">
            {(
              [
                ["directory", "User Directory"],
                ["staff-invites", "Staff Invitations"],
                ["registrations", "Student Registrations"],
                ["imports", "CSV / XLSX Import"],
              ] as const
            ).map(([key, label]) => (
              <button
                key={key}
                type="button"
                onClick={() => setTab(key)}
                className={cn(
                  "rounded-lg px-3 py-1.5 text-xs font-semibold transition-colors cursor-pointer",
                  tab === key
                    ? "bg-primary text-primary-foreground"
                    : "text-muted-foreground hover:bg-muted hover:text-foreground"
                )}
              >
                {label}
              </button>
            ))}
          </div>

          {/* Tab 1: Directory */}
          {tab === "directory" && (
            <div className="grid gap-6 lg:grid-cols-12">
              <Card className="lg:col-span-5">
                <CardHeader>
                  <CardTitle className="text-base">Create User Account</CardTitle>
                </CardHeader>
                <CardContent>
                  <form
                    noValidate
                    onSubmit={(e) => {
                      e.preventDefault();
                      const parsed = createUserSchema.safeParse({
                        fullName,
                        email,
                        role,
                        password,
                        confirmPassword,
                      });
                      if (!parsed.success) {
                        setFieldErrors(extractFieldErrors(parsed.error));
                        return;
                      }
                      setFieldErrors({});
                      createUserMutation.mutate(parsed.data);
                    }}
                    className="space-y-3.5"
                  >
                    <div className="space-y-1.5">
                      <Label htmlFor="u-name">Full name</Label>
                      <Input
                        id="u-name"
                        value={fullName}
                        hasError={Boolean(fieldErrors.fullName)}
                        onChange={(e) => setFullName(e.target.value)}
                      />
                      {fieldErrors.fullName && (
                        <p className="text-xs text-destructive">{fieldErrors.fullName}</p>
                      )}
                    </div>
                    <div className="space-y-1.5">
                      <Label htmlFor="u-email">Email</Label>
                      <Input
                        id="u-email"
                        type="email"
                        value={email}
                        hasError={Boolean(fieldErrors.email)}
                        onChange={(e) => setEmail(e.target.value)}
                      />
                      {fieldErrors.email && (
                        <p className="text-xs text-destructive">{fieldErrors.email}</p>
                      )}
                    </div>
                    <div className="space-y-1.5">
                      <Label htmlFor="u-role">Role</Label>
                      <SelectField
                        id="u-role"
                        value={role}
                        onChange={(e) =>
                          setRole(e.target.value as "teacher" | "student" | "school_admin")
                        }
                      >
                        <option value="teacher">Teacher</option>
                        <option value="student">Student</option>
                        <option value="school_admin">School Admin</option>
                      </SelectField>
                    </div>
                    <div className="space-y-1.5">
                      <Label htmlFor="u-pw">Password (min 12 chars)</Label>
                      <PasswordInput
                        id="u-pw"
                        value={password}
                        hasError={Boolean(fieldErrors.password)}
                        onChange={(e) => setPassword(e.target.value)}
                      />
                      {fieldErrors.password && (
                        <p className="text-xs text-destructive">{fieldErrors.password}</p>
                      )}
                    </div>
                    <div className="space-y-1.5">
                      <Label htmlFor="u-confirm">Confirm password</Label>
                      <PasswordInput
                        id="u-confirm"
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
                    <Button type="submit" disabled={createUserMutation.isPending}>
                      <Plus className="h-4 w-4" />
                      Create Account
                    </Button>
                  </form>
                </CardContent>
              </Card>

              <Card className="lg:col-span-7">
                <CardHeader className="pb-3">
                  <CardTitle className="text-base">School Directory</CardTitle>
                  <div className="mt-3 flex flex-col gap-2 sm:flex-row">
                    <div className="relative flex-1">
                      <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                      <Input
                        placeholder="Search name or email..."
                        value={q}
                        onChange={(e) => {
                          setQ(e.target.value);
                          setPage(1);
                        }}
                        className="pl-9"
                      />
                    </div>
                    <SelectField
                      value={roleFilter}
                      onChange={(e) => {
                        setRoleFilter(e.target.value);
                        setPage(1);
                      }}
                      className="sm:w-40"
                    >
                      <option value="">All roles</option>
                      <option value="teacher">Teacher</option>
                      <option value="student">Student</option>
                      <option value="school_admin">School Admin</option>
                    </SelectField>
                  </div>
                </CardHeader>
                <CardContent className="space-y-2.5">
                  {(usersQuery.data?.items || []).map((u) => (
                    <div
                      key={u.membership_id}
                      className="flex flex-wrap items-center justify-between gap-2 rounded-xl border border-border bg-muted/40 px-4 py-3"
                    >
                      <div className="min-w-0">
                        <p className="truncate text-sm font-semibold text-foreground">
                          {u.full_name}
                        </p>
                        <p className="truncate text-xs text-muted-foreground">
                          {u.email} · <span className="font-mono">{u.role}</span>
                        </p>
                      </div>
                      <div className="flex items-center gap-2">
                        <Badge
                          variant={
                            u.status === "active"
                              ? "success"
                              : u.status === "pending"
                              ? "accent"
                              : "outline"
                          }
                        >
                          {u.status}
                        </Badge>
                        {u.status !== "revoked" ? (
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() =>
                              updateMembershipMutation.mutate({
                                membershipId: u.membership_id,
                                status: "revoked",
                              })
                            }
                          >
                            Revoke
                          </Button>
                        ) : (
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() =>
                              updateMembershipMutation.mutate({
                                membershipId: u.membership_id,
                                status: "active",
                              })
                            }
                          >
                            Restore
                          </Button>
                        )}
                      </div>
                    </div>
                  ))}
                  <PaginationBar meta={usersQuery.data?.meta} onPageChange={setPage} />
                </CardContent>
              </Card>
            </div>
          )}

          {/* Tab 2: Staff Invitations */}
          {tab === "staff-invites" && (
            <div className="grid gap-6 lg:grid-cols-12">
              <Card className="lg:col-span-5">
                <CardHeader>
                  <CardTitle className="text-base">Invite Staff by Email</CardTitle>
                </CardHeader>
                <CardContent>
                  <form
                    onSubmit={(e) => {
                      e.preventDefault();
                      sendStaffInviteMutation.mutate();
                    }}
                    className="space-y-4"
                  >
                    <div className="space-y-1.5">
                      <Label htmlFor="si-name">Full name</Label>
                      <Input
                        id="si-name"
                        required
                        value={inviteName}
                        onChange={(e) => setInviteName(e.target.value)}
                      />
                    </div>
                    <div className="space-y-1.5">
                      <Label htmlFor="si-email">Email address</Label>
                      <Input
                        id="si-email"
                        type="email"
                        required
                        value={inviteEmail}
                        onChange={(e) => setInviteEmail(e.target.value)}
                      />
                    </div>
                    <div className="space-y-1.5">
                      <Label htmlFor="si-role">Role</Label>
                      <SelectField
                        id="si-role"
                        value={inviteRole}
                        onChange={(e) =>
                          setInviteRole(e.target.value as "teacher" | "school_admin")
                        }
                      >
                        <option value="teacher">Teacher</option>
                        <option value="school_admin">School Admin</option>
                      </SelectField>
                    </div>
                    <Button type="submit" disabled={sendStaffInviteMutation.isPending}>
                      <Mail className="h-4 w-4" />
                      Send Activation Email
                    </Button>
                  </form>
                </CardContent>
              </Card>

              <Card className="lg:col-span-7">
                <CardHeader>
                  <CardTitle className="text-base">Sent Invitations</CardTitle>
                </CardHeader>
                <CardContent className="space-y-2.5">
                  {(staffInvitesQuery.data?.items || []).length === 0 ? (
                    <EmptyState
                      icon={Mail}
                      title="No staff invitations yet"
                      description="Invite teachers or administrators so they can set their own password securely."
                    />
                  ) : (
                    (staffInvitesQuery.data?.items || []).map((inv) => (
                      <div
                        key={inv.id}
                        className="flex items-center justify-between rounded-xl border border-border bg-muted/40 px-4 py-3"
                      >
                        <div>
                          <p className="text-sm font-semibold text-foreground">
                            {inv.full_name}
                          </p>
                          <p className="text-xs text-muted-foreground">
                            {inv.email} · <span className="font-mono">{inv.role}</span>
                          </p>
                        </div>
                        <Badge
                          variant={inv.status === "accepted" ? "success" : "accent"}
                        >
                          {inv.status}
                        </Badge>
                      </div>
                    ))
                  )}
                </CardContent>
              </Card>
            </div>
          )}

          {/* Tab 3: Student Registrations & Cohort Codes */}
          {tab === "registrations" && (
            <div className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">
                    Generate Student Registration Cohort Code
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex flex-col gap-3 sm:flex-row">
                    <Input
                      placeholder="Label (e.g. 2026 SS1 Intake)"
                      value={codeLabel}
                      onChange={(e) => setCodeLabel(e.target.value)}
                      className="sm:max-w-xs"
                    />
                    <Button
                      onClick={() => createCodeMutation.mutate()}
                      disabled={createCodeMutation.isPending}
                    >
                      <KeyRound className="h-4 w-4" />
                      Generate Code
                    </Button>
                  </div>

                  {generatedCode && (
                    <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-primary/30 bg-primary/5 px-4 py-3">
                      <div>
                        <p className="text-xs font-medium text-muted-foreground">
                          Share this code with students ({generatedCode.label})
                        </p>
                        <p className="mt-0.5 font-mono text-base font-bold text-foreground">
                          {generatedCode.code}
                        </p>
                      </div>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => {
                          navigator.clipboard.writeText(generatedCode.code);
                          toast.success("Copied registration code.");
                        }}
                      >
                        <Copy className="h-3.5 w-3.5" />
                        Copy Code
                      </Button>
                    </div>
                  )}
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="text-base">
                    Pending &amp; Reviewed Student Registrations
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-2.5">
                  {(registrationsQuery.data?.items || []).length === 0 ? (
                    <EmptyState
                      icon={UserCheck}
                      title="No student registration requests"
                      description="When students self-register with a cohort code, they will appear here for approval."
                    />
                  ) : (
                    (registrationsQuery.data?.items || []).map((req) => (
                      <div
                        key={req.id}
                        className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-border bg-muted/40 px-4 py-3"
                      >
                        <div>
                          <p className="text-sm font-semibold text-foreground">
                            {req.full_name}
                          </p>
                          <p className="text-xs text-muted-foreground">
                            {req.email}
                            {req.student_reference ? ` · ID: ${req.student_reference}` : ""}
                          </p>
                        </div>
                        <div className="flex items-center gap-2">
                          <Badge
                            variant={
                              req.status === "approved"
                                ? "success"
                                : req.status === "pending"
                                ? "accent"
                                : "outline"
                            }
                          >
                            {req.status}
                          </Badge>
                          {req.status === "pending" && (
                            <>
                              <Button
                                size="sm"
                                onClick={() =>
                                  decideRegistrationMutation.mutate({
                                    id: req.id,
                                    decision: "approve",
                                  })
                                }
                              >
                                <CheckCircle2 className="h-3.5 w-3.5" />
                                Approve
                              </Button>
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() =>
                                  decideRegistrationMutation.mutate({
                                    id: req.id,
                                    decision: "reject",
                                  })
                                }
                              >
                                <XCircle className="h-3.5 w-3.5" />
                                Reject
                              </Button>
                            </>
                          )}
                        </div>
                      </div>
                    ))
                  )}
                </CardContent>
              </Card>
            </div>
          )}

          {/* Tab 4: Bulk CSV / XLSX Import */}
          {tab === "imports" && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-base">
                  <FileSpreadsheet className="h-4 w-4 text-primary" />
                  Spreadsheet Bulk Import (CSV / XLSX)
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <p className="text-xs leading-relaxed text-muted-foreground">
                  Upload a CSV or Excel (`.xlsx`) roster up to 5 MB. Run dry-run
                  validation first to catch row errors before committing accounts.
                </p>

                <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
                  <Input
                    type="file"
                    accept=".csv,.xlsx"
                    onChange={(e) => {
                      setImportFile(e.target.files?.[0] || null);
                      setValidationResult(null);
                    }}
                    className="sm:max-w-sm"
                  />
                  <Button
                    variant="outline"
                    disabled={!importFile || validateImportMutation.isPending}
                    onClick={() => importFile && validateImportMutation.mutate(importFile)}
                  >
                    {validateImportMutation.isPending ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <Upload className="h-4 w-4" />
                    )}
                    1. Validate Spreadsheet
                  </Button>
                  <Button
                    disabled={
                      !importFile ||
                      !validationResult ||
                      validationResult.error_count > 0 ||
                      commitImportMutation.isPending
                    }
                    onClick={() => importFile && commitImportMutation.mutate(importFile)}
                  >
                    {commitImportMutation.isPending ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <CheckCircle2 className="h-4 w-4" />
                    )}
                    2. Commit Import
                  </Button>
                </div>

                {validationResult && (
                  <div className="rounded-xl border border-border bg-muted/40 p-4 space-y-3">
                    <div className="flex flex-wrap gap-4 text-xs font-semibold">
                      <span>Total rows: {validationResult.total_rows}</span>
                      <span className="text-emerald-600 dark:text-emerald-400">
                        Valid: {validationResult.valid_rows}
                      </span>
                      <span className="text-destructive">
                        Errors: {validationResult.error_count}
                      </span>
                    </div>
                    {validationResult.errors.length > 0 && (
                      <div className="max-h-48 space-y-1 overflow-y-auto text-xs text-destructive">
                        {validationResult.errors.map((err, idx) => (
                          <p key={idx} className="font-mono">
                            Row {err.row_number} [{err.field}]: {err.message}
                          </p>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </CardContent>
            </Card>
          )}
        </div>
      )}
    </PortalShell>
  );
}
