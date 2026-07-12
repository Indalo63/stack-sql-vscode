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

### Conectividad a Supabase desde este devcontainer (importante, se repite en cada sesión)
Este devcontainer no resuelve por IPv6 el host directo de Postgres (`db.<ref>.supabase.co`) → cualquier conexión directa falla con "Network is unreachable". Hay que enrutar por el **Session Pooler** (`aws-1-eu-west-2.pooler.supabase.com`, usuario `postgres.<ref>`).

**Para verificar código/queries en vivo (scripts sueltos, `python3 -c`, etc.):** usar `scripts/_supabase_env.py::load_supabase_secrets()` — llamarla *antes* de cualquier `from app... import`. Reutilizada ya por `asignar_leyes.py`, `asignar_epigrafes.py`, `asignar_epigrafe_leyes.py` y `load_convocatoria.py` (flag `--supabase`).

**Por qué no basta con exportar solo `DB_HOST`/`DB_USER` por variable de entorno** (error engañoso: Supavisor devuelve `no tenant identifier provided`, no un error de red): `app/config.py::_get()` cae a `import streamlit as st` en cuanto una clave (`DB_NAME`, `DB_PASSWORD`, `OPENAI_API_KEY`...) no está ya en `os.environ` — y ese `import streamlit` tiene el efecto secundario de volcar `st.secrets` sobre `os.environ`, pisando silenciosamente el override del pooler. `load_supabase_secrets()` evita esto exportando **las 5 claves `DB_*` a la vez** (más el resto de `secrets.toml`), así que `_get()` nunca necesita importar Streamlit. Confirmado en vivo el 11/07/2026.

**Para probar la app Streamlit completa (no solo scripts):** Streamlit vuelca `st.secrets` a variables de entorno al arrancar, así que ni siquiera `load_supabase_secrets()` sirve ahí — hay que editar `.streamlit/secrets.toml` temporalmente y restaurarlo al terminar (patrón ya usado en pasos anteriores, ver hito de abajo).

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
- `normas.historial_simulacros`: registro de cada intento de simulacro (personal/academia) con su nota, para "Mi progreso" del alumno.
- Migraciones ejecutadas: `020`–`033`.
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
| `asignar_epigrafe_leyes.py` | Clasifica cada tema oficial contra el catálogo completo de leyes de la oposición vía Claude; puebla `normas.epigrafe_leyes` (relación tema↔ley, usada por el selector Bloque→Tema→Ley de Administración) |

Flujo de carga de una ley nueva:
`parse_boe.py <ELI> --output data/leyes/XX.json` → `load_ley.py XX.json --supabase --embeddings`

## Hito inmediato — Plataforma de estudio para el alumno

Diseño completo aprobado el 05/07/2026. Implementación en 9 pasos secuenciales — **completados los 9 el 11/07/2026**. Pendiente de definir el siguiente hito.

**Arquitectura aprobada:**
- Jerarquía: Oposición → Modo (Repaso / Simulacro) → Bloque o Tema → sesión
- Auth: Google OAuth (editor/academia) + email+contraseña Supabase Auth (alumno)
- Prueba de nivel: 40 preguntas, dificultad creciente individual, gratuita con registro, genera informe de partida + plan de estudio
- Mix adaptativo 4 fases (Inicio 0/40/60 · Aprendizaje 15/20/65 · Consolidación 30/25/45 · Pre-examen 40/35/25) — porcentajes: débiles/oficial/nueva
- Progreso vivo (`plan_estudio`) por **tema oficial** (epígrafe), no por bloque — rediseño 11/07/2026, ver sección debajo. Bloque "estudiado" = todos sus temas con preguntas vistas ≥70% de acierto (derivado, no se guarda una fila por bloque)
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
| 7 | Visualización de progreso (3 momentos) | ✅ Completado |
| 8 | Simulacro personal | ✅ Completado |
| 9 | Simulacro de academia | ✅ Completado |

### Completado — Rediseño navegación "Gestión banco de preguntas" (12/07/2026)
Fase 1 del rediseño propuesto por el usuario en un boceto (PDF, diagrama a mano). Alcance acotado con él antes de tocar código (4 rondas de preguntas): **solo navegación + Nuevas preguntas + Revisar preguntas + Generar test**. El resto del boceto queda explícitamente para fases posteriores, y **no se empieza la siguiente hasta cerrar esta**.

- [✅ Renombrado] El perfil "Administración" pasa a llamarse **"Gestión banco de preguntas"** en toda la UI (botón de Acceso, título, textos). El valor interno `st.session_state.acceso == "administracion"` se mantiene (solo cambia lo visible); nuevo mapa `_ETIQUETA_ACCESO` porque `.capitalize()` ya no daba una etiqueta correcta.
- [✅ Navegación] `modo` se elige **antes** que cualquier selector. El modo "Editor" (contenedor con tabs Generar/Revisar) **desaparece**: sus dos tabs pasan a ser modos de primer nivel. Radio final: **Q&A / Nuevas preguntas / Revisar preguntas / Generar test / Simulacros academia**.
- [✅ Fin del selector global] El sidebar Bloque→Tema→Ley global (que condicionaba a todos los modos por igual) se elimina. Cada modo monta **su propio selector**, con `session_state` aislado por prefijo (`qa_*`, `nq_*`, `gt_*`, `rev_*`) para que la selección de un modo no arrastre a la de otro. Helper común `_checkboxes(...)` para el patrón multi-checkbox + "Seleccionar todo"/"Elimina la selección", que antes estaba triplicado.
  - **Q&A** y **Nuevas preguntas**: cascada Bloque→Tema→Ley multi-selección (`_selector_bloque_tema_ley`).
  - **Revisar preguntas**: radio **excluyente** "Por bloque" / "Por tema", selección **única** en ambas ramas (`_selector_revisar`).
  - **Generar test**: Bloque **único** → radio excluyente "Generar por" Tema/Ley → multi-checkbox dentro de ese bloque (`_selector_generar_test`). **Nunca genera sobre el bloque completo sin acotar** — requisito explícito del usuario.
  - **Simulacros academia**: sin cambios (no usa bloques/leyes).
