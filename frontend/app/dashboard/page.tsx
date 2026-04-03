import { Suspense } from "react";
import { StatCard } from "@/components/stat-card";
import { DashboardCharts } from "@/components/dashboard-charts";
import { getMissions, getProfiles } from "@/lib/api";

// Mock data for charts - in production, this would come from analytics API
const mockProfileBySeniority = [
  { name: "Junior", value: 35 },
  { name: "Mid", value: 45 },
  { name: "Senior", value: 20 },
];

const mockMissionsByStatus = [
  { name: "Draft", value: 5 },
  { name: "Open", value: 12 },
  { name: "In Progress", value: 8 },
  { name: "Closed", value: 15 },
];

const mockMatchScoreDistribution = [
  { name: "0-20", value: 5 },
  { name: "20-40", value: 12 },
  { name: "40-60", value: 28 },
  { name: "60-80", value: 35 },
  { name: "80-100", value: 20 },
];

const mockProfileTrends = [
  { date: "2026-03-01", count: 5 },
  { date: "2026-03-08", count: 12 },
  { date: "2026-03-15", count: 18 },
  { date: "2026-03-22", count: 25 },
  { date: "2026-03-29", count: 35 },
  { date: "2026-04-03", count: 42 },
];

const mockMissionTrends = [
  { date: "2026-03-01", count: 2 },
  { date: "2026-03-08", count: 3 },
  { date: "2026-03-15", count: 5 },
  { date: "2026-03-22", count: 7 },
  { date: "2026-03-29", count: 10 },
  { date: "2026-04-03", count: 12 },
];

