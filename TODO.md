# TODO – Plataforma IA de Preparación de Oposiciones

Backlog completo. El estado macro y el hito inmediato viven en `CLAUDE.md`.

## Mapeo de leyes cargadas (`normas.*`)

| ley_id | Código | Nombre | Estado |
|--------|--------|--------|--------|
| 1 | CE | Constitución Española 1978 | ✅ cargada |
| 4 | LPAC | Ley 39/2015 Procedimiento Administrativo Común | ✅ cargada |
| 7 | LRJSP | Ley 40/2015 Régimen Jurídico Sector Público | ✅ cargada |
| 8 | TREBEP | RDL 5/2015 Estatuto Básico Empleado Público | ✅ cargada |
| 9 | LGP | Ley 47/2003 General Presupuestaria | ✅ cargada |
| 12 | LCSP | Ley 9/2017 Contratos Sector Público | ✅ cargada |
| 14 | GACE_NORM | Normativa Oposición GACE (criterios + programa) | ✅ cargada |
| 15 | LODP | LO 3/1981 Defensor del Pueblo | ✅ cargada |
| 17 | LOTC | LO 2/1979 Tribunal Constitucional | ✅ cargada |
| 18 | LGOB | Ley 50/1997 del Gobierno | ✅ cargada |
| 19 | LOCE | LO 3/1980 Consejo de Estado | ✅ cargada |
| 20 | LBRL | Ley 7/1985 Bases del Régimen Local | ✅ cargada |
| 21 | LTBG | Ley 19/2013 Transparencia y Buen Gobierno | ✅ cargada |
| 22 | LOPD | LO 3/2018 Protección de Datos | ✅ cargada |
| 23 | LOEPSF | LO 2/2012 Estabilidad Presupuestaria | ✅ cargada |
| 26 | LOPJ | LO 6/1985 Poder Judicial | ✅ cargada |
| 27 | LGSS | RDL 8/2015 Ley General Seguridad Social | ✅ cargada |
| 29 | LTPP | Ley 8/1989 Tasas y Precios Públicos | ✅ cargada |
| 31 | LGT | Ley 58/2003 General Tributaria | ✅ cargada |
| 33 | TUE | Tratado de la Unión Europea (consolidada 2016) | ✅ cargada |
| 34 | TFUE | Tratado de Funcionamiento de la UE (consolidada 2016) | ✅ cargada |
| 35 | LOIEMH | LO 3/2007 Igualdad Efectiva de Mujeres y Hombres | ✅ cargada |
| 36 | LOIVG | LO 1/2004 Violencia de Género | ✅ cargada |
| 37 | LJCA | Ley 29/1998 Jurisdicción Contencioso-Administrativa | ✅ cargada |
| 38 | LGS | Ley 38/2003 General de Subvenciones | ✅ cargada |
| 39 | LEF | Ley de Expropiación Forzosa (1954) | ✅ cargada |
| 40 | LPAP | Ley 33/2003 Patrimonio de las Administraciones Públicas | ✅ cargada |
| 42 | RIRS | RD 462/2002 Indemnizaciones por Razón del Servicio | ✅ cargada |
| 43 | MUFACE | RD 375/2003 Reglamento General del Mutualismo Administrativo | ✅ cargada |
| 44 | LMRFP | Ley 30/1984 Medidas para la Reforma de la Función Pública | ✅ cargada |
| 45 | RDSA | RD 365/1995 Situaciones Administrativas Funcionarios AGE | ✅ cargada |
| 46 | RDRD | RD 33/1986 Régimen Disciplinario Funcionarios AGE | ✅ cargada |
| 47 | REGI | RD 364/1995 Reglamento General de Ingreso AGE | ✅ cargada |
| 48 | LOTCU | LO 2/1982 Tribunal de Cuentas | ✅ cargada |
| 49 | ET | RDLeg 2/2015 Estatuto de los Trabajadores | ✅ cargada |
| 50 | LOIT | Ley 15/2022 Igualdad de Trato y No Discriminación | ✅ cargada |
| 51 | LASEE | Ley 2/2014 Acción y Servicio Exterior del Estado | ✅ cargada |
| 53 | ENI | RD 4/2010 Esquema Nacional de Interoperabilidad | ✅ cargada |
| 57 | CC | Código Civil (RD 24 julio 1889) | ✅ cargada |
| 58 | LPNAT | Ley 42/2007 Patrimonio Natural y Biodiversidad | ✅ cargada |
| 59 | LE | Ley 3/2023 de Empleo | ✅ cargada |
| 60 | RLEF | Reglamento de la Ley de Expropiación Forzosa (Decreto 657/1957) | ✅ cargada |
| 61 | RLGS | Reglamento de la Ley General de Subvenciones (RD 887/2006) | ✅ cargada |
| 62 | BCPSA | Bases comunes procesos selectivos AGE (RD 364/2017) | ✅ cargada |
| 63 | RRCP | Reglamento del Registro Central de Personal (RD 2073/1999) | ✅ cargada |
| 64 | IGAE | Reglamento control interno IGAE (RD 2188/1995) | ✅ cargada |
| 65 | ACF | Reglamento Anticipos de Caja Fija (RD 725/1989) | ✅ cargada |
| 66 | PLJ | Reglamento pagos librados a justificar (RD 640/1987) | ✅ cargada |
| 67 | ROCE | Reglamento Orgánico del Consejo de Estado (RD 1674/1980) | ✅ cargada |

## Pendientes de carga – inventario BOE-443

Estrategia por ley: `parse_boe.py <ELI> --output data/leyes/XX.json` → `load_ley.py XX.json --supabase --embeddings`

> Las fichas BOE con el Permalink ELI de cada norma se localizan en `https://www.boe.es/buscar/act.php?id=<BOE-ID>`.

### FASE 4 – ALTA prioridad (directamente examinables en GACE)

| Código | Ley | BOE-ID |
|--------|-----|--------|
| ~~LPAP~~ | ~~Ley 33/2003 Patrimonio de las Administraciones Públicas~~ | ~~BOE-A-2003-20254~~ |
| ~~RIRS~~ | ~~RD 462/2002 Indemnizaciones por Razón del Servicio~~ | ~~BOE-A-2002-10337~~ |
| ~~MUFACE~~ | ~~RD 375/2003 Reglamento General Mutualismo Administrativo~~ | ~~BOE-A-2003-7527~~ |
| ~~LMRFP~~ | ~~Ley 30/1984 Medidas Reforma Función Pública~~ | ~~BOE-A-1984-17387~~ |
| ~~RDSA~~ | ~~RD 365/1995 Situaciones Administrativas Funcionarios AGE~~ | ~~BOE-A-1995-8730~~ |
| ~~RDRD~~ | ~~RD 33/1986 Régimen Disciplinario Funcionarios AGE~~ | ~~BOE-A-1986-1216~~ |
| ~~REGI~~ | ~~RD 364/1995 Reglamento General de Ingreso AGE~~ | ~~BOE-A-1995-8729~~ |
| ~~LOTCU~~ | ~~LO 2/1982 Tribunal de Cuentas~~ | ~~BOE-A-1982-11584~~ |
| ~~ET~~ | ~~TR Ley del Estatuto de los Trabajadores~~ | ~~BOE-A-2015-11430~~ |

### FASE 4 – MEDIA prioridad

