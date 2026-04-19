from enum import Enum, auto


class TokenType(Enum):
    # Palabras clave
    CREATE = auto();  TABLE = auto();   FROM = auto();    FILE = auto()
    SELECT = auto();  WHERE = auto();   BETWEEN = auto(); AND = auto()
    INSERT = auto();  INTO = auto();    VALUES = auto()
    DELETE = auto();  INDEX = auto();   POINT = auto()
    RADIUS = auto();  IN = auto();      K = auto()
    # Literales
    IDENT = auto()      # nombres de tabla/columna
    INTEGER = auto()
    FLOAT = auto()
    STRING = auto()     # 'texto'
    # Símbolos
    LPAREN = auto();  RPAREN = auto()
    COMMA = auto();   SEMICOLON = auto()
    EQ = auto();      STAR = auto()
    # Control
    EOF = auto()


class Token:
    def __init__(self, type: TokenType, value, line: int):
        self.type = type
        self.value = value
        self.line = line

    def __repr__(self):
        return f"Token({self.type.name}, {self.value!r}, line={self.line})"


# Mapa de palabras reservadas → TokenType
_KEYWORDS: dict[str, TokenType] = {
    "CREATE": TokenType.CREATE,   "TABLE":  TokenType.TABLE,
    "FROM":   TokenType.FROM,     "FILE":   TokenType.FILE,
    "SELECT": TokenType.SELECT,   "WHERE":  TokenType.WHERE,
    "BETWEEN":TokenType.BETWEEN,  "AND":    TokenType.AND,
    "INSERT": TokenType.INSERT,   "INTO":   TokenType.INTO,
    "VALUES": TokenType.VALUES,   "DELETE": TokenType.DELETE,
    "INDEX":  TokenType.INDEX,    "POINT":  TokenType.POINT,
    "RADIUS": TokenType.RADIUS,   "IN":     TokenType.IN,
    "K":      TokenType.K,
}


class LexError(Exception):
    pass


class Lexer:
    """
    Tokenizador para el subconjunto SQL del proyecto.
    Input:  sql  cadena con la sentencia SQL
    Output: list[Token] vía tokenize()
    """

    def __init__(self, sql: str):
        self.sql = sql
        self.pos = 0
        self.line = 1

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------

    def tokenize(self) -> list:
        tokens = []
        while self.pos < len(self.sql):
            self._skip_whitespace()
            if self.pos >= len(self.sql):
                break
            tok = self._next_token()
            if tok is not None:
                tokens.append(tok)
        tokens.append(Token(TokenType.EOF, None, self.line))
        return tokens

    # ------------------------------------------------------------------
    # Métodos privados
    # ------------------------------------------------------------------

    def _skip_whitespace(self):
        while self.pos < len(self.sql) and self.sql[self.pos] in " \t\r\n":
            if self.sql[self.pos] == "\n":
                self.line += 1
            self.pos += 1

    def _next_token(self) -> Token:
        ch = self.sql[self.pos]

        # Símbolos de un carácter
        single = {
            "(": TokenType.LPAREN,
            ")": TokenType.RPAREN,
            ",": TokenType.COMMA,
            ";": TokenType.SEMICOLON,
            "=": TokenType.EQ,
            "*": TokenType.STAR,
        }
        if ch in single:
            self.pos += 1
            return Token(single[ch], ch, self.line)

        # Cadena entre comillas simples
        if ch == "'":
            return self._read_string()

        # Número (incluye negativos)
        if ch.isdigit() or (
            ch == "-"
            and self.pos + 1 < len(self.sql)
            and self.sql[self.pos + 1].isdigit()
        ):
            return self._read_number()

        # Identificador o palabra clave
        if ch.isalpha() or ch == "_":
            return self._read_ident_or_keyword()

        raise LexError(f"Carácter inesperado '{ch}' en línea {self.line}")

    def _read_string(self) -> Token:
        self.pos += 1  # saltar comilla de apertura
        start = self.pos
        while self.pos < len(self.sql) and self.sql[self.pos] != "'":
            self.pos += 1
        if self.pos >= len(self.sql):
            raise LexError(f"Cadena sin cerrar en línea {self.line}")
        value = self.sql[start : self.pos]
        self.pos += 1  # saltar comilla de cierre
        return Token(TokenType.STRING, value, self.line)

    def _read_number(self) -> Token:
        start = self.pos
        if self.sql[self.pos] == "-":
            self.pos += 1
        while self.pos < len(self.sql) and self.sql[self.pos].isdigit():
            self.pos += 1
        # Float si hay punto decimal
        if self.pos < len(self.sql) and self.sql[self.pos] == ".":
            self.pos += 1
            while self.pos < len(self.sql) and self.sql[self.pos].isdigit():
                self.pos += 1
            return Token(TokenType.FLOAT, float(self.sql[start : self.pos]), self.line)
        return Token(TokenType.INTEGER, int(self.sql[start : self.pos]), self.line)

    def _read_ident_or_keyword(self) -> Token:
        start = self.pos
        while self.pos < len(self.sql) and (
            self.sql[self.pos].isalnum() or self.sql[self.pos] == "_"
        ):
            self.pos += 1
        word = self.sql[start : self.pos]
        upper = word.upper()
        if upper in _KEYWORDS:
            return Token(_KEYWORDS[upper], upper, self.line)
        return Token(TokenType.IDENT, word, self.line)
