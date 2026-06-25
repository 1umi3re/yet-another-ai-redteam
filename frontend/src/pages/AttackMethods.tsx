import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Edit3, Plus, Save, Search, Tags, Trash2, X } from "lucide-react";
import { useMemo, useState } from "react";
import { toast } from "sonner";
import { Badge } from "../components/ui/Badge";
import { Button } from "../components/ui/Button";
import { Card, CardBody } from "../components/ui/Card";
import { Field, Input, Select, Textarea } from "../components/ui/Form";
import { api } from "../lib/api";
import { extractTemplateVariables } from "../lib/promptAssetHelpers";
import {
  CategoryScope,
  filterMappings,
  formatAttackMethodName,
  mappingKey,
  scopeMappings,
  sortCategories,
} from "../lib/attackMethodTaxonomy";
import { useI18n } from "../lib/i18n";
import clsx from "clsx";

type Category = {
  id: string;
  name: string;
  alias: string;
  type: string;
  description?: string | null;
  display_order: number;
  is_builtin: boolean;
  mapped_count: number;
};

type Mapping = {
  executor_kind: "executor" | "converter_method";
  executor_name: string;
  category_id: string;
  technical_category?: string | null;
  is_builtin: boolean;
};

type Catalog = {
  categories: Category[];
  mappings: Mapping[];
};

type AttackMethodTemplate = {
  id: string;
  asset_id: string;
  name: string;
  template: string;
  is_builtin: boolean;
  is_active: boolean;
  created_at?: string | null;
  updated_at?: string | null;
};

type AttackMethodTemplateDetail = {
  executor_kind: string;
  executor_name: string;
  is_template_backed: boolean;
  default_asset_id: string | null;
  active_override?: { id: string } | null;
  asset?: {
    id: string;
    variables: string[];
    template: string;
  };
  templates: AttackMethodTemplate[];
};

type Draft = {
  id: string;
  name: string;
  alias: string;
  type: string;
  description: string;
  display_order: string;
};

type CategoryEditMode = "none" | "create" | "edit";

const emptyDraft: Draft = {
  id: "",
  name: "",
  alias: "",
  type: "",
  description: "",
  display_order: "1000",
};

