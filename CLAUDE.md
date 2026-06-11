# CLAUDE.md – Proyecto Stack SQL + VS Code + PostgreSQL

## Quién soy
Soy Indalecio Plaza, consultor y formador técnico en bases de datos relacionales (PostgreSQL), desarrollo web y automatización con IA.

## Objetivo de este proyecto
Configurar y documentar un stack de trabajo para SQL que combine:

- Windows + WSL2 (Ubuntu)
- VS Code
- Git
- PostgreSQL en Docker
- Extensión PostgreSQL para VS Code
- Claude Code en VS Code
- SQL Crack para visualización de SQL

La guía debe ser reutilizable para alumnos en prácticas y para mí mismo.

## Forma de trabajo deseada con la IA
- Avanzar siempre en pasos numerados (Paso 1, Paso 2, etc.).
- No pasar al siguiente paso hasta que el anterior esté completado y confirmado.
- Explicaciones en español, con lenguaje técnico pero tono docente.
- Preferir explicaciones breves y accionables, con comandos concretos que pueda pegar en WSL2.
- Cuando propongas cambios en archivos, describe:
  - Ruta del archivo
  - Bloque a modificar o crear
  - Contenido completo del bloque

## Entorno asumido
- Sistema: Windows con WSL2 (Ubuntu).
- Directorio de proyecto en WSL2: ~/dev/stack-sql-vscode
- Git ya instalado y configurado en WSL2.
- Aún sin remoto configurado (esto se hará más adelante).

## Convenciones iniciales
- Toda la documentación del stack vive en docs/.
- El archivo principal de guía es docs/stack-sql-vscode.md.
- Usar Markdown para cualquier guía o checklist.
- Cuando se propongan nuevos archivos, ubicarlos dentro de este repo respetando la estructura existente.

## Próximos pasos esperados
- Paso 3: Conectar este repo con un Proyecto de Claude y usar este CLAUDE.md como referencia.
- Paso 4: Configurar Docker + PostgreSQL.
- Paso 5: Instalar y configurar extensiones de VS Code (PostgreSQL, Claude Code, SQL Crack).
- Paso 6: Estructurar carpetas sql/ y docs/database/ para mejorar prompts SQL.
