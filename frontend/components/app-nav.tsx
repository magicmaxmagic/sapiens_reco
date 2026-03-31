"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { LogoutButton } from "@/components/logout-button";

const links = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/profiles", label: "Profils" },
  { href: "/missions", label: "Missions & Matching" },
  { href: "/notes", label: "Notes" },
];

export function AppNav() {
  const pathname = usePathname();

  if (pathname === "/login" || pathname === "/setup-error") {
    return null;
  }

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
            {links.map((link) => (
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
