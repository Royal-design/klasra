# FRONTEND_DESIGN_PLAN.md — School LMS Frontend Architecture & UI/UX Blueprint

**Target Stack:** Next.js (App Router, TypeScript), Tailwind CSS v4, **shadcn/ui** (Radix UI primitives + `cmdk` + `sonner`), Framer Motion, Lucide Icons, TanStack Query, Zod + React Hook Form, `next-themes`  
**Backend API:** FastAPI `/api/v1` (`HttpOnly` cookie sessions + `X-CSRF-Token`, paginated `items` + `meta`, Backblaze B2 / S3 presigned uploads & video playback)  
**Scope:** Public marketing/onboarding landing experience + 5 role-scoped portals (Platform Admin, School Admin, Teacher, Student, Multi-School Parent)

---

## 1. Visual Identity & Catchy Color System (Light & Dark Mode)

Instead of generic flat gray dashboards or harsh neon gradients, the LMS uses a **Scholarly Modern** palette: crisp academic clarity paired with vibrant, trustworthy accent colors that feel alive for secondary-school students, teachers, and parents.

### 1.1 Brand Palette (Semantic CSS Variables)

| Token | Light Mode | Dark Mode | Usage |
| --- | --- | --- | --- |
| `--bg-canvas` | `#F8FAFC` (Cool Alabaster) | `#090D16` (Deep Midnight Ink) | App & page background |
| `--bg-surface` | `#FFFFFF` (Pure White) | `#111827` (Elevated Slate) | Cards, modals, tables, drawers |
| `--bg-subtle` | `#F1F5F9` (Soft Mist) | `#1A2234` (Muted Navy) | Hover states, table headers, input fills |
| `--border-subtle` | `#E2E8F0` | `#1F2937` | Hairline 1px borders & dividers |
| `--text-primary` | `#0F172A` (Ink Navy) | `#F8FAFC` (Crisp White) | Headings, primary copy (WCAG AAA) |
| `--text-secondary` | `#475569` (Slate) | `#94A3B8` (Cool Silver) | Subtitles, metadata, timestamps |
| `--brand-primary` | `#4F46E5` (Electric Indigo) | `#6366F1` (Luminous Indigo) | Primary buttons, active nav, focus rings |
| `--brand-secondary` | `#0D9488` (Vibrant Teal) | `#2DD4BF` (Bright Mint Teal) | Progress indicators, published badges, parent highlights |
| `--brand-accent` | `#F59E0B` (Warm Amber Gold) | `#FBBF24` (Solar Gold) | Highlights, late/pending badges, streak/achievement accents |
| `--status-success` | `#10B981` (Emerald) | `#34D399` | Present attendance, approved links, high grades |
| `--status-warning` | `#F59E0B` (Amber) | `#FBBF24` | Pending approval, late submission, draft items |
| `--status-danger` | `#EF4444` (Coral Red) | `#F87171` | Absent, revoked, overdue, destructive actions |

### 1.2 Light & Dark Mode Engineering
- Powered by `next-themes` (`attribute="class"`, `defaultTheme="system"`, `enableSystem`) with zero hydration flash.
- Animated **Sun / Moon / System** toggle in both the public navbar and the authenticated topbar.
- **Dark-mode surface elevation:** Cards in dark mode use subtle 1px translucent borders (`border-white/10`) and soft indigo/teal ambient glow rather than heavy drop shadows.
- **Role-tinted subtle accents:** Each portal carries a refined top-bar indicator pill (e.g., Indigo for School Admin, Teal for Teacher, Sky/Violet for Student, Amber/Emerald for Parent) so users with multiple roles or parents viewing children across schools always know their context at a glance.

### 1.3 Typography & Layout Rhythm
- **Display / Headings:** `Plus Jakarta Sans` (geometric, warm, modern, crisp at large hero sizes).
- **Body / UI:** `Inter` (high legibility for long lessons, assignment instructions, and dense gradebooks).
- **Monospace / Codes:** `JetBrains Mono` (subject codes like `PHY10`, registration cohort codes, scores `92 / 100`, timestamps).
- **Tabular numbers (`tabular-nums`)** on all scores, percentages, attendance counts, and dates so columns align cleanly.

