# Pendientes — checklist de control de avance

> **Qué es esto:** lista única de todo lo que consta como **sin empezar** en `CLAUDE.md`/`TODO.md`
> a fecha 18/07/2026, con checklist para marcar avance. No sustituye a `TODO.md` (el backlog
> narrativo, con el porqué de cada cosa) ni a `CLAUDE.md` (el estado del proyecto) — es un
> resumen operativo derivado de ambos. Si marcas algo aquí, actualiza también su sección de
> origen en `TODO.md`/`CLAUDE.md` para que no se desincronicen.

---

## 🔴 Seguridad / operativo

- [ ] Cambiar producción al rol de permisos mínimos `app_asistente` (ya creado y probado en
      local, migración 040): generar/recuperar su contraseña y actualizar `DB_USER`/`DB_PASSWORD`
      en los Secrets de Streamlit Cloud. Detalle: `docs/cambiar-usuario-bd-produccion.md`.
- [ ] Rotar la contraseña de Postgres de Supabase (quedó expuesta en un chat el 09/07/2026; ya
      hay una nueva generada desde el Dashboard, pendiente de aplicar en `secrets.toml` y en
      Streamlit Cloud sin romper la conexión activa). Antes de dar acceso a alumnos reales.
- [ ] Confirmar en los Secrets de Streamlit Cloud (producción) que `SUPABASE_URL`/
      `SUPABASE_ANON_KEY` están antes de `[auth.google]` (el mismo bug de orden TOML que se
      corrigió en local).

## ⚖️ Requiere criterio jurídico (no lo decide el código)

- [ ] **RRCP**: decidir qué norma citar — `url_boe` apunta a un decreto *modificador*
      (RD 2073/1999), no al reglamento en sí — y corregir `url_boe` + `nombre_oficial` +
      `numero_oficial`.
- [ ] **BCPSA**: resolver la contradicción entre `url_boe` (Orden HFP/688/2017) y
      `numero_oficial` (RD 364/2017), y alinear los tres campos.

## 🔍 Auditoría externa

- [ ] Auditar la pantalla de consentimiento OAuth en Google Cloud Console: modo *Testing* vs
      *In production*, tipo de usuario (*External*/*Internal*), URIs de redirección de
      producción, estado de verificación de scopes.

## 🎯 Hito "Mejoras del perfil alumno" (5 fases)

- [ ] **Fase 1 — Confianza**: puerta anti-alucinación en el generador (que `_parse_and_validate()`
      compruebe que el artículo citado es el artículo fuente) + mostrar el artículo del BOE al
      corregir una respuesta.
- [ ] **Fase 2 — Corrección diagnóstica**: por qué falló el alumno, no solo cuál era la opción
      correcta (segunda llamada al modelo con artículo + pregunta + opción elegida + correcta).
- [ ] **Fase 3 — Explotar lo que ya hay**: Radar del Tribunal por tema (`GROUP BY` sobre las 157
      preguntas oficiales ya clasificadas) + dar el Q&A semántico al alumno (hoy solo lo usan
      editores; ningún competidor lo tiene).
- [ ] **Fase 4 — Informe para el preparador** (venta B2B): requiere vínculo alumno↔academia, que
      hoy no existe. Mucho diseño previo.
- [ ] **Fase 5 — Retención**: rachas/constancia (B2C) + "¿estoy listo para el examen?" a partir
      del % por tema y el peso oficial.

## 🧭 Rediseño navegación "Gestión banco de preguntas" — fases siguientes

- [ ] **Actualización Legislación**: submodo automático (revisa cambios del BOE) y manual (el
      editor lo dispara), ambos con pantalla de aprobación antes de aplicar a la BD (mismo
      espíritu que la revisión de preguntas). Hoy solo existe `scripts/sync_boe.py` (CLI, sin UI).
- [ ] **Generador de test de prueba** (por tema completo / por ley): simulacro de prueba para que
      el editor pruebe la experiencia del alumno. Distinto del "Generar test" actual (repaso SM-2
      del editor).
- [ ] **Reubicar "Simulacros academia"** en el árbol de navegación (vía para academias gestionadas
      por una sola persona) — pendiente de concretar dónde cuelga.
- [ ] **Panel de progreso de revisión**: ajustes pendientes de concretar con el usuario.

## 📊 Pantalla de gestión de alumnos

- [ ] Decidir alcance: **A) solo lectura** sobre tablas ya existentes (`progreso_usuario`,
      `plan_estudio`, `historial_simulacros`) — recomendado para empezar; o **B) gestión
      completa** (baja, reset contraseña) — requiere `service_role` en secrets + modelo
      multi-academia.
- [ ] Implementar la opción elegida.

## 🪫 Baja prioridad, aparcado

- [ ] Cargar **LCCU** (necesita parser específico distinto de `parse_boe.py`).
- [ ] Cargar **PGCP** (idem).
- [ ] Limpiar artefactos OCR en `normas.articulos` de GACE_NORM.

---

## ⏳ Bloqueado por falta de escala — no accionable aún

Todo lo de aquí abajo **está construido y funcionando**, pero calibrado con conjeturas: no es
trabajo pendiente de programar, es esperar a que haya volumen real de alumnos/respuestas. No
tiene sentido marcarlo como "hecho" hasta que el disparador de cada uno se cumpla — y tampoco
tiene sentido empezarlo antes, porque el resultado sería ruido, no señal (el mismo error que ya
se cometió una vez con la dificultad heurística sin validar).

- [ ] **Validar la dificultad heurística contra la empírica.** Ejecutar periódicamente
      `python3 scripts/calcular_dificultad.py --supabase --solo-empirica` y comparar ambas en las
      preguntas que tengan las dos. Si no correlacionan, la heurística es ruido y hay que tirarla.
      Disparador: preguntas acumulando `min_respuestas_dificultad` (20) respuestas reales.
- [ ] **Recalibrar los 5 parámetros de `parametros_aprendizaje`** (muestra_minima, umbral_dominio,
      repeticiones_ok, cobertura_bloque, min_respuestas_dificultad) con datos de uso real.
- [ ] **Ritmo por bloque y por tema** (`retrieval.get_ritmo_por_bloque()`, TODO.md § 3.bis).
      Disparador: 4-6 simulacros cronometrados por alumno (~200-300 respuestas con
      `segundos IS NOT NULL`).
- [ ] **Rachas y constancia** (Fase 5.1 de arriba, en cuanto haya datos que agregar — hoy no se
      guarda ningún registro diario).
- [ ] **"¿Estoy listo para el examen?"** (Fase 5.2) — necesita que el SM-2 acumule `intervalo` y
      `proxima_revision` durante semanas.
- [ ] **Informe para el preparador con datos reales** (Fase 4) — vacío sin alumnos con recorrido.
- [ ] Revisar si la regla de dominio de un tema **frustra** al alumno en la práctica (un bloque
      que no se da por estudiado pese a ir bien).
