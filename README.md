# Stack SQL + VS Code + PostgreSQL

Entorno de trabajo práctico para SQL con PostgreSQL, Docker, VS Code y Claude Code.

Pensado para aprendizaje estructurado y reutilizable para alumnos en prácticas.

## Stack

| Capa | Tecnología |
|---|---|
| Sistema | Windows + WSL2 (Ubuntu) |
| Editor | VS Code |
| Control de versiones | Git |
| Base de datos | PostgreSQL 16 en Docker |
| Soporte vectorial | pgvector |
| Asistente técnico | Claude Code |

## Requisitos previos

- Windows con WSL2 (Ubuntu) instalado y configurado
- Git instalado en WSL2
- Docker Desktop instalado y accesible desde WSL2
- VS Code con extensión Remote - WSL

## Inicio rápido

```bash
# 1. Clonar el repositorio
git clone <url-del-repo> ~/dev/stack-sql-vscode
cd ~/dev/stack-sql-vscode

# 2. Levantar PostgreSQL
cd docker
docker compose up -d

# 3. Verificar la conexión
docker exec -it stack-sql-postgres psql -U postgres -d stack_db -c "\dn"
```

La base de datos `stack_db` arranca con el esquema `sales` (tablas `customers` y `orders`) cargado automáticamente desde `sql/ddl/`.

## Estructura del repositorio

```
stack-sql-vscode/
├── CLAUDE.md                  # Contexto del proyecto para Claude Code
├── docker/
│   └── docker-compose.yml     # PostgreSQL + pgvector
├── docs/
│   ├── database/              # Documentación del esquema
│   ├── project/               # Estado, arquitectura, bitácora y decisiones
│   └── sql/                   # Guía de estilo SQL y recetas de prompts
└── sql/
    ├── ddl/                   # Scripts de creación de esquema
    ├── dml/                   # Datos de ejemplo
    ├── queries/               # Consultas de práctica
    ├── snippets/              # Fragmentos reutilizables
    └── tests/                 # Verificaciones SQL
```

## Conexión desde VS Code

Con la extensión PostgreSQL configurada, usar estos datos:

- **Host:** localhost
- **Puerto:** 5432
- **Usuario:** postgres
- **Contraseña:** postgres
- **Base de datos:** stack_db

## Documentación del proyecto

El directorio `docs/project/` contiene la memoria operativa del proyecto:

- `01-current-state.md` — estado actual verificado
- `02-architecture.md` — diseño del stack y evolución prevista
- `03-chronological-log.md` — bitácora de pasos realizados
- `04-claude-workflow.md` — cómo trabajar con Claude Code en este proyecto
- `05-decisions-and-rationale.md` — decisiones técnicas y principios
- `06-next-steps.md` — prioridades y siguientes pasos
- `07-project-prompt-template.md` — plantilla de prompts para Claude

## Autor

Indalecio Plaza — consultor y formador técnico en bases de datos relacionales, desarrollo web y automatización con IA.
