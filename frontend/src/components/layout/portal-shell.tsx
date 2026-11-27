"use client";

import * as React from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { AnimatePresence, motion } from "framer-motion";
import {
  BookOpen,
  Building2,
  CalendarCheck2,
  ClipboardList,
  HeartHandshake,
  KeyRound,
  LayoutDashboard,
  LogOut,
  Menu,
  Shield,
  Users,
  X,
} from "lucide-react";
import { toast } from "sonner";
import { KlasraMark } from "@/components/brand/klasra-logo";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { SelectField } from "@/components/ui/select-field";
import { ThemeToggle } from "@/components/theme-toggle";
import { ChangePasswordDialog } from "@/components/layout/change-password-dialog";
import { useAuth } from "@/lib/auth-context";
import { cn } from "@/lib/utils";

interface NavItem {
  label: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
  badge?: string;
}

export function PortalShell({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const { user, isLoading, activeMembership, setActiveMembershipId, logout } =
    useAuth();
  const [mobileOpen, setMobileOpen] = React.useState(false);
  const [changePwOpen, setChangePwOpen] = React.useState(false);

  React.useEffect(() => {
    if (!isLoading && !user) {
      router.replace("/login");
    }
  }, [isLoading, user, router]);

  const navItems = React.useMemo<NavItem[]>(() => {
    const items: NavItem[] = [
      { label: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
    ];
    if (!user) return items;

    if (user.is_platform_admin) {
      items.push({
        label: "Schools Directory",
        href: "/platform/schools",
        icon: Shield,
        badge: "Platform",
      });
    }

    const role = activeMembership?.role;
    if (role === "school_admin") {
      items.push(
        { label: "Academic Setup", href: "/school/academics", icon: Building2 },
        { label: "Users & Invites", href: "/school/users", icon: Users },
        {
          label: "Guardian Links",
          href: "/school/guardians",
          icon: HeartHandshake,
        }
      );
    } else if (role === "teacher") {
      items.push(
        { label: "My Offerings", href: "/teacher/offerings", icon: BookOpen },
        {
          label: "Assignments & Grading",
          href: "/teacher/assignments",
          icon: ClipboardList,
        },
        {
          label: "Attendance",
          href: "/teacher/attendance",
          icon: CalendarCheck2,
        }
      );
    } else if (role === "student") {
      items.push(
        { label: "My Classes", href: "/student/classes", icon: BookOpen },
        {
          label: "My Grades",
          href: "/student/grades",
          icon: ClipboardList,
        },
        {
          label: "My Attendance",
          href: "/student/attendance",
          icon: CalendarCheck2,
        }
      );
    }

    const hasParentRole =
      user.memberships.some((m) => m.role === "parent") || role === "parent";
    if (hasParentRole) {
      items.push({
        label: "My Children",
        href: "/parent/children",
        icon: HeartHandshake,
        badge: "Parent",
      });
    }

    return items;
  }, [user, activeMembership]);

  async function handleLogout() {
    await logout();
    toast.success("Signed out cleanly.");
    router.replace("/login");
  }

  if (isLoading || !user) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background">
        <div className="flex flex-col items-center gap-3">
          <div className="h-10 w-10 animate-spin rounded-full border-4 border-primary/20 border-t-primary" />
          <p className="text-xs font-semibold text-muted-foreground">
            Loading your workspace...
          </p>
        </div>
      </div>
    );
  }

  const activeMemberships = user.memberships.filter((m) => m.status === "active");
  const roleLabel = user.is_platform_admin
    ? "Platform Admin"
    : activeMembership?.role
        ?.replace("_", " ")
        .replace(/\b\w/g, (c) => c.toUpperCase()) || "Account";

  const sidebarContent = (
    <div className="flex h-full flex-col">
      <div className="flex h-16 items-center border-b border-border px-5">
        <Link
          href="/"
          onClick={() => setMobileOpen(false)}
          className="flex min-w-0 items-center gap-2.5 rounded-lg transition-opacity hover:opacity-85 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
        >
          <KlasraMark className="h-8 w-8" />
          <div className="min-w-0">
            <p className="truncate font-display text-sm font-bold tracking-tight text-foreground">
              Klasra
            </p>
            <p className="truncate text-[11px] font-medium text-muted-foreground">
              {activeMembership?.school_name || (user.is_platform_admin ? "Platform Ops" : "LMS Portal")}
            </p>
          </div>
        </Link>
      </div>

      {activeMemberships.length > 1 && (
        <div className="border-b border-border px-4 py-3">
          <label
            htmlFor="school-switcher"
            className="mb-1 block text-[11px] font-semibold uppercase tracking-wider text-muted-foreground"
          >
            Active School
          </label>
          <SelectField
            id="school-switcher"
            value={activeMembership?.id || ""}
            onChange={(e) => setActiveMembershipId(e.target.value)}
            aria-label="Active school"
          >
            {activeMemberships.map((m) => (
              <option key={m.id} value={m.id}>
                {m.school_name || m.school_id} ({m.role})
              </option>
            ))}
          </SelectField>
        </div>
      )}

      <nav className="flex-1 space-y-1 overflow-y-auto px-3 py-4">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive =
            pathname === item.href ||
            (item.href !== "/dashboard" && pathname.startsWith(item.href));
          return (
            <Link
              key={item.href}
              href={item.href}
              onClick={() => setMobileOpen(false)}
              className={cn(
                "flex items-center justify-between rounded-xl px-3 py-2.5 text-sm font-medium transition-colors",
                isActive
                  ? "bg-primary text-primary-foreground shadow-sm shadow-primary/25"
                  : "text-muted-foreground hover:bg-muted hover:text-foreground"
              )}
            >
              <span className="flex items-center gap-2.5">
                <Icon className="h-4 w-4 shrink-0" />
                {item.label}
              </span>
              {item.badge && (
                <span
                  className={cn(
                    "rounded-full px-2 py-0.5 text-[10px] font-semibold",
                    isActive
                      ? "bg-primary-foreground/15 text-primary-foreground"
                      : "bg-primary/10 text-primary"
                  )}
                >
                  {item.badge}
                </span>
              )}
            </Link>
          );
        })}
      </nav>

      <div className="border-t border-border p-3 space-y-1.5">
        <button
          type="button"
          onClick={() => {
            setMobileOpen(false);
            setChangePwOpen(true);
          }}
          className="flex w-full items-center gap-2.5 rounded-xl px-3 py-2 text-xs font-semibold text-muted-foreground transition-colors hover:bg-muted hover:text-foreground cursor-pointer"
        >
          <KeyRound className="h-4 w-4" />
          Change Password
        </button>
        <button
          type="button"
          onClick={handleLogout}
          className="flex w-full items-center gap-2.5 rounded-xl px-3 py-2 text-xs font-semibold text-destructive transition-colors hover:bg-destructive/10 cursor-pointer"
        >
          <LogOut className="h-4 w-4" />
          Sign Out
        </button>
      </div>
    </div>
  );

  return (
    <div className="flex min-h-screen bg-background">
      {/* Desktop Sidebar */}
      <aside className="hidden w-64 shrink-0 border-r border-border bg-card lg:block">
        {sidebarContent}
      </aside>

      {/* Mobile Drawer */}
      <AnimatePresence>
        {mobileOpen && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setMobileOpen(false)}
              className="fixed inset-0 z-40 bg-slate-950/60 backdrop-blur-xs lg:hidden"
            />
            <motion.aside
              initial={{ x: "-100%" }}
              animate={{ x: 0 }}
              exit={{ x: "-100%" }}
              transition={{ type: "spring", stiffness: 360, damping: 32 }}
              className="fixed inset-y-0 left-0 z-50 w-72 border-r border-border bg-card shadow-2xl lg:hidden"
            >
              <button
                type="button"
                onClick={() => setMobileOpen(false)}
                aria-label="Close sidebar"
                className="absolute right-3 top-4 rounded-lg p-1.5 text-muted-foreground hover:bg-muted cursor-pointer"
              >
                <X className="h-4 w-4" />
              </button>
              {sidebarContent}
            </motion.aside>
          </>
        )}
      </AnimatePresence>

      {/* Main Content */}
      <div className="flex min-w-0 flex-1 flex-col">
        <header className="sticky top-0 z-30 flex h-16 items-center justify-between gap-4 border-b border-border bg-background/85 px-4 backdrop-blur-xl sm:px-6">
          <div className="flex items-center gap-3">
            <Button
              variant="outline"
              size="icon"
              onClick={() => setMobileOpen(true)}
              aria-label="Open navigation menu"
              className="rounded-xl lg:hidden"
            >
              <Menu className="h-4 w-4" />
            </Button>
            <Badge variant="default" className="hidden sm:inline-flex">
              {roleLabel}
            </Badge>
          </div>

          <div className="flex items-center gap-3">
            <div className="hidden text-right sm:block">
              <p className="text-xs font-bold text-foreground">{user.full_name}</p>
              <p className="text-[11px] text-muted-foreground">{user.email}</p>
            </div>
            <ThemeToggle />
          </div>
        </header>

        <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-6 sm:px-6 lg:px-8">
          {children}
        </main>
      </div>

      <ChangePasswordDialog
        open={changePwOpen}
        onOpenChange={setChangePwOpen}
      />
    </div>
  );
}
