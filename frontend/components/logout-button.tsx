"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { clearAdminToken } from "@/lib/api";

export function LogoutButton() {
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(false);

  const onLogout = async () => {
    setIsLoading(true);
    try {
      await fetch("/api/app-auth/logout", {
        method: "POST",
      });
    } catch {
      // Even if the backend call fails, we still clear local state.
    } finally {
      clearAdminToken();
      router.push("/login");
      router.refresh();
      setIsLoading(false);
    }
  };

  return (
    <button
      type="button"
      onClick={onLogout}
      disabled={isLoading}
      className="rounded-md border border-black/10 px-3 py-2 text-sm font-medium text-[color:var(--text)] transition hover:bg-black/5 disabled:cursor-not-allowed disabled:opacity-60"
    >
      {isLoading ? "Deconnexion..." : "Deconnexion"}
    </button>
  );
}