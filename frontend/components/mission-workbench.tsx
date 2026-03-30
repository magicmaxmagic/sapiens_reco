"use client";

import Link from "next/link";
import { useMemo, useState, type FormEvent } from "react";

import { AdminAuthPanel } from "@/components/admin-auth-panel";
import { MatchPill } from "@/components/match-pill";
import {
  ApiError,
  createMission,
  getMissionMatches,
  runMissionMatch,
  updateMission,
  type MatchResult,
  type Mission,
  type Profile,
} from "@/lib/api";

function toCsv(values: string[]): string {
  return values.join(", ");
}

function fromCsv(value: string): string[] {
  return value
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}

type MissionFormState = {
  title: string;
  description: string;
  requiredSkillsCsv: string;
  requiredLanguage: string;
  requiredLocation: string;
  requiredSeniority: string;
  desiredStartDate: string;
};

const EMPTY_FORM: MissionFormState = {
  title: "",
  description: "",
  requiredSkillsCsv: "",
  requiredLanguage: "",
  requiredLocation: "",
  requiredSeniority: "",
  desiredStartDate: "",
};

function missionToForm(mission: Mission): MissionFormState {
  return {
    title: mission.title,
    description: mission.description,
    requiredSkillsCsv: toCsv(mission.required_skills),
    requiredLanguage: mission.required_language ?? "",
    requiredLocation: mission.required_location ?? "",
    requiredSeniority: mission.required_seniority ?? "",
    desiredStartDate: mission.desired_start_date ?? "",
  };
}

type MissionWorkbenchProps = {
  initialMissions: Mission[];
  initialProfiles: Profile[];
  initialMatches: MatchResult[];
};