- [✅ `retrieval.py`] `get_preguntas_sm2` cambia de firma: `bloques: tuple[str, ...]` → `ley_ids: tuple[int, ...]` (y `ol.bloque = ANY(...)` → `pt.ley_id = ANY(...)` en sus dos queries). Necesario porque el nuevo "Generar test" acota a temas/leyes, no a bloques; el `JOIN oposicion_leyes` se conserva como guardia de que la ley pertenece a la oposición. Único punto de uso (`streamlit_app.py`), sin migración de BD.
- [✅ Verificado en vivo, navegador real] Playwright headless contra Supabase real vía Session Pooler. Como el login Google **no es automatizable** aquí, se parcheó temporalmente la autenticación (variable `FAKE_EDITOR_EMAIL`) para simular sesión de editor, se recorrieron los 5 modos, y **se revirtió el parche** (verificado: 0 referencias en el código final). Comprobado: los 5 modos presentes y "Editor" ya no existe; Revisar preguntas alterna Bloque/Tema y muestra el panel de progreso con cifras reales (70 pendientes / 0 revisadas); Generar test muestra Bloque único → Tema/Ley → multi-checkbox; Nuevas preguntas exige la cascada completa; Simulacros academia no pide bloque. Sin errores de consola. `secrets.toml` restaurado al valor original.
- [ℹ️ Nota de entorno, resuelta] Playwright necesitaba libs del sistema que faltaban (`libatk`, `libXcomposite`…) y `apt update` fallaba por un repo de yarn roto. Se desactivó ese repo (`/etc/apt/sources.list.d/yarn.list` → `/tmp/yarn.list.disabled`) y se instalaron con `playwright install-deps chromium`. Si vuelve a fallar en otra sesión, ese es el camino.

### Completado — Lista blanca de editores (migración 036, 12/07/2026)
**Riesgo corregido.** El perfil de gestión **no validaba qué cuenta de Google entraba**: la única comprobación era `logged_in = "email" in user`, así que *cualquier* cuenta que completase el OAuth obtenía acceso completo (generar, aprobar y **borrar** preguntas; autorizar simulacros). Lo único que mantenía la app cerrada era el modo *Testing* de la pantalla de consentimiento de Google Cloud — un control externo al código que se anula al publicarla.

- [✅ Migración 036, `sql/ddl/036_editores.sql`] Tabla `normas.editores` (email PK, nombre, academia, activo, creado_en, creado_por). La lista vive **en BD**, no en código ni en secrets: alta/baja sin redesplegar (principio "configurable sin tocar código"), y `academia` queda reservada para el modelo B2B. Revocar = `activo=FALSE` (preferible a borrar: conserva la trazabilidad de `preguntas_test.revisado_por`). Aplicada en Supabase; **sembrada con `indaleciopf@gmail.com`** — sin esa fila nadie podría entrar.
- [✅ `retrieval.es_editor_autorizado(email)`] Comprueba la lista blanca (case-insensitive, exige `activo=TRUE`).
- [✅ `streamlit_app.py`] Tras validar la sesión Google, si el email no está autorizado se muestra "⛔ Acceso denegado" + botón de cerrar sesión y `st.stop()`: no ve ningún modo de gestión ni dato alguno. Sugiere entrar por Alumno.
- [✅ Verificado en vivo, navegador real] Cuenta no autorizada (`atacante.no.autorizado@gmail.com`): ve "Acceso denegado" y **ningún** modo (Modo/Nuevas preguntas/Revisar preguntas ausentes del sidebar). Cuenta autorizada (`indaleciopf@gmail.com`): entra con normalidad y ve los 5 modos. Probado también a nivel de función: mayúsculas/minúsculas indiferentes, email vacío rechazado, `activo=FALSE` bloquea. Sin errores de consola.
- **Para dar de alta a un editor nuevo:** `INSERT INTO normas.editores (email, nombre, creado_por) VALUES ('...', '...', '...');` — no requiere tocar código ni redesplegar.

**Nota:** esto no sustituye a mantener la pantalla de consentimiento OAuth bien configurada, pero ya no es la única barrera: aunque se publicase a producción, una cuenta ajena no pasaría de "Acceso denegado".

### Completado — Nombres de ley: `nombre_oficial` (migración 038, 12/07/2026)
Auditoría pedida por el usuario ("comprueba que siempre se aplica bien el nombre de las leyes"). **Encontró un incumplimiento real de la norma obligatoria nº2.**

**El problema:** `leyes.nombre` no era homogéneo — **25 de las 60** leyes lo tenían *sin* la referencia oficial (LPAC era `"Ley del Procedimiento Administrativo Común de las Administraciones Públicas"`, sin el `"Ley 39/2015, de 1 de octubre"`). Como el generador pasaba ese campo al prompt, Claude completaba la referencia **de memoria unas veces sí y otras no**: **18 de las 70** preguntas pendientes citaban la norma de forma incompleta, incumpliendo la norma nº2 ("el enunciado cita la norma completa"). Preguntas de la *misma* ley salían unas bien y otras mal — el síntoma delator.

**Modelo de nombres acordado con el usuario (3 campos, cada uno con su papel):**
| Campo | Contenido | Quién lo usa |
|---|---|---|
| `nombre_oficial` (nuevo) | Título exacto del BOE | **Todo lo que cita la norma**: generador de preguntas, Q&A, y las futuras actualizaciones de legislación |
| `nombre` | Nombre de trabajo (se deja como estaba) | Nada que cite; contexto interno |
| `nombre_corto` | Etiqueta de UI (`Ley 39/2015 — Procedimiento Administrativo`) | Sidebar y selectores |