export default function AttackMethods() {
  const { t, language } = useI18n();
  const queryClient = useQueryClient();
  const { data: catalog } = useQuery<Catalog>({
    queryKey: ["attack-method-categories"],
    queryFn: async () => (await api.get("/api/attack-method-categories")).data,
  });
  const { data: plugins } = useQuery({
    queryKey: ["plugins"],
    queryFn: async () => (await api.get("/api/plugins")).data,
  });

  const [scope, setScope] = useState<CategoryScope>({ kind: "all" });
  const [selectedMethodKey, setSelectedMethodKey] = useState("");
  const [selectedMappingKeys, setSelectedMappingKeys] = useState<Set<string>>(new Set());
  const [search, setSearch] = useState("");
  const [kindFilter, setKindFilter] = useState("all");
  const [draft, setDraft] = useState<Draft>(emptyDraft);
  const [editingId, setEditingId] = useState("");
  const [categoryEditMode, setCategoryEditMode] = useState<CategoryEditMode>("none");
  const [mappingEditKey, setMappingEditKey] = useState("");
  const [mappingDraft, setMappingDraft] = useState({ categoryId: "", technicalCategory: "" });
  const [batchCategoryId, setBatchCategoryId] = useState("");
  const [updatedMappingKey, setUpdatedMappingKey] = useState("");

  const categories = catalog?.categories ?? [];
  const mappings = catalog?.mappings ?? [];
  const sortedCategories = useMemo(() => sortCategories(categories), [categories]);
  const categoryById = useMemo(
    () => new Map(categories.map(category => [category.id, category])),
    [categories],
  );
  const executorLanguageSupport: Record<string, string[]> = plugins?.executor_language_support ?? {};
  const executorMethodDescriptions: Record<string, string> = plugins?.executor_method_descriptions ?? {};
  const selectedMapping = useMemo(
    () => mappings.find(mapping => mappingKey(mapping) === selectedMethodKey) ?? null,
    [mappings, selectedMethodKey],
  );
  const selectedCategory = scope.kind === "category" ? categoryById.get(scope.id) : undefined;
  const uncategorizedCount = useMemo(
    () => mappings.filter(mapping => !categoryById.has(mapping.category_id)).length,
    [categoryById, mappings],
  );
  const scopedMappings = useMemo(
    () => scopeMappings(mappings, categoryById, scope),
    [categoryById, mappings, scope],
  );
  const filteredMappings = useMemo(
    () => filterMappings(scopedMappings, categoryById, search, kindFilter, language),
    [categoryById, kindFilter, language, scopedMappings, search],
  );
  const selectedBatchMappings = useMemo(
    () => mappings.filter(mapping => selectedMappingKeys.has(mappingKey(mapping))),
    [mappings, selectedMappingKeys],
  );
  const canSaveCategory = draft.name.trim() && (editingId || draft.id.trim());
  const missingCategoryFields = [
    !editingId && !draft.id.trim() && t("Category ID"),
    !draft.name.trim() && t("Name"),
  ].filter(Boolean);

  const categoryLabel = (category: Category | undefined) => {
    if (!category) return t("Uncategorized");
    return language === "zh" ? category.name : (category.alias || category.name);
  };
  const methodKindLabel = (mapping: Mapping) => (
    mapping.executor_kind === "executor" ? t("Native executor") : t("Converter method")
  );
  const languageLabel = (name: string) => {
    const languages = executorLanguageSupport[name] ?? [];
    return languages.length ? languages.join(", ") : t("No compatible language support");
  };
  const scopeTitle = () => {
    if (scope.kind === "all") return t("All methods");
    if (scope.kind === "uncategorized") return t("Uncategorized");
    return categoryLabel(selectedCategory);
  };

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ["attack-method-categories"] });
    queryClient.invalidateQueries({ queryKey: ["plugins"] });
  };

  const saveCategory = useMutation({
    mutationFn: async () => {
      const body = {
        id: draft.id.trim(),
        name: draft.name.trim(),
        alias: draft.alias.trim(),
        type: draft.type.trim(),
        description: draft.description.trim() || null,
        display_order: Number(draft.display_order || "0"),
      };
      if (editingId) {
        const { id, ...patch } = body;
        return (await api.patch(`/api/attack-method-categories/${editingId}`, patch)).data;
      }
      return (await api.post("/api/attack-method-categories", body)).data;
    },
    onSuccess: (category) => {
      toast.success(t("Attack category saved"));
      setDraft(emptyDraft);
      setEditingId("");
      setCategoryEditMode("none");
      if (category?.id) setScope({ kind: "category", id: category.id });
      invalidate();
    },
    onError: (e: any) => toast.error(e?.response?.data?.detail ?? t("Failed to save attack category")),
  });

  const deleteCategory = useMutation({
    mutationFn: async (categoryId: string) => {
      await api.delete(`/api/attack-method-categories/${categoryId}`);
    },
    onSuccess: () => {
      toast.success(t("Attack category deleted"));
      setScope({ kind: "all" });
      setCategoryEditMode("none");
      setEditingId("");
      invalidate();
    },
    onError: (e: any) => toast.error(e?.response?.data?.detail ?? t("Failed to delete attack category")),
  });

  const updateMapping = useMutation({
    mutationFn: async ({
      mapping,
      categoryId,
      technicalCategory,
    }: {
      mapping: Mapping;
      categoryId: string;
      technicalCategory?: string;
    }) => (
      await api.put(
        `/api/attack-method-categories/mappings/${mapping.executor_kind}/${mapping.executor_name}`,
        {
          category_id: categoryId,
          technical_category: technicalCategory ?? mapping.technical_category,
        },
      )
    ).data,
    onSuccess: (_data, variables) => {
      toast.success(t("Attack mapping saved"));
      setUpdatedMappingKey(mappingKey(variables.mapping));
      setMappingEditKey("");
      invalidate();
    },
    onError: (e: any) => toast.error(e?.response?.data?.detail ?? t("Failed to save attack mapping")),
  });

  const batchUpdate = useMutation({
    mutationFn: async ({ selected, categoryId }: { selected: Mapping[]; categoryId: string }) => {
      await Promise.all(selected.map(mapping => api.put(
        `/api/attack-method-categories/mappings/${mapping.executor_kind}/${mapping.executor_name}`,
        {
          category_id: categoryId,
          technical_category: mapping.technical_category,
        },
      )));
    },
    onSuccess: () => {
      toast.success(t("Updated {{count}} mappings", { count: selectedBatchMappings.length }));
      setSelectedMappingKeys(new Set());
      setBatchCategoryId("");
      invalidate();
    },
    onError: (e: any) => toast.error(e?.response?.data?.detail ?? t("Failed to update selected mappings")),
  });

  const selectScope = (next: CategoryScope) => {
    setScope(next);
    setSearch("");
    setSelectedMethodKey("");
    setMappingEditKey("");
    setCategoryEditMode("none");
    setEditingId("");
  };

  const toggleMappingSelection = (key: string) => {
    setSelectedMappingKeys(prev => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  };

  const startCreateCategory = () => {
    setSelectedMethodKey("");
    setMappingEditKey("");
    setCategoryEditMode("create");
    setEditingId("");
    setDraft(emptyDraft);
  };

  const startEditCategory = (category: Category) => {
    setSelectedMethodKey("");
    setMappingEditKey("");
    setCategoryEditMode("edit");
    setEditingId(category.id);
    setDraft({
      id: category.id,
      name: category.name,
      alias: category.alias ?? "",
      type: category.type ?? "",
      description: category.description ?? "",
      display_order: String(category.display_order),
    });
  };

  const startEditMapping = (mapping: Mapping) => {
    setMappingEditKey(mappingKey(mapping));
    setMappingDraft({
      categoryId: mapping.category_id,
      technicalCategory: mapping.technical_category ?? "",
    });
  };

  const emptyMessage = () => {
    if (search.trim()) return t("No attack methods match this search.");
    if (scope.kind === "uncategorized") return t("No uncategorized methods.");
    if (scope.kind === "category") return t("No methods are mapped to this category yet.");
    return t("No attack methods match this search.");
  };

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">{t("Attack Method Taxonomy")}</h1>
          <p className="text-sm text-gray-500 mt-1">
            {t("Find methods, organize mappings, and maintain taxonomy categories.")}
          </p>
        </div>
        <div className="flex flex-wrap gap-2 text-xs text-gray-500">
          <Badge tone="gray">{t("{{count}} methods", { count: mappings.length })}</Badge>
          <Badge tone="gray">{t("{{count}} categories", { count: categories.length })}</Badge>
          {uncategorizedCount > 0 && <Badge tone="amber">{t("{{count}} uncategorized", { count: uncategorizedCount })}</Badge>}
        </div>
      </div>

      <Card className="overflow-hidden">
        <CardBody className="p-0">
          <div className="grid min-h-[calc(100dvh-12rem)] lg:grid-cols-[16rem_minmax(0,1fr)_22rem]">
            <section className="min-h-0 border-b border-gray-200 bg-gray-50/60 lg:border-b-0 lg:border-r">
              <div className="flex items-center justify-between gap-2 border-b border-gray-200 px-3 py-2.5">
                <div>
                  <div className="text-xs font-semibold uppercase tracking-wide text-gray-500">{t("Scope")}</div>
                  <div className="text-sm font-medium text-gray-900">{t("Categories")}</div>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  aria-label={t("Create category")}
                  icon={<Plus className="h-3.5 w-3.5" />}
                  onClick={startCreateCategory}
                >
                  {t("New")}
                </Button>
              </div>
              <div className="max-h-[calc(100dvh-16rem)] space-y-1 overflow-y-auto p-2">
                <ScopeButton
                  active={scope.kind === "all"}
                  label={t("All methods")}
                  meta={t("Every mapped method")}
                  count={mappings.length}
                  onClick={() => selectScope({ kind: "all" })}
                />
                <ScopeButton
                  active={scope.kind === "uncategorized"}
                  label={t("Uncategorized")}
                  meta={t("Missing category")}
                  count={uncategorizedCount}
                  tone={uncategorizedCount ? "amber" : "gray"}
                  onClick={() => selectScope({ kind: "uncategorized" })}
                />
                <div className="pt-1">
                  {sortedCategories.map(category => (
                    <ScopeButton
                      key={category.id}
                      active={scope.kind === "category" && scope.id === category.id}
                      label={categoryLabel(category)}
                      meta={category.type || category.id}
                      count={category.mapped_count}
                      badge={category.is_builtin ? t("Built-in") : t("custom")}
                      tone={category.is_builtin ? "blue" : "green"}
                      onClick={() => selectScope({ kind: "category", id: category.id })}
                    />
                  ))}
                </div>
              </div>
            </section>

            <section className="min-w-0 border-b border-gray-200 lg:border-b-0 lg:border-r">
              <div className="border-b border-gray-200 px-4 py-3">
                <div className="flex flex-wrap items-end justify-between gap-3">
                  <div>
                    <div className="text-xs font-semibold uppercase tracking-wide text-gray-500">{t("Methods")}</div>
                    <div className="text-sm font-medium text-gray-900">
                      {scopeTitle()} · {t("Showing {{count}} of {{total}}", {
                        count: filteredMappings.length,
                        total: scopedMappings.length,
                      })}
                    </div>
                  </div>
                  <div className="grid w-full gap-2 sm:w-auto sm:grid-cols-[minmax(16rem,1fr)_10rem]">
                    <Field label={t("Search")}>
                      <div className="relative">
                        <Search className="pointer-events-none absolute left-3 top-2.5 h-4 w-4 text-gray-400" />
                        <Input
                          className="pl-9"
                          value={search}
                          onChange={event => setSearch(event.target.value)}
                          placeholder={t("Search methods")}
                        />
                      </div>
                    </Field>
                    <Field label={t("Kind")}>
                      <Select value={kindFilter} onChange={event => setKindFilter(event.target.value)}>
                        <option value="all">{t("All")}</option>
                        <option value="executor">{t("Native")}</option>
                        <option value="converter_method">{t("Converter")}</option>
                      </Select>
                    </Field>
                  </div>
                </div>

                {selectedMappingKeys.size > 0 && (
                  <div className="mt-3 flex flex-wrap items-end gap-2 rounded-md border border-brand-100 bg-brand-50/60 px-3 py-2">
                    <div className="mr-auto text-sm">
                      <span className="font-medium text-brand-900">
                        {t("{{count}} selected", { count: selectedMappingKeys.size })}
                      </span>
                      <span className="ml-2 text-xs text-brand-700">{t("Applies to selected methods only.")}</span>
                    </div>
                    <div className="min-w-56">
                      <Field label={t("Category")}>
                        <Select
                          value={batchCategoryId}
                          disabled={batchUpdate.isPending}
                          onChange={event => setBatchCategoryId(event.target.value)}
                        >
                          <option value="">{t("-- pick category --")}</option>
                          {sortedCategories.map(category => (
                            <option key={category.id} value={category.id}>{categoryLabel(category)}</option>
                          ))}
                        </Select>
                      </Field>
                    </div>
                    <Button
                      size="sm"
                      icon={<Save className="h-3.5 w-3.5" />}
                      loading={batchUpdate.isPending}
                      disabled={!batchCategoryId || selectedBatchMappings.length === 0}
                      onClick={() => batchUpdate.mutate({ selected: selectedBatchMappings, categoryId: batchCategoryId })}
                    >
                      {t("Apply category")}
                    </Button>
                    <Button
                      size="sm"
                      variant="secondary"
                      disabled={batchUpdate.isPending}
                      onClick={() => setSelectedMappingKeys(new Set())}
                    >
                      {t("Clear selection")}
                    </Button>
                  </div>
                )}
              </div>

              <div className="max-h-[calc(100dvh-20rem)] overflow-auto">
                <table className="w-full text-left text-sm">
                  <thead className="sticky top-0 z-10 bg-white text-xs uppercase tracking-wide text-gray-500 shadow-[0_1px_0_0_rgb(229,231,235)]">
                    <tr>
                      <th className="px-4 py-2">{t("Method")}</th>
                      <th className="px-4 py-2">{t("Technical category")}</th>
                      <th className="px-4 py-2">{t("Languages")}</th>
                      <th className="px-4 py-2">{t("Category")}</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {filteredMappings.map(mapping => {
                      const key = mappingKey(mapping);
                      const active = selectedMethodKey === key;
                      const checked = selectedMappingKeys.has(key);
                      const rowCategory = categoryById.get(mapping.category_id);
                      const showCheckbox = selectedMappingKeys.size > 0;
                      const methodName = formatAttackMethodName(mapping.executor_name, language);
                      return (
                        <tr
                          key={key}
                          tabIndex={0}
                          aria-selected={active}
                          className={clsx(
                            "group cursor-pointer outline-none transition focus-within:bg-brand-50/60 focus:bg-brand-50/60 hover:bg-gray-50",
                            active && "bg-brand-50/70",
                            checked && "bg-brand-50/50",
                          )}
                          onClick={() => {
                            setSelectedMethodKey(key);
                            setCategoryEditMode("none");
                          }}
                          onKeyDown={event => {
                            if (event.key === "Enter") {
                              setSelectedMethodKey(key);
                              setCategoryEditMode("none");
                            }
                          }}
                        >
                          <td className="px-4 py-2.5">
                            <div className="flex items-start gap-2">
                              <input
                                type="checkbox"
                                aria-label={t("Select attack method {{name}}", { name: methodName })}
                                checked={checked}
                                onClick={event => event.stopPropagation()}
                                onChange={() => toggleMappingSelection(key)}
                                className={clsx(
                                  "mt-0.5 h-4 w-4 rounded border-gray-300 text-brand-600 transition focus:opacity-100",
                                  showCheckbox ? "opacity-100" : "opacity-0 group-hover:opacity-100 group-focus-within:opacity-100",
                                )}
                              />
                              <div className="min-w-0">
                                <div className="flex items-center gap-2">
                                  <Tags className="h-4 w-4 shrink-0 text-gray-400" />
                                  <span className="font-medium text-gray-900 break-all">{methodName}</span>
                                </div>
                                <div className="mt-0.5 text-xs text-gray-500">{methodKindLabel(mapping)}</div>
                              </div>
                            </div>
                          </td>
                          <td className="px-4 py-2.5 text-xs text-gray-600">{mapping.technical_category ?? "other"}</td>
                          <td className="px-4 py-2.5 text-xs text-gray-600">{languageLabel(mapping.executor_name)}</td>
                          <td className="px-4 py-2.5">
                            <div className="flex flex-wrap items-center gap-1.5">
                              <span className="text-xs text-gray-700">{categoryLabel(rowCategory)}</span>
                              {mapping.is_builtin && <Badge tone="blue">{t("Built-in")}</Badge>}
                              {updatedMappingKey === key && <span aria-live="polite" className="text-[11px] text-emerald-700">{t("Updated")}</span>}
                            </div>
                          </td>
                        </tr>
                      );
                    })}
                    {filteredMappings.length === 0 && (
                      <tr>
                        <td colSpan={4} className="px-4 py-12 text-center text-sm text-gray-500">
                          {emptyMessage()}
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </section>

            <aside className="min-h-0 bg-white">
              <div className="flex items-center justify-between gap-2 border-b border-gray-200 px-4 py-3">
                <div>
                  <div className="text-xs font-semibold uppercase tracking-wide text-gray-500">{t("Detail")}</div>
                  <div className="text-sm font-medium text-gray-900">
                    {selectedMapping ? mappingName(selectedMapping, language) : scopeTitle()}
                  </div>
                </div>
                {selectedMapping && (
                  <button
                    type="button"
                    className="rounded-md p-1 text-gray-400 hover:bg-gray-100 hover:text-gray-600"
                    aria-label={t("Back to category")}
                    onClick={() => {
                      setSelectedMethodKey("");
                      setMappingEditKey("");
                    }}
                  >
                    <X className="h-4 w-4" />
                  </button>
                )}
              </div>

              <div className="max-h-[calc(100dvh-16rem)] overflow-y-auto p-4">
                {selectedMapping ? (
                  <MethodDetail
                    key={mappingKey(selectedMapping)}
                    mapping={selectedMapping}
                    currentCategory={categoryById.get(selectedMapping.category_id)}
                    description={executorMethodDescriptions[selectedMapping.executor_name] ?? ""}
                    methodName={mappingName(selectedMapping, language)}
                    categories={sortedCategories}
                    categoryLabel={categoryLabel}
                    languageLabel={languageLabel}
                    methodKindLabel={methodKindLabel}
                    mappingEditKey={mappingEditKey}
                    mappingDraft={mappingDraft}
                    setMappingDraft={setMappingDraft}
                    startEditMapping={startEditMapping}
                    cancelEdit={() => setMappingEditKey("")}
                    saveEdit={() => updateMapping.mutate({
                      mapping: selectedMapping,
                      categoryId: mappingDraft.categoryId,
                      technicalCategory: mappingDraft.technicalCategory,
                    })}
                    saving={updateMapping.isPending}
                  />
                ) : categoryEditMode !== "none" ? (
                  <CategoryEditForm
                    mode={categoryEditMode}
                    draft={draft}
                    setDraft={setDraft}
                    canSave={!!canSaveCategory}
                    missingFields={missingCategoryFields}
                    isBuiltin={categoryEditMode === "edit" && !!categoryById.get(editingId)?.is_builtin}
                    onSave={() => saveCategory.mutate()}
                    onCancel={() => {
                      setCategoryEditMode("none");
                      setEditingId("");
                      setDraft(emptyDraft);
                    }}
                    saving={saveCategory.isPending}
                  />
                ) : scope.kind === "category" && selectedCategory ? (
                  <CategoryDetail
                    category={selectedCategory}
                    label={categoryLabel(selectedCategory)}
                    onEdit={() => startEditCategory(selectedCategory)}
                    onDelete={() => {
                      if (confirm(t("Delete attack category {{name}}?", {
                        name: categoryLabel(selectedCategory),
                      }))) deleteCategory.mutate(selectedCategory.id);
                    }}
                    deleting={deleteCategory.isPending}
                    deleteDisabled={selectedCategory.mapped_count > 0}
                    deleteTitle={selectedCategory.mapped_count > 0
                      ? t("Cannot delete while {{count}} methods are mapped", { count: selectedCategory.mapped_count })
                      : undefined}
                  />
                ) : (
                  <ScopeDetail
                    scope={scope}
                    totalMethods={mappings.length}
                    totalCategories={categories.length}
                    uncategorizedCount={uncategorizedCount}
                    scopedCount={scopedMappings.length}
                    onCreateCategory={startCreateCategory}
                  />
                )}
              </div>
            </aside>
          </div>
        </CardBody>
      </Card>
    </div>
  );
}

function mappingName(mapping: Mapping, language: "en" | "zh"): string {
  return formatAttackMethodName(mapping.executor_name, language);
}

function ScopeButton({
  active,
  label,
  meta,
  count,
  badge,
  tone = "gray",
  onClick,
}: {
  active: boolean;
  label: string;
  meta: string;
  count: number;
  badge?: string;
  tone?: "gray" | "blue" | "green" | "amber";
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      aria-pressed={active}
      onClick={onClick}
      className={clsx(
        "w-full rounded-md border px-2.5 py-2 text-left transition",
        active
          ? "border-brand-300 bg-white shadow-soft ring-1 ring-brand-100"
          : "border-transparent hover:border-gray-200 hover:bg-white",
      )}
    >
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <div className="truncate text-sm font-medium text-gray-900">{label}</div>
          <div className="mt-0.5 truncate text-xs text-gray-500">{meta}</div>
        </div>
        <span className="shrink-0 rounded-full bg-gray-100 px-2 py-0.5 text-xs tabular-nums text-gray-600">{count}</span>
      </div>
      {badge && (
        <div className="mt-1.5">
          <Badge tone={tone}>{badge}</Badge>
        </div>
      )}
    </button>
  );
}

function DetailRow({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="border-b border-gray-100 pb-2 last:border-b-0 last:pb-0">
      <div className="text-[11px] font-semibold uppercase tracking-wide text-gray-500">{label}</div>
      <div className="mt-0.5 text-sm text-gray-900 break-words">{value || "—"}</div>
    </div>
  );
}

function CategoryDetail({
  category,
  label,
  onEdit,
  onDelete,
  deleting,
  deleteDisabled,
  deleteTitle,
}: {
  category: Category;
  label: string;
  onEdit: () => void;
  onDelete: () => void;
  deleting: boolean;
  deleteDisabled: boolean;
  deleteTitle?: string;
}) {
  const { t } = useI18n();
  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div>
          <div className="text-base font-semibold text-gray-900">{label}</div>
          <div className="mt-1 font-mono text-xs text-gray-500">{category.id}</div>
        </div>
        <Badge tone={category.is_builtin ? "blue" : "green"}>
          {category.is_builtin ? t("Built-in") : t("custom")}
        </Badge>
      </div>
      <div className="space-y-3">
        <DetailRow label={t("Name")} value={category.name} />
        <DetailRow label={t("Alias")} value={category.alias} />
        <DetailRow label={t("Type")} value={category.type} />
        <DetailRow label={t("Display order")} value={category.display_order} />
        <DetailRow label={t("Mapped methods")} value={category.mapped_count} />
        <DetailRow label={t("Description")} value={category.description || t("No description")} />
      </div>
      <div className="flex flex-wrap gap-2 pt-2">
        <Button variant="secondary" size="sm" icon={<Edit3 className="h-3.5 w-3.5" />} onClick={onEdit}>
          {t("Edit category")}
        </Button>
        <Button
          variant="danger"
          size="sm"
          icon={<Trash2 className="h-3.5 w-3.5" />}
          loading={deleting}
          disabled={deleteDisabled}
          title={deleteTitle}
          onClick={onDelete}
        >
          {t("Delete")}
        </Button>
      </div>
    </div>
  );
}

