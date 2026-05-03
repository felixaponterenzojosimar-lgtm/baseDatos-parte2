import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Play, RotateCcw } from "lucide-react";

interface Step {
  op: string;
  tid: number;
  result: "granted" | "blocked" | "committed" | "aborted" | "deadlock" | "skipped";
  message: string;
  lock_table: Record<string, { mode: string; holders: number[] }>;
  waiting: Record<string, { item: string; mode: string }>;
}

interface Summary {
  committed: number[];
  aborted: number[];
  active: number[];
  waiting: number[];
}

interface SimResult {
  steps: Step[];
  summary: Summary;
}

const RESULT_STYLES: Record<string, string> = {
  granted:   "bg-green-900/40 text-green-300 border-green-700/50",
  committed: "bg-blue-900/40 text-blue-300 border-blue-700/50",
  blocked:   "bg-yellow-900/40 text-yellow-300 border-yellow-700/50",
  deadlock:  "bg-red-900/40 text-red-300 border-red-700/50",
  aborted:   "bg-red-900/30 text-red-400 border-red-800/40",
  skipped:   "bg-slate-800 text-slate-500 border-slate-700",
};

const TX_COLORS = [
  "text-blue-400", "text-emerald-400", "text-purple-400",
  "text-orange-400", "text-pink-400", "text-cyan-400",
];

const EXAMPLES = [
  { label: "Sin conflicto", value: "R1(A) R2(A) W1(B) W2(C) C1 C2" },
  { label: "Conflicto W-R", value: "W1(A) R2(A) C1 C2" },
  { label: "Deadlock", value: "R1(A) R2(B) W1(B) W2(A) C1 C2" },
  { label: "Upgrade lock", value: "R1(A) R2(A) W1(A) C1 C2" },
];

function txColor(tid: number) {
  return TX_COLORS[(tid - 1) % TX_COLORS.length];
}

