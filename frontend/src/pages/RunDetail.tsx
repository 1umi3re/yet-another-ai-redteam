import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Link, useParams, useNavigate } from "react-router-dom";
import { useEffect, useMemo, useState } from "react";
import { api } from "../lib/api";
import { useAuth } from "../lib/auth";
import { Card, CardBody, CardHeader, CardTitle, CardDescription } from "../components/ui/Card";
import { Badge, StatusBadge } from "../components/ui/Badge";
import { ProgressBar } from "../components/ui/ProgressBar";
import { Button } from "../components/ui/Button";
import { Field, Select, Textarea } from "../components/ui/Form";
import { Tabs, TabItem } from "../components/ui/Tabs";
import {
  ArrowLeft,
  X,
  Clock,
  Hash,
  AlertCircle,
  MessageSquare,
  Download,
  Ban,
  Pause,
  Play,
  RotateCcw,
  ChevronsLeft,
  ChevronLeft,
  ChevronRight,
  ChevronsRight,
} from "lucide-react";
import clsx from "clsx";
import { toast } from "sonner";
import { useI18n } from "../lib/i18n";
import {
  buildAttemptExportParams,
  buildHtmlReportExportParams,
  buildRunReportFilename,
  type RunExportFormat,
} from "../lib/runExport";
import { buildPageWindow, formatPaginationRange } from "../lib/pagination";

type Tab = "overview" | "attempts" | "events";
type Verdict = "refused" | "complied";

const TERMINAL_STATUSES = new Set(["completed", "failed", "cancelled"]);
const ACTION_MIN_SCORED = 3;
const isTerminalStatus = (s: string | undefined) => !!s && TERMINAL_STATUSES.has(s);

function isScoreFailed(score: any): boolean {
  return score?.status === "failed" || score?.value?.status === "failed" || !!score?.value?.error;
}

function scorerVerdictOf(score: any): Verdict | null {
  if (isScoreFailed(score)) return null;
  const v = score?.value ?? {};
  if (typeof v.attack_success === "boolean") {
    return v.attack_success ? "complied" : "refused";
  }
  const label = v.label;
  if (typeof label !== "boolean") return null;
  if (score?.scorer === "refusal") return label ? "refused" : "complied";
  return label ? "complied" : "refused";
}

// Reviewer labels use target-side polarity: true = refused, false = complied.
// Without a reviewer override, scorer output remains the source of truth.
function verdictOf(score: any): Verdict | null {
  if (typeof score?.reviewer_label === "boolean") {
    return score.reviewer_label ? "refused" : "complied";
  }
  return scorerVerdictOf(score);
}

function formatPercent(value: unknown): string {
  return typeof value === "number" ? `${Math.round(value * 100)}%` : "—";
}

function formatDateTime(value?: string | null): string {
  if (!value) return "—";
  return new Date(value).toLocaleString();
}

function formatDuration(value?: number | null): string {
  if (typeof value !== "number") return "—";
  if (value < 1000) return `${value} ms`;
  const seconds = value / 1000;
  if (seconds < 60) return `${seconds.toFixed(seconds < 10 ? 1 : 0)} s`;
  const minutes = Math.floor(seconds / 60);
  const remainder = Math.round(seconds % 60);
  return `${minutes}m ${remainder}s`;
}

function successRate(row: any): number {
  return typeof row?.success_rate === "number" ? row.success_rate : -1;
}

function executorText(row: any, emptyLabel: string): string {
  return row?.executor_name || row?.key || emptyLabel;
}

function executorKey(row: any): string {
  return row?.executor_name || row?.key || "(none)";
}

function heatTone(rate: number): string {
  if (rate >= 0.75) return "bg-red-100 text-red-900 border-red-200";
  if (rate >= 0.5) return "bg-orange-100 text-orange-900 border-orange-200";
  if (rate >= 0.25) return "bg-amber-100 text-amber-900 border-amber-200";
  if (rate >= 0) return "bg-emerald-50 text-emerald-900 border-emerald-200";
  return "bg-gray-50 text-gray-400 border-gray-200";
}

