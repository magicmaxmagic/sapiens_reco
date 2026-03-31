"use client";

import Link from "next/link";
import { useState, type KeyboardEvent } from "react";

type ProfileSearchFiltersProps = {
  q: string;
  skillsRaw: string;
  skillMode: "any" | "all";
  location: string;
  availability: string;
  seniority: string;
  language: string;
  sortBy: "relevance" | "date" | "seniority";
  resultsSummary: string;
};

const AVAILABILITY_OPTIONS = [
  "",
  "ASAP",
  "In 15 days",
  "In 30 days",
  "In 60 days",
  "Later",
  "unknown",
];

const SORT_OPTIONS = [
  { value: "relevance", label: "Pertinence" },
  { value: "date", label: "Date" },
  { value: "seniority", label: "Seniorite" },
] as const;

function parseSkills(raw: string): string[] {
  const unique = new Set<string>();
  raw
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean)
    .forEach((item) => unique.add(item));
  return Array.from(unique);
}

function normalizeSkill(raw: string): string {
  return raw.trim().replace(/\s+/g, " ");
}

export function ProfileSearchFilters({
  q,
  skillsRaw,
  skillMode,
  location,
  availability,
  seniority,
  language,
  sortBy,
  resultsSummary,
}: ProfileSearchFiltersProps) {
  const [skills, setSkills] = useState<string[]>(() => parseSkills(skillsRaw));
  const [skillInput, setSkillInput] = useState("");

  const addSkill = (raw: string) => {
    const value = normalizeSkill(raw);
    if (!value) {
      return;
    }

    const exists = skills.some((skill) => skill.toLowerCase() === value.toLowerCase());
    if (exists) {
      setSkillInput("");
      return;
    }

    setSkills((current) => [...current, value]);
    setSkillInput("");
  };

  const removeSkill = (value: string) => {
    setSkills((current) => current.filter((item) => item !== value));
  };

  const onSkillInputKeyDown = (event: KeyboardEvent<HTMLInputElement>) => {
    if (event.key === "Enter" || event.key === ",") {
      event.preventDefault();
      addSkill(skillInput);
      return;
    }

    if (event.key === "Backspace" && skillInput.trim() === "" && skills.length > 0) {
      event.preventDefault();
      setSkills((current) => current.slice(0, current.length - 1));
    }
  };

  return (
    <form action="/profiles" className="mt-6 grid gap-3 md:grid-cols-2 lg:grid-cols-4" method="get">
      <label className="flex flex-col gap-1 text-sm text-[color:var(--text)]">
        Texte libre
        <input
          className="rounded-md border border-black/15 px-3 py-2 text-sm outline-none transition focus:border-[color:var(--accent)]"
          defaultValue={q}
          name="q"
          placeholder="Nom, texte CV..."
          type="text"
        />
      </label>

      <label className="flex flex-col gap-1 text-sm text-[color:var(--text)]">
        Technos (tags)
        <div className="rounded-md border border-black/15 px-2 py-2 focus-within:border-[color:var(--accent)]">
          <div className="mb-2 flex flex-wrap gap-2">
            {skills.length > 0 ? (
              skills.map((skill) => (
                <span
                  key={skill}
                  className="inline-flex items-center gap-1 rounded-full border border-black/10 bg-black/[0.04] px-2.5 py-1 text-xs text-[color:var(--text)]"
                >
                  {skill}
                  <button
                    aria-label={`Supprimer ${skill}`}
                    className="rounded-full px-1 text-[color:var(--text-muted)] hover:bg-black/10"
                    onClick={() => removeSkill(skill)}
                    type="button"
                  >
                    x
                  </button>
                </span>
              ))
            ) : (
              <span className="text-xs text-[color:var(--text-muted)]">Aucune techno ajoutee</span>
            )}
          </div>

          <div className="flex gap-2">
            <input
              className="w-full bg-transparent text-sm outline-none"
              onChange={(event) => setSkillInput(event.target.value)}
              onKeyDown={onSkillInputKeyDown}
              placeholder="Ex: Python"
              type="text"
              value={skillInput}
            />
            <button
              className="rounded-md border border-black/15 px-2 py-1 text-xs font-medium text-[color:var(--text)] hover:bg-black/5"
              onClick={() => addSkill(skillInput)}
              type="button"
            >
              Ajouter
            </button>
          </div>
        </div>
        <input name="skills" type="hidden" value={skills.join(",")} />
      </label>

      <label className="flex flex-col gap-1 text-sm text-[color:var(--text)]">
        Mode techno
        <select
          className="rounded-md border border-black/15 bg-white px-3 py-2 text-sm outline-none transition focus:border-[color:var(--accent)]"
          defaultValue={skillMode}
          name="skill_mode"
        >
          <option value="any">OU (au moins une techno)</option>
          <option value="all">ET (toutes les technos)</option>
        </select>
      </label>

      <label className="flex flex-col gap-1 text-sm text-[color:var(--text)]">
        Localisation
        <input
          className="rounded-md border border-black/15 px-3 py-2 text-sm outline-none transition focus:border-[color:var(--accent)]"
          defaultValue={location}
          name="location"
          placeholder="Ex: Paris, Remote"
          type="text"
        />
      </label>

      <label className="flex flex-col gap-1 text-sm text-[color:var(--text)]">
        Disponibilite
        <select
          className="rounded-md border border-black/15 bg-white px-3 py-2 text-sm outline-none transition focus:border-[color:var(--accent)]"
          defaultValue={availability}
          name="availability"
        >
          {AVAILABILITY_OPTIONS.map((option) => (
            <option key={option || "any"} value={option}>
              {option || "Toutes"}
            </option>
          ))}
        </select>
      </label>

      <label className="flex flex-col gap-1 text-sm text-[color:var(--text)]">
        Seniorite
        <input
          className="rounded-md border border-black/15 px-3 py-2 text-sm outline-none transition focus:border-[color:var(--accent)]"
          defaultValue={seniority}
          name="seniority"
          placeholder="Ex: Junior, Senior"
          type="text"
        />
      </label>

      <label className="flex flex-col gap-1 text-sm text-[color:var(--text)]">
        Langue
        <input
          className="rounded-md border border-black/15 px-3 py-2 text-sm outline-none transition focus:border-[color:var(--accent)]"
          defaultValue={language}
          name="language"
          placeholder="Ex: Francais, Anglais"
          type="text"
        />
      </label>

      <label className="flex flex-col gap-1 text-sm text-[color:var(--text)]">
        Tri
        <select
          className="rounded-md border border-black/15 bg-white px-3 py-2 text-sm outline-none transition focus:border-[color:var(--accent)]"
          defaultValue={sortBy}
          name="sort_by"
        >
          {SORT_OPTIONS.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </label>

      <div className="flex items-end gap-2 md:col-span-2 lg:col-span-4">
        <button
          className="rounded-md bg-[color:var(--accent)] px-4 py-2 text-sm font-semibold text-[color:var(--surface)] transition hover:opacity-90"
          type="submit"
        >
          Rechercher
        </button>
        <Link
          className="rounded-md border border-black/15 px-4 py-2 text-sm font-medium text-[color:var(--text)] hover:bg-black/5"
          href="/profiles"
        >
          Reinitialiser
        </Link>
        <p className="ml-auto text-sm text-[color:var(--text-muted)]">{resultsSummary}</p>
      </div>
    </form>
  );
}
