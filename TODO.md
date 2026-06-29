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
| 13 | GACE_NORM | Normativa Oposición GACE (criterios + programa) | ✅ cargada |
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

## Pendientes de carga – inventario BOE-443

Estrategia por ley: `parse_boe.py <ELI> --output data/leyes/XX.json` → `load_ley.py XX.json --supabase --embeddings`

> Las fichas BOE con el Permalink ELI de cada norma se localizan en `https://www.boe.es/buscar/act.php?id=<BOE-ID>`.

### FASE 4 – ALTA prioridad (directamente examinables en GACE)

| Código | Ley | BOE-ID |
|--------|-----|--------|
| LPAP | Ley 33/2003 Patrimonio de las Administraciones Públicas | BOE-A-2003-20254 |
| RIRS | RD 462/2002 Indemnizaciones por Razón del Servicio | BOE-A-2002-10337 |
| MUFACE | RD 375/2003 Reglamento General Mutualismo Administrativo | BOE-A-2003-7527 |
| LMRFP | Ley 30/1984 Medidas Reforma Función Pública | BOE-A-1984-17387 |
| RDSA | RD 365/1995 Situaciones Administrativas Funcionarios AGE | BOE-A-1995-8730 |
| RDRD | RD 33/1986 Régimen Disciplinario Funcionarios AGE | BOE-A-1986-1216 |
| REGI | RD 364/1995 Reglamento General de Ingreso AGE | BOE-A-1995-8729 |
| LOTCU | LO 2/1982 Tribunal de Cuentas | BOE-A-1982-11584 |
| ET | TR Ley del Estatuto de los Trabajadores | BOE-A-2015-11430 |

### FASE 4 – MEDIA prioridad

| Código | Ley | BOE-ID |
|--------|-----|--------|
| LOIT | Ley 15/2022 Igualdad de Trato y No Discriminación | BOE-A-2022-11589 |
| LCCU | IV Convenio Colectivo Único Personal Laboral AGE | BOE-A-2019-7414 |
| LASEE | Ley 2/2014 Acción y Servicio Exterior del Estado | BOE-A-2014-3248 |
| PGCP | Plan General de Contabilidad Pública 2010 | BOE-A-2010-6710 |
| ENI | Esquema Nacional de Interoperabilidad | BOE-A-2010-1331 |
| CC | Código Civil (1889) | BOE-A-1889-4763 |
| LPNAT | Ley 42/2007 Patrimonio Natural y Biodiversidad | BOE-A-2007-21490 |
| LE | Ley 3/2023 de Empleo | BOE-A-2023-5365 |

### Reglamentos / normas técnicas complementarias (baja prioridad GACE)

| Nombre | BOE-ID |
|--------|--------|
| Reglamento Ley Expropiación Forzosa | BOE-A-1957-7998 |
| Reglamento Ley General de Subvenciones | BOE-A-2006-13371 |
| Bases comunes procesos selectivos AGE | BOE-A-2017-8652 |
| Acceso empleo personas con discapacidad | BOE-A-2004-21221 |
| TR Ley General derechos personas con discapacidad | BOE-A-2013-12632 |
| Reglamento Registro Central de Personal | BOE-A-2000-1007 |
| Reglamento Orgánico del Consejo de Estado | BOE-A-1980-18703 |
| Control interno IGAE (RD 2188/1995) | BOE-A-1996-1578 |
| Anticipos de Caja Fija (RD 725/1989) | BOE-A-1989-14441 |
| Pagos librados a justificar (RD 640/1987) | BOE-A-1987-12158 |
| Ley 39/2006 Movilidad / Dependencia (TR Empleo) | BOE-A-2015-11431 |
| TR Ley SS Funcionarios Civiles del Estado | BOE-A-2000-12140 |
| LO 4/2000 Extranjeros en España | BOE-A-2000-544 |
| Ley 12/2009 Derecho de Asilo | BOE-A-2009-17242 |
| Ley 4/2023 Trans e igualdad LGTBI | BOE-A-2023-5366 |
| LO 2/2006 Educación | BOE-A-2006-7899 |
| Ley 2/2013 Garantía Unidad de Mercado | BOE-A-2013-12888 |
| Ley 9/2022 General de Telecomunicaciones | BOE-A-2022-10757 |
| Ley 22/2022 Evaluación Políticas Públicas AGE | BOE-A-2022-21677 |

## Próximos pasos

### En curso
- [FASE 4] 5/14 leyes ALTA cargadas — pendientes: LPAP, RIRS, MUFACE, LMRFP, RDSA, RDRD, REGI, LOTCU, ET.

### Completado en sesión 28/06/2026
- [✅ FASE 1] 8 leyes ALTA: LODP, LOTC, LGOB, LOCE, LBRL, LTBG, LOPD, LOEPSF (673 arts.)
- [✅ FASE 2] 4 leyes: LOPJ, LGSS, LTPP, LGT (1.603 arts.)
- [✅ Validación] 79 preguntas oficiales cruzadas con BD → 0 artículos ausentes
- [✅ Generador] `build_test_bank.py` mejorado: few-shot oficial, sub-artículos, estilo mixto, prioridad examinables
- [✅ Producto] Objetivo redefinido: plataforma multi-oposición, multi-formato, configurable sin código
- [✅ FASE 3] TUE (ley_id=33, 55 arts.) + TFUE (ley_id=34, 358 arts.) desde EUR-Lex con embeddings
- [✅ FASE 4 — bloque 1] LOIEMH (130) + LOIVG (107) + LJCA (175) + LGS (105) + LEF (134) — 651 arts. con embeddings

### Hitos pendientes — Normativa (GACE)
- [FASE 4 — ALTA] LPAP, RIRS, MUFACE, LMRFP, RDSA, RDRD, REGI, LOTCU, ET (9 leyes)
- [FASE 4 — MEDIA] LOIT, LCCU, LASEE, PGCP, ENI, CC, LPNAT, LE (8 leyes)
- Generar banco IA: `build_test_bank.py --supabase --n 50` (~300 preguntas, ~3-4€)

### Hitos pendientes — Ejercicio tipo test
- Simulacro: 100 preguntas, temporizador, puntuación A-(E/3), escala 0-50 pts
- Interfaz de revisión: tab "Revisión" para aprobar/rechazar preguntas IA
- Exportar banco a CSV / Moodle XML
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
