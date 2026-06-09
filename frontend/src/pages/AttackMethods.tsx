import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Edit3, Plus, Save, Search, Tags, Trash2, X } from "lucide-react";
import { useMemo, useState } from "react";
import { toast } from "sonner";
import { Badge } from "../components/ui/Badge";
import { Button } from "../components/ui/Button";
import { Card, CardBody, CardHeader, CardTitle } from "../components/ui/Card";
import { Field, Input, Select, Textarea } from "../components/ui/Form";
import { api } from "../lib/api";
import { useI18n } from "../lib/i18n";

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

type Draft = {
  id: string;
  name: string;
  alias: string;
  type: string;
  description: string;
  display_order: string;
};

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

  const [draft, setDraft] = useState<Draft>(emptyDraft);
  const [editingId, setEditingId] = useState("");
  const [search, setSearch] = useState("");
  const [kindFilter, setKindFilter] = useState("all");
  const [categoryFilter, setCategoryFilter] = useState("all");

  const categories = catalog?.categories ?? [];
  const mappings = catalog?.mappings ?? [];
  const categoryById = useMemo(
    () => new Map(categories.map(category => [category.id, category])),
    [categories],
  );
  const executorLanguageSupport: Record<string, string[]> = plugins?.executor_language_support ?? {};

  const filteredMappings = useMemo(() => {
    const q = search.trim().toLowerCase();
    return mappings.filter(mapping => {
      if (kindFilter !== "all" && mapping.executor_kind !== kindFilter) return false;
      if (categoryFilter !== "all" && mapping.category_id !== categoryFilter) return false;
      if (!q) return true;
      const category = categoryById.get(mapping.category_id);
      return mapping.executor_name.toLowerCase().includes(q)
        || mapping.executor_kind.toLowerCase().includes(q)
        || (mapping.technical_category ?? "").toLowerCase().includes(q)
        || (category?.name ?? "").toLowerCase().includes(q)
        || (category?.alias ?? "").toLowerCase().includes(q);
    });
  }, [categoryById, categoryFilter, kindFilter, mappings, search]);

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
    onSuccess: () => {
      toast.success(t("Attack category saved"));
      setDraft(emptyDraft);
      setEditingId("");
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
      invalidate();
    },
    onError: (e: any) => toast.error(e?.response?.data?.detail ?? t("Failed to delete attack category")),
  });

  const updateMapping = useMutation({
    mutationFn: async ({ mapping, categoryId }: { mapping: Mapping; categoryId: string }) => (
      await api.put(
        `/api/attack-method-categories/mappings/${mapping.executor_kind}/${mapping.executor_name}`,
        {
          category_id: categoryId,
          technical_category: mapping.technical_category,
        },
      )
    ).data,
    onSuccess: () => {
      toast.success(t("Attack mapping saved"));
      invalidate();
    },
    onError: (e: any) => toast.error(e?.response?.data?.detail ?? t("Failed to save attack mapping")),
  });

  const editCategory = (category: Category) => {
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

  const resetDraft = () => {
    setEditingId("");
    setDraft(emptyDraft);
  };

  const categoryLabel = (category: Category | undefined) => {
    if (!category) return t("Uncategorized");
    return language === "zh" ? category.name : (category.alias || category.name);
  };

  const languageLabel = (name: string) => {
    const languages = executorLanguageSupport[name] ?? [];
    return languages.length ? languages.join(", ") : t("No compatible language support");
  };

  const canSave = draft.name.trim() && (editingId || draft.id.trim());

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">{t("Attack Method Categories")}</h1>
        </div>
      </div>

      <div className="grid gap-6 xl:grid-cols-[minmax(0,0.9fr)_minmax(0,1.1fr)]">
        <Card>
          <CardHeader>
            <CardTitle>{t("Categories")}</CardTitle>
          </CardHeader>
          <CardBody className="space-y-5">
            <div className="grid gap-3 md:grid-cols-2">
              <Field label={t("Category ID")}>
                <Input
                  value={draft.id}
                  disabled={!!editingId}
                  placeholder="custom_strategy"
                  onChange={e => setDraft(prev => ({ ...prev, id: e.target.value }))}
                />
              </Field>
              <Field label={t("Display order")}>
                <Input
                  type="number"
                  value={draft.display_order}
                  onChange={e => setDraft(prev => ({ ...prev, display_order: e.target.value }))}
                />
              </Field>
              <Field label={t("Name")}>
                <Input
                  value={draft.name}
                  onChange={e => setDraft(prev => ({ ...prev, name: e.target.value }))}
                />
              </Field>
              <Field label={t("Alias")}>
                <Input
                  value={draft.alias}
                  onChange={e => setDraft(prev => ({ ...prev, alias: e.target.value }))}
                />
              </Field>
              <Field label={t("Type")}>
                <Input
                  value={draft.type}
                  onChange={e => setDraft(prev => ({ ...prev, type: e.target.value }))}
                />
              </Field>
              <div className="md:col-span-2">
                <Field label={t("Description")}>
                  <Textarea
                    rows={3}
                    value={draft.description}
                    onChange={e => setDraft(prev => ({ ...prev, description: e.target.value }))}
                  />
                </Field>
              </div>
            </div>
            <div className="flex flex-wrap gap-2">
              <Button
                icon={editingId ? <Save className="h-4 w-4" /> : <Plus className="h-4 w-4" />}
                loading={saveCategory.isPending}
                disabled={!canSave}
                onClick={() => saveCategory.mutate()}
              >
                {editingId ? t("Save") : t("Create")}
              </Button>
              {editingId && (
                <Button
                  variant="secondary"
                  icon={<X className="h-4 w-4" />}
                  onClick={resetDraft}
                >
                  {t("Cancel")}
                </Button>
              )}
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="text-xs uppercase tracking-wide text-gray-500">
                  <tr>
                    <th className="px-2 py-2">{t("Category")}</th>
                    <th className="px-2 py-2">{t("Type")}</th>
                    <th className="px-2 py-2">{t("Mapped")}</th>
                    <th className="px-2 py-2 text-right">{t("Action")}</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {categories.map(category => (
                    <tr key={category.id} className="align-top">
                      <td className="px-2 py-2">
                        <div className="font-medium text-gray-900">{category.name}</div>
                        <div className="mt-0.5 text-xs text-gray-500">{category.alias || category.id}</div>
                        <div className="mt-1 flex flex-wrap gap-1">
                          <Badge tone={category.is_builtin ? "blue" : "green"}>
                            {category.is_builtin ? t("Built-in") : t("custom")}
                          </Badge>
                          <Badge>{category.id}</Badge>
                        </div>
                      </td>
                      <td className="px-2 py-2 text-xs text-gray-600">{category.type}</td>
                      <td className="px-2 py-2 tabular-nums text-gray-700">{category.mapped_count}</td>
                      <td className="px-2 py-2">
                        <div className="flex justify-end gap-2">
                          <Button
                            variant="secondary"
                            size="sm"
                            icon={<Edit3 className="h-3.5 w-3.5" />}
                            onClick={() => editCategory(category)}
                          >
                            {t("Edit")}
                          </Button>
                          <Button
                            variant="danger"
                            size="sm"
                            icon={<Trash2 className="h-3.5 w-3.5" />}
                            disabled={category.mapped_count > 0 || deleteCategory.isPending}
                            onClick={() => {
                              if (confirm(t("Delete this category?"))) deleteCategory.mutate(category.id);
                            }}
                          >
                            {t("Delete")}
                          </Button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardBody>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>{t("Executor mappings")}</CardTitle>
          </CardHeader>
          <CardBody className="space-y-4">
            <div className="grid gap-3 md:grid-cols-[minmax(0,1fr)_160px_180px]">
              <Field label={t("Search")}>
                <div className="relative">
                  <Search className="pointer-events-none absolute left-3 top-2.5 h-4 w-4 text-gray-400" />
                  <Input
                    className="pl-9"
                    value={search}
                    onChange={e => setSearch(e.target.value)}
                    placeholder={t("Search attack methods")}
                  />
                </div>
              </Field>
              <Field label={t("Kind")}>
                <Select value={kindFilter} onChange={e => setKindFilter(e.target.value)}>
                  <option value="all">{t("All")}</option>
                  <option value="executor">{t("Native executor")}</option>
                  <option value="converter_method">{t("Converter method")}</option>
                </Select>
              </Field>
              <Field label={t("Category")}>
                <Select value={categoryFilter} onChange={e => setCategoryFilter(e.target.value)}>
                  <option value="all">{t("All categories")}</option>
                  {categories.map(category => (
                    <option key={category.id} value={category.id}>{categoryLabel(category)}</option>
                  ))}
                </Select>
              </Field>
            </div>

            <div className="text-xs text-gray-500">
              {t("Showing {{count}} of {{total}}", { count: filteredMappings.length, total: mappings.length })}
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="text-xs uppercase tracking-wide text-gray-500">
                  <tr>
                    <th className="px-2 py-2">{t("Attack method")}</th>
                    <th className="px-2 py-2">{t("Technical category")}</th>
                    <th className="px-2 py-2">{t("Languages")}</th>
                    <th className="px-2 py-2">{t("Category")}</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {filteredMappings.map(mapping => (
                    <tr key={`${mapping.executor_kind}:${mapping.executor_name}`} className="align-middle">
                      <td className="px-2 py-2">
                        <div className="flex items-center gap-2">
                          <Tags className="h-4 w-4 text-gray-400" />
                          <div>
                            <div className="font-medium text-gray-900">{mapping.executor_name}</div>
                            <div className="text-xs text-gray-500">
                              {mapping.executor_kind === "executor" ? t("Native executor") : t("Converter method")}
                            </div>
                          </div>
                        </div>
                      </td>
                      <td className="px-2 py-2 text-xs text-gray-600">{mapping.technical_category ?? "other"}</td>
                      <td className="px-2 py-2 text-xs text-gray-600">{languageLabel(mapping.executor_name)}</td>
                      <td className="px-2 py-2">
                        <Select
                          value={mapping.category_id}
                          disabled={updateMapping.isPending}
                          onChange={e => updateMapping.mutate({ mapping, categoryId: e.target.value })}
                        >
                          {categories.map(category => (
                            <option key={category.id} value={category.id}>{categoryLabel(category)}</option>
                          ))}
                        </Select>
                      </td>
                    </tr>
                  ))}
                  {filteredMappings.length === 0 && (
                    <tr>
                      <td colSpan={4} className="px-2 py-8 text-center text-xs text-gray-500">
                        {t("No attack methods match.")}
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </CardBody>
        </Card>
      </div>
    </div>
  );
}
