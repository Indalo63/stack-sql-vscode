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
