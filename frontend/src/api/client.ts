import type {
  MetricsEntry,
  QueryResult,
  RTreePointsResponse,
  TableListResponse,
} from "../types/api";

const BASE = import.meta.env.VITE_API_URL ?? "/api/v1";

async function request<T>(
  path: string,
  options?: RequestInit
): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    const detail = body?.detail ?? body;
    const msg =
      typeof detail === "object"
        ? detail?.message ?? JSON.stringify(detail)
        : String(detail);
    throw new Error(msg || `HTTP ${res.status}`);
  }

  return res.json() as Promise<T>;
}

export const api = {
  executeQuery: (sql: string) =>
    request<QueryResult>("/query", {
      method: "POST",
      body: JSON.stringify({ sql }),
    }),

  listTables: () => request<TableListResponse>("/tables"),

  dropTable: (name: string) =>
    request<{ message: string; table: string }>(`/tables/${name}`, {
      method: "DELETE",
    }),

  getRTreePoints: (table: string) =>
    request<RTreePointsResponse>(`/indexes/${table}/points`),

  getMetricsHistory: (limit = 50) =>
    request<{ entries: MetricsEntry[]; count: number }>(
      `/metrics/history?limit=${limit}`
    ),

  clearMetrics: () =>
    request<{ message: string }>("/metrics", { method: "DELETE" }),
};
