# CLAUDE.md – Plataforma IA de Preparación de Oposiciones

> Repo: `Indalo63/stack-sql-vscode` (rama `master`). El backlog detallado vive en `TODO.md`.

## Quién soy
Indalecio Plaza: licenciado en Derecho, consultor y técnico en bases de datos relacionales (PostgreSQL), desarrollo web y automatización con IA.

## Objetivo
Plataforma modular de preparación de oposiciones basada en IA, **configurable sin tocar código**: la normativa, el formato de examen, la fórmula de corrección y los tipos de ejercicio de cada convocatoria se gestionan desde la base de datos o desde ficheros de configuración, nunca hardcodeados.

Permite a cualquier opositor: consultar su normativa en lenguaje natural (Q&A semántico), practicar con tipo test calibrado al examen real, entrenar supuestos prácticos generados por IA y hacer simulacros cronometrados con la fórmula oficial.

La oposición de referencia es **GACE** (Cuerpo General Administrativo del Estado): su programa, banco de preguntas oficiales y supuestos prácticos son la base del sistema. La arquitectura está pensada para integrar cualquier otra oposición con mínimo esfuerzo. Audiencia: preparadores y academias de cualquier cuerpo o escala.

## Producto y audiencia

### Modelo de negocio
Dos líneas que se desarrollan en paralelo:

1. **B2B — Herramienta para academias y preparadores (primer cliente de pago, horizonte 3-6 meses):**
   La academia usa Streamlit como herramienta interna de su equipo (generar, revisar, exportar preguntas). El banco aprobado se exporta a su LMS (Moodle XML / CSV) para que sus alumnos practiquen. La academia gestiona sus propios alumnos.

2. **B2C — Plataforma propia para el opositor (segunda línea, horizonte 6-12 meses):**
   El opositor se suscribe directamente. La plataforma gestiona usuarios, simulacros, estadísticas y seguimiento. Requiere frontend dedicado (FastAPI + React/Vue) sobre el mismo backend IA.

### Arquitectura de referencia
```
[Backend IA — valor diferencial]          [LMS de la academia]
  Streamlit admin (generación/revisión)     Moodle / TalentLMS / etc.
  Claude + pgvector + BOE          →→→      Alumnos, simulacros, estadísticas
  exporta Moodle XML / CSV
```

### Perfiles de usuario
- **Editor / revisor (academia):** genera preguntas por ley, las revisa y exporta. Accede vía Streamlit con login Google OAuth.
- **Alumno (opositor):** practica en la plataforma con login email+contraseña (Supabase Auth). Accede a repaso adaptativo, simulacro personal y prueba de nivel.
- **Administrador de plataforma:** gestiona leyes, convocatorias y fórmula desde BD sin tocar código.

## Entorno técnico
- **Sistema:** Windows + WSL2 (Ubuntu 24.04 LTS). Git instalado y configurado.
- **Directorio del proyecto:** `~/dev/stack-sql-vscode`
- **Python 3** disponible en WSL2.
- **Base de datos:** Supabase cloud (PostgreSQL 16 + pgvector), región Europe West, conexión vía Session Pooler. Docker Desktop disponible para desarrollo local opcional.
- **IA:** Claude (Anthropic API) como motor de generación/evaluación; OpenAI API para embeddings.
- **Interfaz:** Streamlit desplegado en Streamlit Cloud (producción).
- **Claude Code** como copiloto técnico y documental.

### Credenciales (estructura, sin valores)
- `app/config.py` lee `os.environ` primero (scripts/CLI) y luego `st.secrets` (Streamlit).
- Local: `.env` + `.streamlit/secrets.toml` (ninguno se sube a Git).
- Producción: secrets en el dashboard de Streamlit Cloud.
- Scripts con `--supabase`: leen `.streamlit/secrets.toml` y convierten a Session Pooler automáticamente.
- **Las credenciales reales (ref de Supabase, usuario, claves API) no se reproducen en este archivo.** Viven solo en `.env` / `secrets.toml`.

## Forma de trabajo con la IA
- Avanzar siempre en **pasos numerados** (Paso 1, Paso 2…). No pasar al siguiente hasta confirmar el anterior.
- Explicaciones en español, técnicas pero con tono docente. Breves y accionables, con comandos concretos pegables en WSL2.
- Al proponer cambios en archivos, indicar siempre: **ruta**, **bloque a crear/modificar** y **contenido completo del bloque**.
- Documentación técnica en `docs/` (despliegue, configuración, arquitectura). Guía principal: `docs/stack-sql-vscode.md`. Todo en Markdown.
- Los archivos nuevos respetan la estructura existente del repo.

