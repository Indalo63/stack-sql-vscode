"""
Genera embeddings para los títulos de todas las leyes activas.
El texto a embeder = nombre del título + primeros 300 chars de cada artículo que contiene.

Uso:
  python3 scripts/generate_title_embeddings.py
"""

import os
import time
import psycopg2
from openai import OpenAI

EMBEDDING_MODEL = "text-embedding-3-small"
MAX_CHARS       = 30_000
BATCH_SIZE      = 20

DB_CONFIG = {
    "host":     os.getenv("DB_HOST",     "localhost"),
    "port":     int(os.getenv("DB_PORT", "5432")),
    "dbname":   os.getenv("DB_NAME",     "stack_db"),
    "user":     os.getenv("DB_USER",     "postgres"),
    "password": os.getenv("DB_PASSWORD", "postgres"),
}


def build_title_text(titulo: dict, articulos: list[dict]) -> str:
    """Texto representativo de un título: cabecera + fragmento de cada artículo."""
    parts = [f"Título {titulo['numero']}: {titulo['denominacion']}."]
    for a in articulos:
        resumen = a["contenido"][:300].replace("\n", " ")
        parts.append(f"Art. {a['numero']}: {resumen}")
    texto = "\n".join(parts)
    return texto[:MAX_CHARS] if len(texto) > MAX_CHARS else texto


def main():
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise SystemExit("Error: define la variable de entorno OPENAI_API_KEY")

    client = OpenAI(api_key=api_key)
    conn   = psycopg2.connect(**DB_CONFIG)
    cur    = conn.cursor()

    # Títulos sin embedding
    cur.execute("""
        SELECT t.titulo_id, t.numero, t.denominacion, l.nombre AS ley_nombre
        FROM normas.titulos t
        JOIN normas.leyes l ON t.ley_id = l.ley_id
        WHERE t.embedding IS NULL AND l.activa = true
        ORDER BY l.ley_id, t.orden
    """)
    titulos = [
        {"titulo_id": r[0], "numero": r[1], "denominacion": r[2], "ley": r[3]}
        for r in cur.fetchall()
    ]

    total = len(titulos)
    if total == 0:
        print("Todos los títulos ya tienen embedding.")
        conn.close()
        return

    print(f"Títulos sin embedding: {total}")
    print(f"Modelo: {EMBEDDING_MODEL}\n")

    procesados = 0
    for i in range(0, total, BATCH_SIZE):
        batch = titulos[i:i + BATCH_SIZE]

        # Construir texto de cada título del lote
        textos = []
        for t in batch:
            cur.execute("""
                SELECT numero, contenido
                FROM normas.articulos
                WHERE titulo_id = %s AND tipo = 'articulo'
                ORDER BY orden_global
            """, (t["titulo_id"],))
            arts = [{"numero": r[0], "contenido": r[1]} for r in cur.fetchall()]
            textos.append(build_title_text(t, arts))

        response   = client.embeddings.create(model=EMBEDDING_MODEL, input=textos)
        embeddings = [e.embedding for e in response.data]

        for titulo, vector in zip(batch, embeddings):
            cur.execute(
                "UPDATE normas.titulos SET embedding = %s WHERE titulo_id = %s",
                (vector, titulo["titulo_id"])
            )

        conn.commit()
        procesados += len(batch)
        print(f"  {procesados}/{total} títulos embebidos")
        time.sleep(0.2)

    cur.close()
    conn.close()
    print("\nCompletado.")


if __name__ == "__main__":
    main()
