# Next Steps

_Última actualización: 2026-06-23_

## Estado actual (punto de partida)

Pipeline Q&A y generador de tests operativos sobre 6 leyes prioritarias GACE:
CE, LPAC, LRJSP, TREBEP, LGP, LCSP — 1.350 artículos con embeddings de artículo y de título.
RAG jerárquico activo para leyes >60K tokens. Sincronización automática semanal con el BOE.

---

## Hitos completados

### ~~Hito 1 — Evaluación de calidad~~ ✅ (2026-06-18)
Pipeline Q&A: 13/13 preguntas de referencia. Generador: 8/8 preguntas correctas.

### ~~Hito 4 — Expansión a leyes prioritarias GACE~~ ✅ (2026-06-23)
Cargadas: LPAC (ley 39/2015), LRJSP (40/2015), TREBEP (RDL 5/2015), LGP (47/2003), LCSP (9/2017).
Parser del BOE genérico y robusto: soporta Libros, Subsecciones, sufijos bis/ter/quáter/sexies, ordinales hasta trigésimo, deduplicación automática.

### ~~Hito 5 — Sincronización automática con el BOE~~ ✅ (2026-06-23)
`scripts/sync_boe.py` + cron semanal (domingos 04:00). Hash SHA-256, diff incremental, log en `logs/sync_boe.log`.

### ~~Refinamiento del sistema~~ ✅ (2026-06-23)
RAG jerárquico (embeddings de título), TOP_K 5→8, umbral de similitud 0.20, filtrado de artículos no testables, prompt GACE 2025 alineado con examen oficial.

---

## Próximos hitos

### Hito 2 — Interfaz web Streamlit multi-ley ⬅ siguiente

Interfaz web que reemplaza el CLI para Q&A y generación de tests.

**Requisitos mínimos:**
- Selector de ley (cargado desde `normas.leyes`)
- Pestaña Q&A: campo de pregunta + respuesta formateada en Markdown
- Pestaña Tests: parámetros (n, título/capítulo) + visualización de preguntas con corrección
- Indicador de qué ley está activa y número de artículos

**Archivo:** `app/streamlit_app.py` (existe esqueleto, actualizar a multi-ley)

### Hito 3 — Exportación de tests

Exportar el banco de preguntas generadas a formatos reutilizables.

**Pasos:**
1. Crear `scripts/export_test.py`
2. Salida a CSV (columnas: ley, articulo, pregunta, a, b, c, d, correcta, explicacion)
3. Salida a Moodle XML (formato GIFT o XML nativo)
4. Opción `--export csv|moodle` en `scripts/gentest.py`

### Hito 6 — Simulacro de examen GACE

Motor de simulacro completo que replica el examen oficial.

**Especificaciones del examen GACE 2025:**
- 100 preguntas, 90 minutos
- Penalización: A − (E/3) donde A = aciertos, E = errores
- Escala final: 0–50 puntos, mínimo 25 para aprobar

**Componentes:**
- Selección automática de 100 preguntas distribuidas por ley según el programa oficial
- Temporizador con cuenta regresiva
- Marcado de respuestas (puede dejarse en blanco)
- Puntuación final con fórmula A−(E/3) y conversión a escala 0–50
- Revisión de respuestas con explicación al finalizar

**Dependencia:** requiere banco de preguntas suficiente (Hito 3 facilita la acumulación).

### Hito 7 — Módulo de oposiciones (banco histórico + few-shot)

Ingesta de preguntas reales de convocatorias anteriores y generación guiada por ejemplos.

**Esquema nuevo:** `oposiciones.*`
- `oposiciones.convocatorias` — año, organismo, nº plazas, fórmula de puntuación
- `oposiciones.preguntas_historicas` — enunciado, opciones, correcta, tema, artículo, convocatoria

**Pipeline mejorado:** artículo + 2-3 preguntas reales de la misma oposición → Claude → pregunta alineada con el estilo oficial real (no solo por reglas).

**Requisito mínimo:** 20-30 preguntas reales por oposición.

---

## Expansiones futuras

- Caché de consultas Q&A frecuentes en tabla `normas.qa_cache`
- Modo batch en `gentest.py`: generar preguntas para un título completo en un comando
- Comparativa de embeddings: OpenAI `text-embedding-3-small` vs. modelos locales (sentence-transformers)
- API REST (FastAPI) para exponer Q&A y gentest como endpoints
- Siembra del programa oficial GACE en esquema `programa.*` (6 bloques, 58 temas)

---

## Regla de revisión

Actualizar este archivo cada vez que se complete un hito o cambie la prioridad.
