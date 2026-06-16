"""
Genera embeddings para los artículos de la Constitución Española
usando la Inference API gratuita de Hugging Face y los almacena
en legislacion.articulos.embedding (vector 768).

Modelo: sentence-transformers/paraphrase-multilingual-mpnet-base-v2
  - 768 dimensiones
  - Multilingüe (optimizado para español)
  - Gratuito en HuggingFace Inference API

Requisitos:
  pip install requests psycopg2-binary

Variables de entorno:
  HF_TOKEN     → token de HuggingFace (Settings → Access Tokens)
  DB_HOST      → host PostgreSQL (default: localhost)
  DB_PORT      → puerto (default: 5432)
  DB_NAME      → base de datos (default: stack_db)
  DB_USER      → usuario (default: postgres)
  DB_PASSWORD  → contraseña (default: postgres)

Uso:
  export HF_TOKEN=hf_xxxxxxxxxxxx
  python3 scripts/generate_embeddings.py
"""

import os
import time
import requests
import psycopg2

HF_MODEL   = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"
HF_API_URL = f"https://api-inference.huggingface.co/pipeline/feature-extraction/{HF_MODEL}"
BATCH_SIZE = 16   # lotes pequeños para respetar el rate limit gratuito
RETRY_MAX  = 5    # reintentos ante error 503 (modelo cargando)
RETRY_WAIT = 20   # segundos de espera entre reintentos

DB_CONFIG = {
    "host":     os.getenv("DB_HOST",     "localhost"),
    "port":     int(os.getenv("DB_PORT", "5432")),
    "dbname":   os.getenv("DB_NAME",     "stack_db"),
    "user":     os.getenv("DB_USER",     "postgres"),
    "password": os.getenv("DB_PASSWORD", "postgres"),
}


def build_text(row: dict) -> str:
    """Construye el texto a embedear con contexto jerárquico + contenido."""
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


def embed_batch(textos: list[str], headers: dict) -> list[list[float]]:
    """Envía un lote a la API de HuggingFace con reintentos ante 503."""
    payload = {"inputs": textos, "options": {"wait_for_model": True}}

    for intento in range(1, RETRY_MAX + 1):
        response = requests.post(HF_API_URL, headers=headers, json=payload, timeout=60)

        if response.status_code == 200:
            return response.json()

        if response.status_code == 503:
            print(f"  Modelo cargando (503) — reintento {intento}/{RETRY_MAX} en {RETRY_WAIT}s")
            time.sleep(RETRY_WAIT)
            continue

        if response.status_code == 429:
            wait = int(response.headers.get("Retry-After", 60))
            print(f"  Rate limit (429) — esperando {wait}s")
            time.sleep(wait)
            continue

        response.raise_for_status()

    raise RuntimeError(f"No se pudo obtener embedding tras {RETRY_MAX} reintentos")


def main():
    hf_token = os.environ.get("HF_TOKEN")
    if not hf_token:
        raise SystemExit("Error: define la variable de entorno HF_TOKEN")

    headers = {"Authorization": f"Bearer {hf_token}"}

    conn = psycopg2.connect(**DB_CONFIG)
    cur  = conn.cursor()

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

    total = len(rows)
    if total == 0:
        print("Todos los artículos ya tienen embedding.")
        return

    print(f"Artículos sin embedding: {total}")
    print(f"Modelo: {HF_MODEL}")
    print(f"Lotes de {BATCH_SIZE} — estimado: {total // BATCH_SIZE + 1} llamadas a la API\n")

    procesados = 0
    for i in range(0, total, BATCH_SIZE):
        batch  = rows[i:i + BATCH_SIZE]
        textos = [build_text(r) for r in batch]

        vectores = embed_batch(textos, headers)

        for row, vector in zip(batch, vectores):
            cur.execute(
                "UPDATE legislacion.articulos SET embedding = %s WHERE articulo_id = %s",
                (vector, row["articulo_id"])
            )

        conn.commit()
        procesados += len(batch)
        print(f"  {procesados}/{total} embeddings almacenados")
        time.sleep(1)  # pausa entre lotes para el plan gratuito

    cur.close()
    conn.close()
    print("\nCompletado. Todos los artículos tienen embedding.")


if __name__ == "__main__":
    main()
