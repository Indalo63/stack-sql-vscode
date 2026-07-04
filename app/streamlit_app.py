import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

import time
import anthropic
import streamlit as st
from app.qa_pipeline import run_qa
from app.test_pipeline import run_gentest
from app.retrieval import get_leyes_disponibles, get_oposiciones
from app.config import ANTHROPIC_API_KEY, CLAUDE_MODEL
from app.db import get_connection
from scripts.build_test_bank import (
    _fetch_articles, _fetch_few_shots, _build_prompt,
    _parse_and_validate, _has_numbered_paragraphs, _save,
)

st.set_page_config(
    page_title="Asistente Jurídico",
    page_icon="⚖️",
    layout="centered",
)

# ── Autenticación ─────────────────────────────────────────────────────────────
user = st.user
logged_in = "email" in user

# ── Carga de datos ────────────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def _cargar_oposiciones():
    return get_oposiciones()

@st.cache_data(ttl=300)
def _cargar_leyes(oposicion_id: int | None):
    return get_leyes_disponibles(oposicion_id)

try:
    oposiciones = _cargar_oposiciones()
except Exception as e:
    st.error(f"No se puede conectar a la base de datos: {e}")
    st.stop()

# ── Sidebar ────────────────────────────────────────────────────────────────────
ops_opciones = {f"{o['nombre_corto'] or o['codigo']}": o for o in oposiciones}
op_seleccion = st.sidebar.selectbox("Oposición", list(ops_opciones.keys()))
oposicion_seleccionada = ops_opciones[op_seleccion]
oposicion_id = oposicion_seleccionada["oposicion_id"]

try:
    leyes = _cargar_leyes(oposicion_id)
except Exception as e:
    st.error(f"Error al cargar las leyes: {e}")
    st.stop()

if not leyes:
    st.warning("Esta oposición no tiene leyes asignadas. Ejecuta la migración 025.")
    st.stop()

opciones = {f"{l['codigo']} — {l['nombre_corto'] or l['nombre']}": l for l in leyes}

seleccion = st.sidebar.selectbox("Ley", list(opciones.keys()))
ley_seleccionada = opciones[seleccion]
ley_id     = ley_seleccionada["ley_id"]
ley_nombre = ley_seleccionada["nombre"]

modos = ["Q&A", "Generar test"]
if logged_in:
    modos.append("Editor")

modo = st.sidebar.radio("Modo", modos)

st.sidebar.markdown("---")
if logged_in:
    st.sidebar.markdown(f"👤 {user["email"]}")
    if st.sidebar.button("Cerrar sesión"):
        st.logout()
else:
    if st.sidebar.button("Acceso Editor (Google)"):
        st.login("google")

# ── Cabecera ──────────────────────────────────────────────────────────────────
st.title("⚖️ Asistente Jurídico")
st.caption("Búsqueda semántica + Claude")

# ── Helpers BD — Editor ───────────────────────────────────────────────────────
def _get_pending(ley_id: int) -> list[dict]:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT pregunta_id, articulo, pregunta,
                       opcion_a, opcion_b, opcion_c, opcion_d,
                       correcta, explicacion
                FROM normas.preguntas_test
                WHERE ley_id   = %s
                  AND fuente   = 'ia'
                  AND revisada = FALSE
                ORDER BY generada_en DESC
            """, (ley_id,))
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]


def _approve(pregunta_id: int, email: str, data: dict) -> None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE normas.preguntas_test SET
                    pregunta     = %s,
                    opcion_a     = %s,
                    opcion_b     = %s,
                    opcion_c     = %s,
                    opcion_d     = %s,
                    correcta     = %s,
                    explicacion  = %s,
                    revisada     = TRUE,
                    revisado_por = %s,
                    revisado_en  = NOW()
                WHERE pregunta_id = %s
            """, (
                data["pregunta"],
                data["opcion_a"], data["opcion_b"],
                data["opcion_c"], data["opcion_d"],
                data["correcta"], data["explicacion"],
                email, pregunta_id,
            ))
        conn.commit()


def _reject(pregunta_id: int) -> None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM normas.preguntas_test WHERE pregunta_id = %s",
                (pregunta_id,)
            )
        conn.commit()


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
elif modo == "Generar test":
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

