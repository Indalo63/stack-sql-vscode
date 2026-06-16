# Guía de consultas – Base de datos legislativa CE

## Propósito

Este documento explica cómo usar el archivo `sql/queries/constitucion_preguntas.sql` para explorar el contenido de la Constitución Española y construir el pipeline de generación de preguntas (Q&A).

Las consultas están organizadas en 5 bloques según su función.

---

## Bloque 1 — Navegación jerárquica

**Para qué sirve:** entender la estructura del documento antes de generar preguntas. Útil para decidir qué bloque temático trabajar.

**Consultas incluidas:**

- Todos los títulos con número de artículos por título
- Estructura completa título > capítulo > sección con recuento

**Ejemplo de resultado:**

```
titulo | denominacion                                  | articulos
-------+-----------------------------------------------+-----------
I      | De los Derechos y Deberes Fundamentales       | 46
II     | De la Corona                                  | 10
III    | De las Cortes Generales                       | 31
...
```

---

## Bloque 2 — Consultas de contenido para Q&A

**Para qué sirve:** recuperar el texto exacto de uno o varios artículos para enviarlo al modelo de lenguaje junto con la pregunta del usuario.

**Patrones disponibles:**

| Consulta | Parámetro a cambiar | Ejemplo |
|----------|---------------------|---------|
| Texto de un artículo concreto | `numero = '14'` | Cambiar el número de artículo |
| Todos los artículos de un título | `t.numero = 'I'` | Cambiar el número de título |
| Artículos de una sección | `s.numero = '1.ª'` | Cambiar número de sección |
| Preámbulo completo | — | No requiere parámetros |
| Todas las disposiciones | — | Filtra por tipo != articulo |

---

## Bloque 3 — Búsqueda por palabra clave

**Para qué sirve:** localizar artículos relevantes para un tema sin necesidad de embeddings. Útil para prototipado rápido o como fallback si los embeddings no están generados.

**Operador usado:** `ILIKE '%termino%'` — búsqueda insensible a mayúsculas.

**Ejemplos de búsqueda:**

```sql
-- Todos los artículos que mencionan "libertad"
WHERE contenido ILIKE '%libertad%'

-- Artículos que regulan el Tribunal Constitucional
WHERE contenido ILIKE '%Tribunal Constitucional%'
```

**Limitación:** encuentra coincidencias exactas de texto pero no sinónimos ni variantes semánticas. Para búsqueda conceptual, usar el Bloque 5 (pgvector).

---

## Bloque 4 — Plantillas para generación automática de preguntas

**Para qué sirve:** preparar lotes de artículos para enviar al modelo de lenguaje y que genere preguntas sobre ellos.

**Tres patrones incluidos:**

### 4a. Artículos cortos (< 300 caracteres)
Buenos para preguntas directas de tipo "¿Qué establece el artículo X?". Ejemplo: Art. 5 ("La capital del Estado es la villa de Madrid.") o Art. 12 (mayoría de edad).

### 4b. Artículos con apartados numerados
Los artículos que comienzan con `1.`, `2.`, `3.` permiten preguntas de detalle sobre cada apartado: "¿Cuál es la diferencia entre el apartado 1 y el 2 del artículo X?".

### 4c. Lote completo con contexto jerárquico
Consulta principal para el pipeline Q&A. Devuelve cada artículo con su título, capítulo y sección, lo que permite al modelo generar preguntas más precisas y contextualizadas:

```
articulo | titulo                                      | capitulo | seccion | contenido
---------+---------------------------------------------+----------+---------+----------
15       | I – De los Derechos y Deberes Fundamentales | SEGUNDO  | 1.ª     | Todos tienen derecho...
```

---

## Bloque 5 — Búsqueda semántica con pgvector

**Prerequisito:** embeddings generados con `scripts/generate_embeddings.py`.

**Para qué sirve:** dado el texto de una pregunta del usuario, encontrar los artículos más relevantes por similitud semántica (no por palabras exactas).

### Flujo del pipeline Q&A

```
Pregunta del usuario
      │
      ▼
Modelo de embeddings (paraphrase-multilingual-mpnet-base-v2 — HuggingFace)
      │  genera vector de 768 dimensiones
      ▼
Consulta SQL con operador <=> (distancia coseno)
      │  devuelve top-N artículos más similares
      ▼
Contexto enviado al modelo de lenguaje (Claude)
      │  junto con la pregunta original
      ▼
Respuesta fundamentada en el texto de la CE
```

### Operadores pgvector disponibles

| Operador | Métrica | Uso |
|----------|---------|-----|
| `<=>` | Distancia coseno | Recomendado para texto |
| `<->` | Distancia euclidiana | Para vectores normalizados |
| `<#>` | Producto interno negativo | Alternativa eficiente |

### Patrón de consulta

```sql
-- Sustituir [VECTOR] por el embedding de la pregunta del usuario
SELECT
    a.numero,
    LEFT(a.contenido, 300)        AS contenido,
    1 - (a.embedding <=> '[VECTOR]') AS similitud_coseno
FROM legislacion.articulos a
WHERE a.embedding IS NOT NULL
ORDER BY a.embedding <=> '[VECTOR]'
LIMIT 5;
```

`similitud_coseno` devuelve un valor entre 0 y 1. Por encima de 0.8 indica alta relevancia semántica.

---

## Verificar estado de embeddings

Antes de usar el Bloque 5, comprobar cuántos artículos tienen embedding generado:

```sql
SELECT
    COUNT(*) FILTER (WHERE embedding IS NOT NULL) AS con_embedding,
    COUNT(*) FILTER (WHERE embedding IS NULL)     AS sin_embedding
FROM legislacion.articulos;
```

Si `sin_embedding > 0`, ejecutar:

```bash
export HF_TOKEN=hf_xxxxxxxxxxxx
python3 scripts/generate_embeddings.py
```

---

## Archivos relacionados

| Archivo | Descripción |
|---------|-------------|
| `sql/queries/constitucion_preguntas.sql` | Todas las consultas de este documento |
| `scripts/generate_embeddings.py` | Genera y carga los embeddings en la DB |
| `docs/database/constitucion/02-schema.md` | Documentación del esquema de tablas |
