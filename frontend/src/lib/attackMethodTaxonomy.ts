export type CategoryScope =
  | { kind: "all" }
  | { kind: "uncategorized" }
  | { kind: "category"; id: string };

export type TaxonomyCategory = {
  id: string;
  name: string;
  alias?: string | null;
  type?: string | null;
  display_order: number;
};

export type TaxonomyMapping = {
  executor_kind: "executor" | "converter_method";
  executor_name: string;
  category_id: string;
  technical_category?: string | null;
};

export function mappingKey(mapping: TaxonomyMapping): string {
  return `${mapping.executor_kind}:${mapping.executor_name}`;
}

export function sortCategories<T extends TaxonomyCategory>(categories: T[]): T[] {
  return [...categories].sort((a, b) => {
    if (a.display_order !== b.display_order) return a.display_order - b.display_order;
    return (a.alias || a.name || a.id).localeCompare(b.alias || b.name || b.id);
  });
}

export function scopeMappings<T extends TaxonomyMapping>(
  mappings: T[],
  categoryById: Map<string, TaxonomyCategory>,
  scope: CategoryScope,
): T[] {
  if (scope.kind === "all") return mappings;
  if (scope.kind === "uncategorized") {
    return mappings.filter(mapping => !categoryById.has(mapping.category_id));
  }
  return mappings.filter(mapping => mapping.category_id === scope.id);
}

export function filterMappings<T extends TaxonomyMapping>(
  mappings: T[],
  categoryById: Map<string, TaxonomyCategory>,
  search: string,
  kindFilter: string,
): T[] {
  const q = search.trim().toLowerCase();
  return mappings.filter(mapping => {
    if (kindFilter !== "all" && mapping.executor_kind !== kindFilter) return false;
    if (!q) return true;
    const category = categoryById.get(mapping.category_id);
    return mapping.executor_name.toLowerCase().includes(q)
      || mapping.executor_kind.toLowerCase().includes(q)
      || (mapping.technical_category ?? "").toLowerCase().includes(q)
      || (category?.name ?? "").toLowerCase().includes(q)
      || (category?.alias ?? "").toLowerCase().includes(q);
  });
}
