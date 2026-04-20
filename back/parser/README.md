# Parser

Este módulo reúne el estado actual del parser del proyecto. Su responsabilidad es transformar una consulta SQL del subconjunto definido por el equipo en tokens válidos y luego en nodos AST consumibles por el resto del sistema.

Pruebas manuales del lexer y parser:

```powershell
python -m back.parser.__init__
```

## Análisis Léxico

El análisis léxico está implementado en `lexical_analizer.py`. Su trabajo es recorrer la consulta carácter por carácter, validar que cada símbolo pertenezca al alfabeto aceptado por el proyecto y generar la secuencia de tokens que utilizará el parser.

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

El análisis sintáctico está implementado en `parser.py` mediante un parser descendente recursivo. Su entrada es la lista de tokens producida por `LexicalAnalizer`, y su salida es un nodo del AST definido en `ast_nodes.py`.

En la estructura actual del módulo:

- `parser.py` conserva la API pública `Parser`
- `Parser` mantiene la consulta recibida en `__init__` y ejecuta todo el pipeline en `parse()`
- `LexicalAnalizer` recibe la consulta en `tokenize(sql)`
- `syntactic_analyzer.py` concentra las reglas del análisis sintáctico
- `SyntacticAnalyzer` recibe la lista de tokens en `parse(tokens)` y encapsula su excepción interna
- `parser.py` traduce los errores sintácticos internos a `ParseError` para conservar la API pública estable
- `semantic_analyzer.py` ejecuta la validación semántica posterior sobre el AST

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

La verificación semántica se encuentra en una primera etapa de implementación. Actualmente existe una revisión semántica inicial sobre el AST, sin depender todavía del motor de almacenamiento.

Por el momento, el parser valida estructura y forma de los tokens, y además puede ejecutar una primera capa de validaciones semánticas que dependen únicamente del AST y de la definición local de la consulta.

Restricciones semánticas implementadas actualmente:

- Verificar que no existan nombres de columna repetidos dentro de una misma tabla
- Verificar que `CHAR(n)` use un tamaño entero positivo mayor que cero
- Verificar que `BETWEEN` reciba dos literales comparables entre sí
- Verificar que `K` reciba un entero positivo en búsquedas `IN (POINT(...), K ...)`
- Verificar que `RADIUS` reciba un valor numérico positivo
- Verificar que `POINT(x, y)` reciba coordenadas numéricas
- Verificar que una declaración `FROM FILE` use un `STRING_LITERAL` no vacío
- Verificar formato semántico básico de literales `DATE 'yyyy-mm-dd'` y `TIME 'hh:mm:ss'`

Restricciones cubiertas actualmente por el análisis sintáctico:

- Verificar que `CREATE TABLE` defina al menos una columna
- Verificar que una técnica de índice compuesta esté completa y sea coherente con la gramática aceptada
- Verificar que `DELETE` y `SELECT` usen operadores permitidos para el subconjunto SQL definido

Restricciones semánticas que dependen de un motor funcional:

- Verificar que la tabla referenciada exista realmente en la base de datos
- Verificar que las columnas referenciadas existan en el esquema persistido de la tabla
- Verificar que el número de valores de `INSERT` coincida con el esquema real almacenado
- Verificar tipos contra el esquema real de una tabla ya creada
- Verificar que los valores de `INSERT` tengan una cantidad compatible con las columnas declaradas cuando el análisis cuente con el esquema real de la tabla
- Verificar compatibilidad básica entre tipos declarados y literales cuando el esquema de la tabla esté disponible en memoria durante el análisis
- Verificar que no se intente crear una tabla con un nombre ya existente en el catálogo persistente
- Verificar que el archivo indicado en `FROM FILE` exista realmente y pueda abrirse
- Verificar que las columnas requeridas por un `RTREE` correspondan a un esquema espacial válido en el motor
- Verificar que la técnica de índice declarada sea compatible con las operaciones que luego se intenten ejecutar sobre la tabla
- Verificar claves duplicadas, integridad de clave primaria o conflictos de inserción
- Verificar restricciones apoyadas en datos almacenados, como búsquedas, borrados o rangos sobre registros realmente persistidos

En consecuencia, el estado actual del módulo debe interpretarse así:

- El análisis léxico está operativo
- El análisis sintáctico está operativo dentro del subconjunto definido
- La verificación semántica ya puede aplicarse sobre reglas que dependan del AST y del contexto inmediato
- La verificación semántica dependiente del estado real de la base debe esperar a que el motor y la persistencia estén completos