| Código | Ley | BOE-ID |
|--------|-----|--------|
| ~~LOIT~~ | ~~Ley 15/2022 Igualdad de Trato y No Discriminación~~ | ~~BOE-A-2022-11589~~ |
| LCCU | IV Convenio Colectivo Único Personal Laboral AGE | BOE-A-2019-7414 | ⚠️ No tiene ELI consolidado en BOE. Estructura de Resolución/Convenio (cláusulas y anexos), incompatible con parse_boe.py. Requiere parser específico. Prioridad: MEDIA. |
| ~~LASEE~~ | ~~Ley 2/2014 Acción y Servicio Exterior del Estado~~ | ~~BOE-A-2014-3248~~ |
| PGCP | Plan General de Contabilidad Pública 2010 | BOE-A-2010-6710 | ⚠️ Parser captura solo 65 arts. normativos (Orden EHA/1037/2010). Faltan los anexos con el plan de cuentas (grupos, subgrupos, cuentas con definiciones y relaciones de cargo/abono). Requiere parser específico para tablas contables. Prioridad: MEDIA. |
| ~~ENI~~ | ~~Esquema Nacional de Interoperabilidad~~ | ~~BOE-A-2010-1331~~ |
| ~~CC~~ | ~~Código Civil (1889)~~ | ~~BOE-A-1889-4763~~ |
| ~~LPNAT~~ | ~~Ley 42/2007 Patrimonio Natural y Biodiversidad~~ | ~~BOE-A-2007-21490~~ |
| ~~LE~~ | ~~Ley 3/2023 de Empleo~~ | ~~BOE-A-2023-5365~~ |

### FASE 5 – Reglamentos de desarrollo (necesarios para supuestos prácticos)

Prioridad elevada a FASE 5 por su incidencia directa en los supuestos prácticos GACE
(procedimientos detallados, plazos, órganos competentes, formularios).
Se cargan **antes** de generar el banco de preguntas IA.

#### FASE 5A – Reglamentos de función pública y procedimiento (alta incidencia en supuestos)

| Código | Nombre | BOE-ID |
|--------|--------|--------|
| ~~RLEF~~ | ~~Reglamento Ley Expropiación Forzosa~~ | ~~BOE-A-1957-7998~~ |
| ~~RLGS~~ | ~~Reglamento Ley General de Subvenciones~~ | ~~BOE-A-2006-13371~~ |
| ~~BCPSA~~ | ~~Bases comunes procesos selectivos AGE~~ | ~~BOE-A-2017-8652~~ |
| ~~RRCP~~ | ~~Reglamento Registro Central de Personal~~ | ~~BOE-A-2000-1007~~ |
| ~~IGAE~~ | ~~Control interno IGAE (RD 2188/1995)~~ | ~~BOE-A-1996-1578~~ |
| ~~ACF~~ | ~~Anticipos de Caja Fija (RD 725/1989)~~ | ~~BOE-A-1989-14441~~ |
| ~~PLJ~~ | ~~Pagos librados a justificar (RD 640/1987)~~ | ~~BOE-A-1987-12158~~ |
| ~~ROCE~~ | ~~Reglamento Orgánico del Consejo de Estado~~ | ~~BOE-A-1980-18703~~ |

#### ~~FASE 5B~~ – ~~Leyes complementarias (media incidencia en supuestos)~~ ✅ COMPLETADA

| Código | Nombre | BOE-ID | Arts. | ley_id |
|--------|--------|--------|-------|--------|
| ~~LGPD~~ | ~~TR Ley General derechos personas con discapacidad~~ | ~~BOE-A-2013-12632~~ | 128 | 68 |
| ~~LAEPD~~ | ~~RD 2271/2004 Acceso empleo discapacidad~~ | ~~BOE-A-2004-21221~~ | 17 | 69 |
| ~~LSSF~~ | ~~TR Ley SS Funcionarios Civiles del Estado~~ | ~~BOE-A-2000-12140~~ | 54 | 70 |
| ~~LDEP~~ | ~~TR Ley de Empleo (RDLeg 3/2015)~~ | ~~BOE-A-2015-11431~~ | 61 | 71 |
| ~~LOE~~ | ~~LO 2/2006 Educación~~ | ~~BOE-A-2006-7899~~ | 250 | 72 |
| ~~LO4000~~ | ~~LO 4/2000 Extranjeros en España~~ | ~~BOE-A-2000-544~~ | 117 | 73 |
| ~~LASIL~~ | ~~Ley 12/2009 Derecho de Asilo~~ | ~~BOE-A-2009-17242~~ | 64 | 74 |
| ~~LTRANS~~ | ~~Ley 4/2023 Trans e igualdad LGTBI~~ | ~~BOE-A-2023-5366~~ | 108 | 75 |
| ~~LGUM~~ | ~~Ley 20/2013 Garantía Unidad de Mercado~~ | ~~BOE-A-2013-12888~~ | 47 | 77 |
| ~~LGT22~~ | ~~Ley 11/2022 General de Telecomunicaciones~~ | ~~BOE-A-2022-10757~~ | 158 | 78 |
| ~~LEPP~~ | ~~Ley 27/2022 Evaluación Políticas Públicas AGE~~ | ~~BOE-A-2022-21677~~ | 42 | 79 |

## Próximos pasos

### 🔴 APROBADO Y PENDIENTE DE IMPLEMENTAR — Teoría de test (12/07/2026)

Aprobado por el usuario en la sesión del 12/07/2026. **Orden de ejecución: 1 → 2 → resto.**

#### 1. ✅ HECHO (12/07/2026) — Sesgo de la opción "a"
**Medido:** el **86,4%** de las 88 preguntas IA tienen la respuesta correcta en la **opción "a"** (b: 6,8% · c: 5,7% · d: 1,1%). El examen oficial real está equilibrado (a: 27,8% · b: 22,5% · c: 31,6% · d: 18,2%).

**Por qué es grave:** el alumno aprende *"ante la duda, marca la a"*, acierta sin saber la ley, y esa costumbre **le perjudica en el examen real**. Además **invalida nuestras métricas** (dominio, dificultad empírica, "¿estoy listo?"): miden a alguien que adivina el patrón, no que aprende.

- [x] Barajado **dirigido** de las 88 (no aleatorio: el aleatorio deja el reparto desigual). Clave al **25,0% exacto**. `scripts/equilibrar_clave.py`.
- [x] **Remapeo de las letras dentro de la explicación**: 59 de 88 citaban las opciones por letra ("La opción b) es incorrecta…") y habrían quedado señalando a la opción equivocada. No toca las referencias a artículos (`artículo 10.2.c)`). Validación automática: **0 incoherencias**.
- [x] Barajado **en el generador** (`build_test_bank._barajar_opciones`), verificado con 400 generaciones: 23,8/24,0/25,2/27,0%.
- [x] Las preguntas **oficiales no se tocaron**: son el examen real.

#### 2. ✅ HECHO (12/07/2026, migración 048) — Guardar QUÉ opción eligió el alumno
`progreso_usuario` solo guarda `ultima_correcta` (sí/no). **Se está tirando la señal pedagógica más valiosa.** Sin ella no hay análisis de distractores, ni diagnóstico real del error, ni detección de preguntas rotas.

- [x] `normas.respuestas`: una fila por CADA respuesta (`opcion_elegida`, **NULL = en blanco**, `correcta`, `contexto`, `segundos` para el futuro cronómetro).
- [x] `registrar_respuesta()` enganchado en los 4 modos del alumno. **Registra también las dejadas en blanco**: con A−E/3, dejar en blanco es una decisión estratégica (habilita el punto 4).
- [x] `analisis_distractores()` ya operativo: detecta **distractores muertos** y preguntas **sospechosas** (un distractor gana a la correcta → clave mal marcada o pregunta ambigua).
- [x] El script de limpieza del MVP borra también esta tabla.

#### 3. ✅ HECHO (12/07/2026, migración 049) — Discriminación del ítem
La dificultad es solo **la mitad** de la teoría clásica de test. La otra mitad: ¿la pregunta **distingue** al que sabe del que no?