- [✅ Migración 038, `sql/ddl/038_nombre_oficial.sql`] Columna `nombre_oficial`. **Los títulos no están escritos de memoria**: se descargaron del propio BOE (cabecera `documento-tit` de cada `url_boe`) — 56 de 60. Las otras 4 (CE1978, TUE, TFUE, GACE_NORM) no proceden del BOE y ya tenían nombre correcto, así que heredan su `nombre`. Aplicada; 60/60 con `nombre_oficial`.
- [✅ `retrieval.py`] `get_leyes_disponibles` (sus 3 ramas) y `get_ley_info` devuelven `nombre_oficial`.
- [✅ `streamlit_app.py` + `qa_pipeline.py`] El generador y `run_qa` usan `nombre_oficial` (con *fallback* a `nombre`). La **etiqueta de pantalla no cambia**: el editor sigue viendo el nombre corto en los selectores.
- [✅ Las 18 preguntas mal citadas, corregidas] Sustitución del nombre incompleto por el oficial en el enunciado (no se regeneraron: opciones y respuesta correcta no se tocan). Verificado: **0 de 70** preguntas citan ya la norma sin referencia oficial.
- [✅ Verificado en vivo] Pregunta nueva de LPAC generada tras el cambio: *"Según el artículo 27.4 de la **Ley 39/2015, de 1 de octubre**, del Procedimiento Administrativo Común…"*. La causa está resuelta, no solo el síntoma.

**🔴 PENDIENTE IMPORTANTE — dos leyes con la referencia oficial contradictoria.** Requiere criterio jurídico del usuario (el código no puede decidirlo). No bloquea, pero **sí afecta a la calidad jurídica de las preguntas**: el generador cita ahora `nombre_oficial`, así que si el título es el equivocado, las preguntas de esas dos leyes citarán una norma que no es. Detalle y query de comprobación en `TODO.md`.
- **RRCP**: su `url_boe` apunta al *RD 2073/1999 "por el que se **modifica** el Reglamento del Registro Central de Personal"* — es un decreto **modificador**, no el reglamento. (Ojo: ya hubo un vaivén previo RD 2073/1999 ↔ RD 172/1988, ver `git log` de la migración 029.)
- **BCPSA**: el BOE devuelve *"Orden HFP/688/2017, de 20 de julio"*, pero `numero_oficial` dice *"Real Decreto 364/2017, de 8 de abril"*. **Se contradicen**; el `url_boe` guardado apunta a la Orden.

### Completado — Backfill de tema en las preguntas IA (12/07/2026)
Al explicar por qué los contadores por tema sumaban más que el total del banco, salió a la luz un hueco de datos: **60 de las 70 preguntas IA pendientes no tenían tema asignado** (`preguntas_test.epigrafe_id IS NULL`). El generador (`build_test_bank._save`) acepta `epigrafe_id` pero **la app nunca se lo pasa**, así que toda pregunta generada desde Streamlit nace sin tema.

Consecuencia (era lógica de negocio, no un bug): sin tema propio, el contador por tema tenía que deducirlo a través de la ley, y una misma ley es material de muchos temas (LPAC → **18** temas, LGP → 15). Las 10 preguntas de LPAC se contaban en los 18 temas que la estudian, de ahí que la suma se disparase.

- [✅ Backfill ejecutado] `scripts/asignar_epigrafes.py --supabase --n 100` sobre las 60 sin tema: **60/60 OK, 0 errores**. Dry-run previo sobre 5 para revisar calidad (TUE → tema II.1, correcto). No tocó las preguntas oficiales (ya tenían tema).
- [✅ Resultado] Las 70 pendientes reparten ahora en **12 temas oficiales** sumando **exactamente 70** (antes, contadas vía ley, se solapaban). Reparto: IV.7 (20), VI.1 (11), II.6 (9), II.1 (8), IV.11 (8), VI.3 (3), VI.5 (3), II.3 (2), IV.12 (2), VI.4 (2), II.5 (1), VI.2 (1).
- [ℹ️ Contador del selector, sin cambios por decisión del usuario] `pendientes_por_tema` sigue contando **vía ley** (tema → leyes → pendientes), no por el `epigrafe_id` de la pregunta. Es lo coherente con lo que el editor realmente ve: el filtro "Por tema" de Revisar resuelve tema → leyes y `_get_pending` filtra por `ley_id`. Si algún día se quiere que "Revisar por tema" muestre **solo las preguntas de ese tema** (exacto, sin solape), hay que cambiar **las dos cosas a la vez**: `_get_pending` (filtrar por `epigrafe_id`) y `pendientes_por_tema`.

**[✅ Corregido el 12/07/2026] El generador ya asigna el tema al crear la pregunta.** El script CLI (`build_test_bank.run()`) siempre lo hizo bien — pedía el tema a Claude **dentro del mismo prompt que genera la pregunta** y lo validaba contra los temas del bloque de la ley (`_build_prompt(epigrafes=...)` + `_parse_and_validate(temas_validos=...)`). La app de Streamlit simplemente no usaba esa parte: llamaba a `_build_prompt` sin `epigrafes` y a `_save` sin `epigrafe_id`. Corregido replicando el patrón del CLI en el modo "Nuevas preguntas" (`get_bloque_y_epigrafes` → prompt con temas → validación → `_save(..., epigrafe_id=...)`). **No cuesta llamadas extra a la API**: el tema viene en la misma respuesta que la pregunta. Si una ley no tiene temas asociados, avisa y guarda sin tema (no rompe); un contador informa de cuántas quedaron sin tema. [✅ Verificado en vivo, navegador real] Clic real en "Generar y guardar en BD" → la pregunta creada nace con su tema oficial (V.2), sin aviso de "sin tema". Pregunta de prueba borrada; BD queda con las 70, todas con tema.

### Completado — Revisar preguntas: hacer visible dónde está el trabajo (12/07/2026)
Detectado por el usuario al ver la app: el panel decía **70 pendientes (todo el banco)** pero el bloque seleccionado (I, el que sale por defecto) mostraba "No hay preguntas pendientes". No era un bug — las 70 estaban en los bloques II (20), IV (30) y VI (20), y el Bloque I está genuinamente vacío. La anomalía era **de diseño**: el contador es global pero la lista está filtrada, así que la app decía *cuánto* trabajo hay pero no *dónde*, y había que ir probando bloques (o los 58 temas) a ciegas.

