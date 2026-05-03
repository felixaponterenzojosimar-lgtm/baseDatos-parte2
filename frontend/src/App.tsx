import { AnimatePresence, motion } from "framer-motion";
import { Database, MapPin } from "lucide-react";
import { useState } from "react";
import { MetricsHistory } from "./components/MetricsHistory";
import { ResultsTable } from "./components/ResultsTable";
import { RTreeVisualization } from "./components/RTreeVisualization";
import { Sidebar } from "./components/Sidebar";
import { SqlEditor } from "./components/SqlEditor";
import { StatsPanel } from "./components/StatsPanel";
import { useQuery } from "./hooks/useQuery";
import { useTables } from "./hooks/useTables";
import type { TableInfo } from "./types/api";

type Tab = "results" | "rtree" | "history";

const EXAMPLE_QUERIES = [
  `CREATE TABLE employees (\n  id INT,\n  name VARCHAR,\n  salary FLOAT\n) USING INDEX bplus;`,
  `INSERT INTO employees VALUES (1, 'Alice', 4500.0);`,
  `SELECT * FROM employees WHERE salary BETWEEN 3000 AND 6000;`,
  `SELECT * FROM employees WHERE id = 1;`,
  `DELETE FROM employees WHERE id = 1;`,
];

const tabVariants = {
  initial: { opacity: 0, y: 6 },
  animate: { opacity: 1, y: 0 },
  exit:    { opacity: 0, y: -6 },
};

export default function App() {
  const [sql, setSql] = useState(EXAMPLE_QUERIES[0]);
  const [activeTab, setActiveTab] = useState<Tab>("results");
  const [rtreeTable, setRtreeTable] = useState<string | null>(null);
  const [selectedTable, setSelectedTable] = useState<string | null>(null);

  const { result, error, loading, execute } = useQuery();
  const { tables, loading: tablesLoading, refresh, drop } = useTables();

  async function runQuery() {
    await execute(sql);
    await refresh();
    setActiveTab("results");
  }

  function handleSelectTable(t: TableInfo) {
    setSelectedTable(t.name);
    setSql(`SELECT * FROM ${t.name};`);
  }

  function handleShowRTree(name: string) {
    setRtreeTable(name);
    setActiveTab("rtree");
  }

  const tabs: { key: Tab; label: React.ReactNode }[] = [
    {
      key: "results",
      label: (
        <>
          Results
          <AnimatePresence>
            {result && (
              <motion.span
                initial={{ scale: 0.6, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                exit={{ scale: 0.6, opacity: 0 }}
                className="ml-1.5 bg-blue-600 text-white text-[10px] font-bold px-1.5 py-px rounded-full"
              >
                {result.row_count}
              </motion.span>
            )}
          </AnimatePresence>
        </>
      ),
    },
    { key: "rtree",   label: <span className="flex items-center gap-1.5"><MapPin size={12} />R-Tree</span> },
    { key: "history", label: "History" },
  ];

  return (
    <div className="grid h-screen overflow-hidden bg-slate-900 text-slate-100" style={{ gridTemplateColumns: "220px 1fr" }}>

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

        {/* Header */}
        <motion.header
          initial={{ opacity: 0, y: -8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
          className="flex items-center justify-between px-4 py-2.5 bg-slate-800 border-b border-slate-700 shrink-0"
        >
          <div className="flex items-center gap-2 font-bold text-[15px] tracking-wide">
            <Database size={18} className="text-blue-500" />
            DB Manager Simulator
          </div>
          <div className="flex gap-1.5">
            {EXAMPLE_QUERIES.map((q, i) => (
              <motion.button
                key={i}
                whileHover={{ scale: 1.04 }}
                whileTap={{ scale: 0.96 }}
                onClick={() => setSql(q)}
                title={q}
                className="px-2.5 py-1 text-xs rounded border border-slate-600 text-slate-400 hover:text-slate-100 hover:border-slate-400 transition-colors"
              >
                Ex {i + 1}
              </motion.button>
            ))}
          </div>
        </motion.header>

        {/* Editor */}
        <SqlEditor value={sql} onChange={setSql} onRun={runQuery} loading={loading} />

        {/* Stats */}
        <StatsPanel result={result} error={error} />

        {/* Tab bar */}
        <div className="flex bg-slate-800 border-b border-slate-700 shrink-0">
          {tabs.map(({ key, label }) => (
            <button
              key={key}
              onClick={() => setActiveTab(key)}
              className={`relative flex items-center gap-1.5 px-4 py-2 text-sm transition-colors ${
                activeTab === key ? "text-blue-400" : "text-slate-400 hover:text-slate-200"
              }`}
            >
              {label}
              {activeTab === key && (
                <motion.div
                  layoutId="tab-indicator"
                  className="absolute bottom-0 left-0 right-0 h-0.5 bg-blue-500"
                  transition={{ type: "spring", stiffness: 500, damping: 35 }}
                />
              )}
            </button>
          ))}
        </div>

        {/* Tab content */}
        <div className="flex-1 overflow-auto relative">
          <AnimatePresence mode="wait">
            <motion.div
              key={activeTab}
              variants={tabVariants}
              initial="initial"
              animate="animate"
              exit="exit"
              transition={{ duration: 0.18 }}
              className="absolute inset-0 overflow-auto"
            >
              {activeTab === "results" && (
                <ResultsTable columns={result?.columns ?? []} rows={result?.rows ?? []} />
              )}
              {activeTab === "rtree" && (
                rtreeTable
                  ? <RTreeVisualization table={rtreeTable} />
                  : <p className="p-8 text-center text-slate-500 text-sm">Select an R-Tree table from the sidebar and click Visualize.</p>
              )}
              {activeTab === "history" && <MetricsHistory />}
            </motion.div>
          </AnimatePresence>
        </div>

      </main>
    </div>
  );
}
