import { cn } from "@/lib/utils";
import { ArrowDown, ArrowUp, Minus } from "lucide-react";

interface StatCardProps {
  label: string;
  value: string;
  delta: string;
  trend?: "up" | "down" | "neutral";
}

export function StatCard({ label, value, delta, trend = "neutral" }: StatCardProps) {
  const trendColors = {
    up: "text-green-600 bg-green-50",
    down: "text-red-600 bg-red-50",
    neutral: "text-[color:var(--text-muted)] bg-gray-50",
  };

  const TrendIcon = {
    up: ArrowUp,
    down: ArrowDown,
    neutral: Minus,
  };

  const Icon = TrendIcon[trend];

  return (
    <div className="rounded-xl border border-black/10 bg-white p-5">
      <p className="text-xs uppercase tracking-[0.18em] text-[color:var(--text-muted)]">
        {label}
      </p>
      <p className="mt-2 text-3xl font-semibold text-[color:var(--text-strong)]">
        {value}
      </p>
      <div className={cn("mt-2 flex items-center gap-1 rounded-full px-2 py-0.5 w-fit", trendColors[trend])}>
        <Icon className="h-3 w-3" />
        <span className="text-xs font-medium">{delta}</span>
      </div>
    </div>
  );
}