---

## 2. Motion & Micro-Interaction System

Motion should make the interface feel **responsive, tactile, and calm** — never distracting or sluggish.

- **Library:** `framer-motion` wrapped in `<MotionConfig reducedMotion="user">` so users with OS-level `prefers-reduced-motion` get instant, zero-jank transitions.
- **Page & Section Reveals:** Staggered fade-up (`opacity: 0 → 1`, `y: 16 → 0`, `duration: 0.45s`, spring easing `[0.22, 1, 0.36, 1]`) on landing sections and dashboard KPI cards.
- **Shared-Element Layout Tabs (`layoutId`):** Smooth sliding indicator pill on navigation tabs, role switcher pills (Admin / Teacher / Student / Parent preview on the landing page), and filter tabs (`All | Published | Draft`).
- **Interactive Card Lift:** Subtle `-translate-y-1` + soft indigo/teal border glow on hover for class cards, lesson cards, and feature bento tiles.
- **Upload & Submission Feedback:** Animated upload progress bar during direct Backblaze B2 / S3 presigned video & file uploads, plus a crisp checkmark spring animation on successful submission or attendance roll-call save.
- **Drawers & Modals:** Spring slide-over panels for quick grading, student detail inspection, and mobile navigation.

---

## 3. Public Landing Page Blueprint (`/`)

The landing page will feel like a flagship modern SaaS education platform — informative, visual, and tailored to secondary schools, teachers, students, and parents.

### 3.1 Sticky Glassmorphic Navbar
- Brand logo mark + **School LMS** wordmark.
- Anchor links: *Features*, *For Schools*, *For Parents*, *Security*.
- Theme toggle (Light / Dark), **Student Self-Register** secondary link, and **Sign In** primary CTA button.

### 3.2 Hero Section (Above the Fold)
- **Left Column:**
  - Eyebrow badge: *"Multi-School Learning & Parent Portal — Built for Secondary Schools"*.
  - Bold headline: **"One Modern Classroom for Every School, Teacher, Student & Parent."**
  - Clear subheadline explaining isolated multi-school management, lessons & video learning, assignments, grading, attendance, and verified multi-school parent visibility.
  - Primary CTA (**Sign In to Your School**), Secondary CTA (**Register with School Code**), and a subtle *"Explore Portal Preview ↓"* link.
  - Quick trust metrics strip: *Strict School Isolation · Verified Parent Access · Encrypted Storage · Mobile-First*.
- **Right Column (Visual Showcase):**
  - High-resolution generated hero editorial illustration/photo-composite of a modern diverse secondary classroom & tablet dashboard + floating interactive glassmorphic UI cards (live Attendance Snapshot, Published Grade Card, and Lesson Video Player preview) with subtle float motion.

### 3.3 Visual Feature Bento Grid ("Everything a Secondary School Needs")
An asymmetric modern bento grid with crisp UI mini-previews and custom illustrations:
1. **Rich Lessons & Video Learning (Wide Card):** Markdown/rich lesson notes, embedded YouTube/Vimeo/Loom player, direct 50 MB video uploads, and downloadable PDFs/slides.
2. **Assignments & Versioned Submissions:** Due dates, late/resubmission toggles, drag-and-drop file uploads, and full version history (`v1 → v2`).
3. **Transparent Grading & Feedback:** Draft-to-publish grading workflow so teachers review before releasing marks and comments.
4. **One-Click Attendance & Audit Trail:** Fast `Present | Absent | Late | Excused` roll-call chips with staff attribution and full history.
5. **Multi-School Parent Portal (Wide Card):** One parent login linked to approved children across *multiple* schools — seeing only their own children's published grades, feedback, and attendance.
6. **Flexible School Structure & Bulk Import:** Custom terminology (`JSS 1–SS 3` or `Grade 7–12`, `Term` or `Semester`) + CSV/XLSX dry-run validation before import.

