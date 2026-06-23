"""
Configuración centralizada: variables de entorno, modelos y constantes.
"""

import os

DB_CONFIG = {
    "host":     os.getenv("DB_HOST",     "localhost"),
    "port":     int(os.getenv("DB_PORT", "5432")),
    "dbname":   os.getenv("DB_NAME",     "stack_db"),
    "user":     os.getenv("DB_USER",     "postgres"),
    "password": os.getenv("DB_PASSWORD", "postgres"),
}

OPENAI_EMBEDDING_MODEL = "text-embedding-3-small"
CLAUDE_MODEL           = "claude-sonnet-4-6"

TOP_K_ARTICLES              = 8      # artículos a recuperar en búsqueda semántica
SIMILARITY_THRESHOLD        = 0.20   # similitud coseno mínima para incluir un artículo
TOKEN_THRESHOLD_HIERARCHICAL = 60_000 # leyes con más tokens usan RAG jerárquico