export default function RunDetail() {
  const { t, language } = useI18n();
  const { id = "" } = useParams();
  const token = useAuth(s => s.token);
  const queryClient = useQueryClient();
  const [events, setEvents] = useState<any[]>([]);
  const [tab, setTab] = useState<Tab>("overview");
  const [detailAttemptId, setDetailAttemptId] = useState<string | null>(null);
  const [attemptVerdict, setAttemptVerdict] = useState("");
  const [attemptStatus, setAttemptStatus] = useState("");
  const [attemptTarget, setAttemptTarget] = useState("");
  const [attemptExecutor, setAttemptExecutor] = useState("");
  const [attemptPage, setAttemptPage] = useState(0);
  const [attemptLimit, setAttemptLimit] = useState(50);
  const [judgeTargetId, setJudgeTargetId] = useState("");

  const { data: run } = useQuery({
    queryKey: ["run", id],
    queryFn: async () => (await api.get(`/api/runs/${id}`)).data,
    refetchInterval: (q) => isTerminalStatus(q.state.data?.status) ? false : 2000,
  });
  const pollInterval: number | false = isTerminalStatus(run?.status) ? false : 2000;
  const { data: attemptsPage = { items: [], total: 0, offset: 0, limit: attemptLimit } } = useQuery({
    queryKey: ["run-attempts", id, attemptVerdict, attemptStatus, attemptTarget, attemptExecutor, attemptPage, attemptLimit],
    queryFn: async () => (await api.get(`/api/runs/${id}/attempts`, {
      params: {
        paged: true,
        limit: attemptLimit,
        offset: attemptPage * attemptLimit,
        verdict: attemptVerdict || undefined,
        status: attemptStatus || undefined,
        target_id: attemptTarget || undefined,
        executor: attemptExecutor || undefined,
      },
    })).data,
    refetchInterval: pollInterval,
  });
  const attempts = attemptsPage.items ?? [];
  const attemptTotal = attemptsPage.total ?? attempts.length;
  const attemptOffset = attemptsPage.offset ?? attemptPage * attemptLimit;
  const attemptPageCount = Math.max(1, Math.ceil(attemptTotal / attemptLimit));
  const attemptPageNumbers = useMemo(
    () => buildPageWindow({ page: attemptPage, pageCount: attemptPageCount }),
    [attemptPage, attemptPageCount],
  );
  const { data: scoresRaw = [] } = useQuery({
    queryKey: ["run-scores", id],
    queryFn: async () => (await api.get(`/api/runs/${id}/scores`)).data,
    refetchInterval: pollInterval,
  });
  const scores = Array.isArray(scoresRaw) ? scoresRaw : (scoresRaw.items ?? []);
  const { data: report } = useQuery({
    queryKey: ["run-report", id],
    queryFn: async () => (await api.get(`/api/runs/${id}/report`)).data,
    refetchInterval: pollInterval,
  });
  const { data: targets = [] } = useQuery({
    queryKey: ["targets"],
    queryFn: async () => (await api.get("/api/targets")).data,
  });

  useEffect(() => {
    if (!id || !token || isTerminalStatus(run?.status)) return;
    const url = `${api.defaults.baseURL}/api/runs/${id}/events?token=${encodeURIComponent(token)}`;
    const es = new EventSource(url);
    es.onmessage = (e) => setEvents(prev => [...prev.slice(-199), JSON.parse(e.data)]);
    // Intentionally no onerror handler — EventSource auto-reconnects on transient
    // network errors. The cleanup below closes the stream on unmount.
    return () => es.close();
  }, [id, token, run?.status]);

  useEffect(() => {
    const maxPage = Math.max(0, Math.ceil(attemptTotal / attemptLimit) - 1);
    if (attemptPage > maxPage) setAttemptPage(maxPage);
  }, [attemptLimit, attemptPage, attemptTotal]);

  const scoreByAttempt = useMemo(() => {
    const m = new Map<string, any>();
    for (const s of scores as any[]) {
      const current = m.get(s.attempt_id);
      if (!current || (isScoreFailed(current) && !isScoreFailed(s))) m.set(s.attempt_id, s);
    }
    return m;
  }, [scores]);

  const failedScores = useMemo(
    () => (scores as any[]).filter(score => isScoreFailed(score) && score.retryable !== false),
    [scores],
  );

  const attackMetrics = useMemo(() => {
    if (report?.totals) {
      return {
        refused: report.totals.refused ?? 0,
        complied: report.totals.complied ?? 0,
        scored: report.totals.scored ?? 0,
        attempts: report.totals.attempts ?? 0,
        failed: report.totals.failed ?? 0,
        unscored: report.totals.unscored ?? 0,
        successRate: report.totals.success_rate ?? null,
      };
    }
    let refused = 0, complied = 0;
    for (const s of scores as any[]) {
      const verdict = verdictOf(s);
      if (verdict === "refused") refused++;
      else if (verdict === "complied") complied++;
    }
    const scored = refused + complied;
    return {
      refused,
      complied,
      scored,
      attempts: attempts.length,
      failed: 0,
      unscored: Math.max(0, attempts.length - scored),
      successRate: scored ? complied / scored : null,
    };
  }, [attempts.length, scores, report]);

  const targetRiskRows = useMemo(
    () => [...(report?.by_target ?? [])].sort((a: any, b: any) => successRate(b) - successRate(a)),
    [report],
  );
  const executorRiskRows = useMemo(
    () => [...(report?.by_executor ?? [])].sort((a: any, b: any) => successRate(b) - successRate(a)),
    [report],
  );
  const targetExecutorRows = useMemo(
    () => [...(report?.by_target_executor ?? [])].sort((a: any, b: any) => successRate(b) - successRate(a)),
    [report],
  );
  const heatTargets = useMemo(() => {
    const seen = new Map<string, string>();
    for (const row of targetExecutorRows) {
      const key = row.target_id ?? row.target_name ?? row.key;
      seen.set(key, row.target_name ?? key);
    }
    return [...seen.entries()];
  }, [targetExecutorRows]);
  const heatExecutors = useMemo(() => {
    const seen = new Map<string, string>();
    for (const row of targetExecutorRows) {
      seen.set(executorKey(row), executorText(row, t("No executor")));
    }
    return [...seen.entries()];
  }, [targetExecutorRows, t]);
  const targetExecutorByKey = useMemo(() => {
    const out = new Map<string, any>();
    for (const row of targetExecutorRows) {
      out.set(`${row.target_id ?? row.target_name ?? row.key}|${executorKey(row)}`, row);
    }
    return out;
  }, [targetExecutorRows]);
  const highRiskActions = useMemo(
    () => targetExecutorRows.filter((row: any) => (row.scored ?? 0) >= ACTION_MIN_SCORED).slice(0, 3),
    [targetExecutorRows],
  );

  const targetOptions = useMemo(() => {
    const seen = new Map<string, string>();
    for (const row of report?.by_target ?? []) {
      seen.set(row.target_id ?? row.target_name ?? row.key, row.target_name ?? row.key);
    }
    return [...seen.entries()];
  }, [report]);
  const executorOptions = useMemo<[string, string][]>(() => {
    const rows = report?.by_executor ?? [];
    return rows.map((row: any) => [executorKey(row), executorText(row, t("No executor"))]);
  }, [report, t]);

  const cancelMut = useMutation({
    mutationFn: async () => (await api.post(`/api/runs/${id}/cancel`)).data,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["run", id] });
      queryClient.invalidateQueries({ queryKey: ["run-report", id] });
      toast.success(t("Run cancelled"));
    },
    onError: (e: any) => toast.error(e?.response?.data?.detail ?? t("Failed to cancel run")),
  });
  const pauseMut = useMutation({
    mutationFn: async () => (await api.post(`/api/runs/${id}/pause`)).data,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["run", id] });
      queryClient.invalidateQueries({ queryKey: ["run-report", id] });
      queryClient.invalidateQueries({ queryKey: ["run-attempts"] });
      toast.success(t("Run pause requested"));
    },
    onError: (e: any) => toast.error(e?.response?.data?.detail ?? t("Failed to pause run")),
  });
  const resumeMut = useMutation({
    mutationFn: async (retryFailed: boolean) => (await api.post(`/api/runs/${id}/resume`, { retry_failed: retryFailed })).data,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["run", id] });
      queryClient.invalidateQueries({ queryKey: ["run-report", id] });
      queryClient.invalidateQueries({ queryKey: ["run-attempts"] });
      toast.success(t("Run resumed"));
    },
    onError: (e: any) => toast.error(e?.response?.data?.detail ?? t("Failed to resume run")),
  });
  const retryScoresMut = useMutation({
    mutationFn: async () => (await api.post(`/api/runs/${id}/scores/retry`, { failed_only: true })).data,
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["run-scores", id] });
      queryClient.invalidateQueries({ queryKey: ["run-attempts", id] });
      queryClient.invalidateQueries({ queryKey: ["run-report", id] });
      toast.success(t("Retried {{count}} judge scores", { count: data?.retried ?? 0 }));
    },
    onError: (e: any) => toast.error(e?.response?.data?.detail ?? t("Failed to retry judge scores")),
  });
  const rejudgeMut = useMutation({
    mutationFn: async (judgeConfigId: string) => (await api.post(`/api/runs/${id}/scores/retry`, {
      failed_only: false,
      scorer_ref: { plugin: "llm_judge", params: { judge_config_id: judgeConfigId } },
    })).data,
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["run-scores", id] });
      queryClient.invalidateQueries({ queryKey: ["run-attempts", id] });
      queryClient.invalidateQueries({ queryKey: ["run-report", id] });
      toast.success(t("Rejudged {{count}} attempts", { count: data?.retried ?? 0 }));
    },
    onError: (e: any) => toast.error(e?.response?.data?.detail ?? t("Failed to rejudge run")),
  });
  const retryAttemptMut = useMutation({
    mutationFn: async (attemptId: string) => (await api.post(`/api/runs/${id}/attempts/${attemptId}/retry`)).data,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["run", id] });
      queryClient.invalidateQueries({ queryKey: ["run-report", id] });
      queryClient.invalidateQueries({ queryKey: ["run-attempts", id] });
      queryClient.invalidateQueries({ queryKey: ["run-scores", id] });
      toast.success(t("Retried failed attempt"));
    },
    onError: (e: any) => toast.error(e?.response?.data?.detail ?? t("Failed to retry attempt")),
  });

  const downloadExport = async (format: RunExportFormat) => {
    const response = await api.get(`/api/runs/${id}/export`, {
      params: { format },
      responseType: "blob",
    });
    const url = URL.createObjectURL(response.data);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${run?.name ?? "run"}-${id.slice(0, 8)}.${format}`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  };

  const downloadFilteredAttemptsExport = async (format: RunExportFormat) => {
    const response = await api.get(`/api/runs/${id}/export`, {
      params: buildAttemptExportParams(format, {
        verdict: attemptVerdict,
        status: attemptStatus,
        targetId: attemptTarget,
        executor: attemptExecutor,
      }),
      responseType: "blob",
    });
    const url = URL.createObjectURL(response.data);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${run?.name ?? "run"}-${id.slice(0, 8)}-filtered-attempts.${format}`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  };

  const downloadHtmlReport = async () => {
    const response = await api.get(`/api/runs/${id}/report.html`, {
      params: buildHtmlReportExportParams(language),
      responseType: "blob",
    });
    const url = URL.createObjectURL(response.data);
    const a = document.createElement("a");
    a.href = url;
    a.download = buildRunReportFilename(run?.name, id);
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  };

  const focusTargetComplied = (targetId: string | undefined, executorValue?: string) => {
    if (!targetId) return;
    setAttemptTarget(targetId);
    setAttemptExecutor(executorValue ?? "");
    setAttemptVerdict("complied");
    setAttemptPage(0);
    setTab("attempts");
  };

  const highestRiskTarget = targetRiskRows.find((row: any) => (row.scored ?? 0) > 0);
  const highestRiskExecutor = executorRiskRows.find((row: any) => (row.scored ?? 0) > 0);
  const highestRiskTargetExecutor = targetExecutorRows.find((row: any) => (row.scored ?? 0) > 0);
  const runTabs: Array<TabItem<Tab>> = [
    { id: "overview", label: t("Overview") },
    { id: "attempts", label: t("Attempts ({{count}})", { count: attemptsPage.total ?? attempts.length }) },
    { id: "events", label: t("Live events") },
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <Link to="/runs" className="inline-flex items-center gap-1 text-xs text-gray-500 hover:text-gray-700 mb-2">
            <ArrowLeft className="h-3 w-3" /> {t("Back to runs")}
          </Link>
          <h1 className="text-2xl font-bold tracking-tight">{run?.name ?? t("Run")}</h1>
          <div className="flex items-center gap-3 mt-2">
            {run && <StatusBadge status={run.status} />}
            <span className="text-xs text-gray-500 font-mono">{id.slice(0, 8)}</span>
            {!!run?.target_names?.length && (
              <span className="text-xs text-gray-600">{run.target_names.join(", ")}</span>
            )}
            {run?.started_at && (
              <span className="inline-flex items-center gap-1 text-xs text-gray-500">
                <Clock className="h-3 w-3" />
                {t("Started")} {formatDateTime(run.started_at)}
              </span>
            )}
            {typeof run?.duration_ms === "number" && (
              <span className="text-xs text-gray-500">
                {t("Duration")} {formatDuration(run.duration_ms)}
              </span>
            )}
          </div>
          {run?.error && <div className="mt-2 text-xs text-red-600">{run.error}</div>}
        </div>
        <div className="flex flex-wrap justify-end gap-2">
          <Button variant="secondary" size="sm" icon={<Download className="h-4 w-4" />}
            onClick={() => downloadExport("json")}>
            {t("Export JSON")}
          </Button>
          <Button variant="secondary" size="sm" icon={<Download className="h-4 w-4" />}
            onClick={() => downloadExport("csv")}>
            {t("Export CSV")}
          </Button>
          {run?.kind === "automated" && (
            <Button variant="secondary" size="sm" icon={<Download className="h-4 w-4" />}
              onClick={downloadHtmlReport}>
              {t("Export HTML report")}
            </Button>
          )}
          {run?.kind === "automated" && run?.status === "running" && (
            <Button variant="secondary" size="sm" icon={<Pause className="h-4 w-4" />}
              loading={pauseMut.isPending}
              onClick={() => pauseMut.mutate()}>
              {t("Pause run")}
            </Button>
          )}
          {run?.kind === "automated" && ["paused", "failed"].includes(run?.status) && (
            <>
              <Button variant="secondary" size="sm" icon={<Play className="h-4 w-4" />}
                loading={resumeMut.isPending && resumeMut.variables === false}
                onClick={() => resumeMut.mutate(false)}>
                {t("Resume run")}
              </Button>
              <Button variant="secondary" size="sm" icon={<RotateCcw className="h-4 w-4" />}
                loading={resumeMut.isPending && resumeMut.variables === true}
                onClick={() => resumeMut.mutate(true)}>
                {t("Resume retrying failed")}
              </Button>
            </>
          )}
          {failedScores.length > 0 && (
            <Button variant="secondary" size="sm" icon={<RotateCcw className="h-4 w-4" />}
              loading={retryScoresMut.isPending}
              onClick={() => retryScoresMut.mutate()}>
              {t("Retry failed judges ({{count}})", { count: failedScores.length })}
            </Button>
          )}
          {run?.kind === "automated" && run?.status === "completed" && (
            <div className="flex items-end gap-2">
              <div className="min-w-44">
                <Field label={t("Judger target")}>
                  <Select
                    className="h-8 text-xs"
                    value={judgeTargetId}
                    onChange={e => setJudgeTargetId(e.target.value)}
                  >
                    <option value="">{t("-- pick judger --")}</option>
                    {targets.map((target: any) => (
                      <option key={target.id} value={target.id}>{target.name}</option>
                    ))}
                  </Select>
                </Field>
                {!judgeTargetId && (
                  <p className="mt-1 text-xs text-gray-500">{t("Choose a judger target to rejudge this run.")}</p>
                )}
              </div>
              <Button
                variant="secondary"
                size="sm"
                icon={<RotateCcw className="h-4 w-4" />}
                loading={rejudgeMut.isPending}
                disabled={!judgeTargetId}
                onClick={() => rejudgeMut.mutate(judgeTargetId)}
              >
                {t("Rejudge run")}
              </Button>
            </div>
          )}
          {run?.kind === "automated" && ["running", "pausing", "paused"].includes(run?.status) && (
            <Button variant="danger" size="sm" icon={<Ban className="h-4 w-4" />}
              loading={cancelMut.isPending}
              onClick={() => cancelMut.mutate()}>
              {t("Cancel run")}
            </Button>
          )}
        </div>
      </div>
      {run?.status === "pausing" && (
        <div className="rounded-md border border-sky-200 bg-sky-50 px-3 py-2 text-sm text-sky-800">
          {t("Pause requested. Waiting for in-flight attempts to finish.")}
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-3 xl:grid-cols-5 gap-4">
        <StatCard label={t("Attack success rate")} value={formatPercent(attackMetrics.successRate)} tone="red" />
        <StatCard label={t("Attack successes")} value={attackMetrics.complied} tone="red" />
        <StatCard label={t("Refused")} value={attackMetrics.refused} tone="green" />
        <StatCard label={t("Effective scores")} value={`${attackMetrics.scored}/${attackMetrics.attempts}`} tone="brand" />
        <Card><CardBody>
          <div className="text-xs text-gray-500 mb-1">{t("Progress")}</div>
          <ProgressBar done={run?.progress_done ?? 0} total={run?.progress_total ?? 0} />
        </CardBody></Card>
      </div>

      <Tabs tabs={runTabs} value={tab} onChange={setTab} idBase="run-detail">
        {activeTab => (
          <>
      {activeTab === "overview" && (
        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>{t("Next actions")}</CardTitle>
              <CardDescription>{t("Start with high-risk combinations that have enough scored attempts.")}</CardDescription>
            </CardHeader>
            <CardBody>
              {highRiskActions.length ? (
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-3">
                  {highRiskActions.map((row: any) => (
                    <ActionSuggestion
                      key={`${row.target_id ?? row.target_name ?? row.key}|${executorKey(row)}`}
                      target={row.target_name ?? row.key}
                      method={executorText(row, t("No executor"))}
                      rate={row.success_rate}
                      complied={row.complied ?? 0}
                      scored={row.scored ?? 0}
                      failed={row.failed ?? 0}
                      unscored={row.unscored ?? 0}
                      onClick={() => focusTargetComplied(
                        row.target_id ?? row.target_name ?? row.key,
                        executorKey(row),
                      )}
                    />
                  ))}
                </div>
              ) : (
                <div className="rounded-md border border-gray-200 bg-gray-50 px-3 py-4 text-sm text-gray-500">
                  {t("No high-risk combinations with at least {{count}} scored attempts.", { count: ACTION_MIN_SCORED })}
                </div>
              )}
            </CardBody>
          </Card>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
            <RiskSummaryCard
              label={t("Highest-risk target")}
              title={highestRiskTarget?.target_name ?? highestRiskTarget?.key ?? "—"}
              rate={highestRiskTarget?.success_rate}
              detail={highestRiskTarget ? t("{{count}} scored", { count: highestRiskTarget.scored ?? 0 }) : t("No scored attempts yet.")}
            />
            <RiskSummaryCard
              label={t("Highest-risk attack method")}
              title={highestRiskExecutor ? executorText(highestRiskExecutor, t("No executor")) : "—"}
              rate={highestRiskExecutor?.success_rate}
              detail={highestRiskExecutor ? t("{{count}} scored", { count: highestRiskExecutor.scored ?? 0 }) : t("No scored attempts yet.")}
            />
            <RiskSummaryCard
              label={t("Highest-risk combination")}
              title={highestRiskTargetExecutor
                ? `${highestRiskTargetExecutor.target_name ?? highestRiskTargetExecutor.key} · ${executorText(highestRiskTargetExecutor, t("No executor"))}`
                : "—"}
              rate={highestRiskTargetExecutor?.success_rate}
              detail={highestRiskTargetExecutor ? t("{{count}} scored", { count: highestRiskTargetExecutor.scored ?? 0 }) : t("No scored attempts yet.")}
            />
          </div>

          <Card>
            <CardHeader>
              <CardTitle>{t("Target × attack method risk matrix")}</CardTitle>
              <CardDescription>{t("Darker cells indicate higher attack success rate.")}</CardDescription>
            </CardHeader>
            <CardBody>
              {targetExecutorRows.length ? (
                <div className="overflow-x-auto">
                  <table className="w-full min-w-[720px] text-sm">
                    <thead className="text-xs uppercase tracking-wider text-gray-500">
                      <tr>
                        <th className="text-left px-3 py-2">{t("Target")}</th>
                        {heatExecutors.map(([key, label]) => (
                          <th key={key} className="text-left px-3 py-2">{label}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100">
                      {heatTargets.map(([targetId, targetName]) => (
                        <tr key={targetId}>
                          <td className="px-3 py-2 font-medium text-gray-800 whitespace-nowrap">{targetName}</td>
                          {heatExecutors.map(([key]) => {
                            const row = targetExecutorByKey.get(`${targetId}|${key}`);
                            const rate = successRate(row);
                            return (
                              <td key={key} className="px-3 py-2 align-top">
                                {row ? (
                                  <button
                                    className={clsx("w-full rounded-md border px-2 py-2 text-left transition hover:ring-2 hover:ring-brand-200", heatTone(rate))}
                                    onClick={() => focusTargetComplied(
                                      row.target_id ?? row.target_name ?? row.key,
                                      executorKey(row),
                                    )}
                                  >
                                    <div className="font-semibold tabular-nums">{formatPercent(row.success_rate)}</div>
                                    <div className="text-[11px] opacity-80">
                                      {row.complied}/{row.scored} · {t("{{count}} attempts", { count: row.attempts ?? 0 })}
                                    </div>
                                  </button>
                                ) : (
                                  <div className="rounded-md border border-gray-200 bg-gray-50 px-2 py-2 text-gray-400">—</div>
                                )}
                              </td>
                            );
                          })}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className="text-sm text-gray-500 py-8 text-center">{t("No scored attempts yet.")}</div>
              )}
            </CardBody>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>{t("Risk ranking")}</CardTitle>
              <CardDescription>{t("Click a row to inspect successful attacks for that target.")}</CardDescription>
            </CardHeader>
            <CardBody>
              {targetExecutorRows.length ? (
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead className="bg-gray-50 text-gray-600 text-xs uppercase tracking-wider">
                      <tr>
                        <th className="text-left px-4 py-2">{t("Target")}</th>
                        <th className="text-left px-4 py-2">{t("Attack method")}</th>
                        <th className="text-left px-4 py-2">{t("Attack success rate")}</th>
                        <th className="text-left px-4 py-2">{t("Attack successes")}</th>
                        <th className="text-left px-4 py-2">{t("Refused")}</th>
                        <th className="text-left px-4 py-2">{t("Failed")}</th>
                        <th className="text-left px-4 py-2">{t("Unscored")}</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100">
                      {targetExecutorRows.map((row: any) => (
                        <tr
                          key={`${row.target_id ?? row.target_name ?? row.key}|${executorKey(row)}`}
                          className="hover:bg-gray-50 cursor-pointer"
                          onClick={() => focusTargetComplied(
                            row.target_id ?? row.target_name ?? row.key,
                            executorKey(row),
                          )}
                        >
                          <td className="px-4 py-2 font-medium text-gray-800">{row.target_name ?? row.key}</td>
                          <td className="px-4 py-2 text-gray-600">{executorText(row, t("No executor"))}</td>
                          <td className="px-4 py-2 font-semibold tabular-nums text-red-600">{formatPercent(row.success_rate)}</td>
                          <td className="px-4 py-2 tabular-nums">{row.complied ?? 0}</td>
                          <td className="px-4 py-2 tabular-nums">{row.refused ?? 0}</td>
                          <td className="px-4 py-2 tabular-nums">{row.failed ?? 0}</td>
                          <td className="px-4 py-2 tabular-nums">{row.unscored ?? 0}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className="text-sm text-gray-500 py-8 text-center">{t("No scored attempts yet.")}</div>
              )}
            </CardBody>
          </Card>
        </div>
      )}

      {activeTab === "attempts" && (
        <Card>
          <CardBody className="border-b border-gray-100">
            <div className="flex flex-col gap-3">
              <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
                <select className="input" value={attemptVerdict} onChange={e => { setAttemptVerdict(e.target.value); setAttemptPage(0); }}>
                  <option value="">{t("All verdicts")}</option>
                  <option value="refused">{t("refused")}</option>
                  <option value="complied">{t("complied")}</option>
                  <option value="unscored">{t("Unscored")}</option>
                </select>
                <select className="input" value={attemptStatus} onChange={e => { setAttemptStatus(e.target.value); setAttemptPage(0); }}>
                  <option value="">{t("All statuses")}</option>
                  <option value="completed">{t("Completed")}</option>
                  <option value="failed">{t("Failed")}</option>
                  <option value="skipped">{t("Skipped")}</option>
                </select>
                <select className="input" value={attemptTarget} onChange={e => { setAttemptTarget(e.target.value); setAttemptPage(0); }}>
                  <option value="">{t("All targets")}</option>
                  {targetOptions.map(([value, label]) => <option key={value} value={value}>{label}</option>)}
                </select>
                <select className="input" value={attemptExecutor} onChange={e => { setAttemptExecutor(e.target.value); setAttemptPage(0); }}>
                  <option value="">{t("All attack methods")}</option>
                  {executorOptions.map(([value, label]) => <option key={value} value={value}>{label}</option>)}
                </select>
              </div>
              <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                <div className="text-xs text-gray-500">
                  {t("Showing {{range}}", {
                    range: formatPaginationRange({ total: attemptTotal, offset: attemptOffset, limit: attemptLimit }),
                  })}
                </div>
                <div className="flex flex-wrap gap-2">
                  <Button variant="secondary" size="sm" icon={<Download className="h-4 w-4" />}
                    onClick={() => downloadFilteredAttemptsExport("json")}>
                    {t("Export filtered JSON")}
                  </Button>
                  <Button variant="secondary" size="sm" icon={<Download className="h-4 w-4" />}
                    onClick={() => downloadFilteredAttemptsExport("csv")}>
                    {t("Export filtered CSV")}
                  </Button>
                </div>
              </div>
            </div>
          </CardBody>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 text-gray-600 text-xs uppercase tracking-wider">
                <tr>
                  <th className="text-left px-5 py-2.5">{t("Target")}</th>
                  <th className="text-left px-5 py-2.5">{t("Status")}</th>
                  <th className="text-left px-5 py-2.5">{t("Test time")}</th>
                  <th className="text-left px-5 py-2.5">{t("Original prompt")}</th>
                  <th className="text-left px-5 py-2.5">{t("Transformed prompt")}</th>
                  <th className="text-left px-5 py-2.5">{t("LLM response")}</th>
                  <th className="text-left px-5 py-2.5">{t("Score")}</th>
                  <th className="px-5 py-2.5"></th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {attempts.map((a: any) => {
                  const sc = scoreByAttempt.get(a.id);
                  const verdict = sc ? verdictOf(sc) : null;
                  const scoreFailed = sc ? isScoreFailed(sc) : false;
                  return (
                    <tr key={a.id} className="align-top hover:bg-gray-50/60">
                      <td className="px-5 py-3 font-medium whitespace-nowrap">{a.target_name}</td>
                      <td className="px-5 py-3 whitespace-nowrap"><StatusBadge status={a.status} /></td>
                      <td className="px-5 py-3 text-gray-600 whitespace-nowrap">{formatDuration(a.duration_ms)}</td>
                      <td className="px-5 py-3 max-w-xs">
                        <div className="truncate text-gray-700" title={a.original_prompt ?? a.prompt}>
                          {a.original_prompt ?? a.prompt}
                        </div>
                      </td>
                      <td className="px-5 py-3 max-w-xs">
                        <div className="truncate text-gray-700" title={a.transformed_prompt ?? a.prompt}>
                          {a.transformed_prompt ?? a.prompt}
                        </div>
                      </td>
                      <td className="px-5 py-3 max-w-md"><div className="truncate text-gray-600" title={a.response ?? ""}>{a.response ?? <span className="text-gray-400">({t("blob")})</span>}</div></td>
                      <td className="px-5 py-3">
                        {scoreFailed ? <Badge tone="amber">{t("Judge failed")}</Badge>
                          : verdict === "refused" ? <Badge tone="green">{t("refused")}</Badge>
                          : verdict === "complied" ? <Badge tone="red">{t("complied")}</Badge>
                          : <Badge>-</Badge>}
                      </td>
                      <td className="px-5 py-3 text-right">
                        <div className="flex justify-end gap-2">
                          {run?.kind === "automated" && a.status === "failed" && (
                            <Button
                              variant="secondary"
                              size="sm"
                              icon={<RotateCcw className="h-3.5 w-3.5" />}
                              loading={retryAttemptMut.isPending && retryAttemptMut.variables === a.id}
                              onClick={() => retryAttemptMut.mutate(a.id)}
                            >
                              {t("Retry attempt")}
                            </Button>
                          )}
                          <Button
                            variant="ghost"
                            size="sm"
                            aria-label={t("Inspect attempt {{id}}", { id: a.id.slice(0, 8) })}
                            onClick={() => setDetailAttemptId(a.id)}
                          >
                            {t("Inspect")}
                          </Button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
                {!attempts.length && (
                  <tr><td colSpan={8} className="px-5 py-10 text-center text-sm text-gray-500">{t("No attempts yet.")}</td></tr>
                )}
              </tbody>
            </table>
          </div>
          <CardBody className="flex flex-col gap-3 border-t border-gray-100 lg:flex-row lg:items-center lg:justify-between">
            <div className="flex flex-wrap items-center gap-2 text-xs text-gray-600">
              <span>{t("Showing {{range}}", {
                range: formatPaginationRange({ total: attemptTotal, offset: attemptOffset, limit: attemptLimit }),
              })}</span>
              <label className="inline-flex items-center gap-2">
                <span>{t("Page size")}</span>
                <select
                  className="input h-8 w-20 text-xs"
                  value={attemptLimit}
                  onChange={e => {
                    setAttemptLimit(Number(e.target.value));
                    setAttemptPage(0);
                  }}
                >
                  {[25, 50, 100, 200].map(value => (
                    <option key={value} value={value}>{value}</option>
                  ))}
                </select>
              </label>
            </div>
            <div className="flex flex-wrap items-center justify-end gap-1">
              <Button
                variant="secondary"
                size="sm"
                aria-label={t("First page")}
                icon={<ChevronsLeft className="h-4 w-4" />}
                disabled={attemptPage === 0}
                onClick={() => setAttemptPage(0)}
              />
              <Button
                variant="secondary"
                size="sm"
                aria-label={t("Previous")}
                icon={<ChevronLeft className="h-4 w-4" />}
                disabled={attemptPage === 0}
                onClick={() => setAttemptPage(p => Math.max(0, p - 1))}
              />
              {attemptPageNumbers.map(pageNumber => (
                <Button
                  key={pageNumber}
                  variant={pageNumber - 1 === attemptPage ? "primary" : "secondary"}
                  size="sm"
                  aria-label={t("Page {{page}}", { page: pageNumber })}
                  onClick={() => setAttemptPage(pageNumber - 1)}
                >
                  {pageNumber}
                </Button>
              ))}
              <Button
                variant="secondary"
                size="sm"
                aria-label={t("Next")}
                icon={<ChevronRight className="h-4 w-4" />}
                disabled={attemptPage >= attemptPageCount - 1}
                onClick={() => setAttemptPage(p => Math.min(attemptPageCount - 1, p + 1))}
              />
              <Button
                variant="secondary"
                size="sm"
                aria-label={t("Last page")}
                icon={<ChevronsRight className="h-4 w-4" />}
                disabled={attemptPage >= attemptPageCount - 1}
                onClick={() => setAttemptPage(attemptPageCount - 1)}
              />
            </div>
          </CardBody>
        </Card>
      )}

      {activeTab === "events" && (
        <Card>
          <CardHeader>
            <CardTitle>{t("Live events")}</CardTitle>
            <CardDescription>
              {isTerminalStatus(run?.status)
                ? t("Live stream is inactive for terminal runs.")
                : t("Streamed via Server-Sent Events. Last 200 messages.")}
            </CardDescription>
          </CardHeader>
          <CardBody>
            <pre className="text-xs bg-gray-900 text-gray-100 rounded-lg p-3 max-h-80 overflow-auto font-mono">
{events.length
  ? events.map(e => JSON.stringify(e)).join("\n")
  : isTerminalStatus(run?.status)
    ? t("This run is complete. Live events are only shown while a run is active.")
    : t("(waiting for events…)")}
            </pre>
          </CardBody>
        </Card>
      )}
          </>
        )}
      </Tabs>

      <AttemptDetailDrawer
        runId={id}
        attempt={detailAttemptId ? attempts.find((a: any) => a.id === detailAttemptId) ?? null : null}
        scores={detailAttemptId ? (scores as any[]).filter(s => s.attempt_id === detailAttemptId) : []}
        onClose={() => setDetailAttemptId(null)}
      />
    </div>
  );
}

function AttemptDetailDrawer({ runId, attempt, scores, onClose }: { runId: string; attempt: any | null; scores: any[]; onClose: () => void }) {
  const { t } = useI18n();
  const nav = useNavigate();
  const { data: conversation } = useQuery({
    queryKey: ["attempt-conversation", runId, attempt?.id],
    queryFn: async () => {
      if (!attempt) return { messages: [] };
      const attemptRunId = attempt.run_id ?? runId;
      const res = await api.get(`/api/runs/${attemptRunId}/attempts/${attempt.id}/conversation`);
      return res.data;
    },
    enabled: !!attempt,
  });
  const { data: promptSnapshot } = useQuery({
    queryKey: ["attempt-prompt-snapshot", runId, attempt?.id],
    queryFn: async () => {
      if (!attempt) return null;
      const attemptRunId = attempt.run_id ?? runId;
      const res = await api.get(`/api/runs/${attemptRunId}/attempts/${attempt.id}/prompt-snapshot`);
      return res.data;
    },
    enabled: !!attempt?.prompt_snapshot_blob_path,
  });

  const replayMut = useMutation({
    mutationFn: async ({ name, target_id, attempt_id }: { name: string; target_id: string; attempt_id: string }) => {
      const createRes = await api.post("/api/manual/runs", { name, target_id });
      const runId = createRes.data.run_id;
      const convRes = await api.post(`/api/manual/runs/${runId}/conversations`, { seed_attempt_id: attempt_id });
      return { run_id: runId, attempt_id: convRes.data.attempt_id };
    },
    onSuccess: (data) => {
      nav(`/manual?run=${data.run_id}&attempt=${data.attempt_id}`);
    },
    onError: () => toast.error(t("Failed to start replay")),
  });

  useEffect(() => {
    if (!attempt) return;
    const onKey = (e: KeyboardEvent) => { if (e.key === "Escape") onClose(); };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [attempt, onClose]);

  if (!attempt) return null;
  const chain = Array.isArray(attempt.converter_chain) ? attempt.converter_chain : [];
  const messages = conversation?.messages ?? [];

  const handleReplay = () => {
    if (!attempt.target_id) {
      toast.error(t("Cannot replay: target_id not available"));
      return;
    }
    const replayName = t("Replay of attempt {{id}}", { id: attempt.id.slice(0, 8) });
    replayMut.mutate({ name: replayName, target_id: attempt.target_id, attempt_id: attempt.id });
  };

  return (
    <div className="fixed inset-0 z-50 flex">
      <div className="flex-1 bg-gray-900/40 backdrop-blur-sm" onClick={onClose} />
      <div className="w-full max-w-2xl bg-white shadow-2xl overflow-y-auto border-l border-gray-200">
        <div className="sticky top-0 z-10 flex items-center justify-between px-6 py-4 border-b border-gray-200 bg-white/90 backdrop-blur">
          <div>
            <div className="text-xs text-gray-500">{t("Attempt")}</div>
            <div className="font-semibold text-gray-900">{attempt.target_name}</div>
            <div className="text-[10px] font-mono text-gray-400 mt-0.5">{attempt.id}</div>
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-700 p-1 rounded hover:bg-gray-100">
            <X className="h-4 w-4" />
          </button>
        </div>

        <div className="px-6 py-5 space-y-5">
          <div className="flex flex-wrap items-center gap-2 text-xs text-gray-600">
            <StatusBadge status={attempt.status} />
            {attempt.executor_name && (
              <span className="inline-flex items-center gap-1">
                {t("executor")}:
                <Badge>{attempt.executor_name}</Badge>
              </span>
            )}
            {attempt.dataset_item_language && (
              <span className="inline-flex items-center gap-1">
                {t("Language")}:
                <Badge>{attempt.dataset_item_language}</Badge>
              </span>
            )}
            {typeof attempt.latency_ms === "number" && (
              <span className="inline-flex items-center gap-1"><Clock className="h-3 w-3" />{attempt.latency_ms} ms</span>
            )}
            {typeof attempt.duration_ms === "number" && (
              <span className="inline-flex items-center gap-1">
                <Clock className="h-3 w-3" />
                {t("Test time")} {formatDuration(attempt.duration_ms)}
              </span>
            )}
            {attempt.started_at && (
              <span className="inline-flex items-center gap-1">
                {t("Started")} {formatDateTime(attempt.started_at)}
              </span>
            )}
            {attempt.finished_at && (
              <span className="inline-flex items-center gap-1">
                {t("Finished")} {formatDateTime(attempt.finished_at)}
              </span>
            )}
            {(attempt.tokens_in != null || attempt.tokens_out != null) && (
              <span className="inline-flex items-center gap-1">
                <Hash className="h-3 w-3" />
                {t("in")} {attempt.tokens_in ?? "-"} / {t("out")} {attempt.tokens_out ?? "-"}
              </span>
            )}
            {chain.length > 0 && (
              <span className="inline-flex items-center gap-1">
                {t("converters")}:
                {chain.map((c: string, i: number) => <Badge key={i}>{c}</Badge>)}
              </span>
            )}
          </div>

          {messages.length > 0 && attempt.target_id && (
            <div>
              <Button 
                variant="secondary" 
                size="sm" 
                onClick={handleReplay}
                loading={replayMut.isPending}
                icon={<MessageSquare className="h-3.5 w-3.5" />}
              >
                {t("Replay in Manual Console")}
              </Button>
            </div>
          )}

          {attempt.error && (
            <div className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-xs text-red-700 flex gap-2">
              <AlertCircle className="h-4 w-4 shrink-0 mt-0.5" />
              <span className="font-mono whitespace-pre-wrap break-words">{attempt.error}</span>
            </div>
          )}

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Section title={t("Original prompt")}>
              <pre className="text-xs whitespace-pre-wrap break-words font-mono bg-gray-50 border border-gray-200 rounded-lg p-3 text-gray-800 max-h-64 overflow-auto">
{attempt.original_prompt ?? attempt.prompt ?? ""}
              </pre>
            </Section>
            <Section title={t("Transformed prompt")}>
              <pre className="text-xs whitespace-pre-wrap break-words font-mono bg-gray-50 border border-gray-200 rounded-lg p-3 text-gray-800 max-h-64 overflow-auto">
{attempt.transformed_prompt ?? attempt.prompt ?? ""}
              </pre>
            </Section>
          </div>

          {messages.length > 0 ? (
            <Section title={t("Conversation")}>
              <div className="space-y-3">
                {messages.map((msg: any, i: number) => (
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
                    </div>
                  </div>
                ))}
              </div>
            </Section>
          ) : (
            <Section title={t("LLM response")}>
              {attempt.response ? (
                <pre className="text-xs whitespace-pre-wrap break-words font-mono bg-gray-50 border border-gray-200 rounded-lg p-3 text-gray-800 max-h-96 overflow-auto">
{attempt.response}
                </pre>
              ) : attempt.response_blob_path ? (
                <div className="text-xs text-gray-500 italic">{t("Response stored as blob")}: <span className="font-mono">{attempt.response_blob_path}</span></div>
              ) : (
                <div className="text-xs text-gray-400 italic">{t("No response")}</div>
              )}
            </Section>
          )}

          <Section title={scores.length > 1 ? t("Scores ({{count}})", { count: scores.length }) : t("Score")}>
            {scores.length === 0 ? (
              <div className="text-xs text-gray-400 italic">{t("No score yet")}</div>
            ) : (
              <div className="space-y-3">
                {scores.map((s) => <ScoreCard key={s.id} score={s} />)}
              </div>
            )}
          </Section>

          {promptSnapshot && (
            <Section title={t("Executor Prompt Snapshots")}>
              <PromptSnapshotView snapshot={promptSnapshot} />
            </Section>
          )}
        </div>
      </div>
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div>
      <div className="text-xs font-semibold uppercase tracking-wider text-gray-500 mb-1.5">{title}</div>
      {children}
    </div>
  );
}

function PromptSnapshotView({ snapshot }: { snapshot: any }) {
  const { t } = useI18n();
  const snapshots = Array.isArray(snapshot?.snapshots) ? snapshot.snapshots : [snapshot];
  return (
    <div className="space-y-3">
      {snapshots.map((item: any, idx: number) => (
        <div key={`${item.asset_id ?? "snapshot"}-${idx}`} className="rounded-lg border border-gray-200 bg-gray-50 p-3">
          <div className="flex flex-wrap items-center gap-2 text-[11px]">
            <Badge>{item.asset_id ?? t("Prompt snapshot")}</Badge>
            {item.source && <Badge>{item.source}</Badge>}
            {item.override_id && <Badge>{t("override")}</Badge>}
            {item.sha256 && <span className="font-mono text-gray-500">{item.sha256.slice(0, 12)}</span>}
          </div>
          {item.variables && (
            <details className="mt-2 text-[11px] text-gray-600">
              <summary className="cursor-pointer hover:text-gray-800">{t("Variables")}</summary>
              <pre className="mt-1 bg-white border border-gray-200 rounded p-2 font-mono overflow-auto max-h-40">
{JSON.stringify(item.variables, null, 2)}
              </pre>
            </details>
          )}
          {item.rendered_text && (
            <details className="mt-2 text-[11px] text-gray-600">
              <summary className="cursor-pointer hover:text-gray-800">{t("Rendered prompt")}</summary>
              <pre className="mt-1 bg-white border border-gray-200 rounded p-2 font-mono whitespace-pre-wrap break-words overflow-auto max-h-64">
{item.rendered_text}
              </pre>
            </details>
          )}
        </div>
      ))}
    </div>
  );
}

function ScoreCard({ score }: { score: any }) {
  const { t } = useI18n();
  const { id: runId = "" } = useParams();
  const queryClient = useQueryClient();
  const [reviewerLabel, setReviewerLabel] = useState<boolean | null>(score.reviewer_label ?? null);
  const [reviewerNotes, setReviewerNotes] = useState<string>(score.reviewer_notes ?? "");
  const [showJudgeRaw, setShowJudgeRaw] = useState(false);
  const { data: promptSnapshot } = useQuery({
    queryKey: ["score-prompt-snapshot", runId, score.id],
    queryFn: async () => (await api.get(`/api/runs/${runId}/scores/${score.id}/prompt-snapshot`)).data,
    enabled: !!score.prompt_snapshot_blob_path,
  });

  useEffect(() => {
    setReviewerLabel(score.reviewer_label ?? null);
    setReviewerNotes(score.reviewer_notes ?? "");
  }, [score.id, score.reviewer_label, score.reviewer_notes]);
  
  const saveMut = useMutation({
    mutationFn: async (body: { reviewer_label: boolean | null; reviewer_notes: string }) =>
      (await api.patch(`/api/runs/${runId}/scores/${score.id}`, body)).data,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["run-scores", runId] });
      queryClient.invalidateQueries({ queryKey: ["run-attempts", runId] });
      queryClient.invalidateQueries({ queryKey: ["run-report", runId] });
      toast.success(t("Annotation saved"));
    },
    onError: () => toast.error(t("Failed to save annotation")),
  });
  const retryMut = useMutation({
    mutationFn: async () => (await api.post(`/api/runs/${runId}/scores/retry`, {
      failed_only: false,
      score_ids: [score.id],
      attempt_ids: [score.attempt_id],
      scorers: [score.scorer],
    })).data,
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["run-scores", runId] });
      queryClient.invalidateQueries({ queryKey: ["run-attempts", runId] });
      queryClient.invalidateQueries({ queryKey: ["run-report", runId] });
      toast.success(t("Retried {{count}} judge scores", { count: data?.retried ?? 0 }));
    },
    onError: (e: any) => toast.error(e?.response?.data?.detail ?? t("Failed to retry judge score")),
  });

  const v = score?.value ?? {};
  const scoreFailed = isScoreFailed(score);
  
  const scorerVerdict = scorerVerdictOf(score);
  
  // Display verdict: use reviewer's if set, otherwise scorer's
  const displayVerdict: Verdict | null = typeof reviewerLabel === "boolean"
    ? (reviewerLabel ? "refused" : "complied")
    : scorerVerdict;
  
  const isOverridden = typeof reviewerLabel === "boolean";
  const tone = displayVerdict === "refused" ? "green" : displayVerdict === "complied" ? "red" : "amber";
  
  // Check for judge format error
  const isLLMJudge = score.scorer === "llm_judge";
  const hasParseError = isLLMJudge && v.parse_error === true;

  const handleSave = () => {
    saveMut.mutate({ reviewer_label: reviewerLabel, reviewer_notes: reviewerNotes });
  };

  return (
    <div className="rounded-lg border border-gray-200 bg-white p-3 space-y-2">
      <div className="flex items-center gap-2 text-xs">
        <span className="font-medium text-gray-700">{score.scorer}{v.judge_name ? ` · ${v.judge_name}` : ""}</span>
        <Badge tone={tone as any}>{displayVerdict ? t(displayVerdict) : t("Judge failed")}</Badge>
        {isOverridden && <span className="text-[10px] text-gray-500">{t("(overridden)")}</span>}
        {isOverridden && scorerVerdict && (
          <Badge tone={scorerVerdict === "refused" ? "green" : "red"} className="line-through opacity-50">
            {t(scorerVerdict)}
          </Badge>
        )}
        {typeof v.confidence === "number" && (
          <span className="text-gray-500">{t("confidence {{value}}", { value: v.confidence.toFixed(2) })}</span>
        )}
        {typeof v.score === "number" && (
          <span className="text-gray-500">{t("score {{value}}", { value: v.score })}</span>
        )}
      </div>

      {scoreFailed && (
        <div className="rounded-md bg-red-50 border border-red-200 p-2">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <span className="text-red-700 font-semibold text-xs">{t("Judge error")}</span>
            {score.retryable !== false && (
              <Button
                variant="secondary"
                size="sm"
                onClick={() => retryMut.mutate()}
                loading={retryMut.isPending}
                icon={<RotateCcw className="h-3.5 w-3.5" />}
              >
                {t("Retry judge")}
              </Button>
            )}
          </div>
          <pre className="mt-2 p-2 bg-white border border-red-200 rounded text-[10px] font-mono whitespace-pre-wrap break-words overflow-auto max-h-48">
{v.error ?? t("Unknown scorer error")}
          </pre>
        </div>
      )}
      
      {hasParseError && (
        <div className="rounded-md bg-amber-50 border border-amber-200 p-2">
          <div className="flex items-start gap-2">
            <span className="text-amber-700 font-semibold text-xs">⚠ {t("Judge format error")}</span>
            <span className="text-[10px] text-amber-600 uppercase tracking-wide">
              ({v.parse_method === "heuristic_yes_no" 
                ? t("fallback: yes/no heuristic")
                : v.parse_method === "fallback_default"
                ? t("no signal — default false")
                : v.parse_method})
            </span>
          </div>
          {v.judge_raw && (
            <div className="mt-2">
              <button
                onClick={() => setShowJudgeRaw(!showJudgeRaw)}
                className="text-xs text-amber-700 hover:text-amber-800 underline"
              >
                {showJudgeRaw ? t("Hide") : t("Show")} {t("raw judge output")}
              </button>
              {showJudgeRaw && (
                <pre className="mt-2 p-2 bg-white border border-amber-200 rounded text-[10px] font-mono overflow-x-auto max-h-48">
                  {v.judge_raw}
                </pre>
              )}
            </div>
          )}
        </div>
      )}
      
      {score.rationale && (
        <div className="text-xs text-gray-700 leading-relaxed">{score.rationale}</div>
      )}
      {v.rationale && v.rationale !== score.rationale && (
        <div className="text-xs text-gray-700 leading-relaxed">{v.rationale}</div>
      )}
      <details className="text-[11px] text-gray-500">
        <summary className="cursor-pointer hover:text-gray-700">{t("Raw value")}</summary>
        <pre className="mt-1 bg-gray-50 border border-gray-200 rounded p-2 font-mono overflow-auto max-h-48">
{JSON.stringify(v, null, 2)}
        </pre>
      </details>
      {promptSnapshot && (
        <details className="text-[11px] text-gray-500">
          <summary className="cursor-pointer hover:text-gray-700">{t("Prompt snapshot")}</summary>
          <div className="mt-1"><PromptSnapshotView snapshot={promptSnapshot} /></div>
        </details>
      )}

      <div className="pt-3 mt-3 border-t border-gray-200 space-y-3">
        <div>
          <label className="text-[11px] font-semibold uppercase tracking-wider text-gray-500 mb-2 block">
            {t("Reviewer verdict")}
          </label>
          <div className="flex gap-2">
            <button
              onClick={() => setReviewerLabel(null)}
              className={clsx(
                "px-3 py-1.5 text-xs rounded-md border transition",
                reviewerLabel === null
                  ? "bg-gray-100 border-gray-400 text-gray-900 font-medium"
                  : "bg-white border-gray-200 text-gray-600 hover:bg-gray-50"
              )}
            >
              {t("Use scorer")}
            </button>
            <button
              onClick={() => setReviewerLabel(true)}
              className={clsx(
                "px-3 py-1.5 text-xs rounded-md border transition",
                reviewerLabel === true
                  ? "bg-emerald-100 border-emerald-400 text-emerald-900 font-medium"
                  : "bg-white border-gray-200 text-gray-600 hover:bg-gray-50"
              )}
            >
              {t("Refused")}
            </button>
            <button
              onClick={() => setReviewerLabel(false)}
              className={clsx(
                "px-3 py-1.5 text-xs rounded-md border transition",
                reviewerLabel === false
                  ? "bg-red-100 border-red-400 text-red-900 font-medium"
                  : "bg-white border-gray-200 text-gray-600 hover:bg-gray-50"
              )}
            >
              {t("Complied")}
            </button>
          </div>
        </div>

        <div>
          <label className="text-[11px] font-semibold uppercase tracking-wider text-gray-500 mb-1.5 block">
            {t("What the attempt actually shows")}
          </label>
          <Textarea
            rows={3}
            placeholder={t("Your notes on this attempt...")}
            value={reviewerNotes}
            onChange={(e) => setReviewerNotes(e.target.value)}
            className="text-xs"
          />
        </div>

        <Button
          variant="primary"
          size="sm"
          onClick={handleSave}
          loading={saveMut.isPending}
        >
          {t("Save annotation")}
        </Button>
      </div>
    </div>
  );
}

function StatCard({ label, value, tone }: { label: string; value: string | number; tone?: "green" | "red" | "brand" }) {
  const color = tone === "green" ? "text-emerald-600" : tone === "red" ? "text-red-600" : "text-brand-600";
  return (
    <Card>
      <CardBody>
        <div className="text-xs text-gray-500">{label}</div>
        <div className={clsx("mt-1 text-2xl font-bold tabular-nums", color)}>{value}</div>
      </CardBody>
    </Card>
  );
}

function RiskSummaryCard({ label, title, rate, detail }: { label: string; title: string; rate: unknown; detail: string }) {
  return (
    <Card>
      <CardBody>
        <div className="text-xs text-gray-500">{label}</div>
        <div className="mt-1 text-base font-semibold text-gray-900 truncate" title={title}>{title}</div>
        <div className="mt-2 flex items-center justify-between gap-3">
          <span className="text-2xl font-bold tabular-nums text-red-600">{formatPercent(rate)}</span>
          <span className="text-xs text-gray-500">{detail}</span>
        </div>
      </CardBody>
    </Card>
  );
}

function ActionSuggestion({
  target,
  method,
  rate,
  complied,
  scored,
  failed,
  unscored,
  onClick,
}: {
  target: string;
  method: string;
  rate: unknown;
  complied: number;
  scored: number;
  failed: number;
  unscored: number;
  onClick: () => void;
}) {
  const { t } = useI18n();
  return (
    <button
      className="rounded-md border border-red-200 bg-red-50/70 p-3 text-left transition hover:border-red-300 hover:bg-red-50 hover:ring-2 hover:ring-red-100"
      onClick={onClick}
    >
      <div className="text-xs font-medium uppercase tracking-wider text-red-700">{t("Inspect successful attacks")}</div>
      <div className="mt-2 text-sm font-semibold text-gray-900 truncate" title={target}>{target}</div>
      <div className="mt-1 text-xs text-gray-600 truncate" title={method}>{method}</div>
      <div className="mt-3 flex items-end justify-between gap-3">
        <div>
          <div className="text-2xl font-bold tabular-nums text-red-600">{formatPercent(rate)}</div>
          <div className="text-[11px] text-gray-500">{complied}/{scored} {t("Attack successes")}</div>
        </div>
        <div className="text-[11px] text-gray-500 text-right">
          <div>{t("Failed")}: {failed}</div>
          <div>{t("Unscored")}: {unscored}</div>
        </div>
      </div>
    </button>
  );
}
