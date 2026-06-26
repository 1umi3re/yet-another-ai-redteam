import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { useMemo, useState } from "react";
import { api } from "../lib/api";
import { Card, CardBody, CardHeader, CardTitle, CardDescription } from "../components/ui/Card";
import { Button } from "../components/ui/Button";
import { Input, Select, Field, Textarea } from "../components/ui/Form";
import { Badge } from "../components/ui/Badge";
import { PlayCircle, Save, Sparkles, Wrench, X } from "lucide-react";
import clsx from "clsx";
import { toast } from "sonner";
import { ConfiguredPlugin, defaultsFor, ParamField, PluginSchemas } from "../components/PluginParamsForm";
import { useI18n } from "../lib/i18n";
import {
  attackMethodSearchText,
  formatAttackMethodName,
} from "../lib/attackMethodTaxonomy";
import {
  applyConverterLlmConfig,
  countConvertersWithLlmConfig,
} from "../lib/converterLlmParams";
import { buildCustomScenarioPayload } from "../lib/customScenarioPayload";
import {
  expandConverterWithAttackTemplates,
  expandRunSpecAttackTemplates,
} from "../lib/attackMethodTemplates";

type ConfiguredExecutor = ConfiguredPlugin & { kind: "executor" | "converter_method" };
type AttackCategoryMeta = {
  id: string;
  name: string;
  alias?: string;
  type?: string;
  description?: string | null;
  display_order?: number;
  mapped_count?: number;
};
type AttackMethodItem = {
  key: string;
  kind: "executor" | "converter_method";
  plugin: string;
  category: string;
  technicalCategory: string;
};

