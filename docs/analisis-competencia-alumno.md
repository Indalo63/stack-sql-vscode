# Análisis competitivo y diseño del perfil alumno

> **Fecha:** 12/07/2026 · **Fuentes:** documentos aportados sobre OpoRuta y OpositaTest.
>
> ⚠️ **Cautela con las fuentes.** Los tres documentos describen a los competidores a partir de
> **su propio marketing** (la web de OpoRuta, el blog y el soporte de OpositaTest). Que OpoRuta
> diga tener "verificación determinista anti-alucinación" no prueba que la tenga: puede ser
> tecnología real o una etiqueta comercial sobre un RAG normal. Aquí se trata como **lo que
> afirman**, no como lo que hacen. Nuestro estado, en cambio, está **medido contra la base de
> datos real** (los números de este documento son reproducibles).

---

## Resumen ejecutivo

**No estamos por detrás en tecnología. Estamos por detrás en producto.**

Tenemos construido, y sin explotar, casi todo lo que OpoRuta vende como diferencial. Y tenemos
una pieza que **ninguno de los dos tiene**: un Q&A semántico sobre el BOE que hoy solo pueden
usar los editores, no los alumnos.

Los tres hallazgos que ordenan todo lo demás:

1. **Nuestras preguntas ya son anti-alucinación, pero no lo demostramos.** Medido: **78 de 78**
   preguntas generadas citan **exactamente** el artículo del que se generaron. Cero
   alucinaciones. Es consecuencia de la arquitectura (el prompt se ancla en el texto real del
   artículo del BOE). Lo que falta no es el motor: es **la comprobación automática** (~20 líneas)
   y **enseñárselo al alumno**.
2. **El "Radar del Tribunal" ya lo podemos calcular hoy**, con datos que llevan meses en la BD:
   157 preguntas de exámenes oficiales GACE 2024-2025 clasificadas por tema. El tema IV.11
   (Procedimiento Administrativo) salió **10 veces**; V.6 (retribuciones), **7**. Eso es
   priorización objetiva, y no la estamos usando para nada.
3. **Nuestro feedback al alumno es el más pobre de los tres.** Cuando falla, ve la respuesta
   correcta y un párrafo de explicación. Ni diagnóstico, ni causa del error, ni qué hacer
   después. Aquí sí vamos detrás de verdad.

---

## 1. Motor pedagógico: dónde estamos y dónde no

| | OpositaTest | OpoRuta | **Nosotros** |
|---|---|---|---|
| Qué pasa al fallar | Respuesta + justificación legal | "Corrección socrática": diagnóstico, causa, truco de memoria, acción recomendada | **Respuesta + explicación.** Nada más |
| Qué preguntar después | "Entrenador Personal": detecta materias débiles | Radar del Tribunal (frecuencia en exámenes) | **SM-2 + mix adaptativo de 4 fases** por tema oficial |
| Unidad de progreso | Materia/bloque | Artículo | **Tema oficial** (58 del programa) |

**Lo bueno, y no es poco:** nuestro motor de *selección* de preguntas es **más sofisticado que
el de OpositaTest** y probablemente que el de OpoRuta. El SM-2 con repetición espaciada y el mix
por fases (débiles/oficial/nueva) es un algoritmo de aprendizaje real, no una heurística de
"muéstrame lo que fallé". Eso no hay que tocarlo.

**Lo malo:** el motor decide *qué* preguntar de forma excelente, y luego, en el momento del
fallo —que es **el único momento en que el alumno realmente aprende**— nos limitamos a enseñar
la respuesta correcta. Es tirar por la borda el trabajo del motor.

> **La "corrección socrática" de OpoRuta no es magia.** Es una segunda llamada al modelo con el
> artículo, la pregunta, la opción elegida y la correcta, pidiéndole que explique *por qué* ese
> error concreto es un error. Nosotros tenemos las cuatro piezas en la base de datos. Es la
> mejora de **mayor impacto por menor esfuerzo** de todo este análisis.

---

## 2. Confianza en el contenido: nuestro punto fuerte camuflado

**Lo que dicen ellos:** OpoRuta vende "verificación determinista: cada cita se valida contra una
base legal antes de mostrarse; si detecta alucinación, descarta y regenera".