export function MissionWorkbench({
  initialMissions,
  initialProfiles,
  initialMatches,
}: MissionWorkbenchProps) {
  const [missions, setMissions] = useState(initialMissions);
  const [selectedMissionId, setSelectedMissionId] = useState<number | null>(initialMissions[0]?.id ?? null);
  const [editingMissionId, setEditingMissionId] = useState<number | null>(null);
  const [matches, setMatches] = useState(initialMatches);

  const [form, setForm] = useState<MissionFormState>(
    initialMissions[0] ? missionToForm(initialMissions[0]) : EMPTY_FORM,
  );

  const [isSaving, setIsSaving] = useState(false);
  const [isMatching, setIsMatching] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const profileById = useMemo(
    () => new Map(initialProfiles.map((profile) => [profile.id, profile])),
    [initialProfiles],
  );

  const selectedMission = missions.find((mission) => mission.id === selectedMissionId) ?? null;

  const setField = (field: keyof MissionFormState, value: string) => {
    setForm((previous) => ({ ...previous, [field]: value }));
  };

  const resetForCreate = () => {
    setEditingMissionId(null);
    setForm(EMPTY_FORM);
    setMessage(null);
    setError(null);
  };

  const selectMission = async (mission: Mission) => {
    setSelectedMissionId(mission.id);
    setEditingMissionId(mission.id);
    setForm(missionToForm(mission));
    setMessage(null);
    setError(null);

    try {
      const refreshedMatches = await getMissionMatches(mission.id);
      setMatches(refreshedMatches);
    } catch {
      setMatches([]);
    }
  };

  const handleSave = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setIsSaving(true);
    setMessage(null);
    setError(null);

    const payload = {
      title: form.title.trim(),
      description: form.description.trim(),
      required_skills: fromCsv(form.requiredSkillsCsv),
      required_language: form.requiredLanguage.trim() || null,
      required_location: form.requiredLocation.trim() || null,
      required_seniority: form.requiredSeniority.trim() || null,
      desired_start_date: form.desiredStartDate.trim() || null,
    };

    try {
      if (editingMissionId) {
        const updated = await updateMission(editingMissionId, payload);
        setMissions((previous) => previous.map((mission) => (mission.id === updated.id ? updated : mission)));
        setForm(missionToForm(updated));
        setMessage("Mission mise a jour.");
      } else {
        const created = await createMission(payload);
        setMissions((previous) => [created, ...previous]);
        setSelectedMissionId(created.id);
        setEditingMissionId(created.id);
        setForm(missionToForm(created));
        setMatches([]);
        setMessage("Mission creee.");
      }
    } catch (error) {
      if (error instanceof ApiError && error.status === 401) {
        setError("Authentification admin requise.");
      } else {
        setError("Impossible d'enregistrer la mission.");
      }
    } finally {
      setIsSaving(false);
    }
  };

  const handleRunMatching = async () => {
    if (!selectedMissionId) {
      setError("Selectionne une mission avant de lancer le matching.");
      return;
    }

    setIsMatching(true);
    setError(null);
    setMessage(null);
    try {
      const generated = await runMissionMatch(selectedMissionId, 10);
      setMatches(generated);
      setMessage("Shortlist mise a jour.");
    } catch (error) {
      if (error instanceof ApiError && error.status === 401) {
        setError("Authentification admin requise.");
      } else {
        setError("Erreur pendant le calcul de matching.");
      }
    } finally {
      setIsMatching(false);
    }
  };

  return (
    <div className="space-y-6">
      <AdminAuthPanel />

      <section className="grid gap-6 lg:grid-cols-[2fr_3fr]">
        <article className="rounded-xl border border-black/10 bg-white p-5">
        <div className="mb-4 flex items-center justify-between gap-3">
          <h2 className="text-lg font-semibold text-[color:var(--text-strong)]">Missions</h2>
          <button
            className="rounded-md border border-black/10 px-3 py-2 text-xs font-medium hover:bg-black/5"
            type="button"
            onClick={resetForCreate}
          >
            Nouvelle mission
          </button>
        </div>

        <ul className="space-y-2 text-sm">
          {missions.length === 0 ? (
            <li className="text-[color:var(--text-muted)]">Aucune mission disponible.</li>
          ) : (
            missions.map((mission) => {
              const selected = mission.id === selectedMissionId;
              return (
                <li
                  key={mission.id}
                  className={`rounded-md border px-3 py-3 ${selected ? "border-[color:var(--accent)] bg-emerald-50/60" : "border-black/5"}`}
                >
                  <div className="flex items-center justify-between gap-3">
                    <button
                      type="button"
                      onClick={() => void selectMission(mission)}
                      className="text-left"
                    >
                      <p className="font-medium text-[color:var(--text-strong)]">{mission.title}</p>
                      <p className="mt-1 line-clamp-2 text-xs text-[color:var(--text-muted)]">{mission.description}</p>
                    </button>
                    <Link
                      href={`/missions/${mission.id}`}
                      className="rounded-md border border-black/10 px-2 py-1 text-xs hover:bg-black/5"
                    >
                      Detail
                    </Link>
                  </div>
                </li>
              );
            })
          )}
        </ul>

        <button
          type="button"
          onClick={() => void handleRunMatching()}
          disabled={isMatching || !selectedMissionId}
          className="mt-4 rounded-md bg-[color:var(--accent)] px-4 py-2 text-sm font-semibold text-white disabled:opacity-60"
        >
          {isMatching ? "Matching..." : "Lancer matching"}
        </button>
        </article>

        <article className="rounded-xl border border-black/10 bg-white p-5">
        <h2 className="text-lg font-semibold text-[color:var(--text-strong)]">Creation / edition mission</h2>
        <form onSubmit={handleSave} className="mt-4 space-y-4 text-sm">
          <label className="block space-y-1">
            <span className="font-medium">Titre</span>
            <input
              className="w-full rounded-md border border-black/15 px-3 py-2"
              value={form.title}
              onChange={(event) => setField("title", event.target.value)}
              required
            />
          </label>

          <label className="block space-y-1">
            <span className="font-medium">Description</span>
            <textarea
              className="min-h-24 w-full rounded-md border border-black/15 px-3 py-2"
              value={form.description}
              onChange={(event) => setField("description", event.target.value)}
              required
            />
          </label>

          <div className="grid gap-3 sm:grid-cols-2">
            <label className="space-y-1">
              <span className="font-medium">Skills (CSV)</span>
              <input
                className="w-full rounded-md border border-black/15 px-3 py-2"
                value={form.requiredSkillsCsv}
                onChange={(event) => setField("requiredSkillsCsv", event.target.value)}
              />
            </label>
            <label className="space-y-1">
              <span className="font-medium">Langue</span>
              <input
                className="w-full rounded-md border border-black/15 px-3 py-2"
                value={form.requiredLanguage}
                onChange={(event) => setField("requiredLanguage", event.target.value)}
              />
            </label>
            <label className="space-y-1">
              <span className="font-medium">Localisation</span>
              <input
                className="w-full rounded-md border border-black/15 px-3 py-2"
                value={form.requiredLocation}
                onChange={(event) => setField("requiredLocation", event.target.value)}
              />
            </label>
            <label className="space-y-1">
              <span className="font-medium">Seniorite</span>
              <input
                className="w-full rounded-md border border-black/15 px-3 py-2"
                value={form.requiredSeniority}
                onChange={(event) => setField("requiredSeniority", event.target.value)}
              />
            </label>
          </div>

          <label className="block space-y-1">
            <span className="font-medium">Date de demarrage souhaitee</span>
            <input
              type="date"
              className="w-full rounded-md border border-black/15 px-3 py-2"
              value={form.desiredStartDate}
              onChange={(event) => setField("desiredStartDate", event.target.value)}
            />
          </label>

          <button
            type="submit"
            className="rounded-md border border-black/10 px-4 py-2 font-medium hover:bg-black/5 disabled:opacity-60"
            disabled={isSaving}
          >
            {isSaving ? "Enregistrement..." : editingMissionId ? "Mettre a jour" : "Creer"}
          </button>

          {message ? <p className="text-emerald-700">{message}</p> : null}
          {error ? <p className="text-rose-700">{error}</p> : null}
        </form>

        <div className="mt-8">
          <h3 className="text-base font-semibold text-[color:var(--text-strong)]">
            Shortlist rapide {selectedMission ? `- ${selectedMission.title}` : ""}
          </h3>
          <ul className="mt-3 space-y-2 text-sm">
            {matches.length === 0 ? (
              <li className="text-[color:var(--text-muted)]">Aucun resultat. Lance le matching.</li>
            ) : (
              matches.slice(0, 10).map((match) => {
                const profile = profileById.get(match.profile_id);
                return (
                  <li key={match.id} className="rounded-md border border-black/5 px-3 py-3">
                    <div className="flex items-center justify-between gap-3">
                      <span className="font-medium text-[color:var(--text-strong)]">
                        {profile?.full_name ?? `Profile #${match.profile_id}`}
                      </span>
                      <MatchPill score={match.final_score} />
                    </div>
                    <p className="mt-1 text-xs text-[color:var(--text-muted)]">
                      Structured {match.structured_score.toFixed(1)} | Semantic {match.semantic_score.toFixed(1)} | Business {match.business_score.toFixed(1)}
                    </p>
                  </li>
                );
              })
            )}
          </ul>
        </div>
        </article>
      </section>
    </div>
  );
}
