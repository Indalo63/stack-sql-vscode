# Prompt Recipes – SQL + Claude Code

Recetas de prompts reutilizables para trabajar SQL con Claude Code en este proyecto.

## 1. Generar una nueva consulta

**Objetivo:** obtener una primera versión de SQL para un problema concreto.

Plantilla:

> Usa el esquema descrito en `docs/database/schema-summary.md` y las reglas de `docs/sql/style-guide.md`.  
> Genera una consulta SQL para PostgreSQL que haga lo siguiente:  
> [DESCRIBE AQUÍ EL OBJETIVO]  
> No inventes tablas ni columnas.  
> Explica primero el enfoque en texto, después da solo la consulta SQL final.

## 2. Explicar una consulta existente

**Objetivo:** usar Claude Code como explicador/docente.

Plantilla:

> Lee el archivo `[RUTA_DEL_SQL]` y céntrate en la consulta `[DESCRIPCIÓN BREVE]`.  
> Usando el contexto de `docs/database/schema-summary.md`, explica paso a paso qué hace la consulta:  
> - Qué tablas usa y cómo las relaciona.  
> - Qué filtros aplica.  
> - Qué devuelve exactamente.  
> Genera una explicación orientada a alumno en prácticas.

## 3. Refactorizar una consulta compleja

**Objetivo:** hacer más legible un SQL largo.

Plantilla:

> Lee `[RUTA_DEL_SQL]` y aplica las reglas de `docs/sql/style-guide.md`.  
> Refactoriza la consulta usando CTEs con nombres `base_`, `filtered_`, `final_` cuando tenga sentido.  
> No cambies el resultado funcional.  
> Devuelve el SQL refactorizado y un breve resumen de los cambios.

## 4. Optimizar una consulta

**Objetivo:** sugerir mejoras de rendimiento (sin tocar el motor).

Plantilla:

> Lee `[RUTA_DEL_SQL]` y, usando el esquema de `docs/database/schema-summary.md`, revisa posibles problemas de rendimiento (joins, filtros tardíos, etc.).  
> Propón una versión optimizada de la consulta y explica por qué podría ser mejor.  
> No propongas índices nuevos todavía, solo cambios en la query.

## 5. Generar ejercicios para alumnos

**Objetivo:** crear material docente a partir de una consulta.

Plantilla:

> Usa `docs/database/schema-summary.md` y `docs/sql/style-guide.md` como contexto.  
> A partir de la consulta en `[RUTA_DEL_SQL]`, genera:  
> - 3 preguntas de tipo “escribe la consulta” para alumnos.  
> - 3 preguntas de interpretación de resultados.  
> NO des las soluciones todavía, solo el enunciado.
