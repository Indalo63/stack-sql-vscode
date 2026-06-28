# CLAUDE.md – Plataforma IA de Preparación de Oposiciones

## Quién soy
Soy Indalecio Plaza, licenciado en Derecho, Consultor y Técnico en bases de datos relacionales (PostgreSQL), desarrollo web y automatización con IA.

## Objetivo de este proyecto
Construir una plataforma modular de preparación de oposiciones basada en IA, capaz de adaptarse a cualquier formato de examen y convocatoria, que combina:

- Windows + WSL2 (Ubuntu) + VS Code + Git
- PostgreSQL 16 + pgvector en Supabase (cloud)
- Python (pipelines de carga normativa, Q&A jurídico, generación de ejercicios)
- Claude (Anthropic API) como motor de generación y evaluación
- OpenAI API para embeddings semánticos
- Streamlit como interfaz web desplegada en cloud
- Claude Code como copiloto técnico y documental

La plataforma permite a cualquier opositor consultar la normativa de su convocatoria en lenguaje natural, practicar con ejercicios generados por IA calibrados al estilo del examen real, y realizar simulacros con la fórmula de corrección oficial.

Está diseñada para ser **configurable sin necesidad de modificar código**: los parámetros de cada convocatoria (normativa, formato, fórmula de corrección, tipos de ejercicio) se gestionan desde la base de datos o desde ficheros de configuración. La sincronización automática de textos legales desde el BOE y EUR-Lex es el objetivo a largo plazo para mantener la normativa actualizada.

El desarrollo inicial toma como referencia la oposición **GACE** (Cuerpo General Administrativo del Estado), cuyo programa, banco de preguntas oficiales y supuestos prácticos constituyen la base del sistema. La arquitectura está diseñada para integrar cualquier oposición futura con mínimo esfuerzo.

La plataforma está orientada a preparadores de oposiciones y academias de cualquier cuerpo o escala.

## Producto y audiencia

### Usuario final
Cualquier opositor que necesite:
- Consultar la normativa de su convocatoria en lenguaje natural (Q&A semántico)
- Practicar con preguntas tipo test al nivel de dificultad del examen real
- Entrenar supuestos prácticos con casos generados por IA (resolución de expedientes, aplicación de plazos, órganos competentes, etc.)
- Realizar simulacros cronometrados con la fórmula de corrección oficial de su convocatoria

### Cliente / integrador
Preparadores de oposiciones y academias que quieran ofrecer a sus alumnos:
- Un asistente jurídico sobre el temario de su convocatoria específica
- Un banco de ejercicios generados por IA calibrado al estilo del examen real (test + supuestos prácticos)
- Una herramienta de simulacro con la fórmula de corrección oficial configurable

### Oposición de referencia
**GACE** (Cuerpo General Administrativo del Estado): primera oposición integrada en la plataforma, que sirve de modelo para el resto. Todo el desarrollo inicial —normativa, banco de preguntas, supuestos prácticos, criterios de corrección— se basa en GACE.

## Forma de trabajo deseada con la IA
- Avanzar siempre en pasos numerados (Paso 1, Paso 2, etc.).
- No pasar al siguiente paso hasta que el anterior esté completado y confirmado.
- Explicaciones en español, con lenguaje técnico pero tono docente.
- Preferir explicaciones breves y accionables, con comandos concretos que pueda pegar en WSL2.
- Cuando propongas cambios en archivos, describe:
  - Ruta del archivo
  - Bloque a modificar o crear
  - Contenido completo del bloque

## Entorno asumido
- Sistema: Windows con WSL2 (Ubuntu 24.04 LTS).
- Directorio de proyecto en WSL2: ~/dev/stack-sql-vscode
- Git instalado y configurado en WSL2.
- Base de datos principal: Supabase cloud (PostgreSQL 16 + pgvector). Docker Desktop disponible para desarrollo local opcional.
- Python 3 disponible en WSL2.
- Variables de entorno `OPENAI_API_KEY` y `ANTHROPIC_API_KEY` configuradas en `.env`.
- Interfaz web: Streamlit desplegado en Streamlit Cloud (producción).

