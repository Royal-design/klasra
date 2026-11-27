"use client";

import * as React from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  CheckCircle2,
  HeartHandshake,
  Loader2,
  Mail,
  Search,
  XCircle,
} from "lucide-react";
import { toast } from "sonner";
import { PortalShell } from "@/components/layout/portal-shell";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { PaginationBar } from "@/components/ui/pagination-bar";
import { SelectField } from "@/components/ui/select-field";
import { ApiClientError, apiRequest } from "@/lib/api-client";
import { useAuth } from "@/lib/auth-context";
import type { GuardianLink, PaginatedResponse, SchoolUser } from "@/lib/types";

const RELATIONSHIP_PRESETS = [
  "Mother",
  "Father",
  "Guardian",
  "Legal Guardian",
  "Grandparent",
  "Sponsor",
];

export default function SchoolGuardiansPage() {
  const { activeMembership } = useAuth();
  const schoolId = activeMembership?.school_id;
  const isSchoolAdmin = activeMembership?.role === "school_admin";
  const queryClient = useQueryClient();

  const [page, setPage] = React.useState(1);
  const [q, setQ] = React.useState("");
  const [statusFilter, setStatusFilter] = React.useState("");

  // Invite form state
  const [studentId, setStudentId] = React.useState("");
  const [guardianName, setGuardianName] = React.useState("");
  const [guardianEmail, setGuardianEmail] = React.useState("");
  const [relationship, setRelationship] = React.useState("Mother");
  const [customRelationship, setCustomRelationship] = React.useState("");

  const enabled = Boolean(schoolId && isSchoolAdmin);

  const studentsQuery = useQuery<PaginatedResponse<SchoolUser>>({
    queryKey: ["school", schoolId, "users", "student"],
    queryFn: () =>
      apiRequest(`/schools/${schoolId}/users?role=student&status=active&page_size=100`),
    enabled,
  });

  const linksQuery = useQuery<PaginatedResponse<GuardianLink>>({
    queryKey: ["school", schoolId, "guardian-links", page, q, statusFilter],
    queryFn: () => {
      const params = new URLSearchParams({ page: String(page), page_size: "15" });
      if (q.trim()) params.set("q", q.trim());
      if (statusFilter) params.set("status", statusFilter);
      return apiRequest(`/schools/${schoolId}/guardian-links?${params.toString()}`);
    },
    enabled,
  });

  const inviteMutation = useMutation({
    mutationFn: () => {
      const finalLabel =
        relationship === "__other__" ? customRelationship.trim() : relationship;
      return apiRequest(`/schools/${schoolId}/guardian-links/invite`, {
        method: "POST",
        body: JSON.stringify({
          student_user_id: studentId || studentsQuery.data?.items[0]?.user_id,
          guardian_full_name: guardianName,
          guardian_email: guardianEmail,
          relationship_label: finalLabel || "Guardian",
        }),
      });
    },
    onSuccess: () => {
      toast.success("Guardian verification email sent.");
      setGuardianName("");
      setGuardianEmail("");
      setCustomRelationship("");
      queryClient.invalidateQueries({ queryKey: ["school", schoolId, "guardian-links"] });
    },
    onError: (err) => {
      toast.error(err instanceof ApiClientError ? err.message : "Could not send invite.");
    },
  });

  const decideMutation = useMutation({
    mutationFn: ({ id, action }: { id: string; action: "approve" | "revoke" }) =>
      apiRequest(`/schools/${schoolId}/guardian-links/${id}/${action}`, {
        method: "POST",
        body: JSON.stringify({}),
      }),
    onSuccess: (_res, vars) => {
      toast.success(
        vars.action === "approve"
          ? "Guardian link approved."
          : "Guardian link revoked."
      );
      queryClient.invalidateQueries({ queryKey: ["school", schoolId, "guardian-links"] });
    },
    onError: (err) => {
      toast.error(err instanceof ApiClientError ? err.message : "Action failed.");
    },
  });

  const students = studentsQuery.data?.items || [];
  const links = linksQuery.data?.items || [];

  return (
    <PortalShell>
      {!isSchoolAdmin || !schoolId ? (
        <EmptyState
          icon={HeartHandshake}
          title="School Administrator access required"
          description="Only School Administrators can invite, approve, and revoke guardian links."
        />
      ) : (
        <div className="space-y-6">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wider text-primary">
              Family Governance
            </p>
            <h1 className="mt-1 font-display text-2xl font-bold tracking-tight text-foreground">
              Parent &amp; Guardian Links
            </h1>
            <p className="mt-1 text-sm text-muted-foreground">
              Invite parents from school records, approve verified links, and revoke
              access immediately when needed.
            </p>
          </div>

          <div className="grid gap-6 lg:grid-cols-12">
            {/* Invite Form */}
            <Card className="lg:col-span-5">
              <CardHeader>
                <CardTitle className="text-base">Invite Parent / Guardian</CardTitle>
              </CardHeader>
              <CardContent>
                <form
                  onSubmit={(e) => {
                    e.preventDefault();
                    inviteMutation.mutate();
                  }}
                  className="space-y-4"
                >
                  <div className="space-y-1.5">
                    <Label htmlFor="g-student">Student</Label>
                    <SelectField
                      id="g-student"
                      required
                      value={studentId || students[0]?.user_id || ""}
                      onChange={(e) => setStudentId(e.target.value)}
                    >
                      <option value="">Select active student</option>
                      {students.map((s) => (
                        <option key={s.user_id} value={s.user_id}>
                          {s.full_name} ({s.email})
                        </option>
                      ))}
                    </SelectField>
                  </div>

                  <div className="space-y-1.5">
                    <Label htmlFor="g-name">Guardian full name</Label>
                    <Input
                      id="g-name"
                      required
                      placeholder="e.g. Mrs. Ngozi Okafor"
                      value={guardianName}
                      onChange={(e) => setGuardianName(e.target.value)}
                    />
                  </div>

                  <div className="space-y-1.5">
                    <Label htmlFor="g-email">Guardian email</Label>
                    <Input
                      id="g-email"
                      type="email"
                      required
                      placeholder="parent@example.com"
                      value={guardianEmail}
                      onChange={(e) => setGuardianEmail(e.target.value)}
                    />
                  </div>

                  <div className="space-y-1.5">
                    <Label htmlFor="g-rel">Relationship label</Label>
                    <SelectField
                      id="g-rel"
                      value={relationship}
                      onChange={(e) => setRelationship(e.target.value)}
                    >
                      {RELATIONSHIP_PRESETS.map((label) => (
                        <option key={label} value={label}>
                          {label}
                        </option>
                      ))}
                      <option value="__other__">Other (custom)</option>
                    </SelectField>
                  </div>

                  {relationship === "__other__" && (
                    <div className="space-y-1.5">
                      <Label htmlFor="g-custom">Custom relationship</Label>
                      <Input
                        id="g-custom"
                        required
                        placeholder="e.g. Aunt, Uncle"
                        value={customRelationship}
                        onChange={(e) => setCustomRelationship(e.target.value)}
                      />
                    </div>
                  )}

                  <Button type="submit" disabled={inviteMutation.isPending}>
                    {inviteMutation.isPending ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <Mail className="h-4 w-4" />
                    )}
                    Send Guardian Invite
                  </Button>
                </form>
              </CardContent>
            </Card>

            {/* Links Directory */}
            <Card className="lg:col-span-7">
              <CardHeader className="pb-3">
                <CardTitle className="text-base">Guardian Links</CardTitle>
                <div className="mt-3 flex flex-col gap-2 sm:flex-row">
                  <div className="relative flex-1">
                    <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                    <Input
                      placeholder="Search guardian or student..."
                      value={q}
                      onChange={(e) => {
                        setQ(e.target.value);
                        setPage(1);
                      }}
                      className="pl-9"
                    />
                  </div>
                  <SelectField
                    value={statusFilter}
                    onChange={(e) => {
                      setStatusFilter(e.target.value);
                      setPage(1);
                    }}
                    className="sm:w-44"
                  >
                    <option value="">All statuses</option>
                    <option value="invited">Invited</option>
                    <option value="pending_approval">Pending Approval</option>
                    <option value="approved">Approved</option>
                    <option value="revoked">Revoked</option>
                  </SelectField>
                </div>
              </CardHeader>

              <CardContent className="space-y-2.5">
                {links.length === 0 ? (
                  <EmptyState
                    icon={HeartHandshake}
                    title="No guardian links found"
                    description="Invite a parent or guardian to start the verified approval flow."
                  />
                ) : (
                  links.map((link) => (
                    <div
                      key={link.id}
                      className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-border bg-muted/40 px-4 py-3"
                    >
                      <div className="min-w-0">
                        <p className="truncate text-sm font-semibold text-foreground">
                          {link.guardian_full_name}{" "}
                          <span className="font-normal text-muted-foreground">
                            ({link.relationship_label})
                          </span>
                        </p>
                        <p className="truncate text-xs text-muted-foreground">
                          {link.guardian_email} → Student:{" "}
                          <strong className="text-foreground">
                            {link.student_full_name || link.student_user_id}
                          </strong>
                        </p>
                      </div>

                      <div className="flex items-center gap-2">
                        <Badge
                          variant={
                            link.status === "approved"
                              ? "success"
                              : link.status === "pending_approval"
                              ? "accent"
                              : "outline"
                          }
                        >
                          {link.status.replace("_", " ")}
                        </Badge>
                        {link.status === "pending_approval" && (
                          <Button
                            size="sm"
                            onClick={() =>
                              decideMutation.mutate({ id: link.id, action: "approve" })
                            }
                          >
                            <CheckCircle2 className="h-3.5 w-3.5" />
                            Approve
                          </Button>
                        )}
                        {link.status !== "revoked" && (
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() =>
                              decideMutation.mutate({ id: link.id, action: "revoke" })
                            }
                          >
                            <XCircle className="h-3.5 w-3.5" />
                            Revoke
                          </Button>
                        )}
                      </div>
                    </div>
                  ))
                )}
                <PaginationBar meta={linksQuery.data?.meta} onPageChange={setPage} />
              </CardContent>
            </Card>
          </div>
        </div>
      )}
    </PortalShell>
  );
}