- [✅ `retrieval.py`] `pendientes_por_bloque(oposicion_id)` y `pendientes_por_tema(oposicion_id)`. **Ojo con el conteo por tema:** una misma ley puede ser relevante para varios temas (`epigrafe_leyes` es N:M), así que la suma por temas **excede** el total del banco — no es un reparto, es "cuántas verás si eliges este tema", que es justo lo que necesita el editor. Documentado en el docstring.
- [✅ `streamlit_app.py`, `_selector_revisar`] Las etiquetas de Bloque y Tema llevan el número de pendientes (`IV — Derecho Administrativo · 30`), con un caption que lo explica.
- [✅ Mensaje de vacío útil] Cuando la selección no tiene pendientes, ahora dice **dónde sí las hay** ("Sí hay pendientes en: II — Unión Europea: 20 · IV — Derecho Administrativo: 30 · VI — Gestión Financiera: 20") en vez de dejar al editor a ciegas.
- [✅ Subtítulo sin ruido] Antes listaba las 8 leyes del bloque aunque ninguna tuviera preguntas; ahora solo las que **realmente aportan** pendientes (`Pendientes de revisión — LGS, LPAC, RLGS`).
- [✅ Verificado en vivo, navegador real] Desplegable de Bloque mostrando los contadores; Bloque I (vacío) indica dónde está el trabajo; Bloque IV muestra "30 preguntas pendientes" y solo las 3 leyes con trabajo. Conteos cuadrados contra BD (suma por bloques = 70 = contador global). Sin errores de consola.

### Completado — Pantalla de gestión de editores (migración 037, 12/07/2026)
Hasta ahora dar de alta a un editor era un `INSERT` a mano. Ahora se hace desde la app. Decisiones confirmadas con el usuario antes de implementar: (1) solo los **administradores** gestionan la lista (nueva columna `rol`), no cualquier editor; (2) la app **bloquea** revocarse a uno mismo y quedarse sin ningún admin activo.

- [✅ Migración 037, `sql/ddl/037_editores_rol.sql`] `normas.editores.rol` (`admin`/`editor`, CHECK constraint, default `editor`). `indaleciopf@gmail.com` promovido a `admin` — **sin al menos un admin nadie podría gestionar la lista**. Aplicada en Supabase.
- [✅ `retrieval.py`] `get_editor` (ficha con rol; sustituye a `es_editor_autorizado` en la app, que se mantiene por compatibilidad), `listar_editores`, `alta_editor`, `revocar_editor`, `cambiar_rol_editor`. **Las protecciones anti-bloqueo viven en la capa de datos, no solo en la UI**: `revocar_editor` rechaza revocarse a uno mismo y rechaza dejar cero admins activos; `cambiar_rol_editor` rechaza degradar al último admin. Así ninguna vía (ni un bug de UI) puede dejar la app sin acceso de gestión. `alta_editor` normaliza el email a minúsculas y **reactiva** la fila si el email ya existía revocado (no duplica: conserva el histórico).
- [✅ `streamlit_app.py`] Nuevo modo **"Editores"**, visible **solo para `rol='admin'`** (`_MODOS` se construye condicionalmente). Formulario de alta (email + nombre + rol) y listado con cambio de rol, Revocar y Reactivar. El botón Revocar de la propia cuenta aparece deshabilitado. El sidebar muestra "Administrador"/"Editor" bajo el email.
- [ℹ️ Bug de UX corregido durante la verificación] Los `st.success()` de alta/revocación/reactivación **nunca llegaban a verse**: el `st.rerun()` inmediato posterior los borraba. Corregido con el patrón flash: el mensaje se guarda en `st.session_state["editores_flash"]` y se consume (`pop`) al principio del render siguiente.
- [✅ Verificado en vivo, navegador real] Playwright headless contra Supabase real. Editor con `rol='editor'`: **no ve** el modo "Editores" (sidebar lo etiqueta como "Editor"). Admin: ve la pantalla, da de alta por clic real (email en mayúsculas → se guarda normalizado), alta duplicada bloqueada con mensaje, revocar → aparece como "revocado", reactivar → vuelve a activo; los tres avisos visibles tras el rerun. Botón Revocar de la propia fila deshabilitado. A nivel de función, probadas también las protecciones: revocarse a uno mismo y degradar al último admin fallan con mensaje claro. Sin errores de consola. Datos de prueba borrados; `normas.editores` queda solo con la cuenta del propietario.
- **Alta de un editor (flujo real):** no se generan ni envían credenciales — el editor entra con **su propia cuenta Google**. (1) Él te dice su email de Google; (2) tú lo das de alta en la pantalla "Editores"; (3) si la pantalla de consentimiento OAuth sigue en modo *Testing*, hay que añadirlo **además** como usuario de prueba en Google Cloud Console (ver pendiente de auditoría); (4) le envías la URL de la app. Autorizar **antes** de enviar la URL, o verá "Acceso denegado".

**⏳ Pendiente (12/07/2026) — auditar la pantalla de consentimiento de OAuth en Google Cloud.** No se ha revisado su estado real (no es accesible desde este entorno: requiere entrar a Google Cloud Console con la cuenta del proyecto). Qué hay que comprobar y por qué importa:
- **Modo de publicación**: *Testing* (solo entran las cuentas dadas de alta como usuarios de prueba, máx. 100; las sesiones caducan cada 7 días) vs *In production* (cualquier usuario de Google puede completar el OAuth). Con la lista blanca de la migración 036 ya no es crítico, pero conviene saber en cuál está: si sigue en *Testing*, **añadir un editor nuevo exige dos pasos** (usuario de prueba en Google Cloud + fila en `normas.editores`), lo cual es fácil de olvidar y da un error confuso.
- **Tipo de usuario**: *External* vs *Internal* (este último solo existe con Google Workspace).
- **URIs de redirección autorizados**: deben incluir la URL de producción (`https://<app>.streamlit.app/oauth2callback`) además de la de local, o el login falla en producción aunque funcione en desarrollo.
- **Estado de verificación**: si la app pide scopes sensibles y está sin verificar, Google muestra la pantalla de "app no verificada" a los usuarios.