## Convenciones iniciales
- La documentación técnica del stack vive en `docs/` y está dirigida a perfiles técnicos (despliegue, configuración, arquitectura).
- El archivo principal de guía técnica es `docs/stack-sql-vscode.md`.
- Usar Markdown para cualquier guía o checklist.
- Cuando se propongan nuevos archivos, ubicarlos dentro de este repo respetando la estructura existente.
- Los parámetros de convocatoria (leyes, fórmula, tipos de ejercicio, plazos) deben residir en la base de datos o en ficheros de configuración, nunca hardcodeados en el código.

## Normas obligatorias para la generación de preguntas tipo test

Estas reglas se aplican SIEMPRE en `app/test_pipeline.py` y en cualquier futuro generador de preguntas. Son innegociables y derivan del análisis del examen oficial GACE 2025.

1. **Sin símbolos matemáticos**: Las preguntas, opciones y explicaciones nunca deben contener símbolos matemáticos (=, >, <, %, +, ×, ÷, →, fracciones, etc.). Escribir siempre en texto: "igual a", "mayor que", "porcentaje", etc.

2. **El enunciado cita la norma completa**: El enunciado debe comenzar siempre con "Según el artículo [N] de [nombre completo de la ley]," o "De acuerdo con el artículo [N] de [nombre completo de la ley],". Nunca omitir el nombre completo de la norma.

3. **Opciones en minúsculas a/b/c/d**: Las cuatro opciones se etiquetan siempre como a), b), c), d) — nunca en mayúsculas.

4. **Distractores de alta precisión**: Las opciones incorrectas deben diferir de la correcta únicamente en datos exactos: un plazo distinto, un porcentaje diferente, un órgano incorrecto, una palabra clave cambiada. Prohibido usar distractores conceptualmente muy distintos; el error debe ser sutil y técnico (estilo examen oficial GACE).

5. **Nivel de dificultad alto**: Preguntar por datos exactos del artículo (plazos, porcentajes, órganos competentes, requisitos concretos), no por conceptos generales.

## Estado actual del proyecto

### Schema Supabase `normas.*` — leyes cargadas con embeddings
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
| 33 | TUE | Tratado de la Unión Europea (versión consolidada 2016) | ✅ cargada |
| 34 | TFUE | Tratado de Funcionamiento de la Unión Europea (versión consolidada 2016) | ✅ cargada |
| 35 | LOIEMH | LO 3/2007 Igualdad Efectiva de Mujeres y Hombres | ✅ cargada |
| 36 | LOIVG | LO 1/2004 Protección Integral contra la Violencia de Género | ✅ cargada |
| 37 | LJCA | Ley 29/1998 Jurisdicción Contencioso-Administrativa | ✅ cargada |
| 38 | LGS | Ley 38/2003 General de Subvenciones | ✅ cargada |
| 39 | LEF | Ley de Expropiación Forzosa (1954) | ✅ cargada |

**Pendientes de carga — inventario BOE-443** (cada nombre es enlace a la ficha BOE donde aparece el Permalink ELI)

Estrategia: `parse_boe.py <ELI> --output data/leyes/XX.json` → `load_ley.py XX.json --supabase --embeddings`

#### FASE 4 — ALTA prioridad (directamente examinables en GACE)

