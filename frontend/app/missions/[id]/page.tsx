import Link from "next/link";
import { notFound } from "next/navigation";

import { AdminAuthPanel } from "@/components/admin-auth-panel";
import { MatchPill } from "@/components/match-pill";
import { RunMatchButton } from "@/components/run-match-button";
import { getMission, getMissionMatches, getProfiles } from "@/lib/api";

type MissionDetailPageProps = {
  params: Promise<{
    id: string;
  }>;
};

export default async function MissionDetailPage({ params }: MissionDetailPageProps) {
  const { id } = await params;
  const missionId = Number(id);

  if (!Number.isInteger(missionId) || missionId <= 0) {
    notFound();
  }

  const mission = await getMission(missionId);
  if (!mission) {
    notFound();
  }

  const [matches, profiles] = await Promise.all([getMissionMatches(missionId), getProfiles()]);
  const profileById = new Map(profiles.map((profile) => [profile.id, profile]));

  return (
    <main className="mx-auto w-full max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
      <section className="mb-6 rounded-2xl border border-black/10 bg-white p-6">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <p className="text-xs uppercase tracking-[0.18em] text-[color:var(--text-muted)]">Mission detail</p>
            <h1 className="mt-2 text-3xl font-semibold text-[color:var(--text-strong)]">{mission.title}</h1>
            <p className="mt-2 max-w-3xl text-sm text-[color:var(--text)]">{mission.description}</p>
            <p className="mt-3 text-xs uppercase tracking-wide text-[color:var(--text-muted)]">
              Skills: {mission.required_skills.join(", ") || "n/a"}
            </p>
          </div>
          <div className="flex flex-col gap-2">
            <AdminAuthPanel />
            <RunMatchButton missionId={mission.id} />
            <Link
              href="/missions"
              className="rounded-md border border-black/10 px-3 py-2 text-sm font-medium hover:bg-black/5"
            >
              Retour missions
            </Link>
          </div>
        </div>
      </section>

      <section className="overflow-hidden rounded-xl border border-black/10 bg-white">
        <table className="min-w-full divide-y divide-black/5 text-sm">
          <thead className="bg-black/[0.03] text-left text-xs uppercase tracking-wide text-[color:var(--text-muted)]">
            <tr>
              <th className="px-4 py-3">Profil</th>
              <th className="px-4 py-3">Final</th>
              <th className="px-4 py-3">Structured</th>
              <th className="px-4 py-3">Semantic</th>
              <th className="px-4 py-3">Business</th>
              <th className="px-4 py-3">Tags</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-black/5">
            {matches.length === 0 ? (
              <tr>
                <td colSpan={6} className="px-4 py-6 text-[color:var(--text-muted)]">
                  Aucune shortlist. Clique sur Recalculer shortlist.
                </td>
              </tr>
            ) : (
              matches.map((match) => {
                const profile = profileById.get(match.profile_id);
                return (
                  <tr key={match.id}>
                    <td className="px-4 py-3 font-medium text-[color:var(--text-strong)]">
                      {profile?.full_name ?? `Profile #${match.profile_id}`}
                    </td>
                    <td className="px-4 py-3">
                      <MatchPill score={match.final_score} />
                    </td>
                    <td className="px-4 py-3">{match.structured_score.toFixed(1)}</td>
                    <td className="px-4 py-3">{match.semantic_score.toFixed(1)}</td>
                    <td className="px-4 py-3">{match.business_score.toFixed(1)}</td>
                    <td className="px-4 py-3 text-[color:var(--text-muted)]">
                      {match.explanation_tags.length ? match.explanation_tags.join(", ") : "-"}
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </section>
    </main>
  );
}