**Pendiente — fases siguientes de este rediseño (no empezar hasta cerrar la fase 1):**
1. **Actualización Legislación** (rama del boceto, no existe hoy como pantalla): submodo *Automática* = revisa cambios del BOE en leyes ya cargadas; *Manual* = el editor dispara la comprobación a mano, ley por ley. En **ambos casos**, los cambios detectados se muestran para **aprobar antes de aplicarlos a la BD** (mismo espíritu que la revisión de preguntas) — requisito explícito del usuario. Hoy solo existe `scripts/sync_boe.py` (CLI, sin UI ni paso de aprobación).
2. **Generador de test de prueba** (Por tema completo / Por ley): simulacro de prueba para que el editor pruebe la experiencia del alumno. Es **distinto** del "Generar test" actual (repaso SM-2 del editor).
3. **Reubicación de "Simulacros academia"** en el árbol: el usuario indicó que es la vía para ofrecer simulacros a academias gestionadas por una sola persona — pendiente de concretar dónde cuelga.
4. **Panel de progreso de revisión**: posibles ajustes (el usuario lo dejó anotado como pendiente; hoy se queda tal cual, global y por supervisor).

### Completado — Administración: navegación Bloque → Tema → Ley (11/07/2026)
Petición del usuario tras ver el nuevo selector del alumno: el sidebar de Administración (Q&A / Generar test / Editor, Google OAuth) también debía dejar elegir el tema oficial dentro del bloque, para acotar qué leyes trabajar. Planificado con `EnterPlanMode` (2 rondas de preguntas + un ajuste de rumbo a mitad de implementación cuando el `--dry-run` reveló un problema de diseño, ver abajo).

- [✅ Migración 035, `sql/ddl/035_epigrafe_leyes.sql`] Tabla nueva `normas.epigrafe_leyes` (epigrafe_id, ley_id) — no existía ninguna relación tema↔ley en el esquema (`oposicion_leyes` vincula ley→bloque, `epigrafes` vincula tema→bloque, pero nada cruza tema con ley directamente). Aplicada en Supabase vía Session Pooler.
- [✅ `scripts/asignar_epigrafe_leyes.py`, nuevo] Mismo patrón que `asignar_epigrafes.py` (`--supabase`/`--dry-run`/`--delay`/`--epigrafe-id` para probar un solo tema): por cada tema, pide a Claude que elija qué leyes del catálogo son relevantes (multi-etiqueta; DELETE+INSERT por tema, así que es seguro re-ejecutarlo). **Decisión de diseño encontrada durante la verificación, no prevista en el plan inicial:** la primera versión limitaba el catálogo de leyes candidatas al mismo bloque del tema — el `--dry-run` sobre los 58 temas reveló que eso dejaba en blanco casos reales (tema I.9 "sector público institucional" sin LRJSP, que está archivada en el bloque IV; tema IV.2 "tipos de leyes" sin CE1978, archivada en el bloque I). Corregido antes de guardar nada: el catálogo pasa a ser **todas las leyes de la oposición**, no solo las del bloque del tema — confirmado con el usuario antes de aplicar el cambio. Backfill de los 58 temas GACE ejecutado y guardado (58/58, 0 errores, 0 temas sin ley asignada).
- [✅ `retrieval.py`] `get_leyes_disponibles` gana el parámetro `temas: tuple[int, ...] | None`. Importante: cuando se pasan temas, el filtro por tema **sustituye** al filtro por bloque (no se exige `ol.bloque = ANY(bloques)` además) — precisamente porque una ley relevante para un tema puede estar archivada en otro bloque del programa (el caso LRJSP/I.9 de arriba); exigir ambos habría descartado justo los cruces que la tabla nueva existe para capturar. Verificado contra la BD real: tema I.9 con bloque "I" seleccionado sí devuelve LRJSP (bloque real IV); sin filtro de tema, el comportamiento por bloque no cambia. `get_temas_por_bloques(oposicion_id, bloques)` nueva (versión plural de la que ya usa el alumno) para el selector multi-bloque del sidebar admin.
- [✅ `streamlit_app.py`] Nuevo bloque **Tema** en el sidebar admin, entre Bloque y Ley, mismo patrón de checkboxes + "Seleccionar todo"/"Elimina la selección" que ya usan Bloque y Ley — aplica a los 3 modos (Q&A, Generar test, Editor) porque comparten el mismo sidebar. `leyes_sel`/`bloques_sel` mantienen la misma forma para el resto del código (sin cambios en Q&A/Generar test/Editor).
- [ℹ️ Riesgo conocido, no bloqueante] Si algún tema no tiene ninguna ley asociada (no ocurre hoy, backfill 58/58 completo), el selector de Ley se queda vacío y bloquea con el aviso ya existente — mismo comportamiento que cuando un bloque no tiene leyes, no es un caso nuevo.
- [⚠️ Pendiente de verificación manual] El login Google no es automatizable desde este entorno (headless, sin credenciales OAuth reales) — el filtrado se verificó llamando directamente a `get_leyes_disponibles`/`get_temas_por_bloques` contra la BD real (ver arriba), pero falta una revisión visual del sidebar completo por el usuario con su propia sesión Google.

### Completado — Repaso por tema oficial, no por bloque (rediseño post-hito, 11/07/2026)
Petición explícita del usuario tras cerrar los 9 pasos: "incluir en cada bloque los temas oficiales correspondientes, objetivo que el alumno seleccione el tema a repasar y no el bloque de leyes". Afecta a una pieza ya construida (progreso vivo por bloque), así que antes de tocar código se confirmaron 6 decisiones de diseño con el usuario (2 rondas de preguntas):
1. Alcance: el progreso vivo (fase, % acierto, "estudiado") pasa a trackearse por **tema**, no solo la selección de qué practicar.
2. Selector: Bloque → Tema en dos pasos, con opción "Todo el bloque" para mantener el comportamiento agregado.
3. Bloque "estudiado" (elegibilidad del simulacro personal) = todos sus temas con preguntas vistas alcanzan ≥70% individualmente (temas nunca practicados no cuentan en contra).
4. Fase del mix adaptativo por tema = número de preguntas vistas **en ese tema** (ya no "cobertura de épigrafes del bloque", que deja de tener sentido cuando el tema ya es la unidad): inicio 0-4, aprendizaje 5-14, consolidación 15-29, pre-examen 30+.
5. Temas con 0 preguntas en el banco (6 de 58 hoy): sin distinción visual en el selector — la creación del banco por tema es un trabajo posterior y separado, no bloquea este rediseño.

