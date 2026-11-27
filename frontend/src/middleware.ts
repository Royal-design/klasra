import type { NextRequest } from "next/server";
import { NextResponse } from "next/server";

const PROTECTED_PREFIXES = [
  "/dashboard",
  "/platform",
  "/school",
  "/teacher",
  "/student",
  "/parent/children",
];

/**
 * Edge route guard:
 * - Redirects unauthenticated visitors away from protected portals when no
 *   session cookie is present.
 * - Intentionally does NOT redirect `/login` -> `/dashboard` on cookie
 *   existence alone, preventing infinite redirect loops when a session cookie
 *   is expired or revoked server-side (valid sessions are redirected by
 *   `/login` once GET /api/v1/auth/me confirms 200 OK).
 */
export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const hasSessionCookie =
    request.cookies.has("__Host-lms_session") ||
    request.cookies.has("lms_session");

  const isProtected = PROTECTED_PREFIXES.some(
    (prefix) => pathname === prefix || pathname.startsWith(`${prefix}/`)
  );
  if (isProtected && !hasSessionCookie) {
    const loginUrl = new URL("/login", request.url);
    loginUrl.searchParams.set("next", pathname);
    return NextResponse.redirect(loginUrl);
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    "/dashboard/:path*",
    "/platform/:path*",
    "/school/:path*",
    "/teacher/:path*",
    "/student/:path*",
    "/parent/children/:path*",
  ],
};