# ── Modo Editor ────────────────────────────────────────────────────────────────
elif modo == "Editor":
    if not logged_in:
        st.warning("Esta sección requiere autenticación con Google.")
        if st.button("Iniciar sesión con Google", type="primary"):
            st.login("google")
        st.stop()

    st.header("Editor de preguntas")
    st.caption(f"Sesión activa: {user["email"]}")

    tab_gen, tab_rev = st.tabs(["Generar", "Revisar"])

    # ── Tab Generar ───────────────────────────────────────────────────────────
    with tab_gen:
        st.subheader(f"Generar preguntas — {ley_nombre}")
        col_n, col_max = st.columns(2)
        with col_n:
            n_gen = st.slider("Número de preguntas", min_value=1, max_value=50, value=10,
                              key="editor_n_gen")
        with col_max:
            max_por_art = st.slider("Máximo por artículo", min_value=1, max_value=5, value=1,
                                    key="editor_max_art",
                                    help="Cuántas preguntas IA puede tener un mismo artículo (pendientes + aprobadas)")

        if st.button("Generar y guardar en BD", type="primary", key="btn_generar"):
            arts = _fetch_articles(ley_id, n_gen, max_por_art)
            if not arts:
                st.info("No hay artículos nuevos que procesar en esta ley.")
            else:
                few_shots = _fetch_few_shots(ley_id)
                client    = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
                progress  = st.progress(0, text="Iniciando generación…")
                ok = err  = 0

                for i, art in enumerate(arts, 1):
                    tiene_apartados = _has_numbered_paragraphs(art["contenido"])
                    try:
                        resp = client.messages.create(
                            model=CLAUDE_MODEL,
                            max_tokens=800,
                            messages=_build_prompt(
                                art, ley_nombre,
                                few_shots=few_shots,
                                tiene_apartados=tiene_apartados,
                            ),
                        )
                        parsed = _parse_and_validate(resp.content[0].text)
                        _save(ley_id, art, parsed)
                        ok += 1
                    except Exception as e:
                        err += 1
                        st.warning(f"Art. {art['numero']}: {e}")

                    progress.progress(i / len(arts),
                                      text=f"Generando… {i}/{len(arts)}")
                    if i < len(arts):
                        time.sleep(0.5)

                progress.empty()
                if ok:
                    st.success(f"{ok} pregunta{'s' if ok > 1 else ''} guardada{'s' if ok > 1 else ''} en BD.")
                if err:
                    st.error(f"{err} error{'es' if err > 1 else ''} durante la generación.")
                st.cache_data.clear()

    # ── Tab Revisar ───────────────────────────────────────────────────────────
    with tab_rev:
        st.subheader(f"Pendientes de revisión — {ley_nombre}")

        pending = _get_pending(ley_id)

        if not pending:
            st.info("No hay preguntas pendientes de revisión para esta ley.")
        else:
            st.caption(f"{len(pending)} pregunta{'s' if len(pending) > 1 else ''} pendiente{'s' if len(pending) > 1 else ''}")

            for p in pending:
                pid = p["pregunta_id"]
                with st.expander(f"Art. {p['articulo']} — {p['pregunta'][:80]}…"):
                    pregunta    = st.text_area("Enunciado",    value=p["pregunta"],    key=f"preg_{pid}")
                    col1, col2  = st.columns(2)
                    with col1:
                        opcion_a = st.text_input("a)", value=p["opcion_a"], key=f"a_{pid}")
                        opcion_b = st.text_input("b)", value=p["opcion_b"], key=f"b_{pid}")
                    with col2:
                        opcion_c = st.text_input("c)", value=p["opcion_c"], key=f"c_{pid}")
                        opcion_d = st.text_input("d)", value=p["opcion_d"], key=f"d_{pid}")
                    correcta    = st.selectbox(
                        "Correcta", ["a", "b", "c", "d"],
                        index=["a", "b", "c", "d"].index(p["correcta"]),
                        key=f"cor_{pid}",
                    )
                    explicacion = st.text_area("Explicación", value=p.get("explicacion", ""),
                                               key=f"exp_{pid}")

                    col_ok, col_ko = st.columns(2)
                    with col_ok:
                        if st.button("✅ Aprobar", key=f"ok_{pid}", type="primary"):
                            _approve(pid, user["email"], {
                                "pregunta":    pregunta,
                                "opcion_a":    opcion_a,
                                "opcion_b":    opcion_b,
                                "opcion_c":    opcion_c,
                                "opcion_d":    opcion_d,
                                "correcta":    correcta,
                                "explicacion": explicacion,
                            })
                            st.success("Aprobada y guardada.")
                            st.rerun()
                    with col_ko:
                        if st.button("❌ Rechazar", key=f"ko_{pid}"):
                            _reject(pid)
                            st.warning("Pregunta eliminada.")
                            st.rerun()
