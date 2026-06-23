# Current State

_Última actualización: 2026-06-23_

## Propósito

Este documento describe el estado actual real del proyecto `stack-sql-vscode`.
Permite retomar el trabajo técnico sin depender de la memoria de sesiones anteriores.

---

## Entorno de trabajo

| Componente | Detalle |
|---|---|
| Sistema anfitrión | Windows con WSL2 (Ubuntu 24.04 LTS) |
| Editor | VS Code + extensión Claude Code |
| Control de versiones | Git (rama `master`) |
| Contenedores | Docker Desktop con integración WSL2 |
| Base de datos | PostgreSQL 16 + pgvector en Docker |
| Ruta base | `~/dev/stack-sql-vscode` |

### Docker stack

| Servicio | Imagen | Puerto | Contenedor |
|---|---|---|---|
| PostgreSQL + pgvector | `pgvector/pgvector:pg16` | 5432 | `stack-sql-postgres` |
| pgAdmin 4 | `dpage/pgadmin4:latest` | 5050 | `stack-sql-pgadmin` |

- Base de datos: `stack_db` / usuario: `postgres` / contraseña: `postgres`
- Levantar: `docker compose -f docker/docker-compose.yml up -d`

---

## Esquemas activos en stack_db

### `sales` — Práctica SQL básica

Modelo mínimo de clientes y pedidos. Scripts: `sql/ddl/001_init_schema.sql`, `sql/dml/001_seed_sales.sql`.

### `normas` — Base de datos legislativa multi-ley ⬅ núcleo del proyecto

Esquema unificado para múltiples leyes con búsqueda semántica mediante pgvector.

**Tablas:**

| Tabla | Contenido |
|---|---|
| `normas.leyes` | Metadatos de cada ley: nombre, tipo, url_eli, token_count, content_hash, fecha_actualizacion |
| `normas.titulos` | Títulos de cada ley + `embedding vector(1536)` para RAG jerárquico |
| `normas.capitulos` | Capítulos |
| `normas.secciones` | Secciones y subsecciones |
| `normas.articulos` | Artículos y disposiciones + `embedding vector(1536)` |

**Leyes cargadas:**

| ley_id | Código | Ley | Artículos | Embeddings | RAG | Tokens est. |
|--------|--------|-----|-----------|-----------|-----|-------------|
| 1 | CE | Constitución Española (1978) | 185 | ✓ | full-text | 27K |
| 4 | Ley 39/2015 | LPAC — Ley del Procedimiento Administrativo Común | 156 | ✓ | full-text | 56K |
| 7 | Ley 40/2015 | LRJSP — Ley de Régimen Jurídico del Sector Público | 219 | ✓ | jerárquico | 84K |
| 8 | RDL 5/2015 | TREBEP — Estatuto Básico del Empleado Público | 137 | ✓ | full-text | 46K |
| 9 | Ley 47/2003 | LGP — Ley General Presupuestaria | 225 | ✓ | jerárquico | 87K |
| 12 | Ley 9/2017 | LCSP — Ley de Contratos del Sector Público | 428 | ✓ | jerárquico | 231K |

**Totales:** 1.350 artículos/disposiciones · 1.350 embeddings de artículo · 50 embeddings de título

---

## Scripts disponibles

| Script | Propósito |
|---|---|
| `scripts/parse_boe.py` | Descarga y parsea texto consolidado del BOE → JSON |
| `scripts/load_ley.py` | Carga JSON en `normas.*` + genera embeddings |
| `scripts/generate_embeddings.py` | Regenera embeddings de artículos pendientes |
| `scripts/generate_title_embeddings.py` | Genera embeddings de títulos (RAG jerárquico) |
| `scripts/sync_boe.py` | Sincronización incremental con BOE (hash diff) |
| `scripts/cron_sync_boe.sh` | Wrapper cron — ejecuta sync_boe.py con .env cargado |
| `scripts/qa.py` | CLI Q&A: `python scripts/qa.py --ley-id 4 "pregunta"` |
| `scripts/gentest.py` | CLI tests: `python scripts/gentest.py --ley-id 4 --n 5` |

**Carga de nueva ley:**
```bash
python3 scripts/parse_boe.py <url_eli> <CODIGO> --nombre "..." --nombre-corto "..." --output data/leyes/<ley>.json
python3 scripts/load_ley.py data/leyes/<ley>.json --embeddings
python3 scripts/generate_title_embeddings.py
```

**Sincronización BOE (manual):**
```bash
python3 scripts/sync_boe.py                  # todas las leyes
python3 scripts/sync_boe.py --ley-id 4       # solo LPAC
python3 scripts/sync_boe.py --forzar         # ignorar hash, reprocesar
```
Log: `logs/sync_boe.log` · Cron: domingos a las 04:00

---

## App Python

```
app/
├── config.py         # DB_CONFIG, modelos, TOP_K=8, SIMILARITY_THRESHOLD=0.20
├── db.py             # ThreadedConnectionPool (psycopg2)
├── retrieval.py      # embed_query(), search_articles(), search_articles_hierarchical()
├── qa_pipeline.py    # run_qa(pregunta, ley_id) — enrutamiento 3 vías
└── test_pipeline.py  # run_gentest(ley_id, ...) — estilo GACE 2025
```

---

## Estado de los pipelines

### Q&A (`scripts/qa.py`)

- Clasificador de 3 vías: ESTRUCTURAL → metadatos BD | RESUMEN → artículos del título | CONTENIDO → RAG semántico
- Leyes <60K tokens: búsqueda plana (`search_articles`, TOP_K=8)
- Leyes >60K tokens: RAG jerárquico (`search_articles_hierarchical`, top-3 títulos → top-8 artículos)
- Umbral de similitud coseno: 0.20 (descarta artículos poco relevantes)

### Generador de tests (`scripts/gentest.py`)

- Estilo GACE 2025: 5 reglas obligatorias (ver CLAUDE.md)
- Selección ponderada por `log(longitud)`: artículos más ricos tienen más probabilidad
- Filtra artículos <200 chars y derogados
- Salida JSON: `{articulo, pregunta, opciones: {a,b,c,d}, correcta, explicacion}`

---

## Sincronización automática con el BOE

- Mecanismo: SHA-256 del HTML consolidado comparado con `normas.leyes.content_hash`
- Sin cambio de hash: ~2s por ley, sin coste de API
- Con cambio: diff artículo a artículo, actualización selectiva, regeneración de embeddings
- Cron: `0 4 * * 0` (domingos, 04:00)
- Log: `logs/sync_boe.log`
