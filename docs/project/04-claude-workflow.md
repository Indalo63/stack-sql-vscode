# Claude Workflow

## Purpose of this document

Este documento define cómo usar Claude de forma consistente dentro del proyecto `stack-sql-vscode`.

Su función es convertir a Claude en una herramienta operativa estable para desarrollo, documentación, aprendizaje técnico y planificación, evitando un uso improvisado o dependiente de cada sesión individual.

## Role of Claude in this project

En este proyecto, Claude cumple varios papeles complementarios:

- copiloto técnico para SQL, PostgreSQL, Docker y estructura del repositorio
- asistente de documentación para mantener archivos Markdown claros y actualizados
- apoyo didáctico para explicar consultas, conceptos y decisiones de arquitectura
- apoyo de planificación para ordenar próximos pasos, comparar opciones y preparar cambios antes de ejecutarlos

Claude no se usa solo para “generar cosas”, sino para ayudar a pensar, estructurar, revisar y mantener continuidad.

## Two complementary ways of working

Este proyecto usará dos modos de trabajo con Claude, cada uno con una función distinta pero complementaria.

El primer modo es **Claude Code dentro del repositorio**, orientado a trabajar directamente sobre archivos, estructura y contenido real del proyecto.

El segundo modo es **Claude app fuera del editor**, orientado a pensar, diseñar, comparar opciones, preparar documentos o refinar prompts antes de aplicar cambios concretos en el repo.

La idea no es elegir uno u otro de forma excluyente, sino usar cada entorno para lo que mejor resuelve.

## Option 1 – Working with Claude Code inside the repository

Claude Code debe usarse cuando el trabajo dependa del estado real del proyecto y requiera operar sobre archivos o carpetas existentes.

Casos típicos:

- crear o editar archivos `.md`
- revisar o refactorizar SQL
- inspeccionar la estructura del repo
- trabajar sobre scripts reales
- mantener coherencia entre documentación y archivos técnicos
- apoyarse en `CLAUDE.md` y en la documentación interna como contexto persistente

Claude Code es el entorno principal cuando el objetivo es producir cambios concretos en el proyecto, no solo discutir ideas.

## Option 2 – Working with Claude app outside the editor

Claude app debe usarse cuando el objetivo principal sea pensar, organizar o preparar trabajo antes de tocar el repositorio.

Casos típicos:

- definir estrategia
- comparar caminos de arquitectura
- diseñar la estructura de un documento
- preparar prompts más precisos para Claude Code
- descomponer una tarea grande en pasos pequeños
- aclarar conceptos técnicos antes de implementar

Claude app funciona mejor como espacio de preparación, reflexión y diseño previo. Después, el resultado de esa preparación puede trasladarse al repo mediante Claude Code.

## Core context files Claude should use

Cuando Claude trabaje dentro de este proyecto, debe apoyarse en los archivos de contexto principales antes de proponer cambios importantes.

Archivos base de contexto:

- `CLAUDE.md`
- `README.md`
- `docs/project/01-current-state.md`
- `docs/project/02-architecture.md`
- `docs/project/03-chronological-log.md`
- `docs/sql/style-guide.md`
- `docs/sql/prompt-recipes.md`
- cualquier resumen de esquema, DDL o archivo SQL directamente relacionado con la tarea activa

La regla general es simple: Claude debe leer primero el contexto existente y solo después proponer, modificar o ampliar contenido.

## Recommended workflow for SQL tasks

Para tareas SQL, el flujo recomendado es el siguiente:

1. identificar el objetivo exacto de la consulta o cambio
2. revisar el esquema disponible y los nombres reales de tablas y columnas
3. revisar la guía de estilo SQL del proyecto
4. redactar o refactorizar la consulta
5. explicar la lógica si la tarea tiene valor didáctico
6. dejar el resultado alineado con el estilo del repositorio

Cuando falte contexto, Claude debe pedirlo o explicitar la limitación en lugar de inventar estructura de base de datos.

## Recommended workflow for documentation tasks

Para tareas de documentación, el flujo recomendado es:

1. identificar qué archivo debe cambiarse
2. revisar archivos relacionados para no duplicar ni contradecir información
3. preservar el tono documental del proyecto
4. proponer estructura antes de escribir si el cambio es grande
5. redactar el contenido final de forma clara y mantenible
6. dejar la documentación alineada con el estado real del proyecto

La documentación debe describir realidad operativa, no deseos vagos ni planes no confirmados.

## Recommended workflow for architecture and planning tasks

Para tareas de arquitectura o planificación, Claude debe trabajar por capas.

Secuencia recomendada:

1. describir el estado actual
2. identificar la necesidad o problema
3. comparar opciones razonables
4. explicar ventajas, riesgos y dependencias
5. proponer un siguiente paso pequeño y ejecutable
6. separar claramente lo actual, lo propuesto y lo futuro

Esto evita mezclar implementación real con ideas todavía no validadas.

## Session-start checklist

Antes de empezar una sesión nueva de trabajo en el proyecto, Claude debería comprobar:

- cuál es la tarea concreta de la sesión
- cuál es el estado actual documentado
- qué archivos son fuente de verdad para esa tarea
- si existe ya una convención escrita aplicable
- si el cambio afecta SQL, documentación, Docker, arquitectura o varios a la vez

El inicio de sesión debe orientarse a recuperar contexto antes de producir contenido.

## Session-end checklist

Antes de cerrar una sesión de trabajo, Claude debería comprobar:

- si el resultado quedó realmente escrito en el archivo correcto
- si la documentación sigue alineada con el estado del proyecto
- si hace falta actualizar `03-chronological-log.md`
- si hace falta actualizar `01-current-state.md`
- si alguna decisión nueva debería reflejarse después en un archivo de decisiones o de próximos pasos

El cierre de sesión debe dejar continuidad útil para la siguiente interacción.

## What Claude should avoid

Claude debe evitar de forma explícita:

- inventar tablas, columnas, scripts o configuraciones no verificadas
- asumir que algo fue implementado si solo fue discutido
- mezclar estado actual con roadmap futuro
- duplicar información ya documentada sin necesidad
- redactar documentación ambigua o demasiado genérica
- cambiar nombres, rutas o estructura sin respetar el repositorio real
- presentar como seguro algo que depende de validación técnica pendiente

Cuando exista incertidumbre, debe marcarla con claridad.

## Maintenance rule for Claude context

El contexto del proyecto debe mantenerse vivo.

Cada vez que cambie una parte relevante del stack, la documentación base también debe revisarse. En particular:

- `CLAUDE.md` debe reflejar la identidad operativa del proyecto
- `01-current-state.md` debe describir el estado vigente
- `02-architecture.md` debe representar la arquitectura real
- `03-chronological-log.md` debe conservar la secuencia de evolución
- este archivo debe seguir describiendo el modo recomendado de trabajar con Claude

La regla de mantenimiento es simple: si cambia la realidad del proyecto, debe cambiar también su contexto documental.