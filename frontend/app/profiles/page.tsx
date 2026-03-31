import { searchProfiles } from "@/lib/api";
import Link from "next/link";

import { ProfileSearchFilters } from "@/components/profile-search-filters";

type ProfilesPageProps = {
  searchParams: Promise<{
    q?: string | string[];
    skills?: string | string[];
    skill_mode?: string | string[];
    location?: string | string[];
    availability?: string | string[];
    seniority?: string | string[];
    language?: string | string[];
    sort_by?: string | string[];
    page?: string | string[];
  }>;
};

const PAGE_SIZE = 25;

function getValue(param: string | string[] | undefined): string {
  if (Array.isArray(param)) {
    return (param[0] ?? "").trim();
  }
  return (param ?? "").trim();
}

const SORT_LABELS: Record<"relevance" | "date" | "seniority", string> = {
  relevance: "Pertinence",
  date: "Date",
  seniority: "Seniorite",
};

function parsePositiveInt(raw: string, fallback: number): number {
  const value = Number.parseInt(raw, 10);
  if (!Number.isFinite(value) || value < 1) {
    return fallback;
  }
  return value;
}

function parseSkills(raw: string): string[] {
  const unique = new Set<string>();
  raw
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean)
    .forEach((item) => unique.add(item));
  return Array.from(unique);
}

function normalizeSkillMode(raw: string): "any" | "all" {
  return raw.toLowerCase() === "all" ? "all" : "any";
}

function normalizeSortBy(raw: string): "relevance" | "date" | "seniority" {
  if (raw === "date" || raw === "seniority") {
    return raw;
  }
  return "relevance";
}

function buildProfilesHref(params: {
  q: string;
  skillsRaw: string;
  skillMode: "any" | "all";
  location: string;
  availability: string;
  seniority: string;
  language: string;
  sortBy: "relevance" | "date" | "seniority";
  page: number;
}): string {
  const search = new URLSearchParams();

  if (params.q) {
    search.set("q", params.q);
  }
  if (params.skillsRaw) {
    search.set("skills", params.skillsRaw);
  }
  if (params.skillMode !== "any") {
    search.set("skill_mode", params.skillMode);
  }
  if (params.location) {
    search.set("location", params.location);
  }
  if (params.availability) {
    search.set("availability", params.availability);
  }
  if (params.seniority) {
    search.set("seniority", params.seniority);
  }
  if (params.language) {
    search.set("language", params.language);
  }
  if (params.sortBy !== "relevance") {
    search.set("sort_by", params.sortBy);
  }
  if (params.page > 1) {
    search.set("page", String(params.page));
  }

  const query = search.toString();
  return query ? `/profiles?${query}` : "/profiles";
}

function sortLabel(value: "relevance" | "date" | "seniority"): string {
  return SORT_LABELS[value] ?? "Pertinence";
}

function paginationWindow(currentPage: number, totalPages: number): number[] {
  if (totalPages <= 1) {
    return [1];
  }

  const windowSize = 5;
  let start = Math.max(1, currentPage - 2);
  const end = Math.min(totalPages, start + windowSize - 1);

  if (end - start + 1 < windowSize) {
    start = Math.max(1, end - windowSize + 1);
  }

  const pages: number[] = [];
  for (let page = start; page <= end; page += 1) {
    pages.push(page);
  }
  return pages;
}

