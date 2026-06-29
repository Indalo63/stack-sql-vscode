#!/usr/bin/env python3
"""
Carga una ley en el schema normas.* desde un archivo JSON estructurado.

Uso:
  python3 scripts/load_ley.py data/leyes/lpac.json
  python3 scripts/load_ley.py data/leyes/lpac.json --embeddings
  python3 scripts/load_ley.py data/leyes/lpac.json --supabase --embeddings
  python3 scripts/load_ley.py data/leyes/lpac.json --force     # sobreescribir si ya existe
  python3 scripts/load_ley.py --ejemplo > data/leyes/plantilla.json

Formato JSON de entrada: ver --ejemplo o docs/database/ley-json-format.md

Variables de entorno:
  DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD
  OPENAI_API_KEY  (solo con --embeddings)
"""

import os
import sys
import json
import argparse
import subprocess
import psycopg2
from pathlib import Path
from psycopg2.extras import execute_values

BASE_DIR = Path(__file__).resolve().parent.parent

sys.path.insert(0, str(BASE_DIR))

from dotenv import load_dotenv
load_dotenv()


def _load_supabase_secrets():
    secrets_path = BASE_DIR / ".streamlit" / "secrets.toml"
    if not secrets_path.exists():
        raise SystemExit("ERROR: .streamlit/secrets.toml no encontrado.")
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


def _db_config():
    return {
        "host":     os.getenv("DB_HOST",     "localhost"),
        "port":     int(os.getenv("DB_PORT", "5432")),
        "dbname":   os.getenv("DB_NAME",     "stack_db"),
        "user":     os.getenv("DB_USER",     "postgres"),
        "password": os.getenv("DB_PASSWORD", "postgres"),
    }

# ── Plantilla de ejemplo ──────────────────────────────────────────────────────
PLANTILLA = {
    "ley": {
        "codigo":         "LPAC",
        "nombre":         "Ley del Procedimiento Administrativo Común de las Administraciones Públicas",
        "nombre_corto":   "Ley 39/2015",
        "tipo":           "ley_ordinaria",
        "numero_oficial": "Ley 39/2015, de 1 de octubre",
        "fecha_pub":      "2015-10-02",
        "url_boe":        "https://www.boe.es/buscar/act.php?id=BOE-A-2015-10565",
        "url_eli":        "https://www.boe.es/eli/es/l/2015/10/01/39/con"
    },
    "titulos": [
        {"numero": "PRELIMINAR", "denominacion": "Disposiciones generales",      "orden": 1},
        {"numero": "I",          "denominacion": "De los interesados en el procedimiento", "orden": 2}
    ],
    "capitulos": [
        {
            "titulo_numero": "PRELIMINAR",
            "numero":        "I",
            "denominacion":  "Objeto, ámbito de aplicación y principios generales",
            "orden":         1
        },
        {
            "titulo_numero": "I",
            "numero":        "I",
            "denominacion":  "De la capacidad de obrar y el concepto de interesado",
            "orden":         1
        }
    ],
    "secciones": [],
    "articulos": [
        {
            "numero":          "1",
            "tipo":            "articulo",
            "contenido":       "Esta Ley tiene por objeto regular los requisitos de validez y eficacia de los actos administrativos...",
            "titulo_numero":   "PRELIMINAR",
            "capitulo_numero": "I",
            "seccion_numero":  None,
            "orden_global":    1
        },
        {
            "numero":          "2",
            "tipo":            "articulo",
            "contenido":       "Las Administraciones Públicas que integran el Sector Público son...",
            "titulo_numero":   "PRELIMINAR",
            "capitulo_numero": "I",
            "seccion_numero":  None,
            "orden_global":    2
        },
        {
            "numero":          "DA-1",
            "tipo":            "disposicion_adicional",
            "contenido":       "Las referencias hechas en los textos normativos...",
            "titulo_numero":   None,
            "capitulo_numero": None,
            "seccion_numero":  None,
            "orden_global":    999
        }
    ]
}

TIPOS_VALIDOS = {
    "constitucion", "ley_organica", "ley_ordinaria",
    "real_decreto_legislativo", "real_decreto", "orden_ministerial",
    "tratado_internacional",
}

TIPOS_ARTICULO_VALIDOS = {
    "preambulo", "articulo", "disposicion_adicional",
    "disposicion_transitoria", "disposicion_derogatoria", "disposicion_final",
}


# ── Validación ────────────────────────────────────────────────────────────────

