import { useEffect, useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { CheckCircle, FileText, Plus, RotateCcw, Save } from "lucide-react";
import clsx from "clsx";
import { toast } from "sonner";

import { api } from "../lib/api";
import { Badge } from "../components/ui/Badge";
import { Button } from "../components/ui/Button";
import { Card, CardBody, CardHeader, CardTitle } from "../components/ui/Card";
import { Field, Input, Textarea } from "../components/ui/Form";
import { useI18n } from "../lib/i18n";
import {
  changedLineRows,
  extractTemplateVariables,
  validateTemplateVariables,
} from "../lib/promptAssetHelpers";

type Override = {
  id: string;
  asset_id: string;
  name: string;
  template: string;
  is_active: boolean;
};

type Asset = {
  id: string;
  version: number;
  plugin: string;
  purpose: string;
  category?: string;
  variables: string[];
  template: string;
  source?: string;
  is_custom?: boolean;
  active_override?: Override | null;
  overrides?: Override[];
};

function toTitleCase(segment: string): string {
  return segment.replace(/_/g, " ").replace(/\b\w/g, c => c.toUpperCase());
}

function deriveVersion(id: string): string | null {
  const m = id.match(/\.v(\d+)$/);
  return m ? `v${m[1]}` : null;
}

function deriveTitle(id: string, idPrefix?: string): string {
  let s = id.replace(/\.v\d+$/, "");
  if (idPrefix && s.startsWith(idPrefix + ".")) {
    s = s.slice(idPrefix.length + 1);
  }
  return s.split(".").map(toTitleCase).join(" · ");
}

export default function PromptAssets({
  titleKey = "Prompt Assets",
  descriptionKey = "Manage evaluator and executor prompt overrides.",
  listTitleKey = "Assets",
  createTitleKey = "Create prompt asset",
  newAssetButtonKey = "New asset",
  saveAssetButtonKey = "Save",
  assetFilter,
  newAssetDefaults,
  idPrefix,
  headingLevel = "h1",
}: {
  titleKey?: string;
  descriptionKey?: string;
  listTitleKey?: string;
  createTitleKey?: string;
  newAssetButtonKey?: string;
  saveAssetButtonKey?: string;
  assetFilter?: (asset: Asset) => boolean;
  newAssetDefaults?: {
    id?: string;
    plugin?: string;
    purpose?: string;
    category?: string;
    variables?: string;
    template?: string;
  };
  idPrefix?: string;
  headingLevel?: "h1" | "h2";
}) {
  const { t } = useI18n();
  const qc = useQueryClient();
  const { data: allAssets = [] } = useQuery<Asset[]>({
    queryKey: ["prompt-assets"],
    queryFn: async () => (await api.get("/api/prompt-assets")).data,
  });
  const filteredAssets = useMemo(
    () => assetFilter ? allAssets.filter(assetFilter) : allAssets,
    [allAssets, assetFilter],
  );
  const categories = useMemo(
    () => Array.from(new Set(filteredAssets.map(a => a.category).filter(Boolean) as string[])).sort(),
    [filteredAssets],
  );
  const [selectedCategory, setSelectedCategory] = useState("all");
  const [assetSearch, setAssetSearch] = useState("");
  const categoryAssets = useMemo(
    () => selectedCategory === "all"
      ? filteredAssets
      : filteredAssets.filter(a => a.category === selectedCategory),
    [filteredAssets, selectedCategory],
  );
  const assets = useMemo(() => {
    const q = assetSearch.trim().toLowerCase();
    if (!q) return categoryAssets;
    return categoryAssets.filter(asset => [
      asset.id,
      deriveTitle(asset.id, idPrefix),
      asset.category ?? "",
      asset.plugin,
      asset.purpose,
    ].some(value => value.toLowerCase().includes(q)));
  }, [assetSearch, categoryAssets, idPrefix]);
  const [selectedId, setSelectedId] = useState("");
  const [editingId, setEditingId] = useState<string | null>(null);
  const [name, setName] = useState("");
  const [template, setTemplate] = useState("");
  const [creatingAsset, setCreatingAsset] = useState(false);
  const [newAssetId, setNewAssetId] = useState("");
  const [newAssetPlugin, setNewAssetPlugin] = useState("custom");
  const [newAssetPurpose, setNewAssetPurpose] = useState("custom");
  const [newAssetCategory, setNewAssetCategory] = useState("custom");
  const [newAssetVersion, setNewAssetVersion] = useState("1");
  const [newAssetVariables, setNewAssetVariables] = useState("");
  const [newAssetTemplate, setNewAssetTemplate] = useState("");

  useEffect(() => {
    if (selectedCategory !== "all" && !categories.includes(selectedCategory)) {
      setSelectedCategory("all");
      return;
    }
    if (assets.length === 0) {
      if (selectedId) setSelectedId("");
      return;
    }
    if (!selectedId || !assets.some(a => a.id === selectedId)) setSelectedId(assets[0].id);
  }, [assets, selectedId, categories, selectedCategory]);

  const { data: asset } = useQuery<Asset>({
    queryKey: ["prompt-asset", selectedId],
    enabled: !!selectedId,
    queryFn: async () => (await api.get(`/api/prompt-assets/${selectedId}`)).data,
  });

  const selectedOverride = useMemo(
    () => asset?.overrides?.find(o => o.id === editingId) ?? null,
    [asset, editingId],
  );

  // Depend on the override's id (a stable primitive), not the memoized object —
  // otherwise every asset refetch reseeds the form and wipes in-flight edits.
  useEffect(() => {
    if (selectedOverride) {
      setName(selectedOverride.name);
      setTemplate(selectedOverride.template);
    }
  }, [selectedOverride?.id]);

  const refresh = () => {
    qc.invalidateQueries({ queryKey: ["prompt-assets"] });
    qc.invalidateQueries({ queryKey: ["prompt-asset", selectedId] });
  };

  const createAssetMut = useMutation({
    mutationFn: async () => {
      return (await api.post("/api/prompt-assets", {
        id: newAssetId,
        plugin: newAssetPlugin,
        purpose: newAssetPurpose,
        category: newAssetCategory,
        version: parseInt(newAssetVersion || "1", 10),
        variables: newAssetVariableList,
        template: newAssetTemplate,
      })).data;
    },
    onSuccess: (data) => {
      setCreatingAsset(false);
      if (data?.id) setSelectedId(data.id);
      qc.invalidateQueries({ queryKey: ["prompt-assets"] });
      toast.success(t("Prompt asset created"));
    },
    onError: (e: any) => toast.error(e?.response?.data?.detail ?? t("Failed to create prompt asset")),
  });

  const saveMut = useMutation({
    mutationFn: async () => {
      if (!asset) return null;
      if (editingId) {
        return (await api.patch(`/api/prompt-assets/overrides/${editingId}`, { name, template })).data;
      }
      return (await api.post(`/api/prompt-assets/${asset.id}/overrides`, { name, template })).data;
    },
    onSuccess: (data) => {
      if (data?.id) setEditingId(data.id);
      refresh();
      toast.success(t("Prompt override saved"));
    },
    onError: (e: any) => toast.error(e?.response?.data?.detail ?? t("Failed to save override")),
  });

  const activeMut = useMutation({
    mutationFn: async (override_id: string | null) =>
      (await api.post(`/api/prompt-assets/${asset?.id}/active`, { override_id })).data,
    onSuccess: () => {
      refresh();
      toast.success(t("Active prompt updated"));
    },
    onError: () => toast.error(t("Failed to update active prompt")),
  });

  const startNew = () => {
    setEditingId(null);
    setName(`${asset?.plugin ?? t("Prompt")} ${t("override")}`);
    setTemplate(asset?.template ?? "");
  };

  const startCreateAsset = () => {
    setCreatingAsset(true);
    setNewAssetId(newAssetDefaults?.id ?? "");
    setNewAssetPlugin(newAssetDefaults?.plugin ?? "custom");
    setNewAssetPurpose(newAssetDefaults?.purpose ?? "custom");
    setNewAssetCategory(newAssetDefaults?.category ?? "");
    setNewAssetVersion("1");
    setNewAssetVariables(newAssetDefaults?.variables ?? "");
    setNewAssetTemplate(newAssetDefaults?.template ?? "");
  };

  useEffect(() => {
    if (asset) startNew();
  }, [asset?.id]);

  const isAttackTemplateMode = idPrefix === "attack_template";
  const idFormatHint = isAttackTemplateMode
    ? t("Use attack_template.short_name.v1. Avoid saving the example value unchanged.")
    : t("Use plugin.area.name.v1, for example general_multi_turn.custom.v1.");
  const newAssetVariableList = useMemo(
    () => newAssetVariables.split(/[\n,]+/).map(v => v.trim()).filter(Boolean),
    [newAssetVariables],
  );
  const newAssetVariableValidation = useMemo(
    () => validateTemplateVariables(newAssetVariableList, newAssetTemplate),
    [newAssetTemplate, newAssetVariableList],
  );
  const newAssetPlaceholders = useMemo(
    () => extractTemplateVariables(newAssetTemplate),
    [newAssetTemplate],
  );
  const diffRows = useMemo(
    () => asset ? changedLineRows(asset.template, template) : [],
    [asset, template],
  );
  const Heading = headingLevel;

  return (
    <div className="space-y-6">
      <div>
        <Heading className="text-2xl font-bold tracking-tight flex items-center gap-2">
          <FileText className="h-6 w-6" />
          {t(titleKey)}
        </Heading>
        <p className="text-sm text-gray-600 mt-1">{t(descriptionKey)}</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-[340px_minmax(0,1fr)] gap-4">
        <Card className="min-h-0">
          <CardHeader className="flex items-center justify-between gap-3">
            <CardTitle>{t(listTitleKey)}</CardTitle>
            <Button variant="secondary" size="sm" icon={<Plus className="h-4 w-4" />} onClick={startCreateAsset}>
              {t(newAssetButtonKey)}
            </Button>
          </CardHeader>
          <CardBody className="space-y-3">
            <Field label={t("Search")}>
              <Input
                value={assetSearch}
                onChange={e => setAssetSearch(e.target.value)}
                placeholder={t("Search by ID, title, category, or plugin")}
              />
            </Field>
            {categories.length > 0 && (
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">
                  {t("Category")}
                </label>
                <select
                  className="w-full rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm outline-none focus:border-brand-500 focus:ring-2 focus:ring-brand-100"
                  value={selectedCategory}
                  onChange={e => setSelectedCategory(e.target.value)}
                >
                  <option value="all">{t("All categories")}</option>
                  {categories.map(category => (
                    <option key={category} value={category}>{category}</option>
                  ))}
                </select>
              </div>
            )}
            <div className="max-h-[calc(100dvh-18rem)] min-h-0 space-y-2 overflow-y-auto pr-1">
              {assets.map(a => {
                const isSelected = !creatingAsset && selectedId === a.id;
                const version = deriveVersion(a.id);
                return (
                  <button key={a.id} type="button" title={a.id}
                    onClick={() => { setCreatingAsset(false); setSelectedId(a.id); }}
                    className={clsx(
                      "block w-full rounded-lg border px-3 py-2.5 text-left transition",
                      isSelected
                        ? "border-brand-500 bg-brand-50 shadow-soft"
                        : "border-gray-200 hover:border-gray-300 hover:bg-gray-50",
                    )}>
                    <div className="flex items-start justify-between gap-2 min-w-0">
                      <div className="min-w-0 flex-1">
                        <div className={clsx(
                          "text-sm font-semibold leading-snug break-words line-clamp-2",
                          isSelected ? "text-brand-900" : "text-gray-900",
                        )}>
                          {deriveTitle(a.id, idPrefix)}
                        </div>
                        <div className="mt-1 font-mono text-[10.5px] leading-tight text-gray-500 truncate">
                          {a.id}
                        </div>
                      </div>
                      {version && (
                        <span className="shrink-0 inline-flex items-center rounded bg-gray-100 px-1.5 py-0.5 font-mono text-[10px] font-medium text-gray-600 ring-1 ring-inset ring-gray-200">
                          {version}
                        </span>
                      )}
                    </div>
                    {(a.is_custom || a.active_override) && (
                      <div className="mt-2 flex flex-wrap gap-1">
                        {a.category && <Badge tone="gray">{a.category}</Badge>}
                        {a.is_custom && <Badge tone="amber">{t("custom")}</Badge>}
                        {a.active_override && <Badge tone="indigo">{t("override")}</Badge>}
                      </div>
                    )}
                    {!(a.is_custom || a.active_override) && a.category && (
                      <div className="mt-2">
                        <Badge tone="gray">{a.category}</Badge>
                      </div>
                    )}
                  </button>
                );
              })}
              {assets.length === 0 && (
                <div className="text-sm text-gray-500 py-4 text-center">{t("No assets yet.")}</div>
              )}
            </div>
          </CardBody>
        </Card>

        {creatingAsset && (
          <Card>
            <CardHeader><CardTitle>{t(createTitleKey)}</CardTitle></CardHeader>
            <CardBody className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <Field label={t("Asset ID")} hint={idFormatHint} required>
                  <Input
                    placeholder={isAttackTemplateMode ? "attack_template.short_name.v1" : "general_multi_turn.custom.v1"}
                    value={newAssetId}
                    onChange={e => setNewAssetId(e.target.value)}
                  />
                </Field>
                <Field label={t("Version")}>
                  <Input type="number" min="1" value={newAssetVersion} onChange={e => setNewAssetVersion(e.target.value)} />
                </Field>
                <Field label={t("Plugin")}>
                  <Input value={newAssetPlugin} onChange={e => setNewAssetPlugin(e.target.value)} />
                </Field>
                <Field label={t("Purpose")}>
                  <Input value={newAssetPurpose} onChange={e => setNewAssetPurpose(e.target.value)} />
                </Field>
                <Field label={t("Category")}>
                  <Input value={newAssetCategory} onChange={e => setNewAssetCategory(e.target.value)} />
                </Field>
              </div>
              <Field label={t("Variables")} hint={t("Leave blank to infer from template variables.")}>
                <Textarea rows={3} placeholder={"goal\ntranscript\nevaluator_feedback"} value={newAssetVariables} onChange={e => setNewAssetVariables(e.target.value)} />
              </Field>
              <Field label={t("Template")} required>
                <Textarea rows={16} value={newAssetTemplate} onChange={e => setNewAssetTemplate(e.target.value)} />
              </Field>
              {isAttackTemplateMode && (
                <div className="rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-800">
                  {t("Attack templates are sent to the tested model. Review variables before saving.")}
                </div>
              )}
              {(newAssetPlaceholders.length > 0 || newAssetVariableValidation.missing.length > 0 || newAssetVariableValidation.unused.length > 0) && (
                <div
                  role={newAssetVariableValidation.missing.length || newAssetVariableValidation.unused.length ? "alert" : undefined}
                  className="rounded-md border border-sky-200 bg-sky-50 px-3 py-2 text-xs text-sky-800"
                >
                  <div className="font-medium">{t("Template variables")}</div>
                  <div className="mt-1">
                    {t("Placeholders found: {{variables}}", {
                      variables: newAssetPlaceholders.length ? newAssetPlaceholders.map(v => `{${v}}`).join(", ") : t("none"),
                    })}
                  </div>
                  {newAssetVariableValidation.missing.length > 0 && (
                    <div className="mt-1 text-amber-800">
                      {t("Missing from Variables: {{variables}}", { variables: newAssetVariableValidation.missing.join(", ") })}
                    </div>
                  )}
                  {newAssetVariableValidation.unused.length > 0 && (
                    <div className="mt-1 text-amber-800">
                      {t("Unused variables: {{variables}}", { variables: newAssetVariableValidation.unused.join(", ") })}
                    </div>
                  )}
                </div>
              )}
              <div className="flex flex-wrap justify-end gap-2">
                <Button variant="secondary" onClick={() => setCreatingAsset(false)}>
                  {t("Cancel")}
                </Button>
                <Button icon={<Save className="h-4 w-4" />}
                  loading={createAssetMut.isPending}
                  disabled={!newAssetId.trim() || !newAssetTemplate.trim()}
                  onClick={() => createAssetMut.mutate()}>
                  {t(saveAssetButtonKey)}
                </Button>
              </div>
            </CardBody>
          </Card>
        )}

        {!creatingAsset && asset && (
          <div className="space-y-4 min-w-0">
            <Card>
              <CardHeader>
                <div className="min-w-0">
                  <CardTitle className="text-base leading-snug break-words">
                    {deriveTitle(asset.id, idPrefix)}
                  </CardTitle>
                  <p className="mt-1 font-mono text-[11px] text-gray-500 break-all">
                    {asset.id}
                  </p>
                </div>
              </CardHeader>
              <CardBody className="space-y-4">
                <div className="flex flex-wrap gap-2">
                  <Badge>v{asset.version}</Badge>
                  <Badge tone="blue">{asset.plugin}</Badge>
                  {asset.category && <Badge tone="gray">{asset.category}</Badge>}
                  {asset.purpose && asset.purpose !== asset.plugin && (
                    <Badge tone="gray">{asset.purpose}</Badge>
                  )}
                  {asset.is_custom && <Badge tone="amber">{t("custom")}</Badge>}
                  {asset.variables.map(v => <Badge key={v}>{`{${v}}`}</Badge>)}
                </div>
                <Field label={t(asset.is_custom ? "Base template" : "Built-in template")}>
                  <Textarea rows={10} readOnly value={asset.template} />
                </Field>
                <div className="flex gap-2">
                  <Button variant="secondary" size="sm" icon={<RotateCcw className="h-4 w-4" />}
                    disabled={!asset.active_override}
                    onClick={() => activeMut.mutate(null)}>
                    {t(asset.active_override ? "Revert to built-in" : "Using built-in")}
                  </Button>
                  <Button variant="secondary" size="sm" icon={<Plus className="h-4 w-4" />} onClick={startNew}>
                    {t("New override")}
                  </Button>
                </div>
              </CardBody>
            </Card>

            <div className="grid grid-cols-1 xl:grid-cols-[280px_minmax(0,1fr)] gap-4">
              <Card>
                <CardHeader><CardTitle>{t("Overrides")}</CardTitle></CardHeader>
                <CardBody className="space-y-2">
                  {asset.overrides?.length ? asset.overrides.map(o => (
                    <button key={o.id} type="button" title={o.name}
                      onClick={() => setEditingId(o.id)}
                      className={clsx(
                        "block w-full rounded-lg border px-3 py-2 text-left transition",
                        editingId === o.id
                          ? "border-brand-500 bg-brand-50"
                          : "border-gray-200 hover:border-gray-300 hover:bg-gray-50",
                      )}>
                      <div className="flex items-center justify-between gap-2 min-w-0">
                        <span className="min-w-0 flex-1 truncate text-sm font-medium text-gray-900">{o.name}</span>
                        {o.is_active && (
                          <span className="shrink-0 inline-flex items-center gap-1 rounded-full bg-emerald-50 px-1.5 py-0.5 text-[10px] font-medium text-emerald-700 ring-1 ring-inset ring-emerald-200">
                            <CheckCircle className="h-3 w-3" />
                            {t("Active")}
                          </span>
                        )}
                      </div>
                    </button>
                  )) : <div className="text-sm text-gray-500">{t("No overrides yet.")}</div>}
                </CardBody>
              </Card>

              <Card>
                <CardHeader><CardTitle>{editingId ? t("Edit override") : t("New override")}</CardTitle></CardHeader>
                <CardBody className="space-y-4">
                  <Field label={t("Name")}>
                    <Input value={name} onChange={e => setName(e.target.value)} />
                  </Field>
                  <Field label={t("Template")}>
                    <Textarea rows={14} value={template} onChange={e => setTemplate(e.target.value)} />
                  </Field>
                  {isAttackTemplateMode && (
                    <div className="rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-800">
                      {t("Attack templates are sent to the tested model. Review variables before saving.")}
                    </div>
                  )}
                  <details className="rounded-lg border border-gray-200 bg-gray-50 p-3 text-xs text-gray-600">
                    <summary className="cursor-pointer font-medium text-gray-700">{t("Review template changes")}</summary>
                    <div className="mt-3 grid grid-cols-1 lg:grid-cols-2 gap-3">
                      <DiffColumn
                        label={t("Base template")}
                        count={asset.template.split("\n").length}
                        rows={diffRows}
                        side="base"
                      />
                      <DiffColumn
                        label={t("Draft template")}
                        count={template.split("\n").length}
                        rows={diffRows}
                        side="draft"
                      />
                    </div>
                  </details>
                  <div className="flex flex-wrap justify-end gap-2">
                    {editingId && (
                      <Button variant="secondary" icon={<CheckCircle className="h-4 w-4" />}
                        onClick={() => activeMut.mutate(editingId)}>
                        {t("Make active")}
                      </Button>
                    )}
                    <Button icon={<Save className="h-4 w-4" />}
                      loading={saveMut.isPending}
                      disabled={!name.trim() || !template.trim()}
                      onClick={() => saveMut.mutate()}>
                      {t("Save")}
                    </Button>
                  </div>
                </CardBody>
              </Card>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function DiffColumn({
  label,
  count,
  rows,
  side,
}: {
  label: string;
  count: number;
  rows: ReturnType<typeof changedLineRows>;
  side: "base" | "draft";
}) {
  const { t } = useI18n();
  return (
    <div>
      <div className="mb-1 flex items-center justify-between gap-2 text-[11px] font-semibold uppercase tracking-wider text-gray-500">
        <span>{label}</span>
        <span>{t("{{count}} lines", { count })}</span>
      </div>
      <div className="max-h-64 overflow-auto rounded border border-gray-200 bg-white py-1 font-mono">
        {rows.map(row => (
          <div
            key={`${side}-${row.lineNumber}`}
            className={clsx(
              "grid grid-cols-[2.5rem_minmax(0,1fr)] gap-2 px-2 py-0.5 text-[11px]",
              row.changed ? "bg-amber-50 text-amber-900" : "text-gray-700",
            )}
          >
            <span className="select-none text-right text-gray-400">{row.lineNumber}</span>
            <span className="whitespace-pre-wrap break-words">{row[side] || " "}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
