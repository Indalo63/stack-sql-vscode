# Plan de fases — mejoras del perfil alumno

> **Origen:** `docs/analisis-competencia-alumno.md` (comparativa con OpoRuta y OpositaTest).
> **Regla de trabajo:** fases secuenciales. **No se empieza una fase sin cerrar y verificar la anterior.**
>
> Conclusión que ordena el plan: *no vamos por detrás en tecnología, sino en producto*. Casi
> todo lo de las fases 1-3 es **conectar cosas que ya funcionan**, no construir cosas nuevas.

---

## Decisiones de arquitectura (ya confirmadas, no reabrir)

1. **El diagnóstico del error se precalcula, no se genera en vivo.** Cada pregunta tiene 3
   opciones erróneas → 3 diagnósticos, generados **una vez** y reutilizados por todos los
   alumnos, para siempre. Hoy serían **627** (209 preguntas aprobadas × 3).
   - *Por qué:* el coste queda acotado y es conocido; la respuesta al alumno es instantánea;
     y **el editor puede revisarlos antes de que un alumno los vea** — que es justo el control
     de calidad que vende el B2B. Generarlos en vivo tendría coste sin techo, latencia de
     varios segundos y nadie revisaría lo que se le dice al alumno.
2. **Además, un botón "No lo entiendo, explícamelo mejor"** que sí dispara una llamada en vivo,
   personalizada. Se sirve lo precalculado al instante y la profundización es opcional.
3. **Backfill + automático**: se generan los 627 de las preguntas ya aprobadas, y a partir de
   ahí se generan solos al aprobar cada pregunta nueva. (Mismo patrón que usamos con los temas,
   que funcionó.)

---

## Fase 1 — Confianza en el contenido *(la base de todo lo demás)*

**Objetivo:** que la pregunta que ve el alumno sea demostrablemente correcta, y que él lo vea.

| # | Tarea | Detalle |
|---|---|---|
| 1.1 | **Puerta anti-alucinación en el generador** | `_parse_and_validate()` valida estructura pero **no** que el artículo citado en el enunciado sea el artículo fuente. Si no coincide → descartar y regenerar. *Hoy 78/78 aciertan, pero por buen comportamiento del modelo, no porque lo impidamos.* |
| 1.2 | **Mostrar el artículo del BOE al corregir** | "Verificado contra el art. 27 de la Ley 39/2015", con el texto oficial desplegable. El texto ya está en `normas.articulos`. |

⚠️ **Límite conocido:** el artículo solo se puede mostrar donde lo tenemos. Medido: **78/78** de
las preguntas IA, pero solo **97 de 209** oficiales (el resto se cargó sin número de artículo).
En esas, se omite el bloque sin romper nada — **no** se inventa.

**Migraciones:** ninguna.
**Hecho cuando:** una pregunta cuya cita no cuadre con su artículo fuente es rechazada
automáticamente en generación; y el alumno, al corregir, ve el texto real del BOE.

---

## Fase 2 — Corrección diagnóstica *(la de mayor impacto)*

**Objetivo:** que al fallar, el alumno aprenda algo que no sabía. Hoy solo ve cuál era la buena.

| # | Tarea | Detalle |
|---|---|---|
| 2.1 | **Migración: tabla de diagnósticos** | Uno por (pregunta, opción errónea): por qué esa opción es tentadora, cuál es la confusión de fondo, y qué repasar. Con `revisado` (control del editor). |
| 2.2 | **Generación en lote (backfill)** | Script tipo `asignar_epigrafes.py`: 627 diagnósticos para las 209 aprobadas. Con `--dry-run` para revisar calidad antes de guardar. |
| 2.3 | **Generación automática al aprobar** | Al pulsar "Aprobar" en Revisar preguntas, se generan sus 3 diagnósticos. |
| 2.4 | **Mostrarlo al alumno** | Al fallar: no solo "la correcta era la b", sino *por qué* su opción era tentadora y qué confundió. |
| 2.5 | **Botón "explícamelo mejor"** | Llamada en vivo, opcional, personalizada. |

**Migraciones:** 1 (tabla nueva).
**Riesgo a vigilar:** el coste de la generación en vivo (2.5) es el único no acotado. Conviene
limitarlo por alumno (p. ej. N al día) — **decidir el límite al implementar**.
**Hecho cuando:** un alumno falla una pregunta y recibe un diagnóstico útil al instante, sin
esperar a ninguna llamada.

---

## Fase 3 — Explotar lo que ya tenemos y no usamos

