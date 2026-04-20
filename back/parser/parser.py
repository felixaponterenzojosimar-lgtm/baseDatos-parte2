from .lexer import Lexer, Token, TokenType
from .ast_nodes import (
    CreateTableNode, InsertNode, SelectEqualNode, SelectComparisonNode, SelectRangeNode,
    SelectPointRadiusNode, SelectKNNNode, DeleteNode,
)


class ParseError(Exception):
    pass


class Parser:
    """
    Parser descendente recursivo para el subconjunto SQL del proyecto.
    Input:  sql  cadena de texto
    Output: nodo AST vía parse()
    """

    def __init__(self, sql: str):
        self.tokens = Lexer(sql).tokenize()
        self.pos = 0

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------

    def parse(self):
        tok = self.peek()
        if tok.type == TokenType.CREATE:
            node = self.parse_create_table()
        elif tok.type == TokenType.INSERT:
            node = self.parse_insert()
        elif tok.type == TokenType.SELECT:
            node = self.parse_select()
        elif tok.type == TokenType.DELETE:
            node = self.parse_delete()
        else:
            raise ParseError(f"Sentencia desconocida: '{tok.value}' en línea {tok.line}")
        self.expect(TokenType.SEMICOLON)
        self.expect(TokenType.EOF)
        return node

    # ------------------------------------------------------------------
    # Reglas de la gramática
    # ------------------------------------------------------------------

    def parse_create_table(self) -> CreateTableNode:
        """
        CREATE TABLE <nombre> (<col> <tipo> [INDEX <tecnica>], ...) [FROM FILE <path>]
        """
        self.expect(TokenType.CREATE)
        self.expect(TokenType.TABLE)
        name = self.expect(TokenType.IDENTIFIER).value
        self.expect(TokenType.LEFT_PARENTHESIS)

        columns = []
        while True:
            col_name = self.expect(TokenType.IDENTIFIER).value
            col_type = self.read_column_type()

            index_type = None
            if self.peek().type == TokenType.INDEX:
                self.advance()
                index_type = self.read_index_type()

            columns.append({"name": col_name, "type": col_type, "index": index_type})

            if self.peek().type == TokenType.COMMA:
                self.advance()
            else:
                break

        self.expect(TokenType.RIGHT_PARENTHESIS)

        from_file = None
        if self.peek().type == TokenType.FROM:
            self.advance()
            self.expect(TokenType.FILE)
            from_file = self.expect(TokenType.STRING_LITERAL).value

        return CreateTableNode(name, columns, from_file)

    def parse_insert(self) -> InsertNode:
        """INSERT INTO <tabla> VALUES (<v1>, <v2>, ...)"""
        self.expect(TokenType.INSERT)
        self.expect(TokenType.INTO)
        name = self.expect(TokenType.IDENTIFIER).value
        self.expect(TokenType.VALUES)
        self.expect(TokenType.LEFT_PARENTHESIS)

        values = []
        while True:
            values.append(self.read_literal())
            if self.peek().type == TokenType.COMMA:
                self.advance()
            else:
                break

        self.expect(TokenType.RIGHT_PARENTHESIS)
        return InsertNode(name, values)

    def parse_select(self):
        """
        SELECT * FROM <tabla> WHERE <col>
            = <valor>
          | BETWEEN <v1> AND <v2>
          | IN (POINT(<x>,<y>), RADIUS <r>)
          | IN (POINT(<x>,<y>), K <k>)
        """
        self.expect(TokenType.SELECT)
        self.expect(TokenType.ASTERISK)
        self.expect(TokenType.FROM)
        table_name = self.expect(TokenType.IDENTIFIER).value
        self.expect(TokenType.WHERE)
        col = self.expect(TokenType.IDENTIFIER).value

        tok = self.peek()

        if tok.type == TokenType.EQUAL:
            self.advance()
            value = self.read_literal()
            return SelectEqualNode(table_name, col, value)

        if tok.type in (
            TokenType.LESS_THAN,
            TokenType.GREATER_THAN,
            TokenType.LESS_THAN_OR_EQUAL,
            TokenType.GREATER_THAN_OR_EQUAL,
        ):
            operator = self.advance().value
            value = self.read_literal()
            return SelectComparisonNode(table_name, col, operator, value)

        if tok.type == TokenType.BETWEEN:
            self.advance()
            begin = self.read_literal()
            self.expect(TokenType.AND)
            end = self.read_literal()
            return SelectRangeNode(table_name, col, begin, end)

        if tok.type == TokenType.IN:
            self.advance()
            self.expect(TokenType.LEFT_PARENTHESIS)
            self.expect(TokenType.POINT)
            self.expect(TokenType.LEFT_PARENTHESIS)
            x = self.read_literal()
            self.expect(TokenType.COMMA)
            y = self.read_literal()
            self.expect(TokenType.RIGHT_PARENTHESIS)
            self.expect(TokenType.COMMA)

            next_tok = self.peek()

            if next_tok.type == TokenType.RADIUS:
                self.advance()
                r = self.read_literal()
                self.expect(TokenType.RIGHT_PARENTHESIS)
                return SelectPointRadiusNode(table_name, col, (x, y), float(r))

            if next_tok.type == TokenType.K:
                self.advance()
                k = self.expect(TokenType.INTEGER_LITERAL).value
                self.expect(TokenType.RIGHT_PARENTHESIS)
                return SelectKNNNode(table_name, col, (x, y), k)

            raise ParseError(
                f"Se esperaba RADIUS o K, se obtuvo '{next_tok.value}' "
                f"en línea {next_tok.line}"
            )

        raise ParseError(
            f"Operador WHERE desconocido: '{tok.value}' en línea {tok.line}"
        )

    def parse_delete(self) -> DeleteNode:
        """DELETE FROM <tabla> WHERE <col> = <valor>"""
        self.expect(TokenType.DELETE)
        self.expect(TokenType.FROM)
        table_name = self.expect(TokenType.IDENTIFIER).value
        self.expect(TokenType.WHERE)
        col = self.expect(TokenType.IDENTIFIER).value
        self.expect(TokenType.EQUAL)
        value = self.read_literal()
        return DeleteNode(table_name, col, value)

    # ------------------------------------------------------------------
    # Utilidades
    # ------------------------------------------------------------------

    def read_literal(self):
        """Lee un valor literal: INTEGER, FLOAT o STRING."""
        tok = self.peek()
        if tok.type in (TokenType.INTEGER_LITERAL, TokenType.FLOAT_LITERAL, TokenType.STRING_LITERAL):
            return self.advance().value
        if tok.type == TokenType.TRUE_LITERAL:
            self.advance()
            return True
        if tok.type == TokenType.FALSE_LITERAL:
            self.advance()
            return False
        if tok.type == TokenType.DATE:
            self.advance()
            return self.expect(TokenType.STRING_LITERAL).value
        if tok.type == TokenType.TIME:
            self.advance()
            return self.expect(TokenType.STRING_LITERAL).value
        raise ParseError(
            f"Se esperaba un valor literal, se obtuvo '{tok.value}' "
            f"({tok.type.name}) en línea {tok.line}"
        )

    def read_column_type(self) -> str:
        tok = self.peek()
        if tok.type == TokenType.INT_TYPE:
            self.advance()
            return "INT"
        if tok.type == TokenType.INTEGER_TYPE:
            self.advance()
            return "INTEGER"
        if tok.type == TokenType.SMALLINT:
            self.advance()
            return "SMALLINT"
        if tok.type == TokenType.BIGINT:
            self.advance()
            return "BIGINT"
        if tok.type == TokenType.REAL:
            self.advance()
            return "REAL"
        if tok.type == TokenType.DOUBLE:
            self.advance()
            self.expect(TokenType.PRECISION)
            return "DOUBLE PRECISION"
        if tok.type == TokenType.BOOLEAN:
            self.advance()
            return "BOOLEAN"
        if tok.type == TokenType.CHAR:
            self.advance()
            self.expect(TokenType.LEFT_PARENTHESIS)
            size = self.expect(TokenType.INTEGER_LITERAL).value
            self.expect(TokenType.RIGHT_PARENTHESIS)
            return f"CHAR({size})"
        if tok.type == TokenType.DATE:
            self.advance()
            return "DATE"
        if tok.type == TokenType.TIME:
            self.advance()
            return "TIME"
        raise ParseError(
            f"Se esperaba un tipo de dato, se obtuvo '{tok.value}' "
            f"({tok.type.name}) en línea {tok.line}"
        )

    def read_index_type(self) -> str:
        tok = self.peek()
        if tok.type == TokenType.RTREE:
            self.advance()
            return "rtree"
        if tok.type == TokenType.BPLUS:
            self.advance()
            self.expect(TokenType.TREE)
            return "bplus"
        if tok.type == TokenType.EXTENDIBLE:
            self.advance()
            self.expect(TokenType.HASHING)
            return "hashing"
        if tok.type == TokenType.SEQUENTIAL:
            self.advance()
            self.expect(TokenType.FILE)
            return "sequential"
        raise ParseError(
            f"Se esperaba una técnica de índice válida, se obtuvo '{tok.value}' "
            f"({tok.type.name}) en línea {tok.line}"
        )

    def expect(self, token_type: TokenType) -> Token:
        tok = self.peek()
        if tok.type != token_type:
            raise ParseError(
                f"Se esperaba {token_type.name}, "
                f"se obtuvo '{tok.value}' ({tok.type.name}) en línea {tok.line}"
            )
        return self.advance()

    def peek(self) -> Token:
        return self.tokens[self.pos]

    def advance(self) -> Token:
        tok = self.tokens[self.pos]
        if tok.type != TokenType.EOF:
            self.pos += 1
        return tok
