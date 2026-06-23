# Q&A App — Arquitectura

_Última actualización: 2026-06-23_

## Decisiones de diseño

| Decisión | Elección | Motivo |
|---|---|---|
| Modelo de embeddings | `text-embedding-3-small` (OpenAI, 1536 dims) | Consistencia con corpus existente |
| Modelo de generación | `claude-sonnet-4-6` vía Anthropic SDK | Calidad, velocidad y coste equilibrados |
| Esquema BD | `normas.*` unificado multi-ley | Una sola BD, leyes identificadas por `ley_id` |
| Estrategia RAG | full-text (<60K tokens) / jerárquico (≥60K) | Equilibrio calidad-coste según tamaño de ley |
| Interfaz actual | CLI Python | Verificable, sin infraestructura extra |
| Interfaz próxima | Streamlit (Hito 2) | Accesible, sin servidor separado |

---

## Pipeline Q&A

```
PREGUNTA + ley_id
      │
      ▼
[0] get_ley_info(ley_id)
      │  → nombre, token_count
      ▼
[1] _clasificar_pregunta(pregunta, ley_nombre)   [Claude, max_tokens=15]
      │
      ├── ESTRUCTURAL ──→ get_estructura_db(ley_id) → respuesta directa de BD
      │
      ├── RESUMEN ──────→ _extraer_titulo_id()
      │                   get_articulos_por_titulo(titulo_id)
      │                   → Claude con texto completo del título
      │
      └── CONTENIDO ────→ embed_query(pregunta)   [OpenAI]
                          │
                          ├─ token_count < 60K → search_articles(vector, ley_id, k=8)
                          │                       búsqueda plana pgvector
                          │
                          └─ token_count ≥ 60K → search_articles_hierarchical(vector, ley_id)
                                                  1. top-3 títulos por embedding de título
                                                  2. top-8 artículos dentro de esos títulos
                                                  fallback a búsqueda plana si escaso
                          │
                          └─ Claude con artículos recuperados → RESPUESTA
```

**Parámetros clave** (`app/config.py`):

| Constante | Valor | Propósito |
|---|---|---|
| `TOP_K_ARTICLES` | 8 | Artículos recuperados por consulta |
| `SIMILARITY_THRESHOLD` | 0.20 | Similitud coseno mínima para incluir un artículo |
| `TOKEN_THRESHOLD_HIERARCHICAL` | 60 000 | Umbral para activar RAG jerárquico |

---

## Pipeline generación de tests

```
ley_id + [titulo_id | capitulo_id] + n
      │
      ▼
fetch_articles(ley_id, filtro, n)
      │  WHERE tipo='articulo'
      │    AND length(contenido) >= 200
      │    AND contenido !~* '(derogado|sin contenido|suprimido)'
      │  ORDER BY RANDOM() * log(length(contenido)) DESC
      ▼
Para cada artículo:
      │
      ├─ _build_test_prompt(articulo, ley_nombre)
      │   5 reglas GACE 2025 obligatorias:
      │   1. Enunciado cita la norma completa
      │   2. Opciones en minúsculas a/b/c/d
      │   3. Distractores de alta precisión (plazo, porcentaje, órgano)
      │   4. Nivel de dificultad alto (datos exactos, no conceptos)
      │   5. Sin símbolos matemáticos
      │
      └─ Claude → JSON {articulo, pregunta, opciones:{a,b,c,d}, correcta, explicacion}
```

---

## Estructura de módulos

```
app/
├── config.py          # DB_CONFIG, constantes RAG, modelos
├── db.py              # ThreadedConnectionPool, get_connection()
├── retrieval.py       # embed_query(), search_articles(), search_articles_hierarchical()
│                      # get_ley_info(), get_leyes_disponibles(), get_estructura_db()
│                      # get_titulos_db(), get_articulos_por_titulo()
├── qa_pipeline.py     # run_qa(pregunta, ley_id) → str
│                      # _clasificar_pregunta(), _responder_estructural()
│                      # _responder_resumen(), _responder_contenido()
└── test_pipeline.py   # run_gentest(ley_id, ...) → list[dict]
                       # fetch_articles(), _build_test_prompt()

scripts/
├── parse_boe.py             # descarga + parsea BOE → JSON
├── load_ley.py              # carga JSON en normas.* + embeddings
├── generate_embeddings.py   # regenera embeddings de artículos (batch)
├── generate_title_embeddings.py  # genera embeddings de títulos
├── sync_boe.py              # sincronización incremental con BOE
├── cron_sync_boe.sh         # wrapper cron
├── qa.py                    # CLI: python scripts/qa.py --ley-id N "pregunta"
└── gentest.py               # CLI: python scripts/gentest.py --ley-id N --n 5
```

---

## Esquema `normas.*`

```sql
normas.leyes        (ley_id, codigo, nombre, nombre_corto, tipo, fecha_pub,
                     url_eli, token_count, content_hash, fecha_actualizacion, activa)

normas.titulos      (titulo_id, ley_id, numero, denominacion, orden,
                     embedding vector(1536))          ← para RAG jerárquico

normas.capitulos    (capitulo_id, titulo_id, numero, denominacion, orden)

normas.secciones    (seccion_id, capitulo_id, titulo_id, numero, denominacion, orden)

normas.articulos    (articulo_id, ley_id, titulo_id, capitulo_id, seccion_id,
                     numero, tipo, contenido, orden_global,
                     embedding vector(1536))          ← para búsqueda semántica
```

**Tipos de artículo** (`tipo`): `preambulo`, `articulo`, `disposicion_adicional`,
`disposicion_transitoria`, `disposicion_derogatoria`, `disposicion_final`.

---

## Variables de entorno requeridas

```bash
OPENAI_API_KEY      # embeddings (query + generación batch)
ANTHROPIC_API_KEY   # generación Q&A y tests
DB_HOST             # default: localhost
DB_PORT             # default: 5432
DB_NAME             # default: stack_db
DB_USER             # default: postgres
DB_PASSWORD         # default: postgres
```

Cargar en shell: `set -a && source .env && set +a`

---

## Evolución futura prevista

- `app/streamlit_app.py` — interfaz web multi-ley (Hito 2)
- `scripts/export_test.py` — exportar banco de tests a CSV / Moodle XML (Hito 3)
- Motor de simulacro GACE: 100 preguntas, temporizador, A−(E/3) (Hito 6)
- `app/api.py` (FastAPI) — endpoints REST para Q&A y gentest
