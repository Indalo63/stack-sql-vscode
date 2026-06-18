# Stack SQL + VS Code + PostgreSQL

Entorno de trabajo práctico para SQL con PostgreSQL, Docker, VS Code y Claude Code.

Incluye una aplicación de Q&A jurídico sobre la Constitución Española con búsqueda semántica y generación de preguntas test mediante IA.

Pensado para aprendizaje estructurado y reutilizable para alumnos en prácticas.

## Stack

| Capa | Tecnología |
|---|---|
| Sistema | Windows + WSL2 (Ubuntu) |
| Editor | VS Code |
| Control de versiones | Git |
| Base de datos | PostgreSQL 16 en Docker |
| Soporte vectorial | pgvector |
| Administración BD | pgAdmin 4 |
| Aplicación | Python 3 |
| Embeddings | OpenAI `text-embedding-3-small` (1536 dims) |
| Generación IA | Claude (`claude-sonnet-4-6`) vía Anthropic SDK |
| Asistente técnico | Claude Code |

## Requisitos previos

- Windows con WSL2 (Ubuntu) instalado y configurado
- Git instalado en WSL2
- Docker Desktop instalado y accesible desde WSL2
- VS Code con extensión Remote - WSL
- Python 3.10+
- Claves de API: `OPENAI_API_KEY` y `ANTHROPIC_API_KEY`

## Inicio rápido

```bash
# 1. Clonar el repositorio
git clone <url-del-repo> ~/dev/stack-sql-vscode
cd ~/dev/stack-sql-vscode

# 2. Configurar variables de entorno
cp .env.example .env
# Editar .env y rellenar OPENAI_API_KEY y ANTHROPIC_API_KEY

# 3. Instalar dependencias Python
pip install -r requirements.txt

# 4. Levantar PostgreSQL + pgAdmin
make setup

# 5. Generar embeddings (Constitución Española)
python scripts/generate_embeddings.py

# 6. Lanzar la aplicación Q&A
python scripts/qa.py "¿Qué derechos reconoce el artículo 20?"

# 7. Generar preguntas test
python scripts/gentest.py
```

La base de datos `stack_db` arranca con dos esquemas: `sales` (tablas `customers` y `orders`) y `legislacion` (artículos de la Constitución Española con embeddings vectoriales).

## Comandos Make

```bash
make setup    # Levanta el entorno y carga esquema + datos de ejemplo
make start    # Levanta el contenedor (sin cargar esquema)
make stop     # Para el contenedor
make reset    # Destruye el entorno y lo reconstruye desde cero
make psql     # Abre una sesión psql interactiva
make status   # Muestra el estado del contenedor
```

También disponible el menú interactivo: `bash scripts/menu.sh`

## Estructura del repositorio

```
stack-sql-vscode/
├── CLAUDE.md                        # Contexto del proyecto para Claude Code
├── Makefile                         # Comandos de gestión del entorno
├── requirements.txt                 # Dependencias Python
├── .env.example                     # Plantilla de variables de entorno
├── app/
│   ├── config.py                    # Configuración centralizada (BD, modelos, constantes)
│   ├── db.py                        # Conexión reutilizable psycopg2
│   ├── retrieval.py                 # Embedding de consulta + búsqueda semántica pgvector
│   ├── qa_pipeline.py               # Pipeline Q&A: retrieval → prompt → Claude
│   └── test_pipeline.py             # Pipeline generación test: fetch → prompt → Claude
├── docker/
│   └── docker-compose.yml           # PostgreSQL + pgvector + pgAdmin
├── docs/
│   ├── database/
│   │   ├── constitucion/            # Documentación del esquema constitucional
│   │   └── schema-summary.md        # Resumen de todos los esquemas
│   ├── project/                     # Memoria operativa del proyecto
│   └── sql/                         # Guía de estilo SQL y recetas de prompts
├── scripts/
│   ├── generate_embeddings.py       # Genera y almacena embeddings en pgvector
│   ├── qa.py                        # CLI — modo Q&A
│   ├── gentest.py                   # CLI — generación de preguntas test
│   ├── menu.sh                      # Menú interactivo de gestión del entorno
│   └── setup.sh                     # Script de configuración inicial
└── sql/
    ├── ddl/                         # Scripts de creación de esquema
    ├── dml/                         # Datos de ejemplo
    ├── queries/                     # Consultas de práctica
    ├── snippets/                    # Fragmentos reutilizables
    └── tests/                       # Verificaciones SQL
```

## Conexión desde VS Code

Con la extensión PostgreSQL configurada, usar estos datos:

- **Host:** localhost
- **Puerto:** 5432
- **Usuario:** postgres
- **Contraseña:** postgres
- **Base de datos:** stack_db

## pgAdmin

Disponible en [http://localhost:5050](http://localhost:5050) una vez levantado el entorno.

- **Email:** indaleciopf@gmail.com
- **Contraseña:** postgres

## Documentación del proyecto

El directorio `docs/project/` contiene la memoria operativa del proyecto:

- `01-current-state.md` — estado actual verificado
- `02-architecture.md` — diseño del stack y evolución prevista
- `03-chronological-log.md` — bitácora de pasos realizados
- `04-claude-workflow.md` — cómo trabajar con Claude Code en este proyecto
- `05-decisions-and-rationale.md` — decisiones técnicas y principios
- `06-next-steps.md` — prioridades y siguientes pasos
- `07-project-prompt-template.md` — plantilla de prompts para Claude
- `08-qa-app-architecture.md` — arquitectura de la aplicación Q&A
- `eval-qa-referencia.md` — evaluación del pipeline Q&A (13/13 ✅)
- `eval-gentest-referencia.md` — evaluación del generador de tests (8/8 ✅)

## Autor

Indalecio Plaza — consultor y formador técnico en bases de datos relacionales, desarrollo web y automatización con IA.
