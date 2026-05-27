import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Fragment, useState } from "react";
import { api } from "../lib/api";
import { Card, CardBody, CardHeader, CardTitle, CardDescription } from "../components/ui/Card";
import { Button } from "../components/ui/Button";
import { Input, Select, Field } from "../components/ui/Form";
import { EmptyState } from "../components/ui/EmptyState";
import { Badge } from "../components/ui/Badge";
import { Target as TargetIcon, Plus, Trash2, CheckCircle2, AlertCircle, Save } from "lucide-react";
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

export default function Targets() {
  const { t } = useI18n();
  const qc = useQueryClient();
  const { data, isLoading } = useQuery({
    queryKey: ["targets"],
    queryFn: async () => (await api.get<T[]>("/api/targets")).data,
  });
  const [form, setForm] = useState({
    name: "", plugin: "openai_compat", base_url: "", model: "", api_key: "",
    timeout: "", max_concurrency: "",
  });
  const [checkResults, setCheckResults] = useState<Record<string, CheckResult | null>>({});
  const [expandedChecks, setExpandedChecks] = useState<Record<string, boolean>>({});
  const [limitDrafts, setLimitDrafts] = useState<Record<string, { timeout: string; max_concurrency: string }>>({});
  const timeoutValue = form.timeout ? Number(form.timeout) : null;
  const maxConcurrencyValue = form.max_concurrency ? Number(form.max_concurrency) : null;
  const validLimits = (timeoutValue === null || timeoutValue > 0)
    && (maxConcurrencyValue === null || (Number.isInteger(maxConcurrencyValue) && maxConcurrencyValue > 0));
  
  const create = useMutation({
    mutationFn: async () => {
      const params: Record<string, any> = { name: form.name, base_url: form.base_url, model: form.model };
      if (timeoutValue !== null) params.timeout = timeoutValue;
      if (maxConcurrencyValue !== null) params.max_concurrency = maxConcurrencyValue;
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
        timeout: "", max_concurrency: "",
      });
      qc.invalidateQueries({ queryKey: ["targets"] });
    },
    onError: (e: any) => toast.error(e?.response?.data?.detail ?? t("Failed to create")),
  });
  const del = useMutation({
    mutationFn: async (id: string) => api.delete(`/api/targets/${id}`),
    onSuccess: () => { toast.success(t("Deleted")); qc.invalidateQueries({ queryKey: ["targets"] }); },
  });
  const updateLimits = useMutation({
    mutationFn: async ({ id, draft }: { id: string; draft: { timeout: string; max_concurrency: string } }) => {
      const timeout = draft.timeout.trim();
      const maxConcurrency = draft.max_concurrency.trim();
      const payload = {
        timeout: timeout ? Number(timeout) : null,
        max_concurrency: maxConcurrency ? Number(maxConcurrency) : null,
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
    onError: (e: any) => toast.error(e?.response?.data?.detail ?? t("Check failed")),
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
            <Field label={t("Name")}><Input placeholder="e.g. gpt-4o-mini" value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} /></Field>
            <Field label={t("Plugin")}>
              <Select value={form.plugin} onChange={e => setForm({ ...form, plugin: e.target.value })}>
                <option value="openai_compat">openai_compat</option>
                <option value="openai_compat_new_session">openai_compat_new_session</option>
                <option value="anthropic_compat">anthropic_compat</option>
              </Select>
            </Field>
            <Field label={t("Base URL")} hint="e.g. https://api.openai.com/v1"><Input value={form.base_url} onChange={e => setForm({ ...form, base_url: e.target.value })} /></Field>
            <Field label={t("Model")}><Input placeholder="e.g. gpt-4o-mini" value={form.model} onChange={e => setForm({ ...form, model: e.target.value })} /></Field>
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
            <div className="md:col-span-2">
              <Field label={t("API key")} hint={t("Stored encrypted. Never exposed via API.")}>
                <Input type="password" value={form.api_key} onChange={e => setForm({ ...form, api_key: e.target.value })} />
              </Field>
            </div>
          </div>
          <div className="mt-5 flex justify-end">
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
                  };
                  const draftTimeout = draft.timeout ? Number(draft.timeout) : null;
                  const draftMaxConcurrency = draft.max_concurrency ? Number(draft.max_concurrency) : null;
                  const draftValid = (draftTimeout === null || draftTimeout > 0)
                    && (draftMaxConcurrency === null || (Number.isInteger(draftMaxConcurrency) && draftMaxConcurrency > 0));
                  return (
                    <Fragment key={target.id}>
                      <tr>
                        <td className="px-5 py-3 font-medium">{target.name}</td>
                        <td className="px-5 py-3"><Badge tone="indigo">{target.plugin}</Badge></td>
                        <td className="px-5 py-3 font-mono text-xs text-gray-700">{target.params?.model}</td>
                        <td className="px-5 py-3">
                          <div className="flex min-w-52 items-end gap-2">
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
                            <Button
                              variant="secondary"
                              size="sm"
                              icon={<Save className="h-3.5 w-3.5" />}
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
                            icon={<CheckCircle2 className="h-3.5 w-3.5" />}
                            onClick={() => check.mutate(target.id)}
                            loading={check.isPending && check.variables === target.id}
                          >
                            {t("Test")}
                          </Button>
                          <Button variant="ghost" size="sm" icon={<Trash2 className="h-3.5 w-3.5" />}
                            onClick={() => { if (confirm(t("Delete this target?"))) del.mutate(target.id); }}>
                            {t("Delete")}
                          </Button>
                        </td>
                      </tr>
                      {result && (
                        <tr>
                          <td colSpan={6} className="px-5 py-2 bg-gray-50">
                            <div className="text-sm">
                              {result.ok ? (
                                <div className="flex items-center gap-2 text-green-700">
                                  <CheckCircle2 className="h-4 w-4" />
                                  <span className="font-medium">✓ OK ({result.latency_ms} ms)</span>
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
                                <div className="flex items-start gap-2 text-red-700">
                                  <AlertCircle className="h-4 w-4 mt-0.5" />
                                  <div>
                                    <span className="font-medium">✗ {t("Error")}: </span>
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
    </div>
  );
}
