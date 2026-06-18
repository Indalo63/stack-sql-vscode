# Evaluación del Pipeline Q&A — Preguntas de Referencia

## Propósito

Verificar la calidad del pipeline Q&A antes de añadir capas nuevas (interfaz, exportación, etc.).

**Fecha de evaluación:** 2026-06-18
**Modelo de embeddings:** `text-embedding-3-small` (OpenAI, 1536 dims)
**Modelo de generación:** `claude-sonnet-4-6`
**TOP_K_ARTICLES:** 5
**Resultado global:** ✅ 13/13 — calidad alta en todas las preguntas

---

## Criterios de evaluación

| Criterio | Descripción |
|---|---|
| Artículos correctos | Los artículos citados son los que corresponden a la pregunta |
| Artículos completos | No faltan artículos relevantes importantes |
| Respuesta precisa | El contenido de la respuesta es jurídicamente correcto |
| Artículos extra | El sistema añade artículos relacionados útiles (bonus positivo) |

---

## Resultados por pregunta

### P01 — Libertad de expresión

**Pregunta:** ¿Qué derechos reconoce el artículo 20 de la Constitución?

| Artículos esperados | Artículos citados | Valoración |
|---|---|---|
| Art. 20 | Art. 20.1.a/b/c/d, 20.2, 20.4, 20.5, 53.2 | ✅ Excelente |

**Notas:** Cita correctamente los cuatro apartados del 20.1, los límites (20.4), la prohibición de censura previa (20.2) y el recurso de amparo (53.2). Respuesta completa.

---

### P02 — Lenguas oficiales

**Pregunta:** ¿Cuáles son las lenguas oficiales de España?

| Artículos esperados | Artículos citados | Valoración |
|---|---|---|
| Art. 3 | Art. 3.1, 3.2, 3.3, Preámbulo | ✅ Excelente |

**Notas:** Diferencia correctamente entre lengua oficial del Estado (castellano, Art. 3.1) y lenguas cooficiales autonómicas (Art. 3.2). Añade la protección del patrimonio lingüístico (Art. 3.3).

---

### P03 — Estado de alarma

**Pregunta:** ¿Cuándo puede el Gobierno declarar el estado de alarma?

| Artículos esperados | Artículos citados | Valoración |
|---|---|---|
| Art. 116.2 | Art. 116.1, 116.2, 116.5, 116.6 | ✅ Excelente |

**Notas:** Detalla los cinco requisitos del 116.2 (órgano, plazo, control, prórroga, territorio) y añade garantías del 116.5 (no disolución del Congreso) y 116.6 (responsabilidad del Gobierno).

---

### P04 — Mayoría de edad

**Pregunta:** ¿Cuál es la mayoría de edad en España según la Constitución?

| Artículos esperados | Artículos citados | Valoración |
|---|---|---|
| Art. 12 | Art. 12, Disposición Adicional Segunda | ✅ Excelente |

**Notas:** Respuesta directa y correcta (18 años). Bonus: identifica la Disposición Adicional Segunda sobre los derechos forales, dato que va más allá de lo esperado.

---

### P05 — Derecho a la huelga

**Pregunta:** ¿Qué dice la Constitución sobre el derecho a la huelga?

| Artículos esperados | Artículos citados | Valoración |
|---|---|---|
| Art. 28.2 | Art. 28.2, 55.1 | ✅ Excelente |

**Notas:** Explica el derecho, el límite de servicios esenciales y la posibilidad de suspensión en estados de excepción/sitio (Art. 55.1). Respuesta completa.

---

### P06 — Tutela judicial efectiva

**Pregunta:** ¿Qué garantiza el artículo 24 sobre la tutela judicial efectiva?

| Artículos esperados | Artículos citados | Valoración |
|---|---|---|
| Art. 24 | Art. 24.1, 24.2, 53.2 | ✅ Excelente |

**Notas:** Tabla clara con los siete derechos procesales del 24.2 (juez ordinario, defensa, información, proceso sin dilaciones, prueba, no autoincriminación, presunción de inocencia). Añade recurso de amparo (53.2).

---

### P07 — Pena de muerte

**Pregunta:** ¿Qué dice la Constitución sobre la pena de muerte?