export default function NewRun() {
  const { t, language } = useI18n();
  const nav = useNavigate();
  const queryClient = useQueryClient();
  const { data: targets } = useQuery({ queryKey: ["targets"], queryFn: async () => (await api.get("/api/targets")).data });
  const { data: datasets } = useQuery({ queryKey: ["datasets"], queryFn: async () => (await api.get("/api/datasets")).data });
  const { data: scenarios } = useQuery({ queryKey: ["scenarios"], queryFn: async () => (await api.get("/api/scenarios")).data });
  const { data: plugins } = useQuery({ queryKey: ["plugins"], queryFn: async () => (await api.get("/api/plugins")).data });
  const { data: promptAssets } = useQuery({ queryKey: ["prompt-assets"], queryFn: async () => (await api.get("/api/prompt-assets")).data });

  const convSchemas: PluginSchemas = plugins?.params?.executor_methods ?? plugins?.params?.converters ?? {};
  const scorerSchemas: PluginSchemas = plugins?.params?.scorers ?? {};
  const executorSchemas: PluginSchemas = plugins?.params?.executors ?? {};
  const nativeExecutorPlugins: string[] = plugins?.executors ?? [];
  const availableConverters: string[] = plugins?.executor_methods ?? plugins?.converters ?? [];
  const legacyConverterCategories: Record<string, string> = plugins?.executor_method_categories ?? plugins?.converter_categories ?? {};
  const attackCategoryMeta: Record<string, AttackCategoryMeta> = plugins?.executor_attack_category_meta ?? {};
  const executorAttackCategories: Record<string, string> = plugins?.executor_attack_categories ?? legacyConverterCategories;
  const executorTechnicalCategories: Record<string, string> = plugins?.executor_technical_categories ?? {};
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
  const [presetScorerOverride, setPresetScorerOverride] = useState(false);
  const [converters, setConverters] = useState<ConfiguredPlugin[]>([]);
  const [attackCategory, setAttackCategory] = useState("all");
  const [attackSearch, setAttackSearch] = useState("");
  const [useAllAttackTemplates, setUseAllAttackTemplates] = useState(false);
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
  const [saveScenarioOpen, setSaveScenarioOpen] = useState(false);
  const [saveScenarioName, setSaveScenarioName] = useState("");
  const [saveScenarioDescription, setSaveScenarioDescription] = useState("");
  const [saveScenarioTags, setSaveScenarioTags] = useState("custom");

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
  const selectedDataset = useMemo(
    () => datasets?.find((dataset: any) => dataset.id === datasetId),
    [datasets, datasetId],
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
  const selectedAttackMethodKeys = useMemo(() => {
    const keys = new Set<string>();
    for (const executor of nativeExecutors) keys.add(`executor:${executor.plugin}`);
    for (const converter of converters) keys.add(`converter_method:${converter.plugin}`);
    return keys;
  }, [converters, nativeExecutors]);
  const attackMethods: AttackMethodItem[] = useMemo(() => [
    ...nativeExecutorPlugins.map(plugin => ({
      key: `executor:${plugin}`,
      kind: "executor" as const,
      plugin,
      category: executorAttackCategories[plugin] ?? "uncategorized",
      technicalCategory: executorTechnicalCategories[plugin] ?? "executor",
    })),
    ...availableConverters.map(plugin => ({
      key: `converter_method:${plugin}`,
      kind: "converter_method" as const,
      plugin,
      category: executorAttackCategories[plugin] ?? legacyConverterCategories[plugin] ?? "uncategorized",
      technicalCategory: executorTechnicalCategories[plugin] ?? legacyConverterCategories[plugin] ?? "other",
    })),
  ], [
    availableConverters,
    executorAttackCategories,
    executorTechnicalCategories,
    legacyConverterCategories,
    nativeExecutorPlugins,
  ]);
  const attackCategoryLabel = (category: string) => {
    if (category === "all") return t("All");
    if (category === "selected") return t("Selected");
    const meta = attackCategoryMeta[category];
    if (!meta) return category;
    return language === "zh" ? meta.name : (meta.alias || meta.name || category);
  };
  const attackMethodName = (plugin: string) => formatAttackMethodName(plugin, language);
  const attackCategoryOptions = useMemo(() => {
    const present = [...new Set(attackMethods.map(method => method.category))];
    present.sort((a, b) => {
      const orderA = attackCategoryMeta[a]?.display_order ?? 9999;
      const orderB = attackCategoryMeta[b]?.display_order ?? 9999;
      if (orderA !== orderB) return orderA - orderB;
      return attackCategoryLabel(a).localeCompare(attackCategoryLabel(b));
    });
    return ["all", "selected", ...present];
  }, [attackCategoryMeta, attackMethods, language]);
  const attackCategoryCounts = useMemo(() => {
    const counts: Record<string, number> = {
      all: attackMethods.length,
      selected: selectedAttackMethodKeys.size,
    };
    for (const method of attackMethods) {
      counts[method.category] = (counts[method.category] ?? 0) + 1;
    }
    return counts;
  }, [attackMethods, selectedAttackMethodKeys.size]);
  const filteredAttackMethods = useMemo(() => {
    const search = attackSearch.trim().toLowerCase();
    return attackMethods.filter(method => {
      if (attackCategory === "selected" && !selectedAttackMethodKeys.has(method.key)) return false;
      if (attackCategory !== "all" && attackCategory !== "selected") {
        if (method.category !== attackCategory) return false;
      }
      if (!search) return true;
      const label = attackCategoryLabel(method.category).toLowerCase();
      return attackMethodSearchText(method.plugin, language).toLowerCase().includes(search)
        || method.kind.toLowerCase().includes(search)
        || method.technicalCategory.toLowerCase().includes(search)
        || label.includes(search);
    });
  }, [
    attackCategory,
    attackMethods,
    attackSearch,
    language,
    selectedAttackMethodKeys,
  ]);
  const groupedAttackMethods = useMemo(() => {
    const groups = new Map<string, AttackMethodItem[]>();
    for (const method of filteredAttackMethods) {
      const list = groups.get(method.category) ?? [];
      list.push(method);
      groups.set(method.category, list);
    }
    const orderedCategories = [...groups.keys()].sort((a, b) => {
      const orderA = attackCategoryMeta[a]?.display_order ?? 9999;
      const orderB = attackCategoryMeta[b]?.display_order ?? 9999;
      if (orderA !== orderB) return orderA - orderB;
      return attackCategoryLabel(a).localeCompare(attackCategoryLabel(b));
    });
    return orderedCategories.map(category => ({
      category,
      methods: (groups.get(category) ?? []).sort((a, b) => {
        if (a.kind !== b.kind) return a.kind === "executor" ? -1 : 1;
        return attackMethodName(a.plugin).localeCompare(attackMethodName(b.plugin));
      }),
    }));
  }, [attackCategoryMeta, filteredAttackMethods, language]);
  const converterLlmConfigCount = useMemo(
    () => countConvertersWithLlmConfig(converters, convSchemas),
    [converters, convSchemas],
  );

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
  const toggleAttackMethod = (method: AttackMethodItem) => {
    if (method.kind === "executor") {
      toggleNativeExecutor(method.plugin);
    } else {
      toggleConverter(method.plugin);
    }
  };
  const selectAttackCategory = (category: string) => {
    const methodsInCategory = attackMethods.filter(
      method => method.category === category && executorSupportsDatasetLanguage(method.plugin),
    );
    const executorAdditions = methodsInCategory
      .filter(method => method.kind === "executor" && !selectedExecutorNames.has(method.plugin))
      .map(method => ({ kind: "executor" as const, plugin: method.plugin, params: defaultsFor(executorSchemas[method.plugin]) }));
    const converterAdditions = methodsInCategory
      .filter(method => method.kind === "converter_method" && !selectedConverterNames.has(method.plugin))
      .map(method => ({ plugin: method.plugin, params: defaultsFor(convSchemas[method.plugin]) }));
    if (executorAdditions.length > 0) {
      setExecutors(prev => [...prev, ...executorAdditions]);
      if (executorAdditions.some(method => generalMultiTurnExecutors.includes(method.plugin))) {
        setGoalSource("dataset_items");
      }
    }
    if (converterAdditions.length > 0) {
      const configuredAdditions = sharedConverterLlmConfigId
        ? applyConverterLlmConfig(converterAdditions, convSchemas, sharedConverterLlmConfigId)
        : converterAdditions;
      setConverters(prev => [...prev, ...configuredAdditions]);
    }
  };
  const clearAttackCategory = (category: string) => {
    setExecutors(prev => prev.filter(
      executor => (executorAttackCategories[executor.plugin] ?? "uncategorized") !== category,
    ));
    setConverters(prev => prev.filter(
      converter => (executorAttackCategories[converter.plugin] ?? legacyConverterCategories[converter.plugin] ?? "uncategorized") !== category,
    ));
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

  const loadAttackMethodTemplateDetail = async (plugin: string) => (
    await api.get(`/api/attack-methods/converter_method/${encodeURIComponent(plugin)}/templates`)
  ).data;

  const resolveConvertersForRun = async () => {
    if (!useAllAttackTemplates) {
      return converters.map(converter => ({ plugin: converter.plugin, params: { ...converter.params } }));
    }
    const expanded = await Promise.all(converters.map(async converter => {
      const detail = await loadAttackMethodTemplateDetail(converter.plugin);
      return expandConverterWithAttackTemplates(converter, detail);
    }));
    return expanded.flat();
  };

  const applyPresetRunOptions = async (runspec: any) => {
    let next = { ...runspec };
    if (useAllAttackTemplates) {
      next = await expandRunSpecAttackTemplates(next, loadAttackMethodTemplateDetail);
    }
    if (presetScorerOverride) {
      next.scorers = [{ plugin: scorer.plugin, params: { ...scorer.params } }];
    }
    return next;
  };

  const paramValidation = useMemo(() => {
    const missing: string[] = [];
    const validateScorer = mode === "custom" || (mode === "preset" && presetScorerOverride);
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
    if (validateScorer) {
      for (const [k, s] of Object.entries(scorerSchema ?? {})) {
        if (s.required) {
          const v = scorer.params[k];
          const empty = v === undefined || v === null || v === "" || (Array.isArray(v) && v.length === 0);
          if (empty) missing.push(`scorer.${k}`);
        }
      }
    }
    return missing;
  }, [
    mode,
    presetScorerOverride,
    nativeExecutors,
    executorSchemas,
    generalMultiTurnExecutors,
    goalSource,
    scorer,
    scorerSchema,
    converters,
    convSchemas,
  ]);
  const selectedMethodCount = nativeExecutors.length + converters.length;
  const canSaveScenario = mode === "custom"
    && selectedMethodCount > 0
    && saveScenarioName.trim().length > 0
    && paramValidation.length === 0;
  const canOpenSaveScenario = mode === "custom" && selectedMethodCount > 0 && paramValidation.length === 0;

  const openSaveScenarioDialog = () => {
    setSaveScenarioName(name.trim() ? `${name.trim()} ${t("Scenario")}` : t("Saved pipeline"));
    setSaveScenarioDescription("");
    setSaveScenarioTags("custom");
    setSaveScenarioOpen(true);
  };

  const submit = useMutation({
    mutationFn: async () => {
      let base: any;
      if (mode === "preset") {
        const rendered = await api.post(`/api/scenarios/${scenarioId}/runspec`, {
          target_config_id: targetId,
          dataset_config_id: datasetId,
          helper_config_ids: scenarioHelpers,
        });
        base = await applyPresetRunOptions({ ...rendered.data, name });
      } else {
        const expandedConverters = await resolveConvertersForRun();
        const executorRefs = [
          ...nativeExecutors.map(ex => {
            const params = { ...ex.params };
            if (generalMultiTurnExecutors.includes(ex.plugin) && goalSource === "dataset_items") {
              params.goal = "";
            }
            return { kind: "executor", plugin: ex.plugin, params };
          }),
          ...expandedConverters.map(c => ({ kind: "converter_method", plugin: c.plugin, params: c.params })),
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

  const saveScenario = useMutation({
    mutationFn: async () => {
      const expandedConverters = await resolveConvertersForRun();
      const payload = buildCustomScenarioPayload({
        scenarioName: saveScenarioName,
        description: saveScenarioDescription,
        tagsText: saveScenarioTags,
        nativeExecutors,
        converters: expandedConverters,
        scorer,
        generalMultiTurnExecutors,
        goalSource,
        samplingEnabled,
        samplingLimit,
        samplingShuffle,
        samplingSeed,
        timeoutSeconds,
      });
      const result = await api.post("/api/scenarios/custom", payload);
      return result.data;
    },
    onSuccess: async (scenario: any) => {
      toast.success(t("Scenario saved"));
      await queryClient.invalidateQueries({ queryKey: ["scenarios"] });
      setScenarioId(scenario.id);
      setScenarioHelpers({});
      setMode("preset");
      setSaveScenarioOpen(false);
    },
    onError: (e: any) => toast.error(e?.response?.data?.detail ?? t("Failed to save scenario")),
  });

  const canSubmit = !!targetId && !!datasetId
    && (mode === "custom" || (!!scenarioId && scenarioRequirements.every((req: any) => !!scenarioHelpers[req.id])))
    && paramValidation.length === 0;
  const missingRunRequirements = [
    !targetId && t("Choose a target"),
    !datasetId && t("Choose a dataset"),
    mode === "preset" && !scenarioId && t("Choose a scenario"),
    mode === "preset" && scenarioRequirements.some((req: any) => !scenarioHelpers[req.id]) && t("Complete scenario helper targets"),
    mode === "custom" && nativeExecutors.length + converters.length === 0 && t("Choose at least one attack method"),
    ...paramValidation.map(field => t("Complete {{field}}", { field })),
  ].filter(Boolean);
  const samplingSummary = samplingEnabled
    ? t("Enabled{{limit}}", { limit: samplingLimit ? `, ${samplingLimit}` : "" })
    : t("Off");
  const renderScorerFields = () => (
    <>
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
    </>
  );

  return (
    <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_320px]">
      <div className="space-y-6">
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
            <div role="radiogroup" aria-label={t("Run mode")} className="grid grid-cols-2 gap-3">
              {([
                { id: "preset", title: t("Preset scenario"), desc: t("Curated pipelines (OWASP, jailbreak, …)"), icon: Sparkles },
                { id: "custom", title: t("Custom pipeline"), desc: t("Choose your own executors, methods, scorer"), icon: Wrench },
              ] as const).map(opt => {
                const Icon = opt.icon;
                const active = mode === opt.id;
                return (
                  <button key={opt.id} type="button" role="radio" aria-checked={active} onClick={() => setMode(opt.id)}
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
            <div className="rounded-lg border border-gray-200 bg-gray-50/50 p-4 space-y-4">
              <div>
                <div className="text-xs font-medium uppercase tracking-wide text-gray-500">
                  {t("Preset configuration")}
                </div>
                <div className="mt-1 text-xs text-gray-500">
                  {t("Adjust how this scenario is expanded at run time.")}
                </div>
              </div>
              <label className="inline-flex items-start gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={useAllAttackTemplates}
                  onChange={e => setUseAllAttackTemplates(e.target.checked)}
                  className="mt-0.5 h-4 w-4 rounded border-gray-300 text-brand-600"
                />
                <span>
                  <span className="block text-gray-700">{t("Use all templates for selected methods")}</span>
                  <span className="block text-xs text-gray-500">{t("Template-backed methods run once per template.")}</span>
                </span>
              </label>
              <div className="border-t border-gray-200 pt-4">
                <label className="inline-flex items-start gap-2 text-sm">
                  <input
                    type="checkbox"
                    checked={presetScorerOverride}
                    onChange={e => setPresetScorerOverride(e.target.checked)}
                    className="mt-0.5 h-4 w-4 rounded border-gray-300 text-brand-600"
                  />
                  <span>
                    <span className="block text-gray-700">{t("Override scenario scorer")}</span>
                    <span className="block text-xs text-gray-500">
                      {t("Use this scorer instead of the scorer bundled with the scenario.")}
                    </span>
                  </span>
                </label>
                {presetScorerOverride && (
                  <div className="mt-4">
                    {renderScorerFields()}
                  </div>
                )}
              </div>
            </div>
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
          <CardHeader className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
            <div>
              <CardTitle>{t("3. Pipeline")}</CardTitle>
              <CardDescription>{t("Each selected executor or method creates a separate attack attempt. Scorer classifies the response.")}</CardDescription>
            </div>
            <Button
              type="button"
              variant="secondary"
              size="sm"
              icon={<Save className="h-4 w-4" />}
              disabled={!canOpenSaveScenario}
              onClick={openSaveScenarioDialog}
            >
              {t("Save as scenario")}
            </Button>
          </CardHeader>
          <CardBody className="space-y-6">
            <div>
              <Field
                label={t("Attack methods")}
                hint={t("Filter by category and select native executors or converter-backed methods.")}
              >
                <div className="space-y-3 rounded-lg border border-gray-200 bg-gray-50/50 p-3">
                  <Input
                    value={attackSearch}
                    onChange={e => setAttackSearch(e.target.value)}
                    placeholder={t("Search attack methods")}
                  />
                  <div className="flex flex-wrap gap-1.5">
                    {attackCategoryOptions.map(category => (
                      <button
                        key={category}
                        type="button"
                        aria-pressed={attackCategory === category}
                        aria-label={t("Filter attack methods by {{category}}, {{count}} methods", {
                          category: attackCategoryLabel(category),
                          count: attackCategoryCounts[category] ?? 0,
                        })}
                        onClick={() => setAttackCategory(category)}
                        className={clsx(
                          "rounded-full border px-2.5 py-1 text-[11px] font-medium transition",
                          attackCategory === category
                            ? "border-brand-600 bg-brand-600 text-white"
                            : "border-gray-200 bg-white text-gray-600 hover:border-gray-300",
                        )}
                      >
                        {attackCategoryLabel(category)}
                        <span className={clsx(
                          "ml-1 tabular-nums",
                          attackCategory === category ? "text-brand-100" : "text-gray-400",
                        )}>
                          {attackCategoryCounts[category] ?? 0}
                        </span>
                      </button>
                    ))}
                  </div>
                  <div className="text-[11px] text-gray-500">
                    {t("Showing {{count}} of {{total}} attack methods", {
                      count: filteredAttackMethods.length,
                      total: attackMethods.length,
                    })}
                  </div>
                  <div className="flex flex-wrap items-center gap-2 text-[11px] text-gray-500">
                    <span>{t("Selected executors")}: {nativeExecutors.length}</span>
                    <span>{t("Selected methods")}: {converters.length}</span>
                    {nativeExecutors.map(ex => (
                      <Badge key={ex.plugin} tone="blue">
                        {attackMethodName(ex.plugin)} · {executorLanguageLabel(ex.plugin)}
                      </Badge>
                    ))}
                  </div>
                  <label className="inline-flex items-center gap-2 text-sm">
                    <input
                      type="checkbox"
                      checked={useAllAttackTemplates}
                      onChange={e => setUseAllAttackTemplates(e.target.checked)}
                      className="h-4 w-4 rounded border-gray-300 text-brand-600"
                    />
                    <span className="text-gray-700">{t("Use all templates for selected methods")}</span>
                    <span className="text-xs text-gray-500">{t("Template-backed methods run once per template.")}</span>
                  </label>
                  {attackMethods.length === 0 ? (
                    <Badge>{t("No attack methods available")}</Badge>
                  ) : groupedAttackMethods.length === 0 ? (
                    <div className="rounded-lg border border-gray-200 bg-white py-6 text-center text-xs text-gray-500">
                      {t("No attack methods match.")}
                    </div>
                  ) : (
                    <div className="max-h-80 overflow-y-auto space-y-3">
                      {groupedAttackMethods.map(group => {
                        const selectedInGroup = group.methods.filter(method =>
                          selectedAttackMethodKeys.has(method.key),
                        ).length;
                        const compatibleInGroup = group.methods.filter(method =>
                          executorSupportsDatasetLanguage(method.plugin),
                        ).length;
                        const meta = attackCategoryMeta[group.category];
                        return (
                          <div
                            key={group.category}
                            className="rounded-lg border border-gray-200 bg-white p-3"
                          >
                            <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
                              <div>
                                <div className="flex flex-wrap items-center gap-2">
                                  <div className="text-xs font-medium uppercase tracking-wide text-gray-500">
                                    {attackCategoryLabel(group.category)}
                                  </div>
                                  {meta?.type && <Badge>{meta.type}</Badge>}
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
                                  onClick={() => selectAttackCategory(group.category)}
                                >
                                  {t("Select all")}
                                </Button>
                                <Button
                                  type="button"
                                  variant="secondary"
                                  size="sm"
                                  disabled={selectedInGroup === 0}
                                  onClick={() => clearAttackCategory(group.category)}
                                >
                                  {t("Clear")}
                                </Button>
                              </div>
                            </div>
                            <div className="grid grid-cols-1 gap-2 sm:grid-cols-2 xl:grid-cols-3">
                              {group.methods.map(method => {
                                const on = selectedAttackMethodKeys.has(method.key);
                                const disabled = !executorSupportsDatasetLanguage(method.plugin);
                                const methodName = attackMethodName(method.plugin);
                                return (
                                  <button
                                    key={method.key}
                                    type="button"
                                    disabled={disabled}
                                    aria-disabled={disabled || undefined}
                                    aria-pressed={on}
                                    aria-label={t("Toggle attack method {{name}}", { name: methodName })}
                                    title={executorLanguageLabel(method.plugin)}
                                    onClick={() => toggleAttackMethod(method)}
                                    className={clsx(
                                      "min-h-16 rounded-md border p-2 text-left text-xs transition",
                                      disabled
                                        ? "cursor-not-allowed border-gray-200 bg-gray-100 text-gray-400"
                                      : on
                                        ? "bg-brand-600 border-brand-600 text-white"
                                        : "bg-white border-gray-200 text-gray-700 hover:border-gray-300",
                                    )}
                                  >
                                    <div className="flex items-start justify-between gap-2">
                                      <span className="break-all font-medium">{methodName}</span>
                                      <span className={clsx(
                                        "shrink-0 rounded px-1.5 py-0.5 text-[10px]",
                                        on ? "bg-white/15 text-white" : "bg-gray-100 text-gray-500",
                                      )}>
                                        {method.kind === "executor" ? t("Native executor") : t("Converter method")}
                                      </span>
                                    </div>
                                    <div className={clsx(
                                      "mt-1 text-[11px]",
                                      on ? "text-brand-100" : disabled ? "text-gray-400" : "text-gray-500",
                                    )}>
                                      {method.technicalCategory} · {executorLanguageLabel(method.plugin)}
                                    </div>
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
                              {attackMethodName(ex.plugin)} {t("params")}
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
                          <div className="text-xs font-medium text-gray-500 uppercase tracking-wide">{attackMethodName(c.plugin)} {t("params")}</div>
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

            <div>
              {renderScorerFields()}
            </div>
          </CardBody>
        </Card>
      )}

      {missingRunRequirements.length > 0 && (
        <div className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
          <div className="font-medium">{t("Required before creating")}</div>
          <ul className="mt-1 list-disc space-y-0.5 pl-5">
            {missingRunRequirements.map(item => <li key={String(item)}>{item}</li>)}
          </ul>
        </div>
      )}

      <div className="flex justify-end">
        <Button icon={<PlayCircle className="h-4 w-4" />} loading={submit.isPending}
          disabled={!canSubmit} onClick={() => submit.mutate()}>
          {t("Create & start")}
        </Button>
      </div>
      </div>
      <aside className="hidden xl:block">
        <Card className="sticky top-8">
          <CardHeader>
            <CardTitle>{t("Review run")}</CardTitle>
            <CardDescription>{t("Confirm the setup before starting.")}</CardDescription>
          </CardHeader>
          <CardBody className="space-y-4">
            <div className="space-y-3 text-sm">
              <SummaryRow label={t("Mode")} value={mode === "preset" ? t("Preset scenario") : t("Custom pipeline")} />
              <SummaryRow label={t("Run name")} value={name || t("Untitled run")} />
              <SummaryRow label={t("Target")} value={selectedTarget?.name ?? t("Not selected")} />
              <SummaryRow label={t("Dataset")} value={selectedDataset?.name ?? t("Not selected")} />
              <SummaryRow
                label={mode === "preset" ? t("Scenario") : t("Attack methods")}
                value={mode === "preset"
                  ? (selectedScenario?.title ?? t("Not selected"))
                  : t("{{count}} selected", { count: selectedMethodCount })}
              />
              <SummaryRow
                label={t("Scorer")}
                value={mode === "preset" && !presetScorerOverride ? t("Scenario default") : scorer.plugin}
              />
              <SummaryRow label={t("Sampling")} value={samplingSummary} />
              <SummaryRow
                label={t("Templates")}
                value={useAllAttackTemplates
                  ? t("All method templates")
                  : mode === "preset" ? t("Scenario default") : t("Active template")}
              />
            </div>
            {missingRunRequirements.length > 0 ? (
              <div className="rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-800">
                <div className="font-medium">{t("Missing requirements")}</div>
                <ul className="mt-1 list-disc space-y-0.5 pl-4">
                  {missingRunRequirements.map(item => <li key={String(item)}>{item}</li>)}
                </ul>
              </div>
            ) : (
              <div role="status" className="rounded-md border border-emerald-200 bg-emerald-50 px-3 py-2 text-xs text-emerald-800">
                {t("Ready to create.")}
              </div>
            )}
            <Button
              className="w-full justify-center"
              icon={<PlayCircle className="h-4 w-4" />}
              loading={submit.isPending}
              disabled={!canSubmit}
              onClick={() => submit.mutate()}
            >
              {t("Create & start")}
            </Button>
            {mode === "custom" && (
              <Button
                type="button"
                variant="secondary"
                className="w-full justify-center"
                icon={<Save className="h-4 w-4" />}
                disabled={!canOpenSaveScenario}
                onClick={openSaveScenarioDialog}
              >
                {t("Save as scenario")}
              </Button>
            )}
          </CardBody>
        </Card>
      </aside>
      {saveScenarioOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-gray-900/40 px-4">
          <div className="w-full max-w-lg rounded-lg bg-white shadow-xl">
            <div className="flex items-start justify-between gap-3 border-b border-gray-100 px-5 py-4">
              <div>
                <div className="text-sm font-semibold text-gray-900">{t("Save as scenario")}</div>
                <div className="mt-0.5 text-xs text-gray-500">{t("Reuse this pipeline from preset scenarios.")}</div>
              </div>
              <button
                type="button"
                aria-label={t("Close")}
                onClick={() => setSaveScenarioOpen(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
            <div className="space-y-4 px-5 py-4">
              <Field label={t("Scenario name")}>
                <Input value={saveScenarioName} onChange={e => setSaveScenarioName(e.target.value)} />
              </Field>
              <Field label={t("Description")}>
                <Textarea
                  rows={3}
                  value={saveScenarioDescription}
                  onChange={e => setSaveScenarioDescription(e.target.value)}
                />
              </Field>
              <Field label={t("Tags")} hint={t("Comma separated")}>
                <Input value={saveScenarioTags} onChange={e => setSaveScenarioTags(e.target.value)} />
              </Field>
            </div>
            <div className="flex justify-end gap-2 border-t border-gray-100 px-5 py-4">
              <Button type="button" variant="secondary" onClick={() => setSaveScenarioOpen(false)}>
                {t("Cancel")}
              </Button>
              <Button
                type="button"
                icon={<Save className="h-4 w-4" />}
                loading={saveScenario.isPending}
                disabled={!canSaveScenario}
                onClick={() => saveScenario.mutate()}
              >
                {t("Save scenario")}
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function SummaryRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-start justify-between gap-3 border-b border-gray-100 pb-2 last:border-b-0 last:pb-0">
      <span className="text-xs font-medium uppercase tracking-wide text-gray-500">{label}</span>
      <span className="max-w-[11rem] text-right text-sm font-medium text-gray-900 break-words">{value}</span>
    </div>
  );
}
