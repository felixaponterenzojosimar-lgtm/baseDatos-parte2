from .lexer import Lexer, Token, TokenType, LexError
from .parser import Parser, ParseError
from .ast_nodes import (
    CreateTableNode, InsertNode, SelectEqualNode, SelectRangeNode,
    SelectPointRadiusNode, SelectKNNNode, DeleteNode,
)


if __name__ == "__main__":
    lexer_valid_examples = [
        "CREATE TABLE single_column (id INT);",
        "CREATE TABLE single_indexed_column (id INT INDEX RTREE);",
        "CREATE TABLE two_columns_no_index (id INT, created_at DATE);",
        "CREATE TABLE mixed_indexes (id INT INDEX BPLUS TREE, active BOOLEAN, score REAL INDEX SEQUENTIAL FILE);",
        "CREATE TABLE many_columns (id INT INDEX BPLUS TREE, age SMALLINT, salary DOUBLE PRECISION, active BOOLEAN, code CHAR(8), created_at DATE, created_time TIME) FROM FILE 'data.csv';",
        "CREATE TABLE no_indexes (id INTEGER, name CHAR(12), birth_date DATE, login_time TIME);",
        "SELECT * FROM users WHERE id = 100;",
        "SELECT * FROM users WHERE id BETWEEN 10 AND 20;",
        "SELECT * FROM users WHERE location IN (POINT(12.5, 7.8), RADIUS 3.2);",
        "SELECT * FROM users WHERE location IN (POINT(12.5, 7.8), K 5);",
        "INSERT INTO users VALUES (1, 12.5, 7.8);",
        "INSERT INTO users VALUES (TRUE, DATE '2026-04-19', TIME '10:30:00');",
        "DELETE FROM users WHERE id = 100;",
    ]

    lexer_rejected_examples = [
        "CREATE TABLE users (id INT, name CHAR(10)) @ FROM FILE 'data.csv';",
        "SELECT * FROM users WHERE id = 100 #;",
        "INSERT INTO users VALUES (1, 12.5, 7.8$);",
        "DELETE FROM users WHERE id = 10 ?;",
    ]

    parser_valid_examples = [
        "CREATE TABLE single_column (id INT);",
        "CREATE TABLE single_indexed_column (id INT INDEX RTREE);",
        "CREATE TABLE mixed_indexes (id INT INDEX BPLUS TREE, active BOOLEAN, score REAL INDEX SEQUENTIAL FILE);",
        "CREATE TABLE many_columns (id INT INDEX BPLUS TREE, age SMALLINT, salary DOUBLE PRECISION, active BOOLEAN, code CHAR(8), created_at DATE, created_time TIME) FROM FILE 'data.csv';",
        "SELECT * FROM users WHERE id = 100;",
        "SELECT * FROM users WHERE id BETWEEN 10 AND 20;",
        "SELECT * FROM users WHERE location IN (POINT(12.5, 7.8), RADIUS 3.2);",
        "SELECT * FROM users WHERE location IN (POINT(12.5, 7.8), K 5);",
        "INSERT INTO users VALUES (1, 12.5, 7.8);",
        "INSERT INTO users VALUES (TRUE, DATE '2026-04-19', TIME '10:30:00');",
        "DELETE FROM users WHERE id = 100;",
    ]

    parser_rejected_examples = [
        "CREATE TABLE empty_table ();",
        "CREATE TABLE missing_type (id);",
        "CREATE TABLE broken_columns (id INT, );",
        "CREATE TABLE bad_char_float (code CHAR(3.5));",
        "CREATE TABLE bad_char_empty (code CHAR());",
        "CREATE TABLE bad_char_text (code CHAR(text));",
        "CREATE TABLE bad_double_only (amount DOUBLE);",
        "CREATE TABLE bad_precision_only (amount PRECISION);",
        "CREATE TABLE bad_extendible_only (id INT INDEX EXTENDIBLE);",
        "CREATE TABLE bad_sequential_only (id INT INDEX SEQUENTIAL);",
        "CREATE TABLE bad_bplus_only (id INT INDEX BPLUS);",
        "CREATE TABLE bad_file_path (id INT) FROM FILE data.csv;",
    ]

    print("PRUEBAS DE LEXER Y PARSER")
    print("")
    print("LEXER")
    print("")
    print("CASOS VALIDOS")

    lexer_valid_passed = 0
    for sql in lexer_valid_examples:
        try:
            tokens = Lexer(sql).tokenize()
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
            tokens = Lexer(sql).tokenize()
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
        except (LexError, ParseError) as error:
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
        except (LexError, ParseError) as error:
            parser_rejected_passed += 1
            print(f"[OK] {sql}")
            print(f"{type(error).__name__}: {error}")
        print("")

    print("RESUMEN PARSER")
    print(f"Validos parseados: {parser_valid_passed}/{len(parser_valid_examples)}")
    print(f"Rechazados por parser: {parser_rejected_passed}/{len(parser_rejected_examples)}")
