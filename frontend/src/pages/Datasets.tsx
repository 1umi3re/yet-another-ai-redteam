import { useEffect, useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Database, History, RotateCcw, Save, Upload } from "lucide-react";
import clsx from "clsx";
import { toast } from "sonner";

import { api } from "../lib/api";
import { Badge } from "../components/ui/Badge";
import { Button } from "../components/ui/Button";
import { Card, CardBody, CardDescription, CardHeader, CardTitle } from "../components/ui/Card";
import { EmptyState } from "../components/ui/EmptyState";
import { Field, Input, Textarea } from "../components/ui/Form";
import { useI18n } from "../lib/i18n";

type Dataset = {
  id: string;
  name: string;
  plugin: string;
  item_count: number | null;
  current_version: number;
};

type DatasetContent = {
  id: string;
  name: string;
  plugin: string;
  version: number;
  item_count: number;
  items: unknown[];
};

type DatasetVersion = {
  id: string | null;
  dataset_id: string;
  version: number;
  item_count: number | null;
  note: string | null;
  created_at: string | null;
  is_current: boolean;
};

function formatDate(value: string | null): string {
  if (!value) return "-";
  return new Date(value).toLocaleString();
}

function parseDatasetItems(text: string): unknown[] {
  const parsed = JSON.parse(text);
  const items = Array.isArray(parsed) ? parsed : parsed?.items;
  if (!Array.isArray(items)) throw new Error("Dataset JSON must be an array or {items: [...]}");
  return items;
}