- [x] `scripts/analisis_items.py`: correlación biserial-puntual con la capacidad **corregida** (excluye el propio ítem, o se correlacionaría consigo misma). Alertas: `clave_sospechosa` · `no_discrimina` · `distractor_muerto`.
- [x] **Validado plantando un defecto**: 30 alumnos sintéticos + una pregunta con la clave mal marcada a propósito. El detector la cazó (**discriminación −0,44**) sin falsas alarmas graves.
- [x] Umbral corregido: la alerta grave exige `d < −0,10`. Con `d < 0` a secas, una pregunta sana con −0,02 (ruido) saltaba como grave — **un detector que grita "lobo" no sirve**.
- [x] Sección **"Calidad del banco"** en el panel de admin.
- [ ] ⚠️ **Ejecutarlo cuando haya alumnos**: con 2 no dice nada (no hay variabilidad de capacidad). Madura con decenas.

#### 4. [✅ HECHO 12/07/2026 — migración 050] Calibración de confianza y decisión de dejar en blanco
La fórmula oficial es **A − E/3**: responder a ciegas **resta**. Saber **cuándo NO contestar** es una destreza entrenable, y **ningún competidor la entrena**. Es específica de las oposiciones españolas.

- [✅ Migración 050] `respuestas.confianza` (`seguro` | `dudo` | `ni_idea`, NULL si no la declara). Se pide **antes** de corregir: sin ese dato, **acertar por saberlo y acertar por suerte son indistinguibles** en la base de datos. `parametros_aprendizaje.min_respuestas_calibracion` (10) en BD.
- [✅ `retrieval.get_umbral_rentabilidad()`] El umbral **se deriva de `convocatorias`, no se hardcodea**: `p* = (pen_error − pen_blanco) / (valor_acierto + pen_error)`. Con GACE da **25,0%** — exactamente el azar de 4 opciones. Conclusión contraintuitiva que se le enseña al alumno: **"ante la duda, en blanco" es matemáticamente FALSO**; descartar una sola opción sube el acierto a 1/3 y responder ya SUMA. Otra oposición con otra fórmula obtiene su propio umbral sin tocar código.
- [✅ `retrieval.get_calibracion()`] Detecta las **dos patologías caras**, invisibles sin este dato:
  - **Exceso de confianza** — falla diciendo "lo sé". Lo grave no es el fallo: es que **nunca lo repasará**, porque cree dominarlo.
  - **Exceso de prudencia** — deja en blanco lo que habría acertado. Regala puntos evitando una penalización que no le salía a cuenta evitar.
  - Además: **calibración monótona** (¿acierta más cuanto más seguro dice estar?) y **puntos/pregunta** por nivel de confianza, en la escala de la fórmula oficial.
- [✅ `streamlit_app.py`] Selector 🟢 Lo sé / 🟡 Dudo / 🔴 Ni idea en **Repaso** y **Simulacro personal** (no en la prueba de nivel: 40 preguntas ya son mucha fricción para el onboarding; no en el simulacro de academia: es el examen de la academia, no un entrenamiento). Aviso en el sitio al fallar diciendo "lo sé". Panel **"¿Sabes lo que sabes?"** en Mi progreso.
- [⚠️ Regla] Con menos de `min_respuestas_calibracion` en un nivel **no se da diagnóstico**: un consejo mal fundado es peor que ninguno.
- [✅ Validado plantando las dos patologías] Alumno de laboratorio con exceso de confianza (58,3% acertando cuando dice "seguro") y exceso de prudencia (41,7% de acierto con "ni idea" —por encima del 25%— y 6 en blanco): **las dos cazadas**, con el texto correcto. Datos borrados. Verificado además en navegador real: el selector aparece, el aviso de "dijiste que lo sabías" salta, y el panel de Mi progreso muestra el umbral 25,0% leído de BD. Sin errores de consola.

#### 5. [✅ HECHO 12/07/2026 — migración 051] Práctica intercalada (interleaving)
El repaso era **por tema, en bloque** — y la práctica en bloque produce **fluidez falsa**: mientras machacas LPAC tienes su esquema cargado, aciertas, y concluyes que te la sabes. El examen te la mezcla con la LRJSP y ahí se ve que no. Practicar cada ley por separado **no entrena la distinción**; entrena a responder cuando ya te han dicho de qué ley va.

- [✅ Migración 051] `normas.pares_confundibles`. **Los pares no se escriben a mano: se DERIVAN de `epigrafe_leyes`** — dos leyes son confundibles si el programa oficial las estudia juntas. Se mide con **Jaccard** (compartidos / totales), no con el conteo bruto, porque el conteo premia a las leyes **ubicuas** (la CE1978 sale en 28 temas: comparte con todo, y no se confunde con todo).
- [✅ `scripts/calcular_confundibles.py`] Re-ejecutable (borra e inserta). Resultado sobre GACE: **19 pares**, y son justo los que un opositor reconocería — **LPAC/LRJSP (0,75)**, ley y su reglamento (LGS/RLGS 0,80, LEF/RLEF), TUE/TFUE (1,00), TREBEP/RIRS, LGP/LOEPSF. **La fórmula sola encontró el par que el usuario había citado de memoria.**
- [✅ `retrieval.get_grupos_intercalados()`] Solo ofrece los pares en los que el alumno **ya tiene base en las DOS leyes** (`min_vistas_intercalada`, 5, en BD).
- [✅ `retrieval._intercalar()`] **No baraja al azar**: el azar deja rachas, y una racha de cuatro LPAC seguidas *es* la práctica en bloque que queremos evitar. Alterna estrictamente mientras haya alternativa. Verificado: 0 rachas en la tanda servida.
- [✅ `streamlit_app.py`] Repaso gana un selector **Por tema / Intercalada**. Al terminar, **desglose de acierto por ley**: si una de las dos se hunde, ahí está la confusión ("no es que no te la sepas, es que se te va detrás de la otra").
- [⚠️ **Dificultad deseable, y hay que decirlo**] Intercalar **empeora el rendimiento mientras se practica** y lo **mejora en el examen**. Dos consecuencias que NO son opcionales: (1) **no se le sirve a un principiante** en esa materia — mezclar antes de tener base impide construir la primera representación, no enseña a discriminar; (2) **se le avisa de que va a fallar más**, o creerá que la app ha empeorado y se volverá al modo que le engaña.
- [✅ Verificado en navegador real] El par LPAC/LRJSP aparece, la tanda alterna **LPAC-LRJSP-LPAC-LRJSP…** (0 rachas), el aviso de "vas a fallar más" se muestra, y el resultado desglosa por ley. Sin errores de consola. Datos sembrados para la prueba, borrados.

#### 6. Cronómetro y gestión del tiempo — ✅ HECHO 12/07/2026 (migración 052)
El examen real: 100 preguntas en 90 minutos = **54 segundos por pregunta**. El simulacro no cronometraba, así que simulaba el examen **menos la restricción que más gente tumba**. Y hay una destreza que sin reloj no se puede ni empezar a entrenar: **repartir el tiempo**. Atascarse en la 12 y no llegar a las 20 últimas cuesta más puntos que no saberse un tema entero.

