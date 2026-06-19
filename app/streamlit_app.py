import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

import streamlit as st
from app.qa_pipeline import run_qa
from app.test_pipeline import run_gentest

st.set_page_config(
    page_title="Q&A Jurídico — Constitución Española",
    page_icon="⚖️",
    layout="centered",
)

st.title("⚖️ Asistente Jurídico")
st.caption("Constitución Española · Búsqueda semántica + Claude")

modo = st.sidebar.radio("Modo", ["Q&A", "Generar test"])

# ── Modo Q&A ──────────────────────────────────────────────────────────────────
if modo == "Q&A":
    st.header("Consulta jurídica")
    pregunta = st.text_area(
        "Escribe tu pregunta sobre la Constitución Española:",
        placeholder="¿Qué derechos fundamentales reconoce la Constitución?",
        height=100,
    )
    if st.button("Consultar", type="primary", disabled=not pregunta.strip()):
        with st.spinner("Buscando artículos relevantes y generando respuesta…"):
            try:
                respuesta = run_qa(pregunta.strip())
                st.markdown("### Respuesta")
                st.markdown(respuesta)
            except Exception as e:
                st.error(f"Error al procesar la consulta: {e}")

# ── Modo Gentest ───────────────────────────────────────────────────────────────
else:
    st.header("Generador de preguntas tipo test")
    n = st.slider("Número de preguntas", min_value=1, max_value=10, value=3)

    if st.button("Generar preguntas", type="primary"):
        with st.spinner(f"Generando {n} pregunta{'s' if n > 1 else ''}…"):
            try:
                preguntas = run_gentest(n=n)
                for i, p in enumerate(preguntas, 1):
                    if "error" in p:
                        st.warning(f"Pregunta {i} — Art. {p.get('articulo', '?')}: {p['error']}")
                        continue
                    with st.expander(f"**Pregunta {i} — Art. {p['articulo']}**  {p['pregunta']}", expanded=True):
                        correcta = p.get("correcta", "")
                        for letra, texto in p["opciones"].items():
                            if letra == correcta:
                                st.markdown(f"**{letra}) {texto} ✓**")
                            else:
                                st.markdown(f"{letra}) {texto}")
                        st.info(f"**Explicación:** {p['explicacion']}")
            except Exception as e:
                st.error(f"Error al generar las preguntas: {e}")
