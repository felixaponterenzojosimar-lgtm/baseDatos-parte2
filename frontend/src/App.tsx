import { AnimatePresence, motion } from "framer-motion";
import { Database, MapPin, Upload, GitBranch, Image as ImageIcon, Music, FolderInput, Terminal, ChevronDown, FlaskConical, TableProperties, History } from "lucide-react";
import { useState } from "react";
import { ConcurrencySimulator } from "./components/ConcurrencySimulator";
import { CsvUploadModal } from "./components/CsvUploadModal";
import { DataLoader } from "./components/DataLoader";
import { ExperimentRunner } from "./components/ExperimentRunner";
import { MetricsHistory } from "./components/MetricsHistory";
import { MusicSearch } from "./components/MusicSearch";
import { ResultsTable } from "./components/ResultsTable";
import { RTreeVisualization } from "./components/RTreeVisualization";
import { Sidebar } from "./components/Sidebar";
import { SqlEditor } from "./components/SqlEditor";
import { StatsPanel } from "./components/StatsPanel";
import { VisualSearch } from "./components/VisualSearch";
import { useQuery } from "./hooks/useQuery";
import { useTables } from "./hooks/useTables";
import type { TableInfo } from "./types/api";

type Tab = "datos" | "visual" | "musical" | "experimentos" | "results" | "rtree" | "history" | "concurrency";

const EXAMPLE_QUERIES = [
  `CREATE TABLE cancion (id INT PRIMARY KEY USING BPLUS TREE, genero CHAR(20), pista AUDIO);`,
  `CREATE INDEX ix_pista ON cancion (pista) USING MULTIMEDIA;`,
  `SELECT * FROM cancion WHERE pista <-> 'consulta.wav' LIMIT 10;`,
  `SELECT * FROM docs WHERE cuerpo @@ 'machine learning' LIMIT 10;`,
];