- [✅ Migración 034, `sql/ddl/034_plan_estudio_por_tema.sql`] `normas.plan_estudio` pasa de `UNIQUE(user_id, oposicion_id, bloque)` a `UNIQUE(user_id, oposicion_id, epigrafe_id)` (columna `epigrafe_id` NOT NULL, FK a `normas.epigrafes`); `bloque` queda como columna denormalizada (se recalcula en cada UPSERT). Las filas antiguas (a nivel de bloque, sin epígrafe) se borraron por ser regenerables — no hay pérdida real de datos, el histórico vive en `progreso_usuario`. Aplicada en Supabase vía Session Pooler; incluía datos de la propia cuenta del usuario (`indalecioplaza@outlook.com`, 6 filas), que se recalculan solas la próxima vez que practique.
- [✅ `retrieval.py`] `get_fase_alumno(user_id, oposicion_id, epigrafe_id)` (antes recibía `bloque`): UPSERT por tema, fase por `_fase_por_vistas` (antes `_fase_por_cobertura`). `get_stats_alumno` reescrita: una fila por tema (LEFT JOIN `epigrafes`↔`plan_estudio`, así que salen también los temas sin practicar) agrupada en `bloques[].temas[]`; el bloque agregado (`porcentaje_acierto`, `estudiado`) se calcula sumando/derivando de sus temas. `proxima_accion` ahora recomienda un **tema** concreto (`tipo: practicar_tema`, con `epigrafe_id`), no un bloque genérico. `get_preguntas_adaptativo(bloque)` (modo "Todo el bloque") usa la fase agregada nueva `_fase_bloque` (media de vistas por tema); `get_preguntas_adaptativo_tema(epigrafe_id)` es la versión nueva acotada a un tema, con sus propios `_fetch_debiles_tema`/`_fetch_por_fuente_tema`. `get_temas_por_bloque(oposicion_id, bloque)` nueva, para el selector. `get_preguntas_simulacro_personal` ya no lee una fila de `plan_estudio` por bloque (ya no existe): deriva `bloques_estudiados`/`bloques_con_datos` llamando a `get_stats_alumno`. `_COLUMNAS_PREGUNTA` ahora incluye `pt.epigrafe_id`, para que la UI sepa qué tema actualizar tras cada tanda.
- [✅ `streamlit_app.py`] `_modo_repaso`: selector "Bloque" (igual que antes) + nuevo selector "Tema" (temas del bloque elegido + "Todo el bloque"), con `session_state` por bloque (`repaso_tema_<bloque>`) para no perder la elección al cambiar de bloque. Al comprobar respuestas, se llama a `get_fase_alumno` una vez por cada tema realmente tocado en la tanda (funciona igual para "un tema" que para "todo el bloque", que puede tocar varios). Momento 3 (resultado) muestra el % del bloque y, si se practicó un tema concreto, también el % de ese tema. `_panel_estado_bloques` ahora lista los temas de cada bloque con su marca (✅ estudiado / · en progreso / — sin practicar) y %, en vez de solo el agregado del bloque. `_modo_prueba_nivel` actualiza `plan_estudio` por cada tema tocado por sus 40 preguntas (antes iteraba los 6 bloques enteros); su informe de partida ya no menciona la fase (corrige además una inconsistencia con la regla del Paso 7, que prohíbe mostrar la fase al alumno y que el informe de partida no cumplía).
- [ℹ️ Bug preexistente corregido, no relacionado con el rediseño] El botón "Ir a Repaso →" de la prueba de nivel reasignaba `st.session_state.modo_alumno_radio` **después** de que el widget `st.radio` con esa misma key ya se hubiera instanciado en la misma ejecución — `StreamlitAPIException` en versiones recientes de Streamlit (1.58, la instalada aquí). Corregido con el patrón estándar: la asignación pasa por una clave intermedia (`_forzar_modo_alumno`) que se consume **antes** de crear el widget, al principio de `_flujo_alumno`.
- [✅ Verificado en vivo, navegador real] Playwright headless contra Supabase real vía Session Pooler (mismo rodeo de entorno que en el Paso 9: sin salida IPv6 al host directo, hay que apuntar `.streamlit/secrets.toml` al pooler temporalmente). Flujo completo: alumno de prueba → prueba de nivel (40 preguntas) → informe de partida sin mostrar fase → "Ir a Repaso →" (bug de navegación ya corregido) → panel "Tu estado actual por bloque y tema" con los temas oficiales listados dentro de cada bloque y su % individual → selector Bloque "I — Organización del Estado" + Tema "Tema 1: La Constitución Española..." → tanda de 4 preguntas (banco pequeño en ese tema, esperable) todas efectivamente del Tema I.1 → "Comprobar respuestas" → resultado con el % del bloque y del tema por separado. Sin errores de consola. Datos de prueba (`plan_estudio`, `progreso_usuario`) borrados tras la verificación; el usuario `alumno.prueba.claude.temas@example.com` queda en Supabase Auth pendiente de limpieza manual (mismo caso que en pasos anteriores, no borrable con la clave anon).
- [ℹ️ Pendiente, fuera de alcance de este cambio] Construir el banco de preguntas por tema a escala (hoy 6 de 58 temas no tienen ninguna pregunta, y la mayoría tiene muy pocas) — decisión explícita del usuario de abordarlo como trabajo separado, después de cerrar el diseño de la app.

### Completado — Paso 9: simulacro de academia (11/07/2026)
Decisiones de diseño confirmadas por el usuario antes de implementar: (1) la generación y autorización las dispara el editor/academia desde una nueva sección dentro de Administración (Google OAuth), no un script CLI; (2) un único intento por alumno y por simulacro; (3) el número de preguntas es configurable al generar (no fijo en 50).

