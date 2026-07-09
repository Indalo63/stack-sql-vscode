# Lógica de negocio

_Última actualización: 2026-07-09_

Resumen consolidado de las reglas de negocio, producto y arquitectura de la plataforma hasta el Paso 8 del hito "App del alumno" (Paso 9 pendiente). Oposición de referencia: **GACE** (Cuerpo General Administrativo del Estado).

## 1. Objetivo y modelo de negocio

Plataforma modular, configurable sin tocar código: normativa, formato de examen, fórmula de corrección y tipos de ejercicio viven en base de datos, nunca hardcodeados.

| Línea | Horizonte | Descripción |
|---|---|---|
| **B2B — Academias y preparadores** | Primer cliente de pago, 3-6 meses | Streamlit como herramienta interna del equipo de la academia (generar, revisar, exportar preguntas). El banco aprobado se exporta a su LMS (Moodle XML / CSV). La academia gestiona a sus propios alumnos. |
| **B2C — Plataforma para el opositor** | Segunda línea, 6-12 meses | El opositor se suscribe directamente. La plataforma gestiona usuarios, simulacros, estadísticas y seguimiento. Requerirá frontend dedicado (FastAPI + React/Vue) sobre el mismo backend IA. |

**Perfiles de usuario:**

| Perfil | Auth | Función |
|---|---|---|
| Editor / revisor (academia) | Google OAuth | Genera preguntas por ley, las revisa y exporta |
| Alumno / opositor | Supabase Auth (email+contraseña) | Repaso adaptativo, simulacro personal, prueba de nivel |
| Administrador de plataforma | — | Gestiona leyes, convocatorias y fórmula desde BD |

## 2. Reglas obligatorias de generación de preguntas

Innegociables, derivadas del análisis del examen oficial GACE 2025. Se aplican siempre en `app/test_pipeline.py` y en cualquier generador futuro.

1. **Sin símbolos matemáticos.** Ni en preguntas, opciones o explicaciones: nada de =, >, <, %, +, ×, ÷, fracciones. Se escribe "igual a", "mayor que", "porcentaje".
2. **El enunciado cita la norma completa.** Siempre "Según el artículo [N] de [nombre completo de la ley],". Nunca se omite el nombre completo.
3. **Opciones en minúsculas a/b/c/d.** Nunca en mayúsculas.
4. **Distractores de alta precisión.** Difieren de la correcta solo en un dato exacto (plazo, porcentaje, órgano, palabra clave). Prohibidos los distractores conceptualmente distintos.
5. **Dificultad alta.** Se pregunta por datos exactos del artículo, no por conceptos generales — estilo GACE.

## 3. Fórmula de corrección y convocatoria

Vive en `normas.convocatorias`, no en código — se lee la convocatoria vigente (año más reciente).

```
Nota = A − (E / 3)
```

- 100 preguntas oficiales, 90 minutos
- Mínimo 25/50 para aprobar
- Escala 0–50

**Extrapolación en simulacros reducidos:** cuando el simulacro tiene menos preguntas que las 100 oficiales, se extrapolan aciertos/errores/blancos proporcionalmente antes de aplicar la fórmula, para que la nota quede en la escala real 0–50 comparable a `nota_minima` / `pct_aprobado`.

## 4. Arquitectura de la app del alumno

Diseño en 9 pasos aprobado el 05/07/2026. Jerarquía de navegación:

```
Oposición → Acceso (Administración / Alumno) → Modo (Repaso / Simulacro) → Bloque o Tema → Sesión
```

- **Prueba de nivel:** 40 preguntas, dificultad creciente individual. Gratuita con registro. Genera informe de partida por bloque + plan de estudio inicial.
- **Bloque "estudiado":** se marca cuando el acierto agregado del bloque alcanza o supera el **70%**. Condición para desbloquear el simulacro personal.

**Mix adaptativo — 4 fases según cobertura de epígrafes del bloque:**

| Fase | Débiles | Oficial | Nueva |
|---|---|---|---|
| Inicio | 0% | 40% | 60% |
| Aprendizaje | 15% | 20% | 65% |
| Consolidación | 30% | 25% | 45% |
| Pre-examen | 40% | 35% | 25% |

**Simulacro personal vs. simulacro de academia:**

| | Simulacro personal | Simulacro de academia |
|---|---|---|
| Preguntas | 50, de bloques con ≥70% de acierto | Mismas preguntas para todos los alumnos |
| Requisito | Prueba de nivel previa | Ventana temporal fija |
| Personalización | Sí | No |
| Fórmula | Oficial, extrapolada | Oficial, extrapolada |
| Efecto en SM-2 | Ninguno (aislado del repaso) | Ninguno |
| Flujo de generación | — | La academia autoriza, nunca genera |
| Estado | ✅ Completado (Paso 8) | ⏭️ Siguiente (Paso 9) |
| Cronómetro | No (por ahora) | — |

**Progreso e histórico — visualización en 3 momentos (repaso):**

1. **Panel de inicio:** % de acierto y estado por bloque.
2. **Composición de la tanda:** mensaje genérico, sin desglose numérico.
3. **Resultado:** aciertos/fallos de la tanda y % de acierto actualizado del bloque.

Cada intento de simulacro (personal o academia) queda registrado en `normas.historial_simulacros`, visible en "Mi progreso".

## 5. Reglas de producto (no derivables del código)

- **El desglose débiles/oficial/nueva y la fase nunca se muestran al alumno.** Son datos reservados para el futuro análisis de la academia sobre sus alumnos (B2B), no para el opositor (B2C).
- **El simulacro personal es aislado del repaso.** No llama a `update_progreso_sm2` ni a `get_fase_alumno`, pero cada intento queda en el histórico general de "Mi progreso".
- **Sin acceso anónimo.** Hasta elegir un tipo de acceso (Administración o Alumno) no se muestra ningún contenido.

## 6. Estado de implementación — los 9 pasos

| Paso | Tarea | Estado |
|---|---|---|
| 1 | Migración 030: dificultad + tabla epígrafes | ✅ Completado |
| 2 | Migración 031: tabla plan_estudio | ✅ Completado |
| 3 | Migración 032: tabla simulacros_academia | ✅ Completado |
| 4 | Supabase Auth: registro alumno | ✅ Completado |
| 5 | retrieval.py: stats, fase, mix adaptativo | ✅ Completado |
| 6 | streamlit_app.py: navegación + prueba de nivel | ✅ Completado |
| 7 | Visualización de progreso (3 momentos) | ✅ Completado |
| 8 | Simulacro personal + historial | ✅ Completado |
| 9 | Simulacro de academia | ⏭️ Siguiente |

## 7. Datos cargados a día de hoy

| Métrica | Valor |
|---|---|
| Normas cargadas (con embeddings) | 60 |
| Preguntas oficiales revisadas | 209 (104 GACE 2024 + 105 GACE 2025) |
| Preguntas con ley + epígrafe identificados | 76% |
| Cobertura BOE-443 del examen real | 76,6% |

El resto de la cobertura del examen real corresponde a TUE/TFUE (9,6% fijo), actualidad impredecible (5,7%) y leyes fuera del BOE-443 (6,7%).

---

**Próximo paso pendiente de confirmación:** Paso 9 — Simulacro de academia (preguntas fijas por ventana temporal, autorizadas, nunca generadas por la academia).
