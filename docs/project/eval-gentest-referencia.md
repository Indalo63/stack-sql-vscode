# Evaluación del Generador de Tests — Preguntas de Referencia

## Propósito

Verificar la calidad de las preguntas tipo test generadas por `gentest.py` antes de añadir
exportación a CSV/Moodle u otras capas adicionales.

**Fecha de evaluación:** 2026-06-18
**Modelo de generación:** `claude-sonnet-4-6`
**Artículos evaluados:** 14, 33, 34, 55, 87, 145, 155, 169
**Resultado global:** ✅ 8/8 — calidad alta, sin símbolos matemáticos

---

## Criterios de evaluación

| Criterio | Descripción |
|---|---|
| **Pregunta clara** | Se entiende sin necesidad de leer el artículo completo |
| **Opción correcta** | La respuesta marcada es correcta según el texto literal de la CE |
| **Distractores plausibles** | Las opciones incorrectas son razonables, no absurdas ni triviales |
| **Sin ambigüedad** | Solo una opción puede considerarse correcta |
| **Explicación útil** | Aporta contexto jurídico más allá de repetir la pregunta |
| **Sin símbolos matemáticos** | Pregunta, opciones y explicación escritas íntegramente en texto |

---

## Resultados por artículo

### T01 — Artículo 14 — Igualdad ante la ley

**Pregunta:** Según el artículo 14 de la Constitución Española, ¿cuál de los siguientes principios recoge dicho artículo respecto a los españoles ante la ley?

| Opción | Texto | Correcta |
|---|---|---|
| A | El principio de igualdad ante la ley, prohibiendo toda discriminación por razón de nacimiento, raza, sexo, religión, opinión o cualquier otra condición o circunstancia personal o social | ✓ |
| B | El principio de igualdad ante la ley, pero únicamente en lo referente a discriminaciones por razón de nacimiento y sexo | — |
| C | El principio de equidad social, que permite establecer diferencias de trato entre los ciudadanos siempre que estén justificadas por razones de orden público | — |
| D | El principio de igualdad ante la ley, aplicable exclusivamente a los ciudadanos españoles de origen y no a los naturalizados | — |

**Explicación generada:** El artículo 14 de la Constitución Española consagra el principio de igualdad ante la ley de todos los españoles, estableciendo que no puede prevalecer discriminación alguna por razón de nacimiento, raza, sexo, religión, opinión o cualquier otra condición o circunstancia personal o social. La lista de causas de discriminación prohibidas no es cerrada, ya que incluye cualquier otra condición o circunstancia personal o social, lo que amplía su alcance protector más allá de los supuestos expresamente mencionados.

| Criterio | Valoración |
|---|---|
| Pregunta clara | ✅ |
| Opción correcta | ✅ |
| Distractores plausibles | ✅ — B restringe la lista; C introduce un principio distinto; D limita el alcance subjetivo |
| Sin ambigüedad | ✅ |
| Explicación útil | ✅ — aclara el carácter abierto de la cláusula |
| Sin símbolos matemáticos | ✅ |

---

### T02 — Artículo 33 — Propiedad privada

**Pregunta:** Según el artículo 33 de la Constitución Española, ¿bajo qué condiciones puede alguien ser privado de sus bienes y derechos?

| Opción | Texto | Correcta |
|---|---|---|
| A | Por causa justificada de utilidad pública o interés social, mediante la correspondiente indemnización y de conformidad con lo dispuesto por las leyes | ✓ |
| B | Por decisión del Gobierno, sin necesidad de indemnización, siempre que exista una causa de interés general | — |
| C | Únicamente por causa de utilidad pública, sin que sea necesaria indemnización alguna si así lo dispone el Parlamento | — |
| D | Por resolución judicial firme, con independencia de que exista o no indemnización previa | — |

**Explicación generada:** El artículo 33.3 de la Constitución Española establece que nadie podrá ser privado de sus bienes y derechos sino por causa justificada de utilidad pública o interés social, mediante la correspondiente indemnización y de conformidad con lo dispuesto por las leyes. Los tres requisitos son acumulativos: causa justificada, indemnización y respeto a la legalidad vigente.

| Criterio | Valoración |
|---|---|
| Pregunta clara | ✅ |
| Opción correcta | ✅ — reproduce los tres requisitos del Art. 33.3 con precisión literal |
| Distractores plausibles | ✅ — cada distractor elimina o altera uno de los tres requisitos acumulativos |
| Sin ambigüedad | ✅ |
| Explicación útil | ✅ — identifica explícitamente los tres requisitos acumulativos |
| Sin símbolos matemáticos | ✅ |

---

### T03 — Artículo 34 — Fundaciones

**Pregunta:** Según el artículo 34 de la Constitución Española, ¿para qué fines se reconoce el derecho de fundación?

| Opción | Texto | Correcta |
|---|---|---|
| A | Para fines de interés general, con arreglo a la ley | ✓ |
| B | Para fines de interés privado, con arreglo a la ley | — |
| C | Para fines de interés general, sin necesidad de regulación legal | — |
| D | Para fines culturales y educativos exclusivamente, con arreglo a la ley | — |

