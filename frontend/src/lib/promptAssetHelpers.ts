export type LineDiffRow = {
  lineNumber: number;
  base: string;
  draft: string;
  changed: boolean;
};

export function extractTemplateVariables(template: string): string[] {
  const variables: string[] = [];
  const seen = new Set<string>();
  for (const match of template.matchAll(/\{([A-Za-z_][A-Za-z0-9_]*)\}/g)) {
    const name = match[1];
    if (!seen.has(name)) {
      seen.add(name);
      variables.push(name);
    }
  }
  return variables;
}

export function validateTemplateVariables(variables: string[], template: string) {
  const normalizedVariables = variables.map(v => v.trim()).filter(Boolean);
  const declared = new Set(normalizedVariables);
  const placeholders = extractTemplateVariables(template);
  const used = new Set(placeholders);
  return {
    missing: placeholders.filter(name => !declared.has(name)),
    unused: normalizedVariables.filter(name => !used.has(name)),
  };
}

export function changedLineRows(base: string, draft: string): LineDiffRow[] {
  const baseLines = base.split("\n");
  const draftLines = draft.split("\n");
  const length = Math.max(baseLines.length, draftLines.length);
  return Array.from({ length }, (_, index) => {
    const baseLine = baseLines[index] ?? "";
    const draftLine = draftLines[index] ?? "";
    return {
      lineNumber: index + 1,
      base: baseLine,
      draft: draftLine,
      changed: baseLine !== draftLine,
    };
  });
}
