from .database import Database
from ..storage import DiskStats
from ..indexes import RTree, NotSupportedError
from ..parser.ast_nodes import (
    CreateTableNode, InsertNode, SelectEqualNode, SelectComparisonNode, SelectRangeNode,
    SelectPointRadiusNode, SelectKNNNode, DeleteNode,
)


class ExecutionError(Exception):
    pass


class Executor:
    """
    Toma un nodo AST y lo ejecuta contra la base de datos.
    Retorna siempre {"results": [...], "stats": {"reads", "writes", "time_ms"}}.
    """

    def __init__(self, db: Database):
        self.db = db
        self.stats = DiskStats()

    # ------------------------------------------------------------------
    # API publica
    # ------------------------------------------------------------------

    def execute(self, node) -> dict:
        """
        Input:  node  cualquier nodo AST del parser
        Output: {"results": list[dict], "stats": dict}
        Raises: ExecutionError si la operacion falla
        """
        self.stats.reset()

        dispatch = {
            CreateTableNode:       self._exec_create,
            InsertNode:            self._exec_insert,
            SelectEqualNode:       self._exec_select_equal,
            SelectComparisonNode:  self._exec_select_comparison,
            SelectRangeNode:       self._exec_select_range,
            SelectPointRadiusNode: self._exec_select_point_radius,
            SelectKNNNode:         self._exec_select_knn,
            DeleteNode:            self._exec_delete,
        }
        handler = dispatch.get(type(node))
        if handler is None:
            raise ExecutionError(f"Tipo de nodo desconocido: {type(node)}")

        try:
            results = handler(node)
        except (KeyError, ValueError, NotSupportedError) as error:
            raise ExecutionError(str(error)) from error

        return {"results": results, "stats": self.stats.snapshot()}

    # ------------------------------------------------------------------
    # Handlers
    # ------------------------------------------------------------------

    def _exec_create(self, node: CreateTableNode) -> list:
        """
        Construye el Schema desde las columnas del parser y crea la tabla.
        Si from_file esta presente, carga el CSV.
        """
        schema, index_type = Database.schema_from_columns(node.columns)
        self.db.create_table(
            name=node.table_name,
            schema=schema,
            index_type=index_type,
            from_file=node.from_file,
        )
        return []

    def _exec_insert(self, node: InsertNode) -> list:
        """
        Mapea los valores posicionales a los campos del schema y llama add().
        """
        table = self.db.get_table(node.table_name)
        fields = table.schema.fields

        if len(node.values) != len(fields):
            raise ExecutionError(
                f"INSERT: se esperaban {len(fields)} valores, "
                f"se recibieron {len(node.values)}"
            )

        record = {}
        for field, value in zip(fields, node.values):
            record[field.name] = self._cast_value(value, field)

        table.index.add(record)
        return []

    def _exec_select_equal(self, node: SelectEqualNode) -> list:
        """Busqueda exacta por clave."""
        table = self.db.get_table(node.table_name)
        key = self._cast_key(node.value, table, node.column)
        result = table.index.search(key)
        return [result] if result is not None else []

    def _exec_select_comparison(self, node: SelectComparisonNode) -> list:
        """Busqueda por comparacion simple usando range_search y filtro final."""
        from ..storage.schema import FieldType

        table = self.db.get_table(node.table_name)
        field = table.schema.get_field(node.column)
        key = self._cast_value(node.value, field)

        if field.field_type == FieldType.INT:
            begin = -2147483648
            end = 2147483647
        elif field.field_type == FieldType.FLOAT:
            begin = float("-inf")
            end = float("inf")
        elif field.field_type == FieldType.BOOL:
            begin = False
            end = True
        else:
            begin = ""
            end = chr(127) * field.size

        if node.operator in ("<", "<="):
            results = table.index.range_search(begin, key)
            if node.operator == "<":
                return [record for record in results if record[node.column] < key]
            return [record for record in results if record[node.column] <= key]

        if node.operator in (">", ">="):
            results = table.index.range_search(key, end)
            if node.operator == ">":
                return [record for record in results if record[node.column] > key]
            return [record for record in results if record[node.column] >= key]

        raise ExecutionError(f"Operador de comparacion no soportado: '{node.operator}'")

    def _exec_select_range(self, node: SelectRangeNode) -> list:
        """Busqueda por rango [begin, end]."""
        table = self.db.get_table(node.table_name)
        begin = self._cast_key(node.begin, table, node.column)
        end = self._cast_key(node.end, table, node.column)
        return table.index.range_search(begin, end)

    def _exec_select_point_radius(self, node: SelectPointRadiusNode) -> list:
        """Busqueda espacial por radio. Solo valida para RTree."""
        table = self.db.get_table(node.table_name)
        if not isinstance(table.index, RTree):
            raise ExecutionError(
                f"La tabla '{node.table_name}' no usa un indice RTree"
            )
        return table.index.range_search(node.point, node.radius)

    def _exec_select_knn(self, node: SelectKNNNode) -> list:
        """Busqueda de k vecinos mas cercanos. Solo valida para RTree."""
        table = self.db.get_table(node.table_name)
        if not isinstance(table.index, RTree):
            raise ExecutionError(
                f"La tabla '{node.table_name}' no usa un indice RTree"
            )
        return table.index.knn(node.point, node.k)

    def _exec_delete(self, node: DeleteNode) -> list:
        """Elimina el registro con la clave dada."""
        table = self.db.get_table(node.table_name)
        key = self._cast_key(node.value, table, node.column)
        removed = table.index.remove(key)
        return [{"deleted": removed}]

    # ------------------------------------------------------------------
    # Utilidades de casting
    # ------------------------------------------------------------------

    def _cast_key(self, raw_value, table, column_name):
        """Convierte el valor literal del parser al tipo Python del campo."""
        try:
            field = table.schema.get_field(column_name)
        except KeyError:
            raise ExecutionError(
                f"Columna '{column_name}' no existe en '{table.name}'"
            )
        return self._cast_value(raw_value, field)

    def _cast_value(self, value, field):
        """Convierte value al tipo correcto del Field."""
        from ..storage.schema import FieldType

        if field.field_type == FieldType.INT:
            return int(value)
        if field.field_type == FieldType.FLOAT:
            return float(value)
        if field.field_type == FieldType.BOOL:
            if isinstance(value, bool):
                return value
            return str(value).lower() in ("true", "1", "yes")
        return str(value)
