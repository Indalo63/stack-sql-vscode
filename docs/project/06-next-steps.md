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

### Hito 5 — Sincronización automática con el BOE

Detectar reformas legislativas publicadas en el BOE y mantener la base de datos actualizada sin intervención manual.

**Problema que resuelve:** una ley cargada en `legislacion.articulos` puede quedar desactualizada si el BOE publica una disposición que la modifica o deroga. Los embeddings existentes reflejarían texto obsoleto.

**Enfoque propuesto:**

1. Crear `scripts/sync_boe.py` que consulte la API pública del BOE (`api.boe.es`) buscando disposiciones que referencien las leyes cargadas en la base de datos.
2. Comparar el texto recuperado con el almacenado en `legislacion.articulos`.
3. Marcar los artículos afectados con un campo `desactualizado = true`.
4. Regenerar embeddings únicamente de los artículos modificados.
5. Registrar cada sincronización en una tabla de auditoría (`legislacion.sync_log`).

**Opciones de activación:**

| Mecanismo | Descripción |
|---|---|
| Cron / scheduler | Ejecución periódica automática (semanal o mensual) |
| RSS/Atom del BOE | Suscripción a feeds por sección; dispara revisión manual antes de ingestar |

**Prioridad por ley:** la CE es muy difícil de reformar (Arts. 167-169), por lo que este hito tiene mayor impacto práctico sobre las leyes del Hito 4 (ET, LOPD, LCSP), donde las modificaciones son frecuentes.

**Dependencia:** se recomienda implementar después del Hito 4.

### Hito 6 — Módulo de oposiciones

Módulo independiente para preparación de oposiciones, combinando preguntas reales de convocatorias anteriores con generación asistida por IA adaptada a cada examen.

**Problema que resuelve:** las preguntas genéricas no reflejan el estilo, dificultad ni sistema de puntuación real de cada oposición. Este módulo genera preguntas que imitan el formato exacto del examen objetivo.

**Arquitectura en dos capas:**

**Capa 1 — Banco de preguntas reales (ingesta)**

Nuevo esquema `oposiciones` con las siguientes tablas:
- `oposiciones.convocatorias` — nombre, año, organismo convocante, nº de plazas
- `oposiciones.reglas_puntuacion` — acierto, error, blanco (configurable por convocatoria)
- `oposiciones.preguntas_historicas` — enunciado, opciones, respuesta correcta, tema, artículo de referencia, convocatoria

**Capa 2 — Generación guiada por ejemplos reales**

Pipeline de generación que combina tres fuentes de contexto para Claude:
1. Artículo legislativo relevante (recuperado por búsqueda semántica con pgvector)
2. 2-3 preguntas reales de esa misma oposición como ejemplos de estilo y dificultad (few-shot)
3. Reglas de puntuación de la convocatoria objetivo

**Scripts nuevos:**
- `scripts/ingest_oposicion.py` — carga preguntas históricas desde CSV
- `scripts/gentest_oposicion.py` — genera preguntas adaptadas a una convocatoria concreta

**Requisito mínimo:** corpus de al menos 20-30 preguntas reales por oposición para que el estilo generado sea fiel al examen. Sin corpus, la generación es válida pero genérica.

**Dependencia:** requiere Hito 4 (expansión a otras leyes) para oposiciones que no sean sobre la CE.

## Expansiones futuras (sin prioridad asignada)

- Caché de embeddings de consultas frecuentes en tabla `qa_cache`
- Histórico de preguntas y respuestas en base de datos
- Modo batch en `gentest.py` para generar preguntas por título entero
- Comparativa de calidad entre embeddings de OpenAI y modelos locales (HuggingFace)

## Review rule

Este archivo debe actualizarse cada vez que se complete un hito o cambie la prioridad.
