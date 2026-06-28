# CLAUDE.md – Proyecto Stack SQL + VS Code + PostgreSQL

## Quién soy
Soy Indalecio Plaza, consultor y formador técnico en bases de datos relacionales (PostgreSQL), desarrollo web y automatización con IA.

## Objetivo de este proyecto
Construir y documentar un stack de trabajo para SQL y aplicaciones de IA que combina:

- Windows + WSL2 (Ubuntu) + VS Code + Git
- PostgreSQL 16 + pgvector en Docker
- Python (pipeline Q&A jurídico + generación de tests)
- Claude (Anthropic API) como motor de generación
- OpenAI API para embeddings semánticos
- Claude Code como copiloto técnico y documental

El proyecto incluye una aplicación de Q&A jurídico sobre la Constitución Española: el usuario pregunta en lenguaje natural y el sistema recupera artículos relevantes mediante búsqueda semántica (pgvector) y genera una respuesta fundamentada usando Claude.

La guía debe ser reutilizable para alumnos en prácticas y para mí mismo.

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
- Docker Desktop con integración WSL2 operativo.
- Python 3 disponible en WSL2.
- Variables de entorno `OPENAI_API_KEY` y `ANTHROPIC_API_KEY` configuradas en `.env`.

## Convenciones iniciales
- Toda la documentación del stack vive en docs/.
- El archivo principal de guía es docs/stack-sql-vscode.md.
- Usar Markdown para cualquier guía o checklist.
- Cuando se propongan nuevos archivos, ubicarlos dentro de este repo respetando la estructura existente.

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

**Pendientes de carga** (48 leyes inventariadas, 42 pendientes — ver análisis BOE-443):
- ALTA prioridad: LODP, LOTC, LGOB, LOPJ, LOCE, LBRL, LTBG, LOPD, LOEPSF, TUE, TFUE
- Estrategia: ley por ley con `url_boe` individual (compatible con `sync_boe.py` y multi-oposición)
- Fuente principal: `BOE-443_Normativa_para_ingreso...06_2026.pdf` (3.792 págs, actualizado 24/06/2026)
- TUE/TFUE: desde EUR-Lex (no incluido en BOE-443)

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
- Migraciones ejecutadas: `020`, `021`, `022`

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
- [FASE 1] Cargar 8 leyes ALTA prioridad del BOE-443: LODP, LOTC, LGOB, LOCE, LBRL, LTBG, LOPD, LOEPSF
- [FASE 2] Cargar LOPJ, LGSS, Ley Tasas, Ley Tributaria
- [FASE 3] Cargar TUE + TFUE desde EUR-Lex (~10 preguntas fijas por examen)
- [FASE 4] Completar leyes de prioridad MEDIA (LJCA, LEF, Mutualismo, Indemnizaciones…)

### Hitos pendientes
- Mejorar generador IA con few-shot examples de exámenes oficiales (mejor calidad)
- Generar banco IA: `build_test_bank.py --supabase --n 50` (~300 preguntas, ~3€)
- Simulacro: 100 preguntas, temporizador, puntuación A-(E/3), escala 0-50 pts (Hito 4)
- Interfaz de revisión: tab "Revisión" para aprobar/rechazar preguntas IA
- Historial de conversación en Q&A (multi-turno con st.session_state)
- Exportar banco a CSV / Moodle XML (Hito 3)
- Sincronización automática BOE mediante GitHub Actions (Hito 5)
