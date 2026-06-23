#!/usr/bin/env python3
"""
CLI modo generación de preguntas tipo test.

Uso:
  python scripts/gentest.py --n 5                        # 5 preguntas aleatorias (CE)
  python scripts/gentest.py --titulo 1 --n 10            # 10 preguntas del Título I
  python scripts/gentest.py --capitulo 2 --n 3           # 3 preguntas del Capítulo II
  python scripts/gentest.py --ley-id 2 --n 5             # de otra ley cargada

Variables de entorno requeridas:
  ANTHROPIC_API_KEY
"""

import sys
import os
import argparse

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv
load_dotenv()

from app.test_pipeline import run_gentest
from app.retrieval import get_ley_info


def main():
    parser = argparse.ArgumentParser(description="Genera preguntas tipo test a partir de una ley.")
    parser.add_argument("--ley-id",   type=int, default=1,    help="ID de la ley (default: 1 = CE1978)")
    parser.add_argument("--titulo",   type=int, default=None, help="ID del título")
    parser.add_argument("--capitulo", type=int, default=None, help="ID del capítulo")
    parser.add_argument("--n",        type=int, default=5,    help="Número de preguntas (default: 5)")
    args = parser.parse_args()

    ley = get_ley_info(args.ley_id)
    print(f"\nGenerando {args.n} pregunta(s) tipo test — {ley['nombre']}\n")

    preguntas = run_gentest(
        ley_id=args.ley_id,
        ley_nombre=ley["nombre"],
        titulo_id=args.titulo,
        capitulo_id=args.capitulo,
        n=args.n,
    )

    for i, p in enumerate(preguntas, 1):
        if "error" in p:
            print(f"[{i}] Art. {p['articulo']} — ERROR: {p['error']}\n")
            continue
        print(f"[{i}] Artículo {p['articulo']}")
        print(f"    {p['pregunta']}")
        for letra, texto in p["opciones"].items():
            marca = " ✓" if letra == p["correcta"] else ""
            print(f"    {letra.lower()}) {texto}{marca}")
        print(f"    → {p['explicacion']}\n")


if __name__ == "__main__":
    main()
