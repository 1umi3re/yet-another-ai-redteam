import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Link, useParams, useNavigate } from "react-router-dom";
import { useEffect, useMemo, useState } from "react";
import { api } from "../lib/api";
import { useAuth } from "../lib/auth";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Legend } from "recharts";
import { Card, CardBody, CardHeader, CardTitle, CardDescription } from "../components/ui/Card";
import { Badge, StatusBadge } from "../components/ui/Badge";
import { ProgressBar } from "../components/ui/ProgressBar";
import { Button } from "../components/ui/Button";
import { Textarea } from "../components/ui/Form";
import { ArrowLeft, X, Clock, Hash, AlertCircle, MessageSquare } from "lucide-react";
import clsx from "clsx";
import { toast } from "sonner";

type Tab = "overview" | "attempts" | "events";

const TERMINAL_STATUSES = new Set(["completed", "failed", "cancelled"]);
const isTerminalStatus = (s: string | undefined) => !!s && TERMINAL_STATUSES.has(s);

function scorerVerdictOf(score: any): "refused" | "complied" {
  const v = score?.value ?? {};
  if (typeof v.attack_success === "boolean") {
    return v.attack_success ? "complied" : "refused";
  }
  const label = v.label;
  if (typeof label !== "boolean") return "complied";
  if (score?.scorer === "refusal") return label ? "refused" : "complied";
  return label ? "complied" : "refused";
}

// Reviewer labels use target-side polarity: true = refused, false = complied.
// Without a reviewer override, scorer output remains the source of truth.
function verdictOf(score: any): "refused" | "complied" {
  if (typeof score?.reviewer_label === "boolean") {
    return score.reviewer_label ? "refused" : "complied";
  }
  return scorerVerdictOf(score);
}

