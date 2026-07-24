import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { useSearchParams } from "react-router-dom";
import { Radar, Save, Sparkles } from "lucide-react";
import { toast } from "sonner";
import { api } from "../lib/api";
import { useI18n } from "../lib/i18n";
import { Badge } from "../components/ui/Badge";
import { Button } from "../components/ui/Button";
import { Card, CardBody, CardHeader, CardTitle } from "../components/ui/Card";
import { Field, Input, Select, Textarea } from "../components/ui/Form";
import { Tabs } from "../components/ui/Tabs";

type Target = { id: string; name: string; plugin: string; params: Record<string, any> };
type ReconReport = {
  id: string; version: number; status: string; target_model: string; generator_model: string;
  report: any; error: string | null; has_trace: boolean; created_at: string | null;
};
type BridgeTemplate = {
  id: string; version: number; status: string; is_active: boolean; topic: string | null;
  language: string | null; template: string | null; target_model: string; generator_model: string;
  source: "generated" | "manual"; verification_passed: boolean; has_trace: boolean;
  error: string | null; created_at: string | null;
};
type WorkspaceTab = "agent" | "topic-bridge";

function statusTone(status: string): "green" | "red" | "amber" {
  if (status === "succeeded") return "green";
  if (status === "failed") return "red";
  return "amber";
}

function capabilityTone(status: string): "green" | "red" | "amber" | "gray" {
  if (status === "verified") return "green";
  if (status === "refuted") return "red";
  if (status === "inconclusive" || status === "claimed_unverified") return "amber";
  return "gray";
}

