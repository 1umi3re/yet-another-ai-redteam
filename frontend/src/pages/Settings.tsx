import { useEffect, useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { BellRing, Save, Send, SlidersHorizontal } from "lucide-react";
import { toast } from "sonner";

import { api } from "../lib/api";
import { useI18n } from "../lib/i18n";
import { Badge } from "../components/ui/Badge";
import { Button } from "../components/ui/Button";
import { Card, CardBody, CardDescription, CardHeader, CardTitle } from "../components/ui/Card";
import { Field, Input } from "../components/ui/Form";
import { Tabs, TabItem } from "../components/ui/Tabs";

type SettingsTab = "monitoring";

type MonitoringSettings = {
  monitor_enabled: boolean;
  delivery_enabled: boolean;
  dingtalk_webhook_configured: boolean;
  dingtalk_webhook_url_display: string | null;
  dingtalk_secret_configured: boolean;
  dingtalk_timeout_seconds: number;
  monitor_failure_rate_threshold: number;
  monitor_empty_response_rate_threshold: number;
  monitor_score_failure_rate_threshold: number;
  monitor_min_samples: number;
  monitor_no_progress_seconds: number;
  monitor_alert_cooldown_seconds: number;
};

type MonitoringForm = {
  monitor_enabled: boolean;
  dingtalk_webhook_url: string;
  dingtalk_secret: string;
  clear_dingtalk_webhook_url: boolean;
  clear_dingtalk_secret: boolean;
  dingtalk_timeout_seconds: string;
  monitor_failure_rate_threshold: string;
  monitor_empty_response_rate_threshold: string;
  monitor_score_failure_rate_threshold: string;
  monitor_min_samples: string;
  monitor_no_progress_seconds: string;
  monitor_alert_cooldown_seconds: string;
};

const tabs: Array<TabItem<SettingsTab>> = [
  { id: "monitoring", label: "Monitoring", icon: <BellRing className="h-4 w-4" /> },
];

export default function Settings() {
  const { t } = useI18n();
  const [active, setActive] = useState<SettingsTab>("monitoring");
  const tabItems = useMemo(() => tabs.map(tab => ({ ...tab, label: t(tab.label as string) })), [t]);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">{t("Settings")}</h1>
        <p className="text-sm text-gray-500 mt-1">{t("Runtime configuration for unattended automation.")}</p>
      </div>

      <Tabs tabs={tabItems} value={active} onChange={setActive} idBase="settings">
        {tab => tab === "monitoring" ? <MonitoringSettingsPanel /> : null}
      </Tabs>
    </div>
  );
}

