export interface SpatialMeta {
  type: "radius" | "knn";
  point: [number, number];
  radius?: number;
  k?: number;
  lat_col: string | null;
  lon_col: string | null;
}

export interface QueryResult {
  columns: string[];
  rows: Record<string, unknown>[];
  row_count: number;
  reads: number;
  writes: number;
  time_ms: number;
  message: string | null;
  spatial_meta?: SpatialMeta | null;
}

export interface ColumnSchema {
  name: string;
  type: string;
}

export interface IndexInfo {
  name: string;
  type: string;
  columns: string[];
}

export interface TableInfo {
  name: string;
  columns: ColumnSchema[];
  primary_key: string;
  primary_index_type: string;
  data_file: string;
  secondary_indexes: IndexInfo[];
  spatial_indexes: IndexInfo[];
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
