# Project Prompt Template

## Purpose of this document

Este documento define una plantilla reutilizable para redactar prompts de trabajo dentro del proyecto `stack-sql-vscode`.

Su objetivo es mejorar consistencia, precisión y continuidad al trabajar con Claude, evitando prompts ambiguos, incompletos o demasiado abiertos.

## When to use this template

Esta plantilla debe usarse cuando la tarea:

- afecte archivos reales del repositorio
- requiera respetar contexto documental existente
- implique SQL, documentación, arquitectura o workflow
- necesite una salida con formato claro
- pueda beneficiarse de instrucciones más precisas que una petición improvisada

No hace falta usarla de forma rígida en tareas triviales, pero sí en cualquier tarea que pueda alterar estructura, contenido o decisiones del proyecto.

## Core prompt template

Usar esta plantilla base:

```md
## Task

[Qué quiero hacer]

## Goal

[Qué resultado final espero]

## Context

[Estado actual, información importante, limitaciones, decisiones previas]

## Relevant files

- [ruta 1]
- [ruta 2]
- [ruta 3]

## Instructions

- [instrucción concreta 1]
- [instrucción concreta 2]
- [instrucción concreta 3]

## Output format

[Cómo debe responder o qué debe entregar]

## Constraints

- [qué no debe asumir]
- [qué no debe cambiar]
- [qué debe respetar]

## Done when

- [criterio de cierre 1]
- [criterio de cierre 2]
- [criterio de cierre 3]
```

La lógica de esta plantilla es simple: objetivo claro, contexto suficiente, archivos relevantes, restricciones explícitas y criterio verificable de cierre.

## Example use cases

### Example 1 – SQL query generation

```md
## Task

Crear una consulta SQL para analizar pedidos por cliente.

## Goal

Obtener una query clara y alineada con el estilo del proyecto.

## Context

El proyecto usa PostgreSQL. El esquema de práctica actual incluye `sales.customers` y `sales.orders`. Debe respetarse la guía de estilo SQL.

## Relevant files

- docs/sql/style-guide.md
- docs/db/schema-summary.md
- sql/ddl/001_init_schema.sql

## Instructions

- Usa nombres reales del esquema disponible.
- Explica la lógica de la consulta.
- Prioriza claridad sobre complejidad innecesaria.

## Output format

Consulta SQL seguida de una explicación breve.

## Constraints

- No inventes tablas ni columnas.
- No uses sintaxis ajena a PostgreSQL.
- No rompas la convención de estilo del proyecto.

## Done when

- La consulta funciona sobre el esquema descrito.
- La explicación es clara.
- El estilo está alineado con el proyecto.
```

### Example 2 – Documentation update

```md
## Task

Actualizar un archivo de documentación del proyecto.

## Goal

Dejar el documento alineado con el estado actual del repositorio.

## Context

El proyecto mantiene su continuidad mediante archivos Markdown internos. La documentación debe reflejar realidad operativa, no planes ambiguos.

## Relevant files

- CLAUDE.md
- docs/project/01-current-state.md
- docs/project/03-chronological-log.md

## Instructions

- Revisa el contexto antes de redactar.
- Conserva el tono documental existente.
- Evita duplicar información innecesaria.

## Output format

Texto final listo para pegar en el archivo correspondiente.

## Constraints

- No inventes avances no implementados.
- No contradigas otros archivos base.
- No escribas contenido genérico.

## Done when

- El texto está listo para pegar.
- El contenido es coherente con el proyecto.
- No hay contradicciones evidentes.
```

### Example 3 – Architecture planning

```md
## Task

Evaluar el siguiente paso técnico para evolucionar el proyecto.

## Goal

Recibir una recomendación concreta, razonada y pequeña.

## Context

El proyecto ya dispone de PostgreSQL en Docker y soporte con `pgvector`, pero el foco actual sigue siendo consolidar base técnica y documental.

## Relevant files

- docs/project/01-current-state.md
- docs/project/02-architecture.md
- docs/project/06-next-steps.md

## Instructions

- Distingue entre estado actual y propuesta futura.
- Propón opciones realistas.
- Prioriza el siguiente paso más simple y útil.

## Output format

Análisis breve con recomendación final.

## Constraints

- No propongas complejidad innecesaria.
- No asumas componentes aún no creados.
- No conviertas la propuesta en roadmap inflado.

## Done when

- Hay una recomendación clara.
- Las opciones están razonadas.
- El siguiente paso es ejecutable.
```

### Example 4 – Repo review

```md
## Task

Revisar la coherencia del repositorio y su documentación.

## Goal

Detectar desalineaciones entre estructura, documentación y estado real.

## Context

El proyecto usa documentación interna como memoria operativa. La coherencia entre archivos es crítica para futuras sesiones con Claude.

## Relevant files

- README.md
- CLAUDE.md
- docs/project/
- docs/sql/

## Instructions

- Busca contradicciones o huecos de contexto.
- Señala duplicidades innecesarias.
- Prioriza problemas reales sobre observaciones menores.

## Output format

Lista breve de hallazgos y acciones sugeridas.

## Constraints

- No inventes errores.
- No critiques estilo sin impacto operativo.
- No propongas reestructuración grande sin justificación.

## Done when

- Los hallazgos son concretos.
- Las acciones sugeridas son razonables.
- La revisión ayuda a mejorar continuidad.
```

## Prompt writing rules for this project

Los prompts del proyecto deberían seguir estas reglas:

- describir una sola tarea principal por prompt
- incluir contexto suficiente, pero no ruido innecesario
- nombrar archivos concretos cuando existan
- distinguir entre pedir análisis y pedir ejecución
- indicar restricciones relevantes de forma explícita
- definir cómo debe verse un buen resultado
- evitar verbos vagos como “mejora”, “ordena” o “hazlo mejor” sin criterio adicional

Un prompt bueno reduce interpretación libre y mejora calidad del resultado.

## Final check before sending a prompt

Antes de enviar un prompt importante, comprobar:

- si el objetivo está formulado con claridad
- si el contexto es suficiente
- si los archivos relevantes están nombrados
- si el formato de salida está definido
- si las restricciones están claras
- si existe un criterio verificable de cierre

Si faltan dos o más de estos elementos, el prompt probablemente necesita refinarse antes de usarse.