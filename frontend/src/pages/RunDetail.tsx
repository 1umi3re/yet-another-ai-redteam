import { useQuery } from "@tanstack/react-query";
import { useParams } from "react-router-dom";
import { useEffect, useState } from "react";
import { api } from "../lib/api";
import { useAuth } from "../lib/auth";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";

export default function RunDetail() {
  const { id = "" } = useParams();
  const token = useAuth(s => s.token);
  const [events, setEvents] = useState<any[]>([]);

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
    es.onmessage = (e) => setEvents(prev => [...prev.slice(-99), JSON.parse(e.data)]);
    es.onerror = () => es.close();
    return () => es.close();
  }, [id, token]);

  const byTarget: Record<string, { target: string; refused: number; complied: number }> = {};
  for (const a of attempts as any[]) {
    byTarget[a.target_name] ||= { target: a.target_name, refused: 0, complied: 0 };
    const sc = (scores as any[]).find((s: any) => s.attempt_id === a.id);
    if (sc?.value?.label === true) byTarget[a.target_name].refused++;
    else if (sc) byTarget[a.target_name].complied++;
  }
  const chartData = Object.values(byTarget);

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-xl font-bold">{run?.name}</h1>
        <div>Status: <span className="font-mono">{run?.status}</span> — {run?.progress_done}/{run?.progress_total}</div>
        {run?.error && <div className="text-red-600">{run.error}</div>}
      </header>
      <section>
        <h2 className="font-semibold mb-2">Refused vs Complied</h2>
        <div style={{ height: 240 }}>
          <ResponsiveContainer><BarChart data={chartData}>
            <XAxis dataKey="target" /><YAxis allowDecimals={false} /><Tooltip />
            <Bar dataKey="refused" stackId="a" fill="#10b981" />
            <Bar dataKey="complied" stackId="a" fill="#ef4444" />
          </BarChart></ResponsiveContainer>
        </div>
      </section>
      <section>
        <h2 className="font-semibold mb-2">Attempts</h2>
        <table className="w-full text-sm">
          <thead><tr className="text-left border-b"><th>Target</th><th>Prompt</th><th>Response</th><th>Score</th></tr></thead>
          <tbody>{(attempts as any[]).map((a: any) => {
            const sc = (scores as any[]).find((s: any) => s.attempt_id === a.id);
            return (
              <tr key={a.id} className="border-b align-top">
                <td>{a.target_name}</td>
                <td className="max-w-xs truncate">{a.prompt}</td>
                <td className="max-w-md truncate">{a.response ?? "(blob)"}</td>
                <td>{sc ? JSON.stringify(sc.value) : "-"}</td>
              </tr>
            );
          })}</tbody>
        </table>
      </section>
      <section>
        <h2 className="font-semibold mb-2">Live events</h2>
        <pre className="text-xs bg-gray-50 p-2 max-h-48 overflow-auto">{events.map(e => JSON.stringify(e)).join("\n")}</pre>
      </section>
    </div>
  );
}
