import { NextRequest, NextResponse } from "next/server";

import {
  APP_SESSION_COOKIE_NAME,
  getSafeRedirectPath,
  getSessionSecret,
  verifySignedSessionToken,
} from "@/lib/app-session";

const PUBLIC_PATHS = new Set(["/favicon.ico", "/robots.txt", "/sitemap.xml"]);
const SETUP_ERROR_PATH = "/setup-error";

function isPublicAsset(pathname: string): boolean {
  if (pathname.startsWith("/_next")) {
    return true;
  }

  if (pathname.startsWith("/api/app-auth")) {
    return true;
  }

  return /\.[a-zA-Z0-9]+$/.test(pathname);
}

function loginRedirect(request: NextRequest): NextResponse {
  const url = request.nextUrl.clone();
  const currentPath = `${request.nextUrl.pathname}${request.nextUrl.search}`;

  url.pathname = "/login";
  url.search = "";
  if (currentPath !== "/") {
    url.searchParams.set("next", currentPath);
  }

  return NextResponse.redirect(url);
}

function setupErrorRedirect(request: NextRequest): NextResponse {
  const url = request.nextUrl.clone();
  url.pathname = SETUP_ERROR_PATH;
  url.search = "";
  return NextResponse.redirect(url);
}

export async function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const isLoginRoute = pathname === "/login";
  const isSetupErrorRoute = pathname === SETUP_ERROR_PATH;

  if (isSetupErrorRoute || (!isLoginRoute && (PUBLIC_PATHS.has(pathname) || isPublicAsset(pathname)))) {
    return NextResponse.next();
  }

  // If session secret is missing, block the app behind a setup error page.
  const sessionSecret = getSessionSecret();
  if (!sessionSecret) {
    return setupErrorRedirect(request);
  }

  const rawCookie = request.cookies.get(APP_SESSION_COOKIE_NAME)?.value;
  if (!rawCookie) {
    return isLoginRoute ? NextResponse.next() : loginRedirect(request);
  }

  const session = await verifySignedSessionToken(rawCookie, sessionSecret);
  if (!session) {
    return isLoginRoute ? NextResponse.next() : loginRedirect(request);
  }

  if (isLoginRoute) {
    const nextPath = getSafeRedirectPath(request.nextUrl.searchParams.get("next"));
    const url = request.nextUrl.clone();
    url.pathname = nextPath;
    url.search = "";
    return NextResponse.redirect(url);
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/:path*"],
};