function MonitoringSettingsPanel() {
  const { t } = useI18n();
  const qc = useQueryClient();
  const { data, isLoading } = useQuery({
    queryKey: ["settings", "monitoring"],
    queryFn: async () => (await api.get<MonitoringSettings>("/api/settings/monitoring")).data,
  });
  const [form, setForm] = useState<MonitoringForm | null>(null);

  useEffect(() => {
    if (!data) return;
    setForm({
      monitor_enabled: data.monitor_enabled,
      dingtalk_webhook_url: "",
      dingtalk_secret: "",
      clear_dingtalk_webhook_url: false,
      clear_dingtalk_secret: false,
      dingtalk_timeout_seconds: String(data.dingtalk_timeout_seconds ?? 5),
      monitor_failure_rate_threshold: toPercent(data.monitor_failure_rate_threshold),
      monitor_empty_response_rate_threshold: toPercent(data.monitor_empty_response_rate_threshold),
      monitor_score_failure_rate_threshold: toPercent(data.monitor_score_failure_rate_threshold),
      monitor_min_samples: String(data.monitor_min_samples ?? 20),
      monitor_no_progress_seconds: String(data.monitor_no_progress_seconds ?? 600),
      monitor_alert_cooldown_seconds: String(data.monitor_alert_cooldown_seconds ?? 900),
    });
  }, [data]);

  const validation = useMemo(() => form ? validate(form) : { valid: false, message: "" }, [form]);

  const save = useMutation({
    mutationFn: async () => {
      if (!form) return;
      const payload: Record<string, any> = {
        monitor_enabled: form.monitor_enabled,
        clear_dingtalk_webhook_url: form.clear_dingtalk_webhook_url,
        clear_dingtalk_secret: form.clear_dingtalk_secret,
        dingtalk_timeout_seconds: Number(form.dingtalk_timeout_seconds),
        monitor_failure_rate_threshold: Number(form.monitor_failure_rate_threshold) / 100,
        monitor_empty_response_rate_threshold: Number(form.monitor_empty_response_rate_threshold) / 100,
        monitor_score_failure_rate_threshold: Number(form.monitor_score_failure_rate_threshold) / 100,
        monitor_min_samples: Number(form.monitor_min_samples),
        monitor_no_progress_seconds: Number(form.monitor_no_progress_seconds),
        monitor_alert_cooldown_seconds: Number(form.monitor_alert_cooldown_seconds),
      };
      if (form.dingtalk_webhook_url.trim()) payload.dingtalk_webhook_url = form.dingtalk_webhook_url.trim();
      if (form.dingtalk_secret.trim()) payload.dingtalk_secret = form.dingtalk_secret.trim();
      return api.patch<MonitoringSettings>("/api/settings/monitoring", payload);
    },
    onSuccess: () => {
      toast.success(t("Monitoring settings saved"));
      qc.invalidateQueries({ queryKey: ["settings", "monitoring"] });
    },
    onError: (e: any) => toast.error(e?.response?.data?.detail ?? t("Failed to save monitoring settings")),
  });

  const test = useMutation({
    mutationFn: async () => api.post("/api/settings/monitoring/test"),
    onSuccess: () => toast.success(t("Test notification sent")),
    onError: (e: any) => toast.error(e?.response?.data?.detail ?? t("Failed to send test notification")),
  });

  if (isLoading || !data || !form) {
    return (
      <Card>
        <CardBody>
          <div className="text-sm text-gray-500">{t("Loading…")}</div>
        </CardBody>
      </Card>
    );
  }

  return (
    <div className="space-y-5">
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatusCard label={t("Monitor")} active={data.monitor_enabled} activeLabel={t("Enabled")} inactiveLabel={t("Disabled")} />
        <StatusCard label={t("Delivery")} active={data.delivery_enabled} activeLabel={t("Active")} inactiveLabel={t("Inactive")} />
        <StatusCard
          label={t("DingTalk webhook")}
          active={data.dingtalk_webhook_configured}
          activeLabel={t("configured")}
          inactiveLabel={t("missing")}
        />
        <StatusCard
          label={t("DingTalk secret")}
          active={data.dingtalk_secret_configured}
          activeLabel={t("configured")}
          inactiveLabel={t("optional")}
        />
      </div>

      <Card>
        <CardHeader className="flex flex-row items-start justify-between gap-4">
          <div>
            <CardTitle>{t("Unattended monitoring")}</CardTitle>
            <CardDescription>{t("Configure DingTalk delivery and anomaly thresholds.")}</CardDescription>
          </div>
          <Badge tone={data.delivery_enabled ? "green" : "amber"}>
            {data.delivery_enabled ? t("Delivery active") : t("Delivery inactive")}
          </Badge>
        </CardHeader>
        <CardBody>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
            <div className="lg:col-span-2">
              <label className="inline-flex items-center gap-2 text-sm font-medium text-gray-700">
                <input
                  type="checkbox"
                  className="h-4 w-4 rounded border-gray-300 text-brand-600 focus:ring-brand-500"
                  checked={form.monitor_enabled}
                  onChange={e => setForm({ ...form, monitor_enabled: e.target.checked })}
                />
                {t("Enable unattended monitoring")}
              </label>
            </div>

            <Field
              label={t("DingTalk webhook URL")}
              hint={data.dingtalk_webhook_url_display ?? t("Leave blank to keep the current webhook.")}
            >
              <Input
                type="password"
                placeholder={data.dingtalk_webhook_configured ? t("configured") : "https://oapi.dingtalk.com/robot/send?..."}
                value={form.dingtalk_webhook_url}
                disabled={form.clear_dingtalk_webhook_url}
                onChange={e => setForm({ ...form, dingtalk_webhook_url: e.target.value })}
              />
            </Field>
            <Field label={t("DingTalk robot secret")} hint={t("Optional signing secret. Leave blank to keep it unchanged.")}>
              <Input
                type="password"
                placeholder={data.dingtalk_secret_configured ? t("configured") : t("optional")}
                value={form.dingtalk_secret}
                disabled={form.clear_dingtalk_secret}
                onChange={e => setForm({ ...form, dingtalk_secret: e.target.value })}
              />
            </Field>

            <div className="lg:col-span-2 grid grid-cols-1 md:grid-cols-2 gap-3">
              {data.dingtalk_webhook_configured && (
                <label className="inline-flex items-center gap-2 text-sm text-gray-700">
                  <input
                    type="checkbox"
                    className="h-4 w-4 rounded border-gray-300 text-brand-600 focus:ring-brand-500"
                    checked={form.clear_dingtalk_webhook_url}
                    onChange={e => setForm({ ...form, clear_dingtalk_webhook_url: e.target.checked })}
                  />
                  {t("Clear DingTalk webhook")}
                </label>
              )}
              {data.dingtalk_secret_configured && (
                <label className="inline-flex items-center gap-2 text-sm text-gray-700">
                  <input
                    type="checkbox"
                    className="h-4 w-4 rounded border-gray-300 text-brand-600 focus:ring-brand-500"
                    checked={form.clear_dingtalk_secret}
                    onChange={e => setForm({ ...form, clear_dingtalk_secret: e.target.checked })}
                  />
                  {t("Clear DingTalk secret")}
                </label>
              )}
            </div>

            <Field label={t("DingTalk timeout")} hint={t("Seconds")}>
              <Input
                type="number"
                min="0.1"
                step="0.1"
                value={form.dingtalk_timeout_seconds}
                onChange={e => setForm({ ...form, dingtalk_timeout_seconds: e.target.value })}
              />
            </Field>
            <Field label={t("Minimum samples")} hint={t("Attempts or scores required before threshold alerts.")}>
              <Input
                type="number"
                min="1"
                step="1"
                value={form.monitor_min_samples}
                onChange={e => setForm({ ...form, monitor_min_samples: e.target.value })}
              />
            </Field>
            <Field label={t("Attempt failure threshold")} hint="%">
              <Input
                type="number"
                min="0"
                max="100"
                step="0.1"
                value={form.monitor_failure_rate_threshold}
                onChange={e => setForm({ ...form, monitor_failure_rate_threshold: e.target.value })}
              />
            </Field>
            <Field label={t("Empty response threshold")} hint="%">
              <Input
                type="number"
                min="0"
                max="100"
                step="0.1"
                value={form.monitor_empty_response_rate_threshold}
                onChange={e => setForm({ ...form, monitor_empty_response_rate_threshold: e.target.value })}
              />
            </Field>
            <Field label={t("Score failure threshold")} hint="%">
              <Input
                type="number"
                min="0"
                max="100"
                step="0.1"
                value={form.monitor_score_failure_rate_threshold}
                onChange={e => setForm({ ...form, monitor_score_failure_rate_threshold: e.target.value })}
              />
            </Field>
            <Field label={t("No progress window")} hint={t("Seconds")}>
              <Input
                type="number"
                min="1"
                step="1"
                value={form.monitor_no_progress_seconds}
                onChange={e => setForm({ ...form, monitor_no_progress_seconds: e.target.value })}
              />
            </Field>
            <Field label={t("Alert cooldown")} hint={t("Seconds")}>
              <Input
                type="number"
                min="1"
                step="1"
                value={form.monitor_alert_cooldown_seconds}
                onChange={e => setForm({ ...form, monitor_alert_cooldown_seconds: e.target.value })}
              />
            </Field>
          </div>

          <div className="mt-5 flex flex-wrap items-center justify-end gap-3">
            {!validation.valid && (
              <div role="alert" className="mr-auto rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-800">
                {t(validation.message)}
              </div>
            )}
            <Button
              variant="secondary"
              icon={<Send className="h-4 w-4" />}
              loading={test.isPending}
              disabled={!data.delivery_enabled || save.isPending}
              onClick={() => test.mutate()}
            >
              {t("Send test")}
            </Button>
            <Button
              icon={<Save className="h-4 w-4" />}
              loading={save.isPending}
              disabled={!validation.valid}
              onClick={() => save.mutate()}
            >
              {t("Save")}
            </Button>
          </div>
        </CardBody>
      </Card>
    </div>
  );
}

