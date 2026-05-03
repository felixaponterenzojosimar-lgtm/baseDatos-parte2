export interface QueryResult {
  columns: string[];
  rows: Record<string, unknown>[];
  row_count: number;
  reads: number;
  writes: number;
  time_ms: number;
  message: string | null;
}

export interface ColumnSchema {
  name: string;
  type: string;
}

export interface TableInfo {
  name: string;
  columns: ColumnSchema[];
  index_type: "sequential" | "isam" | "bplus" | "hash" | "rtree";
  data_file: string;
}

export interface TableListResponse {
  tables: TableInfo[];
  count: number;
}

export interface RTreePoint {
  x: number;
  y: number;
  record: Record<string, unknown>;
}

export interface RTreePointsResponse {
  table: string;
  points: RTreePoint[];
  count: number;
}

export interface MetricsEntry {
  operation: string;
  table: string;
  reads: number;
  writes: number;
  total_io: number;
  time_ms: number;
  row_count: number;
}

export interface ApiError {
  error: string;
  message: string;
}
