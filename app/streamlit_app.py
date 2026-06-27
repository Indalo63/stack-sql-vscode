import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

import streamlit as st
from app.qa_pipeline import run_qa
from app.test_pipeline import run_gentest
from app.retrieval import get_leyes_disponibles

st.set_page_config(
    page_title="Asistente Jurídico",
    page_icon="⚖️",
    layout="centered",
)

st.title("⚖️ Asistente Jurídico")
st.caption("Búsqueda semántica + Claude")

# ── Selector de ley ────────────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def _cargar_leyes():
    return get_leyes_disponibles()

try:
    leyes = _cargar_leyes()
except Exception as e:
    st.error(f"No se puede conectar a la base de datos: {e}")
    st.stop()

opciones = {f"{l['nombre_corto'] or l['codigo']} — {l['nombre']}": l for l in leyes}
seleccion = st.sidebar.selectbox("Ley", list(opciones.keys()))
ley_seleccionada = opciones[seleccion]
ley_id     = ley_seleccionada["ley_id"]
ley_nombre = ley_seleccionada["nombre"]

modo = st.sidebar.radio("Modo", ["Q&A", "Generar test"])

# ── Modo Q&A ──────────────────────────────────────────────────────────────────
if modo == "Q&A":
    st.header("Consulta jurídica")

    for key in ("qa_respuesta", "qa_pregunta"):
        if key not in st.session_state:
            st.session_state[key] = ""

    pregunta = st.text_area(
        f"Escribe tu pregunta sobre {ley_nombre}:",
        placeholder="¿Qué derechos fundamentales reconoce?",
        height=100,
    )
    if st.button("Consultar", type="primary", disabled=not pregunta.strip()):
        with st.spinner("Buscando artículos relevantes y generando respuesta…"):
            try:
                respuesta = run_qa(pregunta.strip(), ley_id=ley_id)
                st.session_state.qa_pregunta  = pregunta.strip()
                st.session_state.qa_respuesta = respuesta
            except Exception as e:
                st.error(f"Error al procesar la consulta: {e}")

    if st.session_state.qa_respuesta:
        st.markdown("### Respuesta")
        st.markdown(st.session_state.qa_respuesta)

# ── Modo Gentest ───────────────────────────────────────────────────────────────
else:
    st.header("Generador de preguntas tipo test")

    if "gentest_preguntas" not in st.session_state:
        st.session_state.gentest_preguntas = []

    n = st.slider("Número de preguntas", min_value=1, max_value=10, value=3)

    if st.button("Generar preguntas", type="primary"):
        with st.spinner(f"Generando {n} pregunta{'s' if n > 1 else ''}…"):
            try:
                st.session_state.gentest_preguntas = run_gentest(
                    ley_id=ley_id, ley_nombre=ley_nombre, n=n
                )
            except Exception as e:
                st.error(f"Error al generar las preguntas: {e}")

    for i, p in enumerate(st.session_state.gentest_preguntas, 1):
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
