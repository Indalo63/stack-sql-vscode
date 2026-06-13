# Next Steps

## Purpose of this document

Este documento define los próximos pasos operativos del proyecto `stack-sql-vscode`.

Su función es mantener una dirección clara de avance, separando prioridades inmediatas, evolución de medio plazo y posibles expansiones futuras sin mezclar planificación con estado ya implementado.

## Current priority

La prioridad actual del proyecto no es añadir más piezas nuevas de inmediato, sino consolidar la base ya creada.

Esto significa:

- cerrar y revisar la documentación principal del proyecto
- asegurar coherencia entre archivos de contexto y estado real
- confirmar que la base PostgreSQL + Docker + `pgvector` está bien entendida y documentada
- preparar el terreno para pasos posteriores sin precipitar una expansión prematura

El foco inmediato es claridad, continuidad y control.

## Short-term next steps

Los próximos pasos de corto plazo deberían ser los siguientes:

1. completar y revisar todos los archivos de `docs/project/`
2. revisar `README.md` para asegurar alineación con la nueva estructura documental
3. verificar que `CLAUDE.md` refleja correctamente el estado, objetivos y reglas del proyecto
4. revisar la documentación SQL existente para eliminar posibles duplicidades o desalineaciones
5. validar el estado actual del contenedor PostgreSQL y de la extensión `vector`
6. dejar definido un punto de partida claro para la siguiente fase técnica

Estos pasos deben cerrar la fase de consolidación documental y operativa.

## Medium-term next steps

Una vez consolidada la base, los siguientes pasos de medio plazo podrían ser:

1. ampliar el esquema SQL con tablas o casos de uso más cercanos al trabajo vectorial
2. crear ejemplos reales de uso de `pgvector`
3. diseñar una primera tabla con embeddings
4. documentar consultas básicas de similitud
5. explorar cómo encajaría `n8n` dentro del flujo futuro del proyecto
6. definir una primera miniarquitectura para experimentos tipo RAG

Estos pasos solo deberían abordarse cuando la base actual ya esté suficientemente estable y bien documentada.

## Readiness conditions before vector work

Antes de avanzar seriamente hacia trabajo vectorial, deberían cumplirse estas condiciones mínimas:

- la documentación principal del proyecto está cerrada y coherente
- el entorno local funciona sin fricción relevante
- PostgreSQL y `pgvector` están verificados y entendidos
- existe claridad sobre el caso de uso que justificaría embeddings o búsqueda semántica
- la base relacional actual está suficientemente asentada
- el siguiente experimento técnico puede formularse como un paso pequeño y verificable

No conviene entrar en una fase vectorial real solo porque la capacidad técnica exista.

## Possible future expansions

Más adelante, el proyecto podría ampliarse en direcciones como estas:

- tablas vectoriales reales con datos de prueba
- pipeline de ingesta y generación de embeddings
- consultas híbridas relacionales + vectoriales
- integración práctica con `n8n`
- automatización parcial del flujo documental o técnico
- experimentos controlados de recuperación semántica
- evolución hacia un stack pequeño de aprendizaje aplicado sobre RAG

Estas líneas son posibilidades razonables, pero no prioridades inmediatas.

## Review rule for this file

Este archivo debe revisarse cada vez que cambie la prioridad real del proyecto.

La regla de mantenimiento es:

- mover a documentación histórica lo ya realizado
- mantener aquí solo lo que sigue pendiente o vigente
- evitar listas infladas de ideas sin compromiso operativo
- reescribir prioridades cuando cambie el foco real

El valor de este archivo depende de que siga siendo corto, concreto y verdadero.