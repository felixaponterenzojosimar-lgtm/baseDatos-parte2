import re
from .ast_nodes import (
    CreateTableNode, DateLiteralNode, TimeLiteralNode, InsertNode, SelectEqualNode,
    SelectComparisonNode, SelectRangeNode, SelectPointRadiusNode, SelectKNNNode, DeleteNode,
)


class SemanticError(Exception):
    pass


class SemanticAnalyzer:
    """
    Verificador semántico inicial para el subconjunto SQL del proyecto.
    Recibe un nodo AST y retorna True si cumple las restricciones
    actualmente verificables sin depender del motor.
    """

    def __init__(self):
        self.error_message = ""

    def validate(self, node) -> bool:
        self.error_message = ""

        if isinstance(node, CreateTableNode):
            return self.validate_create_table_node(node)

        if isinstance(node, InsertNode):
            return self.validate_insert_node(node)

        if isinstance(node, SelectEqualNode):
            return self.validate_select_equal_node(node)

        if isinstance(node, SelectComparisonNode):
            return self.validate_select_comparison_node(node)

        if isinstance(node, SelectRangeNode):
            return self.validate_select_range_node(node)

        if isinstance(node, SelectPointRadiusNode):
            return self.validate_select_point_radius_node(node)

        if isinstance(node, SelectKNNNode):
            return self.validate_select_knn_node(node)

        if isinstance(node, DeleteNode):
            return self.validate_delete_node(node)

        self.error_message = f"No existe verificación semántica para el nodo {type(node).__name__}"
        return False

    def validate_create_table_node(self, node: CreateTableNode) -> bool:
        names = set()
        for column in node.columns:
            name = column["name"]
            column_type = column["type"]

            if name in names:
                self.error_message = f"La columna '{name}' está repetida en CREATE TABLE"
                return False
            names.add(name)

            if column_type.startswith("CHAR(") and column_type.endswith(")"):
                size = int(column_type[5:-1])
                if size <= 0:
                    self.error_message = "CHAR(n) debe usar un tamaño entero mayor que cero"
                    return False

        if node.from_file is not None and node.from_file == "":
            self.error_message = "FROM FILE debe recibir una ruta no vacía"
            return False

        return True

    def validate_insert_node(self, node: InsertNode) -> bool:
        for value in node.values:
            if not self.validate_literal(value):
                return False
        return True

    def validate_select_equal_node(self, node: SelectEqualNode) -> bool:
        return self.validate_literal(node.value)

    def validate_select_comparison_node(self, node: SelectComparisonNode) -> bool:
        if not self.validate_literal(node.value):
            return False
        return True

    def validate_select_range_node(self, node: SelectRangeNode) -> bool:
        if not self.validate_literal(node.begin):
            return False
        if not self.validate_literal(node.end):
            return False

        begin_type = type(node.begin)
        end_type = type(node.end)
        numeric_range = begin_type in (int, float) and end_type in (int, float)
        date_range = isinstance(node.begin, DateLiteralNode) and isinstance(node.end, DateLiteralNode)
        time_range = isinstance(node.begin, TimeLiteralNode) and isinstance(node.end, TimeLiteralNode)

        if begin_type != end_type and not numeric_range and not date_range and not time_range:
            self.error_message = "BETWEEN debe comparar literales compatibles entre sí"
            return False

        begin_value = self.literal_value(node.begin)
        end_value = self.literal_value(node.end)
        if begin_value > end_value:
            self.error_message = "BETWEEN debe usar un límite inferior menor o igual al superior"
            return False

        return True

    def validate_select_point_radius_node(self, node: SelectPointRadiusNode) -> bool:
        x = node.point[0]
        y = node.point[1]

        if type(x) not in (int, float) or type(y) not in (int, float):
            self.error_message = "POINT(x, y) debe usar coordenadas numéricas"
            return False

        if type(node.radius) not in (int, float) or node.radius <= 0:
            self.error_message = "RADIUS debe ser un valor numérico positivo"
            return False

        return True

    def validate_select_knn_node(self, node: SelectKNNNode) -> bool:
        x = node.point[0]
        y = node.point[1]

        if type(x) not in (int, float) or type(y) not in (int, float):
            self.error_message = "POINT(x, y) debe usar coordenadas numéricas"
            return False

        if type(node.k) is not int or node.k <= 0:
            self.error_message = "K debe ser un entero positivo"
            return False

        return True

    def validate_delete_node(self, node: DeleteNode) -> bool:
        return self.validate_literal(node.value)

    def validate_literal(self, value) -> bool:
        if isinstance(value, DateLiteralNode):
            if re.fullmatch(r"\d{4}-\d{2}-\d{2}", value.value) is None:
                self.error_message = "DATE debe tener el formato semántico yyyy-mm-dd"
                return False

            year, month, day = value.value.split("-")
            year = int(year)
            month = int(month)
            day = int(day)
            if month < 1 or month > 12:
                self.error_message = "DATE debe contener un mes entre 01 y 12"
                return False

            days_in_month = {
                1: 31,
                2: 29 if self.is_leap_year(year) else 28,
                3: 31,
                4: 30,
                5: 31,
                6: 30,
                7: 31,
                8: 31,
                9: 30,
                10: 31,
                11: 30,
                12: 31,
            }
            if day < 1 or day > days_in_month[month]:
                self.error_message = "DATE debe contener un día válido para el mes y año indicados"
                return False

        if isinstance(value, TimeLiteralNode):
            if re.fullmatch(r"\d{2}:\d{2}:\d{2}", value.value) is None:
                self.error_message = "TIME debe tener el formato semántico hh:mm:ss"
                return False

            hour, minute, second = value.value.split(":")
            hour = int(hour)
            minute = int(minute)
            second = int(second)
            if hour < 0 or hour > 23 or minute < 0 or minute > 59 or second < 0 or second > 59:
                self.error_message = "TIME debe contener hora, minuto y segundo dentro de rangos válidos"
                return False

        return True

    def literal_value(self, value):
        if isinstance(value, (DateLiteralNode, TimeLiteralNode)):
            return value.value
        return value

    def is_leap_year(self, year: int) -> bool:
        if year % 400 == 0:
            return True
        if year % 100 == 0:
            return False
        return year % 4 == 0
