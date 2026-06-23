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

## Normas obligatorias para la generación de preguntas tipo test

Estas reglas se aplican SIEMPRE en `app/test_pipeline.py` y en cualquier futuro generador de preguntas. Son innegociables y derivan del análisis del examen oficial GACE 2025.

1. **Sin símbolos matemáticos**: Las preguntas, opciones y explicaciones nunca deben contener símbolos matemáticos (=, >, <, %, +, ×, ÷, →, fracciones, etc.). Escribir siempre en texto: "igual a", "mayor que", "porcentaje", etc.

2. **El enunciado cita la norma completa**: El enunciado debe comenzar siempre con "Según el artículo [N] de [nombre completo de la ley]," o "De acuerdo con el artículo [N] de [nombre completo de la ley],". Nunca omitir el nombre completo de la norma.

3. **Opciones en minúsculas a/b/c/d**: Las cuatro opciones se etiquetan siempre como a), b), c), d) — nunca en mayúsculas.

4. **Distractores de alta precisión**: Las opciones incorrectas deben diferir de la correcta únicamente en datos exactos: un plazo distinto, un porcentaje diferente, un órgano incorrecto, una palabra clave cambiada. Prohibido usar distractores conceptualmente muy distintos; el error debe ser sutil y técnico (estilo examen oficial GACE).

5. **Nivel de dificultad alto**: Preguntar por datos exactos del artículo (plazos, porcentajes, órganos competentes, requisitos concretos), no por conceptos generales.

## Estado actual del proyecto
- Stack Docker levantado: PostgreSQL + pgvector + pgAdmin
- Schema `normas.*` multi-ley operativo (CE1978 + LPAC 39/2015 cargadas con embeddings)
- Pipeline Q&A multi-ley operativo con enrutamiento ESTRUCTURAL/RESUMEN/CONTENIDO
- Generador de preguntas tipo test alineado con estilo oficial GACE 2025
- Parser del BOE (HTML → JSON) validado y operativo
- Scripts: `load_ley.py` (carga genérica), `parse_boe.py` (parser BOE), `generate_embeddings.py`

## Próximos pasos
- Parsear y cargar leyes prioritarias GACE: LRJSP (Ley 40/2015), TREBEP (RDL 5/2015), LGP (Ley 47/2003), LCSP (Ley 9/2017)
- Interfaz web Streamlit multi-ley (Hito 2)
- Exportar banco de tests a CSV / Moodle XML (Hito 3)
- Simulacro: 100 preguntas, temporizador, puntuación con penalización A-(E/3) (Hito 4)
- Sincronización automática con el BOE (Hito 5)
