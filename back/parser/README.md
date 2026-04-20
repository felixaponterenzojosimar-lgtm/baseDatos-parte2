# Parser

Este módulo reúne el estado actual del parser del proyecto. Su responsabilidad es transformar una consulta SQL del subconjunto definido por el equipo en tokens válidos y luego en nodos AST consumibles por el resto del sistema.

Pruebas manuales del lexer y parser:

```powershell
python -m back.parser.__init__
```

## Análisis Léxico

El análisis léxico está implementado en `lexer.py`. Su trabajo es recorrer la consulta carácter por carácter, validar que cada símbolo pertenezca al alfabeto aceptado por el proyecto y generar la secuencia de tokens que utilizará el parser.

Actualmente el lexer reconoce:

- Sentencias `CREATE TABLE`, `SELECT`, `INSERT` y `DELETE`
- Identificadores de tablas y columnas con la forma `[A-Za-z_][A-Za-z0-9_]*`
- Literales enteros, flotantes, cadenas entre comillas simples y booleanos
- Literales tipados para `DATE` y `TIME` en la forma `DATE 'yyyy-mm-dd'` y `TIME 'hh:mm:ss'`
- Delimitadores `(`, `)`, `,`, `;` y `*`
- Operadores `=`, `<`, `>`, `<=`, `>=`, `BETWEEN`, `AND`, `IN`
- Técnicas de índice expresadas como combinaciones de keywords: `RTREE`, `BPLUS TREE`, `EXTENDIBLE HASHING` y `SEQUENTIAL FILE`

El lexer también soporta los tipos de datos de longitud fija acordados para el proyecto. Esta restricción se mantiene porque la capa de almacenamiento trabaja con registros de tamaño fijo.

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

Notas actuales del lexer:

- Toda consulta debe terminar con punto y coma, por medio del token `SEMICOLON`
- El path de `FROM FILE` debe escribirse como `STRING_LITERAL`
- El lexer rechaza caracteres inesperados antes de intentar tokenizar

## Análisis Sintáctico

El análisis sintáctico está implementado en `parser.py` mediante un parser descendente recursivo. Su entrada es la lista de tokens producida por `Lexer`, y su salida es un nodo del AST definido en `ast_nodes.py`.

Sentencias soportadas en el estado actual:

1. `CREATE TABLE <name> (<column> <type> [INDEX <technique>], ...) [FROM FILE <path>];`
2. `SELECT * FROM <table> WHERE <column> = <value>;`
3. `SELECT * FROM <table> WHERE <column> <comparison_operator> <value>;`
4. `SELECT * FROM <table> WHERE <column> BETWEEN <value_1> AND <value_2>;`
5. `SELECT * FROM <table> WHERE <column> IN (POINT(<x>, <y>), RADIUS <r>);`
6. `SELECT * FROM <table> WHERE <column> IN (POINT(<x>, <y>), K <k>);`
7. `INSERT INTO <table> VALUES (...);`
8. `DELETE FROM <table> WHERE <column> = <value>;`

Reglas sintácticas ya consolidadas:

- Cada entrada del parser contiene una sola consulta
- El punto y coma final es obligatorio
- `CREATE TABLE` acepta `FROM FILE` solo con una cadena entre comillas simples
- `DELETE` solo acepta comparación por igualdad
- `SELECT` acepta `=`, `<`, `>`, `<=`, `>=`, `BETWEEN` y las dos variantes espaciales con `POINT`

Nodos AST actualmente definidos:

- `CreateTableNode`
- `InsertNode`
- `SelectEqualNode`
- `SelectComparisonNode`
- `SelectRangeNode`
- `SelectPointRadiusNode`
- `SelectKNNNode`
- `DeleteNode`

## Verificación Semántica

La verificación semántica todavía no está implementada. Esta fase sigue en proceso y se abordará después de cerrar la etapa sintáctica.

Por el momento, el parser solo valida estructura y forma de los tokens. Todavía no resuelve reglas semánticas como:

- Compatibilidad entre tipos de datos y valores
- Validación real del formato interno de `DATE` y `TIME`
- Restricciones sobre qué columnas pueden participar en ciertas búsquedas
- Coherencia entre la técnica de índice declarada y el uso posterior en ejecución
- Validación de existencia de tablas, columnas o archivos

En consecuencia, el estado actual del módulo debe interpretarse así:

- El análisis léxico está operativo
- El análisis sintáctico está operativo dentro del subconjunto definido
- La verificación semántica sigue pendiente de implementación
