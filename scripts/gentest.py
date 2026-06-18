#!/usr/bin/env python3
"""
CLI modo generación de preguntas tipo test.

Uso:
  python scripts/gentest.py --n 5                   # 5 preguntas aleatorias
  python scripts/gentest.py --titulo 1 --n 10       # 10 preguntas del Título I
  python scripts/gentest.py --capitulo 2 --n 3      # 3 preguntas del Capítulo II

Variables de entorno requeridas:
  ANTHROPIC_API_KEY
"""

import sys
import os
import json
import argparse

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.test_pipeline import run_gentest


def main():
    parser = argparse.ArgumentParser(description="Genera preguntas tipo test sobre la CE.")
    parser.add_argument("--titulo",   type=int, default=None, help="ID del título (1-10)")
    parser.add_argument("--capitulo", type=int, default=None, help="ID del capítulo")
    parser.add_argument("--n",        type=int, default=5,    help="Número de preguntas (default: 5)")
    args = parser.parse_args()

    print(f"\nGenerando {args.n} pregunta(s) tipo test...\n")

    preguntas = run_gentest(titulo_id=args.titulo, capitulo_id=args.capitulo, n=args.n)

    for i, p in enumerate(preguntas, 1):
        if "error" in p:
            print(f"[{i}] Art. {p['articulo']} — ERROR: {p['error']}\n")
            continue
        print(f"[{i}] Artículo {p['articulo']}")
        print(f"    {p['pregunta']}")
        for letra, texto in p["opciones"].items():
            marca = " ✓" if letra == p["correcta"] else ""
            print(f"    {letra}) {texto}{marca}")
        print(f"    → {p['explicacion']}\n")


if __name__ == "__main__":
    main()
