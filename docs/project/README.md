## Project Documentation

## Purpose of this folder

La carpeta `docs/project/` contiene la documentación operativa del proyecto `stack-sql-vscode`.

Su función es conservar el contexto que permite entender el estado actual del proyecto, su arquitectura, su evolución, la forma de trabajar con Claude, las decisiones ya tomadas y los siguientes pasos previstos.

Esta carpeta existe para que la continuidad del proyecto no dependa de memoria informal ni de conversaciones anteriores.

## Documents in this folder

Los documentos actuales de esta carpeta son:

- `01-current-state.md`
  Describe el estado vigente del proyecto.

- `02-architecture.md`
  Resume la arquitectura actual del stack y la relación entre sus piezas.

- `03-chronological-log.md`
  Registra la evolución del proyecto paso a paso.

- `04-claude-workflow.md`
  Define cómo trabajar con Claude Code y Claude app dentro del contexto del proyecto.

- `05-decisions-and-principles.md`
  Recoge decisiones confirmadas y principios que deben guiar la evolución futura.

- `06-next-steps.md`
  Define prioridades inmediatas, siguientes pasos y condiciones de preparación para etapas posteriores.

- `07-project-prompt-template.md`
  Proporciona una plantilla reutilizable para redactar prompts de trabajo más claros y consistentes.

- `08-qa-app-architecture.md`
  Detalla la arquitectura del pipeline Q&A y de generación de tests.

- `09-business-logic.md`
  Resume la lógica de negocio: modelo B2B/B2C, reglas de generación de test, fórmula de corrección y arquitectura de la app del alumno.

- `10-replication-and-domains.md`
  Explica cómo replicar el stack para otras oposiciones o dominios.

## Reading order

El orden recomendado de lectura es el siguiente:

1. `01-current-state.md`
2. `02-architecture.md`
3. `03-chronological-log.md`
4. `05-decisions-and-principles.md`
5. `06-next-steps.md`
6. `04-claude-workflow.md`
7. `07-project-prompt-template.md`

Este orden permite entender primero qué existe, después cómo está organizado, cómo ha evolucionado, qué decisiones lo sostienen, hacia dónde va y cómo debe trabajarse con Claude dentro de ese contexto.

## Update rule

Esta carpeta debe actualizarse cada vez que cambie una parte relevante del proyecto.

En particular, debe revisarse cuando ocurra alguno de estos casos:

- cambia el estado técnico real del stack
- cambia la arquitectura
- se toma una decisión importante
- se redefine la prioridad del proyecto
- cambia la forma recomendada de colaborar con Claude
- aparece un nuevo documento de contexto que merezca quedar incorporado a esta carpeta

La regla general es simple: si cambia la realidad del proyecto, esta carpeta debe reflejar ese cambio.