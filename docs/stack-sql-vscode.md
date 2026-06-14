# Guía de instalación — Stack SQL + VS Code + PostgreSQL

Guía paso a paso para replicar el entorno de trabajo SQL de este proyecto.

Dirigida a alumnos en prácticas o a cualquier persona que quiera montar el mismo stack desde cero.

---

## Paso 1 — Git en WSL2

Instalar y configurar Git dentro del entorno WSL2 (Ubuntu).

```bash
sudo apt update && sudo apt install git -y

git config --global user.name "Tu Nombre"
git config --global user.email "tu@email.com"

git --version
```

Estado: COMPLETADO.

---

## Paso 2 — Carpeta base del proyecto

Crear la estructura de trabajo y clonar o inicializar el repositorio.

```bash
mkdir -p ~/dev
cd ~/dev

# Opción A: clonar el repositorio existente
git clone <url-del-repo> stack-sql-vscode

# Opción B: inicializar desde cero
mkdir stack-sql-vscode && cd stack-sql-vscode
git init
```

Estado: COMPLETADO.

---

## Paso 3 — Docker + PostgreSQL con pgvector

El proyecto usa la imagen `pgvector/pgvector:pg16`, que incluye PostgreSQL 16 con soporte vectorial integrado.

### Levantar el contenedor

```bash
cd ~/dev/stack-sql-vscode/docker
docker compose up -d
```

### Verificar que el contenedor está en marcha

```bash
docker ps
```

Debe aparecer el contenedor `stack-sql-postgres` con estado `Up`.

### Conectarse a PostgreSQL

```bash
docker exec -it stack-sql-postgres psql -U postgres -d stack_db
```

Datos de conexión:

| Parámetro | Valor |
|---|---|
| Host | localhost |
| Puerto | 5432 |
| Usuario | postgres |
| Contraseña | postgres |
| Base de datos | stack_db |

Estado: COMPLETADO.

---

## Paso 4 — Activar la extensión pgvector

Dentro de la sesión `psql`, ejecutar:

```sql
CREATE EXTENSION IF NOT EXISTS vector;

-- Verificar que está activa
\dx
```

Debe aparecer `vector` en la lista de extensiones instaladas.

Estado: COMPLETADO.

---

## Paso 5 — Cargar el esquema y los datos de ejemplo

El esquema no se carga automáticamente. Hay que ejecutar los scripts en orden.

### Crear el esquema `sales`

```bash
docker exec -i stack-sql-postgres psql -U postgres -d stack_db \
  < ~/dev/stack-sql-vscode/sql/ddl/001_init_schema.sql
```

Esto crea las tablas `sales.customers` y `sales.orders`.

### Cargar datos de ejemplo

```bash
docker exec -i stack-sql-postgres psql -U postgres -d stack_db \
  < ~/dev/stack-sql-vscode/sql/dml/001_seed_sales.sql
```

### Verificar

```bash
docker exec -it stack-sql-postgres psql -U postgres -d stack_db -c "\dt sales.*"
```

Estado: COMPLETADO.

---

## Paso 6 — Extensión PostgreSQL en VS Code

Instalar la extensión **PostgreSQL** (de Chris Kolkman) desde el panel de extensiones de VS Code.

Crear una conexión con estos datos:

- Host: `localhost`
- Port: `5432`
- User: `postgres`
- Password: `postgres`
- Database: `stack_db`

Una vez conectado, es posible explorar el esquema `sales` y ejecutar consultas directamente desde el editor.

Estado: COMPLETADO.

---

## Paso 7 — Claude Code en VS Code

Instalar la extensión **Claude Code** desde el panel de extensiones de VS Code.

El archivo `CLAUDE.md` en la raíz del proyecto actúa como contexto persistente para Claude Code. Cargarlo al inicio de cada sesión de trabajo garantiza respuestas alineadas con el proyecto.

Para tareas SQL, usar las recetas definidas en `docs/sql/prompt-recipes.md`.

Estado: COMPLETADO.

---

## Referencia rápida

### Comandos frecuentes de Docker

```bash
# Levantar el contenedor
docker compose -f ~/dev/stack-sql-vscode/docker/docker-compose.yml up -d

# Detener el contenedor
docker compose -f ~/dev/stack-sql-vscode/docker/docker-compose.yml down

# Ver logs
docker logs stack-sql-postgres

# Conectarse a psql
docker exec -it stack-sql-postgres psql -U postgres -d stack_db
```

### Comandos frecuentes de psql

```sql
-- Ver esquemas disponibles
\dn

-- Ver tablas del esquema sales
\dt sales.*

-- Ver extensiones instaladas
\dx

-- Salir
\q
```