## Qué NO hacer
- **No hardcodear** parámetros de convocatoria (leyes, fórmula, plazos, tipos de ejercicio): siempre en BD o config.
- **No reproducir credenciales** ni valores sensibles en código, documentación ni respuestas.
- **No avanzar de paso** sin confirmación explícita.
- En generación de preguntas, **no violar ninguna de las normas obligatorias** de la sección siguiente (son innegociables).
- **No inventar** estado del proyecto: si un dato no consta aquí o en `TODO.md`, consultarlo antes de asumirlo.

## Normas obligatorias para la generación de preguntas tipo test
Se aplican SIEMPRE en `app/test_pipeline.py` y en cualquier futuro generador. Innegociables; derivan del análisis del examen oficial GACE 2025.

1. **Sin símbolos matemáticos.** Las preguntas, opciones y explicaciones nunca contienen símbolos (=, >, <, %, +, ×, ÷, →, fracciones, etc.). Escribir en texto: "igual a", "mayor que", "porcentaje", etc.
2. **El enunciado cita la norma completa.** Empieza siempre con "Según el artículo [N] de [nombre completo de la ley]," o "De acuerdo con el artículo [N] de [nombre completo de la ley],". Nunca omitir el nombre completo.
3. **Opciones en minúsculas a/b/c/d** — nunca en mayúsculas.
4. **Distractores de alta precisión.** Las opciones incorrectas difieren de la correcta solo en datos exactos (un plazo, un porcentaje, un órgano, una palabra clave). Prohibido usar distractores conceptualmente muy distintos: el error debe ser sutil y técnico (estilo GACE).
5. **Dificultad alta.** Preguntar por datos exactos del artículo (plazos, porcentajes, órganos competentes, requisitos), no por conceptos generales.

## Estado actual

### Normativa cargada en `normas.*` (con embeddings)
60 normas cargadas y operativas (ley_ids hasta 79):
CE, LPAC, LRJSP, TREBEP, LGP, LCSP, GACE_NORM, LODP, LOTC, LGOB, LOCE, LBRL, LTBG, LOPD, LOEPSF, LOPJ, LGSS, LTPP, LGT, TUE, TFUE, LOIEMH, LOIVG, LJCA, LGS, LEF, LPAP, RIRS, MUFACE, LMRFP, RDSA, RDRD, REGI, LOTCU, ET, LOIT, LASEE, ENI, CC, LPNAT, LE, RLEF, RLGS, BCPSA, RRCP, IGAE, ACF, PLJ, ROCE, LGPD, LAEPD, LSSF, LDEP, LOE, LO4000, LASIL, LTRANS, LGUM, LGT22, LEPP.

*(Mapeo completo `ley_id` → código → nombre, e inventario de leyes pendientes BOE-443 con sus ELI, en `TODO.md`.)*

### Banco de preguntas (`normas.preguntas_test`)
- **209 preguntas oficiales** cargadas (104 GACE 2024 + 105 GACE 2025), `revisada=TRUE`. *(Son preguntas, no exámenes completos.)*
- 167 con `ley_id` + `epigrafe_id` identificados (76%); 52 con `ley_id=NULL` correctamente (actualidad/normas no cargadas — no es un gap, ver `scripts/asignar_leyes.py`).
- Cobertura BOE-443: **76,6%** del examen real (TUE/TFUE 9,6% fijo; actualidad 5,7% impredecible; leyes fuera del BOE-443 6,7%).

### Otras tablas y migraciones
- `normas.oposiciones` + `normas.oposicion_leyes`: 60 leyes GACE con bloque (I–VI), excluir_test y peso en simulacro.
- `normas.convocatorias`: metadatos 2024 y 2025. Fórmula GACE: **A−(E/3)**, 100 preguntas, 90 min, mínimo 25/50, escala 0–50.
- `normas.progreso_usuario`: historial SM-2 por alumno (intervalo, repeticiones, facilidad, proxima_revision, total_vistas, total_correctas).
- `normas.epigrafes`: 58 temas oficiales GACE (Anexo VII) por bloque, verificados contra el PDF fuente.
- `normas.plan_estudio`: estado vivo del alumno por bloque (fase, % acierto, estudiado) — se actualiza vía `get_fase_alumno`.
- `normas.simulacros_academia` + `simulacro_academia_preguntas`: simulacro de academia con preguntas fijas y ventana temporal.
- Migraciones ejecutadas: `020`–`032`.
  - `025`: repertorio completo GACE en oposicion_leyes (60 leyes, preguntas_simulacro≥0)
  - `026`: columna bloque I–VI en oposicion_leyes según programa oficial GACE 2025
  - `027`: tabla progreso_usuario (sistema repaso adaptativo SM-2)
  - `028`: columna excluir_test (GACE_NORM y LSSF excluidas del test)
  - `029`: nombre_corto actualizado con etiqueta coloquial para las 59 leyes GACE activas

