"use client";

import * as React from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  BookOpen,
  Building2,
  Calendar,
  GraduationCap,
  Layers,
  Loader2,
  Plus,
  Users,
} from "lucide-react";
import { toast } from "sonner";
import { PortalShell } from "@/components/layout/portal-shell";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { SelectField } from "@/components/ui/select-field";
import { ApiClientError, apiRequest } from "@/lib/api-client";
import { useAuth } from "@/lib/auth-context";
import type {
  AcademicYear,
  ClassGroup,
  Enrollment,
  PaginatedResponse,
  SchoolUser,
  Subject,
  SubjectOffering,
  Term,
  YearLevel,
} from "@/lib/types";
import { cn } from "@/lib/utils";

type TabKey =
  | "years"
  | "terms"
  | "levels"
  | "classes"
  | "subjects"
  | "offerings"
  | "enrollments";

const TABS: Array<{ key: TabKey; label: string }> = [
  { key: "years", label: "Academic Years" },
  { key: "terms", label: "Terms" },
  { key: "levels", label: "Year Levels" },
  { key: "classes", label: "Class Groups" },
  { key: "subjects", label: "Subjects" },
  { key: "offerings", label: "Offerings" },
  { key: "enrollments", label: "Enrollments" },
];

export default function SchoolAcademicsPage() {
  const { activeMembership } = useAuth();
  const schoolId = activeMembership?.school_id;
  const isSchoolAdmin = activeMembership?.role === "school_admin";
  const queryClient = useQueryClient();
  const [tab, setTab] = React.useState<TabKey>("years");

  // Form states
  const [yearName, setYearName] = React.useState("");
  const [yearStart, setYearStart] = React.useState("2026-09-01");
  const [yearEnd, setYearEnd] = React.useState("2027-07-31");

  const [termYearId, setTermYearId] = React.useState("");
  const [termName, setTermName] = React.useState("");
  const [termStart, setTermStart] = React.useState("2026-09-01");
  const [termEnd, setTermEnd] = React.useState("2026-12-18");

  const [levelName, setLevelName] = React.useState("");
  const [levelOrder, setLevelOrder] = React.useState("1");

  const [cgYearId, setCgYearId] = React.useState("");
  const [cgLevelId, setCgLevelId] = React.useState("");
  const [cgName, setCgName] = React.useState("");

  const [subjectCode, setSubjectCode] = React.useState("");
  const [subjectName, setSubjectName] = React.useState("");

  const [offClassId, setOffClassId] = React.useState("");
  const [offSubjectId, setOffSubjectId] = React.useState("");
  const [offTermId, setOffTermId] = React.useState("");
  const [offTeacherId, setOffTeacherId] = React.useState("");

  const [enrStudentId, setEnrStudentId] = React.useState("");
  const [enrClassId, setEnrClassId] = React.useState("");
  const [enrDate, setEnrDate] = React.useState(
    new Date().toISOString().slice(0, 10)
  );

  const enabled = Boolean(schoolId && isSchoolAdmin);

  const yearsQuery = useQuery<PaginatedResponse<AcademicYear>>({
    queryKey: ["school", schoolId, "academic-years"],
    queryFn: () => apiRequest(`/schools/${schoolId}/academic-years?page_size=100`),
    enabled,
  });
  const termsQuery = useQuery<PaginatedResponse<Term>>({
    queryKey: ["school", schoolId, "terms"],
    queryFn: () => apiRequest(`/schools/${schoolId}/terms?page_size=100`),
    enabled,
  });
  const levelsQuery = useQuery<PaginatedResponse<YearLevel>>({
    queryKey: ["school", schoolId, "year-levels"],
    queryFn: () => apiRequest(`/schools/${schoolId}/year-levels?page_size=100`),
    enabled,
  });
  const classesQuery = useQuery<PaginatedResponse<ClassGroup>>({
    queryKey: ["school", schoolId, "class-groups"],
    queryFn: () => apiRequest(`/schools/${schoolId}/class-groups?page_size=100`),
    enabled,
  });
  const subjectsQuery = useQuery<PaginatedResponse<Subject>>({
    queryKey: ["school", schoolId, "subjects"],
    queryFn: () => apiRequest(`/schools/${schoolId}/subjects?page_size=100`),
    enabled,
  });
  const offeringsQuery = useQuery<PaginatedResponse<SubjectOffering>>({
    queryKey: ["school", schoolId, "subject-offerings"],
    queryFn: () =>
      apiRequest(`/schools/${schoolId}/subject-offerings?page_size=100`),
    enabled,
  });
  const enrollmentsQuery = useQuery<PaginatedResponse<Enrollment>>({
    queryKey: ["school", schoolId, "enrollments"],
    queryFn: () => apiRequest(`/schools/${schoolId}/enrollments?page_size=100`),
    enabled,
  });
  const teachersQuery = useQuery<PaginatedResponse<SchoolUser>>({
    queryKey: ["school", schoolId, "users", "teacher"],
    queryFn: () =>
      apiRequest(`/schools/${schoolId}/users?role=teacher&status=active&page_size=100`),
    enabled,
  });
  const studentsQuery = useQuery<PaginatedResponse<SchoolUser>>({
    queryKey: ["school", schoolId, "users", "student"],
    queryFn: () =>
      apiRequest(`/schools/${schoolId}/users?role=student&status=active&page_size=100`),
    enabled,
  });

  const createMutation = useMutation({
    mutationFn: ({ path, body }: { path: string; body: Record<string, unknown> }) =>
      apiRequest(`/schools/${schoolId}${path}`, {
        method: "POST",
        body: JSON.stringify(body),
      }),
    onSuccess: (_data, vars) => {
      toast.success("Saved successfully.");
      queryClient.invalidateQueries({ queryKey: ["school", schoolId] });
      if (vars.path === "/academic-years") setYearName("");
      if (vars.path === "/terms") setTermName("");
      if (vars.path === "/year-levels") setLevelName("");
      if (vars.path === "/class-groups") setCgName("");
      if (vars.path === "/subjects") {
        setSubjectCode("");
        setSubjectName("");
      }
    },
    onError: (err) => {
      toast.error(err instanceof ApiClientError ? err.message : "Could not save record.");
    },
  });

  const years = yearsQuery.data?.items || [];
  const terms = termsQuery.data?.items || [];
  const levels = levelsQuery.data?.items || [];
  const classes = classesQuery.data?.items || [];
  const subjects = subjectsQuery.data?.items || [];
  const offerings = offeringsQuery.data?.items || [];
  const enrollments = enrollmentsQuery.data?.items || [];
  const teachers = teachersQuery.data?.items || [];
  const students = studentsQuery.data?.items || [];

  return (
    <PortalShell>
      {!isSchoolAdmin || !schoolId ? (
        <EmptyState
          icon={Building2}
          title="School Administrator access required"
          description="Switch to an active School Admin membership to configure academic structure."
        />
      ) : (
        <div className="space-y-6">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wider text-primary">
              Academic Configuration
            </p>
            <h1 className="mt-1 font-display text-2xl font-bold tracking-tight text-foreground">
              Academic Setup &amp; Enrollments
            </h1>
            <p className="mt-1 text-sm text-muted-foreground">
              Configure years, terms, year levels, class groups, subjects, teacher
              offerings, and student enrollments.
            </p>
          </div>

          {/* Tabs */}
          <div className="flex flex-wrap gap-1.5 rounded-xl border border-border bg-card p-1.5">
            {TABS.map((t) => (
              <button
                key={t.key}
                type="button"
                onClick={() => setTab(t.key)}
                className={cn(
                  "rounded-lg px-3 py-1.5 text-xs font-semibold transition-colors cursor-pointer",
                  tab === t.key
                    ? "bg-primary text-primary-foreground"
                    : "text-muted-foreground hover:bg-muted hover:text-foreground"
                )}
              >
                {t.label}
              </button>
            ))}
          </div>

          {/* 1. Academic Years */}
          {tab === "years" && (
            <div className="grid gap-6 lg:grid-cols-12">
              <Card className="lg:col-span-5">
                <CardHeader>
                  <CardTitle className="text-base">Add Academic Year</CardTitle>
                </CardHeader>
                <CardContent>
                  <form
                    onSubmit={(e) => {
                      e.preventDefault();
                      createMutation.mutate({
                        path: "/academic-years",
                        body: {
                          name: yearName,
                          start_date: yearStart,
                          end_date: yearEnd,
                        },
                      });
                    }}
                    className="space-y-4"
                  >
                    <div className="space-y-1.5">
                      <Label htmlFor="ay-name">Name</Label>
                      <Input
                        id="ay-name"
                        required
                        placeholder="e.g. 2026/2027 Session"
                        value={yearName}
                        onChange={(e) => setYearName(e.target.value)}
                      />
                    </div>
                    <div className="grid gap-3 sm:grid-cols-2">
                      <div className="space-y-1.5">
                        <Label htmlFor="ay-start">Start date</Label>
                        <Input
                          id="ay-start"
                          type="date"
                          required
                          value={yearStart}
                          onChange={(e) => setYearStart(e.target.value)}
                        />
                      </div>
                      <div className="space-y-1.5">
                        <Label htmlFor="ay-end">End date</Label>
                        <Input
                          id="ay-end"
                          type="date"
                          required
                          value={yearEnd}
                          onChange={(e) => setYearEnd(e.target.value)}
                        />
                      </div>
                    </div>
                    <Button type="submit" disabled={createMutation.isPending}>
                      {createMutation.isPending ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                      ) : (
                        <Plus className="h-4 w-4" />
                      )}
                      Create Academic Year
                    </Button>
                  </form>
                </CardContent>
              </Card>

              <Card className="lg:col-span-7">
                <CardHeader>
                  <CardTitle className="text-base">
                    Academic Years ({years.length})
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-2.5">
                  {years.length === 0 ? (
                    <EmptyState
                      icon={Calendar}
                      title="No academic years yet"
                      description="Create your first academic session to begin setting up terms and classes."
                    />
                  ) : (
                    years.map((y) => (
                      <div
                        key={y.id}
                        className="flex items-center justify-between rounded-xl border border-border bg-muted/40 px-4 py-3"
                      >
                        <div>
                          <p className="text-sm font-semibold text-foreground">
                            {y.name}
                          </p>
                          <p className="font-mono text-xs text-muted-foreground">
                            {y.start_date} → {y.end_date}
                          </p>
                        </div>
                        <Badge variant={y.status === "active" ? "success" : "outline"}>
                          {y.status}
                        </Badge>
                      </div>
                    ))
                  )}
                </CardContent>
              </Card>
            </div>
          )}

          {/* 2. Terms */}
          {tab === "terms" && (
            <div className="grid gap-6 lg:grid-cols-12">
              <Card className="lg:col-span-5">
                <CardHeader>
                  <CardTitle className="text-base">Add Term / Semester</CardTitle>
                </CardHeader>
                <CardContent>
                  <form
                    onSubmit={(e) => {
                      e.preventDefault();
                      createMutation.mutate({
                        path: "/terms",
                        body: {
                          academic_year_id: termYearId || years[0]?.id,
                          name: termName,
                          start_date: termStart,
                          end_date: termEnd,
                        },
                      });
                    }}
                    className="space-y-4"
                  >
                    <div className="space-y-1.5">
                      <Label htmlFor="t-year">Academic year</Label>
                      <SelectField
                        id="t-year"
                        required
                        value={termYearId || years[0]?.id || ""}
                        onChange={(e) => setTermYearId(e.target.value)}
                      >
                        <option value="">Select academic year</option>
                        {years.map((y) => (
                          <option key={y.id} value={y.id}>
                            {y.name}
                          </option>
                        ))}
                      </SelectField>
                    </div>
                    <div className="space-y-1.5">
                      <Label htmlFor="t-name">Term name</Label>
                      <Input
                        id="t-name"
                        required
                        placeholder="e.g. First Term"
                        value={termName}
                        onChange={(e) => setTermName(e.target.value)}
                      />
                    </div>
                    <div className="grid gap-3 sm:grid-cols-2">
                      <div className="space-y-1.5">
                        <Label htmlFor="t-start">Start</Label>
                        <Input
                          id="t-start"
                          type="date"
                          required
                          value={termStart}
                          onChange={(e) => setTermStart(e.target.value)}
                        />
                      </div>
                      <div className="space-y-1.5">
                        <Label htmlFor="t-end">End</Label>
                        <Input
                          id="t-end"
                          type="date"
                          required
                          value={termEnd}
                          onChange={(e) => setTermEnd(e.target.value)}
                        />
                      </div>
                    </div>
                    <Button type="submit" disabled={createMutation.isPending}>
                      <Plus className="h-4 w-4" />
                      Create Term
                    </Button>
                  </form>
                </CardContent>
              </Card>

              <Card className="lg:col-span-7">
                <CardHeader>
                  <CardTitle className="text-base">Terms ({terms.length})</CardTitle>
                </CardHeader>
                <CardContent className="space-y-2.5">
                  {terms.length === 0 ? (
                    <EmptyState
                      icon={Calendar}
                      title="No terms created"
                      description="Add terms or semesters under your academic years."
                    />
                  ) : (
                    terms.map((t) => (
                      <div
                        key={t.id}
                        className="flex items-center justify-between rounded-xl border border-border bg-muted/40 px-4 py-3"
                      >
                        <div>
                          <p className="text-sm font-semibold text-foreground">
                            {t.name}
                          </p>
                          <p className="text-xs text-muted-foreground">
                            {t.academic_year_name} ·{" "}
                            <span className="font-mono">
                              {t.start_date} → {t.end_date}
                            </span>
                          </p>
                        </div>
                      </div>
                    ))
                  )}
                </CardContent>
              </Card>
            </div>
          )}

          {/* 3. Year Levels */}
          {tab === "levels" && (
            <div className="grid gap-6 lg:grid-cols-12">
              <Card className="lg:col-span-5">
                <CardHeader>
                  <CardTitle className="text-base">Add Year Level / Form</CardTitle>
                </CardHeader>
                <CardContent>
                  <form
                    onSubmit={(e) => {
                      e.preventDefault();
                      createMutation.mutate({
                        path: "/year-levels",
                        body: {
                          name: levelName,
                          display_order: Number(levelOrder) || 0,
                        },
                      });
                    }}
                    className="space-y-4"
                  >
                    <div className="space-y-1.5">
                      <Label htmlFor="yl-name">Name</Label>
                      <Input
                        id="yl-name"
                        required
                        placeholder="e.g. JSS 1 or Grade 10"
                        value={levelName}
                        onChange={(e) => setLevelName(e.target.value)}
                      />
                    </div>
                    <div className="space-y-1.5">
                      <Label htmlFor="yl-order">Display order</Label>
                      <Input
                        id="yl-order"
                        type="number"
                        min={0}
                        value={levelOrder}
                        onChange={(e) => setLevelOrder(e.target.value)}
                      />
                    </div>
                    <Button type="submit" disabled={createMutation.isPending}>
                      <Plus className="h-4 w-4" />
                      Add Year Level
                    </Button>
                  </form>
                </CardContent>
              </Card>

              <Card className="lg:col-span-7">
                <CardHeader>
                  <CardTitle className="text-base">
                    Year Levels ({levels.length})
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-2.5">
                  {levels.length === 0 ? (
                    <EmptyState
                      icon={Layers}
                      title="No year levels yet"
                      description="Define your school's levels (e.g. JSS 1–SS 3 or Year 7–12)."
                    />
                  ) : (
                    levels.map((l) => (
                      <div
                        key={l.id}
                        className="flex items-center justify-between rounded-xl border border-border bg-muted/40 px-4 py-3"
                      >
                        <span className="text-sm font-semibold text-foreground">
                          {l.name}
                        </span>
                        <span className="font-mono text-xs text-muted-foreground">
                          Order #{l.display_order}
                        </span>
                      </div>
                    ))
                  )}
                </CardContent>
              </Card>
            </div>
          )}

          {/* 4. Class Groups */}
          {tab === "classes" && (
            <div className="grid gap-6 lg:grid-cols-12">
              <Card className="lg:col-span-5">
                <CardHeader>
                  <CardTitle className="text-base">Add Class Group</CardTitle>
                </CardHeader>
                <CardContent>
                  <form
                    onSubmit={(e) => {
                      e.preventDefault();
                      createMutation.mutate({
                        path: "/class-groups",
                        body: {
                          academic_year_id: cgYearId || years[0]?.id,
                          year_level_id: cgLevelId || levels[0]?.id,
                          name: cgName,
                        },
                      });
                    }}
                    className="space-y-4"
                  >
                    <div className="space-y-1.5">
                      <Label htmlFor="cg-year">Academic year</Label>
                      <SelectField
                        id="cg-year"
                        required
                        value={cgYearId || years[0]?.id || ""}
                        onChange={(e) => setCgYearId(e.target.value)}
                      >
                        <option value="">Select year</option>
                        {years.map((y) => (
                          <option key={y.id} value={y.id}>
                            {y.name}
                          </option>
                        ))}
                      </SelectField>
                    </div>
                    <div className="space-y-1.5">
                      <Label htmlFor="cg-level">Year level</Label>
                      <SelectField
                        id="cg-level"
                        required
                        value={cgLevelId || levels[0]?.id || ""}
                        onChange={(e) => setCgLevelId(e.target.value)}
                      >
                        <option value="">Select level</option>
                        {levels.map((l) => (
                          <option key={l.id} value={l.id}>
                            {l.name}
                          </option>
                        ))}
                      </SelectField>
                    </div>
                    <div className="space-y-1.5">
                      <Label htmlFor="cg-name">Class group name</Label>
                      <Input
                        id="cg-name"
                        required
                        placeholder="e.g. SS2 Science A"
                        value={cgName}
                        onChange={(e) => setCgName(e.target.value)}
                      />
                    </div>
                    <Button type="submit" disabled={createMutation.isPending}>
                      <Plus className="h-4 w-4" />
                      Create Class Group
                    </Button>
                  </form>
                </CardContent>
              </Card>

              <Card className="lg:col-span-7">
                <CardHeader>
                  <CardTitle className="text-base">
                    Class Groups ({classes.length})
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-2.5">
                  {classes.length === 0 ? (
                    <EmptyState
                      icon={Users}
                      title="No class groups yet"
                      description="Create class groups or sections under an academic year and year level."
                    />
                  ) : (
                    classes.map((c) => (
                      <div
                        key={c.id}
                        className="flex items-center justify-between rounded-xl border border-border bg-muted/40 px-4 py-3"
                      >
                        <div>
                          <p className="text-sm font-semibold text-foreground">
                            {c.name}
                          </p>
                          <p className="text-xs text-muted-foreground">
                            {c.year_level_name} · {c.academic_year_name}
                          </p>
                        </div>
                      </div>
                    ))
                  )}
                </CardContent>
              </Card>
            </div>
          )}

          {/* 5. Subjects */}
          {tab === "subjects" && (
            <div className="grid gap-6 lg:grid-cols-12">
              <Card className="lg:col-span-5">
                <CardHeader>
                  <CardTitle className="text-base">Add Subject</CardTitle>
                </CardHeader>
                <CardContent>
                  <form
                    onSubmit={(e) => {
                      e.preventDefault();
                      createMutation.mutate({
                        path: "/subjects",
                        body: { code: subjectCode, name: subjectName },
                      });
                    }}
                    className="space-y-4"
                  >
                    <div className="space-y-1.5">
                      <Label htmlFor="subj-code">Subject code</Label>
                      <Input
                        id="subj-code"
                        required
                        placeholder="e.g. PHY201"
                        value={subjectCode}
                        onChange={(e) => setSubjectCode(e.target.value)}
                        className="font-mono text-xs"
                      />
                    </div>
                    <div className="space-y-1.5">
                      <Label htmlFor="subj-name">Subject name</Label>
                      <Input
                        id="subj-name"
                        required
                        placeholder="e.g. Physics"
                        value={subjectName}
                        onChange={(e) => setSubjectName(e.target.value)}
                      />
                    </div>
                    <Button type="submit" disabled={createMutation.isPending}>
                      <Plus className="h-4 w-4" />
                      Add Subject
                    </Button>
                  </form>
                </CardContent>
              </Card>

              <Card className="lg:col-span-7">
                <CardHeader>
                  <CardTitle className="text-base">
                    Subjects ({subjects.length})
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-2.5">
                  {subjects.length === 0 ? (
                    <EmptyState
                      icon={BookOpen}
                      title="No subjects yet"
                      description="Add subjects offered in your curriculum."
                    />
                  ) : (
                    subjects.map((s) => (
                      <div
                        key={s.id}
                        className="flex items-center justify-between rounded-xl border border-border bg-muted/40 px-4 py-3"
                      >
                        <span className="text-sm font-semibold text-foreground">
                          {s.name}
                        </span>
                        <Badge variant="outline" className="font-mono">
                          {s.code}
                        </Badge>
                      </div>
                    ))
                  )}
                </CardContent>
              </Card>
            </div>
          )}

          {/* 6. Subject Offerings */}
          {tab === "offerings" && (
            <div className="grid gap-6 lg:grid-cols-12">
              <Card className="lg:col-span-5">
                <CardHeader>
                  <CardTitle className="text-base">Create Subject Offering</CardTitle>
                </CardHeader>
                <CardContent>
                  <form
                    onSubmit={(e) => {
                      e.preventDefault();
                      createMutation.mutate({
                        path: "/subject-offerings",
                        body: {
                          class_group_id: offClassId || classes[0]?.id,
                          subject_id: offSubjectId || subjects[0]?.id,
                          term_id: offTermId || null,
                          teacher_user_ids: offTeacherId ? [offTeacherId] : [],
                        },
                      });
                    }}
                    className="space-y-4"
                  >
                    <div className="space-y-1.5">
                      <Label htmlFor="off-cg">Class group</Label>
                      <SelectField
                        id="off-cg"
                        required
                        value={offClassId || classes[0]?.id || ""}
                        onChange={(e) => setOffClassId(e.target.value)}
                      >
                        <option value="">Select class group</option>
                        {classes.map((c) => (
                          <option key={c.id} value={c.id}>
                            {c.name}
                          </option>
                        ))}
                      </SelectField>
                    </div>
                    <div className="space-y-1.5">
                      <Label htmlFor="off-subj">Subject</Label>
                      <SelectField
                        id="off-subj"
                        required
                        value={offSubjectId || subjects[0]?.id || ""}
                        onChange={(e) => setOffSubjectId(e.target.value)}
                      >
                        <option value="">Select subject</option>
                        {subjects.map((s) => (
                          <option key={s.id} value={s.id}>
                            {s.code} — {s.name}
                          </option>
                        ))}
                      </SelectField>
                    </div>
                    <div className="space-y-1.5">
                      <Label htmlFor="off-term">Term (optional)</Label>
                      <SelectField
                        id="off-term"
                        value={offTermId}
                        onChange={(e) => setOffTermId(e.target.value)}
                      >
                        <option value="">Full academic year</option>
                        {terms.map((t) => (
                          <option key={t.id} value={t.id}>
                            {t.name}
                          </option>
                        ))}
                      </SelectField>
                    </div>
                    <div className="space-y-1.5">
                      <Label htmlFor="off-teacher">Assign teacher (optional)</Label>
                      <SelectField
                        id="off-teacher"
                        value={offTeacherId}
                        onChange={(e) => setOffTeacherId(e.target.value)}
                      >
                        <option value="">Assign later</option>
                        {teachers.map((t) => (
                          <option key={t.user_id} value={t.user_id}>
                            {t.full_name} ({t.email})
                          </option>
                        ))}
                      </SelectField>
                    </div>
                    <Button type="submit" disabled={createMutation.isPending}>
                      <Plus className="h-4 w-4" />
                      Create Offering
                    </Button>
                  </form>
                </CardContent>
              </Card>

              <Card className="lg:col-span-7">
                <CardHeader>
                  <CardTitle className="text-base">
                    Subject Offerings ({offerings.length})
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-2.5">
                  {offerings.length === 0 ? (
                    <EmptyState
                      icon={BookOpen}
                      title="No subject offerings yet"
                      description="Link a subject to a class group and assign teachers."
                    />
                  ) : (
                    offerings.map((o) => (
                      <div
                        key={o.id}
                        className="rounded-xl border border-border bg-muted/40 px-4 py-3"
                      >
                        <div className="flex items-center justify-between gap-2">
                          <p className="text-sm font-semibold text-foreground">
                            {o.subject_code} · {o.subject_name} — {o.class_group_name}
                          </p>
                          <Badge variant={o.status === "active" ? "success" : "outline"}>
                            {o.status}
                          </Badge>
                        </div>
                        <p className="mt-1 text-xs text-muted-foreground">
                          Teachers:{" "}
                          {o.teachers.length > 0
                            ? o.teachers.map((t) => t.full_name).join(", ")
                            : "Unassigned"}
                        </p>
                      </div>
                    ))
                  )}
                </CardContent>
              </Card>
            </div>
          )}

          {/* 7. Enrollments */}
          {tab === "enrollments" && (
            <div className="grid gap-6 lg:grid-cols-12">
              <Card className="lg:col-span-5">
                <CardHeader>
                  <CardTitle className="text-base">Enroll Student</CardTitle>
                </CardHeader>
                <CardContent>
                  <form
                    onSubmit={(e) => {
                      e.preventDefault();
                      createMutation.mutate({
                        path: "/enrollments",
                        body: {
                          student_user_id: enrStudentId || students[0]?.user_id,
                          class_group_id: enrClassId || classes[0]?.id,
                          effective_from: enrDate,
                        },
                      });
                    }}
                    className="space-y-4"
                  >
                    <div className="space-y-1.5">
                      <Label htmlFor="enr-student">Active student</Label>
                      <SelectField
                        id="enr-student"
                        required
                        value={enrStudentId || students[0]?.user_id || ""}
                        onChange={(e) => setEnrStudentId(e.target.value)}
                      >
                        <option value="">Select student</option>
                        {students.map((s) => (
                          <option key={s.user_id} value={s.user_id}>
                            {s.full_name} ({s.email})
                          </option>
                        ))}
                      </SelectField>
                    </div>
                    <div className="space-y-1.5">
                      <Label htmlFor="enr-class">Class group</Label>
                      <SelectField
                        id="enr-class"
                        required
                        value={enrClassId || classes[0]?.id || ""}
                        onChange={(e) => setEnrClassId(e.target.value)}
                      >
                        <option value="">Select class group</option>
                        {classes.map((c) => (
                          <option key={c.id} value={c.id}>
                            {c.name}
                          </option>
                        ))}
                      </SelectField>
                    </div>
                    <div className="space-y-1.5">
                      <Label htmlFor="enr-date">Effective from</Label>
                      <Input
                        id="enr-date"
                        type="date"
                        required
                        value={enrDate}
                        onChange={(e) => setEnrDate(e.target.value)}
                      />
                    </div>
                    <Button type="submit" disabled={createMutation.isPending}>
                      <Plus className="h-4 w-4" />
                      Enroll Student
                    </Button>
                  </form>
                </CardContent>
              </Card>

              <Card className="lg:col-span-7">
                <CardHeader>
                  <CardTitle className="text-base">
                    Enrollments ({enrollments.length})
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-2.5">
                  {enrollments.length === 0 ? (
                    <EmptyState
                      icon={GraduationCap}
                      title="No enrollments yet"
                      description="Enroll active students into class groups to unlock their subject offerings."
                    />
                  ) : (
                    enrollments.map((e) => (
                      <div
                        key={e.id}
                        className="flex items-center justify-between rounded-xl border border-border bg-muted/40 px-4 py-3"
                      >
                        <div>
                          <p className="text-sm font-semibold text-foreground">
                            {e.student_full_name || e.student_user_id}
                          </p>
                          <p className="text-xs text-muted-foreground">
                            {e.class_group_name} ·{" "}
                            <span className="font-mono">From {e.effective_from}</span>
                          </p>
                        </div>
                        <Badge variant={e.status === "active" ? "success" : "outline"}>
                          {e.status}
                        </Badge>
                      </div>
                    ))
                  )}
                </CardContent>
              </Card>
            </div>
          )}
        </div>
      )}
    </PortalShell>
  );
}
