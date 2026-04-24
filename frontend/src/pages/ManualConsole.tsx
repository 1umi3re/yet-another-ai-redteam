import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useNavigate, useSearchParams } from "react-router-dom";
import { useState, useEffect, useRef } from "react";
import { api } from "../lib/api";
import { Card, CardBody, CardHeader, CardTitle } from "../components/ui/Card";
import { Button } from "../components/ui/Button";
import { Input, Select, Field, Textarea } from "../components/ui/Form";
import { MessageSquare, Plus, CheckCircle, Send } from "lucide-react";
import clsx from "clsx";
import { toast } from "sonner";

type SessionState = {
  run_id: string;
  attempt_id: string;
  messages: Array<{ role: string; text: string }>;
};

export default function ManualConsole() {
  const nav = useNavigate();
  const [searchParams] = useSearchParams();
  const queryClient = useQueryClient();

  const [sessionState, setSessionState] = useState<SessionState | null>(null);
  const [selectedTargetId, setSelectedTargetId] = useState("");
  const [runName, setRunName] = useState("");
  const [userInput, setUserInput] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const { data: targets = [] } = useQuery({
    queryKey: ["targets"],
    queryFn: async () => (await api.get("/api/targets")).data,
  });

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
        messages: data.conversation || [],
      });
    },
    onError: () => toast.error("Failed to start conversation"),
  });

  const sendTurnMut = useMutation({
    mutationFn: async ({ run_id, attempt_id, text }: { run_id: string; attempt_id: string; text: string }) =>
      (await api.post(`/api/manual/runs/${run_id}/conversations/${attempt_id}/turn`, { text })).data,
    onSuccess: (data) => {
      setSessionState(prev => prev ? { ...prev, messages: data.conversation } : null);
      setUserInput("");
    },
    onError: () => toast.error("Failed to send message"),
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

  // Handle query param replay
  useEffect(() => {
    const runId = searchParams.get("run");
    const attemptId = searchParams.get("attempt");
    if (runId && attemptId && !sessionState) {
      api.get(`/api/runs/${runId}/attempts/${attemptId}/conversation`)
        .then(res => {
          setSessionState({
            run_id: runId,
            attempt_id: attemptId,
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
    if (!userInput.trim() || !sessionState) return;
    sendTurnMut.mutate({
      run_id: sessionState.run_id,
      attempt_id: sessionState.attempt_id,
      text: userInput,
    });
  };

  const handleNewConversation = () => {
    if (!sessionState) return;
    startConversationMut.mutate({ run_id: sessionState.run_id, seed_attempt_id: null });
  };

  const handleFinishRun = () => {
    if (!sessionState) return;
    finishRunMut.mutate(sessionState.run_id);
  };

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
          <p className="text-xs text-gray-500 font-mono mt-1">Run ID: {sessionState.run_id.slice(0, 8)}</p>
        </div>
        <div className="flex gap-2">
          <Button variant="secondary" onClick={handleNewConversation} icon={<Plus className="h-4 w-4" />}>
            New conversation
          </Button>
          <Button variant="primary" onClick={handleFinishRun} icon={<CheckCircle className="h-4 w-4" />}>
            Finish run
          </Button>
        </div>
      </div>

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
                disabled={!userInput.trim()}
                icon={<Send className="h-4 w-4" />}
              >
                Send
              </Button>
            </div>
          </div>
        </CardBody>
      </Card>
    </div>
  );
}
