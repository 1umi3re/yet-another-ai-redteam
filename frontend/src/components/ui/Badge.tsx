import clsx from "clsx";
import { ReactNode } from "react";
import { useI18n } from "../../lib/i18n";

type Tone = "gray" | "green" | "red" | "amber" | "blue" | "indigo";

const tones: Record<Tone, string> = {
  gray: "bg-gray-100 text-gray-700 ring-1 ring-inset ring-gray-200",
  green: "bg-emerald-50 text-emerald-700 ring-1 ring-inset ring-emerald-200",
  red: "bg-red-50 text-red-700 ring-1 ring-inset ring-red-200",
  amber: "bg-amber-50 text-amber-800 ring-1 ring-inset ring-amber-200",
  blue: "bg-sky-50 text-sky-700 ring-1 ring-inset ring-sky-200",
  indigo: "bg-brand-50 text-brand-700 ring-1 ring-inset ring-brand-200",
};

export function Badge({ tone = "gray", children, className }: { tone?: Tone; children: ReactNode; className?: string }) {
  return <span className={clsx("badge", tones[tone], className)}>{children}</span>;
}

export function StatusBadge({ status }: { status: string }) {
  const { t } = useI18n();
  const map: Record<string, { tone: Tone; label: string }> = {
    pending:   { tone: "gray",   label: "Pending" },
    running:   { tone: "blue",   label: "Running" },
    pausing:   { tone: "blue",   label: "Pausing" },
    paused:    { tone: "amber",  label: "Paused" },
    completed: { tone: "green",  label: "Completed" },
    failed:    { tone: "red",    label: "Failed" },
    cancelled: { tone: "amber",  label: "Cancelled" },
  };
  const m = map[status] ?? { tone: "gray" as Tone, label: status };
  return (
    <Badge tone={m.tone}>
      <span className={clsx("h-1.5 w-1.5 rounded-full",
        m.tone === "blue" && "bg-sky-500 animate-pulse",
        m.tone === "green" && "bg-emerald-500",
        m.tone === "red" && "bg-red-500",
        m.tone === "amber" && "bg-amber-500",
        m.tone === "gray" && "bg-gray-400",
      )} />
      {t(m.label)}
    </Badge>
  );
}
