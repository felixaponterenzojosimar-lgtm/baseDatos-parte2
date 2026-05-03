from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from collections import deque

from ..engine import Database, Executor
from ..parser import Parser, ParseError
from ..parser.semantic_analyzer import SemanticError
from ..engine.executor import ExecutionError
from ..indexes import SequentialFile, ExtendibleHashing, BPlusTree, RTree
from ..parser.ast_nodes import (
    CreateTableNode, InsertNode, SelectEqualNode, SelectComparisonNode,
    SelectRangeNode, SelectPointRadiusNode, SelectKNNNode, DeleteNode,
)

app = FastAPI(title="Mini-SGBD API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

db = Database()
executor = Executor(db)
_metrics_history: deque = deque(maxlen=1000)

# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

_NODE_OP = {
    CreateTableNode:       "CREATE TABLE",
    InsertNode:            "INSERT",
    SelectEqualNode:       "SELECT",
    SelectComparisonNode:  "SELECT",
    SelectRangeNode:       "SELECT RANGE",
    SelectPointRadiusNode: "SELECT RADIUS",
    SelectKNNNode:         "SELECT KNN",
    DeleteNode:            "DELETE",
}


def _index_type_name(index) -> str:
    if isinstance(index, SequentialFile):   return "sequential"
    if isinstance(index, ExtendibleHashing): return "hash"
    if isinstance(index, BPlusTree):         return "bplus"
    if isinstance(index, RTree):             return "rtree"
    return "unknown"


def _table_name_from(node) -> str:
    return getattr(node, "table_name", "")


# ------------------------------------------------------------------
# Schemas
# ------------------------------------------------------------------

class QueryRequest(BaseModel):
    sql: str


# ------------------------------------------------------------------
# Endpoints
# ------------------------------------------------------------------

@app.post("/api/v1/query")
def run_query(req: QueryRequest):
    try:
        node = Parser(req.sql).parse()
    except (ParseError, SemanticError) as e:
        raise HTTPException(status_code=400, detail=str(e))

    try:
        result = executor.execute(node)
    except ExecutionError as e:
        raise HTTPException(status_code=422, detail=str(e))

    rows: list[dict] = result["results"]
    stats: dict = result["stats"]
    columns = list(rows[0].keys()) if rows else []

    # Mensaje para operaciones que no retornan filas
    message = None
    node_type = type(node)
    if node_type in (CreateTableNode, InsertNode):
        message = f"{_NODE_OP[node_type]} ejecutado correctamente"
    elif node_type == DeleteNode:
        deleted = rows[0]["deleted"] if rows else False
        message = "Registro eliminado" if deleted else "Registro no encontrado"
        rows = []

    op_name = _NODE_OP.get(node_type, "UNKNOWN")
    table = _table_name_from(node)
    _metrics_history.append({
        "operation": op_name,
        "table":     table,
        "reads":     stats["reads"],
        "writes":    stats["writes"],
        "total_io":  stats["reads"] + stats["writes"],
        "time_ms":   stats["time_ms"],
        "row_count": len(rows),
    })

    return {
        "columns":   columns,
        "rows":      rows,
        "row_count": len(rows),
        "reads":     stats["reads"],
        "writes":    stats["writes"],
        "time_ms":   stats["time_ms"],
        "message":   message,
    }


@app.get("/api/v1/tables")
def list_tables():
    tables = []
    for name in db.list_tables():
        table = db.get_table(name)
        columns = [
            {"name": f.name, "type": f.field_type.value}
            for f in table.schema.fields
        ]
        tables.append({
            "name":       name,
            "columns":    columns,
            "index_type": _index_type_name(table.index),
            "data_file":  table.index.pm.filepath,
        })
    return {"tables": tables, "count": len(tables)}


@app.delete("/api/v1/tables/{name}")
def drop_table(name: str):
    try:
        db.drop_table(name)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {"message": f"Tabla '{name}' eliminada", "table": name}


@app.get("/api/v1/indexes/{table}/points")
def get_rtree_points(table: str):
    try:
        t = db.get_table(table)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    if not isinstance(t.index, RTree):
        raise HTTPException(status_code=400, detail=f"'{table}' no usa índice RTree")
    raw = t.index.all_points()
    points = [{"x": p["lon"], "y": p["lat"], "record": p["record"]} for p in raw]
    return {"table": table, "points": points, "count": len(points)}


@app.get("/api/v1/metrics/history")
def metrics_history(limit: int = 50):
    entries = list(_metrics_history)[-limit:]
    return {"entries": entries, "count": len(entries)}


@app.delete("/api/v1/metrics")
def clear_metrics():
    _metrics_history.clear()
    return {"message": "Historial de métricas limpiado"}
