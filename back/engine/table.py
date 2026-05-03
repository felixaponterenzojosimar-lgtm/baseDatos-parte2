from ..storage import Schema
from ..indexes import Index


class Table:
    """
    Representa una tabla: schema + el índice que la gestiona.
    El índice es polimórfico → el Executor llama siempre igual.
    """

    def __init__(self, name: str, schema: Schema, index: Index):
        self.name = name
        self.schema = schema
        self.index = index  # SequentialFile | ExtendibleHashing | BPlusTree | RTree
        self.secondary_indexes: dict[str, Index] = {}  # column -> Index

    def __repr__(self):
        return f"Table('{self.name}', {self.schema}, index={type(self.index).__name__})"
