# Parser

Este módulo implementa el análisis léxico y sintáctico del subconjunto de SQL usado por el proyecto. Su responsabilidad es convertir una consulta de texto en una secuencia de tokens y luego en un nodo AST consumible por el motor de ejecución.

## Componentes

- `lexer.py`: tokeniza la consulta SQL.
- `parser.py`: aplica análisis sintáctico descendente recursivo.
- `ast_nodes.py`: define los nodos del árbol sintáctico abstracto.
- `__init__.py`: expone las clases principales y contiene pruebas manuales del lexer y parser.
- `documentation.txt`: documento base con la lista de instrucciones y la gramática de referencia.

## Instrucciones soportadas

El parser acepta actualmente las siguientes sentencias:

1. `CREATE TABLE <name> (<column> <type> [INDEX <technique>], ...) [FROM FILE <path>];`
2. `SELECT * FROM <table> WHERE <column> = <value>;`
3. `SELECT * FROM <table> WHERE <column> BETWEEN <value_1> AND <value_2>;`
4. `SELECT * FROM <table> WHERE <column> IN (POINT(<x>, <y>), RADIUS <r>);`
5. `SELECT * FROM <table> WHERE <column> IN (POINT(<x>, <y>), K <k>);`
6. `INSERT INTO <table> VALUES (...);`
7. `DELETE FROM <table> WHERE <column> = <value>;`

## Tipos de dato soportados

El proyecto trabaja con registros de longitud fija. Por esa razón, el subconjunto de SQL aceptado por el parser se limita a tipos de dato que pueden mapearse a una representación de tamaño fijo en almacenamiento. Esta decisión simplifica el manejo del esquema, el cálculo del tamaño de registro y la serialización en disco.

| Tipo de dato | Descripción | Tamaño fijo |
| --- | --- | --- |
| `INTEGER` / `INT` | Entero de propósito general | 4 bytes |
| `SMALLINT` | Entero pequeño | 2 bytes |
| `BIGINT` | Entero grande | 8 bytes |
| `REAL` | Número de punto flotante | 4 bytes |
| `DOUBLE PRECISION` | Número de punto flotante doble | 8 bytes |
| `BOOLEAN` | Valor lógico verdadero o falso | 1 byte |
| `CHAR(n)` | Cadena de longitud fija | `n` bytes |
| `DATE` | Fecha sin componente de hora | 4 bytes |
| `TIME` | Hora sin componente de fecha | 8 bytes |

## Técnicas de índice soportadas

Las técnicas de índice se expresan como combinaciones de keywords:

- `RTREE`
- `BPLUS TREE`
- `EXTENDIBLE HASHING`
- `SEQUENTIAL FILE`

## Literales soportados

El parser reconoce los siguientes valores literales:

- enteros
- flotantes
- cadenas entre comillas simples
- booleanos: `TRUE`, `FALSE`
- fecha tipada: `DATE 'yyyy-mm-dd'`
- hora tipada: `TIME 'hh:mm:ss'`

## Convenciones actuales

- El path en `FROM FILE` debe escribirse entre comillas simples.
- El lexer acepta nombres de tabla y columna con el patrón `identifier ::= [A-Za-z_][A-Za-z0-9_]*`.
- La validación de `DATE` y `TIME` es sintáctica. Por ahora, el parser exige la forma `DATE <string>` y `TIME <string>`, pero no valida todavía el formato semántico interno.

## Gramática de referencia

La gramática base usada en este módulo es la siguiente. Puede ajustarse más adelante según evolucione el parser.

```ebnf
statement ::= create_stmt | select_stmt | insert_stmt | delete_stmt

create_stmt ::= CREATE TABLE <identifier> ( <column_list> ) [ FROM FILE <string_literal> ] ;
column_list ::= <column_def> ( , <column_def> )*
column_def  ::= <identifier> <data_type> [ INDEX <index_type> ]
data_type   ::= INT
             | INTEGER
             | SMALLINT
             | BIGINT
             | REAL
             | DOUBLE PRECISION
             | BOOLEAN
             | CHAR ( <integer_literal> )
             | DATE
             | TIME
index_type  ::= SEQUENTIAL FILE | EXTENDIBLE HASHING | BPLUS TREE | RTREE

select_stmt ::= SELECT * FROM <identifier> WHERE <identifier> = <literal> ;
select_stmt ::= SELECT * FROM <identifier> WHERE <identifier> BETWEEN <literal> AND <literal> ;
select_stmt ::= SELECT * FROM <identifier> WHERE <identifier> IN ( POINT ( <literal> , <literal> ) , RADIUS <literal> ) ;
select_stmt ::= SELECT * FROM <identifier> WHERE <identifier> IN ( POINT ( <literal> , <literal> ) , K <literal> ) ;

insert_stmt ::= INSERT INTO <identifier> VALUES ( <literal> ( , <literal> )* ) ;

delete_stmt ::= DELETE FROM <identifier> WHERE <identifier> = <literal> ;
```

## Ejemplos válidos

```sql
CREATE TABLE users (
    id INT INDEX BPLUS TREE,
    active BOOLEAN,
    salary DOUBLE PRECISION,
    created_at DATE,
    created_time TIME
) FROM FILE 'data.csv';

SELECT * FROM users WHERE id = 100;
SELECT * FROM users WHERE id BETWEEN 10 AND 20;
SELECT * FROM users WHERE location IN (POINT(12.5, 7.8), RADIUS 3.2);
SELECT * FROM users WHERE location IN (POINT(12.5, 7.8), K 5);

INSERT INTO users VALUES (TRUE, DATE '2026-04-19', TIME '10:30:00');

DELETE FROM users WHERE id = 100;
```

## Pruebas manuales

El archivo `back/parser/__init__.py` contiene pruebas manuales para lexer y parser. Para ejecutarlas desde la raíz del proyecto:

```powershell
python -m back.parser.__init__
```

## Estado actual

- El análisis léxico está operativo con la sintaxis acordada.
- El parser ya reconoce `CREATE TABLE`, `SELECT`, `INSERT` y `DELETE` dentro del subconjunto definido.
- El backend compila correctamente después de los cambios recientes.
- La gramática documentada aquí debe considerarse una referencia viva y puede ajustarse cuando continúe el trabajo del análisis sintáctico.
