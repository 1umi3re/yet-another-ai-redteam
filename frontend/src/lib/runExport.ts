export type RunExportFormat = "json" | "csv";

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
