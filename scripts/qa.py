#!/usr/bin/env python3
"""
CLI modo Q&A.

Uso:
  python scripts/qa.py "¿Qué dice la Constitución sobre la libertad de expresión?"
  python scripts/qa.py --ley-id 2 "¿Qué establece el artículo 3?"

Variables de entorno requeridas:
  OPENAI_API_KEY
  ANTHROPIC_API_KEY
"""

import sys
import os
import argparse

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv
load_dotenv()

from app.qa_pipeline import run_qa


def main():
    parser = argparse.ArgumentParser(description="Consulta jurídica por Q&A semántico.")
    parser.add_argument("pregunta", nargs="+", help="Pregunta en lenguaje natural")
    parser.add_argument("--ley-id", type=int, default=1,
                        help="ID de la ley a consultar (default: 1 = CE1978)")
    args = parser.parse_args()

    pregunta = " ".join(args.pregunta)
    print(f"\nPregunta: {pregunta}\n")
    print("Buscando artículos relevantes y generando respuesta...\n")

    respuesta = run_qa(pregunta, ley_id=args.ley_id)
    print(respuesta)


if __name__ == "__main__":
    main()