- [✅ La duración NO se hardcodea] Sale de `convocatorias` (`tiempo_minutos` / `num_preguntas`, migración 022): 54 s/pregunta, así que un simulacro de 50 hereda 45 minutos. Si mañana la convocatoria cambia el reloj, el simulacro cambia solo. `retrieval.get_tiempo_simulacro()`.
- [✅ Entrega automática] Al llegar a cero se corrige solo, con lo que haya. Decisión del usuario, y es la fiel: en el examen no hay prórroga. Cuenta atrás en vivo con `st.fragment(run_every=1)` — **solo se repinta el reloj**, no las 50 preguntas. El tiempo se calcula contra la marca de inicio del servidor, no con un contador, así que **sigue corriendo aunque el alumno cierre la pestaña**.
- [⚠️ **El hallazgo que no estaba en este TODO**] En cuanto el reloj entrega solo, aparece un **blanco nuevo**: el de la pregunta **a la que no llegó**. En la BD se veía idéntico al blanco estratégico de la migración 050 (`opcion_elegida NULL`), y confundirlos rompía **tres** cosas: (1) `get_calibracion()` le habría dicho *"eres demasiado prudente, contesta más"* al que en realidad **va lento** — el consejo justo al revés; (2) **envenenaba la dificultad empírica y la discriminación del ítem**: las preguntas del **final** del examen son a las que menos gente llega, así que acumularían filas `correcta=FALSE` y **parecerían imposibles por su posición**, no por su contenido — el detector de preguntas rotas empezaría a señalar preguntas sanas; (3) falseaba el análisis de distractores. Por eso `respuestas.blanco_por_tiempo`, excluido ya en `get_calibracion`, `analisis_distractores` y `scripts/analisis_items.py`. Criterio **conservador**: solo se marca la que **no tocó en absoluto** (ni respuesta ni confianza declarada). Si la vio y decidió callar, **eso es una decisión y se respeta**.
- [⚠️ **Fallo de método detectado en la verificación**] La primera versión medía `ritmo = segundos / n_preguntas`. Pero **quien agota el reloj consume el tiempo entero**, así que le salía clavado el ritmo objetivo (54,0) y la app le decía *"vas justo, pero llegas"* **debajo del aviso de que se había quedado sin tiempo**. El denominador honrado son **las preguntas a las que llegó** (`historial_simulacros.sin_llegar`): con él, el mismo intento pasa de "54 s/pregunta, vas bien" a **"108 s/pregunta, margen −100%"**, que es la verdad.
- [✅ `streamlit_app.py`] Reloj + aviso al 15% restante en **los dos simulacros** (personal y academia). Resultado con tiempo empleado y ritmo. Panel **"¿Le da el tiempo?"** en Mi progreso: ritmo real vs. el del examen, y cuántas preguntas se ha quedado **sin leer**.
- [✅ Tiempo por pregunta] `respuestas.segundos`, que llevaba vacío desde la migración 048, ya se rellena: se sella al contestar por primera vez. **Es una aproximación y está documentado como tal**: en un examen de una sola página (donde se puede saltar y volver, como en el real), el rato que se pasa leyendo las preguntas que salta se le atribuye a la siguiente que contesta.
- [✅ Verificado en navegador real] Simulacro personal: reloj de 45:00 descontando, tiempos por pregunta sellados (11, 5, 7 s), intento guardado (31 s de 2700). Simulacro de academia de 2 preguntas (reloj de 108 s) **dejando que llegara a cero**: entrega automática a los 108 s exactos, `tiempo_agotado=TRUE`, la contestada con sus segundos y **la que no tocó marcada `blanco_por_tiempo=TRUE`**. Sin errores de consola. Datos de prueba borrados.
- [→] **Lo que queda del cronómetro no es código, es esperar datos:** el ritmo **por bloque y por tema** ("¿en qué materia se te va el tiempo?"). Los segundos ya se guardan; falta el agregado, y hoy no hay ni una respuesta cronometrada real que agregar. **Anotado con su disparador en la deuda empírica, punto 3.bis.**

---

### 🔬 Pendiente — Lo que solo se puede cerrar CON ALUMNOS REALES (12/07/2026)

Todo esto está **construido y funcionando**, pero calibrado con conjeturas o valores por defecto. **No se puede validar sin datos de alumnos.** No es deuda técnica: es deuda *empírica*.

#### 1. La dificultad de las preguntas es una CONJETURA, no un dato
- **Estado:** las 297 preguntas tienen `dificultad_origen = 'heuristica'` (migración 047): un valor provisional sacado de señales del texto. **Nadie ha comprobado que acierte.**
- [ ] **Ejecutar periódicamente** `python3 scripts/calcular_dificultad.py --supabase --solo-empirica`. Sustituye la conjetura por el % de acierto real en cuanto una pregunta acumula `min_respuestas_dificultad` (20, en `parametros_aprendizaje`).
- [ ] **Validar la heurística**: cuando haya datos, comparar `heuristica` vs `empirica` en las preguntas que tengan ambas. **Si no correlacionan, la heurística es ruido y hay que tirarla**, no maquillarla. Es la única forma de saber si vale.
- ⚠️ **Realidad de escala:** calibrar el banco entero exige **~4.860 respuestas** (243 preguntas × 20). Con **2 alumnos** eso no va a pasar: el umbral solo se alcanzará en las preguntas más servidas. **La dificultad empírica madura con escala** (una academia con decenas de alumnos), no con el MVP. Si se quiere ver antes, se puede bajar el umbral — pero por debajo de ~10 respuestas el dato es ruido.

#### 2. Los parámetros pedagógicos están puestos "a ojo"
`normas.parametros_aprendizaje` — **están en BD precisamente para calibrarlos sin desplegar**:

| Parámetro | Valor hoy | Qué hay que mirar con alumnos reales |
|---|---|---|
| `muestra_minima` | 5 | ¿Con 5 preguntas el dominio de un tema ya significa algo, o sigue siendo ruido? |
| `umbral_dominio` | 70% | ¿Los alumnos que lo superan aprueban de verdad el simulacro? |
| `repeticiones_ok` | 2 | ¿Dos aciertos seguidos bastan para dar una pregunta por asentada? |
| `cobertura_bloque` | 60% | ¿Es alcanzable sin frustrar, o hay que bajarlo? |
| `min_respuestas_dificultad` | 20 | Ver punto 1 |

- [ ] Revisar estos cinco tras las primeras semanas de uso real.

#### 3. Funciones que solo tienen sentido con historial
- [ ] **"¿Estoy listo para el examen?"** (Fase 5.2): necesita que el SM-2 haya acumulado `intervalo` y `proxima_revision` durante semanas. Con un alumno recién llegado no se puede proyectar nada.
- [ ] **Rachas y constancia** (Fase 5.1): necesita días de actividad. Hoy no se guarda ningún registro diario.
- [ ] **Informe para el preparador** (Fase 4): sin alumnos con recorrido, el informe está vacío.

#### 3.bis Ritmo por bloque y por tema — *"¿en qué materia se te va el tiempo?"* (anotado 12/07/2026)
**Los datos ya se están guardando** desde la migración 052 (`respuestas.segundos`, sellado en cada simulacro cronometrado). Lo que falta es la **agregación** y la pantalla. Es deliberadamente lo siguiente, no lo de ahora, y por una razón concreta:

- **Hoy no diría nada.** No hay **ni una sola** respuesta cronometrada real: las de la verificación eran de laboratorio y se borraron. Un desglose de ritmo por bloque construido sobre 3 respuestas es una gráfica bonita que miente.
- **Es el mismo error que ya cometimos** con la dificultad heurística: publicar una cifra provisional que nadie ha comprobado y que el alumno lee como si fuera un dato. Esta vez el dato **llega solo** con el uso; basta con esperar a tenerlo.

**Disparador — cuándo incorporarlo:** cuando haya alumnos reales con **varios simulacros cronometrados** a la espalda (orden de magnitud: unas 200-300 respuestas con `segundos IS NOT NULL` por alumno, o sea 4-6 simulacros). Antes de eso, la señal está dominada por el ruido de una sola tanda.

**Qué habría que hacer entonces (no antes):**
- [ ] `retrieval.get_ritmo_por_bloque(user_id, oposicion_id)` — `AVG(segundos)` de `respuestas` agrupado por bloque y por tema, vía `preguntas_test.ley_id`/`epigrafe_id`. Excluir `blanco_por_tiempo` (esas no tienen segundos) y **excluir el repaso**: sin reloj ni penalización, el alumno se toma su tiempo y el dato no es comparable con el del examen.
- [ ] Contrastar el ritmo de cada bloque con el **objetivo** (54 s) y con **su propio acierto** en ese bloque. El cruce es lo que de verdad diagnostica, y son **cuatro** casos con remedios distintos: *lento y falla* (no se lo sabe) · ***lento y acierta* (se lo sabe pero le cuesta: es el caso que más puntos regala, porque llega al final sin tiempo sabiéndoselo)** · *rápido y falla* (va a ciegas, o se confía) · *rápido y acierta* (dominado).
- [ ] Validar antes de enseñárselo a nadie que el ritmo por tema es **estable entre simulacros** del mismo alumno. Si un tema le sale a 40 s en uno y a 90 s en el siguiente, lo que estamos midiendo es el orden de las preguntas, no la materia.
- [ ] ⚠️ **Límite conocido y heredado:** `respuestas.segundos` es una **aproximación** (el examen es de una sola página: el rato de leer las preguntas que salta se le atribuye a la siguiente que contesta). Para el agregado por bloque el ruido se compensa; **para una pregunta suelta, no** — así que no se muestra "esta pregunta te llevó X segundos".

