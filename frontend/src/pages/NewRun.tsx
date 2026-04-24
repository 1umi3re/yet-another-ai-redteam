import { useQuery, useMutation } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { useMemo, useState } from "react";
import { api } from "../lib/api";
import { Card, CardBody, CardHeader, CardTitle, CardDescription } from "../components/ui/Card";
import { Button } from "../components/ui/Button";
import { Input, Select, Field, Textarea } from "../components/ui/Form";
import { Badge } from "../components/ui/Badge";
import { PlayCircle, Sparkles, Wrench, X } from "lucide-react";
import clsx from "clsx";
import { toast } from "sonner";

type ParamSchema = {
  type: "bool" | "string" | "text" | "string_list" | "enum" | "target_ref";
  required?: boolean;
  default?: any;
  label?: string;
  help?: string;
  placeholder?: string;
  options?: string[];
};
type PluginSchemas = Record<string, Record<string, ParamSchema>>;
type ConfiguredPlugin = { plugin: string; params: Record<string, any> };

function defaultsFor(schema: Record<string, ParamSchema> | undefined): Record<string, any> {
  if (!schema) return {};
  const out: Record<string, any> = {};
  for (const [k, s] of Object.entries(schema)) {
    if (s.default !== undefined) out[k] = s.default;
    else if (s.type === "bool") out[k] = false;
    else if (s.type === "string_list") out[k] = [];
    else out[k] = "";
  }
  return out;
}

function ParamField({
  name, schema, value, onChange, targets,
}: {
  name: string; schema: ParamSchema; value: any;
  onChange: (v: any) => void;
  targets: any[];
}) {
  const label = (schema.label ?? name) + (schema.required ? " *" : "");
  const common = { label, hint: schema.help } as const;
  switch (schema.type) {
    case "bool":
      return (
        <Field {...common}>
          <label className="inline-flex items-center gap-2 text-sm">
            <input type="checkbox" checked={!!value} onChange={e => onChange(e.target.checked)} />
            <span className="text-gray-600">{schema.help ?? "Enabled"}</span>
          </label>
        </Field>
      );
    case "enum":
      return (
        <Field {...common}>
          <Select value={value ?? ""} onChange={e => onChange(e.target.value)}>
            {(schema.options ?? []).map(o => <option key={o} value={o}>{o}</option>)}
          </Select>
        </Field>
      );
    case "target_ref":
      return (
        <Field {...common}>
          <Select value={value ?? ""} onChange={e => onChange(e.target.value)}>
            <option value="">-- pick target --</option>
            {targets.map(t => <option key={t.id} value={t.id}>{t.name}</option>)}
          </Select>
        </Field>
      );
    case "text":
      return (
        <Field {...common}>
          <Textarea rows={4} placeholder={schema.placeholder}
            value={value ?? ""} onChange={e => onChange(e.target.value)} />
        </Field>
      );
    case "string_list":
      return (
        <Field {...common} hint={(schema.help ?? "") + " (one per line)"}>
          <Textarea rows={3} placeholder={schema.placeholder}
            value={Array.isArray(value) ? value.join("\n") : ""}
            onChange={e => onChange(e.target.value.split("\n").map(s => s.trim()).filter(Boolean))} />
        </Field>
      );
    case "string":
    default:
      return (
        <Field {...common}>
          <Input placeholder={schema.placeholder} value={value ?? ""}
            onChange={e => onChange(e.target.value)} />
        </Field>
      );
  }
}