def validar(data: dict) -> None:
    """Valida la estructura del JSON antes de intentar la carga."""
    errores = []

    ley = data.get("ley", {})
    for campo in ("codigo", "nombre", "fecha_pub"):
        if not ley.get(campo):
            errores.append(f"ley.{campo} es obligatorio")

    if ley.get("tipo") and ley["tipo"] not in TIPOS_VALIDOS:
        errores.append(f"ley.tipo inválido: '{ley['tipo']}'. Válidos: {TIPOS_VALIDOS}")

    titulos_set = {t["numero"] for t in data.get("titulos", [])}
    cap_set     = set()

    for c in data.get("capitulos", []):
        if titulos_set and c.get("titulo_numero") not in titulos_set:
            errores.append(f"Capítulo '{c.get('numero')}' referencia título '{c.get('titulo_numero')}' inexistente")
        cap_set.add((c.get("titulo_numero"), c.get("numero")))

    for s in data.get("secciones", []):
        key = (s.get("titulo_numero"), s.get("capitulo_numero"))
        if key not in cap_set:
            errores.append(f"Sección '{s.get('numero')}' referencia capítulo inexistente")

    for a in data.get("articulos", []):
        if not a.get("numero") or not a.get("contenido"):
            errores.append(f"Artículo sin numero o contenido: {a}")
        if a.get("tipo") and a["tipo"] not in TIPOS_ARTICULO_VALIDOS:
            errores.append(f"Artículo '{a.get('numero')}': tipo inválido '{a['tipo']}'")

    if errores:
        raise ValueError("Errores en el JSON:\n" + "\n".join(f"  - {e}" for e in errores))


# ── Carga ─────────────────────────────────────────────────────────────────────