#### 4. Lo que hay que vigilar cuando entren los 2 alumnos
- [ ] ¿La regla de dominio **frustra**? (un bloque que no se da por estudiado pese a ir bien).
- [ ] ¿La prueba de nivel del veterano **detecta** de verdad sus lagunas por bloque?
- [ ] ¿El plan de partida del principiante le resulta **útil o arbitrario**?

### 📊 Backlog del perfil alumno — del análisis competitivo (12/07/2026)

Análisis completo (con datos medidos contra la BD, no impresiones) en **`docs/analisis-competencia-alumno.md`**. Conclusión: *no vamos por detrás en tecnología, sino en producto* — el motor es mejor de lo que la interfaz deja ver.

**Prioridad 1 (alto valor, bajo esfuerzo — no requieren arquitectura nueva):**
- [ ] **Corrección diagnóstica al fallar.** Hoy el alumno solo ve la respuesta correcta + una explicación. No sabe *por qué* se equivocó. Es el momento de máximo aprendizaje y lo estamos desperdiciando. (Una segunda llamada al modelo con artículo + pregunta + opción elegida + correcta: las 4 piezas ya están en BD.)
- [ ] **Mostrar el artículo del BOE junto a la respuesta** ("verificado contra el art. X de la Ley Y", con el texto desplegable). Convierte nuestra arquitectura en confianza visible. El texto ya está en `normas.articulos`.
- [ ] **Puerta anti-alucinación en el generador**: `_parse_and_validate()` no comprueba que el artículo citado en el enunciado sea el artículo fuente. Medido: hoy 78/78 aciertan, pero por buen comportamiento del modelo, no porque lo impidamos. ~20 líneas.
- [ ] **Dar el Q&A semántico al alumno.** Está construido y probado, pero solo lo usan los editores. **Ningún competidor lo tiene.**
- [ ] **Radar del Tribunal por tema**: frecuencia de cada tema en los exámenes oficiales. Es un `GROUP BY` sobre datos que ya existen (157 preguntas oficiales clasificadas; IV.11 salió 10 veces, V.6 siete).

**Prioridad 2:**
- [ ] **Informe para el preparador** (cómo van sus alumnos, dónde fallan). **Es lo que vende el B2B**: la academia no compra gamificación, compra evidencia de que sus alumnos mejoran.
- [ ] Rachas/constancia y dashboard (B2C). Hoy **no existe ningún concepto de racha**.
- [ ] Estimación "¿estoy listo para el examen?" a partir del % por tema y el peso oficial.

**Prioridad 3 / no copiar:** radar por artículo (exige re-procesar los exámenes: hoy `articulo='S/N'`), gamificación social (con pocos alumnos un ranking desmotiva), y **generar más preguntas sin revisar** — el cuello de botella no es generar, es revisar (78 esperando).

### 🔴 Pendiente — Cambiar producción al usuario de BD con permisos mínimos (12/07/2026)

**Lo tiene que hacer el usuario**: requiere tocar los secrets de Streamlit Cloud, y si algo falla la app deja de conectar. Guía paso a paso (con rollback) en **`docs/cambiar-usuario-bd-produccion.md`**.

**Estado:** el rol `app_asistente` **ya está creado y probado** en Supabase (migración 040). La app funciona entera con él y no puede borrar tablas ni datos (verificado: `DROP`/`DELETE`/`TRUNCATE`/`CREATE` fallan con `InsufficientPrivilege`). **Producción sigue conectando como `postgres`** hasta que se haga este cambio.

- [ ] Generar/recuperar la contraseña de `app_asistente` (no está en el repo, a propósito). Si no se tiene: `ALTER ROLE app_asistente PASSWORD '<aleatoria>';` desde el SQL Editor de Supabase.
- [ ] En Streamlit Cloud → Settings → Secrets, cambiar **solo** dos líneas: `DB_USER = "app_asistente"` y `DB_PASSWORD = "<la nueva>"`. **No tocar** `DB_HOST`/`DB_PORT`/`DB_NAME`.
- [ ] Comprobar en la app: carga de leyes, cola de "Revisar preguntas", aprobar una pregunta, listado de "Editores".
- **Por qué importa:** hoy la app conecta como `postgres`, que puede **borrar tablas** y se salta el RLS. La app no necesita ninguno de esos permisos.
- **Si falla con un error de permisos:** no hay que volver a `postgres`; basta añadir el `GRANT` concreto que falte.

### 🔴 Pendiente IMPORTANTE — Dos leyes con la referencia oficial contradictoria (12/07/2026)

Detectado al poblar `leyes.nombre_oficial` desde el BOE (migración 038). **No bloquea nada hoy, pero sí afecta a la calidad jurídica de las preguntas**: el generador cita ahora el `nombre_oficial`, así que si el título es el equivocado, las preguntas de esas dos leyes citarán una norma que no es. Requiere criterio jurídico (no lo puede decidir el código).

- [ ] **RRCP** (`ley_id` de "Reglamento del Registro Central de Personal"). Su `url_boe` apunta al **RD 2073/1999, "por el que se _modifica_ el Reglamento del Registro Central de Personal"** — es un decreto **modificador**, no el reglamento en sí. El reglamento original es otro (histórico del repo: hubo un vaivén previo entre RD 2073/1999 y RD 172/1988, ver `git log` de la migración 029). **Decidir qué norma se quiere citar y corregir `url_boe` + `nombre_oficial` + `numero_oficial` en consecuencia.**
- [ ] **BCPSA** (bases comunes de procesos selectivos AGE). El BOE devuelve **"Orden HFP/688/2017, de 20 de julio"**, pero la columna `numero_oficial` dice **"Real Decreto 364/2017, de 8 de abril"**. **Se contradicen: una de las dos está mal.** (El `url_boe` guardado apunta a la Orden.) Verificar cuál es la norma correcta y alinear los tres campos.

**Cómo comprobar el impacto:** `SELECT codigo, nombre, nombre_oficial, numero_oficial, url_boe FROM normas.leyes WHERE codigo IN ('RRCP','BCPSA');`

### ⏳ Pendiente — Pantalla de gestión de alumnos (12/07/2026)

Contrapartida de la pantalla de "Editores" (ya hecha, migración 037), pero **no es simétrica** — conviene tenerlo claro antes de planificarla:

- **Los editores viven en BD** (`normas.editores`) → alta/baja es un `INSERT`/`UPDATE` normal.
- **Los alumnos viven en Supabase Auth**, no en una tabla nuestra. La app solo tiene la clave `anon`, que **no permite listar ni borrar usuarios** (por eso los usuarios de prueba de sesiones anteriores quedaron pendientes de limpieza manual). Gestionarlos de verdad exigiría la clave `service_role`, que da acceso total saltándose las políticas de seguridad y habría que meterla en los secrets — decisión no trivial.
- **No hay vínculo alumno↔academia** todavía, que es justo lo que el modelo B2B necesita para que cada academia vea solo a sus alumnos.

Dos alcances posibles (decidir cuál):
- [ ] **A) Solo lectura, sin claves nuevas (recomendado para empezar):** listar alumnos y su progreso a partir de las tablas que ya tenemos (`progreso_usuario`, `plan_estudio`, `historial_simulacros`, todas con `user_id`). Cubre el "análisis de la academia sobre sus alumnos" que ya se menciona como valor B2B en la regla de producto del Paso 7, sin tocar Supabase Auth.
- [ ] **B) Gestión completa:** dar de baja, resetear contraseña, etc. Requiere `service_role` en secrets + tabla/vínculo de alumnos + decidir el modelo multi-academia.