function ScopeDetail({
  scope,
  totalMethods,
  totalCategories,
  uncategorizedCount,
  scopedCount,
  onCreateCategory,
}: {
  scope: CategoryScope;
  totalMethods: number;
  totalCategories: number;
  uncategorizedCount: number;
  scopedCount: number;
  onCreateCategory: () => void;
}) {
  const { t } = useI18n();
  return (
    <div className="space-y-4">
      {scope.kind === "all" ? (
        <>
          <div>
            <div className="text-base font-semibold text-gray-900">{t("Taxonomy overview")}</div>
            <p className="mt-1 text-sm text-gray-500">
              {t("Review every attack method and use the left list to focus on a category.")}
            </p>
          </div>
          <div className="grid grid-cols-2 gap-2">
            <Metric label={t("Methods")} value={totalMethods} />
            <Metric label={t("Categories")} value={totalCategories} />
            <Metric label={t("Uncategorized")} value={uncategorizedCount} />
            <Metric label={t("In scope")} value={scopedCount} />
          </div>
        </>
      ) : (
        <>
          <div>
            <div className="text-base font-semibold text-gray-900">{t("Uncategorized")}</div>
            <p className="mt-1 text-sm text-gray-500">
              {t("Methods here reference a category that is missing from the current catalog.")}
            </p>
          </div>
          <Metric label={t("Uncategorized methods")} value={uncategorizedCount} />
        </>
      )}
      <Button variant="secondary" size="sm" icon={<Plus className="h-3.5 w-3.5" />} onClick={onCreateCategory}>
        {t("Create category")}
      </Button>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-md border border-gray-200 bg-gray-50 px-3 py-2">
      <div className="text-xs text-gray-500">{label}</div>
      <div className="mt-0.5 text-lg font-semibold tabular-nums text-gray-900">{value}</div>
    </div>
  );
}

