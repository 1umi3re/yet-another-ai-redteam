import { useMutation, useQuery } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { toast } from "sonner";
import { ArrowLeft, PlayCircle } from "lucide-react";
import { api } from "../lib/api";
import { useI18n } from "../lib/i18n";
import { Badge } from "../components/ui/Badge";
import { Button } from "../components/ui/Button";
import { Card, CardBody, CardHeader, CardTitle } from "../components/ui/Card";
import { Field, Input, Select } from "../components/ui/Form";
import { ConfiguredPlugin, defaultsFor, ParamField, PluginSchemas } from "../components/PluginParamsForm";

const PAGE_SIZE = 100;

export default function RetestRun() {
  const { t } = useI18n();
  const nav = useNavigate();
  const [params] = useSearchParams();
  const targetId = params.get("target") ?? "";
  const [page, setPage] = useState(0);
  const [mode, setMode] = useState<"exact_replay" | "reapply_method">("exact_replay");
  const [excluded, setExcluded] = useState<Set<string>>(new Set());
  const [name, setName] = useState(t("Successful attempt retest"));
  const [scorer, setScorer] = useState<ConfiguredPlugin>({ plugin: "refusal", params: {} });
  const [concurrency, setConcurrency] = useState("4");
  const [timeout, setTimeout] = useState("");

  const { data: targets = [] } = useQuery({ queryKey: ["targets"], queryFn: async () => (await api.get("/api/targets")).data });
  const { data: plugins } = useQuery({ queryKey: ["plugins"], queryFn: async () => (await api.get("/api/plugins")).data });
  const { data: promptAssets = [] } = useQuery({ queryKey: ["prompt-assets"], queryFn: async () => (await api.get("/api/prompt-assets")).data });
  const { data, isLoading } = useQuery({
    queryKey: ["successful-attempts", targetId, page],
    enabled: !!targetId,
    queryFn: async () => (await api.get(`/api/targets/${targetId}/successful-attempts`, {
      params: { limit: PAGE_SIZE, offset: page * PAGE_SIZE },
    })).data,
  });
  const target = targets.find((item: any) => item.id === targetId);
  const scorerSchemas: PluginSchemas = plugins?.params?.scorers ?? {};
  const scorerSchema = scorerSchemas[scorer.plugin];
  const items: any[] = data?.items ?? [];
  const summary = data?.summary ?? {};
  const selectedCount = Math.max(0, (mode === "exact_replay" ? data?.total ?? 0 : summary.reapply_available ?? 0) - excluded.size);
  const pages = Math.max(1, Math.ceil((data?.total ?? 0) / PAGE_SIZE));
  const visibleSelectable = useMemo(
    () => items.filter(item => mode === "exact_replay" || item.reapply_eligible),
    [items, mode],
  );

  const toggle = (id: string) => setExcluded(previous => {
    const next = new Set(previous);
    if (next.has(id)) next.delete(id); else next.add(id);
    return next;
  });
  const mutation = useMutation({
    mutationFn: async () => {
      const created = await api.post("/api/retests", {
        name,
        target_config_id: targetId,
        mode,
        scorer,
        concurrency: Number(concurrency),
        timeout_seconds: timeout ? Number(timeout) : null,
        select_all: true,
        excluded_attempt_ids: Array.from(excluded),
      });
      await api.post(`/api/runs/${created.data.id}/start`);
      return created.data;
    },
    onSuccess: run => nav(`/runs/${run.id}`),
    onError: (error: any) => toast.error(error?.response?.data?.detail ?? t("Failed to start retest")),
  });

  if (!targetId) return (
    <Card><CardBody><p className="text-sm text-gray-600">{t("Select one target on the Runs page before starting a retest.")}</p></CardBody></Card>
  );

  return <div className="space-y-6">
    <div className="flex items-start justify-between gap-4">
      <div>
        <Link to={`/runs`} className="inline-flex items-center gap-1 text-xs text-gray-500 hover:text-gray-800 mb-2"><ArrowLeft className="h-3.5 w-3.5" />{t("Back to runs")}</Link>
        <h1 className="text-2xl font-bold tracking-tight">{t("Retest successful attempts")}</h1>
        <p className="text-sm text-gray-500 mt-1">{target?.name ?? targetId}</p>
      </div>
      <Button disabled={!selectedCount || !name.trim() || mutation.isPending} onClick={() => mutation.mutate()} icon={<PlayCircle className="h-4 w-4" />}>
        {mutation.isPending ? t("Starting…") : t("Start retest ({{count}})", { count: selectedCount })}
      </Button>
    </div>

    <div className="grid gap-4 md:grid-cols-4">
      {[
        [t("Successful attempts"), data?.total ?? 0],
        [t("Source runs"), summary.source_runs ?? 0],
        [t("Attack methods"), Object.keys(summary.by_method ?? {}).length],
        [t("Method replay available"), `${summary.reapply_available ?? 0}/${data?.total ?? 0}`],
      ].map(([label, value]) => <Card key={String(label)}><CardBody><div className="text-xs text-gray-500">{label}</div><div className="text-2xl font-semibold mt-1">{value}</div></CardBody></Card>)}
    </div>

    <Card>
      <CardHeader><CardTitle>{t("1. Choose replay mode")}</CardTitle></CardHeader>
      <CardBody className="grid gap-3 md:grid-cols-2">
        <label className={`rounded-lg border p-4 cursor-pointer ${mode === "exact_replay" ? "border-blue-500 bg-blue-50" : "border-gray-200"}`}>
          <input className="mr-2" type="radio" checked={mode === "exact_replay"} onChange={() => { setMode("exact_replay"); setExcluded(new Set()); }} />
          <span className="font-medium">{t("Exact replay")}</span>
          <p className="text-xs text-gray-500 mt-1 ml-5">{t("Replay stored prompts or user turns without converters or topic bridging.")}</p>
        </label>
        <label className={`rounded-lg border p-4 cursor-pointer ${mode === "reapply_method" ? "border-blue-500 bg-blue-50" : "border-gray-200"}`}>
          <input className="mr-2" type="radio" checked={mode === "reapply_method"} onChange={() => { setMode("reapply_method"); setExcluded(new Set()); }} />
          <span className="font-medium">{t("Reapply attack method")}</span>
          <p className="text-xs text-gray-500 mt-1 ml-5">{t("Regenerate attacks from original prompts using the historical method and current target configuration.")}</p>
        </label>
      </CardBody>
    </Card>

    <Card>
      <CardHeader><CardTitle>{t("2. Review attempts")}</CardTitle></CardHeader>
      {isLoading ? <div className="p-5 text-sm text-gray-500">{t("Loading…")}</div> : !items.length ? <div className="p-5 text-sm text-gray-500">{t("No successful attempts found for this target.")}</div> : <>
        <div className="border-b border-gray-100 px-5 py-3 flex items-center justify-between text-xs text-gray-500">
          <span>{t("{{count}} selected", { count: selectedCount })}</span>
          <div className="space-x-2"><Button size="sm" variant="ghost" onClick={() => setExcluded(new Set())}>{t("Select all compatible")}</Button><Button size="sm" variant="ghost" onClick={() => setExcluded(previous => new Set([...previous, ...visibleSelectable.map(item => item.id)]))}>{t("Deselect page")}</Button></div>
        </div>
        <div className="overflow-x-auto"><table className="w-full text-sm"><thead className="bg-gray-50 text-xs uppercase text-gray-600"><tr>
          <th className="px-4 py-2"></th><th className="text-left px-4 py-2">{t("Source run")}</th><th className="text-left px-4 py-2">{t("Attack method")}</th><th className="text-left px-4 py-2">{t("Prompt")}</th><th className="text-left px-4 py-2">{t("Provenance")}</th>
        </tr></thead><tbody className="divide-y divide-gray-100">{items.map(item => {
          const compatible = mode === "exact_replay" || item.reapply_eligible;
          return <tr key={item.id} className={!compatible ? "opacity-50" : ""}>
            <td className="px-4 py-3"><input type="checkbox" disabled={!compatible} checked={compatible && !excluded.has(item.id)} onChange={() => toggle(item.id)} /></td>
            <td className="px-4 py-3">{item.source_run_name}</td>
            <td className="px-4 py-3"><div>{item.executor_name}</div><div className="text-xs text-gray-400">{item.executor_kind}</div></td>
            <td className="px-4 py-3 max-w-xl"><div className="truncate" title={item.original_prompt}>{item.original_prompt}</div>{item.multi_turn && <Badge tone="blue">{t("Multi-turn")}</Badge>}</td>
            <td className="px-4 py-3"><Badge tone={item.provenance_quality === "defaulted" ? "amber" : item.reapply_eligible ? "green" : "red"}>{item.provenance_quality}</Badge>{item.reapply_reason && <div className="text-xs text-gray-500 mt-1 max-w-xs">{item.reapply_reason}</div>}</td>
          </tr>;
        })}</tbody></table></div>
        <div className="p-4 flex justify-end items-center gap-3"><Button variant="secondary" size="sm" disabled={page === 0} onClick={() => setPage(value => value - 1)}>{t("Previous")}</Button><span className="text-xs text-gray-500">{page + 1} / {pages}</span><Button variant="secondary" size="sm" disabled={page + 1 >= pages} onClick={() => setPage(value => value + 1)}>{t("Next")}</Button></div>
      </>}
    </Card>

    <Card>
      <CardHeader><CardTitle>{t("3. Configure new run")}</CardTitle></CardHeader>
      <CardBody className="space-y-4">
        <div className="grid gap-4 md:grid-cols-3"><Field required label={t("Run name")}><Input value={name} onChange={event => setName(event.target.value)} /></Field><Field label={t("Concurrency")}><Input type="number" min="1" value={concurrency} onChange={event => setConcurrency(event.target.value)} /></Field><Field label={t("Run timeout")} hint={t("Blank means no limit.")}><Input type="number" min="1" value={timeout} onChange={event => setTimeout(event.target.value)} /></Field></div>
        <Field label={t("Scorer")}><Select value={scorer.plugin} onChange={event => setScorer({ plugin: event.target.value, params: defaultsFor(scorerSchemas[event.target.value]) })}>{plugins?.scorers?.map((plugin: string) => <option key={plugin}>{plugin}</option>)}</Select></Field>
        {scorerSchema && Object.keys(scorerSchema).length > 0 && <div className="rounded-lg border border-gray-200 bg-gray-50 p-4 space-y-3">{Object.entries(scorerSchema).map(([key, schema]) => <ParamField key={key} name={key} schema={schema} targets={targets} promptAssets={promptAssets} value={scorer.params[key]} onChange={value => setScorer(previous => ({ ...previous, params: { ...previous.params, [key]: value } }))} />)}</div>}
      </CardBody>
    </Card>
  </div>;
}
