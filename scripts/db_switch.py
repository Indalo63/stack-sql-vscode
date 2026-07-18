"""
scripts/db_switch.py

Alterna la app completa (streamlit run) entre Supabase cloud y el Postgres
local de docker/docker-compose.yml, sin arriesgar apuntar a producción por
error ni tener que editar `.streamlit/secrets.toml` a mano cada vez.

Cómo funciona: `.streamlit/secrets.toml` (el fichero que Streamlit lee de
verdad) pasa a ser un symlink a uno de estos dos ficheros, gemelos en todo
menos en el bloque DB_*:
  - .streamlit/secrets.supabase.toml  (el original: BD real de producción)
  - .streamlit/secrets.local.toml     (mismo contenido, BD → Postgres local)

Un symlink en vez de sobrescribir el fichero cada vez: el estado queda
inspeccionable (`readlink .streamlit/secrets.toml`) y no hay riesgo de que
un editor manual deje las credenciales de Supabase a medio pisar.

Uso:
    python3 scripts/db_switch.py local
    python3 scripts/db_switch.py supabase
    python3 scripts/db_switch.py status
"""

import re
import sys
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
SECRETS_DIR = BASE_DIR / ".streamlit"
CURRENT = SECRETS_DIR / "secrets.toml"
SUPABASE_FILE = SECRETS_DIR / "secrets.supabase.toml"
LOCAL_FILE = SECRETS_DIR / "secrets.local.toml"

DB_KEYS = ["DB_HOST", "DB_PORT", "DB_NAME", "DB_USER", "DB_PASSWORD"]
LOCAL_VALUES = {
    "DB_HOST": "localhost",
    "DB_PORT": "5432",
    "DB_NAME": "stack_db",
    "DB_USER": "postgres",
    "DB_PASSWORD": "postgres",
}


def _asegurar_separacion_inicial() -> None:
    """La primera vez que se usa este script: separa el secrets.toml actual
    (apunta a Supabase) en su propio fichero, sin tocar su contenido."""
    if CURRENT.is_symlink():
        return
    if not CURRENT.exists():
        print("ERROR: no existe .streamlit/secrets.toml", file=sys.stderr)
        sys.exit(1)
    if SUPABASE_FILE.exists():
        print("ERROR: existen secrets.toml (fichero real) y secrets.supabase.toml a la vez; "
              "revísalo a mano antes de continuar.", file=sys.stderr)
        sys.exit(1)
    CURRENT.rename(SUPABASE_FILE)
    CURRENT.symlink_to(SUPABASE_FILE.name)
    print(f"Primer uso: {CURRENT.name} separado en {SUPABASE_FILE.name} (contenido intacto).")


def _generar_local_desde_supabase() -> None:
    contenido = SUPABASE_FILE.read_text(encoding="utf-8")
    ancho = max(len(k) for k in DB_KEYS)
    for key in DB_KEYS:
        contenido = re.sub(
            rf'^{key}\s*=.*$',
            f'{key.ljust(ancho)} = "{LOCAL_VALUES[key]}"',
            contenido,
            count=1,
            flags=re.MULTILINE,
        )
    LOCAL_FILE.write_text(contenido, encoding="utf-8")
    print(f"Generado {LOCAL_FILE.name} (mismas API keys/Auth, BD → Postgres local).")


def _entorno_de(path: Path) -> str:
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip().startswith("DB_HOST"):
            host = line.split("=", 1)[1].strip().strip('"').strip("'")
            return "SUPABASE (producción)" if "supabase" in host else f"local ({host})"
    return "desconocido"


def main() -> None:
    if len(sys.argv) != 2 or sys.argv[1] not in ("local", "supabase", "status"):
        print(__doc__)
        sys.exit(1)

    accion = sys.argv[1]
    _asegurar_separacion_inicial()

    if accion == "status":
        activo = CURRENT.resolve().name
        print(f"secrets.toml -> {activo}  [{_entorno_de(CURRENT)}]")
        return

    if accion == "local" and not LOCAL_FILE.exists():
        _generar_local_desde_supabase()

    destino = LOCAL_FILE if accion == "local" else SUPABASE_FILE
    if CURRENT.is_symlink() or CURRENT.exists():
        CURRENT.unlink()
    CURRENT.symlink_to(destino.name)
    print(f"secrets.toml -> {destino.name}  [{_entorno_de(CURRENT)}]")


if __name__ == "__main__":
    main()
