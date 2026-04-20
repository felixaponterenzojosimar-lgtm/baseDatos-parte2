from .lexer import Lexer, Token, TokenType
from .ast_nodes import (
    CreateTableNode, InsertNode, SelectEqualNode, SelectRangeNode,
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
        tok = self._peek()
        if tok.type == TokenType.CREATE:
            return self._parse_create_table()
        if tok.type == TokenType.INSERT:
            return self._parse_insert()
        if tok.type == TokenType.SELECT:
            return self._parse_select()
        if tok.type == TokenType.DELETE:
            return self._parse_delete()
        raise ParseError(
            f"Sentencia desconocida: '{tok.value}' en línea {tok.line}"
        )

    # ------------------------------------------------------------------
    # Reglas de la gramática
    # ------------------------------------------------------------------

    def _parse_create_table(self) -> CreateTableNode:
        """
        CREATE TABLE <nombre> (<col> <tipo> [INDEX <tecnica>], ...) [FROM FILE <path>]
        """
        self._expect(TokenType.CREATE)
        self._expect(TokenType.TABLE)
        name = self._expect(TokenType.IDENTIFIER).value
        self._expect(TokenType.LEFT_PARENTHESIS)

        columns = []
        while True:
            col_name = self._expect(TokenType.IDENTIFIER).value
            col_type = self._read_column_type()

            index_type = None
            if self._peek().type == TokenType.INDEX:
                self._advance()
                index_type = self._read_index_type()

            columns.append({"name": col_name, "type": col_type, "index": index_type})

            if self._peek().type == TokenType.COMMA:
                self._advance()
            else:
                break

        self._expect(TokenType.RIGHT_PARENTHESIS)

        from_file = None
        if self._peek().type == TokenType.FROM:
            self._advance()
            self._expect(TokenType.FILE)
            from_file = self._expect(TokenType.STRING_LITERAL).value

        self._consume_optional(TokenType.SEMICOLON)
        return CreateTableNode(name, columns, from_file)

    def _parse_insert(self) -> InsertNode:
        """INSERT INTO <tabla> VALUES (<v1>, <v2>, ...)"""
        self._expect(TokenType.INSERT)
        self._expect(TokenType.INTO)
        name = self._expect(TokenType.IDENTIFIER).value
        self._expect(TokenType.VALUES)
        self._expect(TokenType.LEFT_PARENTHESIS)

        values = []
        while True:
            values.append(self._read_literal())
            if self._peek().type == TokenType.COMMA:
                self._advance()
            else:
                break

        self._expect(TokenType.RIGHT_PARENTHESIS)
        self._consume_optional(TokenType.SEMICOLON)
        return InsertNode(name, values)

    def _parse_select(self):
        """
        SELECT * FROM <tabla> WHERE <col>
            = <valor>
          | BETWEEN <v1> AND <v2>
          | IN (POINT(<x>,<y>), RADIUS <r>)
          | IN (POINT(<x>,<y>), K <k>)
        """
        self._expect(TokenType.SELECT)
        self._expect(TokenType.ASTERISK)
        self._expect(TokenType.FROM)
        table_name = self._expect(TokenType.IDENTIFIER).value
        self._expect(TokenType.WHERE)
        col = self._expect(TokenType.IDENTIFIER).value

        tok = self._peek()

        if tok.type == TokenType.EQUAL:
            self._advance()
            value = self._read_literal()
            self._consume_optional(TokenType.SEMICOLON)
            return SelectEqualNode(table_name, col, value)

        if tok.type == TokenType.BETWEEN:
            self._advance()
            begin = self._read_literal()
            self._expect(TokenType.AND)
            end = self._read_literal()
            self._consume_optional(TokenType.SEMICOLON)
            return SelectRangeNode(table_name, col, begin, end)

        if tok.type == TokenType.IN:
            self._advance()
            self._expect(TokenType.LEFT_PARENTHESIS)
            self._expect(TokenType.POINT)
            self._expect(TokenType.LEFT_PARENTHESIS)
            x = self._read_literal()
            self._expect(TokenType.COMMA)
            y = self._read_literal()
            self._expect(TokenType.RIGHT_PARENTHESIS)
            self._expect(TokenType.COMMA)

            next_tok = self._peek()

            if next_tok.type == TokenType.RADIUS:
                self._advance()
                r = self._read_literal()
                self._expect(TokenType.RIGHT_PARENTHESIS)
                self._consume_optional(TokenType.SEMICOLON)
                return SelectPointRadiusNode(table_name, col, (x, y), float(r))

            if next_tok.type == TokenType.K:
                self._advance()
                k = self._expect(TokenType.INTEGER_LITERAL).value
                self._expect(TokenType.RIGHT_PARENTHESIS)
                self._consume_optional(TokenType.SEMICOLON)
                return SelectKNNNode(table_name, col, (x, y), k)

            raise ParseError(
                f"Se esperaba RADIUS o K, se obtuvo '{next_tok.value}' "
                f"en línea {next_tok.line}"
            )

        raise ParseError(
            f"Operador WHERE desconocido: '{tok.value}' en línea {tok.line}"
        )

    def _parse_delete(self) -> DeleteNode:
        """DELETE FROM <tabla> WHERE <col> = <valor>"""
        self._expect(TokenType.DELETE)
        self._expect(TokenType.FROM)
        table_name = self._expect(TokenType.IDENTIFIER).value
        self._expect(TokenType.WHERE)
        col = self._expect(TokenType.IDENTIFIER).value
        self._expect(TokenType.EQUAL)
        value = self._read_literal()
        self._consume_optional(TokenType.SEMICOLON)
        return DeleteNode(table_name, col, value)

    # ------------------------------------------------------------------
    # Utilidades
    # ------------------------------------------------------------------

    def _read_literal(self):
        """Lee un valor literal: INTEGER, FLOAT o STRING."""
        tok = self._peek()
        if tok.type in (TokenType.INTEGER_LITERAL, TokenType.FLOAT_LITERAL, TokenType.STRING_LITERAL):
            return self._advance().value
        if tok.type == TokenType.TRUE_LITERAL:
            self._advance()
            return True
        if tok.type == TokenType.FALSE_LITERAL:
            self._advance()
            return False
        if tok.type == TokenType.DATE:
            self._advance()
            return self._expect(TokenType.STRING_LITERAL).value
        if tok.type == TokenType.TIME:
            self._advance()
            return self._expect(TokenType.STRING_LITERAL).value
        raise ParseError(
            f"Se esperaba un valor literal, se obtuvo '{tok.value}' "
            f"({tok.type.name}) en línea {tok.line}"
        )

    def _read_column_type(self) -> str:
        tok = self._peek()
        if tok.type == TokenType.INT_TYPE:
            self._advance()
            return "INT"
        if tok.type == TokenType.INTEGER_TYPE:
            self._advance()
            return "INTEGER"
        if tok.type == TokenType.SMALLINT:
            self._advance()
            return "SMALLINT"
        if tok.type == TokenType.BIGINT:
            self._advance()
            return "BIGINT"
        if tok.type == TokenType.REAL:
            self._advance()
            return "REAL"
        if tok.type == TokenType.DOUBLE:
            self._advance()
            self._expect(TokenType.PRECISION)
            return "DOUBLE PRECISION"
        if tok.type == TokenType.BOOLEAN:
            self._advance()
            return "BOOLEAN"
        if tok.type == TokenType.CHAR:
            self._advance()
            self._expect(TokenType.LEFT_PARENTHESIS)
            size = self._expect(TokenType.INTEGER_LITERAL).value
            self._expect(TokenType.RIGHT_PARENTHESIS)
            return f"CHAR({size})"
        if tok.type == TokenType.DATE:
            self._advance()
            return "DATE"
        if tok.type == TokenType.TIME:
            self._advance()
            return "TIME"
        raise ParseError(
            f"Se esperaba un tipo de dato, se obtuvo '{tok.value}' "
            f"({tok.type.name}) en línea {tok.line}"
        )

    def _read_index_type(self) -> str:
        tok = self._peek()
        if tok.type == TokenType.RTREE:
            self._advance()
            return "rtree"
        if tok.type == TokenType.BPLUS:
            self._advance()
            self._expect(TokenType.TREE)
            return "bplus"
        if tok.type == TokenType.EXTENDIBLE:
            self._advance()
            self._expect(TokenType.HASHING)
            return "hashing"
        if tok.type == TokenType.SEQUENTIAL:
            self._advance()
            self._expect(TokenType.FILE)
            return "sequential"
        raise ParseError(
            f"Se esperaba una técnica de índice válida, se obtuvo '{tok.value}' "
            f"({tok.type.name}) en línea {tok.line}"
        )

    def _expect(self, token_type: TokenType) -> Token:
        tok = self._peek()
        if tok.type != token_type:
            raise ParseError(
                f"Se esperaba {token_type.name}, "
                f"se obtuvo '{tok.value}' ({tok.type.name}) en línea {tok.line}"
            )
        return self._advance()

    def _consume_optional(self, token_type: TokenType) -> None:
        if self._peek().type == token_type:
            self._advance()

    def _peek(self) -> Token:
        return self.tokens[self.pos]

    def _advance(self) -> Token:
        tok = self.tokens[self.pos]
        if tok.type != TokenType.EOF:
            self.pos += 1
        return tok
