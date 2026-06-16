# Esquema de datos – Base de datos legislativa CE

## Decisiones de diseño

### Por qué un esquema propio (`legislacion`)

Se crea el esquema `legislacion` separado de `public` y `sales` para aislar el dominio jurídico del resto del proyecto. Permite añadir futuras leyes sin interferir con otros datos.

### Jerarquía legislativa modelada

La Constitución Española tiene esta estructura jerárquica real:

```
Ley
 └── Título          (11 en la CE: Preliminar + I al X)
       └── Capítulo  (opcional — solo en Títulos I, III y VIII)
             └── Sección  (opcional — solo en Título I, Capítulo Segundo)
                   └── Artículo / Disposición
```

Los capítulos y secciones son **nullable** en `articulos` para permitir artículos que pertenecen directamente a un título (p.ej. todos los artículos del Título II).

### Por qué una sola tabla para artículos y disposiciones

El preámbulo, los 169 artículos y las 15 disposiciones son estructuralmente idénticos: una unidad de texto con ubicación en la jerarquía. El campo `tipo` diferencia entre ellos y permite filtrar o agrupar según el uso.

### Dimensión del vector de embeddings

Se usa `vector(1536)` para ser compatible con `text-embedding-3-small` de OpenAI (el modelo de embeddings más eficiente en coste/calidad para texto jurídico en español). El índice HNSW con similitud coseno es el estándar para búsqueda semántica en pgvector.

---

## Tablas

### `legislacion.leyes`

Metadatos de la ley fuente. Permite escalar el módulo a otras leyes (ET, LOPD, etc.) sin cambiar el esquema.

| Columna    | Tipo    | Restricción       | Descripción                         |
|------------|---------|-------------------|-------------------------------------|
| ley_id     | serial  | PK                | Identificador interno               |
| codigo     | text    | NOT NULL, UNIQUE  | Código corto: `CE1978`              |
| nombre     | text    | NOT NULL          | Nombre completo de la ley           |
| fecha_pub  | date    | NOT NULL          | Fecha de publicación en BOE         |
| url_eli    | text    |                   | Permalink ELI oficial del BOE       |
| activa     | boolean | NOT NULL, DEFAULT true | Si la ley está vigente         |

**Dato cargado:** 1 fila → Constitución Española (1978)

---

### `legislacion.titulos`

Los 11 títulos de la CE (Preliminar + I al X).

| Columna      | Tipo   | Restricción                        | Descripción                        |
|--------------|--------|------------------------------------|------------------------------------|
| titulo_id    | serial | PK                                 | Identificador interno              |
| ley_id       | int    | NOT NULL, FK → leyes, CASCADE      | Ley a la que pertenece             |
| numero       | text   | NOT NULL                           | `PRELIMINAR`, `I`, `II` … `X`     |
| denominacion | text   | NOT NULL                           | Nombre del título                  |
| orden        | int    | NOT NULL                           | Posición para ordenación           |

**Filas cargadas:** 11

---

### `legislacion.capitulos`

Capítulos dentro de los títulos. Solo los Títulos I, III y VIII tienen capítulos.

| Columna      | Tipo   | Restricción                         | Descripción                         |
|--------------|--------|-------------------------------------|-------------------------------------|
| capitulo_id  | serial | PK                                  | Identificador interno               |
| titulo_id    | int    | NOT NULL, FK → titulos, CASCADE     | Título al que pertenece             |
| numero       | text   | NOT NULL                            | `PRIMERO`, `SEGUNDO` …              |
| denominacion | text   | NOT NULL                            | Nombre del capítulo                 |
| orden        | int    | NOT NULL                            | Posición dentro del título          |

**Filas cargadas:** 11 (5 en Título I + 3 en Título III + 3 en Título VIII)

---

### `legislacion.secciones`

Secciones dentro de capítulos. Solo en el Capítulo Segundo del Título I.

| Columna      | Tipo   | Restricción                          | Descripción                        |
|--------------|--------|--------------------------------------|------------------------------------|
| seccion_id   | serial | PK                                   | Identificador interno              |
| capitulo_id  | int    | NOT NULL, FK → capitulos, CASCADE    | Capítulo al que pertenece          |
| numero       | text   | NOT NULL                             | `1.ª`, `2.ª`                       |
| denominacion | text   | NOT NULL                             | Nombre de la sección               |
| orden        | int    | NOT NULL                             | Posición dentro del capítulo       |

