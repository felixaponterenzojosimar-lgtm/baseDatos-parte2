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
        name = self._expect(TokenType.IDENT).value
        self._expect(TokenType.LPAREN)

        columns = []
        while True:
            col_name = self._expect(TokenType.IDENT).value

            # tipo puede ser INT, FLOAT, BOOL, VARCHAR — VARCHAR va seguido de (n)
            col_type_tok = self._expect(TokenType.IDENT)
            col_type = col_type_tok.value.upper()

            if col_type == "VARCHAR":
                self._expect(TokenType.LPAREN)
                size = self._expect(TokenType.INTEGER).value
                self._expect(TokenType.RPAREN)
                col_type = f"VARCHAR({size})"

            index_type = None
            if self._peek().type == TokenType.INDEX:
                self._advance()
                index_type = self._expect(TokenType.IDENT).value.lower()

            columns.append({"name": col_name, "type": col_type, "index": index_type})

            if self._peek().type == TokenType.COMMA:
                self._advance()
            else:
                break

        self._expect(TokenType.RPAREN)

        from_file = None
        if self._peek().type == TokenType.FROM:
            self._advance()
            self._expect(TokenType.FILE)
            from_file = self._expect(TokenType.STRING).value

        self._consume_optional(TokenType.SEMICOLON)
        return CreateTableNode(name, columns, from_file)

    def _parse_insert(self) -> InsertNode:
        """INSERT INTO <tabla> VALUES (<v1>, <v2>, ...)"""
        self._expect(TokenType.INSERT)
        self._expect(TokenType.INTO)
        name = self._expect(TokenType.IDENT).value
        self._expect(TokenType.VALUES)
        self._expect(TokenType.LPAREN)

        values = []
        while True:
            values.append(self._read_literal())
            if self._peek().type == TokenType.COMMA:
                self._advance()
            else:
                break

        self._expect(TokenType.RPAREN)
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
        self._expect(TokenType.STAR)
        self._expect(TokenType.FROM)
        table_name = self._expect(TokenType.IDENT).value
        self._expect(TokenType.WHERE)
        col = self._expect(TokenType.IDENT).value

        tok = self._peek()

        if tok.type == TokenType.EQ:
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
            self._expect(TokenType.LPAREN)
            self._expect(TokenType.POINT)
            self._expect(TokenType.LPAREN)
            x = self._read_literal()
            self._expect(TokenType.COMMA)
            y = self._read_literal()
            self._expect(TokenType.RPAREN)
            self._expect(TokenType.COMMA)

            next_tok = self._peek()

            if next_tok.type == TokenType.RADIUS:
                self._advance()
                r = self._read_literal()
                self._expect(TokenType.RPAREN)
                self._consume_optional(TokenType.SEMICOLON)
                return SelectPointRadiusNode(table_name, col, (x, y), float(r))

            if next_tok.type == TokenType.K:
                self._advance()
                k = self._expect(TokenType.INTEGER).value
                self._expect(TokenType.RPAREN)
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
        table_name = self._expect(TokenType.IDENT).value
        self._expect(TokenType.WHERE)
        col = self._expect(TokenType.IDENT).value
        self._expect(TokenType.EQ)
        value = self._read_literal()
        self._consume_optional(TokenType.SEMICOLON)
        return DeleteNode(table_name, col, value)

    # ------------------------------------------------------------------
    # Utilidades
    # ------------------------------------------------------------------

    def _read_literal(self):
        """Lee un valor literal: INTEGER, FLOAT o STRING."""
        tok = self._peek()
        if tok.type in (TokenType.INTEGER, TokenType.FLOAT, TokenType.STRING):
            return self._advance().value
        raise ParseError(
            f"Se esperaba un valor literal, se obtuvo '{tok.value}' "
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