export default function Reconnaissance() {
  const { t } = useI18n();
  const qc = useQueryClient();
  const [params, setParams] = useSearchParams();
  const rawTab = params.get("tab");
  const activeTab: WorkspaceTab = rawTab === "topic-bridge" ? "topic-bridge" : "agent";
  const targetId = params.get("target") ?? "";
  const [reconGeneratorId, setReconGeneratorId] = useState("");
  const [bridgeGeneratorId, setBridgeGeneratorId] = useState("");
  const [manualBridgeTemplate, setManualBridgeTemplate] = useState("");
  const [maxRounds, setMaxRounds] = useState("10");
  const [maxCandidates, setMaxCandidates] = useState("10");
  const [traces, setTraces] = useState<Record<string, any>>({});
  const [expandedTrace, setExpandedTrace] = useState<string | null>(null);

  const { data: targets = [] } = useQuery({
    queryKey: ["targets"],
    queryFn: async () => (await api.get<Target[]>("/api/targets")).data,
  });
  const { data: reports = [], isLoading: reportsLoading } = useQuery({
    queryKey: ["target-reconnaissance", targetId],
    enabled: !!targetId,
    queryFn: async () => (await api.get<ReconReport[]>(`/api/targets/${targetId}/reconnaissance`)).data,
  });
  const { data: templates = [], isLoading: templatesLoading } = useQuery({
    queryKey: ["service-context-templates", targetId],
    enabled: !!targetId,
    queryFn: async () => (
      await api.get<BridgeTemplate[]>(`/api/targets/${targetId}/service-context-templates`)
    ).data,
  });

  const setTab = (tab: WorkspaceTab) => {
    const next = new URLSearchParams(params);
    next.set("tab", tab);
    setParams(next, { replace: true });
  };
  const setTarget = (id: string) => {
    const next = new URLSearchParams(params);
    if (id) next.set("target", id); else next.delete("target");
    setParams(next, { replace: true });
    setReconGeneratorId("");
    setBridgeGeneratorId("");
    setManualBridgeTemplate("");
    setExpandedTrace(null);
  };
  const recon = useMutation({
    mutationFn: async () => api.post<ReconReport>(`/api/targets/${targetId}/reconnaissance/run`, {
      generator_config_id: reconGeneratorId,
      max_rounds: Number(maxRounds),
    }),
    onSuccess: ({ data }) => {
      if (data.status === "succeeded") toast.success(t("Reconnaissance completed"));
      else toast.error(data.error ?? t("Reconnaissance failed"));
      qc.invalidateQueries({ queryKey: ["target-reconnaissance", targetId] });
    },
    onError: (error: any) => toast.error(error?.response?.data?.detail ?? t("Reconnaissance failed")),
  });
  const generateBridge = useMutation({
    mutationFn: async () => api.post<BridgeTemplate>(
      `/api/targets/${targetId}/service-context-templates/generate`,
      { generator_config_id: bridgeGeneratorId, max_candidates: Number(maxCandidates) },
    ),
    onSuccess: ({ data }) => {
      if (data.status === "succeeded") toast.success(t("Topic-bridge template generated"));
      else toast.error(data.error ?? t("Template generation failed"));
      qc.invalidateQueries({ queryKey: ["service-context-templates", targetId] });
    },
    onError: (error: any) => toast.error(error?.response?.data?.detail ?? t("Template generation failed")),
  });
  const activateBridge = useMutation({
    mutationFn: async (templateId: string) => api.post(
      `/api/targets/${targetId}/service-context-templates/${templateId}/activate`,
    ),
    onSuccess: () => {
      toast.success(t("Template activated"));
      qc.invalidateQueries({ queryKey: ["service-context-templates", targetId] });
    },
    onError: (error: any) => toast.error(error?.response?.data?.detail ?? t("Failed to activate template")),
  });
  const createManualBridge = useMutation({
    mutationFn: async () => api.post<BridgeTemplate>(
      `/api/targets/${targetId}/service-context-templates/manual`,
      { template: manualBridgeTemplate },
    ),
    onSuccess: () => {
      toast.success(t("Manual topic-bridge template saved"));
      setManualBridgeTemplate("");
      qc.invalidateQueries({ queryKey: ["service-context-templates", targetId] });
    },
    onError: (error: any) => toast.error(error?.response?.data?.detail ?? t("Failed to save manual template")),
  });
  const loadTrace = useMutation({
    mutationFn: async ({ id, kind }: { id: string; kind: "recon" | "bridge" }) => {
      const path = kind === "recon"
        ? `/api/targets/${targetId}/reconnaissance/${id}/trace`
        : `/api/targets/${targetId}/service-context-templates/${id}/trace`;
      return { key: `${kind}:${id}`, trace: (await api.get(path)).data };
    },
    onSuccess: ({ key, trace }) => {
      setTraces(previous => ({ ...previous, [key]: trace }));
      setExpandedTrace(key);
    },
    onError: (error: any) => toast.error(error?.response?.data?.detail ?? t("Failed to load generation trace")),
  });
  const toggleTrace = (id: string, kind: "recon" | "bridge") => {
    const key = `${kind}:${id}`;
    if (expandedTrace === key) setExpandedTrace(null);
    else if (traces[key]) setExpandedTrace(key);
    else loadTrace.mutate({ id, kind });
  };

  const generatorOptions = targets.filter(target => target.id !== targetId);
  const usableTemplates = templates.filter(template => (
    template.status === "succeeded"
    && !!template.template
    && (template.verification_passed || template.source === "manual")
  ));
  const activeTemplate = usableTemplates.find(template => template.is_active);
  const manualPlaceholderCount = manualBridgeTemplate.split("{prompt}").length - 1;
  const manualTemplateValid = !!manualBridgeTemplate.trim() && manualPlaceholderCount === 1;
  const tabs = [
    { id: "agent" as const, label: t("Agent reconnaissance"), icon: <Radar className="h-4 w-4" /> },
    { id: "topic-bridge" as const, label: t("Topic bridge"), icon: <Sparkles className="h-4 w-4" /> },
  ];

  return <div className="space-y-6">
    <div>
      <h1 className="text-2xl font-bold tracking-tight">{t("Reconnaissance")}</h1>
      <p className="text-sm text-gray-500 mt-1">{t("Inventory agent capabilities and manage topic bridges for configured targets.")}</p>
    </div>
    <Card><CardBody>
      <Field label={t("Target")} hint={t("Select the target agent or chat application to inspect.")}>
        <Select value={targetId} onChange={event => setTarget(event.target.value)}>
          <option value="">{t("-- select target --")}</option>
          {targets.map(target => <option key={target.id} value={target.id}>{target.name} · {target.params?.model}</option>)}
        </Select>
      </Field>
    </CardBody></Card>
    {!targetId ? <Card><CardBody><div className="text-sm text-gray-500">{t("Select a target to begin reconnaissance or manage topic bridges.")}</div></CardBody></Card> :
      <Tabs tabs={tabs} value={activeTab} onChange={setTab} idBase="recon-workspace">
        {tab => tab === "agent" ? <div className="space-y-5">
          <Card>
            <CardHeader><CardTitle>{t("Run black-box reconnaissance")}</CardTitle></CardHeader>
            <CardBody>
              <div className="rounded-lg border border-amber-200 bg-amber-50 p-3 text-xs text-amber-900 mb-4">
                {t("Results are observations, not an authoritative skill or MCP manifest. Only public, synthetic, read-only probes are sent.")}
              </div>
              <div className="grid gap-4 md:grid-cols-[minmax(0,1fr)_180px_auto] items-end">
                <Field label={t("Generator model")} hint={t("A separate model analyzes untrusted responses and gates every probe.")}>
                  <Select value={reconGeneratorId} onChange={event => setReconGeneratorId(event.target.value)}>
                    <option value="">{t("-- pick generator --")}</option>
                    {generatorOptions.map(target => <option key={target.id} value={target.id}>{target.name} · {target.params?.model}</option>)}
                  </Select>
                </Field>
                <Field label={t("Maximum probe rounds")} hint={t("Stops early when coverage is complete.")}>
                  <Input type="number" min="1" max="10" value={maxRounds} onChange={event => setMaxRounds(event.target.value)} />
                </Field>
                <Button icon={<Radar className="h-4 w-4" />} loading={recon.isPending} disabled={!reconGeneratorId || Number(maxRounds) < 1 || Number(maxRounds) > 10} onClick={() => recon.mutate()}>
                  {reports.length ? t("Run again") : t("Start reconnaissance")}
                </Button>
              </div>
            </CardBody>
          </Card>
          <Card>
            <CardHeader><CardTitle>{t("Reconnaissance history")}</CardTitle></CardHeader>
            {reportsLoading ? <div className="p-5 text-sm text-gray-500">{t("Loading…")}</div> : !reports.length ? <div className="p-5 text-sm text-gray-500">{t("No reconnaissance report has been generated for this target.")}</div> : <div className="divide-y divide-gray-100">{reports.map(report => {
              const result = report.report ?? {};
              const traceKey = `recon:${report.id}`;
              return <div key={report.id} className="p-5">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div className="flex items-center gap-2"><span className="font-medium">v{report.version}</span><Badge tone={statusTone(report.status)}>{report.status}</Badge>{result.classification && <Badge tone="blue">{result.classification}</Badge>}{result.primary_language?.code && <Badge>{result.primary_language.code}</Badge>}</div>
                  <div className="text-xs text-gray-500">{t("Generated by")}: {report.generator_model}{report.created_at ? ` · ${new Date(report.created_at).toLocaleString()}` : ""}</div>
                </div>
                {report.error && <div className="mt-3 text-xs text-red-700">{report.error}</div>}
                {result.summary && <p className="mt-3 text-sm text-gray-700">{result.summary}</p>}
                {!!result.service_topics?.length && <div className="mt-3 flex flex-wrap gap-2">{result.service_topics.map((topic: string) => <Badge key={topic}>{topic}</Badge>)}</div>}
                {!!result.capabilities?.length && <div className="mt-4 overflow-x-auto"><table className="w-full text-sm"><thead className="bg-gray-50 text-xs text-gray-600"><tr><th className="text-left px-3 py-2">{t("Capability")}</th><th className="text-left px-3 py-2">{t("Kind")}</th><th className="text-left px-3 py-2">{t("Verification")}</th><th className="text-left px-3 py-2">{t("Evidence and boundary")}</th></tr></thead><tbody className="divide-y divide-gray-100">{result.capabilities.map((capability: any) => <tr key={capability.id}><td className="px-3 py-2"><div className="font-medium">{capability.name}</div><div className="text-xs text-gray-500">{capability.description}</div></td><td className="px-3 py-2">{capability.kind}</td><td className="px-3 py-2"><Badge tone={capabilityTone(capability.status)}>{capability.status}</Badge><div className="text-xs text-gray-400 mt-1">{Math.round((capability.confidence ?? 0) * 100)}%</div></td><td className="px-3 py-2 text-xs text-gray-600"><div>{capability.evidence?.join(" · ")}</div><div className="mt-1 text-gray-500">{capability.safety_boundary}</div></td></tr>)}</tbody></table></div>}
                {!!result.boundary_findings?.length && <div className="mt-4 rounded bg-gray-50 p-3 text-xs"><div className="font-medium mb-1">{t("Boundary findings")}</div><ul className="list-disc pl-5 space-y-1">{result.boundary_findings.map((finding: string) => <li key={finding}>{finding}</li>)}</ul></div>}
                {report.has_trace && <div className="mt-3"><Button size="sm" variant="ghost" loading={loadTrace.isPending && loadTrace.variables?.id === report.id} onClick={() => toggleTrace(report.id, "recon")}>{expandedTrace === traceKey ? t("Hide generation trace") : t("View generation trace")}</Button></div>}
                {expandedTrace === traceKey && traces[traceKey] && <ReconTrace trace={traces[traceKey]} />}
              </div>;
            })}</div>}
          </Card>
        </div> : <div className="space-y-5">
          <Card>
            <CardHeader><CardTitle>{t("Generate topic-bridge template")}</CardTitle></CardHeader>
            <CardBody>
              <div className="grid gap-4 md:grid-cols-[minmax(0,1fr)_180px_auto] items-end">
                <Field label={t("Generator model")} hint={t("Choose a separate configured model to discover the service topic and validate the wrapper.")}>
                  <Select value={bridgeGeneratorId} onChange={event => setBridgeGeneratorId(event.target.value)}><option value="">{t("-- pick generator --")}</option>{generatorOptions.map(target => <option key={target.id} value={target.id}>{target.name} · {target.params?.model}</option>)}</Select>
                </Field>
                <Field label={t("Maximum template attempts")} hint={t("Failed candidates feed evaluation into the next attempt.")}><Input type="number" min="1" max="20" value={maxCandidates} onChange={event => setMaxCandidates(event.target.value)} /></Field>
                <Button icon={<Sparkles className="h-4 w-4" />} loading={generateBridge.isPending} disabled={!bridgeGeneratorId || Number(maxCandidates) < 1 || Number(maxCandidates) > 20} onClick={() => generateBridge.mutate()}>{templates.length ? t("Regenerate and verify") : t("Generate and verify")}</Button>
              </div>
            </CardBody>
          </Card>
          <Card>
            <CardHeader><CardTitle>{t("Enter topic-bridge template manually")}</CardTitle></CardHeader>
            <CardBody>
              <div className="space-y-4">
                <Field
                  label={t("Template content")}
                  hint={t("The template must contain exactly one {prompt} placeholder and no other variables.")}
                >
                  <Textarea
                    rows={8}
                    value={manualBridgeTemplate}
                    placeholder={t("Place the transformed prompt at {prompt}.")}
                    onChange={event => setManualBridgeTemplate(event.target.value)}
                  />
                </Field>
                <div className="flex justify-end">
                  <Button
                    icon={<Save className="h-4 w-4" />}
                    loading={createManualBridge.isPending}
                    disabled={!manualTemplateValid}
                    onClick={() => createManualBridge.mutate()}
                  >
                    {t("Save as new version")}
                  </Button>
                </div>
              </div>
            </CardBody>
          </Card>
          <Card>
            <CardHeader><CardTitle>{t("Topic-bridge versions")}</CardTitle></CardHeader>
            {!templatesLoading && !!usableTemplates.length && <div className="border-b border-gray-100 p-5">
              <Field label={t("Active version")} hint={t("New runs use this topic-bridge version by default.")}>
                <Select
                  value={activeTemplate?.id ?? ""}
                  disabled={activateBridge.isPending}
                  onChange={event => event.target.value && activateBridge.mutate(event.target.value)}
                >
                  <option value="">{t("-- no active version --")}</option>
                  {usableTemplates.map(template => (
                    <option key={template.id} value={template.id}>
                      v{template.version} · {template.source === "manual" ? t("Manually entered") : t("Model generated")}
                    </option>
                  ))}
                </Select>
              </Field>
            </div>}
            {templatesLoading ? <div className="p-5 text-sm text-gray-500">{t("Loading…")}</div> : !templates.length ? <div className="p-5 text-sm text-gray-500">{t("No topic-bridge template has been generated for this model.")}</div> : <div className="divide-y divide-gray-100">{templates.map(template => {
              const traceKey = `bridge:${template.id}`;
              return <div key={template.id} className="p-5">
                <div className="flex flex-wrap items-center gap-2"><span className="font-medium">v{template.version}</span><Badge tone={statusTone(template.status)}>{template.status}</Badge>{template.is_active && <Badge tone="indigo">{t("active")}</Badge>}<Badge tone={template.source === "manual" ? "amber" : "gray"}>{template.source === "manual" ? t("Manually entered") : t("Model generated")}</Badge>{template.topic && <Badge>{template.topic}</Badge>}{template.language && <Badge tone="blue">{template.language}</Badge>}</div>
                <div className="mt-2 text-xs text-gray-500">{template.source === "generated" ? `${t("Generated by")}: ${template.generator_model}` : t("Manually entered")}{template.created_at ? ` · ${new Date(template.created_at).toLocaleString()}` : ""}</div>
                {template.template && <pre className="mt-3 max-h-48 overflow-auto whitespace-pre-wrap rounded bg-gray-50 p-3 text-xs font-mono">{template.template}</pre>}
                {template.error && <div className="mt-2 text-xs text-red-700">{template.error}</div>}
                {template.has_trace && <div className="mt-3"><Button size="sm" variant="ghost" loading={loadTrace.isPending && loadTrace.variables?.id === template.id} onClick={() => toggleTrace(template.id, "bridge")}>{expandedTrace === traceKey ? t("Hide generation trace") : t("View generation trace")}</Button></div>}
                {expandedTrace === traceKey && traces[traceKey] && <BridgeTrace trace={traces[traceKey]} />}
              </div>;
            })}</div>}
          </Card>
        </div>}
      </Tabs>}
  </div>;
}