export default function NewRun() {
  const nav = useNavigate();
  const { data: targets } = useQuery({ queryKey: ["targets"], queryFn: async () => (await api.get("/api/targets")).data });
  const { data: datasets } = useQuery({ queryKey: ["datasets"], queryFn: async () => (await api.get("/api/datasets")).data });
  const { data: scenarios } = useQuery({ queryKey: ["scenarios"], queryFn: async () => (await api.get("/api/scenarios")).data });
  const { data: plugins } = useQuery({ queryKey: ["plugins"], queryFn: async () => (await api.get("/api/plugins")).data });

  const convSchemas: PluginSchemas = plugins?.params?.converters ?? {};
  const scorerSchemas: PluginSchemas = plugins?.params?.scorers ?? {};
  const executorSchemas: PluginSchemas = plugins?.params?.executors ?? {};

  const [mode, setMode] = useState<"preset" | "custom">("preset");
  const [name, setName] = useState("My run");
  const [scenarioId, setScenarioId] = useState("");
  const [targetId, setTargetId] = useState("");
  const [datasetId, setDatasetId] = useState("");
  const [executor, setExecutor] = useState<ConfiguredPlugin>({ plugin: "single_turn", params: {} });
  const [scorer, setScorer] = useState<ConfiguredPlugin>({ plugin: "refusal", params: {} });
  const [converters, setConverters] = useState<ConfiguredPlugin[]>([]);
  const [samplingEnabled, setSamplingEnabled] = useState(false);
  const [samplingLimit, setSamplingLimit] = useState<string>("");
  const [samplingShuffle, setSamplingShuffle] = useState(false);
  const [samplingSeed, setSamplingSeed] = useState<string>("");

  const executorSchema = executorSchemas[executor.plugin];
  const scorerSchema = scorerSchemas[scorer.plugin];

  const toggleConverter = (c: string) => {
    setConverters(prev => {
      const existing = prev.findIndex(p => p.plugin === c);
      if (existing >= 0) return prev.filter((_, i) => i !== existing);
      return [...prev, { plugin: c, params: defaultsFor(convSchemas[c]) }];
    });
  };

  const updateConverterParam = (idx: number, key: string, v: any) => {
    setConverters(prev => prev.map((p, i) => i === idx ? { ...p, params: { ...p.params, [key]: v } } : p));
  };

  const setExecutorPlugin = (p: string) => {
    setExecutor({ plugin: p, params: defaultsFor(executorSchemas[p]) });
  };
  const updateExecutorParam = (key: string, v: any) => {
    setExecutor(prev => ({ ...prev, params: { ...prev.params, [key]: v } }));
  };

  const setScorerPlugin = (p: string) => {
    setScorer({ plugin: p, params: defaultsFor(scorerSchemas[p]) });
  };
  const updateScorerParam = (key: string, v: any) => {
    setScorer(prev => ({ ...prev, params: { ...prev.params, [key]: v } }));
  };

  const paramValidation = useMemo(() => {
    const missing: string[] = [];
    if (mode === "custom") {
      for (const [k, s] of Object.entries(executorSchema ?? {})) {
        if (s.required) {
          const v = executor.params[k];
          const empty = v === undefined || v === null || v === "" || (Array.isArray(v) && v.length === 0);
          if (empty) missing.push(`executor.${k}`);
        }
      }
      for (const [k, s] of Object.entries(scorerSchema ?? {})) {
        if (s.required) {
          const v = scorer.params[k];
          const empty = v === undefined || v === null || v === "" || (Array.isArray(v) && v.length === 0);
          if (empty) missing.push(`scorer.${k}`);
        }
      }
      for (const [i, c] of converters.entries()) {
        const cs = convSchemas[c.plugin] ?? {};
        for (const [k, s] of Object.entries(cs)) {
          if (s.required) {
            const v = c.params[k];
            const empty = v === undefined || v === null || v === "" || (Array.isArray(v) && v.length === 0);
            if (empty) missing.push(`converters[${i}].${k}`);
          }
        }
      }
    }
    return missing;
  }, [mode, executor, executorSchema, scorer, scorerSchema, converters, convSchemas]);

  const submit = useMutation({
    mutationFn: async () => {
      const base: any = {
        name,
        targets: [{ config_id: targetId }],
        dataset: { config_id: datasetId },
        executor: { plugin: executor.plugin, params: executor.params },
        scorers: [{ plugin: scorer.plugin, params: scorer.params }],
        converters: converters.map(c => ({ plugin: c.plugin, params: c.params })),
      };
      if (mode === "preset") base.scenario = scenarioId;
      
      // Add sampling if enabled
      if (samplingEnabled) {
        base.sampling = {
          limit: samplingLimit ? parseInt(samplingLimit, 10) : null,
          shuffle: samplingShuffle,
          seed: samplingShuffle && samplingSeed ? parseInt(samplingSeed, 10) : null,
        };
      }
      
      const r = await api.post("/api/runs", { name, runspec: base });
      await api.post(`/api/runs/${r.data.id}/start`);
      nav(`/runs/${r.data.id}`);
    },
    onError: (e: any) => toast.error(e?.response?.data?.detail ?? "Failed to start run"),
  });

  const canSubmit = !!targetId && !!datasetId
    && (mode === "custom" || !!scenarioId)
    && paramValidation.length === 0;

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
          
          <div className="mt-5">
            <div className="flex items-center gap-2 mb-3">
              <input
                type="checkbox"
                id="sampling-toggle"
                checked={samplingEnabled}
                onChange={e => setSamplingEnabled(e.target.checked)}
                className="h-4 w-4 text-brand-600 rounded border-gray-300"
              />
              <label htmlFor="sampling-toggle" className="text-sm font-medium text-gray-700 cursor-pointer">
                Dataset sampling (optional)
              </label>
            </div>
            
            {samplingEnabled && (
              <div className="rounded-lg border border-gray-200 bg-gray-50/50 p-4 space-y-3">
                <Field label="Limit" hint="Maximum number of items to process (blank = no limit)">
                  <Input
                    type="number"
                    min="1"
                    placeholder="e.g., 50"
                    value={samplingLimit}
                    onChange={e => setSamplingLimit(e.target.value)}
                  />
                </Field>
                
                <Field label="Shuffle">
                  <label className="inline-flex items-center gap-2 text-sm">
                    <input
                      type="checkbox"
                      checked={samplingShuffle}
                      onChange={e => setSamplingShuffle(e.target.checked)}
                      className="h-4 w-4 text-brand-600 rounded border-gray-300"
                    />
                    <span className="text-gray-600">Randomize dataset order</span>
                  </label>
                </Field>
                
                {samplingShuffle && (
                  <Field label="Seed" hint="Random seed for deterministic shuffle (optional)">
                    <Input
                      type="number"
                      placeholder="e.g., 42"
                      value={samplingSeed}
                      onChange={e => setSamplingSeed(e.target.value)}
                    />
                  </Field>
                )}
              </div>
            )}
          </div>
        </CardBody>
      </Card>

      {mode === "custom" && (
        <Card>
          <CardHeader>
            <CardTitle>3. Pipeline</CardTitle>
            <CardDescription>Executor orchestrates multi-turn conversations. Converters mutate the prompt. Scorer classifies the response.</CardDescription>
          </CardHeader>
          <CardBody className="space-y-6">
            <div>
              <Field label="Executor">
                <Select value={executor.plugin} onChange={e => setExecutorPlugin(e.target.value)}>
                  {plugins?.executors?.map((ex: string) => <option key={ex} value={ex}>{ex}</option>)}
                </Select>
              </Field>
              {executorSchema && Object.keys(executorSchema).length > 0 && (
                <div className="mt-3 rounded-lg border border-gray-200 bg-gray-50/50 p-4 space-y-3">
                  <div className="text-xs font-medium text-gray-500 uppercase tracking-wide">Executor params</div>
                  {Object.entries(executorSchema).map(([k, s]) => (
                    <ParamField key={k} name={k} schema={s} targets={targets ?? []}
                      value={executor.params[k]} onChange={v => updateExecutorParam(k, v)} />
                  ))}
                </div>
              )}
            </div>

            <div>
              <Field label="Scorer">
                <Select value={scorer.plugin} onChange={e => setScorerPlugin(e.target.value)}>
                  {plugins?.scorers?.map((s: string) => <option key={s} value={s}>{s}</option>)}
                </Select>
              </Field>
              {scorerSchema && Object.keys(scorerSchema).length > 0 && (
                <div className="mt-3 rounded-lg border border-gray-200 bg-gray-50/50 p-4 space-y-3">
                  <div className="text-xs font-medium text-gray-500 uppercase tracking-wide">Scorer params</div>
                  {Object.entries(scorerSchema).map(([k, s]) => (
                    <ParamField key={k} name={k} schema={s} targets={targets ?? []}
                      value={scorer.params[k]} onChange={v => updateScorerParam(k, v)} />
                  ))}
                </div>
              )}
            </div>

            <div>
              <Field label="Converters" hint="Click to toggle. Executed in order.">
                <div className="flex flex-wrap gap-2">
                  {plugins?.converters?.length ? plugins.converters.map((c: string) => {
                    const on = converters.some(p => p.plugin === c);
                    return (
                      <button key={c} type="button" onClick={() => toggleConverter(c)}
                        className={clsx(
                          "px-2.5 py-1 text-xs rounded-full border transition",
                          on ? "bg-brand-600 border-brand-600 text-white" : "bg-white border-gray-200 text-gray-700 hover:border-gray-300",
                        )}
                      >{c}</button>
                    );
                  }) : <Badge>No converters available</Badge>}
                </div>
              </Field>
              {converters.length > 0 && (
                <div className="mt-3 space-y-3">
                  {converters.map((c, i) => {
                    const cs = convSchemas[c.plugin] ?? {};
                    if (Object.keys(cs).length === 0) return null;
                    return (
                      <div key={c.plugin} className="rounded-lg border border-gray-200 bg-gray-50/50 p-4 space-y-3">
                        <div className="flex items-center justify-between">
                          <div className="text-xs font-medium text-gray-500 uppercase tracking-wide">{c.plugin} params</div>
                          <button type="button" onClick={() => toggleConverter(c.plugin)}
                            className="text-gray-400 hover:text-gray-600"><X className="h-4 w-4" /></button>
                        </div>
                        {Object.entries(cs).map(([k, s]) => (
                          <ParamField key={k} name={k} schema={s} targets={targets ?? []}
                            value={c.params[k]} onChange={v => updateConverterParam(i, k, v)} />
                        ))}
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          </CardBody>
        </Card>
      )}

      {paramValidation.length > 0 && (
        <div className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
          Missing required fields: {paramValidation.join(", ")}
        </div>
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