**Filas cargadas:** 2

| Sección | Denominación | Artículos |
|---------|-------------|-----------|
| 1.ª | De los derechos fundamentales y de las libertades públicas | 15–29 |
| 2.ª | De los derechos y deberes de los ciudadanos | 30–38 |

---

### `legislacion.articulos`

Unidad mínima de contenido. Almacena el texto literal de cada artículo, disposición y el preámbulo. Incluye la columna de embedding para búsqueda semántica.

| Columna      | Tipo          | Restricción                          | Descripción                                  |
|--------------|---------------|--------------------------------------|----------------------------------------------|
| articulo_id  | serial        | PK                                   | Identificador interno                        |
| ley_id       | int           | NOT NULL, FK → leyes, CASCADE        | Ley a la que pertenece                       |
| titulo_id    | int           | FK → titulos (nullable)              | Título (null para disposiciones)             |
| capitulo_id  | int           | FK → capitulos (nullable)            | Capítulo (null si el título no tiene)        |
| seccion_id   | int           | FK → secciones (nullable)            | Sección (null si el capítulo no tiene)       |
| numero       | text          | NOT NULL                             | `1`…`169`, `DA-1`, `DT-1`…`DT-9`, `DD`, `DF`, `PREÁMBULO` |
| tipo         | text          | NOT NULL, CHECK                      | Ver valores permitidos abajo                 |
| contenido    | text          | NOT NULL                             | Texto literal extraído del BOE               |
| orden_global | int           | NOT NULL                             | Posición lineal en el documento (1–185)      |
| embedding    | vector(1536)  | nullable                             | Vector semántico generado con text-embedding-3-small |

**Valores permitidos para `tipo`:**

| Valor | Descripción | Filas |
|-------|-------------|-------|
| `preambulo` | Preámbulo de la CE | 1 |
| `articulo` | Artículos 1–169 | 169 |
| `disposicion_adicional` | DA-1 a DA-4 | 4 |
| `disposicion_transitoria` | DT-1 a DT-9 | 9 |
| `disposicion_derogatoria` | DD | 1 |
| `disposicion_final` | DF | 1 |
| **Total** | | **185** |

---

## Índices

| Índice | Tipo | Columna(s) | Propósito |
|--------|------|------------|-----------|
| PK en cada tabla | B-tree | `*_id` | Navegación por clave primaria |
| `titulos(ley_id, orden)` | B-tree | `ley_id, orden` | Listar títulos de una ley en orden |
| `capitulos(titulo_id, orden)` | B-tree | `titulo_id, orden` | Listar capítulos de un título |
| `secciones(capitulo_id, orden)` | B-tree | `capitulo_id, orden` | Listar secciones de un capítulo |
| `articulos(ley_id, orden_global)` | B-tree | `ley_id, orden_global` | Recorrer artículos en orden lineal |
| `articulos(titulo_id)` | B-tree | `titulo_id` | Filtrar artículos por título |
| `articulos(tipo)` | B-tree | `tipo` | Filtrar por tipo de elemento |
| `articulos_embedding_idx` | **HNSW** | `embedding vector_cosine_ops` | Búsqueda semántica por similitud coseno |

---

## Relaciones principales

```
leyes ──< titulos ──< capitulos ──< secciones ──< articulos
  └─────────────────────────────────────────────< articulos
                         └───────────────────────< articulos
                                     └───────────< articulos
```

Cada `articulo` referencia directamente `ley_id` para simplificar consultas sin necesidad de hacer JOIN con todos los niveles superiores.

---

## Scripts asociados

| Archivo | Propósito |
|---------|-----------|
| `sql/ddl/002_constitucion_schema.sql` | Crea el esquema, tablas e índices |
| `sql/dml/002_constitucion_seed.sql` | Carga los 185 elementos desde el BOE |
| `sql/queries/constitucion_preguntas.sql` | Consultas de navegación, búsqueda y Q&A |
| `scripts/generate_embeddings.py` | Genera y almacena los embeddings (OpenAI) |
