"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

type SignupErrorResponse = {
  detail?: string;
};

export default function SignupPage() {
  const router = useRouter();
  const [nextPath, setNextPath] = useState("/login");

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const next = params.get("next");
    if (next && next.startsWith("/") && !next.startsWith("//")) {
      setNextPath(next);
    }
  }, []);

  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const onSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setIsLoading(true);
    setError(null);

    // Client-side validation
    if (username.trim().length < 3) {
      setError("L'identifiant doit contenir au moins 3 caracteres.");
      setIsLoading(false);
      return;
    }

    if (!/^[a-zA-Z0-9_]+$/.test(username.trim())) {
      setError("L'identifiant ne peut contenir que des lettres, chiffres et underscores.");
      setIsLoading(false);
      return;
    }

    if (!email.trim()) {
      setError("L'adresse email est requise.");
      setIsLoading(false);
      return;
    }

    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim())) {
      setError("Format d'email invalide.");
      setIsLoading(false);
      return;
    }

    if (password.length < 8) {
      setError("Le mot de passe doit contenir au moins 8 caracteres.");
      setIsLoading(false);
      return;
    }

    if (password !== confirmPassword) {
      setError("Les mots de passe ne correspondent pas.");
      setIsLoading(false);
      return;
    }

    // Password strength validation
    const hasUpper = /[A-Z]/.test(password);
    const hasLower = /[a-z]/.test(password);
    const hasDigit = /[0-9]/.test(password);

    if (!hasUpper || !hasLower || !hasDigit) {
      setError("Le mot de passe doit contenir au moins une majuscule, une minuscule et un chiffre.");
      setIsLoading(false);
      return;
    }

    try {
      const response = await fetch("/api/app-auth/signup", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          username: username.trim(),
          email: email.trim().toLowerCase(),
          password,
        }),
      });

      if (!response.ok) {
        let detail = "Inscription impossible.";
        try {
          const payload = (await response.json()) as SignupErrorResponse;
          if (typeof payload.detail === "string" && payload.detail.length > 0) {
            detail = payload.detail;
          }
        } catch {
          // Keep fallback message.
        }

        setError(detail);
        return;
      }

      // Success - redirect to login with success message
      setPassword("");
      setConfirmPassword("");
      router.push(`/login?signup=success&username=${encodeURIComponent(username.trim())}`);
    } catch {
      setError("Erreur reseau pendant l'inscription.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <main className="mx-auto flex min-h-[calc(100vh-3rem)] w-full max-w-7xl items-center px-4 py-10 sm:px-6 lg:px-8">
      <section className="mx-auto w-full max-w-md rounded-2xl border border-black/10 bg-white p-6 shadow-[0_20px_60px_-45px_rgba(15,23,42,0.55)]">
        <p className="text-xs uppercase tracking-[0.16em] text-[color:var(--text-muted)]">Nouveau compte</p>
        <h1 className="mt-2 text-2xl font-semibold text-[color:var(--text-strong)]">Creer un compte Optimus</h1>
        <p className="mt-2 text-sm text-[color:var(--text)]">
          Remplis les informations ci-dessous pour creer ton compte.
        </p>

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
              placeholder="3 caracteres min. (lettres, chiffres, _)"
              className="w-full rounded-lg border border-black/15 px-3 py-2 text-sm outline-none transition focus:border-[color:var(--accent)]"
            />
          </div>

          <div>
            <label
              htmlFor="email"
              className="mb-1 block text-sm font-medium text-[color:var(--text-strong)]"
            >
              Adresse email
            </label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              autoComplete="email"
              required
              placeholder="nom@exemple.com"
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
              autoComplete="new-password"
              required
              placeholder="8 caracteres min. (majuscule, minuscule, chiffre)"
              className="w-full rounded-lg border border-black/15 px-3 py-2 text-sm outline-none transition focus:border-[color:var(--accent)]"
            />
          </div>

          <div>
            <label
              htmlFor="confirmPassword"
              className="mb-1 block text-sm font-medium text-[color:var(--text-strong)]"
            >
              Confirmer le mot de passe
            </label>
            <input
              id="confirmPassword"
              type="password"
              value={confirmPassword}
              onChange={(event) => setConfirmPassword(event.target.value)}
              autoComplete="new-password"
              required
              placeholder="Retape ton mot de passe"
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
            {isLoading ? "Creation en cours..." : "Creer mon compte"}
          </button>
        </form>

        <p className="mt-4 text-center text-sm text-[color:var(--text-muted)]">
          Deja un compte?{" "}
          <a href="/login" className="text-[color:var(--accent)] hover:underline">
            Se connecter
          </a>
        </p>
      </section>
    </main>
  );
}