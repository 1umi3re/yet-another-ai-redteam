import { useQuery, useMutation } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { useState } from "react";
import { api } from "../lib/api";
import { Card, CardBody, CardHeader, CardTitle, CardDescription } from "../components/ui/Card";
import { Button } from "../components/ui/Button";
import { Input, Select, Field } from "../components/ui/Form";
import { Badge } from "../components/ui/Badge";
import { PlayCircle, Sparkles, Wrench } from "lucide-react";
import clsx from "clsx";
import { toast } from "sonner";

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
              executor: { plugin: "single_turn" }, scorers: [{ plugin: scorer }],
              converters: converters.map(c => ({ plugin: c })) }
          : { name, targets: [{ config_id: targetId }],
              dataset: { config_id: datasetId },
              executor: { plugin: "single_turn" },
              scorers: [{ plugin: scorer }],
              converters: converters.map(c => ({ plugin: c })) };
      const r = await api.post("/api/runs", { name, runspec });
      await api.post(`/api/runs/${r.data.id}/start`);
      nav(`/runs/${r.data.id}`);
    },
    onError: (e: any) => toast.error(e?.response?.data?.detail ?? "Failed to start run"),
  });

  const canSubmit = !!targetId && !!datasetId && (mode === "custom" || !!scenarioId);

  return (
    <div className="max-w-3xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">New run</h1>
        <p className="text-sm text-gray-500 mt-1">Pick a preset scenario or assemble your own pipeline.</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>1. Basics</CardTitle>
        </CardHeader>
        <CardBody>
          <Field label="Run name"><Input value={name} onChange={e => setName(e.target.value)} /></Field>
          <div className="mt-5">
            <div className="label">Mode</div>
            <div className="grid grid-cols-2 gap-3">
              {([
                { id: "preset", title: "Preset scenario", desc: "Curated pipelines (OWASP, jailbreak, …)", icon: Sparkles },
                { id: "custom", title: "Custom pipeline", desc: "Choose your own executor, converters, scorer", icon: Wrench },
              ] as const).map(opt => {
                const Icon = opt.icon;
                const active = mode === opt.id;
                return (
                  <button key={opt.id} type="button" onClick={() => setMode(opt.id)}
                    className={clsx(
                      "text-left rounded-xl border px-4 py-3 transition",
                      active ? "border-brand-500 ring-2 ring-brand-200 bg-brand-50/50" : "border-gray-200 hover:border-gray-300",
                    )}>
                    <div className="flex items-center gap-2">
                      <Icon className={clsx("h-4 w-4", active ? "text-brand-600" : "text-gray-500")} />
                      <span className="font-medium text-sm">{opt.title}</span>
                    </div>
                    <p className="text-xs text-gray-500 mt-1">{opt.desc}</p>
                  </button>
                );
              })}
            </div>
          </div>
        </CardBody>
      </Card>

      {mode === "preset" && (
        <Card>
          <CardHeader>
            <CardTitle>2. Scenario</CardTitle>
            <CardDescription>A pre-configured combination of executor, converters, and scorer.</CardDescription>
          </CardHeader>
          <CardBody>
            <Field label="Scenario">
              <Select value={scenarioId} onChange={e => setScenarioId(e.target.value)}>
                <option value="">-- pick scenario --</option>
                {scenarios?.map((s: any) => <option key={s.id} value={s.id}>{s.title}</option>)}
              </Select>
            </Field>
          </CardBody>
        </Card>
      )}

      <Card>
        <CardHeader><CardTitle>{mode === "preset" ? "3" : "2"}. Target &amp; dataset</CardTitle></CardHeader>
        <CardBody>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Field label="Target">
              <Select value={targetId} onChange={e => setTargetId(e.target.value)}>
                <option value="">-- pick target --</option>
                {targets?.map((t: any) => <option key={t.id} value={t.id}>{t.name}</option>)}
              </Select>
            </Field>
            <Field label="Dataset">
              <Select value={datasetId} onChange={e => setDatasetId(e.target.value)}>
                <option value="">-- pick dataset --</option>
                {datasets?.map((d: any) => <option key={d.id} value={d.id}>{d.name}</option>)}
              </Select>
            </Field>
          </div>
        </CardBody>
      </Card>

      {mode === "custom" && (
        <Card>
          <CardHeader>
            <CardTitle>3. Pipeline</CardTitle>
            <CardDescription>Converters mutate the prompt before it hits the target. Scorer classifies the response.</CardDescription>
          </CardHeader>
          <CardBody>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Field label="Scorer">
                <Select value={scorer} onChange={e => setScorer(e.target.value)}>
                  {plugins?.scorers?.map((s: string) => <option key={s} value={s}>{s}</option>)}
                </Select>
              </Field>
              <Field label="Converters" hint="Click to toggle. Executed in order.">
                <div className="flex flex-wrap gap-2">
                  {plugins?.converters?.length ? plugins.converters.map((c: string) => {
                    const on = converters.includes(c);
                    return (
                      <button key={c} type="button"
                        onClick={() => setConverters(on ? converters.filter(x => x !== c) : [...converters, c])}
                        className={clsx(
                          "px-2.5 py-1 text-xs rounded-full border transition",
                          on ? "bg-brand-600 border-brand-600 text-white" : "bg-white border-gray-200 text-gray-700 hover:border-gray-300",
                        )}
                      >{c}</button>
                    );
                  }) : <Badge>No converters available</Badge>}
                </div>
              </Field>
            </div>
          </CardBody>
        </Card>
      )}

      <div className="flex justify-end">
        <Button icon={<PlayCircle className="h-4 w-4" />} loading={submit.isPending}
          disabled={!canSubmit} onClick={() => submit.mutate()}>
          Create &amp; start
        </Button>
      </div>
    </div>
  );
}
