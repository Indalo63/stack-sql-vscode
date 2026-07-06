"""
Autenticación de alumnos vía Supabase Auth (email + contraseña).

Independiente del login de editor/academia (Google OAuth vía st.login,
ver app/streamlit_app.py) — son dos mecanismos de sesión distintos.
"""

from supabase import create_client, Client
from app.config import SUPABASE_URL, SUPABASE_ANON_KEY

_client: Client | None = None


def get_client() -> Client:
    global _client
    if _client is None:
        if not SUPABASE_URL or not SUPABASE_ANON_KEY:
            raise RuntimeError(
                "SUPABASE_URL / SUPABASE_ANON_KEY no configurados. "
                "Añádelos a .streamlit/secrets.toml o .env."
            )
        _client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
    return _client


def registrar_alumno(email: str, password: str) -> dict:
    """Registra un alumno nuevo. Devuelve {"user_id": ..., "email": ...}."""
    response = get_client().auth.sign_up({"email": email, "password": password})
    if response.user is None:
        raise ValueError("No se pudo crear el usuario.")
    return {"user_id": response.user.id, "email": response.user.email}


def login_alumno(email: str, password: str) -> dict:
    """Inicia sesión de un alumno. Devuelve {"user_id": ..., "email": ...}."""
    response = get_client().auth.sign_in_with_password(
        {"email": email, "password": password}
    )
    if response.user is None:
        raise ValueError("Credenciales incorrectas.")
    return {"user_id": response.user.id, "email": response.user.email}
