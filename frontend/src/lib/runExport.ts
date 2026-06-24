export type RunExportFormat = "json" | "csv";
export type ReportLanguage = "en" | "zh";

export type AttemptExportFilters = {
  verdict?: string;
  status?: string;
  targetId?: string;
  executor?: string;
};

export function buildAttemptExportParams(
  format: RunExportFormat,
  filters: AttemptExportFilters,
): Record<string, string> {
  const params: Record<string, string> = { format };
  if (filters.verdict) params.verdict = filters.verdict;
  if (filters.status) params.status = filters.status;
  if (filters.targetId) params.target_id = filters.targetId;
  if (filters.executor) params.executor = filters.executor;
  return params;
}

export function buildHtmlReportExportParams(language: ReportLanguage): Record<string, string> {
  return { lang: language };
}

export function buildRunReportFilename(runName: string | null | undefined, runId: string): string {
  const safeName = (runName || "run")
    .replace(/[\\/:*?"<>|]+/g, "-")
    .replace(/\s+/g, " ")
    .trim() || "run";
  return `${safeName}-${runId.slice(0, 8)}-report.html`;
}
