import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Fragment, useState } from "react";
import { api } from "../lib/api";
import { Card, CardBody, CardHeader, CardTitle, CardDescription } from "../components/ui/Card";
import { Button } from "../components/ui/Button";
import { Input, Select, Field } from "../components/ui/Form";
import { EmptyState } from "../components/ui/EmptyState";
import { Badge } from "../components/ui/Badge";
import { Target as TargetIcon, Plus, Trash2, CheckCircle2, AlertCircle, Save, Sparkles } from "lucide-react";
import { toast } from "sonner";
import { useI18n } from "../lib/i18n";

type T = { id: string; name: string; plugin: string; params: Record<string, any>; has_secret: boolean };
type CheckResult = {
  ok: boolean;
  latency_ms: number | null;
  response_preview: string | null;
  stream_ok: boolean | null;
  stream_error: string | null;
  error: string | null;
  model_echo: string | null;
};
type ServiceContextTemplate = {
  id: string; version: number; status: string; is_active: boolean; topic: string | null;
  language: string | null;
  template: string | null; rationale: string | null; target_model: string; generator_model: string;
  verification_passed: boolean; error: string | null; created_at: string | null;
};

export default function Targets() {
  const { t } = useI18n();
  const qc = useQueryClient();
  const { data, isLoading } = useQuery({
    queryKey: ["targets"],
    queryFn: async () => (await api.get<T[]>("/api/targets")).data,
  });
  const [form, setForm] = useState({
    name: "", plugin: "openai_compat", base_url: "", model: "", api_key: "",
    timeout: "", max_concurrency: "", max_input_chars: "",
  });
  const [checkResults, setCheckResults] = useState<Record<string, CheckResult | null>>({});
  const [expandedChecks, setExpandedChecks] = useState<Record<string, boolean>>({});
  const [deleteTarget, setDeleteTarget] = useState<T | null>(null);
  const [templateTarget, setTemplateTarget] = useState<T | null>(null);
  const [generatorConfigId, setGeneratorConfigId] = useState("");
  const [maxTemplateCandidates, setMaxTemplateCandidates] = useState("10");
  const [templateTraces, setTemplateTraces] = useState<Record<string, any>>({});
  const [expandedTraceId, setExpandedTraceId] = useState<string | null>(null);
  const [limitDrafts, setLimitDrafts] = useState<Record<string, { timeout: string; max_concurrency: string; max_input_chars: string }>>({});
  const timeoutValue = form.timeout ? Number(form.timeout) : null;
  const maxConcurrencyValue = form.max_concurrency ? Number(form.max_concurrency) : null;
  const maxInputCharsValue = form.max_input_chars ? Number(form.max_input_chars) : null;
  const validLimits = (timeoutValue === null || timeoutValue > 0)
    && (maxConcurrencyValue === null || (Number.isInteger(maxConcurrencyValue) && maxConcurrencyValue > 0))
    && (maxInputCharsValue === null || (Number.isInteger(maxInputCharsValue) && maxInputCharsValue > 0));
  const missingCreateFields = [
    !form.name && t("Name"),
    !form.base_url && t("Base URL"),
    !form.model && t("Model"),
    !form.api_key && t("API key"),
    !validLimits && t("Valid positive limits"),
  ].filter(Boolean);
  
  const create = useMutation({
    mutationFn: async () => {
      const params: Record<string, any> = { name: form.name, base_url: form.base_url, model: form.model };
      if (timeoutValue !== null) params.timeout = timeoutValue;
      if (maxConcurrencyValue !== null) params.max_concurrency = maxConcurrencyValue;
      if (maxInputCharsValue !== null) {
        params.max_input_chars = maxInputCharsValue;
        params.input_limit_unit = "characters";
      }
      return api.post("/api/targets", {
        name: form.name, plugin: form.plugin,
        params,
        secret: { api_key: form.api_key },
      });
    },
    onSuccess: () => {
      toast.success(t("Target created"));
      setForm({
        name: "", plugin: "openai_compat", base_url: "", model: "", api_key: "",
        timeout: "", max_concurrency: "", max_input_chars: "",
      });
      qc.invalidateQueries({ queryKey: ["targets"] });
    },
    onError: (e: any) => toast.error(e?.response?.data?.detail ?? t("Failed to create")),
  });
  const del = useMutation({
    mutationFn: async (id: string) => api.delete(`/api/targets/${id}`),
    onSuccess: () => {
      toast.success(t("Deleted"));
      setDeleteTarget(null);
      qc.invalidateQueries({ queryKey: ["targets"] });
    },
  });
  const updateLimits = useMutation({
    mutationFn: async ({ id, draft }: { id: string; draft: { timeout: string; max_concurrency: string; max_input_chars: string } }) => {
      const timeout = draft.timeout.trim();
      const maxConcurrency = draft.max_concurrency.trim();
      const maxInputChars = draft.max_input_chars.trim();
      const payload = {
        timeout: timeout ? Number(timeout) : null,
        max_concurrency: maxConcurrency ? Number(maxConcurrency) : null,
        max_input_chars: maxInputChars ? Number(maxInputChars) : null,
        input_limit_unit: maxInputChars ? "characters" : null,
      };
      return api.patch<T>(`/api/targets/${id}/limits`, payload);
    },
    onSuccess: ({ data: target }) => {
      toast.success(t("Limits updated"));
      setLimitDrafts(prev => ({
        ...prev,
        [target.id]: {
          timeout: target.params?.timeout != null ? String(target.params.timeout) : "",
          max_concurrency: target.params?.max_concurrency != null ? String(target.params.max_concurrency) : "",
          max_input_chars: target.params?.max_input_chars != null ? String(target.params.max_input_chars) : "",
        },
      }));
      qc.invalidateQueries({ queryKey: ["targets"] });
    },
    onError: (e: any) => toast.error(e?.response?.data?.detail ?? t("Failed to update limits")),
  });
  const check = useMutation({
    mutationFn: async (id: string) => {
      const resp = await api.post<CheckResult>(`/api/targets/${id}/check`);
      return { id, result: resp.data };
    },
    onSuccess: ({ id, result }) => {
      setCheckResults((prev) => ({ ...prev, [id]: result }));
      if (result.ok) {
        toast.success(t("Target OK ({{latency}}ms)", { latency: result.latency_ms ?? "-" }));
      } else {
        toast.error(t("Target check failed: {{error}}", { error: result.error ?? "" }));
      }
    },
    onError: (e: any, id) => {
      const detail = e?.response?.data?.detail ?? t("Check failed");
      setCheckResults(prev => ({
        ...prev,
        [id]: {
          ok: false,
          latency_ms: null,
          response_preview: null,
          stream_ok: null,
          stream_error: null,
          error: detail,
          model_echo: null,
        },
      }));
      toast.error(detail);
    },
  });
  const { data: templateVersions, isLoading: templatesLoading } = useQuery({
    queryKey: ["service-context-templates", templateTarget?.id],
    queryFn: async () => (
      await api.get<ServiceContextTemplate[]>(`/api/targets/${templateTarget!.id}/service-context-templates`)
    ).data,
    enabled: !!templateTarget,
  });
  const generateTemplate = useMutation({
    mutationFn: async () => api.post<ServiceContextTemplate>(
      `/api/targets/${templateTarget!.id}/service-context-templates/generate`,
      { generator_config_id: generatorConfigId, max_candidates: Number(maxTemplateCandidates) },
    ),
    onSuccess: ({ data: generated }) => {
      if (generated.status === "succeeded") toast.success(t("Topic-bridge template generated"));
      else toast.error(generated.error ?? t("Template generation failed"));
      qc.invalidateQueries({ queryKey: ["service-context-templates", templateTarget?.id] });
    },
    onError: (e: any) => toast.error(e?.response?.data?.detail ?? t("Template generation failed")),
  });
  const activateTemplate = useMutation({
    mutationFn: async (templateId: string) => api.post(
      `/api/targets/${templateTarget!.id}/service-context-templates/${templateId}/activate`,
    ),
    onSuccess: () => {
      toast.success(t("Template activated"));
      qc.invalidateQueries({ queryKey: ["service-context-templates", templateTarget?.id] });
    },
    onError: (e: any) => toast.error(e?.response?.data?.detail ?? t("Failed to activate template")),
  });
  const loadTemplateTrace = useMutation({
    mutationFn: async (templateId: string) => (
      await api.get(`/api/targets/${templateTarget!.id}/service-context-templates/${templateId}/trace`)
    ).data,
    onSuccess: (trace, templateId) => {
      setTemplateTraces(prev => ({ ...prev, [templateId]: trace }));
      setExpandedTraceId(templateId);
    },
    onError: (e: any) => toast.error(e?.response?.data?.detail ?? t("Failed to load generation trace")),
  });

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">{t("Targets")}</h1>
        <p className="text-sm text-gray-500 mt-1">{t("Configure AI applications to test against.")}</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>{t("New target")}</CardTitle>
          <CardDescription>{t("OpenAI-compatible or Anthropic-compatible HTTP endpoint.")}</CardDescription>
        </CardHeader>
        <CardBody>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Field label={t("Name")} required><Input placeholder="e.g. gpt-4o-mini" value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} /></Field>
            <Field label={t("Plugin")}>
              <Select value={form.plugin} onChange={e => setForm({ ...form, plugin: e.target.value })}>
                <option value="openai_compat">openai_compat</option>
                <option value="openai_compat_new_session">openai_compat_new_session</option>
                <option value="anthropic_compat">anthropic_compat</option>
              </Select>
            </Field>
            <Field label={t("Base URL")} hint="e.g. https://api.openai.com/v1" required><Input value={form.base_url} onChange={e => setForm({ ...form, base_url: e.target.value })} /></Field>
            <Field label={t("Model")} required><Input placeholder="e.g. gpt-4o-mini" value={form.model} onChange={e => setForm({ ...form, model: e.target.value })} /></Field>
            <Field label={t("Request timeout")} hint={t("Seconds. Blank uses the target plugin default.")}>
              <Input
                type="number"
                min="1"
                step="1"
                placeholder={form.plugin === "anthropic_compat" ? "60" : "300"}
                value={form.timeout}
                onChange={e => setForm({ ...form, timeout: e.target.value })}
              />
            </Field>
            <Field label={t("Per-target concurrency")} hint={t("Max concurrent attempts for this target. Blank follows run concurrency.")}>
              <Input
                type="number"
                min="1"
                step="1"
                placeholder={t("run limit")}
                value={form.max_concurrency}
                onChange={e => setForm({ ...form, max_concurrency: e.target.value })}
              />
            </Field>
            <Field label={t("Input character limit")} hint={t("Blank means no per-message input limit.")}>
              <Input
                type="number"
                min="1"
                step="1"
                placeholder="200"
                value={form.max_input_chars}
                onChange={e => setForm({ ...form, max_input_chars: e.target.value })}
              />
            </Field>
            <div className="md:col-span-2">
              <Field label={t("API key")} hint={t("Stored encrypted. Never exposed via API.")} required>
                <Input type="password" value={form.api_key} onChange={e => setForm({ ...form, api_key: e.target.value })} />
              </Field>
            </div>
          </div>
          <div className="mt-5 flex flex-wrap items-center justify-end gap-3">
            {missingCreateFields.length > 0 && (
              <div className="mr-auto rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-800">
                {t("Required before creating: {{fields}}", { fields: missingCreateFields.join(", ") })}
              </div>
            )}
            <Button
              icon={<Plus className="h-4 w-4" />}
              loading={create.isPending}
              onClick={() => create.mutate()}
              disabled={!form.name || !form.base_url || !form.model || !form.api_key || !validLimits}
            >{t("Create target")}</Button>
          </div>
        </CardBody>
      </Card>

      <Card>
        <CardHeader><CardTitle>{t("Configured targets")}</CardTitle></CardHeader>
        {isLoading ? (
          <CardBody className="text-sm text-gray-500">{t("Loading…")}</CardBody>
        ) : !data?.length ? (
          <EmptyState
            icon={<TargetIcon className="h-10 w-10" />}
            title={t("No targets yet")}
            description={t("Add your first AI endpoint above to start running tests.")}
          />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 text-gray-600 text-xs uppercase tracking-wider">
                <tr>
                  <th className="text-left px-5 py-2.5">{t("Name")}</th>
                  <th className="text-left px-5 py-2.5">{t("Plugin")}</th>
                  <th className="text-left px-5 py-2.5">{t("Model")}</th>
                  <th className="text-left px-5 py-2.5">{t("Limits")}</th>
                  <th className="text-left px-5 py-2.5">{t("Secret")}</th>
                  <th className="px-5 py-2.5"></th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {data.map(target => {
                  const result = checkResults[target.id];
                  const expanded = expandedChecks[target.id];
                  const draft = limitDrafts[target.id] ?? {
                    timeout: target.params?.timeout != null ? String(target.params.timeout) : "",
                    max_concurrency: target.params?.max_concurrency != null ? String(target.params.max_concurrency) : "",
                    max_input_chars: target.params?.max_input_chars != null ? String(target.params.max_input_chars) : "",
                  };
                  const draftTimeout = draft.timeout ? Number(draft.timeout) : null;
                  const draftMaxConcurrency = draft.max_concurrency ? Number(draft.max_concurrency) : null;
                  const draftMaxInputChars = draft.max_input_chars ? Number(draft.max_input_chars) : null;
                  const draftValid = (draftTimeout === null || draftTimeout > 0)
                    && (draftMaxConcurrency === null || (Number.isInteger(draftMaxConcurrency) && draftMaxConcurrency > 0))
                    && (draftMaxInputChars === null || (Number.isInteger(draftMaxInputChars) && draftMaxInputChars > 0));
                  return (
                    <Fragment key={target.id}>
                      <tr>
                        <td className="px-5 py-3 font-medium">{target.name}</td>
                        <td className="px-5 py-3"><Badge tone="indigo">{target.plugin}</Badge></td>
                        <td className="px-5 py-3 font-mono text-xs text-gray-700">{target.params?.model}</td>
                        <td className="px-5 py-3">
                          <div className="flex min-w-[34rem] items-end gap-2">
                            <Field label={t("Timeout")}>
                              <Input
                                type="number"
                                min="1"
                                step="1"
                                placeholder={t("plugin default")}
                                value={draft.timeout}
                                onChange={e => setLimitDrafts(prev => ({
                                  ...prev,
                                  [target.id]: { ...draft, timeout: e.target.value },
                                }))}
                              />
                            </Field>
                            <Field label={t("Concurrency")}>
                              <Input
                                type="number"
                                min="1"
                                step="1"
                                placeholder={t("run limit")}
                                value={draft.max_concurrency}
                                onChange={e => setLimitDrafts(prev => ({
                                  ...prev,
                                  [target.id]: { ...draft, max_concurrency: e.target.value },
                                }))}
                              />
                            </Field>
                            <Field label={t("Input chars")}>
                              <Input
                                type="number"
                                min="1"
                                step="1"
                                placeholder={t("no limit")}
                                value={draft.max_input_chars}
                                onChange={e => setLimitDrafts(prev => ({
                                  ...prev,
                                  [target.id]: { ...draft, max_input_chars: e.target.value },
                                }))}
                              />
                            </Field>
                            <Button
                              variant="secondary"
                              size="sm"
                              icon={<Save className="h-3.5 w-3.5" />}
                              aria-label={t("Save limits for target {{name}}", { name: target.name })}
                              disabled={!draftValid}
                              loading={updateLimits.isPending && updateLimits.variables?.id === target.id}
                              onClick={() => updateLimits.mutate({ id: target.id, draft })}
                            >
                              {t("Save limits")}
                            </Button>
                          </div>
                        </td>
                        <td className="px-5 py-3">
                          {target.has_secret ? <Badge tone="green">{t("configured")}</Badge> : <Badge tone="amber">{t("missing")}</Badge>}
                        </td>
                        <td className="px-5 py-3 text-right space-x-2">
                          <Button
                            variant="ghost"
                            size="sm"
                            icon={<Sparkles className="h-3.5 w-3.5" />}
                            onClick={() => {
                              setTemplateTarget(target);
                              setGeneratorConfigId("");
                              setMaxTemplateCandidates("10");
                            }}
                          >
                            {t("Topic bridge")}
                          </Button>
                          <Button 
                            variant="ghost" 
                            size="sm" 
                            icon={<CheckCircle2 className="h-3.5 w-3.5" />}
                            aria-label={t("Test target {{name}}", { name: target.name })}
                            onClick={() => check.mutate(target.id)}
                            loading={check.isPending && check.variables === target.id}
                          >
                            {t("Test")}
                          </Button>
                          <Button variant="ghost" size="sm" icon={<Trash2 className="h-3.5 w-3.5" />}
                            aria-label={t("Delete target {{name}}", { name: target.name })}
                            onClick={() => setDeleteTarget(target)}>
                            {t("Delete")}
                          </Button>
                        </td>
                      </tr>
                      {result && (
                        <tr>
                          <td colSpan={6} className="px-5 py-2 bg-gray-50">
                            <div className="text-sm">
                              {result.ok ? (
                                <div role="status" className="flex items-center gap-2 text-green-700">
                                  <CheckCircle2 className="h-4 w-4" />
                                  <span className="font-medium">
                                    {t("Target {{name}} OK ({{latency}} ms)", {
                                      name: target.name,
                                      latency: result.latency_ms ?? "-",
                                    })}
                                  </span>
                                  {result.stream_ok === true && <Badge tone="green">{t("stream")}</Badge>}
                                  {result.stream_ok === false && <Badge tone="amber">{t("no stream")}</Badge>}
                                  {result.response_preview && (
                                    <button
                                      className="ml-2 text-xs text-gray-500 hover:text-gray-700 underline"
                                      onClick={() => setExpandedChecks(prev => ({ ...prev, [target.id]: !prev[target.id] }))}
                                    >
                                      {expanded ? t("hide") : t("show")} {t("response")}
                                    </button>
                                  )}
                                </div>
                              ) : (
                                <div role="alert" className="flex items-start gap-2 text-red-700">
                                  <AlertCircle className="h-4 w-4 mt-0.5" />
                                  <div>
                                    <span className="font-medium">{t("Target {{name}} check failed", { name: target.name })}: </span>
                                    <span className="text-sm">{result.error}</span>
                                  </div>
                                </div>
                              )}
                              {result.ok && result.stream_ok === false && result.stream_error && (
                                <div className="mt-1 text-xs text-amber-700">
                                  {t("Stream check failed: {{error}}", { error: result.stream_error })}
                                </div>
                              )}
                              {expanded && result.response_preview && (
                                <pre className="mt-2 p-2 bg-white border rounded text-xs overflow-x-auto">
                                  {result.response_preview}
                                </pre>
                              )}
                            </div>
                          </td>
                        </tr>
                      )}
                    </Fragment>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </Card>
      {templateTarget && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-gray-900/40 px-4">
          <div className="w-full max-w-3xl max-h-[90vh] overflow-y-auto rounded-lg border border-gray-200 bg-white p-5 shadow-2xl">
            <div className="flex items-start justify-between gap-4">
              <div>
                <h2 className="text-base font-semibold text-gray-900">{t("Topic-bridge templates")}</h2>
                <p className="mt-1 text-sm text-gray-600">
                  {templateTarget.name} · <span className="font-mono text-xs">{templateTarget.params?.model}</span>
                </p>
              </div>
              <button className="text-gray-400 hover:text-gray-700" onClick={() => setTemplateTarget(null)}>×</button>
            </div>
            <div className="mt-5 rounded-lg border border-gray-200 bg-gray-50 p-4">
              <Field
                label={t("Generator model")}
                hint={t("Choose a separate configured model to discover the service topic and validate the wrapper.")}
              >
                <Select value={generatorConfigId} onChange={e => setGeneratorConfigId(e.target.value)}>
                  <option value="">{t("-- pick generator --")}</option>
                  {data?.filter(item => item.id !== templateTarget.id).map(item => (
                    <option key={item.id} value={item.id}>{item.name} · {item.params?.model}</option>
                  ))}
                </Select>
              </Field>
              <Field
                label={t("Maximum template attempts")}
                hint={t("Each failed candidate feeds its evaluation back into the next attempt. Default: 10.")}
              >
                <Input
                  type="number"
                  min="1"
                  max="20"
                  step="1"
                  value={maxTemplateCandidates}
                  onChange={e => setMaxTemplateCandidates(e.target.value)}
                />
              </Field>
              <div className="mt-3 flex justify-end">
                <Button
                  icon={<Sparkles className="h-4 w-4" />}
                  disabled={
                    !generatorConfigId
                    || !Number.isInteger(Number(maxTemplateCandidates))
                    || Number(maxTemplateCandidates) < 1
                    || Number(maxTemplateCandidates) > 20
                  }
                  loading={generateTemplate.isPending}
                  onClick={() => generateTemplate.mutate()}
                >
                  {templateVersions?.length ? t("Regenerate and verify") : t("Generate and verify")}
                </Button>
              </div>
            </div>
            <div className="mt-5 space-y-3">
              <h3 className="text-sm font-semibold text-gray-900">{t("Version history")}</h3>
              {templatesLoading ? (
                <div className="text-sm text-gray-500">{t("Loading…")}</div>
              ) : !templateVersions?.length ? (
                <div className="rounded-lg border border-dashed border-gray-300 p-5 text-sm text-gray-500">
                  {t("No topic-bridge template has been generated for this model.")}
                </div>
              ) : templateVersions.map(version => (
                <div key={version.id} className="rounded-lg border border-gray-200 p-4">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <div className="flex items-center gap-2">
                      <span className="font-medium">v{version.version}</span>
                      <Badge tone={version.status === "succeeded" ? "green" : "red"}>{version.status}</Badge>
                      {version.is_active && <Badge tone="indigo">{t("active")}</Badge>}
                      {version.topic && <Badge>{version.topic}</Badge>}
                      {version.language && <Badge tone="blue">{version.language}</Badge>}
                    </div>
                    {!version.is_active && version.status === "succeeded" && (
                      <Button
                        size="sm"
                        variant="secondary"
                        loading={activateTemplate.isPending && activateTemplate.variables === version.id}
                        onClick={() => activateTemplate.mutate(version.id)}
                      >{t("Activate")}</Button>
                    )}
                  </div>
                  <div className="mt-2 text-xs text-gray-500">
                    {t("Generated by")}: {version.generator_model}
                    {version.created_at ? ` · ${new Date(version.created_at).toLocaleString()}` : ""}
                  </div>
                  {version.template && (
                    <pre className="mt-3 max-h-40 overflow-auto whitespace-pre-wrap rounded bg-gray-50 p-3 text-xs font-mono text-gray-800">{version.template}</pre>
                  )}
                  {version.error && <div className="mt-2 text-xs text-red-700">{version.error}</div>}
                  <div className="mt-3">
                    <Button
                      size="sm"
                      variant="ghost"
                      loading={loadTemplateTrace.isPending && loadTemplateTrace.variables === version.id}
                      onClick={() => {
                        if (expandedTraceId === version.id) {
                          setExpandedTraceId(null);
                        } else if (templateTraces[version.id]) {
                          setExpandedTraceId(version.id);
                        } else {
                          loadTemplateTrace.mutate(version.id);
                        }
                      }}
                    >
                      {expandedTraceId === version.id ? t("Hide generation trace") : t("View generation trace")}
                    </Button>
                  </div>
                  {expandedTraceId === version.id && templateTraces[version.id] && (
                    <div className="mt-3 space-y-2 rounded border border-gray-200 bg-gray-50 p-3 text-xs">
                      <div><span className="font-medium">{t("Scope response")}:</span> {templateTraces[version.id]?.scope?.response}</div>
                      <div><span className="font-medium">{t("Verification response")}:</span> {templateTraces[version.id]?.verification?.response}</div>
                      {(templateTraces[version.id]?.candidates ?? []).map((candidate: any) => (
                        <div key={candidate.number} className="rounded border border-gray-200 bg-white p-2">
                          <div className="font-medium">{t("Candidate")} {candidate.number}</div>
                          {(candidate.canaries ?? []).map((canary: any, index: number) => (
                            <div key={index} className="mt-1 flex items-start gap-2">
                              <Badge tone={canary.passed ? "green" : "red"}>{canary.passed ? t("passed") : t("failed")}</Badge>
                              <span>{canary.prompt}</span>
                            </div>
                          ))}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
            <div className="mt-5 flex justify-end">
              <Button variant="secondary" onClick={() => setTemplateTarget(null)}>{t("Close")}</Button>
            </div>
          </div>
        </div>
      )}
      {deleteTarget && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-gray-900/40 px-4">
          <div className="w-full max-w-md rounded-lg border border-gray-200 bg-white p-5 shadow-2xl">
            <h2 className="text-base font-semibold text-gray-900">{t("Delete target?")}</h2>
            <p className="mt-2 text-sm text-gray-600">
              {t("Delete {{name}}. Existing runs keep their historical data, but this target can no longer be selected.", {
                name: deleteTarget.name,
              })}
            </p>
            <div className="mt-5 flex justify-end gap-2">
              <Button variant="secondary" onClick={() => setDeleteTarget(null)}>
                {t("Cancel")}
              </Button>
              <Button
                variant="danger"
                icon={<Trash2 className="h-4 w-4" />}
                loading={del.isPending}
                onClick={() => del.mutate(deleteTarget.id)}
              >
                {t("Delete target")}
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
