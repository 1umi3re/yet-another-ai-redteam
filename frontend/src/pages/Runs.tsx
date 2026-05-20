import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { api } from "../lib/api";
import { Card, CardHeader, CardTitle } from "../components/ui/Card";
import { Button } from "../components/ui/Button";
import { Badge, StatusBadge } from "../components/ui/Badge";
import { ProgressBar } from "../components/ui/ProgressBar";
import { EmptyState } from "../components/ui/EmptyState";
import { ListChecks, PlayCircle, ArrowUpRight, MessageSquare } from "lucide-react";
import { useI18n } from "../lib/i18n";

export default function Runs() {
  const { t } = useI18n();
  const { data, isLoading } = useQuery({
    queryKey: ["runs"],
    queryFn: async () => (await api.get("/api/runs")).data,
    refetchInterval: 2000,
  });
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
        {isLoading ? (
          <div className="p-5 text-sm text-gray-500">{t("Loading…")}</div>
        ) : !data?.length ? (
          <EmptyState
            icon={<ListChecks className="h-10 w-10" />}
            title={t("No runs yet")}
            description={t("Create your first run to attack a configured target.")}
            action={<Link to="/runs/new"><Button icon={<PlayCircle className="h-4 w-4" />}>{t("New run")}</Button></Link>}
          />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 text-gray-600 text-xs uppercase tracking-wider">
                <tr>
                  <th className="text-left px-5 py-2.5">{t("Name")}</th>
                  <th className="text-left px-5 py-2.5">{t("Target")}</th>
                  <th className="text-left px-5 py-2.5">{t("Status")}</th>
                  <th className="text-left px-5 py-2.5 w-64">{t("Progress")}</th>
                  <th className="px-5 py-2.5"></th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {data.map((r: any) => (
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
                    <td className="px-5 py-3"><ProgressBar done={r.progress_done ?? 0} total={r.progress_total ?? 0} /></td>
                    <td className="px-5 py-3 text-right whitespace-nowrap">
                      {r.kind === "manual" && r.status === "running" && (
                        <Link to={`/manual?run=${r.id}`} className="mr-2">
                          <Button variant="secondary" size="sm" icon={<MessageSquare className="h-3.5 w-3.5" />}>{t("Continue")}</Button>
                        </Link>
                      )}
                      <Link to={`/runs/${r.id}`}>
                        <Button variant="ghost" size="sm" icon={<ArrowUpRight className="h-3.5 w-3.5" />}>{t("Open")}</Button>
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
