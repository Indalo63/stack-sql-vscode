"""
Genera embeddings para los artículos sin vectorizar en normas.articulos.
Procesa todas las leyes cargadas en la BD (no solo la CE).

Modelo: text-embedding-3-small (OpenAI) — 1536 dimensiones
Coste estimado: ~0.001$ por cada 185 artículos

Variables de entorno:
  OPENAI_API_KEY  → clave de la API de OpenAI
  DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD → conexión PostgreSQL

Uso:
  python3 scripts/generate_embeddings.py
"""

import os
import time
import psycopg2
from openai import OpenAI

EMBEDDING_MODEL = "text-embedding-3-small"
BATCH_SIZE      = 50

DB_CONFIG = {
    "host":     os.getenv("DB_HOST",     "localhost"),
    "port":     int(os.getenv("DB_PORT", "5432")),
    "dbname":   os.getenv("DB_NAME",     "stack_db"),
    "user":     os.getenv("DB_USER",     "postgres"),
    "password": os.getenv("DB_PASSWORD", "postgres"),
}


def build_text(row: dict) -> str:
    """Construye el texto a embedear combinando contexto jerárquico + contenido."""
    parts = []
    if row["titulo"]:
        parts.append(f"Título {row['titulo']}: {row['denom_titulo']}.")
    if row["capitulo"]:
        parts.append(f"Capítulo {row['capitulo']}: {row['denom_capitulo']}.")
    if row["seccion"]:
        parts.append(f"Sección {row['seccion']}: {row['denom_seccion']}.")
    if row["tipo"] == "articulo":
        parts.append(f"Artículo {row['numero']}.")
    else:
        parts.append(f"{row['numero']}.")
    parts.append(row["contenido"])
    return " ".join(parts)


def main():
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise SystemExit("Error: define la variable de entorno OPENAI_API_KEY")

    client = OpenAI(api_key=api_key)
    conn   = psycopg2.connect(**DB_CONFIG)
    cur    = conn.cursor()

    cur.execute("""
        SELECT
            a.articulo_id,
            a.numero,
            a.tipo,
            a.contenido,
            l.nombre          AS ley_nombre,
            t.numero          AS titulo,
            t.denominacion    AS denom_titulo,
            c.numero          AS capitulo,
            c.denominacion    AS denom_capitulo,
            s.numero          AS seccion,
            s.denominacion    AS denom_seccion
        FROM normas.articulos a
        JOIN normas.leyes l       ON a.ley_id      = l.ley_id
        LEFT JOIN normas.titulos   t ON a.titulo_id   = t.titulo_id
        LEFT JOIN normas.capitulos c ON a.capitulo_id = c.capitulo_id
        LEFT JOIN normas.secciones s ON a.seccion_id  = s.seccion_id
        WHERE a.embedding IS NULL
          AND l.activa = true
        ORDER BY a.ley_id, a.orden_global
    """)
    cols = [d[0] for d in cur.description]
    rows = [dict(zip(cols, r)) for r in cur.fetchall()]

    total = len(rows)
    if total == 0:
        print("Todos los artículos ya tienen embedding.")
        conn.close()
        return

    print(f"Artículos sin embedding: {total}")
    print(f"Modelo: {EMBEDDING_MODEL} (1536 dimensiones)")
    print(f"Lotes de {BATCH_SIZE}\n")

    procesados = 0
    for i in range(0, total, BATCH_SIZE):
        batch  = rows[i:i + BATCH_SIZE]
        textos = [build_text(r) for r in batch]

        response   = client.embeddings.create(model=EMBEDDING_MODEL, input=textos)
        embeddings = [e.embedding for e in response.data]

        for row, vector in zip(batch, embeddings):
            cur.execute(
                "UPDATE normas.articulos SET embedding = %s WHERE articulo_id = %s",
                (vector, row["articulo_id"])
            )

        conn.commit()
        procesados += len(batch)
        print(f"  {procesados}/{total} embeddings almacenados")
        time.sleep(0.3)

    cur.close()
    conn.close()
    print("\nCompletado.")


if __name__ == "__main__":
    main()