| Código | Ley | BOE-ID |
|--------|-----|--------|
| LPAP | [Ley 33/2003 Patrimonio de las Administraciones Públicas](https://www.boe.es/buscar/act.php?id=BOE-A-2003-20254) | BOE-A-2003-20254 |
| RIRS | [RD 462/2002 Indemnizaciones por Razón del Servicio](https://www.boe.es/buscar/act.php?id=BOE-A-2002-10337) | BOE-A-2002-10337 |
| MUFACE | [RD 375/2003 Reglamento General Mutualismo Administrativo](https://www.boe.es/buscar/act.php?id=BOE-A-2003-7527) | BOE-A-2003-7527 |
| LMRFP | [Ley 30/1984 Medidas Reforma Función Pública](https://www.boe.es/buscar/act.php?id=BOE-A-1984-17387) | BOE-A-1984-17387 |
| RDSA | [RD 365/1995 Situaciones Administrativas Funcionarios AGE](https://www.boe.es/buscar/act.php?id=BOE-A-1995-8730) | BOE-A-1995-8730 |
| RDRD | [RD 33/1986 Régimen Disciplinario Funcionarios AGE](https://www.boe.es/buscar/act.php?id=BOE-A-1986-1216) | BOE-A-1986-1216 |
| REGI | [RD 364/1995 Reglamento General de Ingreso AGE](https://www.boe.es/buscar/act.php?id=BOE-A-1995-8729) | BOE-A-1995-8729 |
| LOTCU | [LO 2/1982 Tribunal de Cuentas](https://www.boe.es/buscar/act.php?id=BOE-A-1982-11584) | BOE-A-1982-11584 |
| ET | [TR Ley del Estatuto de los Trabajadores](https://www.boe.es/buscar/act.php?id=BOE-A-2015-11430) | BOE-A-2015-11430 |

#### FASE 4 — MEDIA prioridad

| Código | Ley | BOE-ID |
|--------|-----|--------|
| LOIT | [Ley 15/2022 Igualdad de Trato y No Discriminación](https://www.boe.es/buscar/act.php?id=BOE-A-2022-11589) | BOE-A-2022-11589 |
| LCCU | [IV Convenio Colectivo Único Personal Laboral AGE](https://www.boe.es/buscar/act.php?id=BOE-A-2019-7414) | BOE-A-2019-7414 |
| LASEE | [Ley 2/2014 Acción y Servicio Exterior del Estado](https://www.boe.es/buscar/act.php?id=BOE-A-2014-3248) | BOE-A-2014-3248 |
| PGCP | [Plan General de Contabilidad Pública 2010](https://www.boe.es/buscar/act.php?id=BOE-A-2010-6710) | BOE-A-2010-6710 |
| ENI | [Esquema Nacional de Interoperabilidad](https://www.boe.es/buscar/act.php?id=BOE-A-2010-1331) | BOE-A-2010-1331 |
| CC | [Código Civil (1889)](https://www.boe.es/buscar/act.php?id=BOE-A-1889-4763) | BOE-A-1889-4763 |
| LPNAT | [Ley 42/2007 Patrimonio Natural y Biodiversidad](https://www.boe.es/buscar/act.php?id=BOE-A-2007-21490) | BOE-A-2007-21490 |
| LE | [Ley 3/2023 de Empleo](https://www.boe.es/buscar/act.php?id=BOE-A-2023-5365) | BOE-A-2023-5365 |

#### Reglamentos / normas técnicas complementarias (baja prioridad GACE)

| Nombre | BOE-ID |
|--------|--------|
| [Reglamento Ley Expropiación Forzosa](https://www.boe.es/buscar/act.php?id=BOE-A-1957-7998) | BOE-A-1957-7998 |
| [Reglamento Ley General de Subvenciones](https://www.boe.es/buscar/act.php?id=BOE-A-2006-13371) | BOE-A-2006-13371 |
| [Bases comunes procesos selectivos AGE](https://www.boe.es/buscar/act.php?id=BOE-A-2017-8652) | BOE-A-2017-8652 |
| [Acceso empleo personas con discapacidad](https://www.boe.es/buscar/act.php?id=BOE-A-2004-21221) | BOE-A-2004-21221 |
| [TR Ley General derechos personas con discapacidad](https://www.boe.es/buscar/act.php?id=BOE-A-2013-12632) | BOE-A-2013-12632 |
| [Reglamento Registro Central de Personal](https://www.boe.es/buscar/act.php?id=BOE-A-2000-1007) | BOE-A-2000-1007 |
| [Reglamento Orgánico del Consejo de Estado](https://www.boe.es/buscar/act.php?id=BOE-A-1980-18703) | BOE-A-1980-18703 |
| [Control interno IGAE (RD 2188/1995)](https://www.boe.es/buscar/act.php?id=BOE-A-1996-1578) | BOE-A-1996-1578 |
| [Anticipos de Caja Fija (RD 725/1989)](https://www.boe.es/buscar/act.php?id=BOE-A-1989-14441) | BOE-A-1989-14441 |
| [Pagos librados a justificar (RD 640/1987)](https://www.boe.es/buscar/act.php?id=BOE-A-1987-12158) | BOE-A-1987-12158 |
| [Ley 39/2006 Movilidad / Dependencia (TR Empleo)](https://www.boe.es/buscar/act.php?id=BOE-A-2015-11431) | BOE-A-2015-11431 |
| [TR Ley SS Funcionarios Civiles del Estado](https://www.boe.es/buscar/act.php?id=BOE-A-2000-12140) | BOE-A-2000-12140 |
| [LO 4/2000 Extranjeros en España](https://www.boe.es/buscar/act.php?id=BOE-A-2000-544) | BOE-A-2000-544 |
| [Ley 12/2009 Derecho de Asilo](https://www.boe.es/buscar/act.php?id=BOE-A-2009-17242) | BOE-A-2009-17242 |
| [Ley 4/2023 Trans e igualdad LGTBI](https://www.boe.es/buscar/act.php?id=BOE-A-2023-5366) | BOE-A-2023-5366 |
| [LO 2/2006 Educación](https://www.boe.es/buscar/act.php?id=BOE-A-2006-7899) | BOE-A-2006-7899 |
| [Ley 2/2013 Garantía Unidad de Mercado](https://www.boe.es/buscar/act.php?id=BOE-A-2013-12888) | BOE-A-2013-12888 |
| [Ley 9/2022 General de Telecomunicaciones](https://www.boe.es/buscar/act.php?id=BOE-A-2022-10757) | BOE-A-2022-10757 |
| [Ley 22/2022 Evaluación Políticas Públicas AGE](https://www.boe.es/buscar/act.php?id=BOE-A-2022-21677) | BOE-A-2022-21677 |

### Banco de preguntas (`normas.preguntas_test`)
- **209 preguntas oficiales** cargadas: 104 de GACE 2024 + 105 de GACE 2025
  - `revisada=TRUE`, `fuente='oficial_2024'/'oficial_2025'`
  - 79 con `ley_id` identificada, 130 con `ley_id=NULL` (leyes aún no cargadas)
- Análisis de cobertura BOE-443: cubre el **76.6%** del examen real
  - TUE/TFUE: 9.6% fijo por convocatoria
  - Actualidad/conocimiento general: 5.7% (impredecible)
  - Leyes fuera del BOE-443: 6.7%

### Tablas adicionales en Supabase
- `normas.oposiciones` + `normas.oposicion_leyes`: distribución GACE (51/100 preguntas de nuestras 6 leyes)
- `normas.convocatorias`: metadatos estructurados 2024 y 2025
  - Fórmula: A-(E/3), 100 preguntas, 90 min, nota mínima 25/50 pts, escala 0-50
- Migraciones ejecutadas: `020`, `021`, `022`, `023`

### Scripts disponibles
| Script | Función |
|--------|---------|
| `load_ley.py` | Carga una ley desde BOE (HTML→articulos+embeddings) |
| `parse_boe.py` | Parsea HTML del BOE a JSON estructurado |
| `generate_embeddings.py` | Genera embeddings para artículos sin vector |
| `sync_boe.py` | Sincroniza actualizaciones del BOE |
| `build_test_bank.py` | Genera preguntas IA en lote y las guarda en BD |
| `parse_official_exams.py` | Parsea PDFs de exámenes oficiales GACE y los carga |
| `load_convocatoria.py` | Carga criterios+programa GACE como ley para Q&A |
| `parse_eurlex.py` | Parsea HTML de EUR-Lex (TUE/TFUE) a JSON para load_ley.py |

### Infraestructura cloud
- **Supabase**: proyecto `asistente-juridico` (ref: `cbiwhcfkaarnhenkryza`, región Europe West)
  - Conexión: Session Pooler `aws-1-eu-west-2.pooler.supabase.com`, usuario `postgres.cbiwhcfkaarnhenkryza`
  - Credenciales en `.streamlit/secrets.toml` (excluido de Git)
- **Streamlit Cloud**: app desplegada y operativa (cuenta `Indalo63`, repo `stack-sql-vscode`)
  - Secrets configurados con Session Pooler (no IPv6 directo)
- **GitHub**: repositorio `Indalo63/stack-sql-vscode` (rama `master`)

### Arquitectura de credenciales
- `app/config.py`: lee `os.environ` primero (scripts/CLI), luego `st.secrets` (Streamlit)
- Local: `.env` + `.streamlit/secrets.toml` (ninguno se sube a Git)
- Producción: secrets en dashboard de Streamlit Cloud
- Scripts con `--supabase`: leen `.streamlit/secrets.toml` y convierten a Session Pooler automáticamente

## Próximos pasos

### En curso
- [FASE 4] 5/14 leyes ALTA cargadas — pendientes: LPAP, RIRS, MUFACE, LMRFP, RDSA, RDRD, REGI, LOTCU, ET

### Completado en sesión 28/06/2026
- [✅ FASE 1] 8 leyes ALTA prioridad: LODP, LOTC, LGOB, LOCE, LBRL, LTBG, LOPD, LOEPSF (673 arts.)
- [✅ FASE 2] 4 leyes: LOPJ, LGSS, LTPP, LGT (1.603 arts.)
- [✅ Validación] 79 preguntas oficiales cruzadas con BD → 0 artículos ausentes
- [✅ Generador] build_test_bank.py mejorado: few-shot oficial, sub-artículos, estilo mixto, prioridad examinables
- [✅ Producto] Objetivo redefinido: plataforma multi-oposición, multi-formato, configurable sin código
- [✅ FASE 3] TUE (ley_id=33, 55 arts.) + TFUE (ley_id=34, 358 arts.) desde EUR-Lex con embeddings
- [✅ FASE 4 — bloque 1] LOIEMH (35, 130 arts.) + LOIVG (36, 107 arts.) + LJCA (37, 175 arts.) + LGS (38, 105 arts.) + LEF (39, 134 arts.) — 651 artículos con embeddings

### Hitos pendientes — Normativa (GACE)
- [FASE 4 — ALTA] LPAP, RIRS, MUFACE, LMRFP, RDSA, RDRD, REGI, LOTCU, ET (9 leyes)
- [FASE 4 — MEDIA] LOIT, LCCU, LASEE, PGCP, ENI, CC, LPNAT, LE (8 leyes)
- Generar banco IA: `build_test_bank.py --supabase --n 50` (~300 preguntas, ~3-4€)

### Hitos pendientes — Ejercicio tipo test
- Simulacro: 100 preguntas, temporizador, puntuación A-(E/3), escala 0-50 pts
- Interfaz de revisión: tab "Revisión" para aprobar/rechazar preguntas IA
- Exportar banco a CSV / Moodle XML
- Historial de conversación en Q&A (multi-turno con st.session_state)

### Hitos pendientes — Supuesto práctico (nuevo módulo)
- Diseño del modelo de datos: tabla `casos_practicos` (expedientes, cuestiones, normativa aplicable)
- Generador de supuestos prácticos con Claude (estilo GACE: expedientes INAP/FEGA con plazos, órganos, fórmulas)
- Módulo de práctica en Streamlit: presentar caso, respuesta libre, evaluación IA con retroalimentación
- Banco de supuestos reales 2024-2025 cargado como referencia few-shot

### Hitos pendientes — Plataforma y configurabilidad
- Panel de administración de convocatoria: gestionar leyes, fórmula de corrección, tipos de ejercicio sin código
- Soporte multi-oposición: segunda oposición integrada (a definir) usando la misma arquitectura GACE
- Sincronización automática BOE mediante GitHub Actions (textos legales siempre actualizados)
