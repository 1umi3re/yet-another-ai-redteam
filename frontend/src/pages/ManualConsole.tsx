import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useNavigate, useSearchParams } from "react-router-dom";
import { useEffect, useMemo, useRef, useState } from "react";
import { api } from "../lib/api";
import { Card, CardBody, CardHeader, CardTitle } from "../components/ui/Card";
import { Button } from "../components/ui/Button";
import { Input, Select, Field, Textarea } from "../components/ui/Form";
import { ConfiguredPlugin, defaultsFor, ParamField, PluginSchemas } from "../components/PluginParamsForm";
import { MessageSquare, Plus, CheckCircle, Send, Eye, Wand2, X, ClipboardCheck } from "lucide-react";
import clsx from "clsx";
import { toast } from "sonner";
import { useI18n } from "../lib/i18n";

type SessionState = {
  run_id: string;
  attempt_id: string;
  status?: string;
  target_id?: string;
  target_name?: string;
  evaluated?: boolean;
  scores?: any[];
  messages: Array<{ role: string; text: string; metadata?: Record<string, any> }>;
};

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

export default function ManualConsole() {
  const { t } = useI18n();
  const nav = useNavigate();
  const [searchParams] = useSearchParams();
  const queryClient = useQueryClient();

  const [sessionState, setSessionState] = useState<SessionState | null>(null);
  const [selectedTargetId, setSelectedTargetId] = useState("");
  const [runName, setRunName] = useState("");
  const [userInput, setUserInput] = useState("");
  const [converters, setConverters] = useState<ConfiguredPlugin[]>([]);
  const [scorer, setScorer] = useState<ConfiguredPlugin>({ plugin: "refusal", params: {} });
  const [preview, setPreview] = useState<any>(null);
  const [selectedDatasetId, setSelectedDatasetId] = useState("");
  const [selectedPromptId, setSelectedPromptId] = useState("");
  const [converterSearch, setConverterSearch] = useState("");
  const [converterCategory, setConverterCategory] = useState("all");
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const urlBootstrappedRef = useRef(false);

  const { data: targets = [] } = useQuery({
    queryKey: ["targets"],
    queryFn: async () => (await api.get("/api/targets")).data,
  });
  const { data: runs = [] } = useQuery({
    queryKey: ["runs"],
    queryFn: async () => (await api.get("/api/runs")).data,
    refetchInterval: sessionState ? false : 2000,
  });
  const { data: datasets = [] } = useQuery({
    queryKey: ["datasets"],
    queryFn: async () => (await api.get("/api/datasets")).data,
  });
  const { data: datasetItems } = useQuery({
    queryKey: ["dataset-items", selectedDatasetId],
    queryFn: async () => (await api.get(`/api/datasets/${selectedDatasetId}/items?limit=100`)).data,
    enabled: !!selectedDatasetId,
  });
  const { data: plugins } = useQuery({
    queryKey: ["plugins"],
    queryFn: async () => (await api.get("/api/plugins")).data,
  });
  const convSchemas: PluginSchemas = plugins?.params?.converters ?? {};
  const scorerSchemas: PluginSchemas = plugins?.params?.scorers ?? {};
  const scorerSchema = scorerSchemas[scorer.plugin] ?? {};
  const availableConverters: string[] = plugins?.converters ?? [];
  const converterCategories: Record<string, string> = plugins?.converter_categories ?? {};
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
    const counts: Record<string, number> = { all: availableConverters.length, selected: converters.length };
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
  }, [availableConverters, converterCategories, converterCategory, converterSearch, selectedConverterNames]);

  const converterCategoryLabel = (category: string) => {
    if (category === "all") return t("All");
    if (category === "selected") return t("Selected");
    return t(CONVERTER_CATEGORY_LABELS[category] ?? category);
  };

  const createRunMut = useMutation({
    mutationFn: async (body: { name: string; target_id: string }) =>
      (await api.post("/api/manual/runs", body)).data,
    onSuccess: (data) => {
      startConversationMut.mutate({ run_id: data.run_id, seed_attempt_id: null });
    },
    onError: () => toast.error(t("Failed to create run")),
  });

  const startConversationMut = useMutation({
    mutationFn: async ({ run_id, seed_attempt_id }: { run_id: string; seed_attempt_id: string | null }) =>
      (await api.post(`/api/manual/runs/${run_id}/conversations`, { seed_attempt_id })).data,
    onSuccess: (data, vars) => {
      setSessionState({
        run_id: vars.run_id,
        attempt_id: data.attempt_id,
        status: "running",
        evaluated: false,
        scores: [],
        messages: data.conversation || [],
      });
    },
    onError: () => toast.error(t("Failed to start conversation")),
  });

  const sendTurnMut = useMutation({
    mutationFn: async ({
      run_id, attempt_id, text, converters,
    }: {
      run_id: string; attempt_id: string; text: string; converters: ConfiguredPlugin[];
    }) =>
      (await api.post(`/api/manual/runs/${run_id}/conversations/${attempt_id}/turn`, { text, converters })).data,
    onSuccess: (data) => {
      setSessionState(prev => prev ? {
        ...prev,
        messages: data.conversation,
        evaluated: false,
        scores: [],
      } : null);
      setUserInput("");
      setPreview(null);
    },
    onError: () => toast.error(t("Failed to send message")),
  });

  const previewMut = useMutation({
    mutationFn: async () =>
      (await api.post("/api/converters/preview", { text: userInput, converters })).data,
    onSuccess: setPreview,
    onError: (e: any) => toast.error(e?.response?.data?.detail ?? t("Failed to preview converters")),
  });

  const evaluateMut = useMutation({
    mutationFn: async ({ run_id, attempt_id }: { run_id: string; attempt_id: string }) =>
      (await api.post(`/api/manual/runs/${run_id}/conversations/${attempt_id}/evaluate`, scorer)).data,
    onSuccess: (data) => {
      setSessionState(prev => prev ? {
        ...prev,
        evaluated: data.evaluated,
        scores: data.scores || [data.score],
      } : null);
      toast.success(t("Conversation evaluated"));
    },
    onError: (e: any) => toast.error(e?.response?.data?.detail ?? t("Failed to evaluate conversation")),
  });

  const finishRunMut = useMutation({
    mutationFn: async (run_id: string) =>
      (await api.post(`/api/manual/runs/${run_id}/finish`)).data,
    onSuccess: (_, run_id) => {
      queryClient.invalidateQueries({ queryKey: ["runs"] });
      nav(`/runs/${run_id}`);
    },
    onError: () => toast.error(t("Failed to finish run")),
  });

  const resumeMut = useMutation({
    mutationFn: async (run_id: string) =>
      (await api.get(`/api/manual/runs/${run_id}/session`)).data,
    onSuccess: (data) => {
      setSessionState({
        run_id: data.run_id,
        attempt_id: data.attempt_id,
        status: data.status,
        target_id: data.target_id,
        target_name: data.target_name,
        evaluated: data.evaluated,
        scores: data.scores || [],
        messages: data.conversation || [],
      });
    },
    onError: () => toast.error(t("Failed to resume manual session")),
  });

  // Handle query param replay. Runs once when URL params are present so the
  // effect doesn't re-fire (and re-trigger resume / fetch) on every chat turn.
  useEffect(() => {
    if (urlBootstrappedRef.current) return;
    const runId = searchParams.get("run");
    const attemptId = searchParams.get("attempt");
    if (!runId) return;
    urlBootstrappedRef.current = true;
    if (!attemptId) {
      resumeMut.mutate(runId);
    } else {
      api.get(`/api/runs/${runId}/attempts/${attemptId}/conversation`)
        .then(res => {
          setSessionState({
            run_id: runId,
            attempt_id: attemptId,
            status: "running",
            evaluated: false,
            scores: [],
            messages: res.data.messages || [],
          });
        })
        .catch(() => toast.error(t("Failed to load conversation")));
    }
  }, [searchParams]);

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [sessionState?.messages]);

  const handleStartSession = () => {
    if (!selectedTargetId) {
      toast.error(t("Please select a target"));
      return;
    }
    const name = runName.trim() || `${t("Manual Console")} ${new Date().toLocaleString()}`;
    createRunMut.mutate({ name, target_id: selectedTargetId });
  };

  const handleSendMessage = () => {
    if (!userInput.trim() || !sessionState || sessionState.status === "completed") return;
    sendTurnMut.mutate({
      run_id: sessionState.run_id,
      attempt_id: sessionState.attempt_id,
      text: userInput,
      converters,
    });
  };

  const toggleConverter = (plugin: string) => {
    setConverters(prev => {
      const existing = prev.findIndex(c => c.plugin === plugin);
      if (existing >= 0) return prev.filter((_, i) => i !== existing);
      return [...prev, { plugin, params: defaultsFor(convSchemas[plugin]) }];
    });
    setPreview(null);
  };

  const updateConverterParam = (idx: number, key: string, value: any) => {
    setConverters(prev => prev.map((c, i) => (
      i === idx ? { ...c, params: { ...c.params, [key]: value } } : c
    )));
    setPreview(null);
  };

  const setScorerPlugin = (plugin: string) => {
    setScorer({ plugin, params: defaultsFor(scorerSchemas[plugin]) });
  };

  const updateScorerParam = (key: string, value: any) => {
    setScorer(prev => ({ ...prev, params: { ...prev.params, [key]: value } }));
  };

  const handleNewConversation = () => {
    if (!sessionState) return;
    startConversationMut.mutate({ run_id: sessionState.run_id, seed_attempt_id: null });
  };

  const handleFinishRun = () => {
    if (!sessionState) return;
    finishRunMut.mutate(sessionState.run_id);
  };

  const handleEvaluate = () => {
    if (!sessionState || sessionState.messages.length === 0) return;
    evaluateMut.mutate({
      run_id: sessionState.run_id,
      attempt_id: sessionState.attempt_id,
    });
  };

  const runningManualRuns = runs.filter((r: any) => r.kind === "manual" && r.status === "running");

  if (!sessionState) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold tracking-tight flex items-center gap-2">
            <MessageSquare className="h-6 w-6" />
            {t("Manual Console")}
          </h1>
          <p className="text-sm text-gray-600 mt-1">{t("Interact with targets in real-time")}</p>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>{t("Start a manual session")}</CardTitle>
          </CardHeader>
          <CardBody>
            <div className="space-y-4">
              <Field label={t("Session name")}>
                <Input
                  placeholder={t("Manual session (leave blank for auto-generated name)")}
                  value={runName}
                  onChange={e => setRunName(e.target.value)}
                />
              </Field>

              <Field label={t("Target *")}>
                <Select value={selectedTargetId} onChange={e => setSelectedTargetId(e.target.value)}>
                  <option value="">{t("-- select target --")}</option>
                  {targets.map((target: any) => (
                    <option key={target.id} value={target.id}>{target.name}</option>
                  ))}
                </Select>
              </Field>

              <Button
                variant="primary"
                onClick={handleStartSession}
                loading={createRunMut.isPending || startConversationMut.isPending}
              >
                {t("Start session")}
              </Button>
            </div>
          </CardBody>
        </Card>

        {runningManualRuns.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle>{t("Continue running sessions")}</CardTitle>
            </CardHeader>
            <CardBody className="space-y-2">
              {runningManualRuns.map((run: any) => (
                <button key={run.id} type="button"
                  onClick={() => resumeMut.mutate(run.id)}
                  className="w-full rounded-lg border border-gray-200 px-3 py-2 text-left hover:border-gray-300 hover:bg-gray-50 transition">
                  <div className="flex items-center justify-between gap-3">
                    <div>
                      <div className="text-sm font-medium text-gray-900">{run.name}</div>
                      <div className="text-xs text-gray-500 mt-0.5">
                        {(run.target_names ?? []).join(", ") || t("No target")}
                      </div>
                    </div>
                    <MessageSquare className="h-4 w-4 text-gray-400" />
                  </div>
                </button>
              ))}
            </CardBody>
          </Card>
        )}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight flex items-center gap-2">
            <MessageSquare className="h-6 w-6" />
            {t("Manual Console")}
          </h1>
          <p className="text-xs text-gray-500 mt-1">
            <span className="font-mono">{t("Run ID: {{id}}", { id: sessionState.run_id.slice(0, 8) })}</span>
            {sessionState.target_name && <span className="ml-2">{t("Target: {{target}}", { target: sessionState.target_name })}</span>}
            <span className={clsx(
              "ml-2",
              sessionState.evaluated ? "text-emerald-700" : "text-amber-700",
            )}>
              {sessionState.evaluated ? t("Evaluated") : t("Not evaluated")}
            </span>
            {sessionState.status === "completed" && <span className="ml-2 text-emerald-700">{t("Ended")}</span>}
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="secondary" onClick={handleNewConversation}
            disabled={sessionState.status === "completed"}
            icon={<Plus className="h-4 w-4" />}>
            {t("New conversation")}
          </Button>
          {sessionState.status !== "completed" && (
            <Button variant="primary" onClick={handleFinishRun} icon={<CheckCircle className="h-4 w-4" />}>
              {t("End run")}
            </Button>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-[minmax(0,1fr)_360px] gap-4">
        <Card>
          <CardBody>
            <div className="flex flex-col h-[600px]">
            <div className="flex-1 overflow-y-auto border border-gray-200 rounded-lg p-4 bg-gray-50 space-y-3">
              {sessionState.messages.length === 0 ? (
                <div className="text-sm text-gray-400 text-center py-8">{t("No messages yet. Start the conversation below.")}</div>
              ) : (
                sessionState.messages.map((msg, i) => (
                  <div key={i} className={clsx("flex", msg.role === "user" ? "justify-end" : "justify-start")}>
                    <div className={clsx(
                      "max-w-[80%] rounded-lg px-3 py-2",
                      msg.role === "user"
                        ? "bg-gray-100 border border-gray-200"
                        : "bg-white border border-gray-300"
                    )}>
                      <div className="text-[10px] uppercase tracking-wider font-semibold text-gray-500 mb-1">
                        {msg.role}
                      </div>
                      <pre className="text-xs whitespace-pre-wrap break-words font-mono text-gray-800">
{msg.text}
                      </pre>
                      {msg.role === "user" && msg.metadata?.original_text && (
                        <div className="mt-2 rounded border border-gray-200 bg-white/70 px-2 py-1 text-[11px] text-gray-500">
                          {t("Original")}: <span className="font-mono">{msg.metadata.original_text}</span>
                        </div>
                      )}
                    </div>
                  </div>
                ))
              )}
              <div ref={messagesEndRef} />
            </div>

            <div className="flex gap-2 mt-3">
              <Textarea
                rows={3}
                placeholder={t("Type your message...")}
                value={userInput}
                onChange={e => setUserInput(e.target.value)}
                onKeyDown={e => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    handleSendMessage();
                  }
                }}
                className="flex-1"
              />
              <Button
                variant="primary"
                onClick={handleSendMessage}
                loading={sendTurnMut.isPending}
                disabled={!userInput.trim() || sessionState.status === "completed"}
                icon={<Send className="h-4 w-4" />}
              >
                {t("Send")}
              </Button>
            </div>
            </div>
          </CardBody>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>{t("Session tools")}</CardTitle>
          </CardHeader>
          <CardBody className="space-y-4">
            <div className="rounded-lg border border-gray-200 bg-gray-50/50 p-3 space-y-3">
              <div className="text-xs font-medium text-gray-500 uppercase tracking-wide">{t("Benchmark prompt")}</div>
              <Field label={t("Dataset")}>
                <Select value={selectedDatasetId} onChange={e => {
                  setSelectedDatasetId(e.target.value);
                  setSelectedPromptId("");
                }}>
                  <option value="">{t("-- select dataset --")}</option>
                  {datasets.map((dataset: any) => (
                    <option key={dataset.id} value={dataset.id}>{dataset.name}</option>
                  ))}
                </Select>
              </Field>
              {selectedDatasetId && (
                <Field label={t("Prompt")}>
                  <Select value={selectedPromptId} onChange={e => {
                    const id = e.target.value;
                    setSelectedPromptId(id);
                    const item = datasetItems?.items?.find((it: any) => it.id === id);
                    if (item) {
                      setUserInput(item.text);
                      setPreview(null);
                    }
                  }}>
                    <option value="">{t("-- load prompt --")}</option>
                    {datasetItems?.items?.map((item: any, idx: number) => (
                      <option key={`${item.id}-${idx}`} value={item.id}>
                        {item.id}: {item.text.slice(0, 80)}
                      </option>
                    ))}
                  </Select>
                </Field>
              )}
            </div>

            <div className="rounded-lg border border-gray-200 bg-gray-50/50 p-3 space-y-3">
              <div className="text-xs font-medium text-gray-500 uppercase tracking-wide">{t("Converters")}</div>
              <Field label={t("Search converters")}>
                <Input
                  value={converterSearch}
                  onChange={e => setConverterSearch(e.target.value)}
                  placeholder={t("Filter by name...")}
                />
              </Field>

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

              <div>
                <div className="mb-1 text-[11px] text-gray-500">
                  {t("Showing {{count}} of {{total}} converters", {
                    count: filteredConverters.length,
                    total: availableConverters.length,
                  })}
                </div>
                <div className="max-h-56 overflow-y-auto rounded-lg border border-gray-200 bg-white p-2">
                  {filteredConverters.length ? (
                    <div className="grid grid-cols-1 gap-1">
                      {filteredConverters.map(plugin => {
                        const active = selectedConverterNames.has(plugin);
                        const category = converterCategories[plugin] ?? "other";
                        return (
                          <button
                            key={plugin}
                            type="button"
                            onClick={() => toggleConverter(plugin)}
                            className={clsx(
                              "flex items-center justify-between gap-3 rounded-md border px-2.5 py-2 text-left text-xs transition",
                              active
                                ? "border-brand-500 bg-brand-50 text-brand-800"
                                : "border-transparent text-gray-700 hover:border-gray-200 hover:bg-gray-50",
                            )}
                          >
                            <span className="font-mono">{plugin}</span>
                            <span className="shrink-0 text-[10px] uppercase tracking-wide text-gray-400">
                              {converterCategoryLabel(category)}
                            </span>
                          </button>
                        );
                      })}
                    </div>
                  ) : (
                    <div className="py-6 text-center text-xs text-gray-500">{t("No converters match.")}</div>
                  )}
                </div>
              </div>

              {converters.map((converter, idx) => {
                const schema = convSchemas[converter.plugin] ?? {};
                return (
                  <div key={converter.plugin} className="rounded-lg border border-gray-200 bg-white p-3 space-y-3">
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="text-xs font-medium text-gray-500 uppercase tracking-wide">{converter.plugin}</div>
                        <div className="mt-0.5 text-[10px] text-gray-400">
                          {converterCategoryLabel(converterCategories[converter.plugin] ?? "other")}
                        </div>
                      </div>
                      <button type="button" className="text-gray-400 hover:text-gray-600"
                        onClick={() => toggleConverter(converter.plugin)}>
                        <X className="h-4 w-4" />
                      </button>
                    </div>
                    {Object.keys(schema).length === 0 ? (
                      <div className="text-xs text-gray-500">{t("No parameters")}</div>
                    ) : Object.entries(schema).map(([key, schema]) => (
                      <ParamField key={key} name={key} schema={schema} targets={targets}
                        value={converter.params[key]}
                        onChange={value => updateConverterParam(idx, key, value)} />
                    ))}
                  </div>
                );
              })}

              <div className="flex gap-2">
                <Button variant="secondary" size="sm" icon={<Eye className="h-4 w-4" />}
                  loading={previewMut.isPending}
                  disabled={!userInput.trim() || converters.length === 0 || sessionState.status === "completed"}
                  onClick={() => previewMut.mutate()}>
                  {t("Preview")}
                </Button>
                <Button variant="secondary" size="sm" icon={<Wand2 className="h-4 w-4" />}
                  disabled={!preview?.transformed_text}
                  onClick={() => {
                    setUserInput(preview.transformed_text);
                    setConverters([]);
                    setPreview(null);
                  }}>
                  {t("Apply")}
                </Button>
              </div>

              {preview && (
                <div className="rounded-lg border border-gray-200 bg-white p-3">
                  <div className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-2">{t("Preview")}</div>
                  <pre className="text-xs whitespace-pre-wrap break-words font-mono text-gray-800 max-h-72 overflow-auto">
{preview.transformed_text}
                  </pre>
                  <div className="mt-2 text-[11px] text-gray-500">
                    {t("Chain")}: {preview.converter_chain.join(" -> ") || t("none")}
                  </div>
                </div>
              )}
            </div>

            <div className="rounded-lg border border-gray-200 bg-gray-50/50 p-3 space-y-3">
              <div className="flex items-center justify-between gap-3">
                <div>
                  <div className="text-xs font-medium text-gray-500 uppercase tracking-wide">{t("Evaluator")}</div>
                  <div className={clsx(
                    "mt-1 text-xs",
                    sessionState.evaluated ? "text-emerald-700" : "text-amber-700",
                  )}>
                    {sessionState.evaluated
                      ? t((sessionState.scores?.length ?? 0) === 1 ? "{{count}} score" : "{{count}} scores", { count: sessionState.scores?.length ?? 0 })
                      : t("No score for this conversation")}
                  </div>
                </div>
                <ClipboardCheck className="h-4 w-4 text-gray-400" />
              </div>

              <Field label={t("Scorer")}>
                <Select value={scorer.plugin} onChange={e => setScorerPlugin(e.target.value)}>
                  {plugins?.scorers?.map((plugin: string) => (
                    <option key={plugin} value={plugin}>{plugin}</option>
                  ))}
                </Select>
              </Field>

              {Object.keys(scorerSchema).length > 0 && (
                <div className="space-y-3">
                  {Object.entries(scorerSchema).map(([key, schema]) => (
                    <ParamField key={key} name={key} schema={schema} targets={targets}
                      value={scorer.params[key]}
                      onChange={value => updateScorerParam(key, value)} />
                  ))}
                </div>
              )}

              <Button variant="secondary" size="sm" icon={<ClipboardCheck className="h-4 w-4" />}
                loading={evaluateMut.isPending}
                disabled={sessionState.messages.length === 0}
                onClick={handleEvaluate}>
                {t("Evaluate")}
              </Button>

              {!!sessionState.scores?.length && (
                <div className="space-y-2">
                  {sessionState.scores.map(score => (
                    <div key={score.id} className="rounded border border-gray-200 bg-white px-2 py-2">
                      <div className="flex items-center justify-between gap-2 text-xs">
                        <span className="font-medium text-gray-700">{score.scorer}</span>
                        <span className="text-gray-500">{score.value?.attack_success ? t("complied") : t("refused")}</span>
                      </div>
                      {score.rationale && (
                        <div className="mt-1 text-[11px] text-gray-600 line-clamp-3">{score.rationale}</div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </CardBody>
        </Card>
      </div>
    </div>
  );
}
