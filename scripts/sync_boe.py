"""
Sincronización incremental con el BOE.

Para cada ley activa en la BD:
  1. Descarga el texto consolidado desde url_eli
  2. Calcula SHA-256 del HTML
  3. Si el hash es idéntico al almacenado → sin cambios, pasa a la siguiente
  4. Si difiere → re-parsea, hace diff artículo a artículo y actualiza solo los que cambiaron
  5. Regenera embeddings de los artículos modificados/nuevos
  6. Actualiza content_hash y fecha_actualizacion

Uso:
  python3 scripts/sync_boe.py               # todas las leyes activas
  python3 scripts/sync_boe.py --ley-id 4    # solo una ley
  python3 scripts/sync_boe.py --forzar      # re-procesa aunque el hash no cambie
"""

import sys
import os
import hashlib
import argparse
import subprocess
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv
load_dotenv()

import psycopg2
from scripts.parse_boe import fetch_html, parsear

DB_CONFIG = {
    "host":     os.getenv("DB_HOST",     "localhost"),
    "port":     int(os.getenv("DB_PORT", "5432")),
    "dbname":   os.getenv("DB_NAME",     "stack_db"),
    "user":     os.getenv("DB_USER",     "postgres"),
    "password": os.getenv("DB_PASSWORD", "postgres"),
}

LOG_FILE = os.path.join(os.path.dirname(__file__), "..", "logs", "sync_boe.log")


def _log(msg: str):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    linea = f"[{ts}] {msg}"
    print(linea)
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(linea + "\n")


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _get_leyes(cur, ley_id: int | None) -> list[dict]:
    if ley_id:
        cur.execute("""
            SELECT ley_id, codigo, nombre, nombre_corto, url_eli, content_hash
            FROM normas.leyes
            WHERE ley_id = %s AND activa = true AND url_eli IS NOT NULL
        """, (ley_id,))
    else:
        cur.execute("""
            SELECT ley_id, codigo, nombre, nombre_corto, url_eli, content_hash
            FROM normas.leyes
            WHERE activa = true AND url_eli IS NOT NULL
            ORDER BY ley_id
        """)
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, row)) for row in cur.fetchall()]


def _articulos_bd(cur, ley_id: int) -> dict[tuple, dict]:
    """Devuelve {(numero, tipo): {articulo_id, contenido}} para la ley."""
    cur.execute("""
        SELECT articulo_id, numero, tipo, contenido
        FROM normas.articulos
        WHERE ley_id = %s
    """, (ley_id,))
    return {
        (r[1], r[2]): {"articulo_id": r[0], "contenido": r[3]}
        for r in cur.fetchall()
    }


def _titulo_id(cur, ley_id: int, numero: str | None) -> int | None:
    if not numero:
        return None
    cur.execute(
        "SELECT titulo_id FROM normas.titulos WHERE ley_id = %s AND numero = %s",
        (ley_id, numero))
    row = cur.fetchone()
    return row[0] if row else None


def _capitulo_id(cur, titulo_id: int | None, numero: str | None) -> int | None:
    if not titulo_id or not numero:
        return None
    cur.execute(
        "SELECT capitulo_id FROM normas.capitulos WHERE titulo_id = %s AND numero = %s",
        (titulo_id, numero))
    row = cur.fetchone()
    return row[0] if row else None


def _orden_global_max(cur, ley_id: int) -> int:
    cur.execute(
        "SELECT COALESCE(MAX(orden_global), 0) FROM normas.articulos WHERE ley_id = %s",
        (ley_id,))
    return cur.fetchone()[0]


