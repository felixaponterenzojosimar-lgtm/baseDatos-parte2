from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from collections import deque
import json as _json
import os

from ..engine import Database, Executor
from ..concurrency import Scheduler as ConcurrencyScheduler
from ..parser import Parser, ParseError
from ..parser.semantic_analyzer import SemanticError
from ..engine.executor import ExecutionError
from ..indexes import SequentialFile, ExtendibleHashing, BPlusTree, RTree
from ..storage.schema import Field, FieldType, Schema
from ..engine.database import DATA_DIR
from ..parser.ast_nodes import (
    CreateTableNode, CreateIndexNode, InsertNode, SelectAllNode, SelectEqualNode,
    SelectComparisonNode, SelectRangeNode, SelectPointRadiusNode, SelectKNNNode, DeleteNode,
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
    CreateIndexNode:       "CREATE INDEX",
    InsertNode:            "INSERT",
    SelectAllNode:         "SELECT ALL",
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


class ScheduleRequest(BaseModel):
    schedule: str


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
    if node_type in (CreateTableNode, CreateIndexNode, InsertNode):
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
        secondary = {
            col: _index_type_name(idx)
            for col, idx in table.secondary_indexes.items()
        }
        tables.append({
            "name":              name,
            "columns":           columns,
            "index_type":        _index_type_name(table.index),
            "data_file":         table.index.pm.filepath,
            "secondary_indexes": secondary,
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


@app.post("/api/v1/concurrency/simulate")
def simulate_schedule(req: ScheduleRequest):
    try:
        result = ConcurrencyScheduler().simulate(req.schedule)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return result


@app.post("/api/v1/tables/upload")
async def upload_csv_table(
    file: UploadFile = File(...),
    table_name: str = Form(...),
    index_type: str = Form(...),
    fields: str = Form(...),
    secondary_indexes: str = Form(default="[]"),
):
    fields_data = _json.loads(fields)
    sec_indexes_data = _json.loads(secondary_indexes)

    schema_fields = []
    primary_key = fields_data[0]["name"]
    for fd in fields_data:
        if fd.get("primary_key"):
            primary_key = fd["name"]
        ft_str = fd["type"]
        if ft_str == "INT":
            schema_fields.append(Field(fd["name"], FieldType.INT))
        elif ft_str == "REAL":
            schema_fields.append(Field(fd["name"], FieldType.FLOAT))
        elif ft_str == "BOOLEAN":
            schema_fields.append(Field(fd["name"], FieldType.BOOL))
        else:
            schema_fields.append(Field(fd["name"], FieldType.VARCHAR, max_length=int(fd.get("size", 50))))

    try:
        schema = Schema(schema_fields, primary_key)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    os.makedirs(DATA_DIR, exist_ok=True)
    csv_path = os.path.join(DATA_DIR, f"{table_name}.csv")
    content = await file.read()
    with open(csv_path, "wb") as f:
        f.write(content)

    try:
        table = db.create_table(table_name, schema, index_type)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    try:
        count = db._load_csv(table, csv_path)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Error cargando CSV: {e}")

    for si in sec_indexes_data:
        try:
            db.add_secondary_index(table_name, si["column"], si["index_type"])
        except Exception as e:
            raise HTTPException(status_code=422, detail=f"Error creando índice secundario en '{si['column']}': {e}")

    return {"message": f"Tabla '{table_name}' creada con {count} registros", "table": table_name, "rows_loaded": count}
