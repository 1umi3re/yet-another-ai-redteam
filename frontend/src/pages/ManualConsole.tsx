import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useNavigate, useSearchParams } from "react-router-dom";
import { useState, useEffect, useRef } from "react";
import { api } from "../lib/api";
import { Card, CardBody, CardHeader, CardTitle } from "../components/ui/Card";
import { Button } from "../components/ui/Button";
import { Input, Select, Field, Textarea } from "../components/ui/Form";
import { ConfiguredPlugin, defaultsFor, ParamField, PluginSchemas } from "../components/PluginParamsForm";
import { MessageSquare, Plus, CheckCircle, Send, Eye, Wand2, X, ClipboardCheck } from "lucide-react";
import clsx from "clsx";
import { toast } from "sonner";

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

export default function ManualConsole() {
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
  const messagesEndRef = useRef<HTMLDivElement>(null);

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

  const createRunMut = useMutation({
    mutationFn: async (body: { name: string; target_id: string }) =>
      (await api.post("/api/manual/runs", body)).data,
    onSuccess: (data) => {
      startConversationMut.mutate({ run_id: data.run_id, seed_attempt_id: null });
    },
    onError: () => toast.error("Failed to create run"),
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
    onError: () => toast.error("Failed to start conversation"),
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
    onError: () => toast.error("Failed to send message"),
  });

  const previewMut = useMutation({
    mutationFn: async () =>
      (await api.post("/api/converters/preview", { text: userInput, converters })).data,
    onSuccess: setPreview,
    onError: (e: any) => toast.error(e?.response?.data?.detail ?? "Failed to preview converters"),
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
      toast.success("Conversation evaluated");
    },
    onError: (e: any) => toast.error(e?.response?.data?.detail ?? "Failed to evaluate conversation"),
  });

  const finishRunMut = useMutation({
    mutationFn: async (run_id: string) =>
      (await api.post(`/api/manual/runs/${run_id}/finish`)).data,
    onSuccess: (_, run_id) => {
      queryClient.invalidateQueries({ queryKey: ["runs"] });
      nav(`/runs/${run_id}`);
    },
    onError: () => toast.error("Failed to finish run"),
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
    onError: () => toast.error("Failed to resume manual session"),
  });

  // Handle query param replay
  useEffect(() => {
    const runId = searchParams.get("run");
    const attemptId = searchParams.get("attempt");
    if (runId && !attemptId && !sessionState) {
      resumeMut.mutate(runId);
    } else if (runId && attemptId && !sessionState) {
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
        .catch(() => toast.error("Failed to load conversation"));
    }
  }, [searchParams, sessionState]);

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [sessionState?.messages]);

  const handleStartSession = () => {
    if (!selectedTargetId) {
      toast.error("Please select a target");
      return;
    }
    const name = runName.trim() || `Manual session ${new Date().toLocaleString()}`;
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
            Manual Console
          </h1>
          <p className="text-sm text-gray-600 mt-1">Interact with targets in real-time</p>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Start a manual session</CardTitle>
          </CardHeader>
          <CardBody>
            <div className="space-y-4">
              <Field label="Session name">
                <Input
                  placeholder="Manual session (leave blank for auto-generated name)"
                  value={runName}
                  onChange={e => setRunName(e.target.value)}
                />
              </Field>

              <Field label="Target *">
                <Select value={selectedTargetId} onChange={e => setSelectedTargetId(e.target.value)}>
                  <option value="">-- select target --</option>
                  {targets.map((t: any) => (
                    <option key={t.id} value={t.id}>{t.name}</option>
                  ))}
                </Select>
              </Field>

              <Button
                variant="primary"
                onClick={handleStartSession}
                loading={createRunMut.isPending || startConversationMut.isPending}
              >
                Start session
              </Button>
            </div>
          </CardBody>
        </Card>

        {runningManualRuns.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle>Continue running sessions</CardTitle>
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
                        {(run.target_names ?? []).join(", ") || "No target"}
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
            Manual Console
          </h1>
          <p className="text-xs text-gray-500 mt-1">
            <span className="font-mono">Run ID: {sessionState.run_id.slice(0, 8)}</span>
            {sessionState.target_name && <span className="ml-2">Target: {sessionState.target_name}</span>}
            <span className={clsx(
              "ml-2",
              sessionState.evaluated ? "text-emerald-700" : "text-amber-700",
            )}>
              {sessionState.evaluated ? "Evaluated" : "Not evaluated"}
            </span>
            {sessionState.status === "completed" && <span className="ml-2 text-emerald-700">Ended</span>}
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="secondary" onClick={handleNewConversation}
            disabled={sessionState.status === "completed"}
            icon={<Plus className="h-4 w-4" />}>
            New conversation
          </Button>
          {sessionState.status !== "completed" && (
            <Button variant="primary" onClick={handleFinishRun} icon={<CheckCircle className="h-4 w-4" />}>
              End run
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
                <div className="text-sm text-gray-400 text-center py-8">No messages yet. Start the conversation below.</div>
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
                          Original: <span className="font-mono">{msg.metadata.original_text}</span>
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
                placeholder="Type your message..."
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
                Send
              </Button>
            </div>
            </div>
          </CardBody>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Session tools</CardTitle>
          </CardHeader>
          <CardBody className="space-y-4">
            <div className="rounded-lg border border-gray-200 bg-gray-50/50 p-3 space-y-3">
              <div className="text-xs font-medium text-gray-500 uppercase tracking-wide">Benchmark prompt</div>
              <Field label="Dataset">
                <Select value={selectedDatasetId} onChange={e => setSelectedDatasetId(e.target.value)}>
                  <option value="">-- select dataset --</option>
                  {datasets.map((dataset: any) => (
                    <option key={dataset.id} value={dataset.id}>{dataset.name}</option>
                  ))}
                </Select>
              </Field>
              {selectedDatasetId && (
                <Field label="Prompt">
                  <Select value="" onChange={e => {
                    const item = datasetItems?.items?.find((it: any) => it.id === e.target.value);
                    if (item) {
                      setUserInput(item.text);
                      setPreview(null);
                    }
                  }}>
                    <option value="">-- load prompt --</option>
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
              <div className="text-xs font-medium text-gray-500 uppercase tracking-wide">Converters</div>
              <Field label="Plugins">
                <div className="flex flex-wrap gap-2">
                  {plugins?.converters?.map((plugin: string) => {
                    const active = converters.some(c => c.plugin === plugin);
                    return (
                      <button key={plugin} type="button" onClick={() => toggleConverter(plugin)}
                        className={clsx(
                          "px-2.5 py-1 text-xs rounded-full border transition",
                          active ? "bg-brand-600 border-brand-600 text-white" : "bg-white border-gray-200 text-gray-700 hover:border-gray-300",
                        )}
                      >
                        {plugin}
                      </button>
                    );
                  })}
                </div>
              </Field>

              {converters.map((converter, idx) => {
                const schema = convSchemas[converter.plugin] ?? {};
                return (
                  <div key={converter.plugin} className="rounded-lg border border-gray-200 bg-white p-3 space-y-3">
                    <div className="flex items-center justify-between">
                      <div className="text-xs font-medium text-gray-500 uppercase tracking-wide">{converter.plugin}</div>
                      <button type="button" className="text-gray-400 hover:text-gray-600"
                        onClick={() => toggleConverter(converter.plugin)}>
                        <X className="h-4 w-4" />
                      </button>
                    </div>
                    {Object.keys(schema).length === 0 ? (
                      <div className="text-xs text-gray-500">No parameters</div>
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
                  Preview
                </Button>
                <Button variant="secondary" size="sm" icon={<Wand2 className="h-4 w-4" />}
                  disabled={!preview?.transformed_text}
                  onClick={() => {
                    setUserInput(preview.transformed_text);
                    setConverters([]);
                    setPreview(null);
                  }}>
                  Apply
                </Button>
              </div>

              {preview && (
                <div className="rounded-lg border border-gray-200 bg-white p-3">
                  <div className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-2">Preview</div>
                  <pre className="text-xs whitespace-pre-wrap break-words font-mono text-gray-800 max-h-72 overflow-auto">
{preview.transformed_text}
                  </pre>
                  <div className="mt-2 text-[11px] text-gray-500">
                    Chain: {preview.converter_chain.join(" -> ") || "none"}
                  </div>
                </div>
              )}
            </div>

            <div className="rounded-lg border border-gray-200 bg-gray-50/50 p-3 space-y-3">
              <div className="flex items-center justify-between gap-3">
                <div>
                  <div className="text-xs font-medium text-gray-500 uppercase tracking-wide">Evaluator</div>
                  <div className={clsx(
                    "mt-1 text-xs",
                    sessionState.evaluated ? "text-emerald-700" : "text-amber-700",
                  )}>
                    {sessionState.evaluated
                      ? `${sessionState.scores?.length ?? 0} score${(sessionState.scores?.length ?? 0) === 1 ? "" : "s"}`
                      : "No score for this conversation"}
                  </div>
                </div>
                <ClipboardCheck className="h-4 w-4 text-gray-400" />
              </div>

              <Field label="Scorer">
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
                Evaluate
              </Button>

              {!!sessionState.scores?.length && (
                <div className="space-y-2">
                  {sessionState.scores.map(score => (
                    <div key={score.id} className="rounded border border-gray-200 bg-white px-2 py-2">
                      <div className="flex items-center justify-between gap-2 text-xs">
                        <span className="font-medium text-gray-700">{score.scorer}</span>
                        <span className="text-gray-500">{score.value?.attack_success ? "complied" : "refused"}</span>
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