- [✅ `retrieval.py`] `generar_simulacro_academia(oposicion_id, nombre, n, fecha_inicio, fecha_fin, academia=None)`: reparto proporcional por peso oficial (`oposicion_leyes.preguntas_simulacro`) entre **todos** los bloques de la oposición (a diferencia del simulacro personal, que solo usa bloques "estudiado" — aquí es el mismo examen para todos, sin personalización). Inserta en `simulacros_academia` (estado `generado`) + `simulacro_academia_preguntas` con el orden fijo ya barajado. `autorizar_simulacro_academia(simulacro_id, autorizado_por)` pasa a `autorizado`. `listar_simulacros_academia(oposicion_id)` para el panel de Administración. `get_simulacros_academia_disponibles(oposicion_id, user_id)` para el alumno: solo autorizados, dentro de ventana (`NOW() BETWEEN fecha_inicio AND fecha_fin`), marcando `ya_realizado` vía `EXISTS` contra `historial_simulacros` (así se aplica la regla de un único intento).
- [✅ `streamlit_app.py`, lado Administración] Nueva opción "Simulacros academia" en el radio `Modo` (junto a Q&A/Generar test/Editor): formulario para generar (nombre, número de preguntas, ventana fecha/hora inicio-fin) y listado de simulacros existentes con botón "Autorizar" para los que están en `generado`. La academia nunca elige preguntas — solo genera (reparto automático) y autoriza.
- [✅ `streamlit_app.py`, lado Alumno] Nueva opción "Simulacro academia" en el radio de modos (`_modo_simulacro_academia`): lista los simulacros autorizados y abiertos ahora mismo que el alumno no haya hecho ya; al elegir uno, mismo patrón de preguntas/corrección que el simulacro personal, pero califica con `tipo="academia"` y `simulacro_academia_id`. Sin botón de "nuevo intento" — una vez respondido y guardado, no se puede repetir (ni siquiera reabriendo sesión: `get_simulacros_academia_disponibles` ya lo excluye por `ya_realizado`).
- [✅ `_modo_mi_progreso`] Ya soportaba genéricamente `tipo='academia'` desde el Paso 8 (etiqueta "Academia"); sin cambios necesarios.
- [ℹ️ Bug preexistente corregido de paso, no relacionado con Paso 9] `st.caption(f"Sesión activa: {user["email"]}")` en el modo Editor usaba comillas dobles anidadas en una f-string, sintaxis válida solo en Python 3.12+ (PEP 701); rompía la compilación en este entorno de desarrollo (Python 3.11). Corregido a comillas simples internas (`user['email']`) — compatible con cualquier versión.
- [✅ Verificado en vivo, navegador real] Playwright headless contra Supabase real vía Session Pooler (este devcontainer no tiene salida IPv6 al host directo `db.<ref>.supabase.co`; hubo que enrutar por el pooler para las pruebas — ver nota de entorno más abajo). No se pudo probar el botón "Generar"/"Autorizar" de Administración por clic real (requiere login Google), así que esa parte se validó llamando directamente a `generar_simulacro_academia`/`autorizar_simulacro_academia`/`listar_simulacros_academia` contra la BD real, confirmando que crean/actualizan las filas correctas. El lado alumno sí se probó de principio a fin con navegador real: login → "Simulacro academia" → simulacro de prueba visible → responder → "Comprobar respuestas" → nota calificada y guardada → aparece en "Mi progreso" como "Academia" → recargando sesión desde cero, el mismo simulacro ya no aparece disponible ("Ya has realizado todos los simulacros de academia disponibles ahora mismo"). Sin errores de consola. Datos de prueba (`historial_simulacros`, `simulacro_academia_preguntas`, `simulacros_academia`) borrados tras la verificación; el usuario `alumno.prueba.claude.paso9@example.com` queda en Supabase Auth pendiente de limpieza manual (mismo caso que en Pasos 6-8, no borrable con la clave anon).
- [ℹ️ Nota de entorno, no específica de Paso 9] Este devcontainer no resuelve el host directo de Postgres por IPv6; para pruebas locales de la app (no solo scripts) hay que apuntar `.streamlit/secrets.toml` al Session Pooler (`aws-1-eu-west-2.pooler.supabase.com` / usuario `postgres.<ref>`) temporalmente — Streamlit vuelca `st.secrets` a variables de entorno al arrancar, así que exportar `DB_HOST`/`DB_USER` por shell no basta, hay que editar el fichero. Restaurado el valor original al terminar.

### Completado — Paso 8: simulacro personal + historial (08/07/2026)
Amplía el alcance original (solo simulacro personal) a petición del usuario: el resultado no debe afectar al progreso de repaso, pero sí debe quedar histórico de notas de simulacro (personal y, más adelante, academia) para un informe general.

- [✅ Migración 033, `sql/ddl/033_historial_simulacros.sql`] Tabla `normas.historial_simulacros` (user_id, oposicion_id, tipo `personal`/`academia`, `simulacro_academia_id` nullable con FK a `simulacros_academia`, n_preguntas, aciertos, errores, blancos, nota, aprobado, realizado_en). Diseñada para que el Paso 9 escriba en la misma tabla sin cambios de esquema. Aplicada en Supabase vía Session Pooler.
- [✅ `retrieval.py`] `calificar_simulacro`: lee la convocatoria vigente (año más reciente) de `normas.convocatorias` y aplica su fórmula extrapolando aciertos/errores/blancos de n_preguntas al `num_preguntas` oficial (100), para que la nota quede en la escala real 0-50 comparable a `nota_minima`/`pct_aprobado` — decisión explícita del usuario frente a dejar la nota en una escala reducida a la mitad. `guardar_resultado_simulacro` inserta el intento en `historial_simulacros`. `get_historial_simulacros` lo lista para "Mi progreso".
- [✅ `streamlit_app.py`] Radio `¿Qué quieres hacer?` pasa a 4 opciones: Prueba de nivel / Repaso / **Simulacro personal** / **Mi progreso**.
  - `_modo_simulacro_personal`: 50 preguntas de `get_preguntas_simulacro_personal` (bloques ≥70%, ya construida en el Paso 5); bloquea con el motivo si falta prueba de nivel o no hay bloque estudiado. Al corregir, **no** llama a `update_progreso_sm2`/`get_fase_alumno` (simulacro aislado, decisión explícita del usuario) — solo calcula la nota y la guarda una vez (`session_state["guardado"]` evita duplicados en reruns).
  - `_modo_mi_progreso`: lista los intentos de `get_historial_simulacros` con fecha, tipo, nota y aprobado/no aprobado; la rama "Academia" queda sin datos hasta el Paso 9 pero el diseño ya la contempla.
  - Sin cronómetro en esta versión (decisión explícita del usuario, queda para una iteración posterior).
