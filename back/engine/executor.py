from .database import Database
from ..storage import DiskStats
from ..indexes import RTree, NotSupportedError
from ..parser.ast_nodes import (
    CreateTableNode, InsertNode, SelectEqualNode, SelectRangeNode,
    SelectPointRadiusNode, SelectKNNNode, DeleteNode,
)


class Executor:
    """
    Toma un nodo AST y lo ejecuta contra la base de datos.
    Retorna siempre {"results": [...], "stats": {"reads", "writes", "time_ms"}}.
    """

    def __init__(self, db: Database):
        self.db = db
        self.stats = DiskStats()

    def execute(self, node) -> dict:
        """
        Input:  node  cualquier nodo AST del parser
        Output: {"results": list[dict], "stats": dict}
        Raises: ExecutionError si la operación falla
        """
        self.stats.reset()
        dispatch = {
            CreateTableNode:        self._exec_create,
            InsertNode:             self._exec_insert,
            SelectEqualNode:        self._exec_select_equal,
            SelectRangeNode:        self._exec_select_range,
            SelectPointRadiusNode:  self._exec_select_point_radius,
            SelectKNNNode:          self._exec_select_knn,
            DeleteNode:             self._exec_delete,
        }
        handler = dispatch.get(type(node))
        if handler is None:
            raise ExecutionError(f"Tipo de nodo desconocido: {type(node)}")
        results = handler(node)
        return {"results": results, "stats": self.stats.snapshot()}

    # ------------------------------------------------------------------
    # Handlers por tipo de nodo
    # ------------------------------------------------------------------

    def _exec_create(self, node: CreateTableNode) -> list:
        """
        Input:  CreateTableNode
        Output: []  (no retorna filas)
        — Crea la tabla en db; carga CSV si from_file está presente.
        """
        pass

    def _exec_insert(self, node: InsertNode) -> list:
        """
        Input:  InsertNode
        Output: []
        — table.index.add(record)   ← polimorfismo
        """
        pass

    def _exec_select_equal(self, node: SelectEqualNode) -> list:
        """
        Input:  SelectEqualNode
        Output: [dict] o []
        — table.index.search(key)   ← polimorfismo
        """
        pass

    def _exec_select_range(self, node: SelectRangeNode) -> list:
        """
        Input:  SelectRangeNode
        Output: list[dict]
        — table.index.range_search(begin, end)   ← polimorfismo
        """
        pass

    def _exec_select_point_radius(self, node: SelectPointRadiusNode) -> list:
        """
        Input:  SelectPointRadiusNode
        Output: list[dict]
        — Solo válido para RTree → table.index.range_search(point, radius)
        Raises: ExecutionError si el índice no es RTree
        """
        pass

    def _exec_select_knn(self, node: SelectKNNNode) -> list:
        """
        Input:  SelectKNNNode
        Output: list[dict] con k registros ordenados por distancia
        — Solo válido para RTree → table.index.knn(point, k)
        Raises: ExecutionError si el índice no es RTree
        """
        pass

    def _exec_delete(self, node: DeleteNode) -> list:
        """
        Input:  DeleteNode
        Output: []
        — table.index.remove(key)   ← polimorfismo
        """
        pass


class ExecutionError(Exception):
    pass
