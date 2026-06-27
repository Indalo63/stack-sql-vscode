"""
Configuración centralizada: variables de entorno, modelos y constantes.

En local lee de .env (via python-dotenv en streamlit_app.py).
En Streamlit Cloud lee de st.secrets si está disponible.
"""

import os


def _get(key: str, default: str = "") -> str:
    """Lee de os.environ primero (scripts/CLI), luego de st.secrets (Streamlit)."""
    env_val = os.getenv(key)
    if env_val is not None:
        return env_val
    try:
        import streamlit as st
        return st.secrets.get(key, default)
    except Exception:
        return default


DB_CONFIG = {
    "host":     _get("DB_HOST",     "localhost"),
    "port":     int(_get("DB_PORT", "5432")),
    "dbname":   _get("DB_NAME",     "stack_db"),
    "user":     _get("DB_USER",     "postgres"),
    "password": _get("DB_PASSWORD", "postgres"),
}

OPENAI_API_KEY  = _get("OPENAI_API_KEY")
ANTHROPIC_API_KEY = _get("ANTHROPIC_API_KEY")

OPENAI_EMBEDDING_MODEL = "text-embedding-3-small"
CLAUDE_MODEL           = "claude-sonnet-4-6"

TOP_K_ARTICLES               = 8      # artículos a recuperar en búsqueda semántica
SIMILARITY_THRESHOLD         = 0.20   # similitud coseno mínima para incluir un artículo
TOKEN_THRESHOLD_HIERARCHICAL = 60_000 # leyes con más tokens usan RAG jerárquico
