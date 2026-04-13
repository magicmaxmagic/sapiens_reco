"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { LogoutButton } from "@/components/logout-button";

const dashboardLinks = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/profiles", label: "Profils" },
  { href: "/missions", label: "Missions" },
  { href: "/matching", label: "Matching" },
  { href: "/notes", label: "Notes" },
];

export function AppNav() {
  const pathname = usePathname();

  // No nav on login, signup, or setup-error pages
  if (pathname === "/login" || pathname === "/signup" || pathname === "/setup-error") {
    return null;
  }

  // Landing page nav (public)
  const isLandingPage = pathname === "/";

  if (isLandingPage) {
    return (
      <header className="sticky top-0 z-20 border-b border-black/10 bg-[color:var(--surface)]/90 backdrop-blur">
        <div className="mx-auto flex w-full max-w-7xl items-center justify-between px-4 py-3 sm:px-6 lg:px-8">
          <div className="flex items-center gap-3">
            <div className="grid h-9 w-9 place-items-center rounded-lg bg-[color:var(--accent)] text-[color:var(--surface)]">
              O
            </div>
            <div>
              <p className="text-xs uppercase tracking-[0.16em] text-[color:var(--text-muted)]">
                Staffing Intelligence
              </p>
              <p className="text-sm font-semibold text-[color:var(--text-strong)]">Optimus</p>
            </div>
          </div>
          <nav className="flex items-center gap-4">
            <a
              href="#features"
              className="hidden text-sm font-medium text-[color:var(--text)] transition hover:text-[color:var(--text-strong)] sm:block"
            >
              Fonctionnalites
            </a>
            <a
              href="#pricing"
              className="hidden text-sm font-medium text-[color:var(--text)] transition hover:text-[color:var(--text-strong)] sm:block"
            >
              Tarifs
            </a>
            <Link
              href="/login"
              className="rounded-md px-4 py-2 text-sm font-medium text-[color:var(--text-strong)] transition hover:bg-black/5"
            >
              Se connecter
            </Link>
            <Link
              href="/signup"
              className="rounded-lg bg-[color:var(--accent)] px-4 py-2 text-sm font-semibold text-white transition hover:opacity-90"
            >
              Essai gratuit
            </Link>
          </nav>
        </div>
      </header>
    );
  }

  // Dashboard nav (authenticated)
  return (
    <header className="sticky top-0 z-20 border-b border-black/10 bg-[color:var(--surface)]/90 backdrop-blur">
      <div className="mx-auto flex w-full max-w-7xl items-center justify-between px-4 py-3 sm:px-6 lg:px-8">
        <div className="flex items-center gap-3">
          <div className="grid h-9 w-9 place-items-center rounded-lg bg-[color:var(--accent)] text-[color:var(--surface)]">
            O
          </div>
          <div>
            <p className="text-xs uppercase tracking-[0.16em] text-[color:var(--text-muted)]">
              Staffing Intelligence
            </p>
            <p className="text-sm font-semibold text-[color:var(--text-strong)]">Optimus MVP</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <nav className="flex items-center gap-2">
            {dashboardLinks.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                className="rounded-md px-3 py-2 text-sm font-medium text-[color:var(--text)] transition hover:bg-black/5"
              >
                {link.label}
              </Link>
            ))}
          </nav>
          <LogoutButton />
        </div>
      </div>
    </header>
  );
}
