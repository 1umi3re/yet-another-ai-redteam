import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { api } from "../lib/api";
import { Card, CardHeader, CardTitle } from "../components/ui/Card";
import { Button } from "../components/ui/Button";
import { StatusBadge } from "../components/ui/Badge";
import { ProgressBar } from "../components/ui/ProgressBar";
import { EmptyState } from "../components/ui/EmptyState";
import { ListChecks, PlayCircle, ArrowUpRight } from "lucide-react";

export default function Runs() {
  const { data, isLoading } = useQuery({
    queryKey: ["runs"],
    queryFn: async () => (await api.get("/api/runs")).data,
    refetchInterval: 2000,
  });
  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Runs</h1>
          <p className="text-sm text-gray-500 mt-1">Attack executions against configured targets.</p>
        </div>
        <Link to="/runs/new"><Button icon={<PlayCircle className="h-4 w-4" />}>New run</Button></Link>
      </div>
      <Card>
        <CardHeader><CardTitle>All runs</CardTitle></CardHeader>
        {isLoading ? (
          <div className="p-5 text-sm text-gray-500">Loading…</div>
        ) : !data?.length ? (
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
                {data.map((r: any) => (
                  <tr key={r.id} className="hover:bg-gray-50/70">
                    <td className="px-5 py-3 font-medium">{r.name}</td>
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
