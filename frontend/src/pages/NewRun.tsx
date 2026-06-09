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
import { ConfiguredPlugin, defaultsFor, ParamField, PluginSchemas } from "../components/PluginParamsForm";
import { useI18n } from "../lib/i18n";
import {
  applyConverterLlmConfig,
  countConvertersWithLlmConfig,
} from "../lib/converterLlmParams";

const CONVERTER_CATEGORY_ORDER = [
  "encoding",
  "obfuscation",
  "prompt_framing",
  "llm_rewrite",
  "perturbation",
  "multimodal",
  "utility",
  "other",
] as const;

const CONVERTER_CATEGORY_LABELS: Record<string, string> = {
  encoding: "Encoding",
  obfuscation: "Obfuscation",
  prompt_framing: "Prompt framing",
  llm_rewrite: "LLM rewrite",
  perturbation: "Perturbation",
  multimodal: "Multimodal",
  utility: "Utility",
  other: "Other",
};

type ConfiguredExecutor = ConfiguredPlugin & { kind: "executor" | "converter_method" };

export default function NewRun() {
  const { t } = useI18n();
  const nav = useNavigate();
  const { data: targets } = useQuery({ queryKey: ["targets"], queryFn: async () => (await api.get("/api/targets")).data });
  const { data: datasets } = useQuery({ queryKey: ["datasets"], queryFn: async () => (await api.get("/api/datasets")).data });
  const { data: scenarios } = useQuery({ queryKey: ["scenarios"], queryFn: async () => (await api.get("/api/scenarios")).data });
  const { data: plugins } = useQuery({ queryKey: ["plugins"], queryFn: async () => (await api.get("/api/plugins")).data });
  const { data: promptAssets } = useQuery({ queryKey: ["prompt-assets"], queryFn: async () => (await api.get("/api/prompt-assets")).data });

  const convSchemas: PluginSchemas = plugins?.params?.executor_methods ?? plugins?.params?.converters ?? {};
  const scorerSchemas: PluginSchemas = plugins?.params?.scorers ?? {};
  const executorSchemas: PluginSchemas = plugins?.params?.executors ?? {};
  const availableConverters: string[] = plugins?.executor_methods ?? plugins?.converters ?? [];
  const converterCategories: Record<string, string> = plugins?.executor_method_categories ?? plugins?.converter_categories ?? {};
  const executorLanguageSupport: Record<string, string[]> = plugins?.executor_language_support ?? {};
  const generalMultiTurnExecutors: string[] = plugins?.general_multi_turn_executors ?? ["general_multi_turn"];

  const [mode, setMode] = useState<"preset" | "custom">("preset");
  const [name, setName] = useState(t("My run"));
  const [scenarioId, setScenarioId] = useState("");
  const [scenarioHelpers, setScenarioHelpers] = useState<Record<string, string>>({});
  const [targetId, setTargetId] = useState("");
  const [datasetId, setDatasetId] = useState("");
  const [executors, setExecutors] = useState<ConfiguredExecutor[]>([
    { kind: "executor", plugin: "single_turn", params: {} },
  ]);
  const [scorer, setScorer] = useState<ConfiguredPlugin>({ plugin: "refusal", params: {} });
  const [converters, setConverters] = useState<ConfiguredPlugin[]>([]);
  const [converterCategory, setConverterCategory] = useState("all");
  const [converterSearch, setConverterSearch] = useState("");
  const [sharedConverterLlmConfigId, setSharedConverterLlmConfigId] = useState("");
  const [samplingEnabled, setSamplingEnabled] = useState(false);
  const [samplingLimit, setSamplingLimit] = useState<string>("");
  const [samplingShuffle, setSamplingShuffle] = useState(false);
  const [samplingSeed, setSamplingSeed] = useState<string>("");
  const [timeoutSeconds, setTimeoutSeconds] = useState<string>("");
  const [goalSource, setGoalSource] = useState<"dataset_items" | "fixed">("dataset_items");
  const [goalSearch, setGoalSearch] = useState("");
  const [goalPage, setGoalPage] = useState(0);
  const [selectedGoalItemId, setSelectedGoalItemId] = useState("");

  const nativeExecutors = useMemo(() => executors.filter(ex => ex.kind === "executor"), [executors]);
  const executor = nativeExecutors[0] ?? { kind: "executor" as const, plugin: "single_turn", params: {} };
  const scorerSchema = scorerSchemas[scorer.plugin];
  const isGeneralMultiTurnExecutor = nativeExecutors.some(ex => generalMultiTurnExecutors.includes(ex.plugin));
  const selectedExecutorNames = useMemo(
    () => new Set(nativeExecutors.map(ex => ex.plugin)),
    [nativeExecutors],
  );
  const generalGoalValue = nativeExecutors.find(ex => generalMultiTurnExecutors.includes(ex.plugin))?.params.goal ?? "";
  const showGeneralGoalImport = mode === "custom" && isGeneralMultiTurnExecutor;
  const selectedScenario = useMemo(
    () => scenarios?.find((scenario: any) => scenario.id === scenarioId),
    [scenarios, scenarioId],
  );
  const scenarioRequirements = selectedScenario?.requirements ?? [];
  const scenariosByLevel = useMemo(() => {
    const grouped: Record<string, any[]> = { basic: [], advanced: [] };
    for (const scenario of scenarios ?? []) {
      const level = scenario.level === "advanced" ? "advanced" : "basic";
      grouped[level].push(scenario);
    }
    return grouped;
  }, [scenarios]);
  const selectedTarget = useMemo(
    () => targets?.find((target: any) => target.id === targetId),
    [targets, targetId],
  );
  const selectedTargetMaxInputChars = selectedTarget?.params?.max_input_chars;
  const targetHasInputLimit = selectedTargetMaxInputChars != null && selectedTargetMaxInputChars !== "";
  const showSplitExecutorRecommendation = mode === "custom"
    && targetHasInputLimit
    && nativeExecutors.some(ex => ex.plugin === "single_turn")
    && !nativeExecutors.some(ex => ex.plugin === "split_executor");
  const { data: goalDatasetItems } = useQuery({
    queryKey: ["new-run-goal-dataset-items", datasetId, goalSearch, goalPage],
    queryFn: async () => (await api.get(`/api/datasets/${datasetId}/items`, {
      params: {
        limit: 100,
        offset: goalPage * 100,
        q: goalSearch || undefined,
      },
    })).data,
    enabled: showGeneralGoalImport && goalSource === "fixed" && !!datasetId,
  });
  const selectedConverterNames = useMemo(
    () => new Set(converters.map(c => c.plugin)),
    [converters],
  );
  const converterCategoryOptions = useMemo(() => {
    const present = new Set(availableConverters.map(plugin => converterCategories[plugin] ?? "other"));
    const ordered = CONVERTER_CATEGORY_ORDER.filter(category => present.has(category));
    const extra = [...present].filter(category => !ordered.includes(category as any)).sort();
    return ["all", "selected", ...ordered, ...extra];
  }, [availableConverters, converterCategories]);
  const converterCategoryCounts = useMemo(() => {
    const counts: Record<string, number> = {
      all: availableConverters.length,
      selected: converters.length,
    };
    for (const plugin of availableConverters) {
      const category = converterCategories[plugin] ?? "other";
      counts[category] = (counts[category] ?? 0) + 1;
    }
    return counts;
  }, [availableConverters, converterCategories, converters.length]);
  const filteredConverters = useMemo(() => {
    const search = converterSearch.trim().toLowerCase();
    return availableConverters.filter(plugin => {
      if (converterCategory === "selected" && !selectedConverterNames.has(plugin)) return false;
      if (converterCategory !== "all" && converterCategory !== "selected") {
        const category = converterCategories[plugin] ?? "other";
        if (category !== converterCategory) return false;
      }
      return !search || plugin.toLowerCase().includes(search);
    });
  }, [
    availableConverters,
    converterCategories,
    converterCategory,
    converterSearch,
    selectedConverterNames,
  ]);
  const groupedConverters = useMemo(() => {
    const groups = new Map<string, string[]>();
    for (const plugin of filteredConverters) {
      const category = converterCategories[plugin] ?? "other";
      const list = groups.get(category) ?? [];
      list.push(plugin);
      groups.set(category, list);
    }
    const orderedCategories = [
      ...CONVERTER_CATEGORY_ORDER,
      ...[...groups.keys()].filter(category => !CONVERTER_CATEGORY_ORDER.includes(category as any)).sort(),
    ].filter(category => groups.has(category));
    return orderedCategories.map(category => ({ category, plugins: groups.get(category) ?? [] }));
  }, [converterCategories, filteredConverters]);
  const converterLlmConfigCount = useMemo(
    () => countConvertersWithLlmConfig(converters, convSchemas),
    [converters, convSchemas],
  );

  const converterCategoryLabel = (category: string) => {
    if (category === "all") return t("All");
    if (category === "selected") return t("Selected");
    return t(CONVERTER_CATEGORY_LABELS[category] ?? category);
  };
  const executorLanguageLabel = (plugin: string) => {
    const languages = executorLanguageSupport[plugin] ?? [];
    return languages.length ? languages.join(", ") : t("No compatible language support");
  };
  const executorSupportsDatasetLanguage = (plugin: string) => (executorLanguageSupport[plugin] ?? []).length > 0;

  const toggleConverter = (c: string) => {
    if (!executorSupportsDatasetLanguage(c)) return;
    setConverters(prev => {
      const existing = prev.findIndex(p => p.plugin === c);
      if (existing >= 0) return prev.filter((_, i) => i !== existing);
      const next = { plugin: c, params: defaultsFor(convSchemas[c]) };
      const configured = sharedConverterLlmConfigId
        ? applyConverterLlmConfig([next], convSchemas, sharedConverterLlmConfigId)[0]
        : next;
      return [...prev, configured];
    });
  };

  const selectConverterCategory = (category: string) => {
    const pluginsInCategory = availableConverters.filter(
      plugin => (converterCategories[plugin] ?? "other") === category
        && executorSupportsDatasetLanguage(plugin),
    );
    setConverters(prev => {
      const existing = new Set(prev.map(c => c.plugin));
      const additions = pluginsInCategory
        .filter(plugin => !existing.has(plugin))
        .map(plugin => ({ plugin, params: defaultsFor(convSchemas[plugin]) }));
      const configuredAdditions = sharedConverterLlmConfigId
        ? applyConverterLlmConfig(additions, convSchemas, sharedConverterLlmConfigId)
        : additions;
      return [...prev, ...configuredAdditions];
    });
  };

  const clearConverterCategory = (category: string) => {
    setConverters(prev => prev.filter(
      converter => (converterCategories[converter.plugin] ?? "other") !== category,
    ));
  };

  const updateConverterParam = (idx: number, key: string, v: any) => {
    setConverters(prev => prev.map((p, i) => i === idx ? { ...p, params: { ...p.params, [key]: v } } : p));
  };
  const updateSharedConverterLlmConfig = (configId: string) => {
    setSharedConverterLlmConfigId(configId);
    if (!configId) return;
    setConverters(prev => applyConverterLlmConfig(prev, convSchemas, configId));
  };

  const toggleNativeExecutor = (p: string) => {
    if (!executorSupportsDatasetLanguage(p)) return;
    setExecutors(prev => {
      const existing = prev.findIndex(ex => ex.kind === "executor" && ex.plugin === p);
      if (existing >= 0) return prev.filter((_, i) => i !== existing);
      return [...prev, { kind: "executor", plugin: p, params: defaultsFor(executorSchemas[p]) }];
    });
    if (generalMultiTurnExecutors.includes(p)) setGoalSource("dataset_items");
  };
  const setExecutorPlugin = (p: string) => {
    if (!executorSupportsDatasetLanguage(p)) return;
    setExecutors(prev => {
      const withoutSingleTurn = prev.filter(ex => !(ex.kind === "executor" && ex.plugin === "single_turn"));
      if (withoutSingleTurn.some(ex => ex.kind === "executor" && ex.plugin === p)) return withoutSingleTurn;
      return [...withoutSingleTurn, { kind: "executor", plugin: p, params: defaultsFor(executorSchemas[p]) }];
    });
    if (generalMultiTurnExecutors.includes(p)) setGoalSource("dataset_items");
  };
  const updateExecutorParam = (key: string, v: any, plugin?: string) => {
    setExecutors(prev => prev.map(ex => {
      if (ex.kind !== "executor") return ex;
      if (plugin && ex.plugin !== plugin) return ex;
      if (!plugin && ex.plugin !== executor.plugin) return ex;
      return { ...ex, params: { ...ex.params, [key]: v } };
    }));
  };
  const updateGeneralExecutorParam = (key: string, v: any) => {
    setExecutors(prev => prev.map(ex => (
      ex.kind === "executor" && generalMultiTurnExecutors.includes(ex.plugin)
        ? { ...ex, params: { ...ex.params, [key]: v } }
        : ex
    )));
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
      if (nativeExecutors.length + converters.length === 0) missing.push("executors");
      for (const ex of nativeExecutors) {
        const schema = executorSchemas[ex.plugin] ?? {};
        for (const [k, s] of Object.entries(schema)) {
          if (k === "goal" && generalMultiTurnExecutors.includes(ex.plugin) && goalSource === "dataset_items") {
            continue;
          }
          if (s.required) {
            const v = ex.params[k];
            const empty = v === undefined || v === null || v === "" || (Array.isArray(v) && v.length === 0);
            if (empty) missing.push(`executor.${ex.plugin}.${k}`);
          }
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
  }, [
    mode,
    nativeExecutors,
    executorSchemas,
    generalMultiTurnExecutors,
    goalSource,
    scorer,
    scorerSchema,
    converters,
    convSchemas,
  ]);

  const submit = useMutation({
    mutationFn: async () => {
      let base: any;
      if (mode === "preset") {
        const rendered = await api.post(`/api/scenarios/${scenarioId}/runspec`, {
          target_config_id: targetId,
          dataset_config_id: datasetId,
          helper_config_ids: scenarioHelpers,
        });
        base = { ...rendered.data, name };
      } else {
        const executorRefs = [
          ...nativeExecutors.map(ex => {
            const params = { ...ex.params };
            if (generalMultiTurnExecutors.includes(ex.plugin) && goalSource === "dataset_items") {
              params.goal = "";
            }
            return { kind: "executor", plugin: ex.plugin, params };
          }),
          ...converters.map(c => ({ kind: "converter_method", plugin: c.plugin, params: c.params })),
        ];
        base = {
          version: 2,
          name,
          targets: [{ config_id: targetId }],
          dataset: { config_id: datasetId },
          executors: executorRefs,
          scorers: [{ plugin: scorer.plugin, params: scorer.params }],
        };
      }
      
      // Add sampling if enabled
      if (samplingEnabled) {
        base.sampling = {
          limit: samplingLimit ? parseInt(samplingLimit, 10) : null,
          shuffle: samplingShuffle,
          seed: samplingShuffle && samplingSeed ? parseInt(samplingSeed, 10) : null,
        };
      }
      if (timeoutSeconds) base.timeout_seconds = parseFloat(timeoutSeconds);
      
      const r = await api.post("/api/runs", { name, runspec: base });
      await api.post(`/api/runs/${r.data.id}/start`);
      nav(`/runs/${r.data.id}`);
    },
    onError: (e: any) => toast.error(e?.response?.data?.detail ?? t("Failed to start run")),
  });

  const canSubmit = !!targetId && !!datasetId
    && (mode === "custom" || (!!scenarioId && scenarioRequirements.every((req: any) => !!scenarioHelpers[req.id])))
    && paramValidation.length === 0;

  return (
    <div className="max-w-3xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">{t("New run")}</h1>
        <p className="text-sm text-gray-500 mt-1">{t("Pick a preset scenario or assemble your own pipeline.")}</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>{t("1. Basics")}</CardTitle>
        </CardHeader>
        <CardBody>
          <Field label={t("Run name")}><Input value={name} onChange={e => setName(e.target.value)} /></Field>
          <div className="mt-4">
            <Field label={t("Run timeout")} hint={t("Seconds before an automated run is failed; blank means no limit.")}>
              <Input type="number" min="1" placeholder="300" value={timeoutSeconds}
                onChange={e => setTimeoutSeconds(e.target.value)} />
            </Field>
          </div>
          <div className="mt-5">
            <div className="label">{t("Mode")}</div>
            <div className="grid grid-cols-2 gap-3">
              {([
                { id: "preset", title: t("Preset scenario"), desc: t("Curated pipelines (OWASP, jailbreak, …)"), icon: Sparkles },
                { id: "custom", title: t("Custom pipeline"), desc: t("Choose your own executors, methods, scorer"), icon: Wrench },
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
            <CardTitle>{t("2. Scenario")}</CardTitle>
            <CardDescription>{t("A pre-configured combination of executors, methods, and scorer.")}</CardDescription>
          </CardHeader>
          <CardBody className="space-y-5">
            {(["basic", "advanced"] as const).map(level => (
              <div key={level}>
                <div className="mb-2 flex items-center gap-2">
                  <div className="text-xs font-medium uppercase tracking-wide text-gray-500">
                    {level === "basic" ? t("Basic scenarios") : t("Advanced scenarios")}
                  </div>
                  <Badge tone={level === "basic" ? "green" : "amber"}>
                    {level === "basic" ? t("No extra setup") : t("Advanced methods")}
                  </Badge>
                </div>
                <div className="grid grid-cols-1 gap-3">
                  {(scenariosByLevel[level] ?? []).map((scenario: any) => {
                    const active = scenarioId === scenario.id;
                    const recommended = targetHasInputLimit && scenario.id === "input_limited_split";
                    return (
                      <button
                        key={scenario.id}
                        type="button"
                        onClick={() => {
                          setScenarioId(scenario.id);
                          setScenarioHelpers({});
                        }}
                        className={clsx(
                          "rounded-lg border px-4 py-3 text-left transition",
                          active
                            ? "border-brand-500 bg-brand-50/60 ring-2 ring-brand-200"
                            : "border-gray-200 bg-white hover:border-gray-300",
                        )}
                      >
                        <div className="flex flex-wrap items-start justify-between gap-2">
                          <div>
                            <div className="text-sm font-medium text-gray-900">{scenario.title}</div>
                            <div className="mt-1 text-xs text-gray-500">{scenario.description}</div>
                          </div>
                          {recommended && <Badge tone="amber">{t("Recommended")}</Badge>}
                        </div>
                        <div className="mt-2 flex flex-wrap gap-1.5">
                          {(scenario.tags ?? []).map((tag: string) => (
                            <span key={tag} className="rounded-full bg-gray-100 px-2 py-0.5 text-[11px] text-gray-600">
                              {tag}
                            </span>
                          ))}
                        </div>
                        {!!scenario.requirements?.length && (
                          <div className="mt-2 text-[11px] text-amber-700">
                            {t("Requires")}: {scenario.requirements.map((req: any) => req.label ?? req.id).join(", ")}
                          </div>
                        )}
                      </button>
                    );
                  })}
                </div>
              </div>
            ))}
            {scenarioRequirements.length > 0 && (
              <div className="rounded-lg border border-amber-200 bg-amber-50 p-4 space-y-3">
                <div>
                  <div className="text-xs font-medium uppercase tracking-wide text-amber-800">
                    {t("Scenario requirements")}
                  </div>
                  <div className="mt-1 text-xs text-amber-700">
                    {t("Select helper targets used by this preset.")}
                  </div>
                </div>
                {scenarioRequirements.map((req: any) => (
                  <Field key={req.id} label={req.label ?? req.id} hint={req.help}>
                    <Select
                      value={scenarioHelpers[req.id] ?? ""}
                      onChange={e => setScenarioHelpers(prev => ({ ...prev, [req.id]: e.target.value }))}
                    >
                      <option value="">{t("-- pick target --")}</option>
                      {targets?.map((target: any) => (
                        <option key={target.id} value={target.id}>{target.name}</option>
                      ))}
                    </Select>
                  </Field>
                ))}
              </div>
            )}
          </CardBody>
        </Card>
      )}

      <Card>
        <CardHeader><CardTitle>{mode === "preset" ? "3" : "2"}. {t("Target & dataset")}</CardTitle></CardHeader>
        <CardBody>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Field label={t("Target")}>
              <Select value={targetId} onChange={e => setTargetId(e.target.value)}>
                <option value="">{t("-- pick target --")}</option>
                {targets?.map((t: any) => <option key={t.id} value={t.id}>{t.name}</option>)}
              </Select>
            </Field>
            <Field label={t("Dataset")}>
              <Select value={datasetId} onChange={e => {
                setDatasetId(e.target.value);
                setGoalSearch("");
                setGoalPage(0);
                setSelectedGoalItemId("");
              }}>
                <option value="">{t("-- pick dataset --")}</option>
                {datasets?.map((d: any) => <option key={d.id} value={d.id}>{d.name}</option>)}
              </Select>
            </Field>
          </div>

          {targetHasInputLimit && (
            <div className="mt-4 rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
              <div className="font-medium">
                {t("Selected target limits each user message to {{count}} characters.", {
                  count: selectedTargetMaxInputChars,
                })}
              </div>
              {showSplitExecutorRecommendation && (
                <div className="mt-2 flex flex-wrap items-center gap-3">
                  <span className="text-xs">
                    {t("For long dataset prompts, use split_executor so chunks stay within the limit.")}
                  </span>
                  {plugins?.executors?.includes("split_executor") && (
                    <Button
                      type="button"
                      size="sm"
                      variant="secondary"
                      onClick={() => setExecutorPlugin("split_executor")}
                    >
                      {t("Use split_executor")}
                    </Button>
                  )}
                </div>
              )}
            </div>
          )}

          {showGeneralGoalImport && (
            <div className="mt-5 rounded-lg border border-gray-200 bg-gray-50/50 p-4 space-y-3">
              <div className="text-xs font-medium text-gray-500 uppercase tracking-wide">{t("Attack goal")}</div>
              <Field label={t("Attack goal source")}>
                <Select value={goalSource} onChange={e => {
                  const next = e.target.value as "dataset_items" | "fixed";
                  setGoalSource(next);
                  setGoalPage(0);
                  setSelectedGoalItemId("");
                }}>
                  <option value="dataset_items">{t("Use each dataset item")}</option>
                  <option value="fixed">{t("Fixed goal")}</option>
                </Select>
              </Field>
              {goalSource === "dataset_items" ? (
                <div className="text-xs text-gray-500">{t("Each dataset prompt will be used as the attack goal.")}</div>
              ) : (
                <>
                  {datasetId && (
                    <>
                      <Field label={t("Search prompts")}>
                        <Input value={goalSearch} onChange={e => {
                          setGoalSearch(e.target.value);
                          setGoalPage(0);
                          setSelectedGoalItemId("");
                        }} />
                      </Field>
                      <Field label={t("Import from dataset")}>
                        <Select value={selectedGoalItemId} onChange={e => {
                          const selectedId = e.target.value;
                          setSelectedGoalItemId(selectedId);
                          const item = goalDatasetItems?.items?.find((it: any) => it.id === selectedId);
                          if (item) updateGeneralExecutorParam("goal", item.text);
                        }}>
                          <option value="">{t("-- load prompt --")}</option>
                          {goalDatasetItems?.items?.map((item: any, idx: number) => (
                            <option key={`${item.id}-${idx}`} value={item.id}>
                              {item.id}: {item.text.slice(0, 80)}
                            </option>
                          ))}
                        </Select>
                      </Field>
                      <div className="flex items-center justify-between gap-2 text-xs text-gray-500">
                        <span>{t("Showing {{count}} of {{total}}", {
                          count: goalDatasetItems?.items?.length ?? 0,
                          total: goalDatasetItems?.total ?? goalDatasetItems?.total_returned ?? 0,
                        })}</span>
                        <div className="flex gap-2">
                          <Button variant="secondary" size="sm" disabled={goalPage === 0}
                            onClick={() => {
                              setSelectedGoalItemId("");
                              setGoalPage(p => Math.max(0, p - 1));
                            }}>
                            {t("Previous")}
                          </Button>
                          <Button variant="secondary" size="sm" disabled={!goalDatasetItems?.has_more}
                            onClick={() => {
                              setSelectedGoalItemId("");
                              setGoalPage(p => p + 1);
                            }}>
                            {t("Next")}
                          </Button>
                        </div>
                      </div>
                    </>
                  )}
                  <Field label={t("Attack goal")}>
                    <Textarea rows={4} value={generalGoalValue}
                      onChange={e => updateGeneralExecutorParam("goal", e.target.value)} />
                  </Field>
                </>
              )}
            </div>
          )}
          
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
                {t("Dataset sampling (optional)")}
              </label>
            </div>
            
            {samplingEnabled && (
              <div className="rounded-lg border border-gray-200 bg-gray-50/50 p-4 space-y-3">
                <Field label={t("Limit")} hint={t("Maximum number of items to process (blank = no limit)")}>
                  <Input
                    type="number"
                    min="1"
                    placeholder={t("e.g., 50")}
                    value={samplingLimit}
                    onChange={e => setSamplingLimit(e.target.value)}
                  />
                </Field>
                
                <Field label={t("Shuffle")}>
                  <label className="inline-flex items-center gap-2 text-sm">
                    <input
                      type="checkbox"
                      checked={samplingShuffle}
                      onChange={e => setSamplingShuffle(e.target.checked)}
                      className="h-4 w-4 text-brand-600 rounded border-gray-300"
                    />
                    <span className="text-gray-600">{t("Randomize dataset order")}</span>
                  </label>
                </Field>
                
                {samplingShuffle && (
                  <Field label={t("Seed")} hint={t("Random seed for deterministic shuffle (optional)")}>
                    <Input
                      type="number"
                      placeholder={t("e.g., 42")}
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
            <CardTitle>{t("3. Pipeline")}</CardTitle>
            <CardDescription>{t("Each selected executor or method creates a separate attack attempt. Scorer classifies the response.")}</CardDescription>
          </CardHeader>
          <CardBody className="space-y-6">
            <div>
              <Field label={t("Executors")} hint={t("Native executors can run single-turn or multi-turn attack flows.")}>
                <div className="space-y-3 rounded-lg border border-gray-200 bg-gray-50/50 p-3">
                  <div className="flex flex-wrap gap-2">
                    {plugins?.executors?.map((ex: string) => {
                      const on = selectedExecutorNames.has(ex);
                      const disabled = !executorSupportsDatasetLanguage(ex);
                      return (
                        <button
                          key={ex}
                          type="button"
                          disabled={disabled}
                          title={executorLanguageLabel(ex)}
                          onClick={() => toggleNativeExecutor(ex)}
                          className={clsx(
                            "rounded-full border px-2.5 py-1 text-xs transition",
                            disabled
                              ? "cursor-not-allowed border-gray-200 bg-gray-100 text-gray-400"
                              : on
                              ? "border-brand-600 bg-brand-600 text-white"
                              : "border-gray-200 bg-white text-gray-700 hover:border-gray-300",
                          )}
                        >
                          {ex}
                        </button>
                      );
                    })}
                  </div>
                  <div className="flex flex-wrap items-center gap-2 text-[11px] text-gray-500">
                    <span>{t("Selected executors")}: {nativeExecutors.length}</span>
                    {nativeExecutors.map(ex => (
                      <Badge key={ex.plugin} tone="blue">
                        {ex.plugin} · {executorLanguageLabel(ex.plugin)}
                      </Badge>
                    ))}
                  </div>
                </div>
              </Field>
              {nativeExecutors.length > 0 && (
                <div className="mt-3 space-y-3">
                  {nativeExecutors.map(ex => {
                    const schema = executorSchemas[ex.plugin] ?? {};
                    const visibleEntries = Object.entries(schema)
                      .filter(([k]) => !(generalMultiTurnExecutors.includes(ex.plugin) && k === "goal"));
                    return (
                      <div key={ex.plugin} className="rounded-lg border border-gray-200 bg-gray-50/50 p-4 space-y-3">
                        <div className="flex flex-wrap items-center justify-between gap-2">
                          <div>
                            <div className="text-xs font-medium text-gray-500 uppercase tracking-wide">
                              {ex.plugin} {t("params")}
                            </div>
                            <div className="mt-0.5 text-[11px] text-gray-400">
                              {t("Languages: {{languages}}", { languages: executorLanguageLabel(ex.plugin) })}
                            </div>
                          </div>
                          <button type="button" onClick={() => toggleNativeExecutor(ex.plugin)}
                            className="text-gray-400 hover:text-gray-600"><X className="h-4 w-4" /></button>
                        </div>
                        {visibleEntries.length ? visibleEntries.map(([k, s]) => (
                          <ParamField key={k} name={k} schema={s} targets={targets ?? []}
                            promptAssets={promptAssets ?? []}
                            value={ex.params[k]} onChange={v => updateExecutorParam(k, v, ex.plugin)} />
                        )) : (
                          <div className="text-xs text-gray-500">{t("No parameters")}</div>
                        )}
                      </div>
                    );
                  })}
                </div>
              )}
            </div>

            <div>
              <Field label={t("Scorer")}>
                <Select value={scorer.plugin} onChange={e => setScorerPlugin(e.target.value)}>
                  {plugins?.scorers?.map((s: string) => <option key={s} value={s}>{s}</option>)}
                </Select>
              </Field>
              {scorerSchema && Object.keys(scorerSchema).length > 0 && (
                <div className="mt-3 rounded-lg border border-gray-200 bg-gray-50/50 p-4 space-y-3">
                  <div className="text-xs font-medium text-gray-500 uppercase tracking-wide">{t("Scorer params")}</div>
                  {Object.entries(scorerSchema).map(([k, s]) => (
                    <ParamField key={k} name={k} schema={s} targets={targets ?? []}
                      promptAssets={promptAssets ?? []}
                      value={scorer.params[k]} onChange={v => updateScorerParam(k, v)} />
                  ))}
                </div>
              )}
            </div>

            <div>
              <Field label={t("Executor methods")} hint={t("Each selected executor or method creates a separate attack attempt.")}>
                <div className="space-y-3 rounded-lg border border-gray-200 bg-gray-50/50 p-3">
                  <Input
                    value={converterSearch}
                    onChange={e => setConverterSearch(e.target.value)}
                    placeholder={t("Filter by name...")}
                  />
                  <div className="flex flex-wrap gap-1.5">
                    {converterCategoryOptions.map(category => (
                      <button
                        key={category}
                        type="button"
                        onClick={() => setConverterCategory(category)}
                        className={clsx(
                          "rounded-full border px-2.5 py-1 text-[11px] font-medium transition",
                          converterCategory === category
                            ? "border-brand-600 bg-brand-600 text-white"
                            : "border-gray-200 bg-white text-gray-600 hover:border-gray-300",
                        )}
                      >
                        {converterCategoryLabel(category)}
                        <span className={clsx(
                          "ml-1 tabular-nums",
                          converterCategory === category ? "text-brand-100" : "text-gray-400",
                        )}>
                          {converterCategoryCounts[category] ?? 0}
                        </span>
                      </button>
                    ))}
                  </div>
                  <div className="text-[11px] text-gray-500">
                    {t("Showing {{count}} of {{total}} executor methods", {
                      count: filteredConverters.length,
                      total: availableConverters.length,
                    })}
                  </div>
                  {availableConverters.length === 0 ? (
                    <Badge>{t("No executor methods available")}</Badge>
                  ) : groupedConverters.length === 0 ? (
                    <div className="rounded-lg border border-gray-200 bg-white py-6 text-center text-xs text-gray-500">
                      {t("No methods match.")}
                    </div>
                  ) : (
                    <div className="max-h-80 overflow-y-auto space-y-3">
                      {groupedConverters.map(group => {
                        const selectedInGroup = group.plugins.filter(plugin =>
                          selectedConverterNames.has(plugin),
                        ).length;
                        const compatibleInGroup = group.plugins.filter(plugin =>
                          executorSupportsDatasetLanguage(plugin),
                        ).length;
                        return (
                          <div
                            key={group.category}
                            className="rounded-lg border border-gray-200 bg-white p-3"
                          >
                            <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
                              <div>
                                <div className="text-xs font-medium uppercase tracking-wide text-gray-500">
                                  {converterCategoryLabel(group.category)}
                                </div>
                                <div className="mt-0.5 text-[11px] text-gray-400">
                                  {selectedInGroup}/{compatibleInGroup} {t("Selected")}
                                </div>
                              </div>
                              <div className="flex gap-2">
                                <Button
                                  type="button"
                                  variant="secondary"
                                  size="sm"
                                  disabled={compatibleInGroup === 0}
                                  onClick={() => selectConverterCategory(group.category)}
                                >
                                  {t("Select all")}
                                </Button>
                                <Button
                                  type="button"
                                  variant="secondary"
                                  size="sm"
                                  disabled={selectedInGroup === 0}
                                  onClick={() => clearConverterCategory(group.category)}
                                >
                                  {t("Clear")}
                                </Button>
                              </div>
                            </div>
                            <div className="flex flex-wrap gap-2">
                              {group.plugins.map(plugin => {
                                const on = selectedConverterNames.has(plugin);
                                const disabled = !executorSupportsDatasetLanguage(plugin);
                                return (
                                  <button
                                    key={plugin}
                                    type="button"
                                    disabled={disabled}
                                    title={executorLanguageLabel(plugin)}
                                    onClick={() => toggleConverter(plugin)}
                                    className={clsx(
                                      "px-2.5 py-1 text-xs rounded-full border transition",
                                      disabled
                                        ? "cursor-not-allowed border-gray-200 bg-gray-100 text-gray-400"
                                      : on
                                        ? "bg-brand-600 border-brand-600 text-white"
                                        : "bg-white border-gray-200 text-gray-700 hover:border-gray-300",
                                    )}
                                  >
                                    {plugin}
                                  </button>
                                );
                              })}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>
              </Field>
              {converterLlmConfigCount > 0 && (
                <div className="mt-3 rounded-lg border border-brand-100 bg-brand-50/50 p-4 space-y-3">
                  <div>
                    <div className="text-xs font-medium text-brand-700 uppercase tracking-wide">
                      {t("Shared method LLM")}
                    </div>
                    <div className="mt-1 text-xs text-brand-700">
                      {t("Apply one helper LLM target to {{count}} selected methods that require it.", {
                        count: converterLlmConfigCount,
                      })}
                    </div>
                  </div>
                  <Field
                    label={t("Method LLM")}
                    hint={t("Selecting a target fills every selected method LLM field. Individual method params remain editable.")}
                  >
                    <Select
                      value={sharedConverterLlmConfigId}
                      onChange={e => updateSharedConverterLlmConfig(e.target.value)}
                    >
                      <option value="">{t("-- keep per-converter settings --")}</option>
                      {targets?.map((target: any) => (
                        <option key={target.id} value={target.id}>{target.name}</option>
                      ))}
                    </Select>
                  </Field>
                </div>
              )}
              {converters.length > 0 && (
                <div className="mt-3 space-y-3">
                  {converters.map((c, i) => {
                    const cs = convSchemas[c.plugin] ?? {};
                    if (Object.keys(cs).length === 0) return null;
                    return (
                      <div key={c.plugin} className="rounded-lg border border-gray-200 bg-gray-50/50 p-4 space-y-3">
                        <div className="flex items-center justify-between">
                          <div className="text-xs font-medium text-gray-500 uppercase tracking-wide">{c.plugin} {t("params")}</div>
                          <button type="button" onClick={() => toggleConverter(c.plugin)}
                            className="text-gray-400 hover:text-gray-600"><X className="h-4 w-4" /></button>
                        </div>
                        {Object.entries(cs).map(([k, s]) => (
                          <ParamField key={k} name={k} schema={s} targets={targets ?? []}
                            promptAssets={promptAssets ?? []}
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
          {t("Missing required fields: {{fields}}", { fields: paramValidation.join(", ") })}
        </div>
      )}

      <div className="flex justify-end">
        <Button icon={<PlayCircle className="h-4 w-4" />} loading={submit.isPending}
          disabled={!canSubmit} onClick={() => submit.mutate()}>
          {t("Create & start")}
        </Button>
      </div>
    </div>
  );
}
