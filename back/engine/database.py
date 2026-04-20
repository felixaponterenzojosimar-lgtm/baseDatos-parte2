import os
import csv
from .table import Table
from ..storage import Schema, Field, FieldType, PageManager, DiskStats
from ..indexes import SequentialFile, ExtendibleHashing, BPlusTree, RTree

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")

# Tipos SQL aceptados en CREATE TABLE
_SQL_TYPES = {
    "INT", "INTEGER", "SMALLINT", "BIGINT",
    "REAL", "DOUBLE PRECISION", "BOOLEAN",
    "CHAR", "DATE", "TIME",
}


class Database:
    """
    Gestiona el conjunto de tablas en memoria y en disco.
    Punto de entrada principal del motor.
    """

    INDEX_TYPES = {"sequential", "hashing", "bplus", "rtree"}

    def __init__(self):
        self._tables: dict[str, Table] = {}
        os.makedirs(DATA_DIR, exist_ok=True)

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------

    def create_table(self, name: str, schema: Schema, index_type: str,
                     from_file: str = None) -> Table:
        """
        Input:  name        nombre de la tabla
                schema      Schema con los campos
                index_type  "sequential" | "hashing" | "bplus" | "rtree"
                from_file   ruta CSV opcional para carga inicial
        Output: Table creada
        Raises: ValueError si la tabla ya existe o index_type inválido
        """
        if name in self._tables:
            raise ValueError(f"La tabla '{name}' ya existe")
        if index_type not in self.INDEX_TYPES:
            raise ValueError(
                f"index_type '{index_type}' no válido. Opciones: {self.INDEX_TYPES}"
            )

        stats = DiskStats()
        index = self._build_index(name, schema, index_type, stats)
        table = Table(name, schema, index)
        self._tables[name] = table

        if from_file:
            self._load_csv(table, from_file)

        return table

    def get_table(self, name: str) -> Table:
        """
        Input:  name  nombre de la tabla
        Output: Table
        Raises: KeyError si no existe
        """
        if name not in self._tables:
            raise KeyError(f"Tabla '{name}' no existe")
        return self._tables[name]

    def drop_table(self, name: str) -> None:
        """
        Input:  name  nombre de la tabla
        Output: None — elimina tabla de memoria y archivos de disco
        """
        if name not in self._tables:
            raise KeyError(f"Tabla '{name}' no existe")
        for suffix in ["", "_aux", "_dir"]:
            path = os.path.join(DATA_DIR, f"{name}{suffix}.bin")
            if os.path.exists(path):
                os.remove(path)
        del self._tables[name]

    def list_tables(self) -> list:
        """Output: lista de nombres de tablas existentes."""
        return list(self._tables.keys())

    # ------------------------------------------------------------------
    # Métodos internos
    # ------------------------------------------------------------------

    def _build_index(self, name: str, schema: Schema,
                     index_type: str, stats: DiskStats):
        """Instancia el índice correcto según index_type."""
        main_path = os.path.join(DATA_DIR, f"{name}.bin")
        pm = PageManager(main_path, stats)

        if index_type == "sequential":
            aux_path = os.path.join(DATA_DIR, f"{name}_aux.bin")
            aux_pm = PageManager(aux_path, stats)
            return SequentialFile(schema, pm, aux_pm, stats)

        if index_type == "hashing":
            dir_path = os.path.join(DATA_DIR, f"{name}_dir.bin")
            dir_pm = PageManager(dir_path, stats)
            return ExtendibleHashing(schema, pm, dir_pm, stats)

        if index_type == "bplus":
            return BPlusTree(schema, pm, stats)

        if index_type == "rtree":
            lat_field, lon_field = self._find_spatial_fields(schema)
            return RTree(schema, pm, stats, lat_field, lon_field)

    def _find_spatial_fields(self, schema: Schema) -> tuple:
        """Detecta los campos lat/lon en el schema para RTree."""
        lat_names = {"lat", "latitude", "latitud"}
        lon_names = {"lon", "lng", "longitude", "longitud"}
        lat_field = lon_field = None
        for f in schema.fields:
            if f.name.lower() in lat_names:
                lat_field = f.name
            elif f.name.lower() in lon_names:
                lon_field = f.name
        if not lat_field or not lon_field:
            raise ValueError(
                "RTree requiere campos con nombre lat/latitude/latitud "
                "y lon/lng/longitude/longitud en el schema"
            )
        return lat_field, lon_field

    def _load_csv(self, table: Table, filepath: str) -> int:
        """
        Input:  table     Table destino
                filepath  ruta al archivo CSV
        Output: número de registros insertados
        """
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"CSV no encontrado: {filepath}")

        count = 0
        with open(filepath, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                record = self._cast_row(row, table.schema)
                table.index.add(record)
                count += 1
        return count

    def _cast_row(self, row: dict, schema: Schema) -> dict:
        """Convierte una fila CSV (strings) al tipo Python correcto según el schema."""
        record = {}
        for field in schema.fields:
            raw = row.get(field.name, "")
            if field.field_type == FieldType.INT:
                record[field.name] = int(raw)
            elif field.field_type == FieldType.FLOAT:
                record[field.name] = float(raw)
            elif field.field_type == FieldType.BOOL:
                record[field.name] = raw.strip().lower() in ("true", "1", "yes", "si")
            else:
                record[field.name] = raw
        return record

    # ------------------------------------------------------------------
    # Utilidad: construir Schema desde las columnas del parser
    # ------------------------------------------------------------------

    @staticmethod
    def schema_from_columns(columns: list) -> tuple:
        """
        Input:  columns  lista de dicts {"name", "type", "index"} del parser
        Output: (Schema, index_type str)
        Convierte los tipos SQL a objetos Field.
        """
        fields = []
        index_type = "bplus"    # default si ninguna columna tiene INDEX
        primary_key = columns[0]["name"]

        for col in columns:
            name = col["name"]
            sql_type = col["type"].upper()
            if col.get("index"):
                index_type = col["index"].lower()
                primary_key = name

            if sql_type in {"INT", "INTEGER", "SMALLINT", "BIGINT"}:
                fields.append(Field(name, FieldType.INT))
            elif sql_type in {"REAL", "DOUBLE PRECISION"}:
                fields.append(Field(name, FieldType.FLOAT))
            elif sql_type == "BOOLEAN":
                fields.append(Field(name, FieldType.BOOL))
            elif sql_type.startswith("CHAR("):
                size = int(sql_type[5:-1])
                fields.append(Field(name, FieldType.VARCHAR, max_length=size))
            elif sql_type == "DATE":
                fields.append(Field(name, FieldType.VARCHAR, max_length=10))
            elif sql_type == "TIME":
                fields.append(Field(name, FieldType.VARCHAR, max_length=8))
            else:
                raise ValueError(f"Tipo SQL desconocido: '{sql_type}'")

        return Schema(fields, primary_key), index_type
