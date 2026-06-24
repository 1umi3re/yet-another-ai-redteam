export function buildPageWindow({
  page,
  pageCount,
  windowSize = 5,
}: {
  page: number;
  pageCount: number;
  windowSize?: number;
}): number[] {
  if (pageCount <= 0) return [];
  const size = Math.max(1, Math.min(windowSize, pageCount));
  const current = Math.min(Math.max(page, 0), pageCount - 1);
  let start = Math.max(0, current - Math.floor(size / 2));
  start = Math.min(start, pageCount - size);
  return Array.from({ length: size }, (_, idx) => start + idx + 1);
}

export function formatPaginationRange({
  total,
  offset,
  limit,
}: {
  total: number;
  offset: number;
  limit: number;
}): string {
  if (total <= 0) return "0-0 of 0";
  const start = Math.min(offset + 1, total);
  const end = Math.min(offset + limit, total);
  return `${start}-${end} of ${total}`;
}