def sync_ley(ley: dict, forzar: bool = False) -> dict:
    """
    Sincroniza una ley. Devuelve resumen de cambios:
    {"sin_cambios": bool, "actualizados": N, "nuevos": N, "eliminados": N}
    """
    _log(f"Comprobando [{ley['ley_id']}] {ley['nombre_corto']} ← {ley['url_eli']}")

    try:
        html = fetch_html(ley["url_eli"])
    except Exception as e:
        _log(f"  ERROR descargando: {e}")
        return {"error": str(e)}

    nuevo_hash = _sha256(html)

    conn = psycopg2.connect(**DB_CONFIG)
    cur  = conn.cursor()

    if not forzar and ley["content_hash"] == nuevo_hash:
        _log("  Sin cambios (hash idéntico)")
        cur.close()
        conn.close()
        return {"sin_cambios": True}

    _log("  Hash diferente — analizando cambios...")

    # Re-parsear
    try:
        datos = parsear(html, ley["codigo"], url=ley["url_eli"])
    except Exception as e:
        _log(f"  ERROR parseando: {e}")
        cur.close()
        conn.close()
        return {"error": str(e)}

    arts_bd  = _articulos_bd(cur, ley["ley_id"])
    arts_new = {(a["numero"], a["tipo"]): a for a in datos["articulos"]}

    actualizados = nuevos = eliminados = 0

    # — Artículos modificados o nuevos —
    orden_max = _orden_global_max(cur, ley["ley_id"])
    for clave, art_new in arts_new.items():
        if clave in arts_bd:
            existing = arts_bd[clave]
            if existing["contenido"] != art_new["contenido"]:
                # Actualizar contenido y limpiar embedding para regenerar
                cur.execute("""
                    UPDATE normas.articulos
                    SET contenido = %s, embedding = NULL
                    WHERE articulo_id = %s
                """, (art_new["contenido"], existing["articulo_id"]))
                actualizados += 1
        else:
            # Artículo nuevo: resolver FK de título/capítulo
            tid = _titulo_id(cur, ley["ley_id"], art_new.get("titulo_numero"))
            cid = _capitulo_id(cur, tid, art_new.get("capitulo_numero"))
            orden_max += 1
            cur.execute("""
                INSERT INTO normas.articulos
                  (ley_id, titulo_id, capitulo_id, numero, tipo, contenido, orden_global)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (ley["ley_id"], tid, cid,
                  art_new["numero"], art_new["tipo"],
                  art_new["contenido"], orden_max))
            nuevos += 1

    # — Artículos eliminados (en BD pero no en nuevo texto) —
    for clave, existing in arts_bd.items():
        if clave not in arts_new:
            cur.execute(
                "DELETE FROM normas.articulos WHERE articulo_id = %s",
                (existing["articulo_id"],))
            eliminados += 1

    # — Actualizar hash y fecha —
    cur.execute("""
        UPDATE normas.leyes
        SET content_hash = %s, fecha_actualizacion = %s
        WHERE ley_id = %s
    """, (nuevo_hash, datetime.now(timezone.utc), ley["ley_id"]))

    conn.commit()
    cur.close()
    conn.close()

    _log(f"  Actualizados: {actualizados} | Nuevos: {nuevos} | Eliminados: {eliminados}")

    # Regenerar embeddings si hay artículos modificados o nuevos
    if actualizados + nuevos > 0:
        _log("  Regenerando embeddings...")
        script = os.path.join(os.path.dirname(__file__), "generate_embeddings.py")
        subprocess.run([sys.executable, script], check=False)

    return {"sin_cambios": False, "actualizados": actualizados,
            "nuevos": nuevos, "eliminados": eliminados}


def main():
    parser = argparse.ArgumentParser(description="Sincroniza leyes con el BOE consolidado")
    parser.add_argument("--ley-id", type=int, default=None,
                        help="Sincronizar solo esta ley (default: todas)")
    parser.add_argument("--forzar", action="store_true",
                        help="Re-procesar aunque el hash no haya cambiado")
    args = parser.parse_args()

    conn = psycopg2.connect(**DB_CONFIG)
    cur  = conn.cursor()
    leyes = _get_leyes(cur, args.ley_id)
    cur.close()
    conn.close()

    if not leyes:
        _log("No se encontraron leyes activas con url_eli.")
        return

    _log(f"Iniciando sincronización — {len(leyes)} ley(es)")
    _log("=" * 60)

    resumen = {"sin_cambios": 0, "actualizadas": 0, "errores": 0}
    for ley in leyes:
        resultado = sync_ley(ley, forzar=args.forzar)
        if "error" in resultado:
            resumen["errores"] += 1
        elif resultado.get("sin_cambios"):
            resumen["sin_cambios"] += 1
        else:
            resumen["actualizadas"] += 1

    _log("=" * 60)
    _log(f"Fin — sin cambios: {resumen['sin_cambios']} | "
         f"actualizadas: {resumen['actualizadas']} | "
         f"errores: {resumen['errores']}")


if __name__ == "__main__":
    main()