**Explicación generada:** El artículo 34.1 de la Constitución Española reconoce expresamente el derecho de fundación para fines de interés general, con arreglo a la ley. No se limita a fines culturales o educativos, ni puede ejercerse al margen de la regulación legal, y tampoco se circunscribe al ámbito privado, sino que exige ese carácter de interés general como requisito esencial.

| Criterio | Valoración |
|---|---|
| Pregunta clara | ✅ |
| Opción correcta | ✅ |
| Distractores plausibles | ✅ — B invierte el carácter; C elimina la reserva de ley; D restringe los fines |
| Sin ambigüedad | ✅ |
| Explicación útil | ✅ — descarta cada distractor con su razón concreta |
| Sin símbolos matemáticos | ✅ |

**Nota:** Pregunta sustancialmente mejor que la primera tanda, que preguntaba sobre números de apartado de una remisión interna.

---

### T04 — Artículo 55 — Suspensión individual de derechos

**Pregunta:** Según el artículo 55 de la Constitución Española, ¿qué instrumento jurídico puede determinar la forma y los casos en que ciertos derechos fundamentales sean suspendidos de forma individual en relación con investigaciones sobre bandas armadas o elementos terroristas?

| Opción | Texto | Correcta |
|---|---|---|
| A | Un decreto-ley aprobado por el Gobierno en situaciones de urgencia extraordinaria | — |
| B | Una ley orgánica, con intervención judicial y control parlamentario | ✓ |
| C | Una ley ordinaria aprobada por mayoría simple del Congreso de los Diputados | — |
| D | Un acuerdo del Consejo de Ministros ratificado posteriormente por el Senado | — |

**Explicación generada:** El artículo 55.2 establece expresamente que una ley orgánica podrá determinar la forma y los casos en que, de manera individual y con la necesaria intervención judicial y el adecuado control parlamentario, los derechos reconocidos en el artículo 17, apartado 2, y el artículo 18, apartados 2 y 3, pueden ser suspendidos para personas determinadas en relación con investigaciones sobre bandas armadas o elementos terroristas. Además, el precepto señala que la utilización injustificada o abusiva de estas facultades producirá responsabilidad penal.

| Criterio | Valoración |
|---|---|
| Pregunta clara | ✅ |
| Opción correcta | ✅ — los tres requisitos del Art. 55.2: ley orgánica, intervención judicial, control parlamentario |
| Distractores plausibles | ✅ — A, C y D son instrumentos normativos reales pero de rango o procedimiento incorrecto |
| Sin ambigüedad | ✅ |
| Explicación útil | ✅ — añade la cláusula de responsabilidad penal por uso abusivo |
| Sin símbolos matemáticos | ✅ |

---

### T05 — Artículo 87 — Iniciativa legislativa popular

**Pregunta:** Según el artículo 87 de la Constitución Española, ¿cuántas firmas acreditadas se exigen como mínimo para ejercer la iniciativa legislativa popular?

| Opción | Texto | Correcta |
|---|---|---|
| A | No menos de 250.000 firmas acreditadas | — |
| B | No menos de 500.000 firmas acreditadas | ✓ |
| C | No menos de 750.000 firmas acreditadas | — |
| D | No menos de 1.000.000 de firmas acreditadas | — |

**Explicación generada:** El artículo 87.3 de la Constitución Española establece expresamente que para la presentación de proposiciones de ley mediante iniciativa popular se exigirán no menos de 500.000 firmas acreditadas. Además, esta iniciativa no procederá en materias propias de ley orgánica, tributarias o de carácter internacional, ni en lo relativo a la prerrogativa de gracia.

| Criterio | Valoración |
|---|---|
| Pregunta clara | ✅ |
| Opción correcta | ✅ — dato literal del Art. 87.3 |
| Distractores plausibles | ✅ — cuatro múltiplos plausibles del mismo orden de magnitud |
| Sin ambigüedad | ✅ |
| Explicación útil | ✅ — añade las materias excluidas de la iniciativa popular |
| Sin símbolos matemáticos | ✅ |

**Nota:** Pregunta sobre un dato concreto y fácil de confundir; los distractores están muy bien calibrados.

---

### T06 — Artículo 145 — Convenios entre Comunidades Autónomas

**Pregunta:** Según el artículo 145 de la Constitución Española, ¿qué ocurre con los acuerdos de cooperación entre Comunidades Autónomas que no estén previstos en los Estatutos como convenios para la gestión y prestación de servicios propios?

| Opción | Texto | Correcta |
|---|---|---|
| A | Necesitarán la autorización de las Cortes Generales | ✓ |
| B | Serán nulos de pleno derecho sin posibilidad de subsanación | — |
| C | Bastará con la comunicación al Gobierno central para su validez | — |
| D | Requerirán únicamente la aprobación del Senado como cámara de representación territorial | — |

