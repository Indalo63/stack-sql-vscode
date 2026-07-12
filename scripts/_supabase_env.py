"""
scripts/_supabase_env.py

Apunta la conexión a BD (app.config.DB_CONFIG) a Supabase vía Session Pooler,
en vez del host directo de .streamlit/secrets.toml.

Por qué existe: este devcontainer no resuelve por IPv6 el host directo
(db.<ref>.supabase.co), así que cualquier script o verificación en vivo
tiene que pasar por el pooler (aws-1-eu-west-2.pooler.supabase.com,
usuario postgres.<ref>).

Por qué exporta *todas* las claves de secrets.toml y no solo DB_HOST/DB_USER:
app.config._get() cae a `import streamlit as st; st.secrets.get(...)` en
cuanto una clave (DB_NAME, DB_PASSWORD, OPENAI_API_KEY...) no está ya en
os.environ. Ese `import streamlit` tiene un efecto secundario — Streamlit
vuelca st.secrets sobre os.environ al importarse — que pisa silenciosamente
cualquier override de DB_HOST/DB_USER hecho a medias. Exportar las 5 claves
DB_* (más el resto de secrets.toml, por si algún script las necesita) antes
de que se importe app.config evita que esa rama se ejecute nunca.

Uso: llamar a load_supabase_secrets() ANTES de `from app.db import get_connection`
o de cualquier import que arrastre app.config.
"""

import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent


def load_supabase_secrets() -> None:
    secrets_path = BASE_DIR / ".streamlit" / "secrets.toml"
    if not secrets_path.exists():
        print("ERROR: .streamlit/secrets.toml no encontrado.", file=sys.stderr)
        sys.exit(1)

    secrets = {}
    for line in secrets_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("["):
            continue
        if "=" in line:
            k, _, v = line.partition("=")
            secrets[k.strip()] = v.strip().strip('"').strip("'")

    for k, v in secrets.items():
        os.environ[k] = v

    direct_host = secrets.get("DB_HOST", "")
    ref = direct_host.split(".")[1] if direct_host.startswith("db.") else ""
    if ref:
        os.environ["DB_HOST"] = "aws-1-eu-west-2.pooler.supabase.com"
        os.environ["DB_USER"] = f"postgres.{ref}"

    print(f"Supabase via Session Pooler: {os.environ['DB_HOST']}")


def use_local_defaults() -> None:
    os.environ.setdefault("DB_HOST", "localhost")
    os.environ.setdefault("DB_PORT", "5432")
    os.environ.setdefault("DB_NAME", "stack_db")
    os.environ.setdefault("DB_USER", "postgres")
    os.environ.setdefault("DB_PASSWORD", "postgres")
