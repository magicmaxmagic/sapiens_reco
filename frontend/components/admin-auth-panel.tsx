"use client";

import { useEffect, useState } from "react";

import {
  adminLogin,
  clearAdminToken,
  getAdminMe,
  hasAdminToken,
  saveAdminToken,
  type AdminIdentity,
} from "@/lib/api";

type AdminAuthPanelProps = {
  onAuthChanged?: (isAuthenticated: boolean) => void;
};

export function AdminAuthPanel({ onAuthChanged }: AdminAuthPanelProps) {
  const [username, setUsername] = useState("admin");
  const [password, setPassword] = useState("");
  const [identity, setIdentity] = useState<AdminIdentity | null>(null);
  const [isChecking, setIsChecking] = useState(true);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    const syncSession = async () => {
      if (!hasAdminToken()) {
        if (!cancelled) {
          setIdentity(null);
          setIsChecking(false);
          onAuthChanged?.(false);
        }
        return;
      }

      const me = await getAdminMe();
      if (!cancelled) {
        setIdentity(me);
        setIsChecking(false);
        onAuthChanged?.(Boolean(me));
      }
    };

    void syncSession();

    return () => {
      cancelled = true;
    };
  }, [onAuthChanged]);

  const onLogin = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);
    setIsLoading(true);

    try {
      const token = await adminLogin(username.trim(), password);
      saveAdminToken(token.access_token);
      const me = await getAdminMe();
      setIdentity(me);
      onAuthChanged?.(Boolean(me));
      setPassword("");
    } catch {
      setError("Echec de connexion admin.");
      setIdentity(null);
      onAuthChanged?.(false);
    } finally {
      setIsLoading(false);
    }
  };

  const onLogout = () => {
    clearAdminToken();
    setIdentity(null);
    setError(null);
    onAuthChanged?.(false);
  };

  if (isChecking) {
    return (
      <div className="rounded-xl border border-black/10 bg-white p-4 text-sm text-[color:var(--text-muted)]">
        Verification session admin...
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-black/10 bg-white p-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="text-xs uppercase tracking-[0.14em] text-[color:var(--text-muted)]">
            Session admin
          </p>
          {identity ? (
            <p className="mt-1 text-sm text-emerald-700">
              Connecte en tant que {identity.sub} ({identity.role})
            </p>
          ) : (
            <p className="mt-1 text-sm text-[color:var(--text)]">
              Requise pour les operations de creation/modification.
            </p>
          )}
        </div>
        {identity ? (
          <button
            type="button"
            onClick={onLogout}
            className="rounded-md border border-black/10 px-3 py-2 text-xs font-medium hover:bg-black/5"
          >
            Deconnexion
          </button>
        ) : null}
      </div>

      {!identity ? (
        <form onSubmit={onLogin} className="mt-4 grid gap-3 sm:grid-cols-[1fr_1fr_auto]">
          <input
            className="w-full rounded-md border border-black/15 px-3 py-2 text-sm"
            value={username}
            onChange={(event) => setUsername(event.target.value)}
            placeholder="Username"
            required
          />
          <input
            type="password"
            className="w-full rounded-md border border-black/15 px-3 py-2 text-sm"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            placeholder="Password"
            required
          />
          <button
            type="submit"
            disabled={isLoading}
            className="rounded-md bg-[color:var(--accent)] px-4 py-2 text-sm font-semibold text-white disabled:opacity-60"
          >
            {isLoading ? "Connexion..." : "Connexion"}
          </button>
        </form>
      ) : null}

      {error ? <p className="mt-3 text-sm text-rose-700">{error}</p> : null}
    </div>
  );
}
