"use client";

import Link from "next/link";

const plans = [
  {
    name: "Free",
    price: "0€",
    period: "/mois",
    description: "Ideal pour decouvrir Optimus",
    features: [
      "Jusqu'a 50 profils",
      "5 missions actives",
      "Matching basique",
      "Export CSV",
      "Support email",
    ],
    cta: "Commencer gratuitement",
    ctaHref: "/signup",
    highlighted: false,
  },
  {
    name: "Pro",
    price: "49€",
    period: "/mois",
    description: "Pour les consultants independants",
    features: [
      "Profils illimites",
      "Missions illimitees",
      "Matching IA avance",
      "Analytics detaillees",
      "API complete",
      "Support prioritaire",
    ],
    cta: "Essai gratuit 14 jours",
    ctaHref: "/signup?plan=pro",
    highlighted: true,
    badge: "Populaire",
  },
  {
    name: "Enterprise",
    price: "Sur mesure",
    period: "",
    description: "Pour les equipes et agences",
    features: [
      "Tout de Pro",
      "Utilisateurs illimites",
      "SSO & SAML",
      "SLA garanti",
      "Account manager dedie",
      "Formation sur site",
    ],
    cta: "Nous contacter",
    ctaHref: "mailto:contact@optimus.app",
    highlighted: false,
  },
];

export function Pricing() {
  return (
    <section id="pricing" className="py-20 sm:py-32 bg-gradient-to-b from-transparent to-[color:var(--background)]">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="text-center">
          <h2 className="text-3xl font-bold tracking-tight text-[color:var(--text-strong)] sm:text-4xl">
            Des tarifs simples et transparents
          </h2>
          <p className="mx-auto mt-4 max-w-2xl text-lg text-[color:var(--text)]">
            Choisissez le plan qui correspond a vos besoins. Sans engagement.
          </p>
        </div>
        
        <div className="mt-16 grid gap-8 lg:grid-cols-3">
          {plans.map((plan) => (
            <div
              key={plan.name}
              className={`relative rounded-2xl border p-8 ${
                plan.highlighted
                  ? "border-[color:var(--accent)] bg-gradient-to-b from-[color:var(--accent)]/5 to-white shadow-lg"
                  : "border-black/10 bg-white"
              }`}
            >
              {plan.badge && (
                <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                  <span className="inline-flex items-center rounded-full bg-[color:var(--accent)] px-4 py-1 text-sm font-semibold text-white">
                    {plan.badge}
                  </span>
                </div>
              )}
              
              <div className="text-center">
                <h3 className="text-xl font-semibold text-[color:var(--text-strong)]">
                  {plan.name}
                </h3>
                <div className="mt-4 flex items-baseline justify-center gap-1">
                  <span className="text-4xl font-bold text-[color:var(--text-strong)]">
                    {plan.price}
                  </span>
                  <span className="text-[color:var(--text-muted)]">
                    {plan.period}
                  </span>
                </div>
                <p className="mt-2 text-sm text-[color:var(--text)]">
                  {plan.description}
                </p>
              </div>
              
              <ul className="mt-8 space-y-4">
                {plan.features.map((feature) => (
                  <li key={feature} className="flex items-center gap-3 text-sm text-[color:var(--text)]">
                    <svg
                      className="h-5 w-5 flex-shrink-0 text-[color:var(--accent)]"
                      fill="currentColor"
                      viewBox="0 0 20 20"
                    >
                      <path
                        fillRule="evenodd"
                        d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                        clipRule="evenodd"
                      />
                    </svg>
                    {feature}
                  </li>
                ))}
              </ul>
              
              <Link
                href={plan.ctaHref}
                className={`mt-8 block w-full rounded-lg py-3 text-center font-semibold transition ${
                  plan.highlighted
                    ? "bg-[color:var(--accent)] text-white hover:opacity-90"
                    : "border-2 border-[color:var(--accent)] text-[color:var(--accent)] hover:bg-[color:var(--accent)]/5"
                }`}
              >
                {plan.cta}
              </Link>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}