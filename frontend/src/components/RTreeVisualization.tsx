import { useEffect, useState } from "react";
import {
  CartesianGrid, Legend, ReferenceDot, ResponsiveContainer, Scatter,
  ScatterChart, Tooltip, XAxis, YAxis, ZAxis,
} from "recharts";
import { api } from "../api/client";
import type { RTreePoint, SpatialMeta } from "../types/api";

interface Props {
  table: string;
  queryRows?: Record<string, unknown>[] | null;
  spatialMeta?: SpatialMeta | null;
}

function CustomTooltip({ active, payload }: { active?: boolean; payload?: { payload: RTreePoint }[] }) {
  if (!active || !payload?.length) return null;
  const pt = payload[0].payload;
  return (
    <div className="rtree-tooltip">
      <p><strong>x:</strong> {pt.x}</p>
      <p><strong>y:</strong> {pt.y}</p>
      {Object.entries(pt.record).slice(0, 4).map(([k, v]) => (
        <p key={k}><strong>{k}:</strong> {String(v)}</p>
      ))}
    </div>
  );
}

function QueryMetaBanner({ meta }: { meta: SpatialMeta }) {
  const [cx, cy] = meta.point;
  if (meta.type === "radius") {
    return (
      <div className="flex items-center gap-3 px-3 py-2 mb-3 rounded bg-violet-900/30 border border-violet-700/40 text-xs text-violet-300">
        <span className="font-semibold text-violet-200">RADIO</span>
        <span>Centro: ({cx}, {cy})</span>
        <span>Radio: <strong>{meta.radius}</strong></span>
        <span className="text-violet-400 ml-auto">Mostrando solo resultados de la consulta</span>
      </div>
    );
  }
  return (
    <div className="flex items-center gap-3 px-3 py-2 mb-3 rounded bg-blue-900/30 border border-blue-700/40 text-xs text-blue-300">
      <span className="font-semibold text-blue-200">KNN</span>
      <span>Centro: ({cx}, {cy})</span>
      <span>k = <strong>{meta.k}</strong></span>
      <span className="text-blue-400 ml-auto">Mostrando solo resultados de la consulta</span>
    </div>
  );
}

export function RTreeVisualization({ table, queryRows, spatialMeta }: Props) {
  const [allPoints, setAllPoints] = useState<RTreePoint[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const isQueryMode = !!(spatialMeta && queryRows);

  useEffect(() => {
    if (isQueryMode) return;
    if (!table) return;
    setLoading(true);
    setError(null);
    api.getRTreePoints(table)
      .then((res) => setAllPoints(res.points))
      .catch((e) => setError(e instanceof Error ? e.message : "Failed to load points"))
      .finally(() => setLoading(false));
  }, [table, isQueryMode]);

  if (!isQueryMode) {
    if (loading) return <p className="p-8 text-center text-slate-500 text-sm">Loading spatial data…</p>;
    if (error)   return <p className="p-8 text-center text-red-400 text-sm">{error}</p>;
    if (!allPoints.length) return <p className="p-8 text-center text-slate-500 text-sm">No spatial records in table "{table}".</p>;
  }

  if (isQueryMode) {
    const latCol = spatialMeta.lat_col;
    const lonCol = spatialMeta.lon_col;
    if (!latCol || !lonCol) {
      return <p className="p-8 text-center text-slate-500 text-sm">No se pudo determinar las columnas espaciales del resultado.</p>;
    }

    const resultPoints: RTreePoint[] = (queryRows ?? []).map((row) => ({
      x: row[lonCol] as number,
      y: row[latCol] as number,
      record: row,
    }));

    if (!resultPoints.length) {
      return (
        <div className="p-4">
          <QueryMetaBanner meta={spatialMeta} />
          <p className="text-center text-slate-500 text-sm py-8">La consulta no retornó resultados espaciales.</p>
        </div>
      );
    }

    const [cx, cy] = spatialMeta.point;

    return (
      <div className="p-4">
        <QueryMetaBanner meta={spatialMeta} />
        <p className="text-xs text-slate-400 mb-3">
          R-Tree — <span className="text-emerald-400 font-medium">{resultPoints.length} resultado{resultPoints.length !== 1 ? "s" : ""}</span>
          {" · "}tabla: <span className="text-blue-400">{table}</span>
        </p>
        <ResponsiveContainer width="100%" height={360}>
          <ScatterChart margin={{ top: 16, right: 24, bottom: 24, left: 8 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
            <XAxis dataKey="x" type="number" name={lonCol}
              tick={{ fill: "#94a3b8", fontSize: 12 }}
              label={{ value: lonCol, position: "insideBottom", offset: -10, fill: "#94a3b8" }}
            />
            <YAxis dataKey="y" type="number" name={latCol}
              tick={{ fill: "#94a3b8", fontSize: 12 }}
              label={{ value: latCol, angle: -90, position: "insideLeft", fill: "#94a3b8" }}
            />
            <ZAxis range={[28, 28]} />
            <Tooltip content={<CustomTooltip />} cursor={{ strokeDasharray: "3 3" }} />
            <Legend wrapperStyle={{ fontSize: 12, color: "#94a3b8" }} />
            <ReferenceDot
              x={cx}
              y={cy}
              r={10}
              fill="#f97316"
              stroke="#fed7aa"
              strokeWidth={2}
              label={{ value: "●", fill: "#fed7aa", fontSize: 10 }}
            />
            <Scatter
              name="Resultados"
              data={resultPoints}
              fill="#10b981"
              fillOpacity={0.85}
              stroke="#6ee7b7"
              strokeWidth={1}
            />
          </ScatterChart>
        </ResponsiveContainer>
        <p className="text-xs text-slate-500 mt-2">
          <span className="inline-block w-2.5 h-2.5 rounded-full bg-orange-500 mr-1 align-middle" />
          Punto de consulta ·
          <span className="inline-block w-2.5 h-2.5 rounded-full bg-emerald-500 mx-1 align-middle" />
          Resultados
        </p>
      </div>
    );
  }

  return (
    <div className="p-4">
      <p className="text-xs text-slate-400 mb-3">
        R-Tree — <span className="text-slate-300 font-medium">{allPoints.length} points</span>
        {" · "}tabla: <span className="text-blue-400">{table}</span>
      </p>
      <ResponsiveContainer width="100%" height={360}>
        <ScatterChart margin={{ top: 16, right: 24, bottom: 24, left: 8 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
          <XAxis dataKey="x" type="number" name="x"
            tick={{ fill: "#94a3b8", fontSize: 12 }}
            label={{ value: "x", position: "insideBottom", offset: -10, fill: "#94a3b8" }}
          />
          <YAxis dataKey="y" type="number" name="y"
            tick={{ fill: "#94a3b8", fontSize: 12 }}
            label={{ value: "y", angle: -90, position: "insideLeft", fill: "#94a3b8" }}
          />
          <ZAxis range={[24, 24]} />
          <Tooltip content={<CustomTooltip />} cursor={{ strokeDasharray: "3 3" }} />
          <Scatter data={allPoints} fill="#3b82f6" fillOpacity={0.8} stroke="#60a5fa" strokeWidth={1} />
        </ScatterChart>
      </ResponsiveContainer>
    </div>
  );
}