**Lo que hacemos nosotros:** exactamente esa arquitectura… sin la puerta de verificación y sin
contárselo a nadie.

- Las preguntas se generan **desde el texto real del artículo**, cargado del BOE y almacenado en
  `normas.articulos`. No se le pide al modelo que recuerde la ley: se le da.
- Desde hoy, cada pregunta cita el **título oficial completo** del BOE (migración 038).
- Cada pregunta está vinculada a su ley, su artículo y su tema oficial.
- **Medición real: 78/78 preguntas citan el artículo correcto.** Cero alucinaciones.

**Lo que falta (y es barato):**

1. **La puerta**: `_parse_and_validate()` comprueba estructura (opciones, respuesta, tema) pero
   **no** comprueba que el artículo citado en el enunciado sea el artículo fuente. Hoy pasa
   porque el modelo se porta bien, no porque lo impidamos. Son ~20 líneas: si no coincide, se
   descarta y se regenera.
2. **La prueba visible**: el alumno debería ver *"Verificado contra el artículo 27 de la Ley
   39/2015 — [ver texto oficial]"*, con el texto del BOE desplegable. Tenemos el artículo en la
   BD; es solo mostrarlo.

**Conclusión incómoda:** OpoRuta probablemente no tiene nada que nosotros no tengamos. Tiene una
página de marketing que lo explica. Nosotros tenemos el motor y ni siquiera lo mencionamos.

---

## 3. Qué estudiar primero: el Radar que ya tenemos

**El dato existe.** 157 preguntas de exámenes oficiales GACE 2024 y 2025, clasificadas por tema
del programa. Top real, calculado hoy contra la BD:

| Tema oficial | Veces preguntado |
|---|---|
| IV.11 — Las Leyes del Procedimiento Administrativo | **10** |
| V.6 — Sistema de retribuciones de los funcionarios | 7 |
| I.6 — El poder ejecutivo. El Presidente del Gobierno | 6 |
| II.3 — La organización de la UE (II) | 6 |
| IV.5 — Los contratos del sector público (I) | 6 |
| VI.2 — Las leyes anuales de presupuestos | 6 |

Ese ranking, mostrado al alumno, **ya es un "Radar del Tribunal"**. Y no requiere ninguna IA: es
un `GROUP BY`.

**⚠️ Un límite honesto:** OpoRuta dice hacerlo **por artículo**, no por tema. Nosotros **no
podemos** hoy: las preguntas oficiales se cargaron con `articulo = 'S/N'` (no se extrajo el
número de artículo al parsear los PDFs). Para igualarles a nivel de artículo habría que
re-procesar los exámenes oficiales extrayendo el artículo de cada pregunta. **Es un trabajo
aparte, y no es trivial** (muchas preguntas oficiales no citan el artículo explícitamente).

**Recomendación:** empezar por el Radar **por tema**, que es gratis y ya tiene señal. El de
artículo, solo si el de tema demuestra valor.

---

## 4. Retención: aquí sí estamos desnudos

| | OpositaTest | OpoRuta | **Nosotros** |
|---|---|---|---|
| Gamificación | Rankings, retos, campeonatos | Rachas de estudio | **Nada** |
| Dashboard | Estadísticas, evolución semanal | Progreso, rachas, "¿estás listo?" | **% de acierto por tema + historial de simulacros** |
| Social | Comparación con otros opositores | Individual | **Nada** |

No guardamos **ninguna noción de racha ni de constancia**: `progreso_usuario` registra qué se
respondió, pero no hay concepto de "días seguidos estudiando". Y no existe ninguna estimación de
"¿estoy listo para el examen?", que es justo la pregunta que obsesiona al opositor.

**Matiz importante según la línea de negocio:**
- **B2C:** la retención es supervivencia. Sin rachas ni dashboard, el alumno se va.
- **B2B (tu primer cliente):** la gamificación social **no le importa a la academia**. Lo que
  le importa es *demostrar que sus alumnos mejoran*. Ahí el dashboard sí es crítico, pero como
  **informe para el preparador**, no como juego para el alumno.

---

## 5. Lo que tenemos y ellos no

