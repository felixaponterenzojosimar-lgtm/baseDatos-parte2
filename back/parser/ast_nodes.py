class CreateTableNode:
    """CREATE TABLE nombre (col tipo [INDEX tecnica], ...) [FROM FILE path]"""

    def __init__(self, table_name: str, columns: list, from_file: str = None):
        self.table_name = table_name
        self.columns = columns      # [{"name": str, "type": str, "index": str|None}]
        self.from_file = from_file


class InsertNode:
    """INSERT INTO tabla VALUES (...)"""

    def __init__(self, table_name: str, values: list):
        self.table_name = table_name
        self.values = values


class SelectEqualNode:
    """SELECT * FROM tabla WHERE col = valor"""

    def __init__(self, table_name: str, column: str, value):
        self.table_name = table_name
        self.column = column
        self.value = value


class SelectRangeNode:
    """SELECT * FROM tabla WHERE col BETWEEN v1 AND v2"""

    def __init__(self, table_name: str, column: str, begin, end):
        self.table_name = table_name
        self.column = column
        self.begin = begin
        self.end = end


class SelectPointRadiusNode:
    """SELECT * FROM tabla WHERE col IN (POINT(x, y), RADIUS r)"""

    def __init__(self, table_name: str, column: str, point: tuple, radius: float):
        self.table_name = table_name
        self.column = column
        self.point = point      # (lat, lon)
        self.radius = radius


class SelectKNNNode:
    """SELECT * FROM tabla WHERE col IN (POINT(x, y), K k)"""

    def __init__(self, table_name: str, column: str, point: tuple, k: int):
        self.table_name = table_name
        self.column = column
        self.point = point      # (lat, lon)
        self.k = k


class DeleteNode:
    """DELETE FROM tabla WHERE col = valor"""

    def __init__(self, table_name: str, column: str, value):
        self.table_name = table_name
        self.column = column
        self.value = value