function StatusCard({ label, active, activeLabel, inactiveLabel }: {
  label: string;
  active: boolean;
  activeLabel: string;
  inactiveLabel: string;
}) {
  return (
    <Card>
      <CardBody>
        <div className="flex items-center justify-between gap-3">
          <div className="h-8 w-8 rounded-lg bg-gray-50 text-gray-600 flex items-center justify-center">
            <SlidersHorizontal className="h-4 w-4" />
          </div>
          <Badge tone={active ? "green" : "amber"}>{active ? activeLabel : inactiveLabel}</Badge>
        </div>
        <div className="mt-3 text-xs text-gray-500">{label}</div>
      </CardBody>
    </Card>
  );
}

function toPercent(value: number | null | undefined): string {
  if (value == null) return "";
  return String(Math.round(value * 1000) / 10);
}

function validate(form: MonitoringForm): { valid: boolean; message: string } {
  const percentFields = [
    form.monitor_failure_rate_threshold,
    form.monitor_empty_response_rate_threshold,
    form.monitor_score_failure_rate_threshold,
  ];
  if (percentFields.some(value => !isFiniteNumber(value) || Number(value) < 0 || Number(value) > 100)) {
    return { valid: false, message: "Thresholds must be between 0 and 100." };
  }
  const positiveIntegerFields = [
    form.monitor_min_samples,
    form.monitor_no_progress_seconds,
    form.monitor_alert_cooldown_seconds,
  ];
  if (positiveIntegerFields.some(value => !Number.isInteger(Number(value)) || Number(value) < 1)) {
    return { valid: false, message: "Sample count and time windows must be positive integers." };
  }
  if (!isFiniteNumber(form.dingtalk_timeout_seconds) || Number(form.dingtalk_timeout_seconds) <= 0) {
    return { valid: false, message: "DingTalk timeout must be positive." };
  }
  return { valid: true, message: "" };
}

function isFiniteNumber(value: string): boolean {
  return value.trim() !== "" && Number.isFinite(Number(value));
}
