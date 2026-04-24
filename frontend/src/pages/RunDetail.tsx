import { useQuery } from "@tanstack/react-query";
import { Link, useParams } from "react-router-dom";
import { useEffect, useMemo, useState } from "react";
import { api } from "../lib/api";
import { useAuth } from "../lib/auth";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Legend } from "recharts";
import { Card, CardBody, CardHeader, CardTitle, CardDescription } from "../components/ui/Card";
import { Badge, StatusBadge } from "../components/ui/Badge";
import { ProgressBar } from "../components/ui/ProgressBar";
import { Button } from "../components/ui/Button";
import { ArrowLeft } from "lucide-react";
import clsx from "clsx";

type Tab = "overview" | "attempts" | "events";

export default function RunDetail() {
  const { id = "" } = useParams();
  const token = useAuth(s => s.token);
  const [events, setEvents] = useState<any[]>([]);
  const [tab, setTab] = useState<Tab>("overview");

  const { data: run } = useQuery({
    queryKey: ["run", id],
    queryFn: async () => (await api.get(`/api/runs/${id}`)).data,
    refetchInterval: 2000,
  });
  const { data: attempts = [] } = useQuery({
    queryKey: ["run-attempts", id],
    queryFn: async () => (await api.get(`/api/runs/${id}/attempts`)).data,
    refetchInterval: 2000,
  });
  const { data: scores = [] } = useQuery({
    queryKey: ["run-scores", id],
    queryFn: async () => (await api.get(`/api/runs/${id}/scores`)).data,
    refetchInterval: 2000,
  });

  useEffect(() => {
    if (!id || !token) return;
    const url = `${api.defaults.baseURL}/api/runs/${id}/events?token=${encodeURIComponent(token)}`;
    const es = new EventSource(url);
    es.onmessage = (e) => setEvents(prev => [...prev.slice(-199), JSON.parse(e.data)]);
    es.onerror = () => es.close();
    return () => es.close();
  }, [id, token]);

  const chartData = useMemo(() => {
    const byTarget: Record<string, { target: string; refused: number; complied: number }> = {};
    for (const a of attempts as any[]) {
      byTarget[a.target_name] ||= { target: a.target_name, refused: 0, complied: 0 };
      const sc = (scores as any[]).find((s: any) => s.attempt_id === a.id);
      if (sc?.value?.label === true) byTarget[a.target_name].refused++;
      else if (sc) byTarget[a.target_name].complied++;
    }
    return Object.values(byTarget);
  }, [attempts, scores]);

  const totals = useMemo(() => {
    let refused = 0, complied = 0;
    for (const s of scores as any[]) {
      if (s?.value?.label === true) refused++; else complied++;
    }
    return { refused, complied, total: refused + complied };
  }, [scores]);

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <Link to="/runs" className="inline-flex items-center gap-1 text-xs text-gray-500 hover:text-gray-700 mb-2">
            <ArrowLeft className="h-3 w-3" /> Back to runs
          </Link>
          <h1 className="text-2xl font-bold tracking-tight">{run?.name ?? "Run"}</h1>
          <div className="flex items-center gap-3 mt-2">
            {run && <StatusBadge status={run.status} />}
            <span className="text-xs text-gray-500 font-mono">{id.slice(0, 8)}</span>
          </div>
          {run?.error && <div className="mt-2 text-xs text-red-600">{run.error}</div>}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard label="Refusal rate" value={totals.total ? `${Math.round((totals.refused/totals.total)*100)}%` : "—"} tone="green" />
        <StatCard label="Refused" value={totals.refused} tone="green" />
        <StatCard label="Complied" value={totals.complied} tone="red" />
        <Card><CardBody>
          <div className="text-xs text-gray-500 mb-1">Progress</div>
          <ProgressBar done={run?.progress_done ?? 0} total={run?.progress_total ?? 0} />
        </CardBody></Card>
      </div>

      <div className="flex gap-1 border-b border-gray-200">
        {(["overview", "attempts", "events"] as Tab[]).map(t => (
          <button key={t} onClick={() => setTab(t)}
            className={clsx(
              "px-4 py-2 text-sm font-medium border-b-2 -mb-px transition",
              tab === t ? "border-brand-600 text-brand-700" : "border-transparent text-gray-500 hover:text-gray-700",
            )}>
            {t === "overview" ? "Overview" : t === "attempts" ? `Attempts (${(attempts as any[]).length})` : "Live events"}
          </button>
        ))}
      </div>

      {tab === "overview" && (
        <Card>
          <CardHeader>
            <CardTitle>Refused vs Complied by target</CardTitle>
            <CardDescription>Green = model refused. Red = model complied with the attack prompt.</CardDescription>
          </CardHeader>
          <CardBody>
            {chartData.length ? (
              <div style={{ height: 280 }}>
                <ResponsiveContainer>
                  <BarChart data={chartData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#eee" />
                    <XAxis dataKey="target" tick={{ fontSize: 12 }} />
                    <YAxis allowDecimals={false} tick={{ fontSize: 12 }} />
                    <Tooltip contentStyle={{ fontSize: 12, borderRadius: 8 }} />
                    <Legend wrapperStyle={{ fontSize: 12 }} />
                    <Bar dataKey="refused" stackId="a" fill="#10b981" name="Refused" radius={[4, 4, 0, 0]} />
                    <Bar dataKey="complied" stackId="a" fill="#ef4444" name="Complied" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            ) : <div className="text-sm text-gray-500 py-8 text-center">No scored attempts yet.</div>}
          </CardBody>
        </Card>
      )}

      {tab === "attempts" && (
        <Card>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 text-gray-600 text-xs uppercase tracking-wider">
                <tr>
                  <th className="text-left px-5 py-2.5">Target</th>
                  <th className="text-left px-5 py-2.5">Prompt</th>
                  <th className="text-left px-5 py-2.5">Response</th>
                  <th className="text-left px-5 py-2.5">Score</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {(attempts as any[]).map(a => {
                  const sc = (scores as any[]).find((s: any) => s.attempt_id === a.id);
                  const refused = sc?.value?.label === true;
                  return (
                    <tr key={a.id} className="align-top">
                      <td className="px-5 py-3 font-medium whitespace-nowrap">{a.target_name}</td>
                      <td className="px-5 py-3 max-w-xs"><div className="truncate text-gray-700" title={a.prompt}>{a.prompt}</div></td>
                      <td className="px-5 py-3 max-w-md"><div className="truncate text-gray-600" title={a.response ?? ""}>{a.response ?? <span className="text-gray-400">(blob)</span>}</div></td>
                      <td className="px-5 py-3">
                        {sc ? (refused ? <Badge tone="green">refused</Badge> : <Badge tone="red">complied</Badge>) : <Badge>-</Badge>}
                      </td>
                    </tr>
                  );
                })}
                {!(attempts as any[]).length && (
                  <tr><td colSpan={4} className="px-5 py-10 text-center text-sm text-gray-500">No attempts yet.</td></tr>
                )}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      {tab === "events" && (
        <Card>
          <CardHeader>
            <CardTitle>Live events</CardTitle>
            <CardDescription>Streamed via Server-Sent Events. Last 200 messages.</CardDescription>
          </CardHeader>
          <CardBody>
            <pre className="text-xs bg-gray-900 text-gray-100 rounded-lg p-3 max-h-80 overflow-auto font-mono">
{events.length ? events.map(e => JSON.stringify(e)).join("\n") : "(waiting for events…)"}
            </pre>
          </CardBody>
        </Card>
      )}
    </div>
  );
}

function StatCard({ label, value, tone }: { label: string; value: string | number; tone?: "green" | "red" | "brand" }) {
  const color = tone === "green" ? "text-emerald-600" : tone === "red" ? "text-red-600" : "text-brand-600";
  return (
    <Card>
      <CardBody>
        <div className="text-xs text-gray-500">{label}</div>
        <div className={clsx("mt-1 text-2xl font-bold tabular-nums", color)}>{value}</div>
      </CardBody>
    </Card>
  );
}
