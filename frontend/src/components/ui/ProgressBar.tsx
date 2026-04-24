import clsx from "clsx";

export function ProgressBar({ done, total, tone = "brand" }: { done: number; total: number; tone?: "brand" | "green" }) {
  const pct = total > 0 ? Math.min(100, Math.round((done / total) * 100)) : 0;
  return (
    <div className="w-full">
      <div className="h-1.5 w-full rounded-full bg-gray-200 overflow-hidden">
        <div
          className={clsx(
            "h-full transition-all",
            tone === "brand" ? "bg-brand-500" : "bg-emerald-500",
          )}
          style={{ width: `${pct}%` }}
        />
      </div>
      <div className="mt-1 text-[11px] text-gray-500 tabular-nums">{done}/{total} · {pct}%</div>
    </div>
  );
}