- [✅ Verificado en vivo, navegador real] Playwright headless contra Supabase real vía Session Pooler: (1) simulacro bloqueado antes de la prueba de nivel, mensaje correcto; (2) "Mi progreso" vacío con mensaje correcto; (3) con `plan_estudio` sembrado para simular un bloque estudiado, flujo completo del simulacro (18 preguntas disponibles en el bloque de prueba, no 50 — el reparto respeta lo que hay en banco) → nota extrapolada correcta (6 aciertos/12 fallos sobre 18 → nota 11,11, fórmula A−(E/3) verificada a mano) → intento guardado y visible en "Mi progreso" con dos intentos en orden descendente. Confirmado que `progreso_usuario` no recibe filas nuevas del simulacro (0 borrados en la limpieza, frente a las 6 filas de `plan_estudio` sembradas para la prueba). Sin errores de consola. Datos de prueba borrados tras la verificación.

### Completado — Paso 7: visualización de progreso (08/07/2026)
Diseño en 3 momentos, implementado en `_modo_repaso`/`_panel_estado_bloques` de `streamlit_app.py`, reutilizando `get_stats_alumno`/`get_preguntas_adaptativo` (sin migraciones nuevas):
1. **Panel de inicio** (al entrar en Repaso): expander "Tu estado actual por bloque" (expandido si no hay tanda en curso, colapsable después) con % de acierto y estado (estudiado/en progreso) por bloque, vía `get_stats_alumno`.
2. **Composición de la tanda** (antes de responder): mensaje genérico "🎯 Tanda personalizada según tu progreso en este bloque." — **sin desglose numérico ni categorías** (ver regla siguiente).
3. **Resultado** (al terminar): aciertos/fallos de la tanda + cómo queda el % de acierto del bloque (nueva llamada a `get_stats_alumno` tras `update_progreso_sm2`/`get_fase_alumno`).

**Regla de producto:** prohibido mostrar al alumno el desglose débiles/oficial/nueva o la fase (inicio/aprendizaje/consolidación/pre-examen) de una tanda — es dato reservado para el futuro análisis de la academia sobre sus alumnos (B2B), no para el alumno (B2C).

[✅ Verificado en vivo, navegador real] Playwright headless contra Supabase real vía Session Pooler: alumno de prueba registrado → Repaso → los 3 momentos renderizan con los datos reales (10,00% de acierto en el panel de inicio, mensaje genérico sin desglose en la composición de la tanda, resultado "2/10 correctas (8 fallos)" y bloque actualizado a 15,00% en el momento 3). Sin errores de consola. Datos de prueba (`progreso_usuario`/`plan_estudio`) borrados tras la verificación; el usuario `alumno.prueba.claude.paso7@example.com` eliminado de Supabase Auth el 09/07/2026 (limpieza manual completada junto con el Paso 6).

### Completado — Rediseño sidebar: bifurcación Acceso (08/07/2026)
- [✅ `streamlit_app.py`] Sidebar reestructurado: Oposición (primera selección, sin cambios) → **Acceso** (dos botones: Administración / Alumno) → cada camino despliega su flujo. Sin acceso anónimo: hasta elegir un tipo de acceso no se muestra ningún contenido.
  - **Administración** (Google OAuth): panel intermedio con botón "Iniciar sesión con Google" (no redirige automáticamente); una vez logueado, ve Editor + Q&A + Generar test, igual que antes.
  - **Alumno** (Supabase Auth): mismo flujo de siempre (login/registro → prueba de nivel/repaso).
  - Limpiados los condicionales `if logged_in` que quedaban muertos en "Generar test"/"Editor" (ese tramo del script ya solo se ejecuta con sesión Google activa) y el import sin uso de `get_preguntas_banco`.
  - Botones "Selecciona al menos un bloque"/"Selecciona al menos una ley" renombrados a "Seleccionar todo" (su acción real siempre fue marcar todos, el texto anterior confundía con el aviso de validación).
- [✅ Verificado] Playwright headless con la carga de oposiciones mockeada (este entorno de desarrollo no tiene salida IPv6 y no llega a Supabase directo ni al pooler): las 3 pantallas (inicio con bifurcación, Administración sin login, Alumno) renderizan correctamente sin errores de consola. **Pendiente probar con BD real y login Google/Supabase real** desde WSL2.

### Completado — Paso 6: navegación alumno + prueba de nivel (07/07/2026)
- [✅ `retrieval.get_preguntas_prueba_nivel`] Reparto proporcional por peso oficial entre los 6 bloques (todos, no solo "estudiado"), orden por dificultad creciente.
- [✅ `streamlit_app.py`] Cuando hay alumno logueado (Supabase Auth), flujo propio separado del editor: jerarquía Oposición → Modo (Prueba de nivel / Repaso) → Bloque → sesión. Onboarding de bienvenida para alumnos nuevos; mensajes de error claros en login/registro (email ya registrado, credenciales incorrectas, contraseña corta). El flujo Q&A/Generar test/Editor (Google OAuth) queda intacto.
- [✅ Verificado en vivo, navegador real] Playwright headless contra Supabase real vía Session Pooler: registro → prueba de nivel (40 preguntas reales) → corrección → informe de partida por bloque → cambio automático a "Repaso" → re-login detecta alumno no-nuevo y preselecciona Repaso con el bloque más débil → tanda adaptativa cargada. Sin errores de consola. Datos de prueba (`plan_estudio`/`progreso_usuario`) borrados tras la verificación.
- [✅ Limpieza manual completada (09/07/2026)] Los 3 usuarios de prueba (`alumno.prueba.claude.paso6*@example.com`) eliminados desde el dashboard de Supabase Auth; verificado por SQL que no quedaron filas huérfanas en `progreso_usuario`/`plan_estudio`/`historial_simulacros`.
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
