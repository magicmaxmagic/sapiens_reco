import type { Metadata } from "next";
import { Manrope, Space_Grotesk } from "next/font/google";
import { AppNav } from "@/components/app-nav";
import "./globals.css";

const manrope = Manrope({
  variable: "--font-manrope",
  subsets: ["latin"],
});

const spaceGrotesk = Space_Grotesk({
  variable: "--font-space-grotesk",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Optimus MVP",
  description: "Plateforme de recommandation de profils pour resource managers",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="fr"
      className={`${manrope.variable} ${spaceGrotesk.variable} h-full antialiased`}
    >
      <body className="min-h-full bg-[color:var(--background)] text-[color:var(--text)]">
        <div className="relative min-h-screen overflow-x-hidden">
          <div className="pointer-events-none absolute inset-0 -z-10 bg-[radial-gradient(circle_at_10%_10%,rgba(250,204,21,0.18),transparent_28%),radial-gradient(circle_at_90%_20%,rgba(56,189,248,0.12),transparent_24%),linear-gradient(180deg,#fffef7_0%,#f8fafc_100%)]" />
          <AppNav />
          {children}
        </div>
      </body>
    </html>
  );
}
