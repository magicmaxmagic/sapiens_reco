"use client";

import Link from "next/link";

const footerLinks = {
  product: [
    { label: "Fonctionnalites", href: "#features" },
    { label: "Tarifs", href: "#pricing" },
    { label: "Changelog", href: "#" },
    { label: "API", href: "#" },
  ],
  company: [
    { label: "A propos", href: "#" },
    { label: "Blog", href: "#" },
    { label: "Carrieres", href: "#" },
    { label: "Contact", href: "#" },
  ],
  legal: [
    { label: "Confidentialite", href: "#" },
    { label: "CGU", href: "#" },
    { label: "RGPD", href: "#" },
    { label: "Cookies", href: "#" },
  ],
};

export function Footer() {
  return (
    <footer className="border-t border-black/10 bg-[color:var(--surface)] py-12">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="grid gap-8 md:grid-cols-4">
          <div className="md:col-span-1">
            <div className="flex items-center gap-3">
              <div className="grid h-9 w-9 place-items-center rounded-lg bg-[color:var(--accent)] text-[color:var(--surface)]">
                O
              </div>
              <div>
                <p className="text-xs uppercase tracking-[0.16em] text-[color:var(--text-muted)]">
                  Staffing Intelligence
                </p>
                <p className="text-sm font-semibold text-[color:var(--text-strong)]">
                  Optimus
                </p>
              </div>
            </div>
            <p className="mt-4 text-sm text-[color:var(--text-muted)]">
              La plateforme de recommandation de profils pour resource managers.
            </p>
          </div>
          
          <div>
            <h4 className="text-sm font-semibold text-[color:var(--text-strong)]">
              Produit
            </h4>
            <ul className="mt-4 space-y-3">
              {footerLinks.product.map((link) => (
                <li key={link.label}>
                  <Link
                    href={link.href}
                    className="text-sm text-[color:var(--text-muted)] transition hover:text-[color:var(--text)]"
                  >
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>
          
          <div>
            <h4 className="text-sm font-semibold text-[color:var(--text-strong)]">
              Entreprise
            </h4>
            <ul className="mt-4 space-y-3">
              {footerLinks.company.map((link) => (
                <li key={link.label}>
                  <Link
                    href={link.href}
                    className="text-sm text-[color:var(--text-muted)] transition hover:text-[color:var(--text)]"
                  >
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>
          
          <div>
            <h4 className="text-sm font-semibold text-[color:var(--text-strong)]">
              Legal
            </h4>
            <ul className="mt-4 space-y-3">
              {footerLinks.legal.map((link) => (
                <li key={link.label}>
                  <Link
                    href={link.href}
                    className="text-sm text-[color:var(--text-muted)] transition hover:text-[color:var(--text)]"
                  >
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>
        </div>
        
        <div className="mt-12 border-t border-black/10 pt-8">
          <p className="text-center text-sm text-[color:var(--text-muted)]">
            © {new Date().getFullYear()} Optimus. Tous droits reserves.
          </p>
        </div>
      </div>
    </footer>
  );
}