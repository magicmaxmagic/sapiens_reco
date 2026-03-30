import { MissionWorkbench } from "@/components/mission-workbench";
import { getMissionMatches, getMissions, getProfiles } from "@/lib/api";

export default async function MissionsPage() {
  const missions = await getMissions();
  const profiles = await getProfiles();

  const topMission = missions[0];
  const matches = topMission ? await getMissionMatches(topMission.id) : [];

  return (
    <main className="mx-auto w-full max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
      <section className="mb-8 rounded-2xl border border-black/10 bg-[linear-gradient(145deg,#dcfce7_0%,#ffffff_65%)] p-6">
        <p className="text-xs uppercase tracking-[0.18em] text-[color:var(--text-muted)]">Missions</p>
        <h1 className="mt-2 text-3xl font-semibold text-[color:var(--text-strong)]">Missions & matching</h1>
        <p className="mt-2 max-w-2xl text-sm text-[color:var(--text)]">
          Lancement du matching depuis une mission et visualisation de la shortlist triée avec score.
        </p>
      </section>

      <MissionWorkbench initialMissions={missions} initialProfiles={profiles} initialMatches={matches} />
    </main>
  );
}
