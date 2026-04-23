import { useQuery, useMutation } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { useState } from "react";
import { api } from "../lib/api";

export default function NewRun() {
  const nav = useNavigate();
  const { data: targets } = useQuery({ queryKey: ["targets"], queryFn: async () => (await api.get("/api/targets")).data });
  const { data: datasets } = useQuery({ queryKey: ["datasets"], queryFn: async () => (await api.get("/api/datasets")).data });
  const { data: scenarios } = useQuery({ queryKey: ["scenarios"], queryFn: async () => (await api.get("/api/scenarios")).data });
  const { data: plugins } = useQuery({ queryKey: ["plugins"], queryFn: async () => (await api.get("/api/plugins")).data });

  const [mode, setMode] = useState<"preset" | "custom">("preset");
  const [name, setName] = useState("My run");
  const [scenarioId, setScenarioId] = useState("");
  const [targetId, setTargetId] = useState("");
  const [datasetId, setDatasetId] = useState("");
  const [scorer, setScorer] = useState("refusal");
  const [converters, setConverters] = useState<string[]>([]);

  const submit = useMutation({
    mutationFn: async () => {
      const runspec =
        mode === "preset"
          ? { name, scenario: scenarioId, targets: [{ config_id: targetId }],
              dataset: { config_id: datasetId },
              executor: { plugin: "single_turn" }, scorers: [{ plugin: scorer }], converters: converters.map(c => ({ plugin: c })) }
          : { name, targets: [{ config_id: targetId }],
              dataset: { config_id: datasetId },
              executor: { plugin: "single_turn" },
              scorers: [{ plugin: scorer }],
              converters: converters.map(c => ({ plugin: c })) };
      const r = await api.post("/api/runs", { name, runspec });
      await api.post(`/api/runs/${r.data.id}/start`);
      nav(`/runs/${r.data.id}`);
    },
  });

  return (
    <div className="max-w-2xl space-y-4">
      <h1 className="text-xl font-bold">New run</h1>
      <input className="w-full border rounded px-2 py-1" value={name} onChange={e => setName(e.target.value)} />
      <div className="flex gap-2">
        <button className={`px-3 py-1 border rounded ${mode==="preset"?"bg-black text-white":""}`} onClick={() => setMode("preset")}>Preset scenario</button>
        <button className={`px-3 py-1 border rounded ${mode==="custom"?"bg-black text-white":""}`} onClick={() => setMode("custom")}>Custom</button>
      </div>
      {mode === "preset" && (
        <select className="border rounded px-2 py-1 w-full" value={scenarioId} onChange={e => setScenarioId(e.target.value)}>
          <option value="">-- pick scenario --</option>
          {scenarios?.map((s: any) => <option key={s.id} value={s.id}>{s.title}</option>)}
        </select>
      )}
      <div>
        <label className="block text-sm">Target</label>
        <select className="border rounded px-2 py-1 w-full" value={targetId} onChange={e => setTargetId(e.target.value)}>
          <option value="">-- pick target --</option>
          {targets?.map((t: any) => <option key={t.id} value={t.id}>{t.name}</option>)}
        </select>
      </div>
      <div>
        <label className="block text-sm">Dataset</label>
        <select className="border rounded px-2 py-1 w-full" value={datasetId} onChange={e => setDatasetId(e.target.value)}>
          <option value="">-- pick dataset --</option>
          {datasets?.map((d: any) => <option key={d.id} value={d.id}>{d.name}</option>)}
        </select>
      </div>
      <div>
        <label className="block text-sm">Scorer</label>
        <select className="border rounded px-2 py-1 w-full" value={scorer} onChange={e => setScorer(e.target.value)}>
          {plugins?.scorers?.map((s: string) => <option key={s} value={s}>{s}</option>)}
        </select>
      </div>
      <div>
        <label className="block text-sm">Converters (multi-select)</label>
        <select multiple className="border rounded px-2 py-1 w-full h-32" value={converters} onChange={e => setConverters(Array.from(e.target.selectedOptions).map(o => o.value))}>
          {plugins?.converters?.map((c: string) => <option key={c} value={c}>{c}</option>)}
        </select>
      </div>
      <button className="px-3 py-1 bg-black text-white rounded" disabled={!targetId || !datasetId} onClick={() => submit.mutate()}>Create + Start</button>
    </div>
  );
}
