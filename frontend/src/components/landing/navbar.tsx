"use client";

import * as React from "react";
import Link from "next/link";
import { Menu, X } from "lucide-react";
import { KlasraLogo } from "@/components/brand/klasra-logo";
import { Button } from "@/components/ui/button";
import { ThemeToggle } from "@/components/theme-toggle";

const navLinks = [
  { label: "Why Klasra", href: "#why-klasra" },
  { label: "Experience", href: "#roles" },
  { label: "Capabilities", href: "#features" },
  { label: "Security", href: "#security" },
];

export function LandingNavbar() {
  const [mobileOpen, setMobileOpen] = React.useState(false);

  return (
    <header className="sticky top-0 z-50 w-full border-b border-border bg-background/95 backdrop-blur-sm">
      <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4 sm:px-6 lg:px-8">
        <Link
          href="/"
          aria-label="Klasra Home"
          className="rounded-lg focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
        >
          <KlasraLogo />
        </Link>

        <nav aria-label="Primary navigation" className="hidden items-center gap-8 md:flex">
          {navLinks.map((item) => (
            <a
              key={item.href}
              href={item.href}
              className="rounded-md px-1 py-1 text-sm font-medium text-muted-foreground transition-colors hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            >
              {item.label}
            </a>
          ))}
        </nav>

        <div className="hidden items-center gap-2.5 md:flex">
          <ThemeToggle />
          <Button variant="ghost" size="sm" asChild>
            <Link href="/register/student">Student Code</Link>
          </Button>
          <Button size="sm" asChild>
            <Link href="/login">Sign In</Link>
          </Button>
        </div>

        <div className="flex items-center gap-2 md:hidden">
          <ThemeToggle />
          <Button
            variant="outline"
            size="icon"
            onClick={() => setMobileOpen((prev) => !prev)}
            aria-label="Toggle navigation menu"
            aria-expanded={mobileOpen}
            className="h-9 w-9 rounded-lg"
          >
            {mobileOpen ? <X className="h-4 w-4" /> : <Menu className="h-4 w-4" />}
          </Button>
        </div>
      </div>

      {mobileOpen && (
        <div className="border-t border-border bg-card md:hidden">
          <div className="mx-auto flex max-w-6xl flex-col gap-1 px-4 py-4">
            {navLinks.map((item) => (
              <a
                key={item.href}
                href={item.href}
                onClick={() => setMobileOpen(false)}
                className="rounded-lg px-3 py-2 text-sm font-medium text-foreground hover:bg-muted"
              >
                {item.label}
              </a>
            ))}
            <div className="mt-3 flex flex-col gap-2 border-t border-border pt-3">
              <Button variant="outline" asChild className="w-full">
                <Link href="/register/student">Register with School Code</Link>
              </Button>
              <Button asChild className="w-full">
                <Link href="/login">Sign In to Your School</Link>
              </Button>
            </div>
          </div>
        </div>
      )}
    </header>
  );
}