### 3.4 Interactive Role Showcase (Tabbed Walkthrough with Visual Mockups)
A 4-tab interactive switcher (`School Admin` · `Teacher` · `Student` · `Parent`) with animated `layoutId` pill and a live-styled dashboard preview + bullet highlights for each role, paired with generated role photography/illustrations.

### 3.5 How Onboarding Works (3-Step Visual Timeline)
1. **School Onboards & Imports Roster** (Academic years, class groups, CSV/XLSX import or staff email invites).
2. **Students & Parents Join Securely** (Short-lived cohort codes or email invites → admin approval before access).
3. **Teach, Submit, Grade & Track Progress** (Real-time lessons, assignments, grades, and attendance from any device).

### 3.6 Security, Privacy & Trust Strip
Dedicated dark-tinted/contrast section highlighting what school leaders and parents care about most:
- **Zero Cross-School Data Leakage** (`school_id` isolation enforced server-side)
- **No Unverified Child Access** (Admin approval + instant revocation for guardian links)
- **Private Encrypted Files** (Short-lived signed URLs, magic-byte validation, no public buckets)
- **Full Audit Trail** (Every grade, attendance, enrollment, and role change recorded)

### 3.7 Closing CTA Banner & Clean Multi-Column Footer
- Gradient indigo-to-teal call-to-action card with quick links to **Sign In**, **Student Registration**, and **Activate Staff / Parent Invite**.
- Footer with product links, role quick-links, privacy/NDPA note, and theme switcher.

---

## 4. Extra UI/UX Polish That Makes the LMS Stand Out

Before and during integration, we will bake in these high-craft details:

1. **Dynamic School Terminology:** Read `school.terminology_config` from the API so labels adapt automatically (e.g., *Year Level* → *Class / Grade*, *Term* → *Semester*).
2. **Command Palette (`Ctrl+K` / `Cmd+K`):** Instant keyboard jump to any class, subject offering, student, lesson, or action.
3. **Inline Lesson Video Player + Document Preview:**
   - Auto-detect YouTube/Vimeo/Loom `video_url` and render a clean privacy-enhanced responsive embed (`youtube-nocookie.com`).
   - For uploaded `.mp4`/`.webm`/`.mov` videos, fetch `GET /api/v1/files/{id}/download-url?inline=true` and render a sleek HTML5 video player.
   - For documents, show file-type icons, file size badges, and one-click secure download.
4. **Drag-and-Drop Presigned Uploader:**
   - Shows client-side file type & size validation *before* upload (10 MB for docs/images, 50 MB for lesson videos).
   - Automatically uses `presign → direct PUT with real-time progress bar → complete` when S3/Backblaze B2 is active, with seamless fallback to multipart upload in local dev.
5. **Fast Teacher Workflows:**
   - **Attendance Roll Call:** One-tap segmented pill buttons (`P` / `A` / `L` / `E`) per student + "Mark All Present" shortcut + single batch save.
   - **Split-Screen Grading Drawer:** View student text/file submission on the left while entering score, letter grade, feedback, and Draft/Publish toggle on the right.
6. **Delightful Empty States & Skeletons:**
   - Shimmering skeleton loaders matching card/table geometry (no jarring layout shifts).
   - Friendly illustrated empty states with clear next actions (e.g., *"No lessons published yet — Create your first lesson"*).
7. **Accessible Mobile Experience (360px+):**
   - Collapsible slide-out sidebar drawer, sticky bottom action bar on mobile for attendance/submissions, and responsive cards replacing wide tables on small screens.
8. **Global Toast & Error Handling:**
   - Friendly toast notifications mapped directly to our FastAPI `{ "error": { "code", "message", "details" } }` envelope, including graceful `401` session-expiry redirect and `429` rate-limit feedback.

---

## 5. Frontend Architecture & Route Map (`frontend/`)

