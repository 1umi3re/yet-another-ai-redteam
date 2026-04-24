import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { api } from "../lib/api";
import { Card, CardBody, CardHeader, CardTitle, CardDescription } from "../components/ui/Card";
import { Button } from "../components/ui/Button";
import { Input, Select, Field } from "../components/ui/Form";
import { EmptyState } from "../components/ui/EmptyState";
import { Badge } from "../components/ui/Badge";
import { Target as TargetIcon, Plus, Trash2, CheckCircle2, AlertCircle } from "lucide-react";
import { toast } from "sonner";

type T = { id: string; name: string; plugin: string; params: Record<string, any>; has_secret: boolean };
type CheckResult = {
  ok: boolean;
  latency_ms: number | null;
  response_preview: string | null;
  error: string | null;
  model_echo: string | null;
};

export default function Targets() {
  const qc = useQueryClient();
  const { data, isLoading } = useQuery({
    queryKey: ["targets"],
    queryFn: async () => (await api.get<T[]>("/api/targets")).data,
  });
  const [form, setForm] = useState({
    name: "", plugin: "openai_compat", base_url: "", model: "", api_key: "",
  });
  const [checkResults, setCheckResults] = useState<Record<string, CheckResult | null>>({});
  const [expandedChecks, setExpandedChecks] = useState<Record<string, boolean>>({});
  
  const create = useMutation({
    mutationFn: async () => api.post("/api/targets", {
      name: form.name, plugin: form.plugin,
      params: { name: form.name, base_url: form.base_url, model: form.model },
      secret: { api_key: form.api_key },
    }),
    onSuccess: () => {
      toast.success("Target created");
      setForm({ name: "", plugin: "openai_compat", base_url: "", model: "", api_key: "" });
      qc.invalidateQueries({ queryKey: ["targets"] });
    },
    onError: (e: any) => toast.error(e?.response?.data?.detail ?? "Failed to create"),
  });
  const del = useMutation({
    mutationFn: async (id: string) => api.delete(`/api/targets/${id}`),
    onSuccess: () => { toast.success("Deleted"); qc.invalidateQueries({ queryKey: ["targets"] }); },
  });
  const check = useMutation({
    mutationFn: async (id: string) => {
      const resp = await api.post<CheckResult>(`/api/targets/${id}/check`);
      return { id, result: resp.data };
    },
    onSuccess: ({ id, result }) => {
      setCheckResults((prev) => ({ ...prev, [id]: result }));
      if (result.ok) {
        toast.success(`Target OK (${result.latency_ms}ms)`);
      } else {
        toast.error(`Target check failed: ${result.error}`);
      }
    },
    onError: (e: any) => toast.error(e?.response?.data?.detail ?? "Check failed"),
  });

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Targets</h1>
        <p className="text-sm text-gray-500 mt-1">Configure AI applications to test against.</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>New target</CardTitle>
          <CardDescription>OpenAI-compatible or Anthropic-compatible HTTP endpoint.</CardDescription>
        </CardHeader>
        <CardBody>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Field label="Name"><Input placeholder="e.g. gpt-4o-mini" value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} /></Field>
            <Field label="Plugin">
              <Select value={form.plugin} onChange={e => setForm({ ...form, plugin: e.target.value })}>
                <option value="openai_compat">openai_compat</option>
                <option value="anthropic_compat">anthropic_compat</option>
              </Select>
            </Field>
            <Field label="Base URL" hint="e.g. https://api.openai.com/v1"><Input value={form.base_url} onChange={e => setForm({ ...form, base_url: e.target.value })} /></Field>
            <Field label="Model"><Input placeholder="e.g. gpt-4o-mini" value={form.model} onChange={e => setForm({ ...form, model: e.target.value })} /></Field>
            <div className="md:col-span-2">
              <Field label="API key" hint="Stored encrypted. Never exposed via API.">
                <Input type="password" value={form.api_key} onChange={e => setForm({ ...form, api_key: e.target.value })} />
              </Field>
            </div>
          </div>
          <div className="mt-5 flex justify-end">
            <Button
              icon={<Plus className="h-4 w-4" />}
              loading={create.isPending}
              onClick={() => create.mutate()}
              disabled={!form.name || !form.base_url || !form.model || !form.api_key}
            >Create target</Button>
          </div>
        </CardBody>
      </Card>

      <Card>
        <CardHeader><CardTitle>Configured targets</CardTitle></CardHeader>
        {isLoading ? (
          <CardBody className="text-sm text-gray-500">Loading…</CardBody>
        ) : !data?.length ? (
          <EmptyState
            icon={<TargetIcon className="h-10 w-10" />}
            title="No targets yet"
            description="Add your first AI endpoint above to start running tests."
          />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 text-gray-600 text-xs uppercase tracking-wider">
                <tr>
                  <th className="text-left px-5 py-2.5">Name</th>
                  <th className="text-left px-5 py-2.5">Plugin</th>
                  <th className="text-left px-5 py-2.5">Model</th>
                  <th className="text-left px-5 py-2.5">Secret</th>
                  <th className="px-5 py-2.5"></th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {data.map(t => {
                  const result = checkResults[t.id];
                  const expanded = expandedChecks[t.id];
                  return (
                    <>
                      <tr key={t.id}>
                        <td className="px-5 py-3 font-medium">{t.name}</td>
                        <td className="px-5 py-3"><Badge tone="indigo">{t.plugin}</Badge></td>
                        <td className="px-5 py-3 font-mono text-xs text-gray-700">{t.params?.model}</td>
                        <td className="px-5 py-3">
                          {t.has_secret ? <Badge tone="green">configured</Badge> : <Badge tone="amber">missing</Badge>}
                        </td>
                        <td className="px-5 py-3 text-right space-x-2">
                          <Button 
                            variant="ghost" 
                            size="sm" 
                            icon={<CheckCircle2 className="h-3.5 w-3.5" />}
                            onClick={() => check.mutate(t.id)}
                            loading={check.isPending && check.variables === t.id}
                          >
                            Test
                          </Button>
                          <Button variant="ghost" size="sm" icon={<Trash2 className="h-3.5 w-3.5" />}
                            onClick={() => { if (confirm("Delete this target?")) del.mutate(t.id); }}>
                            Delete
                          </Button>
                        </td>
                      </tr>
                      {result && (
                        <tr key={`${t.id}-result`}>
                          <td colSpan={5} className="px-5 py-2 bg-gray-50">
                            <div className="text-sm">
                              {result.ok ? (
                                <div className="flex items-center gap-2 text-green-700">
                                  <CheckCircle2 className="h-4 w-4" />
                                  <span className="font-medium">✓ OK ({result.latency_ms} ms)</span>
                                  {result.response_preview && (
                                    <button
                                      className="ml-2 text-xs text-gray-500 hover:text-gray-700 underline"
                                      onClick={() => setExpandedChecks(prev => ({ ...prev, [t.id]: !prev[t.id] }))}
                                    >
                                      {expanded ? "hide" : "show"} response
                                    </button>
                                  )}
                                </div>
                              ) : (
                                <div className="flex items-start gap-2 text-red-700">
                                  <AlertCircle className="h-4 w-4 mt-0.5" />
                                  <div>
                                    <span className="font-medium">✗ Error: </span>
                                    <span className="text-sm">{result.error}</span>
                                  </div>
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
                    </>
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