### Scripts disponibles
| Script | Función |
|--------|---------|
| `load_ley.py` | Carga una ley desde BOE (HTML → artículos + embeddings) |
| `parse_boe.py` | Parsea HTML del BOE a JSON estructurado |
| `generate_embeddings.py` | Genera embeddings para artículos sin vector |
| `sync_boe.py` | Sincroniza actualizaciones del BOE |
| `build_test_bank.py` | Genera preguntas IA en lote y las guarda en BD |
| `parse_official_exams.py` | Parsea PDFs de exámenes oficiales GACE y los carga |
| `load_convocatoria.py` | Carga criterios + programa GACE como ley para Q&A |
| `parse_eurlex.py` | Parsea HTML de EUR-Lex (TUE/TFUE) a JSON para `load_ley.py` |
| `asignar_leyes.py` | Resuelve `ley_id` de preguntas oficiales sin mapear, comparando el nombre de norma citado contra el catálogo de leyes cargadas |
| `asignar_epigrafes.py` | Clasifica preguntas contra el temario oficial (`normas.epigrafes`) vía Claude; reutilizable si el temario cambia |

Flujo de carga de una ley nueva:
`parse_boe.py <ELI> --output data/leyes/XX.json` → `load_ley.py XX.json --supabase --embeddings`

## Hito inmediato — Plataforma de estudio para el alumno

Diseño completo aprobado el 05/07/2026. Implementación en 9 pasos secuenciales.

**Arquitectura aprobada:**
- Jerarquía: Oposición → Modo (Repaso / Simulacro) → Bloque o Tema → sesión
- Auth: Google OAuth (editor/academia) + email+contraseña Supabase Auth (alumno)
- Prueba de nivel: 40 preguntas, dificultad creciente individual, gratuita con registro, genera informe de partida + plan de estudio
- Mix adaptativo 4 fases (Inicio 0/40/60 · Aprendizaje 15/20/65 · Consolidación 30/25/45 · Pre-examen 40/35/25) — porcentajes: débiles/oficial/nueva
- Bloque "estudiado" = ≥70% acierto agregado en ese bloque
- Simulacro personal: 50 preguntas, bloques ≥70%, fórmula oficial, requiere prueba de nivel previa
- Simulacro academia: mismas preguntas para todos, ventana temporal, sin personalización
- Visualización en 3 momentos: panel inicio + composición tanda + resultado

| Paso | Tarea | Estado |
|------|-------|--------|
| 1 | Migración 030: campo `dificultad` en `preguntas_test` + tabla `normas.epigrafes` | ✅ Completado |
| 2 | Migración 031: tabla `normas.plan_estudio` | ✅ Completado |
| 3 | Migración 032: tabla `normas.simulacros_academia` | ✅ Completado |
| 4 | Supabase Auth: registro email+contraseña para alumnos | ✅ Completado |
| 5 | `retrieval.py`: funciones stats, fase, mix adaptativo | ✅ Completado |
| 6 | `streamlit_app.py`: reestructura navegación + prueba de nivel | ✅ Completado |
| 7 | Visualización de progreso (3 momentos) | ⏭️ Siguiente |
| 8 | Simulacro personal | Pendiente |
| 9 | Simulacro de academia | Pendiente |

