# Q&A App — Arquitectura

## Propósito de este documento

Define la arquitectura de la aplicación de Q&A jurídico sobre la Constitución Española.
Sirve como referencia de diseño antes de implementar el código.

---

## Decisiones de diseño

| Decisión | Elección | Motivo |
|---|---|---|
| Modelo de embeddings | `text-embedding-3-small` (OpenAI, 1536 dims) | Ya usado para los 185 embeddings existentes. Cambiar requeriría re-generar todo. |
| Modelo de generación | Claude (`claude-sonnet-4-6`) vía Anthropic SDK | Proyecto ya centrado en Claude; SDK Python sencillo. |
| Interfaz MVP | Scripts CLI Python | Coherente con `scripts/generate_embeddings.py`; sin infraestructura extra. |
| Interfaz futura | FastAPI REST | Permite exponer los dos modos como endpoints si el proyecto crece. |

---

## Dos modos de operación

### Modo Q&A

El usuario hace una pregunta en lenguaje natural. El sistema recupera los artículos más
relevantes y Claude genera una respuesta fundamentada en el texto constitucional.

```
PREGUNTA (str)
     │
     ▼
[1] embed_query(pregunta)
     │  OpenAI API → vector[1536]
     ▼
[2] search_articles(vector, k=5)
     │  PostgreSQL + pgvector (cosine similarity, índice HNSW)
     │  → list[Articulo]  (numero, contenido, similitud)
     ▼
[3] build_qa_prompt(pregunta, articulos)
     │  system: rol jurídico + instrucción de citar artículos
     │  user:   pregunta + bloques de contexto
     ▼
[4] claude_client.messages.create(...)
     │  Anthropic API → respuesta en texto
     ▼
RESPUESTA (str)
```

### Modo generación de tests

El sistema selecciona artículos según un filtro (título, capítulo o todos) y Claude
genera una pregunta tipo test por cada artículo.

```
FILTRO (titulo_id | capitulo_id | aleatorio, n)
     │
     ▼
[1] fetch_articles(filtro, n)
     │  PostgreSQL SELECT sin embeddings
     │  → list[Articulo]
     ▼
[2] Para cada artículo:
     │
     ├─ build_test_prompt(articulo)
     │   system: rol de creador de exámenes jurídicos
     │   user:   texto del artículo + instrucción JSON
     │
     └─ claude_client.messages.create(...)
          │  Respuesta JSON: pregunta + 4 opciones + respuesta correcta + explicación
          ▼
[3] Parsear y acumular list[PreguntaTest]
     │
     ▼
SALIDA (stdout / JSON / CSV)
```

---

## Estructura de módulos

```
stack-sql-vscode/
├── app/
│   ├── config.py          # DB_CONFIG, nombres de modelos, constantes
│   ├── db.py              # get_connection() → psycopg2.connection
│   ├── retrieval.py       # embed_query() + search_articles()
│   ├── qa_pipeline.py     # run_qa(pregunta) → str
│   └── test_pipeline.py   # run_gentest(filtro, n) → list[dict]
│
├── scripts/
│   ├── generate_embeddings.py   (existente)
│   ├── qa.py                    (nuevo CLI — modo Q&A)
│   └── gentest.py               (nuevo CLI — modo test)
│
└── requirements.txt             (nuevo)
```

### Responsabilidades por módulo

| Módulo | Responsabilidad |
|---|---|
| `app/config.py` | Lee variables de entorno; expone `DB_CONFIG`, `OPENAI_MODEL`, `CLAUDE_MODEL` |
| `app/db.py` | Abre y cierra conexión psycopg2; función `get_connection()` |
| `app/retrieval.py` | Genera embedding de una consulta; ejecuta búsqueda semántica en pgvector |
| `app/qa_pipeline.py` | Orquesta el flujo Q&A: retrieval → prompt → llamada Claude → respuesta |
| `app/test_pipeline.py` | Orquesta el flujo test: fetch artículos → prompt → llamada Claude → JSON |
| `scripts/qa.py` | Entry point CLI: recibe pregunta como argumento, imprime respuesta |
| `scripts/gentest.py` | Entry point CLI: recibe filtros, imprime o exporta preguntas test |

---

## Variables de entorno requeridas

```bash
OPENAI_API_KEY      # para generar el embedding de la pregunta (modo Q&A)
ANTHROPIC_API_KEY   # para llamar a Claude (ambos modos)
DB_HOST             # default: localhost
DB_PORT             # default: 5432
DB_NAME             # default: stack_db
DB_USER             # default: postgres
DB_PASSWORD         # default: postgres
```

---

## Dependencias Python

```
anthropic           # SDK oficial Anthropic (generación)
openai              # SDK OpenAI (embeddings)
psycopg2-binary     # conexión PostgreSQL
```

---

## Formato de salida del modo test

Claude devolverá JSON estructurado para facilitar el parseo y la exportación:

```json
{
  "articulo": "20.1",
  "pregunta": "¿Cuál de las siguientes libertades reconoce el artículo 20.1 de la Constitución?",
  "opciones": {
    "A": "Libertad de expresión e información",
    "B": "Libertad de reunión",
    "C": "Derecho al sufragio activo",
    "D": "Libertad de circulación"
  },
  "correcta": "A",
  "explicacion": "El artículo 20.1 reconoce y protege los derechos a expresar y difundir libremente pensamientos, ideas y opiniones."
}
```

---

## Flujo de implementación (orden de trabajo)

1. `requirements.txt` — instalar dependencias
2. `app/config.py` — configuración centralizada
3. `app/db.py` — conexión reutilizable
4. `app/retrieval.py` — embedding + búsqueda pgvector
5. `app/qa_pipeline.py` — pipeline Q&A completo
6. `scripts/qa.py` — CLI Q&A funcional y verificado
7. `app/test_pipeline.py` — pipeline generación test
8. `scripts/gentest.py` — CLI test funcional y verificado

---

## Posible evolución futura

- `app/api.py` (FastAPI) — exponer ambos modos como endpoints REST
- `scripts/export_test.py` — exportar banco de preguntas a CSV / Moodle XML
- Modo batch en `gentest.py` — generar preguntas para un título entero en un solo comando
- Caché de embeddings de consultas frecuentes en una tabla `qa_cache`