def cargar_ley(data: dict, conn) -> int:
    """Inserta la ley completa en normas.*. Devuelve el ley_id asignado."""
    cur = conn.cursor()
    ley = data["ley"]

    # 1. Insertar ley
    cur.execute("""
        INSERT INTO normas.leyes
            (codigo, nombre, nombre_corto, tipo, numero_oficial,
             fecha_pub, url_boe, url_eli, activa)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, true)
        RETURNING ley_id
    """, (
        ley["codigo"],
        ley["nombre"],
        ley.get("nombre_corto"),
        ley.get("tipo", "ley_ordinaria"),
        ley.get("numero_oficial"),
        ley["fecha_pub"],
        ley.get("url_boe"),
        ley.get("url_eli"),
    ))
    ley_id = cur.fetchone()[0]
    print(f"  [{ley_id}] {ley['nombre']}")

    # 2. Títulos — mapa: numero → titulo_id
    titulo_map: dict[str, int] = {}
    for t in data.get("titulos", []):
        cur.execute("""
            INSERT INTO normas.titulos (ley_id, numero, denominacion, orden)
            VALUES (%s, %s, %s, %s)
            RETURNING titulo_id
        """, (ley_id, t["numero"], t["denominacion"], t["orden"]))
        titulo_map[t["numero"]] = cur.fetchone()[0]
    print(f"  Títulos:    {len(titulo_map)}")

    # 3. Capítulos — mapa: (titulo_numero, capitulo_numero) → capitulo_id
    # Si la ley tiene capítulos pero no títulos, crear un título raíz sintético
    capitulos = data.get("capitulos", [])
    if capitulos and not titulo_map:
        cur.execute("""
            INSERT INTO normas.titulos (ley_id, numero, denominacion, orden)
            VALUES (%s, %s, %s, %s)
            RETURNING titulo_id
        """, (ley_id, "_ROOT", "[Sin título]", 0))
        titulo_map[None] = cur.fetchone()[0]

    capitulo_map: dict[tuple, int] = {}
    for c in data.get("capitulos", []):
        titulo_id = titulo_map[c["titulo_numero"]]
        cur.execute("""
            INSERT INTO normas.capitulos (titulo_id, numero, denominacion, orden)
            VALUES (%s, %s, %s, %s)
            RETURNING capitulo_id
        """, (titulo_id, c["numero"], c["denominacion"], c["orden"]))
        capitulo_map[(c["titulo_numero"], c["numero"])] = cur.fetchone()[0]
    print(f"  Capítulos:  {len(capitulo_map)}")

    # 4. Secciones — mapa: (titulo_numero, capitulo_numero, seccion_numero) → seccion_id
    seccion_map: dict[tuple, int] = {}
    for s in data.get("secciones", []):
        capitulo_id = capitulo_map[(s["titulo_numero"], s["capitulo_numero"])]
        cur.execute("""
            INSERT INTO normas.secciones (capitulo_id, numero, denominacion, orden)
            VALUES (%s, %s, %s, %s)
            RETURNING seccion_id
        """, (capitulo_id, s["numero"], s["denominacion"], s["orden"]))
        seccion_map[(s["titulo_numero"], s["capitulo_numero"], s["numero"])] = cur.fetchone()[0]
    print(f"  Secciones:  {len(seccion_map)}")

    # 5. Artículos — resolve FKs, auto-numerar orden_global si falta
    articulos = data.get("articulos", [])
    for i, a in enumerate(articulos, 1):
        if "orden_global" not in a:
            a["orden_global"] = i

    rows = []
    for a in articulos:
        t_num = a.get("titulo_numero")
        c_num = a.get("capitulo_numero")
        s_num = a.get("seccion_numero")

        titulo_id   = titulo_map.get(t_num) if t_num else None
        capitulo_id = capitulo_map.get((t_num, c_num)) if t_num and c_num else None
        seccion_id  = seccion_map.get((t_num, c_num, s_num)) if t_num and c_num and s_num else None

        rows.append((
            ley_id, titulo_id, capitulo_id, seccion_id,
            a["numero"],
            a.get("tipo", "articulo"),
            a["contenido"],
            a["orden_global"],
        ))

    execute_values(cur, """
        INSERT INTO normas.articulos
            (ley_id, titulo_id, capitulo_id, seccion_id,
             numero, tipo, contenido, orden_global)
        VALUES %s
    """, rows)
    print(f"  Artículos:  {len(rows)}")

    # 6. Estimar token_count y decidir estrategia RAG
    cur.execute("""
        UPDATE normas.leyes
        SET token_count = (
            SELECT SUM(LENGTH(contenido)) / 4
            FROM normas.articulos WHERE ley_id = %s
        )
        WHERE ley_id = %s
        RETURNING token_count
    """, (ley_id, ley_id))
    tokens = cur.fetchone()[0] or 0
    estrategia = "full-text (<60K)" if tokens < 60_000 else "jerárquico RAG (>60K)"
    print(f"  Tokens est: {tokens:,} → {estrategia}")

    return ley_id


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Carga una ley en normas.* desde un archivo JSON.")
    parser.add_argument("archivo", nargs="?",
                        help="Ruta al archivo JSON de la ley")
    parser.add_argument("--embeddings", action="store_true",
                        help="Generar embeddings tras la carga")
    parser.add_argument("--force", action="store_true",
                        help="Eliminar la ley existente si el código ya existe")
    parser.add_argument("--ejemplo", action="store_true",
                        help="Imprimir una plantilla JSON y salir")
    parser.add_argument("--supabase", action="store_true",
                        help="Conectar a Supabase (lee .streamlit/secrets.toml)")
    args = parser.parse_args()

    if args.ejemplo:
        print(json.dumps(PLANTILLA, ensure_ascii=False, indent=2))
        return

    if args.supabase:
        _load_supabase_secrets()
    else:
        os.environ.setdefault("DB_HOST",     "localhost")
        os.environ.setdefault("DB_PORT",     "5432")
        os.environ.setdefault("DB_NAME",     "stack_db")
        os.environ.setdefault("DB_USER",     "postgres")
        os.environ.setdefault("DB_PASSWORD", "postgres")

    if not args.archivo:
        parser.error("Indica la ruta al JSON (o usa --ejemplo para ver la plantilla)")

    if not os.path.exists(args.archivo):
        raise SystemExit(f"No se encuentra: '{args.archivo}'")

    with open(args.archivo, encoding="utf-8") as f:
        data = json.load(f)

    # Validar antes de conectar a la BD
    validar(data)

    conn = psycopg2.connect(**_db_config())
    try:
        # Comprobar si ya existe
        with conn.cursor() as cur:
            cur.execute("SELECT ley_id FROM normas.leyes WHERE codigo = %s",
                        (data["ley"]["codigo"],))
            existing = cur.fetchone()

        if existing:
            if not args.force:
                raise SystemExit(
                    f"La ley '{data['ley']['codigo']}' ya existe (ley_id={existing[0]}).\n"
                    f"Usa --force para eliminarla y recargar.")
            with conn.cursor() as cur:
                cur.execute("DELETE FROM normas.leyes WHERE codigo = %s RETURNING ley_id",
                            (data["ley"]["codigo"],))
                deleted = cur.fetchone()
                print(f"  Ley anterior eliminada (ley_id={deleted[0]})")
            conn.commit()

        print(f"\nCargando: {data['ley']['nombre']}")
        print("─" * 50)

        ley_id = cargar_ley(data, conn)
        conn.commit()

        print("─" * 50)
        print(f"Completado. ley_id = {ley_id}\n")

        if args.embeddings:
            print("Generando embeddings...\n")
            script = os.path.join(os.path.dirname(__file__), "generate_embeddings.py")
            subprocess.run([sys.executable, script], check=True)

    except (ValueError, psycopg2.Error) as e:
        conn.rollback()
        raise SystemExit(f"Error: {e}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
