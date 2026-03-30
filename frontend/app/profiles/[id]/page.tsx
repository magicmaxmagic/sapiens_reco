import Link from "next/link";
import { notFound } from "next/navigation";

import { ProfileEditForm } from "@/components/profile-edit-form";
import { getProfile } from "@/lib/api";

type ProfilePageProps = {
  params: Promise<{
    id: string;
  }>;
};

export default async function ProfilePage({ params }: ProfilePageProps) {
  const { id } = await params;
  const profileId = Number(id);

  if (!Number.isInteger(profileId) || profileId <= 0) {
    notFound();
  }

  const profile = await getProfile(profileId);
  if (!profile) {
    notFound();
  }

  return (
    <main className="mx-auto w-full max-w-5xl px-4 py-8 sm:px-6 lg:px-8">
      <section className="mb-6 rounded-2xl border border-black/10 bg-white p-6">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <p className="text-xs uppercase tracking-[0.18em] text-[color:var(--text-muted)]">
              Correction manuelle
            </p>
            <h1 className="mt-2 text-2xl font-semibold text-[color:var(--text-strong)]">
              {profile.full_name}
            </h1>
            <p className="mt-2 text-sm text-[color:var(--text)]">
              Ajuste les champs structures extraits depuis le CV, puis enregistre.
            </p>
          </div>
          <Link
            href="/profiles"
            className="rounded-md border border-black/10 px-3 py-2 text-sm font-medium text-[color:var(--text)] hover:bg-black/5"
          >
            Retour a la liste
          </Link>
        </div>
      </section>

      <section className="rounded-xl border border-black/10 bg-white p-6">
        <ProfileEditForm profile={profile} />
      </section>
    </main>
  );
}
