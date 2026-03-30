import { StatCard } from "@/components/stat-card";
import { getMissions, getProfiles } from "@/lib/api";

export default async function DashboardPage() {
  const [profiles, missions] = await Promise.all([getProfiles(), getMissions()]);

  const recentProfiles = profiles.slice(0, 5);
  const recentMissions = missions.slice(0, 5);

  return (
    <main className="mx-auto w-full max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
      <section className="mb-8 rounded-2xl border border-black/10 bg-[linear-gradient(145deg,#fef3c7_0%,#ffffff_65%)] p-6">
        <p className="text-xs uppercase tracking-[0.18em] text-[color:var(--text-muted)]">Overview</p>
        <h1 className="mt-2 text-3xl font-semibold text-[color:var(--text-strong)]">Dashboard RM</h1>
        <p className="mt-2 max-w-2xl text-sm text-[color:var(--text)]">
          Vue synthétique du stock de profils, des missions ouvertes et des dernières actions de matching.
        </p>
      </section>

      <section className="grid gap-4 md:grid-cols-3">
        <StatCard label="Profils" value={String(profiles.length)} delta="+12 cette semaine" />
        <StatCard label="Missions" value={String(missions.length)} delta="3 ouvertes" />
        <StatCard label="Shortlists" value={String(Math.min(missions.length, 10))} delta="Mise à jour aujourd'hui" />
      </section>

      <section className="mt-8 grid gap-6 lg:grid-cols-2">
        <article className="rounded-xl border border-black/10 bg-white p-5">
          <h2 className="text-lg font-semibold text-[color:var(--text-strong)]">Derniers imports</h2>
          <ul className="mt-4 space-y-3 text-sm">
            {recentProfiles.length === 0 ? (
              <li className="text-[color:var(--text-muted)]">Aucun profil importé.</li>
            ) : (
              recentProfiles.map((profile) => (
                <li key={profile.id} className="flex items-center justify-between rounded-md border border-black/5 px-3 py-2">
                  <span className="font-medium text-[color:var(--text-strong)]">{profile.full_name}</span>
                  <span className="text-[color:var(--text-muted)]">{profile.parsed_seniority ?? "n/a"}</span>
                </li>
              ))
            )}
          </ul>
        </article>

        <article className="rounded-xl border border-black/10 bg-white p-5">
          <h2 className="text-lg font-semibold text-[color:var(--text-strong)]">Dernières missions</h2>
          <ul className="mt-4 space-y-3 text-sm">
            {recentMissions.length === 0 ? (
              <li className="text-[color:var(--text-muted)]">Aucune mission créée.</li>
            ) : (
              recentMissions.map((mission) => (
                <li key={mission.id} className="rounded-md border border-black/5 px-3 py-2">
                  <p className="font-medium text-[color:var(--text-strong)]">{mission.title}</p>
                  <p className="mt-1 text-[color:var(--text-muted)] line-clamp-2">{mission.description}</p>
                </li>
              ))
            )}
          </ul>
        </article>
      </section>
    </main>
  );
}