function CategoryEditForm({
  mode,
  draft,
  setDraft,
  canSave,
  missingFields,
  isBuiltin,
  onSave,
  onCancel,
  saving,
}: {
  mode: CategoryEditMode;
  draft: Draft;
  setDraft: React.Dispatch<React.SetStateAction<Draft>>;
  canSave: boolean;
  missingFields: Array<string | false>;
  isBuiltin: boolean;
  onSave: () => void;
  onCancel: () => void;
  saving: boolean;
}) {
  const { t } = useI18n();
  return (
    <div className="space-y-4">
      <div>
        <div className="text-base font-semibold text-gray-900">
          {mode === "create" ? t("Create category") : t("Edit category")}
        </div>
        <p className="mt-1 text-sm text-gray-500">{t("Category maintenance is saved to this workspace taxonomy.")}</p>
      </div>
      <div className="space-y-3">
        <Field label={t("Category ID")} required={mode === "create"}>
          <Input
            value={draft.id}
            disabled={mode === "edit"}
            placeholder="custom_strategy"
            onChange={event => setDraft(prev => ({ ...prev, id: event.target.value }))}
          />
        </Field>
        <Field label={t("Name")} required>
          <Input value={draft.name} onChange={event => setDraft(prev => ({ ...prev, name: event.target.value }))} />
        </Field>
        <Field label={t("Alias")}>
          <Input value={draft.alias} onChange={event => setDraft(prev => ({ ...prev, alias: event.target.value }))} />
        </Field>
        <Field label={t("Type")}>
          <Input value={draft.type} onChange={event => setDraft(prev => ({ ...prev, type: event.target.value }))} />
        </Field>
        <Field label={t("Display order")}>
          <Input
            type="number"
            value={draft.display_order}
            onChange={event => setDraft(prev => ({ ...prev, display_order: event.target.value }))}
          />
        </Field>
        <Field label={t("Description")}>
          <Textarea rows={4} value={draft.description} onChange={event => setDraft(prev => ({ ...prev, description: event.target.value }))} />
        </Field>
      </div>
      {isBuiltin && (
        <div className="rounded-md border border-sky-200 bg-sky-50 px-3 py-2 text-sm text-sky-800">
          {t("Editing built-in category metadata affects how this workspace displays and groups attack methods.")}
        </div>
      )}
      {!canSave && missingFields.length > 0 && (
        <div role="alert" className="rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-800">
          {t("Required before saving: {{fields}}", { fields: missingFields.join(", ") })}
        </div>
      )}
      <div className="flex flex-wrap justify-end gap-2">
        <Button variant="secondary" onClick={onCancel}>{t("Cancel")}</Button>
        <Button icon={<Save className="h-4 w-4" />} loading={saving} disabled={!canSave} onClick={onSave}>
          {mode === "create" ? t("Create") : t("Save")}
        </Button>
      </div>
    </div>
  );
}