export default function App() {
  const [sql, setSql] = useState("");
  const [tab, setTab] = useState<Tab>("musical");
  const [termOpen, setTermOpen] = useState(true);
  const [rtreeTable, setRtreeTable] = useState<string | null>(null);
  const [selectedTable, setSelectedTable] = useState<string | null>(null);
  const [csvModalOpen, setCsvModalOpen] = useState(false);

  const { result, error, loading, execute } = useQuery();
  const { tables, loading: tablesLoading, refresh, drop: dropTable } = useTables();

  async function drop(name: string) {
    await dropTable(name);
    if (rtreeTable === name) setRtreeTable(null);
    if (selectedTable === name) setSelectedTable(null);
  }

  async function runQuery() {
    const res = await execute(sql);
    await refresh();
    if (res?.spatial_meta) {
      const match = sql.match(/\bFROM\s+(\w+)\b/i);
      if (match) setRtreeTable(match[1]);
      setTab("rtree");
    } else {
      setTab("results");
    }
  }

  function handleSelectTable(t: TableInfo) {
    setSelectedTable(t.name);
    setSql(`SELECT * FROM ${t.name};`);
    if (t.spatial_indexes?.length > 0) setRtreeTable(t.name);
    setTab("results");
  }

  function handleShowRTree(name: string) {
    setRtreeTable(name);
    setTab("rtree");
  }

  const tabs: { key: Tab; label: React.ReactNode }[] = [
    { key: "datos",        label: <span className="flex items-center gap-1.5"><FolderInput size={13} />Datos</span> },
    { key: "visual",       label: <span className="flex items-center gap-1.5"><ImageIcon size={13} />Visual</span> },
    { key: "musical",      label: <span className="flex items-center gap-1.5"><Music size={13} />Musical</span> },
    { key: "experimentos", label: <span className="flex items-center gap-1.5"><FlaskConical size={13} />Experimentos</span> },
    { key: "results",      label: <span className="flex items-center gap-1.5"><TableProperties size={13} />Resultados{result ? <span className="ml-0.5 bg-blue-600 text-white text-[10px] font-bold px-1.5 py-px rounded-full">{result.row_count}</span> : null}</span> },
    { key: "rtree",        label: <span className="flex items-center gap-1.5"><MapPin size={13} />R-Tree</span> },
    { key: "history",      label: <span className="flex items-center gap-1.5"><History size={13} />Historial</span> },
    { key: "concurrency",  label: <span className="flex items-center gap-1.5"><GitBranch size={13} />Concurrencia</span> },
  ];

  return (
    <div className="grid h-screen overflow-hidden bg-slate-900 text-slate-100" style={{ gridTemplateColumns: "220px 1fr" }}>
      <CsvUploadModal open={csvModalOpen} onClose={() => setCsvModalOpen(false)} onSuccess={refresh} />

      <Sidebar
        tables={tables}
        loading={tablesLoading}
        onRefresh={refresh}
        onDrop={drop}
        onSelectTable={handleSelectTable}
        selectedTable={selectedTable}
        onShowRTree={handleShowRTree}
      />

      <main className="flex flex-col overflow-hidden">
        <header className="flex items-center justify-between px-4 py-2.5 bg-slate-800 border-b border-slate-700 shrink-0">
          <div className="flex items-center gap-2 font-bold text-[15px] tracking-wide">
            <Database size={18} className="text-blue-500" />
            Multimodal DB — recuperación por contenido
          </div>
          <button onClick={() => setCsvModalOpen(true)}
            className="flex items-center gap-1.5 px-3 py-1 text-xs rounded border border-blue-600 text-blue-400 hover:bg-blue-600 hover:text-white transition-colors">
            <Upload size={12} /> Import CSV
          </button>
        </header>

        {/* Un solo tab bar con TODO al mismo nivel */}
        <div className="flex flex-wrap bg-slate-800 border-b border-slate-700 shrink-0">
          {tabs.map(({ key, label }) => (
            <button key={key} onClick={() => setTab(key)}
              className={`relative px-3.5 py-2 text-sm transition-colors ${tab === key ? "text-blue-400" : "text-slate-400 hover:text-slate-200"}`}>
              {label}
              {tab === key && <motion.div layoutId="tab-ind" className="absolute bottom-0 left-0 right-0 h-0.5 bg-blue-500" />}
            </button>
          ))}
        </div>

        {/* Contenido */}
        <div className="flex-1 overflow-auto relative">
          <AnimatePresence mode="wait">
            <motion.div key={tab} initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -6 }} transition={{ duration: 0.18 }} className="absolute inset-0 overflow-auto">
              {tab === "datos" && <DataLoader tables={tables} onChanged={refresh} />}
              {tab === "visual" && <VisualSearch tables={tables} />}
              {tab === "musical" && <MusicSearch tables={tables} />}
              {tab === "experimentos" && <ExperimentRunner tables={tables} />}
              {tab === "results" && (<><StatsPanel result={result} error={error} /><ResultsTable columns={result?.columns ?? []} rows={result?.rows ?? []} /></>)}
              {tab === "rtree" && (rtreeTable
                ? <RTreeVisualization table={rtreeTable} queryRows={result?.spatial_meta ? result.rows : null} spatialMeta={result?.spatial_meta} />
                : <p className="p-8 text-center text-slate-500 text-sm">Selecciona una tabla espacial en la barra lateral y pulsa Visualizar.</p>)}
              {tab === "history" && <MetricsHistory />}
              {tab === "concurrency" && <ConcurrencySimulator />}
            </motion.div>
          </AnimatePresence>
        </div>

        {/* Terminal SQL (editor) abajo, colapsable */}
        <div className="shrink-0 border-t border-slate-700 bg-slate-800">
          <div className="flex items-center px-3 py-1.5 border-b border-slate-700/60">
            <button onClick={() => setTermOpen(o => !o)} className="flex items-center gap-1.5 text-xs font-semibold text-slate-300 hover:text-white">
              <Terminal size={13} className="text-blue-500" /> Terminal SQL
              <ChevronDown size={13} className={`transition-transform ${termOpen ? "" : "-rotate-90"}`} />
            </button>
            <div className="flex gap-1 ml-3 flex-wrap">
              {EXAMPLE_QUERIES.map((q, i) => (
                <button key={i} onClick={() => { setSql(q); setTermOpen(true); }} title={q}
                  className="px-2 py-0.5 text-[11px] rounded border border-slate-600 text-slate-400 hover:text-slate-100 hover:border-slate-400">
                  Ej {i + 1}
                </button>
              ))}
            </div>
          </div>
          {termOpen && <SqlEditor value={sql} onChange={setSql} onRun={runQuery} loading={loading} />}
        </div>
      </main>
    </div>
  );
}
