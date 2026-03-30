import { getProfiles } from "@/lib/api";
import Link from "next/link";

export default async function ProfilesPage() {
  const profiles = await getProfiles();

  return (
    <main className="mx-auto w-full max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
      <section className="mb-8 rounded-2xl border border-black/10 bg-white p-6">
        <p className="text-xs uppercase tracking-[0.18em] text-[color:var(--text-muted)]">Profiles</p>
        <h1 className="mt-2 text-3xl font-semibold text-[color:var(--text-strong)]">Recherche profils</h1>
        <p className="mt-2 max-w-2xl text-sm text-[color:var(--text)]">
          Vue catalogue avec informations structurées extraites des CV.
        </p>
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
            </tr>
          </thead>
          <tbody className="divide-y divide-black/5 text-sm">
            {profiles.length === 0 ? (
              <tr>
                <td className="px-4 py-6 text-[color:var(--text-muted)]" colSpan={5}>
                  Aucun profil disponible pour le moment. Utilise l&apos;endpoint d&apos;upload pour injecter des CV.
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
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </main>
  );
}
