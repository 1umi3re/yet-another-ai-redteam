import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { api } from "../lib/api";
import { Card, CardBody, CardHeader, CardTitle } from "../components/ui/Card";
import { Button } from "../components/ui/Button";
import { Badge, StatusBadge } from "../components/ui/Badge";
import { ProgressBar } from "../components/ui/ProgressBar";
import { EmptyState } from "../components/ui/EmptyState";
import { Target, Database, ListChecks, CheckCircle2, PlayCircle, ArrowUpRight } from "lucide-react";
import clsx from "clsx";

export default function Dashboard() {
  const { data: targets } = useQuery({ queryKey: ["targets"], queryFn: async () => (await api.get("/api/targets")).data });
  const { data: datasets } = useQuery({ queryKey: ["datasets"], queryFn: async () => (await api.get("/api/datasets")).data });
  const { data: runs } = useQuery({
    queryKey: ["runs"],
    queryFn: async () => (await api.get("/api/runs")).data,
    refetchInterval: 3000,
  });

  const runsArr: any[] = runs ?? [];
  const completed = runsArr.filter(r => r.status === "completed").length;
  const running = runsArr.filter(r => r.status === "running").length;
  const recent = runsArr.slice(0, 5);

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Dashboard</h1>
          <p className="text-sm text-gray-500 mt-1">Overview of your red-team workspace.</p>
        </div>
        <Link to="/runs/new"><Button icon={<PlayCircle className="h-4 w-4" />}>New run</Button></Link>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Stat icon={<Target className="h-4 w-4" />} label="Targets" value={targets?.length ?? 0} to="/targets" tone="brand" />
        <Stat icon={<Database className="h-4 w-4" />} label="Datasets" value={datasets?.length ?? 0} to="/datasets" tone="brand" />
        <Stat icon={<ListChecks className="h-4 w-4" />} label="Total runs" value={runsArr.length} to="/runs" tone="brand" />
        <Stat icon={<CheckCircle2 className="h-4 w-4" />} label="Completed" value={completed} sub={running ? `${running} running` : undefined} to="/runs" tone="green" />
      </div>

      <Card>
        <CardHeader className="flex items-center justify-between flex-row">
          <CardTitle>Recent runs</CardTitle>
          <Link to="/runs" className="text-xs text-brand-700 hover:text-brand-800 font-medium">View all →</Link>
        </CardHeader>
        {!recent.length ? (
          <EmptyState
            icon={<ListChecks className="h-10 w-10" />}
            title="No runs yet"
            description="Create your first run to attack a configured target."
            action={<Link to="/runs/new"><Button icon={<PlayCircle className="h-4 w-4" />}>New run</Button></Link>}
          />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 text-gray-600 text-xs uppercase tracking-wider">
                <tr>
                  <th className="text-left px-5 py-2.5">Name</th>
                  <th className="text-left px-5 py-2.5">Status</th>
                  <th className="text-left px-5 py-2.5 w-64">Progress</th>
                  <th className="px-5 py-2.5"></th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {recent.map(r => (
                  <tr key={r.id} className="hover:bg-gray-50/70">
                    <td className="px-5 py-3 font-medium">
                      <div className="flex items-center gap-2">
                        <span>{r.name}</span>
                        {r.kind === "manual" && <Badge tone="blue">Manual</Badge>}
                      </div>
                    </td>
                    <td className="px-5 py-3"><StatusBadge status={r.status} /></td>
                    <td className="px-5 py-3"><ProgressBar done={r.progress_done ?? 0} total={r.progress_total ?? 0} /></td>
                    <td className="px-5 py-3 text-right">
                      <Link to={`/runs/${r.id}`}>
                        <Button variant="ghost" size="sm" icon={<ArrowUpRight className="h-3.5 w-3.5" />}>Open</Button>
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

function Stat({ icon, label, value, sub, to, tone }: {
  icon: React.ReactNode; label: string; value: number | string; sub?: string; to: string; tone: "brand" | "green";
}) {
  const color = tone === "green" ? "bg-emerald-50 text-emerald-600" : "bg-brand-50 text-brand-600";
  return (
    <Link to={to}>
      <Card className="hover:shadow-card transition">
        <CardBody>
          <div className="flex items-center justify-between">
            <div className={clsx("h-8 w-8 rounded-lg flex items-center justify-center", color)}>{icon}</div>
          </div>
          <div className="mt-3 text-xs text-gray-500">{label}</div>
          <div className="mt-1 text-2xl font-bold tabular-nums">{value}</div>
          {sub && <div className="text-xs text-gray-500 mt-0.5">{sub}</div>}
        </CardBody>
      </Card>
    </Link>
  );
}