**Explicación generada:** El artículo 145.2 establece que, en los supuestos distintos a los convenios entre Comunidades Autónomas previstos en los Estatutos para la gestión y prestación de servicios propios, los acuerdos de cooperación necesitarán la autorización de las Cortes Generales. Además, el artículo 145.1 prohíbe expresamente la federación de Comunidades Autónomas.

| Criterio | Valoración |
|---|---|
| Pregunta clara | ✅ |
| Opción correcta | ✅ — el Art. 145.2 atribuye la autorización a las Cortes Generales |
| Distractores plausibles | ✅ — D (solo el Senado) es el distractor más peligroso y didácticamente valioso |
| Sin ambigüedad | ✅ |
| Explicación útil | ✅ — añade la prohibición de federación del Art. 145.1 |
| Sin símbolos matemáticos | ✅ |

---

### T07 — Artículo 155 — Coerción estatal

**Pregunta:** Según el artículo 155 de la Constitución Española, ¿qué aprobación es necesaria para que el Gobierno pueda adoptar medidas de cumplimiento forzoso contra una Comunidad Autónoma que no cumpla sus obligaciones constitucionales?

| Opción | Texto | Correcta |
|---|---|---|
| A | La aprobación por mayoría simple del Congreso de los Diputados | — |
| B | La aprobación por mayoría absoluta del Senado | ✓ |
| C | La aprobación por mayoría absoluta del Congreso de los Diputados | — |
| D | La aprobación por mayoría de dos tercios del Senado | — |

**Explicación generada:** El artículo 155.1 establece que, previo requerimiento al Presidente de la Comunidad Autónoma y si este no es atendido, el Gobierno necesita la aprobación por mayoría absoluta del Senado para poder adoptar las medidas necesarias que obliguen a la Comunidad Autónoma al cumplimiento forzoso de sus obligaciones o a la protección del interés general de España. No interviene el Congreso de los Diputados ni se exige una mayoría de dos tercios.

| Criterio | Valoración |
|---|---|
| Pregunta clara | ✅ |
| Opción correcta | ✅ — mayoría absoluta del Senado, tal como establece el Art. 155.1 |
| Distractores plausibles | ✅ — A y C confunden la cámara; D confunde el tipo de mayoría |
| Sin ambigüedad | ✅ |
| Explicación útil | ✅ — descarta explícitamente el Congreso y la mayoría de dos tercios |
| Sin símbolos matemáticos | ✅ |

---

### T08 — Artículo 169 — Límites a la reforma constitucional

**Pregunta:** Según el artículo 169 de la Constitución Española, ¿en qué circunstancias no podrá iniciarse la reforma constitucional?

| Opción | Texto | Correcta |
|---|---|---|
| A | En tiempo de guerra o de vigencia de alguno de los estados previstos en el artículo 116 | ✓ |
| B | Únicamente en tiempo de guerra declarada por el Congreso de los Diputados | — |
| C | Solo durante la vigencia del estado de sitio, pero no durante el estado de alarma ni el de excepción | — |
| D | Durante los períodos de sesiones parlamentarias ordinarias y en tiempo de guerra | — |

**Explicación generada:** El artículo 169 establece que no podrá iniciarse la reforma constitucional en tiempo de guerra o de vigencia de alguno de los estados previstos en el artículo 116, que son el estado de alarma, el estado de excepción y el estado de sitio. La prohibición abarca todos estos supuestos de forma conjunta, sin distinguir entre ellos, lo que garantiza que los procesos de reforma constitucional se lleven a cabo en condiciones de plena normalidad democrática e institucional.

| Criterio | Valoración |
|---|---|
| Pregunta clara | ✅ |
| Opción correcta | ✅ — reproduce literalmente el Art. 169 |
| Distractores plausibles | ✅ — B y C son los más eficaces: incluyen un elemento correcto pero omiten o restringen el otro |
| Sin ambigüedad | ✅ |
| Explicación útil | ✅ — enumera los tres estados del Art. 116 y justifica la ratio de la prohibición |
| Sin símbolos matemáticos | ✅ |

---

## Conclusiones

### Fortalezas del generador

- **Precisión jurídica**: en los 8 casos la opción marcada como correcta es verificable en el texto literal de la CE. Sin errores de fondo.
- **Distractores de calidad**: las opciones incorrectas alteran de forma quirúrgica uno de los requisitos del artículo (órgano, mayoría, instrumento normativo, fines, umbrales).
- **Explicaciones útiles**: en los 8 casos la explicación aporta contexto que va más allá de repetir la opción correcta.
- **Formato JSON consistente**: 8/8 respuestas parseadas sin errores.
- **Sin símbolos matemáticos**: restricción aplicada correctamente en todos los campos.

### Decisión

> El generador de tests produce preguntas jurídicamente correctas, didácticamente sólidas y sin símbolos matemáticos. **Pipeline validado y listo para Hito 3: exportación a CSV / Moodle XML.**
