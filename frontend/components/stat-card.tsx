type StatCardProps = {
  label: string;
  value: string;
  delta: string;
};

export function StatCard({ label, value, delta }: StatCardProps) {
  return (
    <article className="rounded-xl border border-black/10 bg-white p-5 shadow-[0_8px_30px_rgba(0,0,0,0.04)]">
      <p className="text-xs uppercase tracking-[0.14em] text-[color:var(--text-muted)]">{label}</p>
      <p className="mt-3 text-3xl font-semibold text-[color:var(--text-strong)]">{value}</p>
      <p className="mt-2 text-sm text-[color:var(--accent)]">{delta}</p>
    </article>
  );
}