```text
frontend/
├── public/
│   └── images/                  # Generated hero, role showcase & empty-state illustrations
├── src/
│   ├── app/
│   │   ├── (public)/            # Landing page, /login, /forgot-password, /reset-password,
│   │   │                        # /register/student, /staff/accept, /parent/verify
│   │   ├── (portal)/            # Authenticated shell (sidebar, topbar, Cmd+K, theme toggle)
│   │   │   ├── platform/        # Platform Admin: schools list, create/suspend school
│   │   │   ├── school/          # School Admin: overview, academics, users, imports,
│   │   │   │                    # student registrations, staff invites, guardian links
│   │   │   ├── teacher/         # Teacher: assigned offerings, lessons + video,
│   │   │   │                    # assignments, grading drawer, attendance roll call
│   │   │   ├── student/         # Student: my classes, lessons, assignments & submissions,
│   │   │   │                    # my grades, my attendance
│   │   │   └── parent/          # Parent: multi-school children switcher, child grades & attendance
│   │   ├── layout.tsx           # Fonts, ThemeProvider, QueryProvider, MotionConfig, Toaster
│   │   └── globals.css          # Semantic light/dark CSS tokens & utility styles
│   ├── components/
│   │   ├── ui/                  # shadcn/ui components (Button, Card, Input, Badge, Dialog, Sheet,
│   │   │                        # Table, Tabs, Select, Command, Skeleton, DropdownMenu, Sonner)
│   │   ├── landing/             # Hero, BentoFeatures, RoleShowcase, OnboardingSteps, SecurityStrip
│   │   ├── layout/              # PortalShell, Sidebar, Topbar, ThemeToggle, CommandPalette
│   │   └── media/               # VideoEmbed, PresignedUploader, FileAttachmentList
│   ├── lib/
│   │   ├── api-client.ts        # Typed fetch wrapper (credentials: "include", auto X-CSRF-Token)
│   │   ├── auth-context.tsx     # Current user, active school/role context, logout
│   │   └── types/               # TypeScript interfaces mirroring FastAPI schemas + PaginatedResponse<T>
│   └── hooks/                   # TanStack Query hooks per domain (schools, lessons, grades, attendance...)
```

---

## 6. Integration Plan (Step-by-Step Build Order)

1. **Phase 1 — Foundation, shadcn/ui Theme & Public Landing Page:**
   - Scaffold Next.js App Router + TypeScript + Tailwind v4 + **shadcn/ui** + Framer Motion + `next-themes` + Lucide + TanStack Query.
   - Theme shadcn's CSS variables (`--primary`, `--secondary`, `--accent`, `--background`, `--card`, `--border`) to our Electric Indigo + Vibrant Teal + Amber Gold Light & Dark palette so it looks bespoke rather than default gray.
   - Generate high-craft visual assets for the landing hero and role sections.
   - Build the Light/Dark mode toggle and the complete **Public Landing Page (`/`)**.
2. **Phase 2 — Auth, CSRF & Public Onboarding Flows:**
   - Build typed `api-client.ts` with `credentials: "include"` and automatic `X-CSRF-Token` attachment on mutations.
   - Implement `/login`, `/forgot-password`, `/reset-password`, `/register/student`, `/staff/accept`, and `/parent/verify`.
   - Build the authenticated `PortalShell` (sidebar, topbar, role-based routing, `Cmd+K` palette, change-password modal).
3. **Phase 3 — Platform Admin & School Admin Portals:**
   - Platform Admin school creation/suspension dashboard.
   - School Admin: academic years/terms/year-levels/class-groups/subjects/offerings, staff & student management, CSV/XLSX bulk import wizard (validate → preview → commit), student registration approval queue, and guardian link management.
4. **Phase 4 — Teacher Portal (Lessons, Video, Assignments, Grading & Attendance):**
   - Assigned subject offerings workspace, lesson editor with `video_url` & presigned 50 MB video/document uploader, assignment builder, split-screen grading drawer, and one-tap attendance roll-call table.
5. **Phase 5 — Student & Multi-School Parent Portals + Final Polish:**
   - Student classroom view (lessons + video player, assignment submission & version history, published grades & attendance).
   - Parent multi-school child switcher with published grades, teacher feedback, and attendance history.
   - End-to-end verification against live FastAPI (`127.0.0.1:8000`) in both Light & Dark mode at desktop and mobile (360px) viewports.
