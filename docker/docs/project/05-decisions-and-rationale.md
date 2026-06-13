# Decisions and Principles

## Purpose of this document

Este documento recoge las decisiones relevantes ya tomadas en el proyecto `stack-sql-vscode` y los principios que deben guiar su evolución.

Su objetivo es reducir ambigüedad, conservar criterio técnico y evitar que decisiones futuras rompan coherencia con la dirección ya establecida.

## Confirmed decisions

Hasta este momento, las decisiones confirmadas del proyecto son las siguientes:

- el entorno base de trabajo es WSL2
- el editor principal es VS Code
- el repositorio Git vive dentro del entorno Linux de trabajo
- PostgreSQL se ejecuta en Docker
- la evolución de PostgreSQL se ha preparado sobre `pgvector`
- el proyecto usa Markdown como memoria operativa principal
- Claude forma parte estructural del workflow del proyecto
- la documentación del proyecto se almacena dentro del propio repositorio
- la continuidad del proyecto debe quedar registrada en archivos persistentes, no solo en conversaciones

Estas decisiones deben tratarse como base vigente, salvo reemplazo explícito posterior.

## Technical principles

Las decisiones técnicas futuras deberían respetar estos principios:

- preferir componentes simples, locales y reproducibles
- evitar complejidad temprana sin necesidad real
- priorizar herramientas que puedan verificarse fácilmente
- mantener la base relacional clara antes de ampliar la capa vectorial
- introducir nuevas piezas solo cuando exista un caso de uso comprensible
- favorecer pasos pequeños, reversibles y comprobables
- separar claramente infraestructura, SQL y documentación

La arquitectura debe crecer por consolidación progresiva, no por acumulación desordenada.

## Documentation principles

La documentación del proyecto debe seguir estos principios:

- describir el estado real del proyecto
- distinguir entre estado actual, decisiones tomadas y planes futuros
- estar cerca del código y versionada con Git
- mantenerse en Markdown simple y legible
- evitar duplicación innecesaria entre archivos
- permitir que una sesión futura recupere contexto sin depender de memoria externa
- actualizarse cuando cambie una parte relevante del stack

La documentación no es un anexo decorativo, sino parte del sistema de trabajo.

## Claude collaboration principles

La colaboración con Claude debe seguir estas reglas:

- Claude debe leer contexto antes de proponer cambios relevantes
- Claude debe apoyarse en archivos reales del proyecto
- Claude no debe inventar estructura, datos ni estado técnico no verificado
- Claude puede ayudar a planificar, redactar, refactorizar y explicar
- Claude debe separar con claridad lo existente, lo propuesto y lo hipotético
- Claude Code se usa para operar sobre el repositorio
- Claude app se usa también para estrategia, diseño de estructura y preparación conceptual

Claude debe aumentar claridad y continuidad, no introducir ruido.

## Decision rule for future changes

Cuando se evalúe un cambio importante, debe aplicarse esta regla:

1. describir el estado actual
2. definir el problema o necesidad concreta
3. comparar opciones razonables
4. elegir la opción más simple que resuelva el problema real
5. documentar la decisión si afecta arquitectura, workflow o estructura base
6. actualizar la documentación relacionada después del cambio

No se deberían introducir cambios estructurales grandes sin una justificación comprensible y verificable.

## Current non-goals

En el estado actual del proyecto, no son objetivos prioritarios inmediatos:

- añadir complejidad innecesaria de infraestructura
- ampliar el esquema SQL sin necesidad clara
- construir un sistema RAG completo antes de consolidar la base actual
- automatizar demasiadas piezas a la vez
- producir documentación extensa pero poco operativa
- adoptar herramientas nuevas solo por exploración tecnológica sin encaje concreto

El foco actual debe seguir siendo consolidar base técnica, continuidad documental y claridad operativa.