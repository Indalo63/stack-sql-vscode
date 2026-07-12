# MVP — datos de prueba y cómo eliminarlos

> ## ⚠️ LEE ESTO PRIMERO
>
> Para validar el motor de aprendizaje con 2 alumnos de prueba hubo que **aprobar
> preguntas sin revisión humana real**. Eso **degrada la lógica de negocio**: el banco
> revisado *es* el producto, y lo que nos separa de la competencia es que un humano lo valida.
>
> **Todo lo que se hizo así está marcado y es reversible con un solo comando.**
> **NADA de esto puede llegar a un alumno de pago.**

---

## Qué se creó (y cómo se identifica)

| Qué | Cuánto | Marca que lo identifica |
|---|---|---|
| Preguntas aprobadas **sin revisión real** | 88 | `preguntas_test.es_prueba = TRUE` · `revisado_por = 'PRUEBA_MVP'` |
| Alumnos de prueba | 2 | `alumno.mvp.uno@example.com`, `alumno.mvp.dos@example.com` (contraseña: `PruebaMVP2026!`) |

**El banco real no se ha tocado:** las 209 preguntas de exámenes oficiales siguen siendo las
únicas revisadas de verdad. Están separadas por la marca `es_prueba`.

```sql
-- Ver la separación en cualquier momento
SELECT es_prueba, COUNT(*) FROM normas.preguntas_test WHERE revisada GROUP BY es_prueba;
--  false | 209   <- banco REAL
--  true  |  88   <- banco de PRUEBA (reversible)
```

## Cómo se borra TODO

```bash
python3 scripts/limpiar_datos_prueba.py --supabase --dry-run   # ver qué haría
python3 scripts/limpiar_datos_prueba.py --supabase             # hacerlo
```

Qué hace:
- Las 88 preguntas **vuelven a "pendiente de revisión"** (no se borran: el trabajo de
  generación se conserva y podrá revisarse de verdad cuando toque).
- Borra el progreso de los alumnos de prueba (`progreso_usuario`, `plan_estudio`,
  `historial_simulacros`).

**Lo único que NO puede hacer:** borrar las cuentas de los alumnos de Supabase Auth (la clave
`anon` no lo permite). Hay que eliminarlas a mano en **Authentication → Users**. El script te lo
recuerda al terminar.

---

## Bug grave encontrado al preparar el MVP (ya corregido)

**Los bloques II (Unión Europea) y III (Políticas Públicas) tenían peso 0**, y la suma de todos
los pesos era **51, no 100**. Efecto en cadena:

1. La prueba de nivel reparte proporcionalmente al peso → **nunca servía preguntas de II ni III**.
2. El simulacro personal exige tener datos en **los 6 bloques**.
3. → **El simulacro personal quedaba bloqueado para siempre.** Los 2 alumnos jamás habrían
   podido hacerlo.

**Corregido en la migración 042.** Los pesos nuevos **no están inventados**: salen del reparto
real de los exámenes oficiales GACE 2024 y 2025 que ya teníamos cargados.

**Método (determinista, sin IA):** los exámenes **están ordenados por bloque** (I → II → III →
IV → V → VI, igual que el programa), así que el bloque de las preguntas sin ley asignada
(actualidad y normas no cargadas) se deduce **por su posición** entre preguntas ya clasificadas.

Esto corrigió un sesgo real: el cálculo ingenuo (contando solo preguntas con ley asignada)
**infravalora a los bloques II y III**, precisamente porque su contenido apunta a normas que no
tenemos cargadas.

| Bloque | Preguntas | % examen | Peso |
|---|---|---|---|
| I | 42 | 21,4% | 21 |
| II | 23 | 11,7% | 12 |
| III | 21 | 10,7% | 11 |
| IV | 39 | 19,9% | 20 |
| V | 42 | 21,4% | 21 |
| VI | 29 | 14,8% | 15 |
| | | | **100** |

---

## Qué quedó validado (probado contra la BD real)

| Mecanismo | Resultado |
|---|---|
| **Prueba de nivel** | ✅ 40 preguntas, cubre **los 6 bloques** (antes solo 4) |
| **Las 4 fases del mix adaptativo** | ✅ inicio → aprendizaje → consolidación → **pre-examen**, todas alcanzables |
| **Mix con una categoría agotada** | ✅ **No se rompe**: reparte con lo que hay |
| **Bloque "estudiado" (≥70% por tema)** | ✅ Funciona, y es **exigente**: un solo tema flojo bloquea el bloque entero |
| **Simulacro personal** | ✅ 50 preguntas, fórmula oficial A−(E/3), escala 0-50 |
| **Mi progreso** | ✅ Guarda e historia los intentos |

**Descubrimiento útil:** el motor cuenta **respuestas**, no preguntas distintas. Como el SM-2
vuelve a servir las falladas, **25 preguntas en un tema bastan** para recorrer las 4 fases — no
hacen falta 30+ preguntas distintas, como se estimó al principio.

### Un comportamiento que conviene conocer antes de que lo sufran los alumnos

La regla "bloque estudiado = **todos** sus temas ≥70%" es **muy estricta**: en la simulación, un
tema con solo **2 preguntas vistas y 0% de acierto** bloqueaba el bloque entero, aunque el bloque
iba al 78% global. Es el diseño acordado y funciona, pero conviene saberlo: **un golpe de mala
suerte en un tema pequeño puede frustrar al alumno**. Se arregla practicando ese tema.

---

## Estado del banco

| | Preguntas |
|---|---|
| Banco REAL (exámenes oficiales, revisados) | 209 |
| Banco de PRUEBA (`es_prueba = TRUE`) | 88 |
| **Alcanzables por el alumno** | **243** |

*(Las 209 no suman con las 88 en "alcanzables" porque 52 preguntas oficiales no tienen ley
asignada — actualidad y normas no cargadas — y el motor no las sirve.)*