| Capacidad | ¿La tienen? |
|---|---|
| **Q&A semántico sobre el BOE** ("¿qué dice la LPAC sobre el silencio administrativo?") | ❌ **Ninguno de los dos.** Nosotros sí, funcionando… pero **solo para editores** |
| Fórmula de corrección oficial configurable en BD (A−E/3, sin hardcodear) | No consta |
| Arquitectura multi-oposición sin tocar código | OpoRuta sí (por oposición) |
| Simulacro con preguntas **oficiales reales** ya cargadas (209) | OpoRuta dice usar exámenes reales |

**El Q&A es el activo más desaprovechado del proyecto.** El alumno puede practicar test pero no
puede *preguntarle a la ley*. Y funciona: resuelve consultas a nivel de capítulo y título.
Dárselo al alumno es, básicamente, gratis: el motor ya está construido y probado.

---

## Backlog priorizado

Ordenado por **valor / esfuerzo**, no por vistosidad. La columna "línea" indica si es
imprescindible ya (B2B) o puede esperar (B2C).

### Prioridad 1 — Alto valor, bajo esfuerzo

| # | Qué | Por qué | Línea |
|---|---|---|---|
| 1 | **Corrección diagnóstica al fallar** (por qué te equivocaste, no solo cuál era la buena) | El momento de máximo aprendizaje, hoy desperdiciado. Es *la* diferencia entre nosotros y OpoRuta | Las dos |
| 2 | **Mostrar el artículo del BOE junto a la respuesta** ("verificado contra el art. X") | Convierte nuestra arquitectura en confianza visible. Ya tenemos el texto en BD | Las dos |
| 3 | **Puerta anti-alucinación en el generador** (descartar si la cita no coincide con el artículo fuente) | ~20 líneas. Hoy funciona por suerte, no por diseño | Las dos |
| 4 | **Dar el Q&A al alumno** | Diferencial que nadie tiene, ya construido | Las dos |
| 5 | **Radar del Tribunal por tema** (frecuencia en exámenes oficiales) | Es un `GROUP BY` sobre datos que ya existen | Las dos |

### Prioridad 2 — Alto valor, esfuerzo medio

| # | Qué | Por qué | Línea |
|---|---|---|---|
| 6 | **Informe para el preparador** (cómo van sus alumnos, dónde fallan) | Es **lo que vende el B2B**. La academia no compra gamificación: compra evidencia | **B2B** |
| 7 | **Rachas y constancia** (días seguidos, dashboard) | Retención. Requiere guardar actividad diaria | B2C |
| 8 | **"¿Estoy listo?"** (estimación de preparación a partir del % por tema y el peso oficial) | La pregunta que obsesiona al opositor. Tenemos los datos | Las dos |

### Prioridad 3 — Solo si el negocio lo pide

| # | Qué | Por qué |
|---|---|---|
| 9 | Radar **por artículo** | Exige re-procesar los exámenes oficiales (hoy `articulo = 'S/N'`). Trabajo real, valor incremental sobre el de tema |
| 10 | Gamificación social (rankings, retos) | Solo tiene sentido en B2C y con masa crítica de alumnos. Con pocos usuarios, un ranking es deprimente |
| 11 | Créditos IA / monetización por consumo | Decisión de negocio, no técnica |

---

## Lo que NO hay que copiar

- **Rankings y competición** con pocos alumnos: un ranking de 5 personas desmotiva.
- **Pago único vs suscripción**: es una decisión comercial de OpoRuta, no una ventaja técnica.
  No condiciona nada del diseño del alumno.
- **"Ilimitado teórico" de preguntas generadas**: nosotros ya podemos generar sin límite, pero
  el cuello de botella real **no es generar, es revisar**. Hoy tenemos 78 preguntas esperando
  revisión humana. Generar más sin revisar no aporta valor: lo empeora.

---

## Conclusión

El proyecto tiene un problema de **producto**, no de tecnología: el motor es mejor de lo que la
interfaz deja ver. Las cinco primeras acciones del backlog no requieren investigación ni
arquitectura nueva — solo conectar cosas que ya funcionan.

Y la más importante es la primera: **hoy, cuando el alumno falla, no aprende nada que no supiera
ya.**
