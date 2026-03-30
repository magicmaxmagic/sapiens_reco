type MatchPillProps = {
  score: number;
};

export function MatchPill({ score }: MatchPillProps) {
  const hueClass =
    score >= 75
      ? "bg-emerald-100 text-emerald-800"
      : score >= 50
        ? "bg-amber-100 text-amber-800"
        : "bg-rose-100 text-rose-800";

  return (
    <span className={`inline-flex items-center rounded-full px-2.5 py-1 text-xs font-semibold ${hueClass}`}>
      {Math.round(score)}%
    </span>
  );
}
