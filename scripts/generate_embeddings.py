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
import sys
import time
import argparse
from pathlib import Path
import psycopg2
from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent


def _load_supabase_secrets():
    secrets_path = BASE_DIR / ".streamlit" / "secrets.toml"
    if not secrets_path.exists():
        raise SystemExit("ERROR: .streamlit/secrets.toml no encontrado.")
    for line in secrets_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("["):
            continue
        if "=" in line:
            k, _, v = line.partition("=")
            os.environ[k.strip()] = v.strip().strip('"').strip("'")
    direct_host = os.environ.get("DB_HOST", "")
    ref = direct_host.split(".")[1] if direct_host.startswith("db.") else ""
    if ref:
        os.environ["DB_HOST"] = "aws-1-eu-west-2.pooler.supabase.com"
        os.environ["DB_USER"] = f"postgres.{ref}"
    print(f"Supabase via Session Pooler: {os.environ['DB_HOST']}")

EMBEDDING_MODEL  = "text-embedding-3-small"
BATCH_SIZE       = 50
MAX_CHARS        = 24000  # ~6800 tokens, margen seguro bajo el límite de 8192

def _db_config():
    return {
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
    texto = " ".join(parts)
    return texto[:MAX_CHARS] if len(texto) > MAX_CHARS else texto


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--supabase", action="store_true", help="Usar Supabase via Session Pooler")
    args = parser.parse_args()
    if args.supabase:
        _load_supabase_secrets()

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise SystemExit("Error: define la variable de entorno OPENAI_API_KEY")

    client = OpenAI(api_key=api_key)
    conn   = psycopg2.connect(**_db_config())
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

        try:
            response   = client.embeddings.create(model=EMBEDDING_MODEL, input=textos)
            embeddings = [e.embedding for e in response.data]
            pairs = list(zip(batch, embeddings))
        except Exception:
            # Lote con artículo demasiado largo: procesar uno a uno
            pairs = []
            for row, texto in zip(batch, textos):
                for max_c in (MAX_CHARS, 16000, 8000):
                    try:
                        resp = client.embeddings.create(
                            model=EMBEDDING_MODEL, input=[texto[:max_c]]
                        )
                        pairs.append((row, resp.data[0].embedding))
                        break
                    except Exception:
                        continue

        for row, vector in pairs:
            cur.execute(
                "UPDATE normas.articulos SET embedding = %s WHERE articulo_id = %s",
                (vector, row["articulo_id"])
            )

        conn.commit()
        procesados += len(pairs)
        print(f"  {procesados}/{total} embeddings almacenados")
        time.sleep(0.3)

    cur.close()
    conn.close()
    print("\nCompletado.")


if __name__ == "__main__":
    main()
