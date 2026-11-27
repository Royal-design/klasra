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

const AUTH_ONLY_PATHS = ["/login", "/forgot-password"];

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

  const isAuthOnly = AUTH_ONLY_PATHS.some((p) => pathname === p);
  if (isAuthOnly && hasSessionCookie) {
    return NextResponse.redirect(new URL("/dashboard", request.url));
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
    "/login",
    "/forgot-password",
  ],
};
