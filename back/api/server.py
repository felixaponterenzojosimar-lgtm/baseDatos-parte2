from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from ..engine import Database, Executor
from ..parser import Parser, ParseError
from ..engine.executor import ExecutionError

app = FastAPI(title="Mini-SGBD API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

db = Database()
executor = Executor(db)


# ------------------------------------------------------------------
# Schemas de request/response
# ------------------------------------------------------------------

class QueryRequest(BaseModel):
    sql: str


class QueryResponse(BaseModel):
    results: list[dict]
    stats: dict   # {"reads": N, "writes": M, "time_ms": T}


# ------------------------------------------------------------------
# Endpoints
# ------------------------------------------------------------------

@app.post("/query", response_model=QueryResponse)
def run_query(req: QueryRequest):
    """
    Input:  { "sql": "SELECT * FROM ..." }
    Output: { "results": [...], "stats": {...} }
    """
    pass


@app.get("/tables")
def list_tables():
    """
    Output: { "tables": ["tabla1", "tabla2"] }
    """
    pass


@app.get("/tables/{name}/schema")
def get_schema(name: str):
    """
    Input:  name  nombre de la tabla (path param)
    Output: { "columns": {"col": "tipo"}, "index_type": "bplus", "record_size": N }
    """
    pass
