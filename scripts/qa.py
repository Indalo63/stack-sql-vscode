#!/usr/bin/env python3
"""
CLI modo Q&A.

Uso:
  python scripts/qa.py "¿Qué dice la Constitución sobre la libertad de expresión?"

Variables de entorno requeridas:
  OPENAI_API_KEY
  ANTHROPIC_API_KEY
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.qa_pipeline import run_qa


def main():
    if len(sys.argv) < 2:
        print("Uso: python scripts/qa.py \"tu pregunta aquí\"")
        sys.exit(1)

    pregunta = " ".join(sys.argv[1:])
    print(f"\nPregunta: {pregunta}\n")
    print("Buscando artículos relevantes y generando respuesta...\n")

    respuesta = run_qa(pregunta)
    print(respuesta)


if __name__ == "__main__":
    main()