function MethodDetail({
  mapping,
  currentCategory,
  description,
  methodName,
  categories,
  categoryLabel,
  languageLabel,
  methodKindLabel,
  mappingEditKey,
  mappingDraft,
  setMappingDraft,
  startEditMapping,
  cancelEdit,
  saveEdit,
  saving,
}: {
  mapping: Mapping;
  currentCategory: Category | undefined;
  description: string;
  methodName: string;
  categories: Category[];
  categoryLabel: (category: Category | undefined) => string;
  languageLabel: (name: string) => string;
  methodKindLabel: (mapping: Mapping) => string;
  mappingEditKey: string;
  mappingDraft: { categoryId: string; technicalCategory: string };
  setMappingDraft: React.Dispatch<React.SetStateAction<{ categoryId: string; technicalCategory: string }>>;
  startEditMapping: (mapping: Mapping) => void;
  cancelEdit: () => void;
  saveEdit: () => void;
  saving: boolean;
}) {
  const { t } = useI18n();
  const queryClient = useQueryClient();
  const editing = mappingEditKey === mappingKey(mapping);
  const templateQueryKey = ["attack-method-templates", mapping.executor_kind, mapping.executor_name];
  const { data: templateDetail } = useQuery<AttackMethodTemplateDetail>({
    queryKey: templateQueryKey,
    queryFn: async () => (
      await api.get(`/api/attack-methods/${mapping.executor_kind}/${mapping.executor_name}/templates`)
    ).data,
  });
  const [templateEditMode, setTemplateEditMode] = useState<"none" | "create" | "edit">("none");
  const [templateEditId, setTemplateEditId] = useState("");
  const [templateName, setTemplateName] = useState("");
  const [templateText, setTemplateText] = useState("");
  const [deletingTemplateId, setDeletingTemplateId] = useState("");
  const templatePlaceholders = useMemo(() => extractTemplateVariables(templateText), [templateText]);
  const templateMissingPrompt = templateEditMode !== "none" && !templatePlaceholders.includes("prompt");
  const invalidateTemplates = () => {
    queryClient.invalidateQueries({ queryKey: templateQueryKey });
    queryClient.invalidateQueries({ queryKey: ["prompt-assets"] });
  };
  const resetTemplateForm = () => {
    setTemplateEditMode("none");
    setTemplateEditId("");
    setTemplateName("");
    setTemplateText("");
  };
  const startCreateTemplate = () => {
    setTemplateEditMode("create");
    setTemplateEditId("");
    setTemplateName(t("Workspace template"));
    setTemplateText(templateDetail?.asset?.template ?? "{prompt}");
  };
  const startEditTemplate = (template: AttackMethodTemplate) => {
    if (template.is_builtin) return;
    setTemplateEditMode("edit");
    setTemplateEditId(template.id);
    setTemplateName(template.name);
    setTemplateText(template.template);
  };
  const createTemplate = useMutation({
    mutationFn: async () => (
      await api.post(`/api/attack-methods/${mapping.executor_kind}/${mapping.executor_name}/templates`, {
        name: templateName,
        template: templateText,
        active: true,
      })
    ).data,
    onSuccess: () => {
      toast.success(t("Attack template saved"));
      resetTemplateForm();
      invalidateTemplates();
    },
    onError: (e: any) => toast.error(e?.response?.data?.detail ?? t("Failed to save attack template")),
  });
  const updateTemplate = useMutation({
    mutationFn: async () => (
      await api.patch(`/api/attack-methods/templates/${templateEditId}`, {
        name: templateName,
        template: templateText,
      })
    ).data,
    onSuccess: () => {
      toast.success(t("Attack template saved"));
      resetTemplateForm();
      invalidateTemplates();
    },
    onError: (e: any) => toast.error(e?.response?.data?.detail ?? t("Failed to save attack template")),
  });
  const activateTemplate = useMutation({
    mutationFn: async (overrideId: string | null) => (
      await api.post(`/api/attack-methods/${mapping.executor_kind}/${mapping.executor_name}/templates/active`, {
        override_id: overrideId,
      })
    ).data,
    onSuccess: () => {
      toast.success(t("Active attack template updated"));
      resetTemplateForm();
      invalidateTemplates();
    },
    onError: (e: any) => toast.error(e?.response?.data?.detail ?? t("Failed to update active attack template")),
  });
  const deleteTemplate = useMutation({
    mutationFn: async (overrideId: string) => {
      await api.delete(`/api/attack-methods/templates/${overrideId}`);
    },
    onSuccess: () => {
      toast.success(t("Attack template deleted"));
      setDeletingTemplateId("");
      resetTemplateForm();
      invalidateTemplates();
    },
    onError: (e: any) => {
      setDeletingTemplateId("");
      toast.error(e?.response?.data?.detail ?? t("Failed to delete attack template"));
    },
  });
  const saveTemplate = () => {
    if (templateEditMode === "create") createTemplate.mutate();
    if (templateEditMode === "edit") updateTemplate.mutate();
  };
  const templateSaving = createTemplate.isPending || updateTemplate.isPending;
  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div className="min-w-0">
          <div className="break-all text-base font-semibold text-gray-900">{methodName}</div>
          <div className="mt-1 text-xs text-gray-500">{methodKindLabel(mapping)}</div>
        </div>
        {mapping.is_builtin && <Badge tone="blue">{t("Built-in")}</Badge>}
      </div>
      <div className="space-y-3">
        <DetailRow label={t("Function")} value={description || t("No method description")} />
        <DetailRow label={t("Technical category")} value={mapping.technical_category ?? "other"} />
        <DetailRow label={t("Compatible languages")} value={languageLabel(mapping.executor_name)} />
        <DetailRow label={t("Current category")} value={categoryLabel(currentCategory)} />
        <DetailRow label={t("Mapping key")} value={<span className="font-mono text-xs">{mappingKey(mapping)}</span>} />
      </div>
      {!editing ? (
        <Button variant="secondary" size="sm" icon={<Edit3 className="h-3.5 w-3.5" />} onClick={() => startEditMapping(mapping)}>
          {t("Edit mapping")}
        </Button>
      ) : (
        <div className="space-y-3 rounded-md border border-gray-200 bg-gray-50 p-3">
          <Field label={t("Category")}>
            <Select
              value={mappingDraft.categoryId}
              onChange={event => setMappingDraft(prev => ({ ...prev, categoryId: event.target.value }))}
            >
              {categories.map(category => (
                <option key={category.id} value={category.id}>{categoryLabel(category)}</option>
              ))}
            </Select>
          </Field>
          <Field label={t("Technical category")}>
            <Input
              value={mappingDraft.technicalCategory}
              onChange={event => setMappingDraft(prev => ({ ...prev, technicalCategory: event.target.value }))}
            />
          </Field>
          <div className="flex flex-wrap justify-end gap-2">
            <Button variant="secondary" size="sm" onClick={cancelEdit}>{t("Cancel")}</Button>
            <Button size="sm" icon={<Save className="h-3.5 w-3.5" />} loading={saving} disabled={!mappingDraft.categoryId} onClick={saveEdit}>
              {t("Save mapping")}
            </Button>
          </div>
        </div>
      )}
      {templateDetail?.is_template_backed && (
        <div className="space-y-3 border-t border-gray-200 pt-4">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div>
              <div className="text-sm font-semibold text-gray-900">{t("Attack prompt templates")}</div>
              <div className="mt-0.5 font-mono text-[11px] text-gray-500 break-all">
                {templateDetail.default_asset_id}
              </div>
            </div>
            <Button
              variant="secondary"
              size="sm"
              icon={<Plus className="h-3.5 w-3.5" />}
              onClick={startCreateTemplate}
            >
              {t("New")}
            </Button>
          </div>

          <div className="space-y-2">
            {templateDetail.templates.map(template => {
              const canActivateTemplate =
                !template.is_active && (!template.is_builtin || template.asset_id === templateDetail.default_asset_id);
              return (
                <div
                  key={template.id}
                  className={clsx(
                    "rounded-md border px-3 py-2",
                    template.is_active ? "border-brand-200 bg-brand-50/70" : "border-gray-200 bg-white",
                  )}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="min-w-0">
                      <div className="flex flex-wrap items-center gap-1.5">
                        <span className="break-words text-sm font-medium text-gray-900">{template.name}</span>
                        {template.is_builtin && <Badge tone="blue">{t("Built-in")}</Badge>}
                        {template.is_active && <Badge tone="green">{t("Active")}</Badge>}
                      </div>
                      <div
                        className={clsx(
                          "mt-2 border-l-2 pl-2",
                          template.is_active ? "border-brand-200" : "border-gray-200",
                        )}
                      >
                        <pre className="whitespace-pre-wrap break-words font-mono text-[11px] leading-5 text-gray-700 [overflow-wrap:anywhere]">{template.template}</pre>
                      </div>
                    </div>
                  </div>
                  <div className="mt-2 flex flex-wrap gap-1.5">
                    {!template.is_builtin && (
                      <Button variant="secondary" size="sm" onClick={() => startEditTemplate(template)}>
                        {t("Edit")}
                      </Button>
                    )}
                    {canActivateTemplate && (
                      <Button
                        variant="secondary"
                        size="sm"
                        loading={activateTemplate.isPending}
                        onClick={() => activateTemplate.mutate(template.is_builtin ? null : template.id)}
                      >
                        {t("Make active")}
                      </Button>
                    )}
                    {!template.is_builtin && (
                      <Button
                        variant="danger"
                        size="sm"
                        icon={<Trash2 className="h-3.5 w-3.5" />}
                        loading={deleteTemplate.isPending && deletingTemplateId === template.id}
                        onClick={() => {
                          if (confirm(t("Delete attack template {{name}}?", { name: template.name }))) {
                            setDeletingTemplateId(template.id);
                            deleteTemplate.mutate(template.id);
                          }
                        }}
                      >
                        {t("Delete")}
                      </Button>
                    )}
                  </div>
                </div>
              );
            })}
          </div>

          {templateEditMode !== "none" && (
            <div className="space-y-3 rounded-md border border-gray-200 bg-gray-50 p-3">
              <div className="text-sm font-medium text-gray-900">
                {templateEditMode === "create" ? t("Create attack template") : t("Edit attack template")}
              </div>
              <Field label={t("Name")}>
                <Input value={templateName} onChange={event => setTemplateName(event.target.value)} />
              </Field>
              <Field label={t("Template")}>
                <Textarea rows={8} value={templateText} onChange={event => setTemplateText(event.target.value)} />
              </Field>
              <div className="rounded-md border border-sky-200 bg-sky-50 px-3 py-2 text-xs text-sky-800">
                {t("Placeholders found: {{variables}}", {
                  variables: templatePlaceholders.length ? templatePlaceholders.map(v => `{${v}}`).join(", ") : t("none"),
                })}
              </div>
              {templateMissingPrompt && (
                <div role="alert" className="rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-800">
                  {t("Attack templates must include {prompt}.")}
                </div>
              )}
              <div className="flex flex-wrap justify-end gap-2">
                <Button variant="secondary" size="sm" onClick={resetTemplateForm}>{t("Cancel")}</Button>
                <Button
                  size="sm"
                  icon={<Save className="h-3.5 w-3.5" />}
                  loading={templateSaving}
                  disabled={!templateName.trim() || !templateText.trim() || templateMissingPrompt}
                  onClick={saveTemplate}
                >
                  {t("Save")}
                </Button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