export function ConcurrencySimulator() {
  const [schedule, setSchedule] = useState("R1(A) R2(B) W1(B) W2(A) C1 C2");
  const [result, setResult] = useState<SimResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [expandedStep, setExpandedStep] = useState<number | null>(null);

  async function run() {
    setLoading(true);
    setError(null);
    setResult(null);
    setExpandedStep(null);
    try {
      const base = (import.meta.env.VITE_API_URL as string | undefined) ?? "/api/v1";
      const res = await fetch(`${base}/concurrency/simulate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ schedule }),
      });
      const body = await res.json();
      if (!res.ok) throw new Error(body?.detail ?? `HTTP ${res.status}`);
      setResult(body);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="p-5 space-y-4 max-w-4xl mx-auto">
      {/* Header */}
      <div>
        <h2 className="text-slate-200 font-semibold text-sm">Simulador de Concurrencia — 2PL Estricto</h2>
        <p className="text-slate-500 text-xs mt-0.5">
          Ingresa un schedule: <code className="text-slate-400">R1(A)</code> lee, <code className="text-slate-400">W2(B)</code> escribe,{" "}
          <code className="text-slate-400">C1</code> commit, <code className="text-slate-400">A2</code> abort
        </p>
      </div>

      {/* Examples */}
      <div className="flex gap-2 flex-wrap">
        {EXAMPLES.map((ex) => (
          <button
            key={ex.label}
            onClick={() => { setSchedule(ex.value); setResult(null); setError(null); }}
            className="px-2.5 py-1 text-xs rounded border border-slate-600 text-slate-400 hover:text-slate-200 hover:border-slate-400 transition-colors"
          >
            {ex.label}
          </button>
        ))}
      </div>

      {/* Input */}
      <div className="space-y-2">
        <textarea
          value={schedule}
          onChange={(e) => setSchedule(e.target.value)}
          rows={3}
          className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm font-mono text-slate-100 focus:outline-none focus:border-blue-500 resize-none"
          placeholder="R1(A) W2(A) C1 C2"
        />
        <div className="flex gap-2">
          <button
            onClick={run}
            disabled={loading}
            className="flex items-center gap-1.5 px-4 py-1.5 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 rounded-lg text-sm font-medium transition-colors"
          >
            {loading
              ? <span className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              : <Play size={13} />}
            {loading ? "Simulando..." : "Simular"}
          </button>
          {result && (
            <button
              onClick={() => { setResult(null); setError(null); }}
              className="flex items-center gap-1.5 px-3 py-1.5 border border-slate-600 text-slate-400 hover:text-slate-200 rounded-lg text-sm transition-colors"
            >
              <RotateCcw size={13} /> Limpiar
            </button>
          )}
        </div>
      </div>

      {/* Error */}
      {error && (
        <p className="text-red-400 text-sm bg-red-900/20 border border-red-800/50 rounded-lg px-3 py-2">{error}</p>
      )}

      {/* Result */}
      <AnimatePresence>
        {result && (
          <motion.div
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            className="space-y-4"
          >
            {/* Summary chips */}
            <div className="flex gap-2 flex-wrap">
              {result.summary.committed.length > 0 && (
                <span className="px-2.5 py-1 bg-blue-900/40 border border-blue-700/50 text-blue-300 text-xs rounded-full">
                  ✓ Commit: {result.summary.committed.map((t) => `T${t}`).join(", ")}
                </span>
              )}
              {result.summary.aborted.length > 0 && (
                <span className="px-2.5 py-1 bg-red-900/40 border border-red-700/50 text-red-300 text-xs rounded-full">
                  ✗ Abort: {result.summary.aborted.map((t) => `T${t}`).join(", ")}
                </span>
              )}
              {result.summary.waiting.length > 0 && (
                <span className="px-2.5 py-1 bg-yellow-900/40 border border-yellow-700/50 text-yellow-300 text-xs rounded-full">
                  ⏳ Bloqueado: {result.summary.waiting.map((t) => `T${t}`).join(", ")}
                </span>
              )}
            </div>

            {/* Steps table */}
            <div className="border border-slate-700 rounded-lg overflow-hidden">
              <table className="w-full text-xs">
                <thead>
                  <tr className="bg-slate-800 text-slate-400">
                    <th className="px-3 py-2 text-left w-8">#</th>
                    <th className="px-3 py-2 text-left w-24">Operación</th>
                    <th className="px-3 py-2 text-left w-24">Estado</th>
                    <th className="px-3 py-2 text-left">Mensaje</th>
                    <th className="px-3 py-2 text-left w-16">Locks</th>
                  </tr>
                </thead>
                <tbody>
                  {result.steps.map((step, i) => (
                    <>
                      <tr
                        key={i}
                        onClick={() => setExpandedStep(expandedStep === i ? null : i)}
                        className={`border-t border-slate-800 cursor-pointer hover:bg-slate-800/40 transition-colors`}
                      >
                        <td className="px-3 py-2 text-slate-500">{i + 1}</td>
                        <td className={`px-3 py-2 font-mono font-bold ${txColor(step.tid)}`}>
                          {step.op}
                        </td>
                        <td className="px-3 py-2">
                          <span className={`px-2 py-0.5 rounded border text-[10px] font-medium ${RESULT_STYLES[step.result]}`}>
                            {step.result}
                          </span>
                        </td>
                        <td className="px-3 py-2 text-slate-300">{step.message}</td>
                        <td className="px-3 py-2 text-slate-500 text-center">
                          {Object.keys(step.lock_table).length > 0 ? (
                            <span className="text-slate-400">{Object.keys(step.lock_table).length}</span>
                          ) : "—"}
                        </td>
                      </tr>
                      {/* Expanded lock table */}
                      {expandedStep === i && Object.keys(step.lock_table).length > 0 && (
                        <tr key={`exp-${i}`} className="bg-slate-900/60">
                          <td colSpan={5} className="px-4 py-3">
                            <p className="text-slate-500 text-[10px] mb-1.5 uppercase tracking-wide">Tabla de locks</p>
                            <div className="flex gap-2 flex-wrap">
                              {Object.entries(step.lock_table).map(([item, lock]) => (
                                <div key={item} className="bg-slate-800 border border-slate-700 rounded px-2.5 py-1.5">
                                  <span className="text-slate-300 font-mono font-bold">{item}</span>
                                  <span className={`ml-1.5 text-[10px] font-bold ${lock.mode === "X" ? "text-red-400" : "text-green-400"}`}>
                                    {lock.mode}
                                  </span>
                                  <span className="text-slate-500 ml-1.5">
                                    {lock.holders.map((t) => `T${t}`).join(",")}
                                  </span>
                                </div>
                              ))}
                            </div>
                            {Object.keys(step.waiting).length > 0 && (
                              <div className="mt-2 flex gap-2 flex-wrap">
                                <p className="text-slate-500 text-[10px] w-full uppercase tracking-wide">Esperando</p>
                                {Object.entries(step.waiting).map(([tid, w]) => (
                                  <div key={tid} className="bg-yellow-900/20 border border-yellow-800/40 rounded px-2 py-1 text-[10px]">
                                    <span className={txColor(Number(tid))}>T{tid}</span>
                                    <span className="text-slate-400 ml-1">→ {w.mode} en {w.item}</span>
                                  </div>
                                ))}
                              </div>
                            )}
                          </td>
                        </tr>
                      )}
                    </>
                  ))}
                </tbody>
              </table>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