### Completado — Paso 6: navegación alumno + prueba de nivel (07/07/2026)
- [✅ `retrieval.get_preguntas_prueba_nivel`] Reparto proporcional por peso oficial entre los 6 bloques (todos, no solo "estudiado"), orden por dificultad creciente.
- [✅ `streamlit_app.py`] Cuando hay alumno logueado (Supabase Auth), flujo propio separado del editor: jerarquía Oposición → Modo (Prueba de nivel / Repaso) → Bloque → sesión. Onboarding de bienvenida para alumnos nuevos; mensajes de error claros en login/registro (email ya registrado, credenciales incorrectas, contraseña corta). El flujo Q&A/Generar test/Editor (Google OAuth) queda intacto.
- [✅ Verificado en vivo, navegador real] Playwright headless contra Supabase real vía Session Pooler: registro → prueba de nivel (40 preguntas reales) → corrección → informe de partida por bloque → cambio automático a "Repaso" → re-login detecta alumno no-nuevo y preselecciona Repaso con el bloque más débil → tanda adaptativa cargada. Sin errores de consola. Datos de prueba (`plan_estudio`/`progreso_usuario`) borrados tras la verificación.
- [⚠️ Pendiente manual] 3 usuarios de prueba (`alumno.prueba.claude.paso6*@example.com`) quedan en Supabase Auth (no borrables con la clave anon) — eliminar desde el dashboard cuando se pueda.
- [✅ Bug corregido, `.streamlit/secrets.toml`] `SUPABASE_URL`/`SUPABASE_ANON_KEY` estaban después de `[auth.google]`, así que TOML las anidaba en esa tabla y el registro de alumno fallaba con "no configurados". Movidas antes de `[auth]`. **Revisar el mismo orden en los Secrets de Streamlit Cloud (producción)** antes de dar acceso a alumnos reales.
- [✅ Mejora Q&A, fuera del plan de 9 pasos] `qa_pipeline.py`/`retrieval.py`: el modo Q&A no sabía listar/resumir artículos a nivel de **capítulo** (solo título completo o agregados). Añadidas `get_capitulos_db`/`get_articulos_por_capitulo` + `_extraer_capitulo_id`; `_responder_resumen` ahora resuelve capítulo cuando la pregunta lo menciona. Verificado en vivo: "lista los artículos del Título I Capítulo II" → 25 artículos correctos (14-38).

### Completado — Paso 5: retrieval.py, mix adaptativo (06/07/2026)
- [✅ 05] `get_fase_alumno` (fase por cobertura de épigrafes + UPSERT `plan_estudio`), `get_stats_alumno` (panel), `get_preguntas_adaptativo` (mix débiles/oficial/nueva), `get_preguntas_simulacro_personal` (reparto proporcional, bloques ≥70%), `get_preguntas_simulacro_academia` (lee lista congelada). Las 5 probadas en vivo contra Supabase.
- [✅ Gap resuelto] 167/219 preguntas (76%) con `ley_id`+`epigrafe_id`; `scripts/asignar_leyes.py` (nuevo) + `scripts/asignar_epigrafes.py` reutilizables para futuras cargas.

### Completado — Paso 4: Supabase Auth alumno (06/07/2026)
- [✅ 04] `app/auth_alumno.py` + sección "Acceso Alumno" en sidebar (registro/login email+contraseña, independiente del Google del editor). Verificado en vivo contra Supabase Auth real. Pendiente conectar al SM-2 en el Paso 6.

### Completado — Migración 032 (06/07/2026)
- [✅ 032] `normas.simulacros_academia` + `simulacro_academia_preguntas`: simulacro con preguntas fijas por ventana temporal, flujo generado→autorizado (la academia nunca genera preguntas, solo autoriza).

### Completado — Migración 031 (06/07/2026)
- [✅ 031] `normas.plan_estudio`: estado vivo del alumno por bloque (fase, preguntas vistas/correctas, % acierto, estudiado). Umbral de fase resuelto en el Paso 5: % cobertura de épigrafes del bloque.

### Completado — Migración 030 (06/07/2026)
- [✅ 030] `normas.epigrafes` con los 58 temas oficiales GACE (Anexo VII), verificados 100% contra el PDF; `preguntas_test.dificultad` (1-3, default 2) y `preguntas_test.epigrafe_id` (FK nullable)
- [✅ Correcciones] Tema I.1 recuperado, artefactos OCR eliminados, texto I.8 completado, nombres de Bloque IV/V corregidos en `load_convocatoria.py`

### Completado — UX Refinamiento (sesiones 04-05/07/2026)
- [✅ 025] Repertorio completo GACE en oposicion_leyes (60 leyes)
- [✅ 026] Columna bloque I–VI en oposicion_leyes
- [✅ 027] Tabla progreso_usuario (SM-2: intervalo, repeticiones, facilidad, proxima_revision)
- [✅ 028] Columna excluir_test; GACE_NORM y LSSF excluidas del test GACE
- [✅ 029] nombre_corto con etiqueta coloquial + referencia oficial para 59 leyes
- [✅ SM-2] get_preguntas_sm2 + update_progreso_sm2 en retrieval.py
- [✅ Generar test] Sirve desde banco aprobado; SM-2 activo para usuarios logueados
- [✅ Sidebar] Bloques I–VI y leyes con checkboxes desmarcados por defecto; botones renombrados
- [✅ Banco IA] 10 preguntas LPAC generadas y validadas (sesión 30/06/2026)

Normas cargadas: 60 (ley_ids hasta 79). Pendiente baja urgencia: LCCU y PGCP (parser específico).
El backlog completo está en `TODO.md`.