### ⏳ Pendiente — Auditar la pantalla de consentimiento de OAuth (Google Cloud) (12/07/2026)

Requiere entrar a Google Cloud Console con la cuenta del proyecto (no accesible desde el entorno de desarrollo). Surge al implementar la lista blanca de editores (migración 036): el control de acceso ya no depende de esta pantalla, pero su configuración sigue afectando a quién puede loguearse y a si el login funciona en producción.

- [ ] **Modo de publicación**: ¿*Testing* o *In production*? Si sigue en *Testing*, dar de alta a un editor nuevo exige **dos pasos** (usuario de prueba en Google Cloud + fila en `normas.editores`) — fácil de olvidar y el error resultante es confuso. Además, en *Testing* las sesiones caducan cada 7 días.
- [ ] **Tipo de usuario**: *External* vs *Internal* (solo con Google Workspace).
- [ ] **URIs de redirección autorizados**: comprobar que incluyen la URL de producción (`https://<app>.streamlit.app/oauth2callback`), no solo la de local. Si falta, el login falla en producción aunque funcione en desarrollo.
- [ ] **Estado de verificación**: si la app pide scopes sensibles sin verificar, Google muestra el aviso de "app no verificada".

### Diseño aprobado — App de estudio del alumno (05/07/2026)

Arquitectura completa definida y aprobada. Implementación en 9 pasos.

#### Plan de implementación

| Paso | Tarea | Estado |
|------|-------|--------|
| 1 | Migración 030: campo `dificultad` (1-3) en `preguntas_test` + tabla `normas.epigrafes` | ✅ Completado |
| 2 | Migración 031: tabla `normas.plan_estudio` (ficticio con alumnos de prueba) | ✅ Completado |
| 3 | Migración 032: tabla `normas.simulacros_academia` | ✅ Completado |
| 4 | Supabase Auth: registro email+contraseña para alumnos | ✅ Completado |
| 5 | `retrieval.py`: `get_fase_alumno`, `get_stats_alumno`, `get_preguntas_adaptativo`, `get_preguntas_simulacro_personal`, `get_preguntas_simulacro_academia` | ✅ Completado |
| 6 | `streamlit_app.py`: reestructura jerarquía navegación + prueba de nivel | ✅ Completado |
| 7 | Visualización progreso: panel inicio + composición tanda + resultado tanda | ⏭️ Siguiente |
| 8 | Simulacro personal (50 preguntas, fórmula GACE, bloques ≥70% acierto) | Pendiente |
| 9 | Simulacro academia (mismas preguntas para todos, ventana temporal) | Pendiente |

- [⚠️ Pendiente seguridad] La contraseña de Postgres de Supabase quedó expuesta en un chat de Claude Code (09/07/2026, configuración de conexión SQLTools). Se generó una contraseña nueva desde el Dashboard (Reset database password), pero **decisión explícita del usuario: no actualizarla todavía** en `.streamlit/secrets.toml` (rompería la conexión activa ahora mismo). Actualizar antes de dar acceso a alumnos reales — recordar también el secreto de Streamlit Cloud (producción) si la app ya está desplegada.

#### Decisiones de diseño clave

| Elemento | Decisión |
|----------|----------|
| Autenticación alumno | Email + contraseña vía Supabase Auth |
| Autenticación editor/academia | Google OAuth (ya implementado) |
| Prueba de nivel | 40 preguntas · peso oficial por bloque · dificultad creciente individual · gratuita con registro · genera informe de partida + plan de estudio |
| Mix adaptativo | Opción C — 4 fases por preguntas vistas: Inicio (0/40/60) · Aprendizaje (15/20/65) · Consolidación (30/25/45) · Pre-examen (40/35/25) — porcentajes: débiles/oficial/nueva |
| Puntos débiles | Del tema seleccionado (o de todo el bloque si se elige esa opción) — actualizado 11/07/2026, ver CLAUDE.md |
| Bloque "estudiado" | Todos sus temas con preguntas vistas ≥70% (progreso trackeado por tema, no por bloque) — actualizado 11/07/2026, ver CLAUDE.md |
| Simulacro personal | 50 preguntas · solo bloques ≥70% · fórmula A−(E/3) · requiere prueba de nivel previa |
| Simulacro academia | Mismas preguntas para todos · sin personalización · ventana temporal fijada por academia |
| Dificultad preguntas | Campo `dificultad` (1-fácil / 2-media / 3-difícil) en `preguntas_test`; editor asigna en revisión |
| Visualización | 3 momentos: panel inicio (fase+%+barras) · composición tanda · resultado tanda |
| LSSF | Sin contenido en normas.leyes · excluir_test=TRUE en GACE · reservada para oposiciones Justicia |

### Completado — Paso 6: navegación alumno + prueba de nivel (07/07/2026)
- [✅ `retrieval.get_preguntas_prueba_nivel`] 40 preguntas repartidas proporcionalmente por peso oficial entre los 6 bloques de la oposición (a diferencia del simulacro personal, no exige bloques "estudiado"), orden por dificultad creciente. Nota: casi todas las preguntas tienen `dificultad=2` (default, pendiente de reclasificar), así que el orden creciente aún tiene efecto práctico limitado.
- [✅ `streamlit_app.py`] Alumno logueado (Supabase Auth) tiene flujo propio: Oposición → Modo (Prueba de nivel / Repaso) → Bloque → sesión, separado del flujo editor (Q&A/Generar test/Editor, Google OAuth, sin cambios). Onboarding de bienvenida si el alumno no tiene ningún bloque en `plan_estudio` todavía. Mensajes de error específicos en login/registro (email duplicado, credenciales incorrectas, contraseña corta) en vez del error crudo de Supabase.
- [✅ Verificación visual, Playwright headless] Instaladas dependencias de Chromium (`libnspr4`, `libnss3`, etc.) tras bloqueo inicial por falta de sudo. Flujo completo probado contra Supabase real: registro → prueba de nivel (40 preguntas) → comprobar respuestas → informe de partida (% y fase por bloque) → botón "Ir a Repaso" cambia de modo → cerrar sesión y volver a entrar detecta que ya no es alumno nuevo y preselecciona Repaso con el bloque recomendado → tanda adaptativa cargada. 0 errores de consola. Datos de prueba borrados de `plan_estudio`/`progreso_usuario` al terminar.
- [✅ Limpieza manual completada (09/07/2026)] Los 3 usuarios de prueba (`alumno.prueba.claude.paso6*@example.com`, `...paso6b...`, `...paso6c...`) eliminados desde el dashboard de Supabase (Authentication → Users). Verificado por SQL que no quedaron filas huérfanas en `progreso_usuario`/`plan_estudio`/`historial_simulacros`.
- [✅ Bug encontrado y corregido] `.streamlit/secrets.toml`: `SUPABASE_URL`/`SUPABASE_ANON_KEY` estaban físicamente después de `[auth.google]`, por lo que TOML las anidaba dentro de esa tabla en vez de dejarlas a nivel superior — el registro de alumno fallaba con "SUPABASE_URL / SUPABASE_ANON_KEY no configurados". Reordenadas antes de `[auth]`. **Pendiente de revisar el mismo problema en los Secrets de Streamlit Cloud** (producción) antes de dar acceso a los alumnos reales — mismo fix, mover esas dos líneas por encima de `[auth]` en el editor de Secrets.
- [✅ Mejora en Q&A, no prevista en el plan de 9 pasos] El modo Q&A no distinguía capítulo dentro de un título (solo título completo o agregados estructurales), así que "lista los artículos del Título I Capítulo II" respondía que no tenía ese desglose. Añadidas `get_capitulos_db`/`get_articulos_por_capitulo` en `retrieval.py` y `_extraer_capitulo_id` en `qa_pipeline.py`; `_responder_resumen` ahora acota al capítulo cuando la pregunta lo menciona (si no, sigue trayendo el título entero como antes). Verificado en vivo: devuelve los 25 artículos correctos (14-38) del Título I Capítulo II de la CE.

