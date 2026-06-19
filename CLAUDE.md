# CLAUDE.md – Proyecto Stack SQL + VS Code + PostgreSQL

## Quién soy
Soy Indalecio Plaza, consultor y formador técnico en bases de datos relacionales (PostgreSQL), desarrollo web y automatización con IA.

## Objetivo de este proyecto
Construir y documentar un stack de trabajo para SQL y aplicaciones de IA que combina:

- Windows + WSL2 (Ubuntu) + VS Code + Git
- PostgreSQL 16 + pgvector en Docker
- Python (pipeline Q&A jurídico + generación de tests)
- Claude (Anthropic API) como motor de generación
- OpenAI API para embeddings semánticos
- Claude Code como copiloto técnico y documental

El proyecto incluye una aplicación de Q&A jurídico sobre la Constitución Española: el usuario pregunta en lenguaje natural y el sistema recupera artículos relevantes mediante búsqueda semántica (pgvector) y genera una respuesta fundamentada usando Claude.

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
- Sistema: Windows con WSL2 (Ubuntu 24.04 LTS).
- Directorio de proyecto en WSL2: ~/dev/stack-sql-vscode
- Git instalado y configurado en WSL2.
- Docker Desktop con integración WSL2 operativo.
- Python 3 disponible en WSL2.
- Variables de entorno `OPENAI_API_KEY` y `ANTHROPIC_API_KEY` configuradas en `.env`.

## Convenciones iniciales
- Toda la documentación del stack vive en docs/.
- El archivo principal de guía es docs/stack-sql-vscode.md.
- Usar Markdown para cualquier guía o checklist.
- Cuando se propongan nuevos archivos, ubicarlos dentro de este repo respetando la estructura existente.

## Estado actual del proyecto
El MVP está completo, operativo y evaluado:
- Stack Docker levantado: PostgreSQL + pgvector + pgAdmin
- Esquema `legislacion` con 185 artículos de la CE y embeddings generados
- Pipeline Q&A operativo y evaluado: 13/13 preguntas de referencia correctas (`docs/project/eval-qa-referencia.md`)
- Pipeline de generación de tests operativo y evaluado: 8/8 preguntas correctas, sin símbolos matemáticos (`docs/project/eval-gentest-referencia.md`)
- Restricción activa en `app/test_pipeline.py`: las preguntas, opciones y explicaciones nunca deben contener símbolos matemáticos

## Próximos pasos
- Añadir interfaz web con Streamlit (Hito 2) — **siguiente**
- Exportar banco de tests a CSV / Moodle XML (Hito 3)
- Extender el módulo legislativo a otras leyes (ET, LOPD, LCSP) (Hito 4)
- Sincronización automática con el BOE para detectar reformas legislativas (Hito 5)
- Módulo de oposiciones: banco de preguntas reales + generación guiada por convocatoria (Hito 6)
