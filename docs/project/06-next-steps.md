# Next Steps

## Purpose of this document

Este documento define los próximos pasos operativos del proyecto `stack-sql-vscode`.

## Estado actual (punto de partida)

El MVP de la aplicación de Q&A jurídico está completo y operativo:

- Constitución Española (1978) cargada desde el BOE (texto oficial)
- 185 elementos con embeddings generados (`text-embedding-3-small`, vector 1536)
- Búsqueda semántica por similitud coseno funcionando con pgvector (índice HNSW)
- Pipeline Q&A operativo: `python scripts/qa.py "pregunta..."`
- Pipeline de generación de tests operativo: `python scripts/gentest.py --n 5`

## Próximos hitos

### ~~Hito 1 — Evaluación de calidad~~ ✅ Completado (2026-06-18)

**Pipeline Q&A:** 13/13 preguntas de referencia respondidas correctamente. Precisión de recuperación y calidad de respuesta: alta.
Ver resultados en `docs/project/eval-qa-referencia.md`.

**Generador de tests:** 8/8 preguntas evaluadas sobre Arts. 14, 33, 34, 55, 87, 145, 155, 169.
Opciones correctas verificadas contra el texto literal de la CE. Distractores de calidad. 0 errores de fondo.
Ver resultados en `docs/project/eval-gentest-referencia.md`.

### Hito 2 — Interfaz de usuario

Elegir e implementar una interfaz más accesible que el CLI.

| Opción | Complejidad | Descripción |
|---|---|---|
| Streamlit | Baja | Interfaz web local en Python, sin servidor separado |
| FastAPI REST | Media | Endpoint HTTP que expone los dos modos como API |
| Integración n8n | Media | Flujo visual sin código adicional en Docker |

**Recomendación:** Streamlit para una demo rápida; FastAPI si el objetivo es exponerlo como servicio.

### Hito 3 — Exportación de tests

Añadir la capacidad de exportar el banco de preguntas generadas a formatos reutilizables.

**Pasos:**
1. Crear `scripts/export_test.py`
2. Soportar salida a CSV y, opcionalmente, a formato Moodle XML
3. Añadir opción `--export csv` a `scripts/gentest.py`

### Hito 4 — Expansión a otras leyes

Replicar el módulo legislativo para otras leyes relevantes.

**Candidatos:**
- Estatuto de los Trabajadores (ET)
- Ley Orgánica de Protección de Datos (LOPD)
- Ley de Contratos del Sector Público (LCSP)

El proceso está documentado y es repetible: DDL → seed → embeddings → pipeline.

## Expansiones futuras (sin prioridad asignada)

- Caché de embeddings de consultas frecuentes en tabla `qa_cache`
- Histórico de preguntas y respuestas en base de datos
- Modo batch en `gentest.py` para generar preguntas por título entero
- Comparativa de calidad entre embeddings de OpenAI y modelos locales (HuggingFace)

## Review rule

Este archivo debe actualizarse cada vez que se complete un hito o cambie la prioridad.