### Completado — Paso 5: retrieval.py, mix adaptativo (06/07/2026)
- [✅ `get_fase_alumno`] Calcula fase por cobertura de épigrafes + % acierto agregado; UPSERT en `plan_estudio`. Probado en vivo.
- [✅ `get_stats_alumno`] Progreso por bloque (desde `plan_estudio`) + "próxima acción" por regla simple + actividad reciente. Probado (incluye caso alumno nuevo → sugiere prueba de nivel).
- [✅ `get_preguntas_adaptativo`] Mix débiles/oficial/nueva por fase, con relleno automático cuando un tramo no tiene suficientes preguntas (hoy no hay preguntas `fuente='ia'` en ningún bloque — el relleno lo compensa; se resolverá al generar banco IA a escala). Probado: débiles se seleccionan correctamente, sin duplicados.
- [✅ `get_preguntas_simulacro_personal`] Reparto proporcional por peso oficial (`oposicion_leyes.preguntas_simulacro`) solo entre bloques "estudiado"; bloquea si falta prueba de nivel o si no hay bloques estudiados. Probado los 3 escenarios.
- [✅ `get_preguntas_simulacro_academia`] Lee la lista congelada de `simulacro_academia_preguntas`; bloquea si no existe o no está `autorizado`. Probado los 3 escenarios.
- [ℹ️ Nota] La fórmula de corrección A-(E/3) se aplica al calificar respuestas, no en la selección de preguntas — queda para el Paso 8 (implementación real del simulacro).
- [✅ Decisión] Umbral de fase = % de cobertura del bloque (temas distintos con ≥1 pregunta vista / total de épigrafes del bloque), no por preguntas_simulacro (evita inflar la fase artificialmente).
- [✅ Decisión] `débiles/oficial/nueva`: débiles = falladas (cualquier fuente, prioridad primero); oficial = `fuente LIKE 'oficial_%'`; nueva = `fuente='ia'`. Se completa débiles primero, y el resto se reparte oficial/nueva excluyendo ya elegidas.
- [✅ `app/retrieval.py`] `get_bloque_y_epigrafes(ley_id, oposicion_codigo="GACE")` — resuelve bloque+épigrafes sin hardcodear la oposición (reutilizable para futuras oposiciones).
- [✅ `scripts/asignar_epigrafes.py`] Backfill de clasificación de preguntas contra el temario oficial vía Claude. Reutilizable como herramienta de resincronización si el temario cambia de estructura en el futuro.
- [✅ `scripts/build_test_bank.py`] Ahora asigna `epigrafe_id` en la misma llamada de generación (sin coste extra de API); añade contexto del Título de la ley al prompt (corrige ambigüedades de clasificación, ver bug abajo).
- [✅ Backfill ejecutado] 89/89 preguntas con `ley_id` ya asignado, clasificadas correctamente contra `normas.epigrafes`.
- [✅ Gap preexistente resuelto] `scripts/asignar_leyes.py` (nuevo, mismo patrón): resuelve `ley_id` de preguntas oficiales sin mapear comparando el nombre de norma citado en el enunciado contra el catálogo de 60 leyes cargadas (o "NINGUNA" si no corresponde a ninguna cargada). De las 130 preguntas con `ley_id=NULL`: **78 resueltas** (LO4000, LODP, LOTC, TUE/TFUE, LOCE, LOPJ, TREBEP, CC, LGOB, LGP, LJCA, LEF, LGT, LOTCU, RIRS, MUFACE, LMRFP, RDSA, BCPSA, RRCP, LSSF, LOEPSF, LGUM, LGS, LPAP, CE...), **52 sin coincidencia** (actualidad/órdenes/normas no cargadas — correcto dejarlas en NULL). Encadenado con `asignar_epigrafes.py` sobre las 78 recién resueltas: **78/78 clasificadas**.
- [✅ Estado final banco] 167/219 preguntas (76%) con `ley_id` + `epigrafe_id` completos. Las 52 restantes son de actualidad/normas no cargadas — no es un error, no deberían tener epígrafe.
- [ℹ️ Bug corregido] `asignar_epigrafes.py` no encontraba el Título de la ley para artículos con sub-apartado (p. ej. "11.3") porque el JOIN comparaba contra `normas.articulos.numero` exacto; corregido con `split_part(articulo, '.', 1)`.
- [ℹ️ Pendiente] Punto 4 de Paso 5 (campos exactos de `get_stats_alumno`) — aplazado hasta resolver 1 y 2, ya resueltos; retomar antes de escribir `get_fase_alumno`/`get_stats_alumno`.

### Completado — Paso 4: Supabase Auth alumno (06/07/2026)
- [✅ `app/auth_alumno.py`] Cliente Supabase + `registrar_alumno()` / `login_alumno()` (sign_up / sign_in_with_password).
- [✅ `app/config.py`] `SUPABASE_URL` / `SUPABASE_ANON_KEY`.
- [✅ `streamlit_app.py`] Sección "Acceso Alumno" en el sidebar (registro/login independiente del login Google del editor), sesión en `st.session_state.alumno`.
- [✅ Dependencia] `supabase>=2.9.0` en `requirements.txt`, instalada.
- [✅ Verificado en vivo] Servidor arranca sin errores; registro+login real contra Supabase Auth probado end-to-end (confirmación de email desactivada, como se decidió). Sin captura visual del formulario (entorno sin Chromium headless funcional) — verificación por llamada directa a las funciones que usa el sidebar, suficiente dado que usan componentes estándar de Streamlit ya usados en el mismo archivo.
- [ℹ️ Pendiente] Conectar esta sesión de alumno al repaso adaptativo SM-2 (hoy sigue gateado por el login Google del editor) — se hace en el Paso 6 al reestructurar la navegación.
- [✅ Limpieza manual completada (09/07/2026)] El usuario de prueba (`alumno.prueba.claude+...@example.com`) eliminado desde el dashboard de Supabase.

### Completado — Migración 032 (06/07/2026)
- [✅ `normas.simulacros_academia`] Simulacro con preguntas fijas para todos los alumnos de una academia, ventana temporal (`fecha_inicio`/`fecha_fin`), flujo `estado` generado→autorizado. Campo `academia` (TEXT, nullable) preparado para futuro multi-tenant.
- [✅ `normas.simulacro_academia_preguntas`] Lista fija y ordenada de preguntas por simulacro.
- [ℹ️ Regla de negocio] La academia nunca genera preguntas (modelo: venta de lotes); solo lee y autoriza el simulacro generado automáticamente.
- [ℹ️ Diferido] Tabla de resoluciones/respuestas de alumnos → Paso 9. Propuestas de corrección de la academia → sin diseñar, ver memoria del proyecto.

### Completado — Migración 031 (06/07/2026)
- [✅ `normas.plan_estudio`] Estado vivo del alumno por bloque (6 filas/alumno): `fase`, `preguntas_vistas`, `preguntas_correctas`, `porcentaje_acierto`, `estudiado`. UNIQUE(user_id, oposicion_id, bloque).
- [ℹ️ Decisión diferida] Umbral de transición de fase (Inicio→Aprendizaje→Consolidación→Pre-examen) por preguntas vistas: **aún sin definir**. `fase` queda en default `'inicio'` hasta implementar la lógica en el Paso 5 (`retrieval.py`).
- [ℹ️ Decisión] Actualización del estado vivo se hace desde una función Python en `retrieval.py` (no trigger de BD), en línea con el patrón ya usado para SM-2.
- [ℹ️ Pendiente] Alumnos de prueba (3, con criterios a definir) — ver memoria del proyecto; se crearán al llegar a la fase de testing (Paso 5+).

