# Next Steps

## Purpose of this document

Este documento define los próximos pasos operativos del proyecto `stack-sql-vscode`.

## Estado actual (punto de partida)

El proyecto tiene una base de datos legislativa completamente operativa:

- Constitución Española (1978) cargada desde el BOE (texto oficial)
- 185 elementos (preámbulo + artículos + disposiciones)
- Embeddings generados con `text-embedding-3-small` (OpenAI, vector 1536)
- Búsqueda semántica por similitud coseno funcionando con pgvector

El siguiente hito es construir la **aplicación de Q&A jurídico** sobre esta base.

## Próximo hito — App de Q&A jurídico

### Objetivo

Dado el texto de una pregunta del usuario, la app debe:

1. Generar el embedding de la pregunta
2. Buscar los artículos más relevantes en la base de datos (pgvector)
3. Enviar esos artículos como contexto a Claude junto con la pregunta
4. Devolver una respuesta fundamentada en el texto de la CE

### Pipeline técnico

```
Pregunta del usuario
      │
      ▼
OpenAI text-embedding-3-small  →  vector(1536)
      │
      ▼
pgvector <=>  →  top-N artículos más similares
      │
      ▼
Claude (claude-sonnet-4-6)  +  artículos como contexto
      │
      ▼
Respuesta con cita del artículo correspondiente
```

### Opciones de implementación

| Opción | Complejidad | Descripción |
|---|---|---|
| Script Python | Baja | Script de consola que acepta una pregunta y devuelve respuesta |
| API REST (FastAPI) | Media | Endpoint HTTP que expone el pipeline |
| Integración n8n | Media | Flujo visual sin código en el stack Docker |

**Recomendación para empezar:** script Python de consola — valida el pipeline completo antes de añadir capas.

## Pasos inmediatos

1. Escribir `scripts/qa_constitucion.py` — script de Q&A con el pipeline completo
2. Verificar la calidad de las respuestas con preguntas de prueba
3. Decidir la interfaz definitiva (consola / API / n8n)
4. Documentar el módulo Q&A en `docs/`

## Expansiones futuras

- Extender el módulo a otras leyes (ET, LOPD, LCSP) siguiendo el mismo proceso
- Interfaz web sencilla (Streamlit o FastAPI + HTML)
- Integración con n8n para automatizar flujos de preguntas
- Histórico de preguntas y respuestas en base de datos

## Review rule

Este archivo debe actualizarse cada vez que se complete un hito o cambie la prioridad.
