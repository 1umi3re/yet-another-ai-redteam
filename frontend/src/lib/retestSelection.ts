export function buildRetestPath(targetId: string, sourceRunIds: string[]): string {
  const params = new URLSearchParams({ target: targetId });
  for (const runId of sourceRunIds) params.append("run", runId);
  return `/runs/retest?${params.toString()}`;
}
