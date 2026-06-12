import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { useMemo, useState } from "react";
import { api } from "../lib/api";
import { Card, CardHeader, CardTitle } from "../components/ui/Card";
import { Button } from "../components/ui/Button";
import { Field, Input, Select } from "../components/ui/Form";
import { Badge, StatusBadge } from "../components/ui/Badge";
import { ProgressBar } from "../components/ui/ProgressBar";
import { EmptyState } from "../components/ui/EmptyState";
import { ListChecks, PlayCircle, ArrowUpRight, MessageSquare } from "lucide-react";
import { useI18n } from "../lib/i18n";

function formatDateTime(value?: string | null): string {
  if (!value) return "-";
  return new Date(value).toLocaleString();
}

function formatDuration(value?: number | null): string {
  if (typeof value !== "number") return "-";
  if (value < 1000) return `${value} ms`;
  const seconds = value / 1000;
  if (seconds < 60) return `${seconds.toFixed(seconds < 10 ? 1 : 0)} s`;
  const minutes = Math.floor(seconds / 60);
  const remainder = Math.round(seconds % 60);
  return `${minutes}m ${remainder}s`;
}

export default function Runs() {
  const { t } = useI18n();
  const [targetFilter, setTargetFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [kindFilter, setKindFilter] = useState("");
  const [runSearch, setRunSearch] = useState("");
  const { data, isLoading } = useQuery({
    queryKey: ["runs", targetFilter],
    queryFn: async () => (await api.get("/api/runs", {
      params: { target_id: targetFilter || undefined },
    })).data,
    refetchInterval: 2000,
  });
  const { data: targets = [] } = useQuery({
    queryKey: ["targets"],
    queryFn: async () => (await api.get("/api/targets")).data,
  });
  const filteredRuns = useMemo(() => {
    const q = runSearch.trim().toLowerCase();
    return (data ?? []).filter((run: any) => {
      if (statusFilter && run.status !== statusFilter) return false;
      if (kindFilter && run.kind !== kindFilter) return false;
      if (!q) return true;
      return run.name.toLowerCase().includes(q)
        || (run.target_names ?? []).join(", ").toLowerCase().includes(q);
    });
  }, [data, kindFilter, runSearch, statusFilter]);
  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">{t("Runs")}</h1>
          <p className="text-sm text-gray-500 mt-1">{t("Attack executions against configured targets.")}</p>
        </div>
        <Link to="/runs/new"><Button icon={<PlayCircle className="h-4 w-4" />}>{t("New run")}</Button></Link>
      </div>
      <Card>
        <CardHeader><CardTitle>{t("All runs")}</CardTitle></CardHeader>
        <div className="border-t border-gray-100 px-5 py-3">
          <div className="grid gap-3 md:grid-cols-[minmax(0,1fr)_220px_180px_180px]">
            <Field label={t("Search runs")}>
              <Input
                value={runSearch}
                onChange={e => setRunSearch(e.target.value)}
                placeholder={t("Search by run or target")}
              />
            </Field>
            <Field label={t("Target")}>
              <Select value={targetFilter} onChange={e => setTargetFilter(e.target.value)}>
                <option value="">{t("All targets")}</option>
                {targets.map((target: any) => (
                  <option key={target.id} value={target.id}>{target.name}</option>
                ))}
              </Select>
            </Field>
            <Field label={t("Status")}>
              <Select value={statusFilter} onChange={e => setStatusFilter(e.target.value)}>
                <option value="">{t("All statuses")}</option>
                <option value="running">{t("Running")}</option>
                <option value="completed">{t("Completed")}</option>
                <option value="failed">{t("Failed")}</option>
                <option value="cancelled">{t("Cancelled")}</option>
              </Select>
            </Field>
            <Field label={t("Kind")}>
              <Select value={kindFilter} onChange={e => setKindFilter(e.target.value)}>
                <option value="">{t("All kinds")}</option>
                <option value="automated">{t("Automated")}</option>
                <option value="manual">{t("Manual")}</option>
              </Select>
            </Field>
          </div>
          <div className="mt-2 text-xs text-gray-500">{t("Auto-refreshing every 2s")}</div>
        </div>
        {isLoading ? (
          <div className="p-5 text-sm text-gray-500">{t("Loading…")}</div>
        ) : !data?.length ? (
          <EmptyState
            icon={<ListChecks className="h-10 w-10" />}
            title={t("No runs yet")}
            description={t("Create your first run to attack a configured target.")}
            action={<Link to="/runs/new"><Button icon={<PlayCircle className="h-4 w-4" />}>{t("New run")}</Button></Link>}
          />
        ) : !filteredRuns.length ? (
          <div className="p-8 text-center text-sm text-gray-500">{t("No runs match these filters.")}</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 text-gray-600 text-xs uppercase tracking-wider">
                <tr>
                  <th className="text-left px-5 py-2.5">{t("Name")}</th>
                  <th className="text-left px-5 py-2.5">{t("Target")}</th>
                  <th className="text-left px-5 py-2.5">{t("Status")}</th>
                  <th className="text-left px-5 py-2.5">{t("Started")}</th>
                  <th className="text-left px-5 py-2.5">{t("Duration")}</th>
                  <th className="text-left px-5 py-2.5 w-64">{t("Progress")}</th>
                  <th className="px-5 py-2.5"></th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {filteredRuns.map((r: any) => (
                  <tr key={r.id} className="hover:bg-gray-50/70">
                    <td className="px-5 py-3 font-medium">
                      <div className="flex items-center gap-2">
                        <span>{r.name}</span>
                        {r.kind === "manual" && <Badge tone="blue">{t("Manual")}</Badge>}
                      </div>
                    </td>
                    <td className="px-5 py-3 text-gray-700">
                      {(r.target_names ?? []).length ? r.target_names.join(", ") : <span className="text-gray-400">-</span>}
                    </td>
                    <td className="px-5 py-3"><StatusBadge status={r.status} /></td>
                    <td className="px-5 py-3 text-gray-600 whitespace-nowrap">{formatDateTime(r.started_at)}</td>
                    <td className="px-5 py-3 text-gray-600 whitespace-nowrap">{formatDuration(r.duration_ms)}</td>
                    <td className="px-5 py-3"><ProgressBar done={r.progress_done ?? 0} total={r.progress_total ?? 0} /></td>
                    <td className="px-5 py-3 text-right whitespace-nowrap">
                      {r.kind === "manual" && r.status === "running" && (
                        <Link to={`/manual?run=${r.id}`} className="mr-2">
                          <Button
                            variant="secondary"
                            size="sm"
                            aria-label={t("Continue manual run {{name}}", { name: r.name })}
                            icon={<MessageSquare className="h-3.5 w-3.5" />}
                          >
                            {t("Continue")}
                          </Button>
                        </Link>
                      )}
                      <Link to={`/runs/${r.id}`}>
                        <Button
                          variant="ghost"
                          size="sm"
                          aria-label={t("Open run {{name}}", { name: r.name })}
                          icon={<ArrowUpRight className="h-3.5 w-3.5" />}
                        >
                          {t("Open")}
                        </Button>
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  );
}
