import os
import csv
import json
import shutil
from .table import Table
from ..storage import Schema, Field, FieldType, PageManager, DiskStats
from ..indexes import SequentialFile, ExtendibleHashing, BPlusTree, RTree

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
CATALOG_SUFFIX = "_catalog.json"


class Database:
    """
    Gestiona el conjunto de tablas en memoria y en disco.
    Punto de entrada principal del motor.
    """

    INDEX_TYPES = {"sequential", "hashing", "bplus", "rtree"}
    PRIMARY_INDEX_TYPES = {"sequential", "hashing", "bplus"}

    def __init__(self):
        self._tables: dict[str, Table] = {}
        self.stats = DiskStats()
        os.makedirs(DATA_DIR, exist_ok=True)
        self._load_catalogs()

    # ------------------------------------------------------------------
    # API publica
    # ------------------------------------------------------------------

    def create_table(
        self,
        name: str,
        schema: Schema,
        column_definitions: list,
        primary_index_type: str = "bplus",
        from_file: str = None,
    ) -> Table:
        if name in self._tables:
            raise ValueError(f"La tabla '{name}' ya existe")
        if primary_index_type not in self.PRIMARY_INDEX_TYPES:
            raise ValueError(
                "La llave primaria solo puede usar SEQUENTIAL, EXTENDIBLE HASHING o BPLUS TREE"
            )

        self._ensure_data_dir()
        pk_storage_name = self._primary_storage_name(schema.primary_key)
        index = self._build_index(name, pk_storage_name, schema, primary_index_type, [schema.primary_key])
        table = Table(name, schema, index, column_definitions, primary_index_type)
        self._tables[name] = table

        if from_file:
            self._load_csv(table, from_file)

        self._save_table_catalog(table)
        return table

    def get_table(self, name: str) -> Table:
        if name not in self._tables:
            raise KeyError(f"Tabla '{name}' no existe")
        return self._tables[name]

    def add_secondary_index(self, table_name: str, index_name: str, columns: list, index_type: str) -> None:
        table = self.get_table(table_name)
        if index_name in table.secondary_indexes:
            raise ValueError(f"Ya existe un indice llamado '{index_name}' en '{table_name}'")
        if index_type not in self.INDEX_TYPES:
            raise ValueError(f"index_type '{index_type}' no valido")

        field_names = [field.name for field in table.schema.fields]
        for column in columns:
            if column not in field_names:
                raise ValueError(f"Columna '{column}' no existe en '{table_name}'")

        pk_field = table.schema.get_field(table.schema.primary_key)
        if index_type == "rtree":
            if len(columns) != 2:
                raise ValueError("RTree requiere exactamente dos columnas")
            sec_schema = Schema(table.schema.fields, table.schema.primary_key)
        else:
            if len(columns) != 1:
                raise ValueError("Los indices escalares requieren exactamente una columna")
            key_field = table.schema.get_field(columns[0])
            sec_schema = Schema([key_field, pk_field], primary_key=columns[0])

        sec_index = self._build_index(table_name, index_name, sec_schema, index_type, columns, secondary=True)
        entry = {"index": sec_index, "type": index_type, "columns": columns}
        table.secondary_indexes[index_name] = entry

        if index_type == "rtree":
            self._populate_rtree_secondary_index(table, entry)
        else:
            self._populate_secondary_index(table, entry)
        self._save_table_catalog(table)

    def drop_secondary_index(self, table_name: str, index_name: str) -> None:
        table = self.get_table(table_name)
        if index_name == self._primary_storage_name(table.schema.primary_key):
            raise ValueError("DROP INDEX no puede eliminar el indice de la llave primaria")
        if index_name not in table.secondary_indexes:
            raise KeyError(f"Indice '{index_name}' no existe en '{table_name}'")

        del table.secondary_indexes[index_name]
        self._delete_index_files(table_name, index_name)
        self._save_table_catalog(table)

    def drop_table(self, name: str) -> None:
        if name not in self._tables:
            raise KeyError(f"Tabla '{name}' no existe")

        self._delete_table_files(name)
        del self._tables[name]

    def list_tables(self) -> list:
        return list(self._tables.keys())

    # ------------------------------------------------------------------
    # Metodos internos
    # ------------------------------------------------------------------

    def _table_catalog_path(self, table_name: str) -> str:
        return os.path.join(DATA_DIR, f"{table_name}{CATALOG_SUFFIX}")

    def _index_base_path(self, table_name: str, index_name: str) -> str:
        return os.path.join(DATA_DIR, f"{table_name}_{index_name}")

    def _primary_storage_name(self, primary_key_column: str) -> str:
        return f"pk_{primary_key_column}"

    def _ensure_data_dir(self) -> None:
        os.makedirs(DATA_DIR, exist_ok=True)

    def _delete_table_files(self, table_name: str) -> None:
        prefix = f"{table_name}_"
        for filename in os.listdir(DATA_DIR):
            if filename.startswith(prefix):
                filepath = os.path.join(DATA_DIR, filename)
                try:
                    if os.path.isfile(filepath):
                        os.remove(filepath)
                except OSError:
                    pass  # Ignorar errores de eliminación individuales

    def _delete_index_files(self, table_name: str, storage_name: str) -> None:
        base_name = f"{table_name}_{storage_name}"
        extensions = [".bin", "_aux.bin", "_dir.bin", ".root"]
        for ext in extensions:
            filepath = os.path.join(DATA_DIR, base_name + ext)
            if os.path.exists(filepath):
                try:
                    os.remove(filepath)
                except OSError:
                    pass

    def _build_index(
        self,
        table_name: str,
        storage_name: str,
        schema: Schema,
        index_type: str,
        index_columns: list | None = None,
        stats: DiskStats = None,
        secondary: bool = False,
    ):
        if stats is None:
            stats = self.stats
        base_path = self._index_base_path(table_name, storage_name)
        main_path = f"{base_path}.bin"
        pm = PageManager(main_path, stats)

        if index_type == "sequential":
            aux_pm = PageManager(f"{base_path}_aux.bin", stats)
            return SequentialFile(schema, pm, aux_pm, stats)

        if index_type == "hashing":
            dir_pm = PageManager(f"{base_path}_dir.bin", stats)
            return ExtendibleHashing(schema, pm, dir_pm, stats)

        if index_type == "bplus":
            return BPlusTree(schema, pm, stats)

        if index_type == "rtree":
            if index_columns is None or len(index_columns) != 2:
                raise ValueError("RTree requiere exactamente dos columnas para construirse")
            return RTree(schema, pm, stats, index_columns[0], index_columns[1])

        raise ValueError(f"index_type '{index_type}' no valido")

    def _populate_secondary_index(self, table: Table, secondary_entry: dict) -> None:
        from ..indexes.base_index import DuplicateKeyError

        sec_index = secondary_entry["index"]
        column_name = secondary_entry["columns"][0]
        for item in table.index.iter_record_refs():
            record = item["record"]
            try:
                sec_index.add_ref(record[column_name], record[table.schema.primary_key])
            except DuplicateKeyError:
                pass

    def _populate_rtree_secondary_index(self, table: Table, secondary_entry: dict) -> None:
        lat_column, lon_column = secondary_entry["columns"]
        refs = []
        for item in table.index.iter_record_refs():
            record = item["record"]
            refs.append({
                "lat": float(record[lat_column]),
                "lon": float(record[lon_column]),
                "pk": record[table.schema.primary_key],
            })
        secondary_entry["index"].build_from_refs(refs)

    def resolve_primary_key(self, table: Table, primary_key_value) -> dict:
        return table.index.search(primary_key_value)

    def find_primary_ref(self, table: Table, key):
        return table.index.find_record_ref(key)

    def _load_csv(self, table: Table, filepath: str) -> int:
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"CSV no encontrado: {filepath}")

        count = 0
        with open(filepath, newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                record = self._cast_row(row, table.schema)
                table.index.add(record)
                count += 1
        return count

    def _cast_row(self, row: dict, schema: Schema) -> dict:
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

    def _save_table_catalog(self, table: Table) -> None:
        entry = {
            "primary_key": {
                "column": table.schema.primary_key,
                "index_type": self._catalog_index_type(table.primary_index_type),
                "storage_name": self._primary_storage_name(table.schema.primary_key),
            },
            "columns": [self._copy_column_definition(column) for column in table.column_definitions],
            "indexes": [
                {
                    "name": index_name,
                    "type": self._catalog_index_type(meta["type"]),
                    "columns": list(meta["columns"]),
                    "storage_name": index_name,
                }
                for index_name, meta in table.secondary_indexes.items()
            ],
        }

        with open(self._table_catalog_path(table.name), "w", encoding="utf-8") as handle:
            json.dump(entry, handle, indent=2)

    def _load_catalogs(self) -> None:
        for filename in os.listdir(DATA_DIR):
            if not filename.endswith(CATALOG_SUFFIX):
                continue
            table_name = filename.removesuffix(CATALOG_SUFFIX)
            catalog_path = os.path.join(DATA_DIR, filename)

            try:
                with open(catalog_path, encoding="utf-8") as handle:
                    entry = json.load(handle)

                primary_key_entry = entry["primary_key"]
                primary_key_column = primary_key_entry["column"]
                primary_index_type = self._parse_catalog_index_type(primary_key_entry["index_type"])
                primary_storage_name = primary_key_entry.get(
                    "storage_name",
                    self._primary_storage_name(primary_key_column),
                )
                column_definitions = [self._copy_column_definition(column) for column in entry["columns"]]
                schema = self.schema_from_catalog_columns(column_definitions, primary_key_column)
                primary_index = self._build_index(
                    table_name,
                    primary_storage_name,
                    schema,
                    primary_index_type,
                    [primary_key_column],
                )
                table = Table(table_name, schema, primary_index, column_definitions, primary_index_type)

                for index_entry in entry.get("indexes", []):
                    index_name = index_entry["name"]
                    index_type = self._parse_catalog_index_type(index_entry["type"])
                    columns = list(index_entry["columns"])
                    storage_name = index_entry.get("storage_name", index_name)
                    if index_type == "rtree":
                        sec_schema = Schema(schema.fields, schema.primary_key)
                    else:
                        sec_schema = Schema([schema.get_field(columns[0]), schema.get_field(schema.primary_key)], columns[0])
                    sec_index = self._build_index(table_name, storage_name, sec_schema, index_type, columns)
                    table.secondary_indexes[index_name] = {
                        "index": sec_index,
                        "type": index_type,
                        "columns": columns,
                    }

                self._tables[table_name] = table
            except Exception:
                continue

    def _catalog_index_type(self, index_type: str) -> str:
        if index_type == "sequential":
            return "SEQUENTIAL"
        if index_type == "hashing":
            return "EXTENDIBLE HASHING"
        if index_type == "bplus":
            return "BPLUS TREE"
        if index_type == "rtree":
            return "RTREE"
        raise ValueError(f"index_type '{index_type}' no valido para catalogo")

    def _parse_catalog_index_type(self, index_type: str) -> str:
        normalized = index_type.upper()
        if normalized == "SEQUENTIAL":
            return "sequential"
        if normalized == "EXTENDIBLE HASHING":
            return "hashing"
        if normalized == "BPLUS TREE":
            return "bplus"
        if normalized == "RTREE":
            return "rtree"
        raise ValueError(f"Tipo de indice desconocido en catalogo: '{index_type}'")

    def _copy_column_definition(self, column: dict) -> dict:
        copied = {"name": column["name"], "type": column["type"]}
        if "size" in column:
            copied["size"] = column["size"]
        return copied

    # ------------------------------------------------------------------
    # Utilidad: construir Schema desde el parser o el catalogo
    # ------------------------------------------------------------------

    @staticmethod
    def schema_from_columns(columns: list) -> tuple:
        fields = []
        column_definitions = []
        primary_key = None
        primary_index_type = "bplus"

        for column in columns:
            name = column["name"]
            sql_type = column["type"].upper()

            if column.get("primary_key"):
                primary_key = name
                primary_index_type = column.get("primary_index_type") or "bplus"

            if sql_type in {"INT", "INTEGER", "SMALLINT", "BIGINT"}:
                fields.append(Field(name, FieldType.INT))
                column_definitions.append({"name": name, "type": sql_type})
            elif sql_type in {"REAL", "DOUBLE PRECISION"}:
                fields.append(Field(name, FieldType.FLOAT))
                column_definitions.append({"name": name, "type": sql_type})
            elif sql_type == "BOOLEAN":
                fields.append(Field(name, FieldType.BOOL))
                column_definitions.append({"name": name, "type": sql_type})
            elif sql_type.startswith("CHAR("):
                size = int(sql_type[5:-1])
                fields.append(Field(name, FieldType.VARCHAR, max_length=size))
                column_definitions.append({"name": name, "type": "CHAR", "size": size})
            elif sql_type == "DATE":
                fields.append(Field(name, FieldType.VARCHAR, max_length=10))
                column_definitions.append({"name": name, "type": "DATE"})
            elif sql_type == "TIME":
                fields.append(Field(name, FieldType.VARCHAR, max_length=8))
                column_definitions.append({"name": name, "type": "TIME"})
            else:
                raise ValueError(f"Tipo SQL desconocido: '{sql_type}'")

        if primary_key is None:
            raise ValueError("CREATE TABLE requiere una columna PRIMARY KEY")

        return Schema(fields, primary_key), column_definitions, primary_index_type

    @staticmethod
    def schema_from_catalog_columns(columns: list, primary_key: str) -> Schema:
        fields = []
        for column in columns:
            column_type = column["type"].upper()
            if column_type in {"INT", "INTEGER", "SMALLINT", "BIGINT"}:
                fields.append(Field(column["name"], FieldType.INT))
            elif column_type in {"REAL", "DOUBLE PRECISION"}:
                fields.append(Field(column["name"], FieldType.FLOAT))
            elif column_type == "BOOLEAN":
                fields.append(Field(column["name"], FieldType.BOOL))
            elif column_type == "CHAR":
                fields.append(Field(column["name"], FieldType.VARCHAR, max_length=column["size"]))
            elif column_type == "DATE":
                fields.append(Field(column["name"], FieldType.VARCHAR, max_length=10))
            elif column_type == "TIME":
                fields.append(Field(column["name"], FieldType.VARCHAR, max_length=8))
            else:
                raise ValueError(f"Tipo de dato invalido en catalogo: '{column['type']}'")
        return Schema(fields, primary_key)
