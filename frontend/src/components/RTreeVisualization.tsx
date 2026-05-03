import { useEffect, useState } from "react";
import {
  CartesianGrid, ResponsiveContainer, Scatter,
  ScatterChart, Tooltip, XAxis, YAxis, ZAxis,
} from "recharts";
import { api } from "../api/client";
import type { RTreePoint } from "../types/api";

interface Props { table: string }

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

export function RTreeVisualization({ table }: Props) {
  const [points, setPoints] = useState<RTreePoint[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!table) return;
    setLoading(true);
    setError(null);
    api.getRTreePoints(table)
      .then((res) => setPoints(res.points))
      .catch((e) => setError(e instanceof Error ? e.message : "Failed to load points"))
      .finally(() => setLoading(false));
  }, [table]);

  if (loading) return <p className="p-8 text-center text-slate-500 text-sm">Loading spatial data…</p>;
  if (error)   return <p className="p-8 text-center text-red-400 text-sm">{error}</p>;
  if (!points.length) return <p className="p-8 text-center text-slate-500 text-sm">No spatial records in table "{table}".</p>;

  return (
    <div className="p-4">
      <p className="text-xs text-slate-400 mb-3">
        R-Tree — <span className="text-slate-300 font-medium">{points.length} points</span> · table: <span className="text-blue-400">{table}</span>
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
          <Scatter data={points} fill="#3b82f6" fillOpacity={0.8} stroke="#60a5fa" strokeWidth={1} />
        </ScatterChart>
      </ResponsiveContainer>
    </div>
  );
}
