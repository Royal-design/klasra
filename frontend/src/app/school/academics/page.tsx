"use client";

import * as React from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  ArrowDown,
  ArrowRightLeft,
  ArrowUp,
  BookOpen,
  Building2,
  Calendar,
  GraduationCap,
  GripVertical,
  Layers,
  Loader2,
  Pencil,
  Plus,
  Trash2,
  UserMinus,
  UserPlus,
  Users,
  X,
} from "lucide-react";
import { toast } from "sonner";
import { PortalShell } from "@/components/layout/portal-shell";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ConfirmDialog } from "@/components/ui/confirm-dialog";
import { DatePicker } from "@/components/ui/date-picker";
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

type DeleteTarget = {
  path: string;
  label: string;
  typeName: string;
};

type EditState =
  | { kind: "year"; item: AcademicYear }
  | { kind: "term"; item: Term }
  | { kind: "level"; item: YearLevel }
  | { kind: "class"; item: ClassGroup }
  | { kind: "subject"; item: Subject }
  | { kind: "offering"; item: SubjectOffering }
  | null;

export default function SchoolAcademicsPage() {
  const { activeMembership } = useAuth();
  const schoolId = activeMembership?.school_id;
  const isSchoolAdmin = activeMembership?.role === "school_admin";
  const queryClient = useQueryClient();
  const [tab, setTab] = React.useState<TabKey>("years");

  // Create form states
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
  const [cgSelectedLevelIds, setCgSelectedLevelIds] = React.useState<string[]>([]);
  const [cgSelectedPresets, setCgSelectedPresets] = React.useState<string[]>([]);
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

  // Edit / Delete / Enrollment action states
  const [editState, setEditState] = React.useState<EditState>(null);
  const [editName, setEditName] = React.useState("");
  const [editCode, setEditCode] = React.useState("");
  const [editStart, setEditStart] = React.useState("");
  const [editEnd, setEditEnd] = React.useState("");
  const [editStatus, setEditStatus] = React.useState("active");
  const [editOrder, setEditOrder] = React.useState("1");
  const [editLevelId, setEditLevelId] = React.useState("");
  const [editAssignTeacherId, setEditAssignTeacherId] = React.useState("");

  const [deleteTarget, setDeleteTarget] = React.useState<DeleteTarget | null>(null);

  const [transferTarget, setTransferTarget] = React.useState<Enrollment | null>(null);
  const [transferClassId, setTransferClassId] = React.useState("");
  const [transferDate, setTransferDate] = React.useState(
    new Date().toISOString().slice(0, 10)
  );

  const [withdrawTarget, setWithdrawTarget] = React.useState<Enrollment | null>(null);
  const [withdrawDate, setWithdrawDate] = React.useState(
    new Date().toISOString().slice(0, 10)
  );

  // Drag-and-drop state for Year Levels
  const [orderedLevels, setOrderedLevels] = React.useState<YearLevel[]>([]);
  const [draggedLevelId, setDraggedLevelId] = React.useState<string | null>(null);
  const [dragOverLevelId, setDragOverLevelId] = React.useState<string | null>(null);

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

  const years = yearsQuery.data?.items || [];
  const terms = termsQuery.data?.items || [];
  const levels = levelsQuery.data?.items || [];
  const classes = classesQuery.data?.items || [];
  const subjects = subjectsQuery.data?.items || [];
  const offerings = offeringsQuery.data?.items || [];
  const enrollments = enrollmentsQuery.data?.items || [];
  const teachers = teachersQuery.data?.items || [];
  const students = studentsQuery.data?.items || [];

  React.useEffect(() => {
    setOrderedLevels(levels);
    const maxOrder = levels.reduce((acc, l) => Math.max(acc, l.display_order), 0);
    setLevelOrder(String(maxOrder + 1));
  }, [levels]);

  const invalidateAcademic = () => {
    queryClient.invalidateQueries({ queryKey: ["school", schoolId] });
  };

  const createMutation = useMutation({
    mutationFn: ({ path, body }: { path: string; body: Record<string, unknown> }) =>
      apiRequest(`/schools/${schoolId}${path}`, {
        method: "POST",
        body: JSON.stringify(body),
      }),
    onSuccess: (_data, vars) => {
      toast.success("Saved successfully.");
      invalidateAcademic();
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

  const bulkClassGroupMutation = useMutation({
    mutationFn: (body: {
      academic_year_id: string;
      year_level_ids: string[];
      names: string[];
    }) =>
      apiRequest<{ created: ClassGroup[]; skipped_existing: number }>(
        `/schools/${schoolId}/class-groups/bulk`,
        {
          method: "POST",
          body: JSON.stringify(body),
        }
      ),
    onSuccess: (res) => {
      const createdCount = res.created.length;
      const skipped = res.skipped_existing;
      if (createdCount > 0 && skipped > 0) {
        toast.success(
          `Created ${createdCount} class group${createdCount === 1 ? "" : "s"} (${skipped} already existed).`
        );
      } else if (createdCount > 0) {
        toast.success(
          `Created ${createdCount} class group${createdCount === 1 ? "" : "s"}.`
        );
      } else {
        toast.info("All selected class groups already exist.");
      }
      setCgName("");
      setCgSelectedPresets([]);
      invalidateAcademic();
    },
    onError: (err) => {
      toast.error(
        err instanceof ApiClientError ? err.message : "Could not create class groups."
      );
    },
  });

  const formatClassLabel = (c: ClassGroup) =>
    c.year_level_name ? `${c.year_level_name} — ${c.name}` : c.name;

  const groupedClasses = React.useMemo(() => {
    const groups = new Map<
      string,
      { levelId: string; levelName: string; items: ClassGroup[] }
    >();
    for (const c of classes) {
      const key = c.year_level_id;
      const existing = groups.get(key);
      if (existing) {
        existing.items.push(c);
      } else {
        groups.set(key, {
          levelId: c.year_level_id,
          levelName: c.year_level_name || "Unassigned Level",
          items: [c],
        });
      }
    }
    return Array.from(groups.values());
  }, [classes]);

  const ARM_PRESETS = ["Science", "Art", "Commercial", "A", "B", "C"];

  const toggleCgLevel = (id: string) => {
    setCgSelectedLevelIds((prev) =>
      prev.includes(id) ? prev.filter((item) => item !== id) : [...prev, id]
    );
  };

  const toggleCgPreset = (name: string) => {
    setCgSelectedPresets((prev) =>
      prev.includes(name) ? prev.filter((item) => item !== name) : [...prev, name]
    );
  };

  const updateMutation = useMutation({
    mutationFn: ({ path, body }: { path: string; body: Record<string, unknown> }) =>
      apiRequest(`/schools/${schoolId}${path}`, {
        method: "PATCH",
        body: JSON.stringify(body),
      }),
    onSuccess: () => {
      toast.success("Changes saved.");
      invalidateAcademic();
      setEditState(null);
    },
    onError: (err) => {
      toast.error(err instanceof ApiClientError ? err.message : "Could not update record.");
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (path: string) =>
      apiRequest(`/schools/${schoolId}${path}`, { method: "DELETE" }),
    onSuccess: () => {
      toast.success("Deleted successfully.");
      invalidateAcademic();
      setDeleteTarget(null);
    },
    onError: (err) => {
      toast.error(err instanceof ApiClientError ? err.message : "Could not delete record.");
      setDeleteTarget(null);
    },
  });

  const reorderMutation = useMutation({
    mutationFn: (orderedIds: string[]) =>
      apiRequest<YearLevel[]>(`/schools/${schoolId}/year-levels/reorder`, {
        method: "PUT",
        body: JSON.stringify({ ordered_ids: orderedIds }),
      }),
    onSuccess: (updated) => {
      setOrderedLevels(updated);
      toast.success("Year level order updated.");
      invalidateAcademic();
    },
    onError: (err) => {
      setOrderedLevels(levels);
      toast.error(
        err instanceof ApiClientError ? err.message : "Could not reorder year levels."
      );
    },
  });

  const assignTeacherMutation = useMutation({
    mutationFn: ({ offeringId, teacherId }: { offeringId: string; teacherId: string }) =>
      apiRequest<SubjectOffering>(
        `/schools/${schoolId}/subject-offerings/${offeringId}/teachers`,
        {
          method: "POST",
          body: JSON.stringify({ teacher_user_id: teacherId }),
        }
      ),
    onSuccess: (updated) => {
      toast.success("Teacher assigned.");
      setEditAssignTeacherId("");
      setEditState((prev) =>
        prev && prev.kind === "offering" ? { kind: "offering", item: updated } : prev
      );
      invalidateAcademic();
    },
    onError: (err) => {
      toast.error(
        err instanceof ApiClientError ? err.message : "Could not assign teacher."
      );
    },
  });

  const unassignTeacherMutation = useMutation({
    mutationFn: ({ offeringId, teacherId }: { offeringId: string; teacherId: string }) =>
      apiRequest<SubjectOffering>(
        `/schools/${schoolId}/subject-offerings/${offeringId}/teachers/${teacherId}`,
        { method: "DELETE" }
      ),
    onSuccess: (updated) => {
      toast.success("Teacher removed from offering.");
      setEditState((prev) =>
        prev && prev.kind === "offering" ? { kind: "offering", item: updated } : prev
      );
      invalidateAcademic();
    },
    onError: (err) => {
      toast.error(
        err instanceof ApiClientError ? err.message : "Could not unassign teacher."
      );
    },
  });

  const transferMutation = useMutation({
    mutationFn: ({
      enrollmentId,
      targetClassGroupId,
      effectiveDate,
    }: {
      enrollmentId: string;
      targetClassGroupId: string;
      effectiveDate: string;
    }) =>
      apiRequest(`/schools/${schoolId}/enrollments/${enrollmentId}/transfer`, {
        method: "POST",
        body: JSON.stringify({
          target_class_group_id: targetClassGroupId,
          effective_date: effectiveDate,
        }),
      }),
    onSuccess: () => {
      toast.success("Student transferred to new class group.");
      setTransferTarget(null);
      invalidateAcademic();
    },
    onError: (err) => {
      toast.error(
        err instanceof ApiClientError ? err.message : "Could not transfer student."
      );
    },
  });

  const withdrawMutation = useMutation({
    mutationFn: ({
      enrollmentId,
      effectiveDate,
    }: {
      enrollmentId: string;
      effectiveDate: string;
    }) =>
      apiRequest(`/schools/${schoolId}/enrollments/${enrollmentId}/withdraw`, {
        method: "POST",
        body: JSON.stringify({ effective_date: effectiveDate }),
      }),
    onSuccess: () => {
      toast.success("Enrollment withdrawn.");
      setWithdrawTarget(null);
      invalidateAcademic();
    },
    onError: (err) => {
      toast.error(
        err instanceof ApiClientError ? err.message : "Could not withdraw enrollment."
      );
    },
  });

  const openEdit = (next: Exclude<EditState, null>) => {
    setEditState(next);
    if (next.kind === "year") {
      setEditName(next.item.name);
      setEditStart(next.item.start_date);
      setEditEnd(next.item.end_date);
      setEditStatus(next.item.status);
    } else if (next.kind === "term") {
      setEditName(next.item.name);
      setEditStart(next.item.start_date);
      setEditEnd(next.item.end_date);
    } else if (next.kind === "level") {
      setEditName(next.item.name);
      setEditOrder(String(next.item.display_order));
    } else if (next.kind === "class") {
      setEditName(next.item.name);
      setEditLevelId(next.item.year_level_id);
    } else if (next.kind === "subject") {
      setEditCode(next.item.code);
      setEditName(next.item.name);
    } else if (next.kind === "offering") {
      setEditStatus(next.item.status);
      setEditAssignTeacherId("");
    }
  };

  const handleEditSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!editState) return;
    if (editState.kind === "year") {
      updateMutation.mutate({
        path: `/academic-years/${editState.item.id}`,
        body: {
          name: editName,
          start_date: editStart,
          end_date: editEnd,
          status: editStatus,
        },
      });
    } else if (editState.kind === "term") {
      updateMutation.mutate({
        path: `/terms/${editState.item.id}`,
        body: { name: editName, start_date: editStart, end_date: editEnd },
      });
    } else if (editState.kind === "level") {
      updateMutation.mutate({
        path: `/year-levels/${editState.item.id}`,
        body: { name: editName, display_order: Number(editOrder) || 0 },
      });
    } else if (editState.kind === "class") {
      updateMutation.mutate({
        path: `/class-groups/${editState.item.id}`,
        body: { name: editName, year_level_id: editLevelId },
      });
    } else if (editState.kind === "subject") {
      updateMutation.mutate({
        path: `/subjects/${editState.item.id}`,
        body: { code: editCode, name: editName },
      });
    } else if (editState.kind === "offering") {
      updateMutation.mutate({
        path: `/subject-offerings/${editState.item.id}`,
        body: { status: editStatus },
      });
    }
  };

  const commitLevelReorder = (nextList: YearLevel[]) => {
    const withOrder = nextList.map((item, idx) => ({
      ...item,
      display_order: idx + 1,
    }));
    setOrderedLevels(withOrder);
    reorderMutation.mutate(withOrder.map((l) => l.id));
  };

  const moveLevelByIndex = (fromIndex: number, toIndex: number) => {
    if (
      fromIndex === toIndex ||
      fromIndex < 0 ||
      toIndex < 0 ||
      toIndex >= orderedLevels.length
    ) {
      return;
    }
    const next = [...orderedLevels];
    const [moved] = next.splice(fromIndex, 1);
    next.splice(toIndex, 0, moved);
    commitLevelReorder(next);
  };

  const handleLevelDrop = (targetId: string) => {
    if (!draggedLevelId || draggedLevelId === targetId) {
      setDraggedLevelId(null);
      setDragOverLevelId(null);
      return;
    }
    const fromIndex = orderedLevels.findIndex((l) => l.id === draggedLevelId);
    const toIndex = orderedLevels.findIndex((l) => l.id === targetId);
    setDraggedLevelId(null);
    setDragOverLevelId(null);
    moveLevelByIndex(fromIndex, toIndex);
  };

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
                      const cleanName = yearName.trim();
                      if (cleanName.length < 2) {
                        toast.error("Academic year name must be at least 2 characters.");
                        return;
                      }
                      if (!yearStart || !yearEnd) {
                        toast.error("Select both start and end dates.");
                        return;
                      }
                      if (yearEnd <= yearStart) {
                        toast.error("End date must be after start date.");
                        return;
                      }
                      createMutation.mutate({
                        path: "/academic-years",
                        body: {
                          name: cleanName,
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
                        <DatePicker
                          id="ay-start"
                          required
                          value={yearStart}
                          onChange={setYearStart}
                        />
                      </div>
                      <div className="space-y-1.5">
                        <Label htmlFor="ay-end">End date</Label>
                        <DatePicker
                          id="ay-end"
                          required
                          value={yearEnd}
                          onChange={setYearEnd}
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
                        className="flex items-center justify-between gap-3 rounded-xl border border-border bg-muted/40 px-4 py-3"
                      >
                        <div className="min-w-0">
                          <p className="truncate text-sm font-semibold text-foreground">
                            {y.name}
                          </p>
                          <p className="font-mono text-xs text-muted-foreground">
                            {y.start_date} → {y.end_date}
                          </p>
                        </div>
                        <div className="flex shrink-0 items-center gap-1.5">
                          <Badge variant={y.status === "active" ? "success" : "outline"}>
                            {y.status}
                          </Badge>
                          <Button
                            type="button"
                            variant="ghost"
                            size="icon"
                            aria-label={`Edit ${y.name}`}
                            onClick={() => openEdit({ kind: "year", item: y })}
                          >
                            <Pencil className="h-3.5 w-3.5" />
                          </Button>
                          <Button
                            type="button"
                            variant="ghost"
                            size="icon"
                            aria-label={`Delete ${y.name}`}
                            className="text-muted-foreground hover:text-destructive"
                            onClick={() =>
                              setDeleteTarget({
                                path: `/academic-years/${y.id}`,
                                label: y.name,
                                typeName: "Academic Year",
                              })
                            }
                          >
                            <Trash2 className="h-3.5 w-3.5" />
                          </Button>
                        </div>
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
                      const yearId = termYearId || years[0]?.id;
                      const cleanName = termName.trim();
                      if (!yearId) {
                        toast.error("Create or select an academic year first.");
                        return;
                      }
                      if (cleanName.length < 2) {
                        toast.error("Term name must be at least 2 characters.");
                        return;
                      }
                      if (!termStart || !termEnd) {
                        toast.error("Select both start and end dates.");
                        return;
                      }
                      if (termEnd <= termStart) {
                        toast.error("Term end date must be after start date.");
                        return;
                      }
                      createMutation.mutate({
                        path: "/terms",
                        body: {
                          academic_year_id: yearId,
                          name: cleanName,
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
                        <DatePicker
                          id="t-start"
                          required
                          value={termStart}
                          onChange={setTermStart}
                        />
                      </div>
                      <div className="space-y-1.5">
                        <Label htmlFor="t-end">End</Label>
                        <DatePicker
                          id="t-end"
                          required
                          value={termEnd}
                          onChange={setTermEnd}
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
                        className="flex items-center justify-between gap-3 rounded-xl border border-border bg-muted/40 px-4 py-3"
                      >
                        <div className="min-w-0">
                          <p className="truncate text-sm font-semibold text-foreground">
                            {t.name}
                          </p>
                          <p className="text-xs text-muted-foreground">
                            {t.academic_year_name} ·{" "}
                            <span className="font-mono">
                              {t.start_date} → {t.end_date}
                            </span>
                          </p>
                        </div>
                        <div className="flex shrink-0 items-center gap-1">
                          <Button
                            type="button"
                            variant="ghost"
                            size="icon"
                            aria-label={`Edit ${t.name}`}
                            onClick={() => openEdit({ kind: "term", item: t })}
                          >
                            <Pencil className="h-3.5 w-3.5" />
                          </Button>
                          <Button
                            type="button"
                            variant="ghost"
                            size="icon"
                            aria-label={`Delete ${t.name}`}
                            className="text-muted-foreground hover:text-destructive"
                            onClick={() =>
                              setDeleteTarget({
                                path: `/terms/${t.id}`,
                                label: t.name,
                                typeName: "Term",
                              })
                            }
                          >
                            <Trash2 className="h-3.5 w-3.5" />
                          </Button>
                        </div>
                      </div>
                    ))
                  )}
                </CardContent>
              </Card>
            </div>
          )}

          {/* 3. Year Levels (with Drag-and-Drop Reorder) */}
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
                <CardHeader className="flex flex-row items-center justify-between gap-2">
                  <div>
                    <CardTitle className="text-base">
                      Year Levels ({orderedLevels.length})
                    </CardTitle>
                    {orderedLevels.length > 1 && (
                      <p className="mt-0.5 text-xs text-muted-foreground">
                        Drag rows or use the arrows to reorder.
                      </p>
                    )}
                  </div>
                  {reorderMutation.isPending && (
                    <span className="inline-flex items-center gap-1.5 text-xs text-muted-foreground">
                      <Loader2 className="h-3.5 w-3.5 animate-spin" />
                      Saving order...
                    </span>
                  )}
                </CardHeader>
                <CardContent className="space-y-2.5">
                  {orderedLevels.length === 0 ? (
                    <EmptyState
                      icon={Layers}
                      title="No year levels yet"
                      description="Define your school's levels (e.g. JSS 1–SS 3 or Year 7–12)."
                    />
                  ) : (
                    orderedLevels.map((l, idx) => (
                      <div
                        key={l.id}
                        draggable={!reorderMutation.isPending}
                        onDragStart={(e) => {
                          setDraggedLevelId(l.id);
                          e.dataTransfer.effectAllowed = "move";
                          e.dataTransfer.setData("text/plain", l.id);
                        }}
                        onDragOver={(e) => {
                          e.preventDefault();
                          e.dataTransfer.dropEffect = "move";
                          if (dragOverLevelId !== l.id) {
                            setDragOverLevelId(l.id);
                          }
                        }}
                        onDragLeave={() => {
                          if (dragOverLevelId === l.id) {
                            setDragOverLevelId(null);
                          }
                        }}
                        onDrop={(e) => {
                          e.preventDefault();
                          handleLevelDrop(l.id);
                        }}
                        onDragEnd={() => {
                          setDraggedLevelId(null);
                          setDragOverLevelId(null);
                        }}
                        className={cn(
                          "flex items-center justify-between gap-3 rounded-xl border border-border bg-muted/40 px-3 py-2.5 transition-all",
                          draggedLevelId === l.id && "opacity-50",
                          dragOverLevelId === l.id &&
                            draggedLevelId !== l.id &&
                            "border-primary ring-2 ring-primary/30"
                        )}
                      >
                        <div className="flex min-w-0 items-center gap-2.5">
                          <span
                            title="Drag to reorder"
                            className="cursor-grab text-muted-foreground hover:text-foreground active:cursor-grabbing"
                          >
                            <GripVertical className="h-4 w-4" />
                          </span>
                          <span className="truncate text-sm font-semibold text-foreground">
                            {l.name}
                          </span>
                        </div>
                        <div className="flex shrink-0 items-center gap-1">
                          <span className="mr-1 font-mono text-xs text-muted-foreground">
                            #{l.display_order}
                          </span>
                          <Button
                            type="button"
                            variant="ghost"
                            size="icon"
                            aria-label={`Move ${l.name} up`}
                            disabled={idx === 0 || reorderMutation.isPending}
                            onClick={() => moveLevelByIndex(idx, idx - 1)}
                          >
                            <ArrowUp className="h-3.5 w-3.5" />
                          </Button>
                          <Button
                            type="button"
                            variant="ghost"
                            size="icon"
                            aria-label={`Move ${l.name} down`}
                            disabled={
                              idx === orderedLevels.length - 1 ||
                              reorderMutation.isPending
                            }
                            onClick={() => moveLevelByIndex(idx, idx + 1)}
                          >
                            <ArrowDown className="h-3.5 w-3.5" />
                          </Button>
                          <Button
                            type="button"
                            variant="ghost"
                            size="icon"
                            aria-label={`Edit ${l.name}`}
                            onClick={() => openEdit({ kind: "level", item: l })}
                          >
                            <Pencil className="h-3.5 w-3.5" />
                          </Button>
                          <Button
                            type="button"
                            variant="ghost"
                            size="icon"
                            aria-label={`Delete ${l.name}`}
                            className="text-muted-foreground hover:text-destructive"
                            onClick={() =>
                              setDeleteTarget({
                                path: `/year-levels/${l.id}`,
                                label: l.name,
                                typeName: "Year Level",
                              })
                            }
                          >
                            <Trash2 className="h-3.5 w-3.5" />
                          </Button>
                        </div>
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
                  <CardTitle className="text-base">Add Class Groups / Arms</CardTitle>
                </CardHeader>
                <CardContent>
                  <form
                    onSubmit={(e) => {
                      e.preventDefault();
                      const yearId = cgYearId || years[0]?.id;
                      const selectedLevels =
                        cgSelectedLevelIds.length > 0
                          ? cgSelectedLevelIds
                          : orderedLevels[0]?.id
                            ? [orderedLevels[0].id]
                            : [];
                      const customNames = cgName
                        .split(",")
                        .map((s) => s.trim())
                        .filter(Boolean);
                      const names = Array.from(
                        new Set([...cgSelectedPresets, ...customNames])
                      );
                      if (!yearId) {
                        toast.error("Select an academic year first.");
                        return;
                      }
                      if (selectedLevels.length === 0) {
                        toast.error("Select at least one year level.");
                        return;
                      }
                      if (names.length === 0) {
                        toast.error(
                          "Pick at least one stream/arm preset or enter a custom name."
                        );
                        return;
                      }
                      bulkClassGroupMutation.mutate({
                        academic_year_id: yearId,
                        year_level_ids: selectedLevels,
                        names,
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

                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <Label>Year levels (select one or many)</Label>
                        {orderedLevels.length > 1 && (
                          <div className="flex gap-2 text-[11px]">
                            <button
                              type="button"
                              onClick={() =>
                                setCgSelectedLevelIds(orderedLevels.map((l) => l.id))
                              }
                              className="font-semibold text-primary hover:underline cursor-pointer"
                            >
                              Select all
                            </button>
                            {cgSelectedLevelIds.length > 0 && (
                              <button
                                type="button"
                                onClick={() => setCgSelectedLevelIds([])}
                                className="text-muted-foreground hover:text-foreground cursor-pointer"
                              >
                                Clear
                              </button>
                            )}
                          </div>
                        )}
                      </div>
                      {orderedLevels.length === 0 ? (
                        <p className="text-xs text-muted-foreground">
                          Create Year Levels first (e.g. JSS1–SS3).
                        </p>
                      ) : (
                        <div className="flex flex-wrap gap-1.5">
                          {orderedLevels.map((l) => {
                            const active = cgSelectedLevelIds.includes(l.id);
                            return (
                              <button
                                key={l.id}
                                type="button"
                                onClick={() => toggleCgLevel(l.id)}
                                className={cn(
                                  "rounded-lg border px-2.5 py-1 text-xs font-semibold transition-colors cursor-pointer",
                                  active
                                    ? "border-primary bg-primary text-primary-foreground"
                                    : "border-border bg-muted/40 text-muted-foreground hover:border-primary/50 hover:text-foreground"
                                )}
                              >
                                {l.name}
                              </button>
                            );
                          })}
                        </div>
                      )}
                    </div>

                    <div className="space-y-2">
                      <Label>Quick streams / arms</Label>
                      <div className="flex flex-wrap gap-1.5">
                        {ARM_PRESETS.map((preset) => {
                          const active = cgSelectedPresets.includes(preset);
                          return (
                            <button
                              key={preset}
                              type="button"
                              onClick={() => toggleCgPreset(preset)}
                              className={cn(
                                "rounded-lg border px-2.5 py-1 text-xs font-semibold transition-colors cursor-pointer",
                                active
                                  ? "border-primary bg-primary/15 text-primary"
                                  : "border-border bg-card text-muted-foreground hover:border-primary/50 hover:text-foreground"
                              )}
                            >
                              + {preset}
                            </button>
                          );
                        })}
                      </div>
                    </div>

                    <div className="space-y-1.5">
                      <Label htmlFor="cg-name">Custom arm / stream name(s)</Label>
                      <Input
                        id="cg-name"
                        placeholder="e.g. Science A, Gold, Silver (comma-separated)"
                        value={cgName}
                        onChange={(e) => setCgName(e.target.value)}
                      />
                    </div>

                    <Button
                      type="submit"
                      disabled={bulkClassGroupMutation.isPending}
                    >
                      {bulkClassGroupMutation.isPending ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                      ) : (
                        <Plus className="h-4 w-4" />
                      )}
                      Create Class Groups
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
                <CardContent className="space-y-4">
                  {classes.length === 0 ? (
                    <EmptyState
                      icon={Users}
                      title="No class groups yet"
                      description="Select one or more year levels and add arms/streams (e.g. Science, Art, Commercial)."
                    />
                  ) : (
                    groupedClasses.map((grp) => (
                      <div key={grp.levelId} className="space-y-2">
                        <div className="flex items-center justify-between">
                          <p className="text-xs font-semibold uppercase tracking-wider text-primary">
                            {grp.levelName}
                          </p>
                          <span className="font-mono text-[11px] text-muted-foreground">
                            {grp.items.length}{" "}
                            {grp.items.length === 1 ? "arm" : "arms"}
                          </span>
                        </div>
                        <div className="space-y-2">
                          {grp.items.map((c) => (
                            <div
                              key={c.id}
                              className="flex items-center justify-between gap-3 rounded-xl border border-border bg-muted/40 px-4 py-2.5"
                            >
                              <div className="min-w-0">
                                <p className="truncate text-sm font-semibold text-foreground">
                                  {c.year_level_name} — {c.name}
                                </p>
                                <p className="text-xs text-muted-foreground">
                                  {c.academic_year_name}
                                </p>
                              </div>
                              <div className="flex shrink-0 items-center gap-1">
                                <Button
                                  type="button"
                                  variant="ghost"
                                  size="icon"
                                  aria-label={`Edit ${formatClassLabel(c)}`}
                                  onClick={() => openEdit({ kind: "class", item: c })}
                                >
                                  <Pencil className="h-3.5 w-3.5" />
                                </Button>
                                <Button
                                  type="button"
                                  variant="ghost"
                                  size="icon"
                                  aria-label={`Delete ${formatClassLabel(c)}`}
                                  className="text-muted-foreground hover:text-destructive"
                                  onClick={() =>
                                    setDeleteTarget({
                                      path: `/class-groups/${c.id}`,
                                      label: formatClassLabel(c),
                                      typeName: "Class Group",
                                    })
                                  }
                                >
                                  <Trash2 className="h-3.5 w-3.5" />
                                </Button>
                              </div>
                            </div>
                          ))}
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
                      const cleanCode = subjectCode.trim();
                      const cleanName = subjectName.trim();
                      if (!cleanCode) {
                        toast.error("Subject code is required.");
                        return;
                      }
                      if (cleanName.length < 2) {
                        toast.error("Subject name must be at least 2 characters.");
                        return;
                      }
                      createMutation.mutate({
                        path: "/subjects",
                        body: { code: cleanCode, name: cleanName },
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
                        className="flex items-center justify-between gap-3 rounded-xl border border-border bg-muted/40 px-4 py-3"
                      >
                        <span className="truncate text-sm font-semibold text-foreground">
                          {s.name}
                        </span>
                        <div className="flex shrink-0 items-center gap-1.5">
                          <Badge variant="outline" className="font-mono">
                            {s.code}
                          </Badge>
                          <Button
                            type="button"
                            variant="ghost"
                            size="icon"
                            aria-label={`Edit ${s.name}`}
                            onClick={() => openEdit({ kind: "subject", item: s })}
                          >
                            <Pencil className="h-3.5 w-3.5" />
                          </Button>
                          <Button
                            type="button"
                            variant="ghost"
                            size="icon"
                            aria-label={`Delete ${s.name}`}
                            className="text-muted-foreground hover:text-destructive"
                            onClick={() =>
                              setDeleteTarget({
                                path: `/subjects/${s.id}`,
                                label: `${s.code} — ${s.name}`,
                                typeName: "Subject",
                              })
                            }
                          >
                            <Trash2 className="h-3.5 w-3.5" />
                          </Button>
                        </div>
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
                      const classId = offClassId || classes[0]?.id;
                      const subjId = offSubjectId || subjects[0]?.id;
                      if (!classId) {
                        toast.error("Create or select a class group first.");
                        return;
                      }
                      if (!subjId) {
                        toast.error("Create or select a subject first.");
                        return;
                      }
                      createMutation.mutate({
                        path: "/subject-offerings",
                        body: {
                          class_group_id: classId,
                          subject_id: subjId,
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
                            {formatClassLabel(c)}
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
                          <div className="min-w-0">
                            <p className="truncate text-sm font-semibold text-foreground">
                              {o.subject_code} · {o.subject_name} — {o.class_group_name}
                            </p>
                            <p className="mt-0.5 text-xs text-muted-foreground">
                              {o.term_name ? `${o.term_name} · ` : "Full year · "}
                              Teachers:{" "}
                              {o.teachers.length > 0
                                ? o.teachers.map((t) => t.full_name).join(", ")
                                : "Unassigned"}
                            </p>
                          </div>
                          <div className="flex shrink-0 items-center gap-1">
                            <Badge variant={o.status === "active" ? "success" : "outline"}>
                              {o.status}
                            </Badge>
                            <Button
                              type="button"
                              variant="ghost"
                              size="icon"
                              aria-label={`Manage ${o.subject_name}`}
                              onClick={() => openEdit({ kind: "offering", item: o })}
                            >
                              <Pencil className="h-3.5 w-3.5" />
                            </Button>
                            <Button
                              type="button"
                              variant="ghost"
                              size="icon"
                              aria-label={`Delete ${o.subject_name}`}
                              className="text-muted-foreground hover:text-destructive"
                              onClick={() =>
                                setDeleteTarget({
                                  path: `/subject-offerings/${o.id}`,
                                  label: `${o.subject_code} · ${o.subject_name} (${o.class_group_name})`,
                                  typeName: "Subject Offering",
                                })
                              }
                            >
                              <Trash2 className="h-3.5 w-3.5" />
                            </Button>
                          </div>
                        </div>
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
                      const studentId = enrStudentId || students[0]?.user_id;
                      const classId = enrClassId || classes[0]?.id;
                      if (!studentId) {
                        toast.error(
                          students.length === 0
                            ? "No active students available. Add or approve a student in Users first."
                            : "Please select an active student."
                        );
                        return;
                      }
                      if (!classId) {
                        toast.error(
                          classes.length === 0
                            ? "No class groups available. Create a class group first."
                            : "Please select a class group."
                        );
                        return;
                      }
                      if (!enrDate) {
                        toast.error("Please select an effective start date.");
                        return;
                      }
                      createMutation.mutate({
                        path: "/enrollments",
                        body: {
                          student_user_id: studentId,
                          class_group_id: classId,
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
                        disabled={students.length === 0}
                        value={enrStudentId || students[0]?.user_id || ""}
                        onChange={(e) => setEnrStudentId(e.target.value)}
                      >
                        <option value="">
                          {students.length === 0
                            ? "No active students yet"
                            : "Select student"}
                        </option>
                        {students.map((s) => (
                          <option key={s.user_id} value={s.user_id}>
                            {s.full_name} ({s.email})
                          </option>
                        ))}
                      </SelectField>
                      {students.length === 0 && (
                        <p className="text-[11px] text-amber-600 dark:text-amber-400">
                          Add or approve a student in School Users before enrolling.
                        </p>
                      )}
                    </div>
                    <div className="space-y-1.5">
                      <Label htmlFor="enr-class">Class group</Label>
                      <SelectField
                        id="enr-class"
                        required
                        disabled={classes.length === 0}
                        value={enrClassId || classes[0]?.id || ""}
                        onChange={(e) => setEnrClassId(e.target.value)}
                      >
                        <option value="">
                          {classes.length === 0
                            ? "No class groups yet"
                            : "Select class group"}
                        </option>
                        {classes.map((c) => (
                          <option key={c.id} value={c.id}>
                            {formatClassLabel(c)}
                          </option>
                        ))}
                      </SelectField>
                    </div>
                    <div className="space-y-1.5">
                      <Label htmlFor="enr-date">Effective from</Label>
                      <DatePicker
                        id="enr-date"
                        required
                        value={enrDate}
                        onChange={setEnrDate}
                      />
                    </div>
                    <Button
                      type="submit"
                      disabled={
                        createMutation.isPending ||
                        students.length === 0 ||
                        classes.length === 0
                      }
                    >
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
                        className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-border bg-muted/40 px-4 py-3"
                      >
                        <div className="min-w-0">
                          <p className="truncate text-sm font-semibold text-foreground">
                            {e.student_full_name || e.student_user_id}
                          </p>
                          <p className="text-xs text-muted-foreground">
                            {e.class_group_name} ·{" "}
                            <span className="font-mono">
                              From {e.effective_from}
                              {e.effective_to ? ` → ${e.effective_to}` : ""}
                            </span>
                          </p>
                        </div>
                        <div className="flex shrink-0 items-center gap-1.5">
                          <Badge variant={e.status === "active" ? "success" : "outline"}>
                            {e.status}
                          </Badge>
                          {e.status === "active" && (
                            <>
                              <Button
                                type="button"
                                variant="outline"
                                size="sm"
                                onClick={() => {
                                  setTransferTarget(e);
                                  const other = classes.find(
                                    (c) => c.id !== e.class_group_id
                                  );
                                  setTransferClassId(other?.id || "");
                                  setTransferDate(new Date().toISOString().slice(0, 10));
                                }}
                              >
                                <ArrowRightLeft className="h-3.5 w-3.5" />
                                Transfer
                              </Button>
                              <Button
                                type="button"
                                variant="ghost"
                                size="sm"
                                className="text-muted-foreground hover:text-destructive"
                                onClick={() => {
                                  setWithdrawTarget(e);
                                  setWithdrawDate(new Date().toISOString().slice(0, 10));
                                }}
                              >
                                <UserMinus className="h-3.5 w-3.5" />
                                Withdraw
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
        </div>
      )}

      {/* Edit Dialog */}
      <Dialog
        open={editState !== null}
        onOpenChange={(open) => {
          if (!open && !updateMutation.isPending) {
            setEditState(null);
          }
        }}
      >
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>
              {editState?.kind === "year" && "Edit Academic Year"}
              {editState?.kind === "term" && "Edit Term"}
              {editState?.kind === "level" && "Edit Year Level"}
              {editState?.kind === "class" && "Edit Class Group"}
              {editState?.kind === "subject" && "Edit Subject"}
              {editState?.kind === "offering" && "Manage Subject Offering"}
            </DialogTitle>
            <DialogDescription>
              Update details below. Changes are recorded in the school audit log.
            </DialogDescription>
          </DialogHeader>

          {editState && (
            <form onSubmit={handleEditSubmit} className="mt-4 space-y-4">
              {editState.kind === "year" && (
                <>
                  <div className="space-y-1.5">
                    <Label htmlFor="edit-ay-name">Name</Label>
                    <Input
                      id="edit-ay-name"
                      required
                      value={editName}
                      onChange={(e) => setEditName(e.target.value)}
                    />
                  </div>
                  <div className="grid gap-3 sm:grid-cols-2">
                    <div className="space-y-1.5">
                      <Label htmlFor="edit-ay-start">Start date</Label>
                      <DatePicker
                        id="edit-ay-start"
                        required
                        value={editStart}
                        onChange={setEditStart}
                      />
                    </div>
                    <div className="space-y-1.5">
                      <Label htmlFor="edit-ay-end">End date</Label>
                      <DatePicker
                        id="edit-ay-end"
                        required
                        value={editEnd}
                        onChange={setEditEnd}
                      />
                    </div>
                  </div>
                  <div className="space-y-1.5">
                    <Label htmlFor="edit-ay-status">Status</Label>
                    <SelectField
                      id="edit-ay-status"
                      value={editStatus}
                      onChange={(e) => setEditStatus(e.target.value)}
                    >
                      <option value="active">Active</option>
                      <option value="archived">Archived</option>
                    </SelectField>
                  </div>
                </>
              )}

              {editState.kind === "term" && (
                <>
                  <div className="space-y-1.5">
                    <Label htmlFor="edit-term-name">Term name</Label>
                    <Input
                      id="edit-term-name"
                      required
                      value={editName}
                      onChange={(e) => setEditName(e.target.value)}
                    />
                  </div>
                  <div className="grid gap-3 sm:grid-cols-2">
                    <div className="space-y-1.5">
                      <Label htmlFor="edit-term-start">Start date</Label>
                      <DatePicker
                        id="edit-term-start"
                        required
                        value={editStart}
                        onChange={setEditStart}
                      />
                    </div>
                    <div className="space-y-1.5">
                      <Label htmlFor="edit-term-end">End date</Label>
                      <DatePicker
                        id="edit-term-end"
                        required
                        value={editEnd}
                        onChange={setEditEnd}
                      />
                    </div>
                  </div>
                </>
              )}

              {editState.kind === "level" && (
                <>
                  <div className="space-y-1.5">
                    <Label htmlFor="edit-yl-name">Name</Label>
                    <Input
                      id="edit-yl-name"
                      required
                      value={editName}
                      onChange={(e) => setEditName(e.target.value)}
                    />
                  </div>
                  <div className="space-y-1.5">
                    <Label htmlFor="edit-yl-order">Display order</Label>
                    <Input
                      id="edit-yl-order"
                      type="number"
                      min={0}
                      required
                      value={editOrder}
                      onChange={(e) => setEditOrder(e.target.value)}
                    />
                  </div>
                </>
              )}

              {editState.kind === "class" && (
                <>
                  <div className="space-y-1.5">
                    <Label htmlFor="edit-cg-name">Class group name</Label>
                    <Input
                      id="edit-cg-name"
                      required
                      value={editName}
                      onChange={(e) => setEditName(e.target.value)}
                    />
                  </div>
                  <div className="space-y-1.5">
                    <Label htmlFor="edit-cg-level">Year level</Label>
                    <SelectField
                      id="edit-cg-level"
                      required
                      value={editLevelId}
                      onChange={(e) => setEditLevelId(e.target.value)}
                    >
                      {orderedLevels.map((l) => (
                        <option key={l.id} value={l.id}>
                          {l.name}
                        </option>
                      ))}
                    </SelectField>
                  </div>
                </>
              )}

              {editState.kind === "subject" && (
                <>
                  <div className="space-y-1.5">
                    <Label htmlFor="edit-subj-code">Subject code</Label>
                    <Input
                      id="edit-subj-code"
                      required
                      value={editCode}
                      onChange={(e) => setEditCode(e.target.value)}
                      className="font-mono text-xs"
                    />
                  </div>
                  <div className="space-y-1.5">
                    <Label htmlFor="edit-subj-name">Subject name</Label>
                    <Input
                      id="edit-subj-name"
                      required
                      value={editName}
                      onChange={(e) => setEditName(e.target.value)}
                    />
                  </div>
                </>
              )}

              {editState.kind === "offering" && (
                <>
                  <div className="rounded-xl border border-border bg-muted/40 px-3.5 py-2.5 text-xs">
                    <p className="font-semibold text-foreground">
                      {editState.item.subject_code} · {editState.item.subject_name}
                    </p>
                    <p className="text-muted-foreground">
                      {editState.item.class_group_name}
                      {editState.item.term_name ? ` · ${editState.item.term_name}` : ""}
                    </p>
                  </div>

                  <div className="space-y-1.5">
                    <Label htmlFor="edit-off-status">Status</Label>
                    <SelectField
                      id="edit-off-status"
                      value={editStatus}
                      onChange={(e) => setEditStatus(e.target.value)}
                    >
                      <option value="active">Active</option>
                      <option value="archived">Archived</option>
                    </SelectField>
                  </div>

                  <div className="space-y-2">
                    <Label>Assigned teachers</Label>
                    {editState.item.teachers.length === 0 ? (
                      <p className="text-xs text-muted-foreground">
                        No teachers assigned yet.
                      </p>
                    ) : (
                      <div className="flex flex-wrap gap-1.5">
                        {editState.item.teachers.map((t) => (
                          <span
                            key={t.user_id}
                            className="inline-flex items-center gap-1.5 rounded-lg border border-border bg-muted/60 px-2.5 py-1 text-xs font-medium text-foreground"
                          >
                            {t.full_name}
                            <button
                              type="button"
                              aria-label={`Unassign ${t.full_name}`}
                              disabled={unassignTeacherMutation.isPending}
                              onClick={() =>
                                unassignTeacherMutation.mutate({
                                  offeringId: editState.item.id,
                                  teacherId: t.user_id,
                                })
                              }
                              className="rounded p-0.5 text-muted-foreground hover:bg-background hover:text-destructive cursor-pointer"
                            >
                              <X className="h-3 w-3" />
                            </button>
                          </span>
                        ))}
                      </div>
                    )}
                    <div className="flex gap-2 pt-1">
                      <SelectField
                        aria-label="Add teacher"
                        value={editAssignTeacherId}
                        onChange={(e) => setEditAssignTeacherId(e.target.value)}
                        className="flex-1"
                      >
                        <option value="">Select teacher to assign...</option>
                        {teachers
                          .filter(
                            (t) =>
                              !editState.item.teacher_user_ids.includes(t.user_id)
                          )
                          .map((t) => (
                            <option key={t.user_id} value={t.user_id}>
                              {t.full_name} ({t.email})
                            </option>
                          ))}
                      </SelectField>
                      <Button
                        type="button"
                        variant="outline"
                        disabled={
                          !editAssignTeacherId || assignTeacherMutation.isPending
                        }
                        onClick={() =>
                          assignTeacherMutation.mutate({
                            offeringId: editState.item.id,
                            teacherId: editAssignTeacherId,
                          })
                        }
                      >
                        <UserPlus className="h-3.5 w-3.5" />
                        Add
                      </Button>
                    </div>
                  </div>
                </>
              )}

              <div className="flex justify-end gap-2 pt-2">
                <Button
                  type="button"
                  variant="outline"
                  disabled={updateMutation.isPending}
                  onClick={() => setEditState(null)}
                >
                  Cancel
                </Button>
                <Button type="submit" disabled={updateMutation.isPending}>
                  {updateMutation.isPending ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin" />
                      Saving...
                    </>
                  ) : (
                    "Save Changes"
                  )}
                </Button>
              </div>
            </form>
          )}
        </DialogContent>
      </Dialog>

      {/* Safe Delete Confirm Dialog */}
      <ConfirmDialog
        open={deleteTarget !== null}
        onOpenChange={(open) => {
          if (!open) setDeleteTarget(null);
        }}
        title={deleteTarget ? `Delete ${deleteTarget.typeName}?` : "Delete?"}
        description={
          deleteTarget
            ? `Permanently delete "${deleteTarget.label}"? If this record is already linked to classes, offerings, enrollments, or coursework, deletion will be blocked to protect academic history.`
            : ""
        }
        confirmLabel="Delete"
        variant="destructive"
        isPending={deleteMutation.isPending}
        onConfirm={() => {
          if (deleteTarget) {
            deleteMutation.mutate(deleteTarget.path);
          }
        }}
      />

      {/* Transfer Enrollment Dialog */}
      <Dialog
        open={transferTarget !== null}
        onOpenChange={(open) => {
          if (!open && !transferMutation.isPending) setTransferTarget(null);
        }}
      >
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Transfer Student Enrollment</DialogTitle>
            <DialogDescription>
              Move{" "}
              <span className="font-semibold text-foreground">
                {transferTarget?.student_full_name}
              </span>{" "}
              from {transferTarget?.class_group_name}. Historical enrollment records are
              preserved.
            </DialogDescription>
          </DialogHeader>
          <form
            onSubmit={(e) => {
              e.preventDefault();
              if (!transferTarget || !transferClassId) return;
              transferMutation.mutate({
                enrollmentId: transferTarget.id,
                targetClassGroupId: transferClassId,
                effectiveDate: transferDate,
              });
            }}
            className="mt-4 space-y-4"
          >
            <div className="space-y-1.5">
              <Label htmlFor="tr-class">Target class group</Label>
              <SelectField
                id="tr-class"
                required
                value={transferClassId}
                onChange={(e) => setTransferClassId(e.target.value)}
              >
                <option value="">Select target class group</option>
                {classes
                  .filter((c) => c.id !== transferTarget?.class_group_id)
                  .map((c) => (
                    <option key={c.id} value={c.id}>
                      {formatClassLabel(c)} ({c.academic_year_name})
                    </option>
                  ))}
              </SelectField>
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="tr-date">Effective date</Label>
              <DatePicker
                id="tr-date"
                required
                value={transferDate}
                onChange={setTransferDate}
              />
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <Button
                type="button"
                variant="outline"
                disabled={transferMutation.isPending}
                onClick={() => setTransferTarget(null)}
              >
                Cancel
              </Button>
              <Button
                type="submit"
                disabled={!transferClassId || transferMutation.isPending}
              >
                {transferMutation.isPending ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <ArrowRightLeft className="h-4 w-4" />
                )}
                Transfer Student
              </Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>

      {/* Withdraw Enrollment Dialog */}
      <Dialog
        open={withdrawTarget !== null}
        onOpenChange={(open) => {
          if (!open && !withdrawMutation.isPending) setWithdrawTarget(null);
        }}
      >
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle className="text-destructive">Withdraw Enrollment</DialogTitle>
            <DialogDescription>
              Withdraw{" "}
              <span className="font-semibold text-foreground">
                {withdrawTarget?.student_full_name}
              </span>{" "}
              from {withdrawTarget?.class_group_name}. Past attendance and grades remain
              preserved.
            </DialogDescription>
          </DialogHeader>
          <form
            onSubmit={(e) => {
              e.preventDefault();
              if (!withdrawTarget) return;
              withdrawMutation.mutate({
                enrollmentId: withdrawTarget.id,
                effectiveDate: withdrawDate,
              });
            }}
            className="mt-4 space-y-4"
          >
            <div className="space-y-1.5">
              <Label htmlFor="wd-date">Effective date</Label>
              <DatePicker
                id="wd-date"
                required
                value={withdrawDate}
                onChange={setWithdrawDate}
              />
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <Button
                type="button"
                variant="outline"
                disabled={withdrawMutation.isPending}
                onClick={() => setWithdrawTarget(null)}
              >
                Cancel
              </Button>
              <Button
                type="submit"
                variant="destructive"
                disabled={withdrawMutation.isPending}
              >
                {withdrawMutation.isPending ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <UserMinus className="h-4 w-4" />
                )}
                Withdraw Student
              </Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>
    </PortalShell>
  );
}