function ReconTrace({ trace }: { trace: any }) {
  const { t } = useI18n();
  return <div className="mt-3 space-y-2 rounded border border-gray-200 bg-gray-50 p-3 text-xs">
    <div><span className="font-medium">{t("Initial response")}:</span> {trace.initial?.response}</div>
    {(trace.rounds ?? []).map((round: any) => <div key={round.number} className="rounded border border-gray-200 bg-white p-2"><div className="flex items-center gap-2 font-medium"><span>{t("Round")} {round.number}</span>{round.stopped_early && <Badge tone="green">{t("early stop")}</Badge>}{round.skipped && <Badge tone="amber">{t("skipped")}</Badge>}</div>{round.probe && <div className="mt-1"><span className="font-medium">{t("Probe")}:</span> {round.probe}</div>}{round.target_response && <div className="mt-1"><span className="font-medium">{t("Response")}:</span> {round.target_response}</div>}{round.skipped && <div className="mt-1 text-amber-800">{round.skipped}</div>}</div>)}
  </div>;
}

function BridgeTrace({ trace }: { trace: any }) {
  const { t } = useI18n();
  return <div className="mt-3 space-y-2 rounded border border-gray-200 bg-gray-50 p-3 text-xs">
    <div><span className="font-medium">{t("Scope response")}:</span> {trace.scope?.response}</div>
    <div><span className="font-medium">{t("Verification response")}:</span> {trace.verification?.response}</div>
    {(trace.candidates ?? []).map((candidate: any) => <div key={candidate.number} className="rounded border border-gray-200 bg-white p-2"><div className="font-medium">{t("Candidate")} {candidate.number}</div>{(candidate.canaries ?? []).map((canary: any, index: number) => <div key={index} className="mt-1 flex items-start gap-2"><Badge tone={canary.passed ? "green" : "red"}>{canary.passed ? t("passed") : t("failed")}</Badge><span>{canary.prompt}</span></div>)}</div>)}
  </div>;
}
