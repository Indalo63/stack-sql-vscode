"""
Genera embeddings para los artículos de la Constitución Española
y los almacena en legislacion.articulos.embedding (vector 1536).

Requiere:
  pip install openai psycopg2-binary

Variables de entorno necesarias:
  OPENAI_API_KEY   → clave de la API de OpenAI
  DB_HOST          → host de PostgreSQL (default: localhost)
  DB_PORT          → puerto (default: 5432)
  DB_NAME          → nombre de la base de datos (default: stack_db)
  DB_USER          → usuario (default: postgres)
  DB_PASSWORD      → contraseña (default: postgres)
"""

import os
import time
import psycopg2
from openai import OpenAI

EMBEDDING_MODEL = "text-embedding-3-small"  # 1536 dimensiones, coincide con el esquema
BATCH_SIZE = 50                              # artículos por lote (límite de tokens OpenAI)

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
        parts.append(f"Título {row['titulo']}: {row['denom_titulo']}")
    if row["capitulo"]:
        parts.append(f"Capítulo {row['capitulo']}: {row['denom_capitulo']}")
    if row["seccion"]:
        parts.append(f"Sección {row['seccion']}: {row['denom_seccion']}")
    if row["tipo"] == "articulo":
        parts.append(f"Artículo {row['numero']}.")
    else:
        parts.append(f"{row['numero']}.")
    parts.append(row["contenido"])
    return " ".join(parts)


def main():
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    # Obtener artículos sin embedding con contexto jerárquico
    cur.execute("""
        SELECT
            a.articulo_id,
            a.numero,
            a.tipo,
            a.contenido,
            t.numero          AS titulo,
            t.denominacion    AS denom_titulo,
            c.numero          AS capitulo,
            c.denominacion    AS denom_capitulo,
            s.numero          AS seccion,
            s.denominacion    AS denom_seccion
        FROM legislacion.articulos a
        LEFT JOIN legislacion.titulos   t ON a.titulo_id   = t.titulo_id
        LEFT JOIN legislacion.capitulos c ON a.capitulo_id = c.capitulo_id
        LEFT JOIN legislacion.secciones s ON a.seccion_id  = s.seccion_id
        WHERE a.embedding IS NULL
        ORDER BY a.orden_global
    """)
    cols = [d[0] for d in cur.description]
    rows = [dict(zip(cols, r)) for r in cur.fetchall()]

    print(f"Artículos sin embedding: {len(rows)}")

    procesados = 0
    for i in range(0, len(rows), BATCH_SIZE):
        batch = rows[i:i + BATCH_SIZE]
        textos = [build_text(r) for r in batch]

        response = client.embeddings.create(model=EMBEDDING_MODEL, input=textos)
        embeddings = [e.embedding for e in response.data]

        for row, vector in zip(batch, embeddings):
            cur.execute(
                "UPDATE legislacion.articulos SET embedding = %s WHERE articulo_id = %s",
                (vector, row["articulo_id"])
            )

        conn.commit()
        procesados += len(batch)
        print(f"  {procesados}/{len(rows)} embeddings generados")
        time.sleep(0.5)  # respetar rate limit de OpenAI

    cur.close()
    conn.close()
    print("Completado.")


if __name__ == "__main__":
    main()