### Completado — Migración 030 (06/07/2026)
- [✅ `normas.epigrafes`] 58 temas oficiales del programa GACE (Anexo VII), verificados carácter a carácter contra el PDF: I=11, II=6, III=10, IV=13, V=10, VI=8.
- [✅ `preguntas_test.dificultad`] SMALLINT (1-3), default 2; 219 preguntas existentes clasificadas como "media" pendiente de reclasificar.
- [✅ `preguntas_test.epigrafe_id`] FK nullable a `normas.epigrafes`, aún sin mapear preguntas existentes.
- [✅ Correcciones detectadas] Tema I.1 faltante (parser lo había omitido); artefacto OCR "DE FUNCION PÚBLICA" en I.11/IV.1/V.9; texto incompleto en I.8 ("servicios comunes de los ministerios. Órganos territoriales"); nombres de Bloque IV ("Derecho administrativo general") y Bloque V ("Administración de recursos humanos") mal etiquetados en `scripts/load_convocatoria.py` — corregidos en el script.
- [ℹ️ Pendiente] `normas.articulos` de `GACE_NORM` sigue con los artefactos/errores originales (no se tocó, fuera de alcance de esta migración); reclasificación de `dificultad` real y mapeo `epigrafe_id` en preguntas existentes quedan para más adelante.

---

### Arquitectura de producto (decisión 30/06/2026)
- **B2B primero (3-6 meses):** Streamlit como herramienta interna para academias. Genera preguntas con IA → revisa → exporta a Moodle XML/CSV para que la academia use en su LMS.
- **B2C después (6-12 meses):** plataforma propia con FastAPI + frontend dedicado sobre el mismo backend IA.
- El valor diferencial es la capa IA (generación desde BOE + Q&A semántico); la gestión de alumnos la hace el LMS de la academia en fase B2B.

### Completado en sesión 30/06/2026
- [✅ Arquitectura] Decisión B2B primero (academias, 3-6 meses) / B2C después (6-12 meses).
- [✅ Migración 024] `revisado_por VARCHAR(150)` + `revisado_en TIMESTAMP` en `normas.preguntas_test`.
- [✅ Google OAuth] Configurado en Streamlit Cloud: `authlib`, `[auth.google]`, `server_metadata_url`. Login funcional con cuenta Google.
- [✅ Tab Editor] Implementado en `app/streamlit_app.py`: tabs Generar + Revisar, auditoría completa.
- [✅ max_por_articulo] Múltiples preguntas IA por artículo: slider 1-5 en UI, flag `--max-por-articulo` en CLI.
- [✅ Validación banco IA] 10 preguntas de LPAC generadas y guardadas correctamente en BD.

### En curso — Refinamiento UX Streamlit
- [⏭️ Siguiente] Mejorar selector de leyes (60 leyes en lista plana, difícil de navegar).
- Otros ajustes de usabilidad a identificar durante el uso real.
- Una vez consolidada la UX → generar banco IA completo (`--supabase --n 50`, ~300 preguntas, ~3-4€).
- [Paso 5 — MVP] Exportación Moodle XML / CSV: integración con LMS de la academia cliente.

### Completado en sesión 29/06/2026 (FASE 5B)
- [✅ FASE 5B completa] LGPD (128) + LAEPD (17) + LSSF (54) + LDEP (61) + LOE (250) + LO4000 (117) + LASIL (64) + LTRANS (108) + LGUM (47) + LGT22 (158) + LEPP (42) — 1.046 artículos con embeddings (ley_ids 68–79)
- [ℹ️ Incidencia] LGUM: capítulo VIII numerado "IV" en el BOE — corregido en el JSON antes de cargar
- [ℹ️ Corrección] LGT22: el TODO indicaba Ley 9/2022; el BOE-A-2022-10757 es Ley 11/2022 (actualizado)

### Completado en sesión 29/06/2026 (FASE 5A)
- [✅ FASE 5A completa] RLEF (140) + RLGS (122) + BCPSA (22) + RRCP (27) + IGAE (58) + ACF (17) + PLJ (16) + ROCE (146) — 548 artículos con embeddings (ley_ids 60–67)

### Completado en sesión 29/06/2026 (continuación)
- [✅ FASE 4 — MEDIA 6/8] LOIT (71) + LASEE (87) + ENI (41) + CC (1941) + LPNAT (113) + LE (103) — 2.356 artículos con embeddings
- [✅ Bugs corregidos load_ley.py] Secciones huérfanas sin título/capítulo; capítulos numero vacío duplicados; artículos numero duplicado
- [⚠️ LCCU + PGCP] Pendientes parser específico (anotados en tabla con prioridad MEDIA)

### Completado en sesión 29/06/2026
- [✅ FASE 4 — ALTA completa] LPAP (240) + RIRS (54) + MUFACE (182) + LMRFP (79) + RDSA (35) + RDRD (59) + REGI (99) + LOTCU (59) + ET (142) — 949 artículos con embeddings
- [✅ Bugs corregidos] load_ley.py: leyes sin títulos con título sintético _ROOT; generate_embeddings.py: flag --supabase, MAX_CHARS 24K, fallback por artículo

### Completado en sesión 28/06/2026
- [✅ FASE 1] 8 leyes ALTA: LODP, LOTC, LGOB, LOCE, LBRL, LTBG, LOPD, LOEPSF (673 arts.)
- [✅ FASE 2] 4 leyes: LOPJ, LGSS, LTPP, LGT (1.603 arts.)
- [✅ Validación] 79 preguntas oficiales cruzadas con BD → 0 artículos ausentes
- [✅ Generador] `build_test_bank.py` mejorado: few-shot oficial, sub-artículos, estilo mixto, prioridad examinables
- [✅ Producto] Objetivo redefinido: plataforma multi-oposición, multi-formato, configurable sin código
- [✅ FASE 3] TUE (ley_id=33, 55 arts.) + TFUE (ley_id=34, 358 arts.) desde EUR-Lex con embeddings
- [✅ FASE 4 — bloque 1] LOIEMH (130) + LOIVG (107) + LJCA (175) + LGS (105) + LEF (134) — 651 arts. con embeddings

### Hitos pendientes — Normativa (GACE)
- [FASE 4 pendiente] LCCU y PGCP con parser específico (baja urgencia)
- Generar banco IA: `build_test_bank.py --supabase --n 50` (~300 preguntas, ~3-4€)

### Hitos pendientes — UX y funcionalidad Streamlit
- [⏭️ UX] Mejorar selector de leyes: 60 en lista plana, difícil de navegar (agrupar por categoría, buscar, mostrar stats)
- [UX] Otros ajustes de usabilidad identificados durante uso real
- [MVP] Exportar banco aprobado a **Moodle XML** y **CSV** por convocatoria/ley
- Generar banco IA completo: `build_test_bank.py --supabase --n 50` (~300 preguntas, ~3-4€)
- Simulacro: 100 preguntas, temporizador, puntuación A-(E/3), escala 0-50 pts (fase B2C)
- Historial de conversación en Q&A (multi-turno con `st.session_state`)

### Hitos pendientes — Supuesto práctico (nuevo módulo)
- Modelo de datos: tabla `casos_practicos` (expedientes, cuestiones, normativa aplicable)
- Generador de supuestos con Claude (estilo GACE: expedientes INAP/FEGA con plazos, órganos, fórmulas)
- Módulo de práctica en Streamlit: presentar caso, respuesta libre, evaluación IA con retroalimentación
- Banco de supuestos reales 2024-2025 como referencia few-shot

### Hitos pendientes — Plataforma y configurabilidad
- Panel de administración de convocatoria: gestionar leyes, fórmula y tipos de ejercicio sin código
- Soporte multi-oposición: segunda oposición integrada (a definir) con la misma arquitectura GACE
- Sincronización automática BOE mediante GitHub Actions
