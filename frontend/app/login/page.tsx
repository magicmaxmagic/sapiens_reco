"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import type { AuthTokenResponse } from "@/lib/api";
import { saveAdminToken } from "@/lib/api";

type LoginErrorResponse = {
  detail?: string;
};

export default function LoginPage() {
  const router = useRouter();
  const [nextPath, setNextPath] = useState("/dashboard");
  const [signupSuccess, setSignupSuccess] = useState(false);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const next = params.get("next");
    if (next && next.startsWith("/") && !next.startsWith("//")) {
      setNextPath(next);
    }

    // Check for signup success
    if (params.get("signup") === "success") {
      setSignupSuccess(true);
      const signupUsername = params.get("username");
      if (signupUsername) {
        setUsername(signupUsername);
      }
    }
  }, []);

  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const onSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch("/api/app-auth/login", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          username: username.trim(),
          password,
        }),
      });

      if (!response.ok) {
        let detail = "Connexion impossible.";
        try {
          const payload = (await response.json()) as LoginErrorResponse;
          if (typeof payload.detail === "string" && payload.detail.length > 0) {
            detail = payload.detail;
          }
        } catch {
          // Keep fallback message.
        }

        setError(detail);
        return;
      }

      const token = (await response.json()) as AuthTokenResponse;
      saveAdminToken(token.access_token);
      setPassword("");
      router.push(nextPath);
      router.refresh();
    } catch {
      setError("Erreur reseau pendant la connexion.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <main className="mx-auto flex min-h-[calc(100vh-3rem)] w-full max-w-7xl items-center px-4 py-10 sm:px-6 lg:px-8">
      <section className="mx-auto w-full max-w-md rounded-2xl border border-black/10 bg-white p-6 shadow-[0_20px_60px_-45px_rgba(15,23,42,0.55)]">
        <p className="text-xs uppercase tracking-[0.16em] text-[color:var(--text-muted)]">Acces securise</p>
        <h1 className="mt-2 text-2xl font-semibold text-[color:var(--text-strong)]">Connexion Optimus</h1>
        <p className="mt-2 text-sm text-[color:var(--text)]">
          Connecte-toi avec ton identifiant et mot de passe.
        </p>

        {signupSuccess ? (
          <p className="mt-3 rounded-md border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm text-emerald-700">
            Compte cree avec succes ! Tu peux maintenant te connecter.
          </p>
        ) : null}

        <form onSubmit={onSubmit} className="mt-6 space-y-4">
          <div>
            <label
              htmlFor="username"
              className="mb-1 block text-sm font-medium text-[color:var(--text-strong)]"
            >
              Identifiant
            </label>
            <input
              id="username"
              type="text"
              value={username}
              onChange={(event) => setUsername(event.target.value)}
              autoComplete="username"
              required
              className="w-full rounded-lg border border-black/15 px-3 py-2 text-sm outline-none transition focus:border-[color:var(--accent)]"
            />
          </div>

          <div>
            <label
              htmlFor="password"
              className="mb-1 block text-sm font-medium text-[color:var(--text-strong)]"
            >
              Mot de passe
            </label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              autoComplete="current-password"
              required
              className="w-full rounded-lg border border-black/15 px-3 py-2 text-sm outline-none transition focus:border-[color:var(--accent)]"
            />
          </div>

          {error ? (
            <p className="rounded-md border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700">{error}</p>
          ) : null}

          <button
            type="submit"
            disabled={isLoading}
            className="w-full rounded-lg bg-[color:var(--accent)] px-4 py-2 text-sm font-semibold text-[color:var(--surface)] transition hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-70"
          >
            {isLoading ? "Connexion..." : "Se connecter"}
          </button>
        </form>

        <p className="mt-4 text-center text-sm text-[color:var(--text-muted)]">
          Pas de compte?{" "}
          <a href="/signup" className="text-[color:var(--accent)] hover:underline">
            Creer un compte
          </a>
        </p>
      </section>
    </main>
  );
}