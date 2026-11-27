"use client";

import * as React from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Building2, Loader2, Save, SlidersHorizontal } from "lucide-react";
import { toast } from "sonner";
import { PortalShell } from "@/components/layout/portal-shell";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ApiClientError, apiRequest } from "@/lib/api-client";
import { useAuth } from "@/lib/auth-context";
import type { School } from "@/lib/types";

export default function SchoolSettingsPage() {
  const { activeMembership, refreshUser } = useAuth();
  const schoolId = activeMembership?.school_id;
  const isSchoolAdmin = activeMembership?.role === "school_admin";
  const queryClient = useQueryClient();

  const [schoolName, setSchoolName] = React.useState("");
  const [motto, setMotto] = React.useState("");
  const [contactEmail, setContactEmail] = React.useState("");
  const [contactPhone, setContactPhone] = React.useState("");
  const [address, setAddress] = React.useState("");
  const [yearLevelLabel, setYearLevelLabel] = React.useState("Year Level");
  const [termLabel, setTermLabel] = React.useState("Term");
  const [classGroupLabel, setClassGroupLabel] = React.useState("Class Group");

  const profileQuery = useQuery<School>({
    queryKey: ["school", schoolId, "profile"],
    queryFn: () => apiRequest<School>(`/schools/${schoolId}/profile`),
    enabled: Boolean(schoolId && isSchoolAdmin),
  });

  React.useEffect(() => {
    const s = profileQuery.data;
    if (!s) return;
    setSchoolName(s.name || "");
    const cfg = s.terminology_config || {};
    setMotto(cfg.motto || "");
    setContactEmail(cfg.contact_email || "");
    setContactPhone(cfg.contact_phone || "");
    setAddress(cfg.address || "");
    setYearLevelLabel(cfg.year_level_label || "Year Level");
    setTermLabel(cfg.term_label || "Term");
    setClassGroupLabel(cfg.class_group_label || "Class Group");
  }, [profileQuery.data]);

  const saveMutation = useMutation({
    mutationFn: () =>
      apiRequest<School>(`/schools/${schoolId}/profile`, {
        method: "PATCH",
        body: JSON.stringify({
          name: schoolName.trim(),
          terminology_config: {
            motto: motto.trim(),
            contact_email: contactEmail.trim(),
            contact_phone: contactPhone.trim(),
            address: address.trim(),
            year_level_label: yearLevelLabel.trim() || "Year Level",
            term_label: termLabel.trim() || "Term",
            class_group_label: classGroupLabel.trim() || "Class Group",
          },
        }),
      }),
    onSuccess: async () => {
      queryClient.invalidateQueries({ queryKey: ["school", schoolId, "profile"] });
      await refreshUser();
      toast.success("School profile and terminology saved.");
    },
    onError: (err) => {
      toast.error(
        err instanceof ApiClientError
          ? err.message
          : "Could not save school settings."
      );
    },
  });

  return (
    <PortalShell>
      {!isSchoolAdmin || !schoolId ? (
        <EmptyState
          icon={Building2}
          title="School Administrator access required"
          description="Only School Administrators can update school profile and terminology settings."
        />
      ) : (
        <div className="space-y-6">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wider text-primary">
              School Identity &amp; Localization
            </p>
            <h1 className="mt-1 font-display text-2xl font-bold tracking-tight text-foreground">
              School Profile &amp; Terminology
            </h1>
            <p className="mt-1 text-sm text-muted-foreground">
              Customize your school&apos;s display details and adapt academic labels
              to match your institution.
            </p>
          </div>

          <form
            onSubmit={(e) => {
              e.preventDefault();
              saveMutation.mutate();
            }}
            className="grid gap-6 lg:grid-cols-12"
          >
            <Card className="lg:col-span-7">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-base">
                  <Building2 className="h-4 w-4 text-primary" />
                  School Details
                </CardTitle>
                <CardDescription>
                  Displayed across emails, student portals, and parent views.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-1.5">
                  <Label htmlFor="sp-name">School name</Label>
                  <Input
                    id="sp-name"
                    required
                    minLength={2}
                    value={schoolName}
                    onChange={(e) => setSchoolName(e.target.value)}
                  />
                </div>
                <div className="space-y-1.5">
                  <Label htmlFor="sp-motto">School motto (optional)</Label>
                  <Input
                    id="sp-motto"
                    placeholder="e.g. Excellence & Integrity"
                    value={motto}
                    onChange={(e) => setMotto(e.target.value)}
                  />
                </div>
                <div className="grid gap-4 sm:grid-cols-2">
                  <div className="space-y-1.5">
                    <Label htmlFor="sp-email">Official contact email</Label>
                    <Input
                      id="sp-email"
                      type="email"
                      placeholder="info@school.edu"
                      value={contactEmail}
                      onChange={(e) => setContactEmail(e.target.value)}
                    />
                  </div>
                  <div className="space-y-1.5">
                    <Label htmlFor="sp-phone">Contact phone</Label>
                    <Input
                      id="sp-phone"
                      placeholder="+234 ..."
                      value={contactPhone}
                      onChange={(e) => setContactPhone(e.target.value)}
                    />
                  </div>
                </div>
                <div className="space-y-1.5">
                  <Label htmlFor="sp-address">Campus address</Label>
                  <Input
                    id="sp-address"
                    placeholder="Street, city, state"
                    value={address}
                    onChange={(e) => setAddress(e.target.value)}
                  />
                </div>
              </CardContent>
            </Card>

            <Card className="flex flex-col justify-between lg:col-span-5">
              <div>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-base">
                    <SlidersHorizontal className="h-4 w-4 text-primary" />
                    Academic Terminology
                  </CardTitle>
                  <CardDescription>
                    Match your school&apos;s naming conventions (e.g. Form, Grade,
                    Semester, Arm).
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-1.5">
                    <Label htmlFor="term-yl">Year Level label</Label>
                    <Input
                      id="term-yl"
                      placeholder="e.g. Class / Grade / Form"
                      value={yearLevelLabel}
                      onChange={(e) => setYearLevelLabel(e.target.value)}
                    />
                  </div>
                  <div className="space-y-1.5">
                    <Label htmlFor="term-t">Term label</Label>
                    <Input
                      id="term-t"
                      placeholder="e.g. Term / Semester"
                      value={termLabel}
                      onChange={(e) => setTermLabel(e.target.value)}
                    />
                  </div>
                  <div className="space-y-1.5">
                    <Label htmlFor="term-cg">Class Group label</Label>
                    <Input
                      id="term-cg"
                      placeholder="e.g. Arm / Section / Stream"
                      value={classGroupLabel}
                      onChange={(e) => setClassGroupLabel(e.target.value)}
                    />
                  </div>
                </CardContent>
              </div>

              <div className="border-t border-border p-6">
                <Button
                  type="submit"
                  className="w-full"
                  disabled={saveMutation.isPending}
                >
                  {saveMutation.isPending ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Save className="h-4 w-4" />
                  )}
                  Save School Profile
                </Button>
              </div>
            </Card>
          </form>
        </div>
      )}
    </PortalShell>
  );
}