**Objetivo:** dos funciones de alto valor que son, literalmente, conectar cables.

| # | Tarea | Detalle | Esfuerzo |
|---|---|---|---|
| 3.1 | **Radar del Tribunal (por tema)** | Frecuencia de cada tema en los exámenes oficiales. Es un `GROUP BY` sobre datos que ya existen: 157 preguntas oficiales clasificadas (IV.11 salió 10 veces, V.6 siete). Se muestra al elegir qué estudiar. | Muy bajo |
| 3.2 | **Q&A semántico para el alumno** | Está construido, probado y funcionando… pero **solo lo usan los editores**. **Ningún competidor lo tiene.** | Bajo |

**Migraciones:** ninguna.
**Decidir al implementar:** si el Q&A del alumno lleva algún límite de uso (tiene coste de API).
**Hecho cuando:** el alumno ve qué temas caen más en el examen real, y puede preguntarle a la ley.

---

## Fase 4 — Informe para el preparador *(lo que vende el B2B)*

**Objetivo:** que la academia vea que sus alumnos mejoran. **Es el argumento de venta de tu
primer cliente de pago.**

| # | Tarea | Detalle |
|---|---|---|
| 4.1 | **Vínculo alumno ↔ academia** | **Hoy no existe** (ver `docs/roles-y-permisos.md` §4). Sin esto, una academia no puede ver "sus" alumnos, y un simulacro autorizado se abre a *todos*. Es el cuello de botella real del B2B. |
| 4.2 | **Informe por alumno y por grupo** | Progreso por tema, temas flojos, evolución. Aquí **sí** se muestra el desglose que al alumno se le oculta (débiles/oficial/nueva y la fase), que ya está reservado para esto por la regla de producto del Paso 7. |

**Migraciones:** al menos 1 (relación alumno↔academia).
⚠️ **Es la fase con más diseño pendiente**, no solo implementación: hay que decidir el modelo
multi-academia. Requerirá su propia ronda de decisiones.

---

## Fase 5 — Retención *(sobre todo B2C)*

| # | Tarea | Detalle |
|---|---|---|
| 5.1 | **Rachas y constancia** | Hoy **no existe ningún concepto de racha**: guardamos qué se respondió, no cuándo se estudió de forma continuada. |
| 5.2 | **"¿Estoy listo para el examen?"** | La pregunta que obsesiona al opositor. Se puede estimar con el % por tema y el peso oficial de cada bloque — datos que ya tenemos. |

**Nota:** la 5.2 aporta valor **también en B2B** (la academia quiere saberlo de sus alumnos).
La 5.1 es puramente B2C.

---

## Lo que NO vamos a hacer (y por qué)

| Descartado | Motivo |
|---|---|
| **Rankings y competición social** | Con pocos alumnos, un ranking de 5 personas desmotiva. Solo tiene sentido con masa crítica. |
| **Radar por artículo** (como dice OpoRuta) | Exige re-procesar los exámenes oficiales: hoy 112 de 209 preguntas tienen `articulo = 'S/N'`. Trabajo real, valor incremental pequeño sobre el radar por tema. |
| **Generar más preguntas** | **El cuello de botella no es generar, es revisar.** Hay 78 esperando revisión. Generar más sin revisar empeora el problema, no lo resuelve. |
| **Créditos IA / pago por consumo** | Decisión de negocio, no de producto. No condiciona nada del diseño del alumno. |

---

## Orden y dependencias

```
Fase 1 (confianza)  ─┬─→  Fase 2 (diagnóstico)  ──→  Fase 5.2 (¿estoy listo?)
                     │
                     └─→  Fase 3 (radar + Q&A)   [independiente, se puede adelantar]

Fase 4 (B2B)  ── requiere decidir antes el modelo alumno↔academia
Fase 5.1 (rachas) ── independiente, B2C
```

- **Las fases 1 y 2 van juntas y en ese orden:** no tiene sentido diagnosticar un error sobre
  una pregunta cuya corrección no está verificada.
- **La fase 3 es independiente**: si en algún momento hace falta una victoria rápida y visible,
  se puede adelantar (son las tareas más baratas de todo el plan).
- **La fase 4 es la más valiosa comercialmente** (es lo que le vendes a la academia) pero es la
  que más diseño pendiente tiene. No se puede improvisar.

**Propuesta de arranque:** Fase 1 → Fase 2. Son las que convierten el motor que ya tenemos en
producto visible, y la 2 es la que de verdad nos separa de la competencia.