| Artículos esperados | Artículos citados | Valoración |
|---|---|---|
| Art. 15 | Art. 15 | ✅ Correcto |

**Notas:** Correcta: abolición general + excepción leyes penales militares en tiempo de guerra. Respuesta precisa y completa.

---

### P08 — Derechos del detenido

**Pregunta:** ¿Qué derechos tiene una persona detenida?

| Artículos esperados | Artículos citados | Valoración |
|---|---|---|
| Art. 17 | Art. 17.2, 17.3, 17.4, 15, 24, 55.1 | ✅ Excelente |

**Notas:** Cinco derechos del Art. 17 correctamente detallados. Añade Arts. 15 y 24 como derechos complementarios aplicables. Menciona la suspensión en estados de excepción/sitio (55.1).

---

### P09 — Forma de gobierno

**Pregunta:** ¿Cuál es la forma de gobierno de España?

| Artículos esperados | Artículos citados | Valoración |
|---|---|---|
| Art. 1.3 | Art. 1.2, 1.3, 56.1, 62 | ✅ Excelente |

**Notas:** Identifica correctamente la Monarquía parlamentaria (1.3), añade la soberanía popular (1.2), el rol del Rey como Jefe de Estado (56.1) y sus competencias (62).

---

### P10 — Tribunal Constitucional

**Pregunta:** ¿Cómo se compone el Tribunal Constitucional?

| Artículos esperados | Artículos citados | Valoración |
|---|---|---|
| Art. 159 | Art. 159.1, 159.2, 159.3, 160 | ✅ Excelente |

**Notas:** Tabla precisa con los 12 miembros, su distribución por órgano proponente y mayorías requeridas. Detalla requisitos (159.2), mandato de nueve años con renovación por tercios (159.3) y presidencia (160).

---

### P11 — Reforma constitucional

**Pregunta:** ¿Cómo se puede reformar la Constitución?

| Artículos esperados | Artículos citados | Valoración |
|---|---|---|
| Art. 167, 168 | Art. 166, 167, 168, 169 | ✅ Excelente |

**Notas:** Diferencia correctamente los dos procedimientos (ordinario/agravado), las materias que activan cada uno, los pasos completos del procedimiento agravado, la limitación temporal (169) y la iniciativa (166).

---

### P12 — Derecho a la educación

**Pregunta:** ¿Qué dice la Constitución sobre el derecho a la educación?

| Artículos esperados | Artículos citados | Valoración |
|---|---|---|
| Art. 27 | Art. 27.1–10, 53.1 | ✅ Excelente |

**Notas:** Cubre todos los aspectos del Art. 27: reconocimiento, objetivos, obligatoriedad y gratuidad, libertad de creación de centros, autonomía universitaria y obligaciones de los poderes públicos.

---

### P13 — Propiedad privada

**Pregunta:** ¿Qué dice la Constitución sobre la propiedad privada?

| Artículos esperados | Artículos citados | Valoración |
|---|---|---|
| Art. 33 | Art. 33.1, 33.2, 33.3, 128.1, 18.2 | ✅ Excelente |

**Notas:** Reconocimiento, función social, garantías frente a la privación (expropiación forzosa: causa + indemnización + ley). Añade subordinación al interés general (128.1) e inviolabilidad del domicilio (18.2).

---

## Conclusiones

### Fortalezas del pipeline

- **Precisión en recuperación semántica**: en todas las preguntas se recuperaron los artículos correctos.
- **Enriquecimiento contextual**: el sistema añade sistemáticamente artículos relacionados relevantes (Arts. 53, 55, 116…) que completan la respuesta sin alejarse del texto constitucional.
- **Formato de salida**: las respuestas están bien estructuradas (tablas, listas, citas textuales), lo que facilita su lectura y verificación.
- **Rigor jurídico**: no se detectaron afirmaciones incorrectas en ninguna de las 13 preguntas.

### Ajustes valorados

- `TOP_K_ARTICLES = 5` es adecuado. Aumentarlo no parece necesario.
- El prompt del sistema (rol de asistente jurídico + instrucción de citar artículos) produce resultados consistentes.

### Decisión

> El pipeline Q&A está listo para añadir una interfaz de usuario. **Hito 1 completado.**
