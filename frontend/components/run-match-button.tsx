"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

import { ApiError, runMissionMatch } from "@/lib/api";

type RunMatchButtonProps = {
  missionId: number;
};

export function RunMatchButton({ missionId }: RunMatchButtonProps) {
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const onRun = async () => {
    setIsLoading(true);
    setError(null);
    try {
      await runMissionMatch(missionId, 10);
      router.refresh();
    } catch (error) {
      if (error instanceof ApiError && error.status === 401) {
        setError("Authentification admin requise.");
      } else {
        setError("Impossible de lancer le matching.");
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col items-start gap-2">
      <button
        type="button"
        onClick={onRun}
        disabled={isLoading}
        className="rounded-md bg-[color:var(--accent)] px-4 py-2 text-sm font-semibold text-white disabled:opacity-60"
      >
        {isLoading ? "Matching..." : "Recalculer shortlist"}
      </button>
      {error ? <span className="text-xs text-rose-700">{error}</span> : null}
    </div>
  );
}
