from .lexical_analizer import LexicalAnalizer, Token, TokenType, LexError
from .parser import Parser, ParseError
from .semantic_analyzer import SemanticAnalyzer, SemanticError
from .ast_nodes import (
    CreateTableNode, CreateIndexNode, DateLiteralNode, TimeLiteralNode, InsertNode,
    SelectEqualNode, SelectComparisonNode, SelectRangeNode, SelectPointRadiusNode,
    SelectKNNNode, DeleteNode, DropTableNode, DropIndexNode,
)


if __name__ == "__main__":
    lexer_valid_examples = [
        "CREATE TABLE users (id INT PRIMARY KEY, name CHAR(10));",
        "CREATE TABLE users_hash (id INT PRIMARY KEY USING EXTENDIBLE HASHING, name CHAR(10));",
        "CREATE TABLE places (id INT PRIMARY KEY, lat REAL, lon REAL) FROM FILE 'data.csv';",
        "CREATE INDEX idx_users_id ON users (id) USING BPLUS TREE;",
        "CREATE INDEX idx_users_name ON users (name) USING EXTENDIBLE HASHING;",
        "CREATE INDEX idx_users_created_at ON users (created_at) USING SEQUENTIAL FILE;",
        "CREATE INDEX idx_places_coords ON places (lat, lon) USING RTREE;",
        "DROP TABLE users;",
        "DROP INDEX idx_users_id ON users;",
        "SELECT * FROM users WHERE id = 100;",
        "SELECT * FROM users WHERE id >= 100;",
        "SELECT * FROM users WHERE id BETWEEN 10 AND 20;",
        "SELECT * FROM users WHERE location IN (POINT(12.5, 7.8), RADIUS 3.2);",
        "SELECT * FROM users WHERE location IN (POINT(12.5, 7.8), K 5);",
        "INSERT INTO users VALUES (1, 12.5, 7.8);",
        "INSERT INTO users VALUES ('Farfetchd''s leek');",
        "INSERT INTO users VALUES (TRUE, DATE '2026-04-19', TIME '10:30:00');",
        "SELECT * FROM users WHERE created_at = DATE '2026-04-19';",
        "SELECT * FROM users WHERE created_time = TIME '10:30:00';",
        "DELETE FROM users WHERE id = 100;",
    ]

    lexer_rejected_examples = [
        "CREATE TABLE users (id INT PRIMARY KEY, name CHAR(10)) @ FROM FILE 'data.csv';",
        "SELECT * FROM users WHERE id = 100 #;",
        "INSERT INTO users VALUES (1, 12.5, 7.8$);",
        "DELETE FROM users WHERE id = 10 ?;",
    ]

    parser_valid_examples = [
        "CREATE TABLE users (id INT PRIMARY KEY);",
        "CREATE TABLE users_hash (id INT PRIMARY KEY USING EXTENDIBLE HASHING, name CHAR(10));",
        "CREATE TABLE users_seq (id INT PRIMARY KEY USING SEQUENTIAL FILE, name CHAR(10));",
        "CREATE TABLE users_bplus (id INT PRIMARY KEY USING BPLUS TREE, name CHAR(10));",
        "CREATE TABLE users (id INT PRIMARY KEY, name CHAR(10), created_at DATE) FROM FILE 'data.csv';",
        "CREATE INDEX idx_users_id ON users (id) USING BPLUS TREE;",
        "CREATE INDEX idx_users_name ON users (name) USING EXTENDIBLE HASHING;",
        "CREATE INDEX idx_users_created_at ON users (created_at) USING SEQUENTIAL FILE;",
        "CREATE INDEX idx_places_coords ON places (lat, lon) USING RTREE;",
        "DROP TABLE users;",
        "DROP INDEX idx_users_id ON users;",
        "SELECT * FROM users WHERE id = 100;",
        "SELECT * FROM users WHERE id >= 100;",
        "SELECT * FROM users WHERE id BETWEEN 10 AND 20;",
        "SELECT * FROM users WHERE location IN (POINT(12.5, 7.8), RADIUS 3.2);",
        "SELECT * FROM users WHERE location IN (POINT(12.5, 7.8), K 5);",
        "INSERT INTO users VALUES (1, 12.5, 7.8);",
        "INSERT INTO users VALUES ('Farfetchd''s leek');",
        "INSERT INTO users VALUES (TRUE, DATE '2026-04-19', TIME '10:30:00');",
        "SELECT * FROM users WHERE created_at = DATE '2026-04-19';",
        "SELECT * FROM users WHERE created_time = TIME '10:30:00';",
        "DELETE FROM users WHERE id = 100;",
    ]

    parser_rejected_examples = [
        "CREATE TABLE empty_table ();",
        "CREATE TABLE missing_type (id);",
        "CREATE TABLE broken_columns (id INT PRIMARY KEY, );",
        "CREATE TABLE bad_char_float (id INT PRIMARY KEY, code CHAR(3.5));",
        "CREATE TABLE bad_char_empty (id INT PRIMARY KEY, code CHAR());",
        "CREATE TABLE bad_char_text (id INT PRIMARY KEY, code CHAR(text));",
        "CREATE TABLE bad_double_only (id INT PRIMARY KEY, amount DOUBLE);",
        "CREATE TABLE bad_precision_only (id INT PRIMARY KEY, amount PRECISION);",
        "CREATE TABLE missing_key_keyword (id INT PRIMARY);",
        "CREATE TABLE bad_primary_rtree (id INT PRIMARY KEY USING RTREE, name CHAR(10));",
        "CREATE TABLE bad_primary_using_missing (id INT PRIMARY KEY USING, name CHAR(10));",
        "CREATE TABLE bad_file_path (id INT PRIMARY KEY) FROM FILE data.csv;",
        "CREATE INDEX ON users (id) USING BPLUS TREE;",
        "CREATE INDEX idx_users_empty ON users () USING BPLUS TREE;",
        "CREATE INDEX idx_users_trailing ON users (id,) USING BPLUS TREE;",
        "CREATE INDEX idx_users_bad_syntax ON users (id) BPLUS TREE;",
        "DROP users;",
        "DROP INDEX idx_users_id users;",
        "DROP INDEX ON users;",
        "SELECT * FROM users WHERE id = 100",
        "INSERT INTO users VALUES (1, 12.5, 7.8)",
        "DELETE FROM users WHERE id = 100",
    ]

    semantic_valid_examples = [
        "CREATE TABLE semantic_ok (id INT PRIMARY KEY, code CHAR(8));",
        "CREATE TABLE semantic_hash (id INT PRIMARY KEY USING EXTENDIBLE HASHING, code CHAR(8));",
        "CREATE TABLE semantic_seq (id INT PRIMARY KEY USING SEQUENTIAL FILE, code CHAR(8));",
        "CREATE TABLE semantic_bplus (id INT PRIMARY KEY USING BPLUS TREE, code CHAR(8));",
        "CREATE TABLE semantic_file (id INT PRIMARY KEY) FROM FILE 'data.csv';",
        "CREATE INDEX idx_users_id ON users (id) USING BPLUS TREE;",
        "CREATE INDEX idx_users_created_at ON users (created_at) USING SEQUENTIAL FILE;",
        "CREATE INDEX idx_places_coords ON places (lat, lon) USING RTREE;",
        "DROP TABLE users;",
        "DROP INDEX idx_users_id ON users;",
        "SELECT * FROM users WHERE id BETWEEN 10 AND 20;",
        "SELECT * FROM users WHERE created_at = DATE '2026-04-19';",
        "SELECT * FROM users WHERE created_at = DATE '2024-02-29';",
        "SELECT * FROM users WHERE created_time = TIME '10:30:00';",
        "SELECT * FROM users WHERE location IN (POINT(12.5, 7.8), RADIUS 3.2);",
        "SELECT * FROM users WHERE location IN (POINT(12.5, 7.8), K 5);",
    ]

    semantic_rejected_examples = [
        "CREATE TABLE duplicated_columns (id INT PRIMARY KEY, id REAL);",
        "CREATE TABLE bad_char_zero (id INT PRIMARY KEY, code CHAR(0));",
        "CREATE TABLE missing_primary_key (id INT, code CHAR(8));",
        "CREATE TABLE two_primary_keys (id INT PRIMARY KEY, code INT PRIMARY KEY);",
        "CREATE TABLE empty_file_path (id INT PRIMARY KEY) FROM FILE '';",
        "CREATE INDEX idx_users_two_cols ON users (id, name) USING BPLUS TREE;",
        "CREATE INDEX idx_users_rtree_one ON users (lat) USING RTREE;",
        "CREATE INDEX idx_users_rtree_dup ON users (lat, lat) USING RTREE;",
        "SELECT * FROM users WHERE id BETWEEN 20 AND 10;",
        "SELECT * FROM users WHERE id BETWEEN 10 AND '20';",
        "SELECT * FROM users WHERE created_at = DATE '2026-13-19';",
        "SELECT * FROM users WHERE created_at = DATE '2026-04';",
        "SELECT * FROM users WHERE created_at = DATE '2026-02-29';",
        "SELECT * FROM users WHERE created_at = DATE '2025-04-31';",
        "SELECT * FROM users WHERE created_time = TIME '25:30:00';",
        "SELECT * FROM users WHERE created_time = TIME '10:70:00';",
        "SELECT * FROM users WHERE created_time = TIME '10:30';",
        "SELECT * FROM users WHERE location IN (POINT('north', 7.8), RADIUS 3.2);",
        "SELECT * FROM users WHERE location IN (POINT(12.5, 7.8), RADIUS 0);",
        "SELECT * FROM users WHERE location IN (POINT(12.5, 7.8), K 0);",
    ]

    print("PRUEBAS DE LEXER Y PARSER")
    print("")
    print("LEXER")
    print("")
    print("CASOS VALIDOS")

    lexer_valid_passed = 0
    for sql in lexer_valid_examples:
        try:
            tokens = LexicalAnalizer().tokenize(sql)
            lexer_valid_passed += 1
            print(f"[OK] {sql}")
            print("TOKENS:", [token.type.name for token in tokens])
        except LexError as error:
            print(f"[ERROR] {sql}")
            print(f"LexError: {error}")
        print("")

    print("CASOS RECHAZADOS")

    lexer_rejected_passed = 0
    for sql in lexer_rejected_examples:
        try:
            tokens = LexicalAnalizer().tokenize(sql)
            print(f"[NO RECHAZADO] {sql}")
            print("TOKENS:", [token.type.name for token in tokens])
        except LexError as error:
            lexer_rejected_passed += 1
            print(f"[OK] {sql}")
            print(f"LexError: {error}")
        print("")

    print("RESUMEN LEXER")
    print(f"Validos tokenizados: {lexer_valid_passed}/{len(lexer_valid_examples)}")
    print(f"Rechazados por lexer: {lexer_rejected_passed}/{len(lexer_rejected_examples)}")
    print("RESUMEN")
    print("")
    print("PARSER")
    print("")
    print("CASOS VALIDOS")

    parser_valid_passed = 0
    for sql in parser_valid_examples:
        try:
            node = Parser(sql).parse()
            parser_valid_passed += 1
            print(f"[OK] {sql}")
            print("AST:", type(node).__name__)
        except (LexError, ParseError, SemanticError) as error:
            print(f"[ERROR] {sql}")
            print(f"{type(error).__name__}: {error}")
        print("")

    print("CASOS RECHAZADOS")

    parser_rejected_passed = 0
    for sql in parser_rejected_examples:
        try:
            node = Parser(sql).parse()
            print(f"[NO RECHAZADO] {sql}")
            print("AST:", type(node).__name__)
        except (LexError, ParseError, SemanticError) as error:
            parser_rejected_passed += 1
            print(f"[OK] {sql}")
            print(f"{type(error).__name__}: {error}")
        print("")

    print("RESUMEN PARSER")
    print(f"Validos parseados: {parser_valid_passed}/{len(parser_valid_examples)}")
    print(f"Rechazados por parser: {parser_rejected_passed}/{len(parser_rejected_examples)}")
    print("")
    print("SEMANTICA")
    print("")
    print("CASOS VALIDOS")

    semantic_valid_passed = 0
    for sql in semantic_valid_examples:
        try:
            node = Parser(sql).parse()
            semantic_valid_passed += 1
            print(f"[OK] {sql}")
            print("AST:", type(node).__name__)
        except (LexError, ParseError, SemanticError) as error:
            print(f"[ERROR] {sql}")
            print(f"{type(error).__name__}: {error}")
        print("")

    print("CASOS RECHAZADOS")

    semantic_rejected_passed = 0
    for sql in semantic_rejected_examples:
        try:
            node = Parser(sql).parse()
            print(f"[NO RECHAZADO] {sql}")
            print("AST:", type(node).__name__)
        except (LexError, ParseError, SemanticError) as error:
            semantic_rejected_passed += 1
            print(f"[OK] {sql}")
            print(f"{type(error).__name__}: {error}")
        print("")

    print("RESUMEN SEMANTICA")
    print(f"Validos aceptados: {semantic_valid_passed}/{len(semantic_valid_examples)}")
    print(f"Rechazados por semantica: {semantic_rejected_passed}/{len(semantic_rejected_examples)}")