async function DashboardContent() {
  const [profiles, missions] = await Promise.all([getProfiles(), getMissions()]);

  const recentProfiles = profiles.slice(0, 5);
  const recentMissions = missions.slice(0, 5);

  // Calculate trends
  const profilesThisWeek = profiles.filter((p) => {
    const created = new Date(p.created_at || "");
    const weekAgo = new Date();
    weekAgo.setDate(weekAgo.getDate() - 7);
    return created > weekAgo;
  }).length;

  const missionsThisWeek = missions.filter((m) => {
    const created = new Date(m.created_at || "");
    const weekAgo = new Date();
    weekAgo.setDate(weekAgo.getDate() - 7);
    return created > weekAgo;
  }).length;

  return (
    <>
      <section className="mb-8 rounded-2xl border border-black/10 bg-[linear-gradient(145deg,#fef3c7_0%,#ffffff_65%)] p-6">
        <p className="text-xs uppercase tracking-[0.18em] text-[color:var(--text-muted)]">
          Overview
        </p>
        <h1 className="mt-2 text-3xl font-semibold text-[color:var(--text-strong)]">
          Dashboard RM
        </h1>
        <p className="mt-2 max-w-2xl text-sm text-[color:var(--text)]">
          Vue synthétique du stock de profils, des missions ouvertes et des dernières actions de matching.
        </p>
      </section>

      <section className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <StatCard
          label="Profils"
          value={String(profiles.length)}
          delta={`+${profilesThisWeek} cette semaine`}
          trend={profilesThisWeek > 0 ? "up" : "neutral"}
        />
        <StatCard
          label="Missions"
          value={String(missions.length)}
          delta={`+${missionsThisWeek} cette semaine`}
          trend={missionsThisWeek > 0 ? "up" : "neutral"}
        />
        <StatCard
          label="Shortlists"
          value={String(Math.min(missions.length, 10))}
          delta="Mise à jour aujourd'hui"
          trend="neutral"
        />
        <StatCard
          label="Score moyen"
          value="67%"
          delta="+5% vs semaine dernière"
          trend="up"
        />
      </section>

      <section className="mt-8">
        <DashboardCharts
          profileBySeniority={mockProfileBySeniority}
          missionsByStatus={mockMissionsByStatus}
          matchScoreDistribution={mockMatchScoreDistribution}
          profileTrends={mockProfileTrends}
          missionTrends={mockMissionTrends}
        />
      </section>

      <section className="mt-8 grid gap-6 lg:grid-cols-2">
        <article className="rounded-xl border border-black/10 bg-white p-5">
          <h2 className="text-lg font-semibold text-[color:var(--text-strong)]">
            Derniers imports
          </h2>
          <ul className="mt-4 space-y-3 text-sm">
            {recentProfiles.length === 0 ? (
              <li className="text-[color:var(--text-muted)]">
                Aucun profil importé.
              </li>
            ) : (
              recentProfiles.map((profile) => (
                <li
                  key={profile.id}
                  className="flex items-center justify-between rounded-md border border-black/5 px-3 py-2"
                >
                  <span className="font-medium text-[color:var(--text-strong)]">
                    {profile.full_name}
                  </span>
                  <span className="text-[color:var(--text-muted)]">
                    {profile.parsed_seniority ?? "n/a"}
                  </span>
                </li>
              ))
            )}
          </ul>
        </article>

        <article className="rounded-xl border border-black/10 bg-white p-5">
          <h2 className="text-lg font-semibold text-[color:var(--text-strong)]">
            Dernières missions
          </h2>
          <ul className="mt-4 space-y-3 text-sm">
            {recentMissions.length === 0 ? (
              <li className="text-[color:var(--text-muted)]">
                Aucune mission créée.
              </li>
            ) : (
              recentMissions.map((mission) => (
                <li
                  key={mission.id}
                  className="rounded-md border border-black/5 px-3 py-2"
                >
                  <p className="font-medium text-[color:var(--text-strong)]">
                    {mission.title}
                  </p>
                  <p className="mt-1 text-[color:var(--text-muted)] line-clamp-2">
                    {mission.description}
                  </p>
                </li>
              ))
            )}
          </ul>
        </article>
      </section>

      <section className="mt-8 rounded-xl border border-black/10 bg-white p-5">
        <h2 className="text-lg font-semibold text-[color:var(--text-strong)]">
          Activité récente
        </h2>
        <ul className="mt-4 space-y-3 text-sm">
          <li className="flex items-center gap-3 rounded-md border border-black/5 px-3 py-2">
            <span className="inline-flex items-center rounded-full bg-green-100 px-2 py-0.5 text-xs font-medium text-green-800">
              Créé
            </span>
            <span className="text-[color:var(--text)]">Nouveau profil importé</span>
            <span className="ml-auto text-[color:var(--text-muted)]">Il y a 5 min</span>
          </li>
          <li className="flex items-center gap-3 rounded-md border border-black/5 px-3 py-2">
            <span className="inline-flex items-center rounded-full bg-blue-100 px-2 py-0.5 text-xs font-medium text-blue-800">
              Match
            </span>
            <span className="text-[color:var(--text)]">Matching effectué pour Mission #12</span>
            <span className="ml-auto text-[color:var(--text-muted)]">Il y a 15 min</span>
          </li>
          <li className="flex items-center gap-3 rounded-md border border-black/5 px-3 py-2">
            <span className="inline-flex items-center rounded-full bg-yellow-100 px-2 py-0.5 text-xs font-medium text-yellow-800">
              Mise à jour
            </span>
            <span className="text-[color:var(--text)]">Profil #42 mis à jour</span>
            <span className="ml-auto text-[color:var(--text-muted)]">Il y a 1h</span>
          </li>
        </ul>
      </section>
    </>
  );
}

export default function DashboardPage() {
  return (
    <main className="mx-auto w-full max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
      <Suspense fallback={<DashboardSkeleton />}>
        <DashboardContent />
      </Suspense>
    </main>
  );
}

function DashboardSkeleton() {
  return (
    <div className="animate-pulse space-y-8">
      <div className="h-32 rounded-2xl bg-gray-200" />
      <div className="grid gap-4 md:grid-cols-4">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="h-24 rounded-xl bg-gray-200" />
        ))}
      </div>
      <div className="grid gap-6 lg:grid-cols-2">
        {[...Array(2)].map((_, i) => (
          <div key={i} className="h-64 rounded-xl bg-gray-200" />
        ))}
      </div>
    </div>
  );
}