export default function Datasets({
  titleKey = "Datasets",
  descriptionKey = "Prompt collections used as the source material for attacks.",
}: {
  titleKey?: string;
  descriptionKey?: string;
}) {
  const { t } = useI18n();
  const qc = useQueryClient();
  const { data = [], isLoading } = useQuery({
    queryKey: ["datasets"],
    queryFn: async () => (await api.get<Dataset[]>("/api/datasets")).data,
  });
  const [selectedId, setSelectedId] = useState("");
  const selected = useMemo(
    () => data.find(d => d.id === selectedId) ?? data[0] ?? null,
    [data, selectedId],
  );
  const [name, setName] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [datasetJson, setDatasetJson] = useState("");
  const [versionNote, setVersionNote] = useState("");

  useEffect(() => {
    if (!selectedId && data.length) setSelectedId(data[0].id);
    if (selectedId && !data.some(d => d.id === selectedId)) {
      setSelectedId(data[0]?.id ?? "");
    }
  }, [data, selectedId]);

  const canEdit = selected?.plugin === "json_upload";
  const { data: content } = useQuery({
    queryKey: ["dataset-content", selected?.id],
    enabled: !!selected?.id && canEdit,
    queryFn: async () => (
      await api.get<DatasetContent>(`/api/datasets/${selected?.id}/content`)
    ).data,
  });
  const { data: versions = [] } = useQuery({
    queryKey: ["dataset-versions", selected?.id],
    enabled: !!selected?.id && canEdit,
    queryFn: async () => (
      await api.get<DatasetVersion[]>(`/api/datasets/${selected?.id}/versions`)
    ).data,
  });

  useEffect(() => {
    if (content) {
      setDatasetJson(JSON.stringify(content.items, null, 2));
      setVersionNote("");
    }
  }, [content?.id, content?.version]);

  const upload = useMutation({
    mutationFn: async () => {
      const fd = new FormData();
      fd.append("name", name);
      if (file) fd.append("file", file);
      return api.post("/api/datasets/upload", fd, {
        headers: { "Content-Type": "multipart/form-data" },
      });
    },
    onSuccess: (resp) => {
      toast.success(t("Dataset uploaded"));
      setName("");
      setFile(null);
      setSelectedId(resp.data.id);
      qc.invalidateQueries({ queryKey: ["datasets"] });
    },
    onError: (e: any) => toast.error(e?.response?.data?.detail ?? t("Upload failed")),
  });

  const save = useMutation({
    mutationFn: async () => {
      if (!selected) return null;
      const items = parseDatasetItems(datasetJson);
      return (await api.put(`/api/datasets/${selected.id}/content`, {
        items,
        note: versionNote,
      })).data;
    },
    onSuccess: () => {
      toast.success(t("Dataset version saved"));
      qc.invalidateQueries({ queryKey: ["datasets"] });
      qc.invalidateQueries({ queryKey: ["dataset-content", selected?.id] });
      qc.invalidateQueries({ queryKey: ["dataset-versions", selected?.id] });
    },
    onError: (e: any) => {
      const detail = e?.response?.data?.detail ?? e?.message ?? t("Failed to save dataset");
      toast.error(detail);
    },
  });

  const restore = useMutation({
    mutationFn: async (version: number) => (
      await api.post(`/api/datasets/${selected?.id}/versions/${version}/restore`)
    ).data,
    onSuccess: () => {
      toast.success(t("Dataset version restored"));
      qc.invalidateQueries({ queryKey: ["datasets"] });
      qc.invalidateQueries({ queryKey: ["dataset-content", selected?.id] });
      qc.invalidateQueries({ queryKey: ["dataset-versions", selected?.id] });
    },
    onError: (e: any) => toast.error(e?.response?.data?.detail ?? t("Failed to restore version")),
  });

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">{t(titleKey)}</h1>
        <p className="text-sm text-gray-500 mt-1">{t(descriptionKey)}</p>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-[420px_minmax(0,1fr)] gap-4">
        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>{t("Upload JSON dataset")}</CardTitle>
              <CardDescription>
                {t("JSON file with an array of items. Each item should have a")}{" "}
                <code className="font-mono text-xs bg-gray-100 px-1 rounded">prompt</code>{" "}
                {t("field.")}
              </CardDescription>
            </CardHeader>
            <CardBody>
              <div className="space-y-4">
                <Field label={t("Dataset name")}>
                  <Input
                    placeholder={t("e.g. my-jailbreaks")}
                    value={name}
                    onChange={e => setName(e.target.value)}
                  />
                </Field>
                <Field label={t("JSON file")}>
                  <label className="flex items-center justify-center gap-2 border-2 border-dashed border-gray-200 rounded-lg px-3 py-3 text-sm cursor-pointer hover:border-brand-400 hover:bg-brand-50/40 transition">
                    <Upload className="h-4 w-4 text-gray-400" />
                    <span className="text-gray-600">
                      {file ? file.name : t("Choose JSON file…")}
                    </span>
                    <input
                      type="file"
                      accept=".json,application/json"
                      className="hidden"
                      onChange={e => setFile(e.target.files?.[0] ?? null)}
                    />
                  </label>
                </Field>
              </div>
              <div className="mt-5 flex justify-end">
                <Button
                  icon={<Upload className="h-4 w-4" />}
                  loading={upload.isPending}
                  disabled={!name || !file}
                  onClick={() => upload.mutate()}
                >
                  {t("Upload")}
                </Button>
              </div>
            </CardBody>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>{t("Available datasets")}</CardTitle>
              <CardDescription>
                {t("Select a JSON dataset to edit items and manage versions.")}
              </CardDescription>
            </CardHeader>
            {isLoading ? (
              <CardBody className="text-sm text-gray-500">{t("Loading…")}</CardBody>
            ) : !data.length ? (
              <EmptyState
                icon={<Database className="h-10 w-10" />}
                title={t("No datasets yet")}
                description={t("Upload a JSON file or seed the built-in samples.")}
              />
            ) : (
              <CardBody className="space-y-2">
                {data.map(d => {
                  const isSelected = selected?.id === d.id;
                  return (
                    <button
                      key={d.id}
                      type="button"
                      onClick={() => setSelectedId(d.id)}
                      className={clsx(
                        "w-full rounded-lg border px-3 py-2.5 text-left transition",
                        isSelected
                          ? "border-brand-500 bg-brand-50 shadow-soft"
                          : "border-gray-200 hover:border-gray-300 hover:bg-gray-50",
                      )}
                    >
                      <div className="flex items-start justify-between gap-2">
                        <div className="min-w-0">
                          <div className="truncate text-sm font-semibold text-gray-900">
                            {d.name}
                          </div>
                          <div className="mt-1 flex flex-wrap gap-1">
                            <Badge tone="indigo">{d.plugin}</Badge>
                            <Badge>v{d.current_version ?? 1}</Badge>
                            <Badge tone="gray">{d.item_count ?? "-"} {t("items")}</Badge>
                          </div>
                        </div>
                      </div>
                    </button>
                  );
                })}
              </CardBody>
            )}
          </Card>
        </div>

        <div className="space-y-4 min-w-0">
          {!selected ? (
            <Card>
              <EmptyState
                icon={<Database className="h-10 w-10" />}
                title={t("No dataset selected")}
                description={t("Upload or select a dataset to inspect its items.")}
              />
            </Card>
          ) : (
            <>
              <Card>
                <CardHeader>
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div className="min-w-0">
                      <CardTitle className="break-words">{selected.name}</CardTitle>
                      <CardDescription className="mt-1">
                        {selected.plugin === "json_upload"
                          ? t("Editing creates a new dataset version.")
                          : t("Remote datasets cannot be edited here.")}
                      </CardDescription>
                    </div>
                    <div className="flex flex-wrap gap-2">
                      <Badge tone="indigo">{selected.plugin}</Badge>
                      <Badge>v{selected.current_version ?? 1}</Badge>
                      <Badge tone="gray">{selected.item_count ?? "-"} {t("items")}</Badge>
                    </div>
                  </div>
                </CardHeader>
                <CardBody className="space-y-4">
                  {!canEdit ? (
                    <div className="rounded-lg border border-gray-200 bg-gray-50 p-4 text-sm text-gray-600">
                      {t("Only uploaded JSON datasets can be edited and versioned in the UI.")}
                    </div>
                  ) : (
                    <>
                      <Field
                        label={t("Dataset items JSON")}
                        hint={t("Use an array or {items: [...]} with a prompt field per object.")}
                      >
                        <Textarea
                          rows={18}
                          value={datasetJson}
                          onChange={e => setDatasetJson(e.target.value)}
                          className="font-mono text-xs"
                        />
                      </Field>
                      <Field label={t("Version note")} hint={t("Optional short note for this edit.")}>
                        <Input
                          value={versionNote}
                          onChange={e => setVersionNote(e.target.value)}
                          placeholder={t("e.g. add policy-evasion goals")}
                        />
                      </Field>
                      <div className="flex justify-end">
                        <Button
                          icon={<Save className="h-4 w-4" />}
                          loading={save.isPending}
                          disabled={!datasetJson.trim()}
                          onClick={() => save.mutate()}
                        >
                          {t("Save new version")}
                        </Button>
                      </div>
                    </>
                  )}
                </CardBody>
              </Card>

              {canEdit && (
                <Card>
                  <CardHeader className="flex items-center gap-2">
                    <History className="h-4 w-4 text-gray-500" />
                    <CardTitle>{t("Versions")}</CardTitle>
                  </CardHeader>
                  <CardBody>
                    {versions.length === 0 ? (
                      <div className="text-sm text-gray-500">{t("No versions yet.")}</div>
                    ) : (
                      <div className="overflow-x-auto">
                        <table className="w-full text-sm">
                          <thead className="bg-gray-50 text-xs uppercase tracking-wider text-gray-600">
                            <tr>
                              <th className="px-3 py-2 text-left">{t("Version")}</th>
                              <th className="px-3 py-2 text-left">{t("Items")}</th>
                              <th className="px-3 py-2 text-left">{t("Note")}</th>
                              <th className="px-3 py-2 text-left">{t("Created")}</th>
                              <th className="px-3 py-2 text-right">{t("Action")}</th>
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-gray-100">
                            {versions.map(v => (
                              <tr key={`${v.version}-${v.id ?? "legacy"}`}>
                                <td className="px-3 py-2 font-mono">v{v.version}</td>
                                <td className="px-3 py-2 tabular-nums">{v.item_count ?? "-"}</td>
                                <td className="px-3 py-2 text-gray-600">{v.note ?? "-"}</td>
                                <td className="px-3 py-2 text-gray-600">{formatDate(v.created_at)}</td>
                                <td className="px-3 py-2 text-right">
                                  {v.is_current ? (
                                    <Badge tone="green">{t("Current")}</Badge>
                                  ) : (
                                    <Button
                                      size="sm"
                                      variant="secondary"
                                      icon={<RotateCcw className="h-4 w-4" />}
                                      loading={restore.isPending}
                                      onClick={() => restore.mutate(v.version)}
                                    >
                                      {t("Restore")}
                                    </Button>
                                  )}
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    )}
                  </CardBody>
                </Card>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
