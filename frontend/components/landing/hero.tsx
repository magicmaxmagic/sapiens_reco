"use client";

import Link from "next/link";

export function Hero() {
  return (
    <section className="relative overflow-hidden py-20 sm:py-32">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="text-center">
          <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-[color:var(--accent)]/30 bg-[color:var(--accent)]/10 px-4 py-1.5 text-sm font-medium text-[color:var(--accent)]">
            <span className="relative flex h-2 w-2">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-[color:var(--accent)] opacity-75"></span>
              <span className="relative inline-flex h-2 w-2 rounded-full bg-[color:var(--accent)]"></span>
            </span>
            Nouveau : Algorithme de matching IA
          </div>
          
          <h1 className="text-4xl font-bold tracking-tight text-[color:var(--text-strong)] sm:text-5xl lg:text-6xl">
            Trouvez le{" "}
            <span className="bg-gradient-to-r from-[color:var(--accent)] to-teal-400 bg-clip-text text-transparent">
              profil idéal
            </span>
            <br />
            en quelques secondes
          </h1>
          
          <p className="mx-auto mt-6 max-w-2xl text-lg text-[color:var(--text)] sm:text-xl">
            Optimus revolutionne le staffing intelligence avec un algorithme de matching 
            proprietaire. Trouvez les meilleurs candidats pour vos missions en un clic.
          </p>
          
          <div className="mt-10 flex flex-col items-center justify-center gap-4 sm:flex-row">
            <Link
              href="/signup"
              className="w-full rounded-lg bg-[color:var(--accent)] px-8 py-4 text-center text-lg font-semibold text-white shadow-lg transition hover:opacity-90 sm:w-auto"
            >
              Commencer gratuitement
            </Link>
            <Link
              href="/login"
              className="w-full rounded-lg border-2 border-[color:var(--accent)] bg-white px-8 py-4 text-center text-lg font-semibold text-[color:var(--accent)] transition hover:bg-[color:var(--accent)]/5 sm:w-auto"
            >
              Se connecter
            </Link>
          </div>
          
          <p className="mt-6 text-sm text-[color:var(--text-muted)]">
            Essai gratuit de 14 jours • Aucune carte requise
          </p>
        </div>
        
        {/* Decorative elements */}
        <div className="pointer-events-none absolute -top-40 left-1/2 -z-10 h-[600px] w-[600px] -translate-x-1/2 rounded-full bg-gradient-to-r from-[color:var(--accent)]/20 to-teal-200/20 blur-3xl" />
      </div>
    </section>
  );
}