export default function RunDetail() {
  const { id = "" } = useParams();
  const token = useAuth(s => s.token);
  const [events, setEvents] = useState<any[]>([]);
  const [tab, setTab] = useState<Tab>("overview");
  const [detailAttemptId, setDetailAttemptId] = useState<string | null>(null);

  const { data: run } = useQuery({
    queryKey: ["run", id],
    queryFn: async () => (await api.get(`/api/runs/${id}`)).data,
    refetchInterval: (q) => isTerminalStatus(q.state.data?.status) ? false : 2000,
  });
  const pollInterval: number | false = isTerminalStatus(run?.status) ? false : 2000;
  const { data: attempts = [] } = useQuery({
    queryKey: ["run-attempts", id],
    queryFn: async () => (await api.get(`/api/runs/${id}/attempts`)).data,
    refetchInterval: pollInterval,
  });
  const { data: scores = [] } = useQuery({
    queryKey: ["run-scores", id],
    queryFn: async () => (await api.get(`/api/runs/${id}/scores`)).data,
    refetchInterval: pollInterval,
  });

  useEffect(() => {
    if (!id || !token) return;
    const url = `${api.defaults.baseURL}/api/runs/${id}/events?token=${encodeURIComponent(token)}`;
    const es = new EventSource(url);
    es.onmessage = (e) => setEvents(prev => [...prev.slice(-199), JSON.parse(e.data)]);
    // Intentionally no onerror handler — EventSource auto-reconnects on transient
    // network errors. The cleanup below closes the stream on unmount.
    return () => es.close();
  }, [id, token]);

  const scoreByAttempt = useMemo(() => {
    const m = new Map<string, any>();
    for (const s of scores as any[]) {
      if (!m.has(s.attempt_id)) m.set(s.attempt_id, s);
    }
    return m;
  }, [scores]);

  const chartData = useMemo(() => {
    const byTarget: Record<string, { target: string; refused: number; complied: number }> = {};
    for (const a of attempts as any[]) {
      byTarget[a.target_name] ||= { target: a.target_name, refused: 0, complied: 0 };
      const sc = scoreByAttempt.get(a.id);
      if (!sc) continue;
      if (verdictOf(sc) === "refused") byTarget[a.target_name].refused++;
      else byTarget[a.target_name].complied++;
    }
    return Object.values(byTarget);
  }, [attempts, scoreByAttempt]);

  const totals = useMemo(() => {
    let refused = 0, complied = 0;
    for (const s of scores as any[]) {
      if (verdictOf(s) === "refused") refused++; else complied++;
    }
    return { refused, complied, total: refused + complied };
  }, [scores]);

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <Link to="/runs" className="inline-flex items-center gap-1 text-xs text-gray-500 hover:text-gray-700 mb-2">
            <ArrowLeft className="h-3 w-3" /> Back to runs
          </Link>
          <h1 className="text-2xl font-bold tracking-tight">{run?.name ?? "Run"}</h1>
          <div className="flex items-center gap-3 mt-2">
            {run && <StatusBadge status={run.status} />}
            <span className="text-xs text-gray-500 font-mono">{id.slice(0, 8)}</span>
            {!!run?.target_names?.length && (
              <span className="text-xs text-gray-600">{run.target_names.join(", ")}</span>
            )}
          </div>
          {run?.error && <div className="mt-2 text-xs text-red-600">{run.error}</div>}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard label="Refusal rate" value={totals.total ? `${Math.round((totals.refused/totals.total)*100)}%` : "—"} tone="green" />
        <StatCard label="Refused" value={totals.refused} tone="green" />
        <StatCard label="Complied" value={totals.complied} tone="red" />
        <Card><CardBody>
          <div className="text-xs text-gray-500 mb-1">Progress</div>
          <ProgressBar done={run?.progress_done ?? 0} total={run?.progress_total ?? 0} />
        </CardBody></Card>
      </div>

      <div className="flex gap-1 border-b border-gray-200">
        {(["overview", "attempts", "events"] as Tab[]).map(t => (
          <button key={t} onClick={() => setTab(t)}
            className={clsx(
              "px-4 py-2 text-sm font-medium border-b-2 -mb-px transition",
              tab === t ? "border-brand-600 text-brand-700" : "border-transparent text-gray-500 hover:text-gray-700",
            )}>
            {t === "overview" ? "Overview" : t === "attempts" ? `Attempts (${(attempts as any[]).length})` : "Live events"}
          </button>
        ))}
      </div>

      {tab === "overview" && (
        <Card>
          <CardHeader>
            <CardTitle>Refused vs Complied by target</CardTitle>
            <CardDescription>Green = model refused. Red = model complied with the attack prompt.</CardDescription>
          </CardHeader>
          <CardBody>
            {chartData.length ? (
              <div style={{ height: 280 }}>
                <ResponsiveContainer>
                  <BarChart data={chartData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#eee" />
                    <XAxis dataKey="target" tick={{ fontSize: 12 }} />
                    <YAxis allowDecimals={false} tick={{ fontSize: 12 }} />
                    <Tooltip contentStyle={{ fontSize: 12, borderRadius: 8 }} />
                    <Legend wrapperStyle={{ fontSize: 12 }} />
                    <Bar dataKey="refused" stackId="a" fill="#10b981" name="Refused" radius={[4, 4, 0, 0]} />
                    <Bar dataKey="complied" stackId="a" fill="#ef4444" name="Complied" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            ) : <div className="text-sm text-gray-500 py-8 text-center">No scored attempts yet.</div>}
          </CardBody>
        </Card>
      )}

      {tab === "attempts" && (
        <Card>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 text-gray-600 text-xs uppercase tracking-wider">
                <tr>
                  <th className="text-left px-5 py-2.5">Target</th>
                  <th className="text-left px-5 py-2.5">Prompt</th>
                  <th className="text-left px-5 py-2.5">Response</th>
                  <th className="text-left px-5 py-2.5">Score</th>
                  <th className="px-5 py-2.5"></th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {(attempts as any[]).map(a => {
                  const sc = scoreByAttempt.get(a.id);
                  const verdict = sc ? verdictOf(sc) : null;
                  return (
                    <tr key={a.id} className="align-top hover:bg-gray-50/60">
                      <td className="px-5 py-3 font-medium whitespace-nowrap">{a.target_name}</td>
                      <td className="px-5 py-3 max-w-xs"><div className="truncate text-gray-700" title={a.prompt}>{a.prompt}</div></td>
                      <td className="px-5 py-3 max-w-md"><div className="truncate text-gray-600" title={a.response ?? ""}>{a.response ?? <span className="text-gray-400">(blob)</span>}</div></td>
                      <td className="px-5 py-3">
                        {verdict === "refused" ? <Badge tone="green">refused</Badge>
                          : verdict === "complied" ? <Badge tone="red">complied</Badge>
                          : <Badge>-</Badge>}
                      </td>
                      <td className="px-5 py-3 text-right">
                        <button onClick={() => setDetailAttemptId(a.id)}
                          className="text-xs font-medium text-brand-600 hover:text-brand-700">View</button>
                      </td>
                    </tr>
                  );
                })}
                {!(attempts as any[]).length && (
                  <tr><td colSpan={5} className="px-5 py-10 text-center text-sm text-gray-500">No attempts yet.</td></tr>
                )}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      {tab === "events" && (
        <Card>
          <CardHeader>
            <CardTitle>Live events</CardTitle>
            <CardDescription>Streamed via Server-Sent Events. Last 200 messages.</CardDescription>
          </CardHeader>
          <CardBody>
            <pre className="text-xs bg-gray-900 text-gray-100 rounded-lg p-3 max-h-80 overflow-auto font-mono">
{events.length ? events.map(e => JSON.stringify(e)).join("\n") : "(waiting for events…)"}
            </pre>
          </CardBody>
        </Card>
      )}

      <AttemptDetailDrawer
        runId={id}
        attempt={detailAttemptId ? (attempts as any[]).find(a => a.id === detailAttemptId) ?? null : null}
        scores={detailAttemptId ? (scores as any[]).filter(s => s.attempt_id === detailAttemptId) : []}
        onClose={() => setDetailAttemptId(null)}
      />
    </div>
  );
}

function AttemptDetailDrawer({ runId, attempt, scores, onClose }: { runId: string; attempt: any | null; scores: any[]; onClose: () => void }) {
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
    onError: () => toast.error("Failed to start replay"),
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
      toast.error("Cannot replay: target_id not available");
      return;
    }
    const replayName = `Replay of attempt ${attempt.id.slice(0, 8)}`;
    replayMut.mutate({ name: replayName, target_id: attempt.target_id, attempt_id: attempt.id });
  };

  return (
    <div className="fixed inset-0 z-50 flex">
      <div className="flex-1 bg-gray-900/40 backdrop-blur-sm" onClick={onClose} />
      <div className="w-full max-w-2xl bg-white shadow-2xl overflow-y-auto border-l border-gray-200">
        <div className="sticky top-0 z-10 flex items-center justify-between px-6 py-4 border-b border-gray-200 bg-white/90 backdrop-blur">
          <div>
            <div className="text-xs text-gray-500">Attempt</div>
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
            {typeof attempt.latency_ms === "number" && (
              <span className="inline-flex items-center gap-1"><Clock className="h-3 w-3" />{attempt.latency_ms} ms</span>
            )}
            {(attempt.tokens_in != null || attempt.tokens_out != null) && (
              <span className="inline-flex items-center gap-1">
                <Hash className="h-3 w-3" />
                in {attempt.tokens_in ?? "-"} / out {attempt.tokens_out ?? "-"}
              </span>
            )}
            {chain.length > 0 && (
              <span className="inline-flex items-center gap-1">
                converters:
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
                Replay in Manual Console
              </Button>
            </div>
          )}

          {attempt.error && (
            <div className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-xs text-red-700 flex gap-2">
              <AlertCircle className="h-4 w-4 shrink-0 mt-0.5" />
              <span className="font-mono whitespace-pre-wrap break-words">{attempt.error}</span>
            </div>
          )}

          {messages.length > 0 ? (
            <Section title="Conversation">
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
            <>
              <Section title="Prompt">
                <pre className="text-xs whitespace-pre-wrap break-words font-mono bg-gray-50 border border-gray-200 rounded-lg p-3 text-gray-800 max-h-64 overflow-auto">
{attempt.prompt ?? ""}
                </pre>
              </Section>

              <Section title="Response">
                {attempt.response ? (
                  <pre className="text-xs whitespace-pre-wrap break-words font-mono bg-gray-50 border border-gray-200 rounded-lg p-3 text-gray-800 max-h-96 overflow-auto">
{attempt.response}
                  </pre>
                ) : attempt.response_blob_path ? (
                  <div className="text-xs text-gray-500 italic">Response stored as blob: <span className="font-mono">{attempt.response_blob_path}</span></div>
                ) : (
                  <div className="text-xs text-gray-400 italic">No response</div>
                )}
              </Section>
            </>
          )}

          <Section title={scores.length > 1 ? `Scores (${scores.length})` : "Score"}>
            {scores.length === 0 ? (
              <div className="text-xs text-gray-400 italic">No score yet</div>
            ) : (
              <div className="space-y-3">
                {scores.map((s) => <ScoreCard key={s.id} score={s} />)}
              </div>
            )}
          </Section>

          {promptSnapshot && (
            <Section title="Executor Prompt Snapshots">
              <pre className="text-xs whitespace-pre-wrap break-words font-mono bg-gray-50 border border-gray-200 rounded-lg p-3 text-gray-800 max-h-80 overflow-auto">
{JSON.stringify(promptSnapshot, null, 2)}
              </pre>
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

function ScoreCard({ score }: { score: any }) {
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
      toast.success("Annotation saved");
    },
    onError: () => toast.error("Failed to save annotation"),
  });

  const v = score?.value ?? {};
  
  const scorerVerdict = scorerVerdictOf(score);
  
  // Display verdict: use reviewer's if set, otherwise scorer's
  const displayVerdict = typeof reviewerLabel === "boolean"
    ? (reviewerLabel ? "refused" : "complied")
    : scorerVerdict;
  
  const isOverridden = typeof reviewerLabel === "boolean";
  const tone = displayVerdict === "refused" ? "green" : "red";
  
  // Check for judge format error
  const isLLMJudge = score.scorer === "llm_judge";
  const hasParseError = isLLMJudge && v.parse_error === true;

  const handleSave = () => {
    saveMut.mutate({ reviewer_label: reviewerLabel, reviewer_notes: reviewerNotes });
  };

  return (
    <div className="rounded-lg border border-gray-200 bg-white p-3 space-y-2">
      <div className="flex items-center gap-2 text-xs">
        <span className="font-medium text-gray-700">{score.scorer}</span>
        <Badge tone={tone as any}>{displayVerdict}</Badge>
        {isOverridden && <span className="text-[10px] text-gray-500">(overridden)</span>}
        {isOverridden && (
          <Badge tone={scorerVerdict === "refused" ? "green" : "red"} className="line-through opacity-50">
            {scorerVerdict}
          </Badge>
        )}
        {typeof v.confidence === "number" && (
          <span className="text-gray-500">confidence {v.confidence.toFixed(2)}</span>
        )}
        {typeof v.score === "number" && (
          <span className="text-gray-500">score {v.score}</span>
        )}
      </div>
      
      {hasParseError && (
        <div className="rounded-md bg-amber-50 border border-amber-200 p-2">
          <div className="flex items-start gap-2">
            <span className="text-amber-700 font-semibold text-xs">⚠ Judge format error</span>
            <span className="text-[10px] text-amber-600 uppercase tracking-wide">
              ({v.parse_method === "heuristic_yes_no" 
                ? "fallback: yes/no heuristic" 
                : v.parse_method === "fallback_default"
                ? "no signal — default false"
                : v.parse_method})
            </span>
          </div>
          {v.judge_raw && (
            <div className="mt-2">
              <button
                onClick={() => setShowJudgeRaw(!showJudgeRaw)}
                className="text-xs text-amber-700 hover:text-amber-800 underline"
              >
                {showJudgeRaw ? "Hide" : "Show"} raw judge output
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
        <summary className="cursor-pointer hover:text-gray-700">Raw value</summary>
        <pre className="mt-1 bg-gray-50 border border-gray-200 rounded p-2 font-mono overflow-auto max-h-48">
{JSON.stringify(v, null, 2)}
        </pre>
      </details>
      {promptSnapshot && (
        <details className="text-[11px] text-gray-500">
          <summary className="cursor-pointer hover:text-gray-700">Prompt snapshot</summary>
          <pre className="mt-1 bg-gray-50 border border-gray-200 rounded p-2 font-mono overflow-auto max-h-48">
{JSON.stringify(promptSnapshot, null, 2)}
          </pre>
        </details>
      )}

      <div className="pt-3 mt-3 border-t border-gray-200 space-y-3">
        <div>
          <label className="text-[11px] font-semibold uppercase tracking-wider text-gray-500 mb-2 block">
            Reviewer verdict
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
              Use scorer
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
              Refused
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
              Complied
            </button>
          </div>
        </div>

        <div>
          <label className="text-[11px] font-semibold uppercase tracking-wider text-gray-500 mb-1.5 block">
            What the attempt actually shows
          </label>
          <Textarea
            rows={3}
            placeholder="Your notes on this attempt..."
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
          Save annotation
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