export default async function ProfilesPage({ searchParams }: ProfilesPageProps) {
  const params = await searchParams;

  const q = getValue(params.q);
  const skillsRaw = getValue(params.skills);
  const skillMode = normalizeSkillMode(getValue(params.skill_mode));
  const location = getValue(params.location);
  const availability = getValue(params.availability);
  const seniority = getValue(params.seniority);
  const language = getValue(params.language);
  const sortBy = normalizeSortBy(getValue(params.sort_by));
  const requestedPage = parsePositiveInt(getValue(params.page), 1);

  const skills = parseSkills(skillsRaw);
  const baseFilters = {
    q: q || undefined,
    skills: skills.length > 0 ? skills : undefined,
    skillMode,
    location: location || undefined,
    availability: availability || undefined,
    seniority: seniority || undefined,
    language: language || undefined,
    sortBy,
  };

  const offset = (requestedPage - 1) * PAGE_SIZE;

  let searchResult = await searchProfiles({
    ...baseFilters,
    limit: PAGE_SIZE,
    offset,
  });

  let profiles = searchResult.items;
  const total = searchResult.total;
  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));
  let currentPage = requestedPage;

  if (total > 0 && requestedPage > totalPages) {
    currentPage = totalPages;
    searchResult = await searchProfiles({
      ...baseFilters,
      limit: PAGE_SIZE,
      offset: (currentPage - 1) * PAGE_SIZE,
    });
    profiles = searchResult.items;
  }

  const from = total === 0 ? 0 : (currentPage - 1) * PAGE_SIZE + 1;
  const to = total === 0 ? 0 : (currentPage - 1) * PAGE_SIZE + profiles.length;
  const pageWindow = paginationWindow(currentPage, totalPages);

  const activeFilters = [
    ["Texte", q],
    ["Technos", skills.join(", ")],
    ["Mode techno", skills.length > 0 ? (skillMode === "all" ? "ET" : "OU") : ""],
    ["Localisation", location],
    ["Disponibilite", availability],
    ["Seniorite", seniority],
    ["Langue", language],
  ].filter((entry): entry is [string, string] => Boolean(entry[1]));

  const baseHrefParams = {
    q,
    skillsRaw,
    skillMode,
    location,
    availability,
    seniority,
    language,
    sortBy,
  };

  return (
    <main className="mx-auto w-full max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
      <section className="mb-8 rounded-2xl border border-black/10 bg-white p-6">
        <p className="text-xs uppercase tracking-[0.18em] text-[color:var(--text-muted)]">Profiles</p>
        <h1 className="mt-2 text-3xl font-semibold text-[color:var(--text-strong)]">Recherche profils</h1>
        <p className="mt-2 max-w-2xl text-sm text-[color:var(--text)]">
          Recherche consultants par techno, localisation, disponibilite et criteres metier.
        </p>

        <ProfileSearchFilters
          availability={availability}
          language={language}
          location={location}
          q={q}
          resultsSummary={`${from}-${to} sur ${total} profil(s)`}
          seniority={seniority}
          skillMode={skillMode}
          skillsRaw={skillsRaw}
          sortBy={sortBy}
        />

        <div className="mt-3 flex flex-wrap items-center gap-2">
          {activeFilters.length > 0 ? (
            activeFilters.map(([label, value]) => (
              <span
                key={`${label}-${value}`}
                className="inline-flex items-center rounded-full border border-black/10 bg-black/[0.03] px-2.5 py-1 text-xs text-[color:var(--text)]"
              >
                {label}: {value}
              </span>
            ))
          ) : (
            <span className="text-xs text-[color:var(--text-muted)]">Aucun filtre actif</span>
          )}
          <span className="inline-flex items-center rounded-full border border-black/10 bg-black/[0.03] px-2.5 py-1 text-xs text-[color:var(--text)]">
            Tri: {sortLabel(sortBy)}
          </span>
        </div>
      </section>

      <div className="overflow-hidden rounded-xl border border-black/10 bg-white">
        <table className="min-w-full divide-y divide-black/5">
          <thead className="bg-black/[0.03] text-left text-xs uppercase tracking-wide text-[color:var(--text-muted)]">
            <tr>
              <th className="px-4 py-3">Nom</th>
              <th className="px-4 py-3">Compétences</th>
              <th className="px-4 py-3">Langues</th>
              <th className="px-4 py-3">Localisation</th>
              <th className="px-4 py-3">Séniorité</th>
              <th className="px-4 py-3">Disponibilité</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-black/5 text-sm">
            {profiles.length === 0 ? (
              <tr>
                <td className="px-4 py-6 text-[color:var(--text-muted)]" colSpan={6}>
                  Aucun profil trouve pour ces criteres. Ajuste les filtres ou reinitialise la recherche.
                </td>
              </tr>
            ) : (
              profiles.map((profile) => (
                <tr key={profile.id}>
                  <td className="px-4 py-3 font-medium text-[color:var(--text-strong)]">
                    <Link href={`/profiles/${profile.id}`} className="hover:underline">
                      {profile.full_name}
                    </Link>
                  </td>
                  <td className="px-4 py-3 text-[color:var(--text)]">
                    {profile.parsed_skills.length ? profile.parsed_skills.join(", ") : "-"}
                  </td>
                  <td className="px-4 py-3 text-[color:var(--text)]">
                    {profile.parsed_languages.length ? profile.parsed_languages.join(", ") : "-"}
                  </td>
                  <td className="px-4 py-3 text-[color:var(--text)]">{profile.parsed_location ?? "-"}</td>
                  <td className="px-4 py-3 text-[color:var(--text)]">{profile.parsed_seniority ?? "-"}</td>
                  <td className="px-4 py-3 text-[color:var(--text)]">{profile.availability_status || "-"}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      <section className="mt-4 flex flex-wrap items-center justify-between gap-3 rounded-xl border border-black/10 bg-white px-4 py-3">
        <p className="text-sm text-[color:var(--text-muted)]">
          Page {currentPage} / {totalPages}
        </p>

        <div className="flex flex-wrap items-center gap-2 text-sm">
          {currentPage > 1 ? (
            <Link
              className="rounded-md border border-black/15 px-3 py-1.5 text-[color:var(--text)] hover:bg-black/5"
              href={buildProfilesHref({ ...baseHrefParams, page: currentPage - 1 })}
            >
              Precedent
            </Link>
          ) : (
            <span className="rounded-md border border-black/10 px-3 py-1.5 text-[color:var(--text-muted)]">
              Precedent
            </span>
          )}

          {pageWindow.map((page) =>
            page === currentPage ? (
              <span
                key={page}
                className="rounded-md bg-[color:var(--accent)] px-3 py-1.5 font-semibold text-[color:var(--surface)]"
              >
                {page}
              </span>
            ) : (
              <Link
                key={page}
                className="rounded-md border border-black/15 px-3 py-1.5 text-[color:var(--text)] hover:bg-black/5"
                href={buildProfilesHref({ ...baseHrefParams, page })}
              >
                {page}
              </Link>
            ),
          )}

          {currentPage < totalPages ? (
            <Link
              className="rounded-md border border-black/15 px-3 py-1.5 text-[color:var(--text)] hover:bg-black/5"
              href={buildProfilesHref({ ...baseHrefParams, page: currentPage + 1 })}
            >
              Suivant
            </Link>
          ) : (
            <span className="rounded-md border border-black/10 px-3 py-1.5 text-[color:var(--text-muted)]">
              Suivant
            </span>
          )}
        </div>
      </section>
    </main>
  );
}
