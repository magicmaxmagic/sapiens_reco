"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

import { AdminAuthPanel } from "@/components/admin-auth-panel";
import { ApiError, manualCorrectProfile, type Profile } from "@/lib/api";

function parseCsvList(input: string): string[] {
  return input
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}

type ProfileEditFormProps = {
  profile: Profile;
};

export function ProfileEditForm({ profile }: ProfileEditFormProps) {
  const router = useRouter();

  const [fullName, setFullName] = useState(profile.full_name);
  const [skills, setSkills] = useState(profile.parsed_skills.join(", "));
  const [languages, setLanguages] = useState(profile.parsed_languages.join(", "));
  const [location, setLocation] = useState(profile.parsed_location ?? "");
  const [seniority, setSeniority] = useState(profile.parsed_seniority ?? "");
  const [availability, setAvailability] = useState(profile.availability_status);
  const [rawText, setRawText] = useState(profile.raw_text ?? "");

  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const onSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);
    setSuccess(null);
    setIsSaving(true);

    try {
      await manualCorrectProfile(profile.id, {
        full_name: fullName.trim(),
        parsed_skills: parseCsvList(skills),
        parsed_languages: parseCsvList(languages),
        parsed_location: location.trim() || null,
        parsed_seniority: seniority.trim() || null,
        availability_status: availability.trim() || "unknown",
        raw_text: rawText.trim() || null,
      });
      setSuccess("Profil mis a jour avec succes.");
      router.refresh();
    } catch (error) {
      if (error instanceof ApiError && error.status === 401) {
        setError("Authentification admin requise.");
      } else {
        setError("Impossible d'enregistrer les modifications.");
      }
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <form onSubmit={onSubmit} className="space-y-4">
      <AdminAuthPanel />

      <div className="grid gap-4 sm:grid-cols-2">
        <label className="space-y-2 text-sm">
          <span className="font-medium text-[color:var(--text-strong)]">Nom complet</span>
          <input
            className="w-full rounded-md border border-black/15 px-3 py-2"
            value={fullName}
            onChange={(event) => setFullName(event.target.value)}
            required
          />
        </label>

        <label className="space-y-2 text-sm">
          <span className="font-medium text-[color:var(--text-strong)]">Disponibilite</span>
          <input
            className="w-full rounded-md border border-black/15 px-3 py-2"
            value={availability}
            onChange={(event) => setAvailability(event.target.value)}
            placeholder="available, soon, unknown"
          />
        </label>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <label className="space-y-2 text-sm">
          <span className="font-medium text-[color:var(--text-strong)]">Competences (CSV)</span>
          <input
            className="w-full rounded-md border border-black/15 px-3 py-2"
            value={skills}
            onChange={(event) => setSkills(event.target.value)}
            placeholder="python, fastapi, sql"
          />
        </label>

        <label className="space-y-2 text-sm">
          <span className="font-medium text-[color:var(--text-strong)]">Langues (CSV)</span>
          <input
            className="w-full rounded-md border border-black/15 px-3 py-2"
            value={languages}
            onChange={(event) => setLanguages(event.target.value)}
            placeholder="fr, en"
          />
        </label>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <label className="space-y-2 text-sm">
          <span className="font-medium text-[color:var(--text-strong)]">Localisation</span>
          <input
            className="w-full rounded-md border border-black/15 px-3 py-2"
            value={location}
            onChange={(event) => setLocation(event.target.value)}
            placeholder="paris"
          />
        </label>

        <label className="space-y-2 text-sm">
          <span className="font-medium text-[color:var(--text-strong)]">Seniorite</span>
          <input
            className="w-full rounded-md border border-black/15 px-3 py-2"
            value={seniority}
            onChange={(event) => setSeniority(event.target.value)}
            placeholder="junior, mid, senior, lead"
          />
        </label>
      </div>

      <label className="block space-y-2 text-sm">
        <span className="font-medium text-[color:var(--text-strong)]">Texte brut extrait</span>
        <textarea
          className="min-h-44 w-full rounded-md border border-black/15 px-3 py-2"
          value={rawText}
          onChange={(event) => setRawText(event.target.value)}
        />
      </label>

      <div className="flex flex-wrap items-center gap-3">
        <button
          type="submit"
          className="rounded-md bg-[color:var(--accent)] px-4 py-2 text-sm font-semibold text-white disabled:opacity-60"
          disabled={isSaving}
        >
          {isSaving ? "Enregistrement..." : "Enregistrer"}
        </button>
        {success ? <span className="text-sm text-emerald-700">{success}</span> : null}
        {error ? <span className="text-sm text-rose-700">{error}</span> : null}
      </div>
    </form>
  );
}
