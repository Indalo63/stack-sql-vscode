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
from app.retrieval import (get_leyes_disponibles, get_oposiciones,
                           get_bloques_por_oposicion,
                           get_preguntas_sm2, update_progreso_sm2,
                           get_fase_alumno, get_stats_alumno,
                           get_preguntas_adaptativo, get_preguntas_prueba_nivel,
                           get_preguntas_simulacro_personal, calificar_simulacro,
                           guardar_resultado_simulacro, get_historial_simulacros)
from app.config import ANTHROPIC_API_KEY, CLAUDE_MODEL
from app.auth_alumno import registrar_alumno, login_alumno
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

_NOMBRES_BLOQUE = {
    "I":   "I — Organización del Estado",
    "II":  "II — Unión Europea",
    "III": "III — Políticas Públicas",
    "IV":  "IV — Derecho Administrativo",
    "V":   "V — Recursos Humanos",
    "VI":  "VI — Gestión Financiera",
}

# ── Autenticación ─────────────────────────────────────────────────────────────
user = st.user
logged_in = "email" in user

# ── Carga de datos ────────────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def _cargar_oposiciones():
    return get_oposiciones()

@st.cache_data(ttl=300)
def _cargar_bloques(oposicion_id: int):
    return get_bloques_por_oposicion(oposicion_id)

@st.cache_data(ttl=300)
def _cargar_leyes(oposicion_id: int | None, bloques: tuple[str, ...] | None = None,
                  excluir_test: bool = False):
    return get_leyes_disponibles(oposicion_id, bloques, excluir_test=excluir_test)

try:
    oposiciones = _cargar_oposiciones()
except Exception as e:
    st.error(f"No se puede conectar a la base de datos: {e}")
    st.stop()

# ── Flujo Alumno (Supabase Auth) ───────────────────────────────────────────────
def _mensaje_error_alumno(e: Exception, accion: str) -> str:
    texto = str(e).lower()
    if "already registered" in texto or "already exists" in texto or "already been" in texto:
        return "Este email ya tiene una cuenta. Prueba a iniciar sesión."
    if "invalid login credentials" in texto or "invalid_credentials" in texto:
        return "Email o contraseña incorrectos."
    if "password" in texto and ("short" in texto or "at least" in texto or "6 characters" in texto):
        return "La contraseña es demasiado corta (mínimo 6 caracteres)."
    accion_txt = "registro" if accion == "Registrarse" else "inicio de sesión"
    return f"No se pudo completar el {accion_txt}: {e}"


def _render_preguntas(preguntas: list[dict], respuestas: dict, key_prefix: str,
                      respondido: bool) -> None:
    """Renderiza una tanda de preguntas a/b/c/d; si `respondido`, muestra corrección."""
    for i, p in enumerate(preguntas, 1):
        pid      = p["pregunta_id"]
        opciones = {
            "a": p["opcion_a"], "b": p["opcion_b"],
            "c": p["opcion_c"], "d": p["opcion_d"],
        }
        st.markdown(f"**{i}. [{p['ley_codigo']}] {p['pregunta']}**")

        if not respondido:
            resp = st.radio(
                "",
                options=list(opciones.keys()),
                format_func=lambda x, op=opciones: f"{x}) {op[x]}",
                key=f"{key_prefix}_{pid}",
                index=None,
                label_visibility="collapsed",
            )
            respuestas[pid] = resp
        else:
            correcta = p["correcta"]
            elegida  = respuestas.get(pid)
            for letra, texto in opciones.items():
                if letra == correcta:
                    st.markdown(f"✅ **{letra}) {texto}**")
                elif letra == elegida:
                    st.markdown(f"❌ {letra}) {texto}")
                else:
                    st.markdown(f"{letra}) {texto}")
            if p.get("explicacion"):
                st.info(p["explicacion"])
        st.divider()


def _modo_prueba_nivel(oposicion_id: int, user_id: str) -> None:
    st.header("Prueba de nivel")
    st.caption(
        "40 preguntas repartidas según el peso oficial de cada bloque, en "
        "dificultad creciente. Al terminar verás tu informe de partida."
    )

    if "nivel" not in st.session_state:
        st.session_state.nivel = {"preguntas": [], "respuestas": {}, "respondido": False}
    nivel = st.session_state.nivel

    if not nivel["preguntas"]:
        if st.button("Empezar prueba de nivel", type="primary"):
            preguntas = get_preguntas_prueba_nivel(oposicion_id, n=40)
            if not preguntas:
                st.warning(
                    "Todavía no hay preguntas suficientes en el banco para "
                    "hacer la prueba de nivel de esta oposición."
                )
            else:
                nivel["preguntas"]  = preguntas
                nivel["respuestas"] = {}
                nivel["respondido"] = False
                st.rerun()
        return

    if not nivel["respondido"]:
        _render_preguntas(nivel["preguntas"], nivel["respuestas"], "nivel", respondido=False)
        respondidas = sum(1 for v in nivel["respuestas"].values() if v is not None)
        st.caption(f"{respondidas} / {len(nivel['preguntas'])} respondidas")
        if st.button("Comprobar respuestas", type="primary"):
            for p in nivel["preguntas"]:
                elegida = nivel["respuestas"].get(p["pregunta_id"])
                if elegida is not None:
                    update_progreso_sm2(user_id, p["pregunta_id"], elegida == p["correcta"])
            for bloque in get_bloques_por_oposicion(oposicion_id):
                get_fase_alumno(user_id, oposicion_id, bloque)
            nivel["respondido"] = True
            st.rerun()
    else:
        _render_preguntas(nivel["preguntas"], nivel["respuestas"], "nivel", respondido=True)
        ok = sum(
            1 for p in nivel["preguntas"]
            if nivel["respuestas"].get(p["pregunta_id"]) == p["correcta"]
        )
        st.success(f"Resultado: **{ok} / {len(nivel['preguntas'])}** correctas")

        st.subheader("Informe de partida")
        stats = get_stats_alumno(user_id, oposicion_id)
        for b in stats["bloques"]:
            nombre = _NOMBRES_BLOQUE.get(b["bloque"], b["bloque"])
            st.markdown(
                f"**{nombre}** — {b['porcentaje_acierto']}% de acierto "
                f"(fase: {b['fase']})"
            )
        st.info(stats["proxima_accion"]["motivo"])

        if st.button("Ir a Repaso →", type="primary"):
            st.session_state.nivel = {"preguntas": [], "respuestas": {}, "respondido": False}
            st.session_state.modo_alumno_radio = "Repaso"
            st.rerun()


def _panel_estado_bloques(stats: dict) -> None:
    """Momento 1: estado actual por bloque (sin desglose débiles/oficial/nueva ni fase)."""
    if not stats["bloques"]:
        st.caption("Todavía no tienes datos de progreso. Empieza una tanda para ver tu evolución.")
        return
    for b in stats["bloques"]:
        nombre = _NOMBRES_BLOQUE.get(b["bloque"], b["bloque"])
        estado = "✅ estudiado" if b["estudiado"] else "en progreso"
        st.markdown(f"**{nombre}** — {b['porcentaje_acierto']}% de acierto ({estado})")


def _modo_repaso(oposicion_id: int, user_id: str, stats: dict) -> None:
    st.header("Repaso adaptativo")

    bloques_disponibles = get_bloques_por_oposicion(oposicion_id)
    if not bloques_disponibles:
        st.warning("Esta oposición no tiene bloques configurados.")
        return

    if "repaso" not in st.session_state:
        st.session_state.repaso = {
            "preguntas": [], "respuestas": {}, "respondido": False, "bloque": None,
        }
    repaso = st.session_state.repaso

    with st.expander("📊 Tu estado actual por bloque", expanded=not repaso["preguntas"]):
        _panel_estado_bloques(stats)

    accion = stats["proxima_accion"]
    bloque_recomendado = (
        accion["bloque"] if accion["tipo"] == "practicar_bloque" else bloques_disponibles[0]
    )
    if "repaso_bloque" not in st.session_state:
        st.session_state.repaso_bloque = bloque_recomendado

    bloque_sel = st.selectbox(
        "Bloque", bloques_disponibles,
        format_func=lambda b: _NOMBRES_BLOQUE.get(b, b),
        key="repaso_bloque",
    )
    if accion["tipo"] == "practicar_bloque" and accion["bloque"] == bloque_sel:
        st.caption(f"💡 {accion['motivo']}")

    if not repaso["preguntas"]:
        if st.button("Iniciar repaso", type="primary"):
            preguntas = get_preguntas_adaptativo(user_id, oposicion_id, bloque_sel, n=10)
            if not preguntas:
                st.warning("No hay preguntas disponibles para este bloque todavía.")
            else:
                repaso.update(
                    preguntas=preguntas, respuestas={}, respondido=False, bloque=bloque_sel,
                )
                st.rerun()
        return

    if not repaso["respondido"]:
        # Momento 2: composición de la tanda — mensaje genérico, sin desglose.
        st.caption("🎯 Tanda personalizada según tu progreso en este bloque.")
        _render_preguntas(repaso["preguntas"], repaso["respuestas"], "repaso", respondido=False)
        if st.button("Comprobar respuestas", type="primary"):
            for p in repaso["preguntas"]:
                elegida = repaso["respuestas"].get(p["pregunta_id"])
                if elegida is not None:
                    update_progreso_sm2(user_id, p["pregunta_id"], elegida == p["correcta"])
            get_fase_alumno(user_id, oposicion_id, repaso["bloque"])
            repaso["respondido"] = True
            st.rerun()
    else:
        _render_preguntas(repaso["preguntas"], repaso["respuestas"], "repaso", respondido=True)
        ok = sum(
            1 for p in repaso["preguntas"]
            if repaso["respuestas"].get(p["pregunta_id"]) == p["correcta"]
        )
        fallos = len(repaso["preguntas"]) - ok
        st.success(
            f"Resultado de esta tanda: **{ok} / {len(repaso['preguntas'])}** correctas "
            f"({fallos} fallos)"
        )

        # Momento 3: cómo queda el % de acierto del bloque tras esta tanda.
        stats_actualizado = get_stats_alumno(user_id, oposicion_id)
        bloque_actualizado = next(
            (b for b in stats_actualizado["bloques"] if b["bloque"] == repaso["bloque"]), None
        )
        if bloque_actualizado:
            nombre = _NOMBRES_BLOQUE.get(repaso["bloque"], repaso["bloque"])
            st.info(
                f"**{nombre}** queda en **{bloque_actualizado['porcentaje_acierto']}%** "
                f"de acierto."
            )

        if st.button("Nueva tanda →", type="primary"):
            repaso.update(preguntas=[], respondido=False)
            st.rerun()


def _modo_simulacro_personal(oposicion_id: int, user_id: str) -> None:
    st.header("Simulacro personal")
    st.caption(
        "50 preguntas de los bloques que ya tienes estudiados (≥70% de acierto), "
        "corregidas con la fórmula oficial. Este resultado no afecta a tu progreso "
        "de repaso: es una prueba de examen completo aparte, que se guarda en "
        "\"Mi progreso\"."
    )

    if "simulacro" not in st.session_state:
        st.session_state.simulacro = {
            "preguntas": [], "respuestas": {}, "respondido": False, "guardado": False,
        }
    simulacro = st.session_state.simulacro

    if not simulacro["preguntas"]:
        if st.button("Empezar simulacro personal", type="primary"):
            resultado = get_preguntas_simulacro_personal(user_id, oposicion_id, n=50)
            if not resultado["disponible"]:
                st.warning(resultado["motivo"])
            else:
                simulacro.update(
                    preguntas=resultado["preguntas"], respuestas={},
                    respondido=False, guardado=False,
                )
                st.rerun()
        return

    if not simulacro["respondido"]:
        _render_preguntas(simulacro["preguntas"], simulacro["respuestas"], "simulacro", respondido=False)
        respondidas = sum(1 for v in simulacro["respuestas"].values() if v is not None)
        st.caption(f"{respondidas} / {len(simulacro['preguntas'])} respondidas")
        if st.button("Comprobar respuestas", type="primary"):
            simulacro["respondido"] = True
            st.rerun()
    else:
        _render_preguntas(simulacro["preguntas"], simulacro["respuestas"], "simulacro", respondido=True)
        preguntas = simulacro["preguntas"]
        aciertos = sum(
            1 for p in preguntas if simulacro["respuestas"].get(p["pregunta_id"]) == p["correcta"]
        )
        blancos = sum(1 for p in preguntas if simulacro["respuestas"].get(p["pregunta_id"]) is None)
        errores = len(preguntas) - aciertos - blancos

        resultado = calificar_simulacro(oposicion_id, aciertos, errores, blancos, len(preguntas))
        if resultado["disponible"]:
            if not simulacro["guardado"]:
                guardar_resultado_simulacro(
                    user_id, oposicion_id, "personal", len(preguntas),
                    aciertos, errores, blancos, resultado["nota"], resultado["aprobado"],
                )
                simulacro["guardado"] = True

            st.success(
                f"**{aciertos} / {len(preguntas)}** correctas · {errores} fallos · "
                f"{blancos} en blanco"
            )
            veredicto = "✅ Aprobado" if resultado["aprobado"] else "❌ No alcanza la nota mínima"
            st.info(
                f"Nota estimada (extrapolada a examen completo): "
                f"**{resultado['nota']} / {resultado['escala_max']}** — {veredicto} "
                f"(mínimo {resultado['nota_minima']})"
            )
            st.caption("Este resultado no afecta a tu progreso de repaso.")
        else:
            st.warning(resultado["motivo"])

        if st.button("Nuevo simulacro →", type="primary"):
            st.session_state.simulacro = {
                "preguntas": [], "respuestas": {}, "respondido": False, "guardado": False,
            }
            st.rerun()


def _modo_mi_progreso(oposicion_id: int, user_id: str) -> None:
    st.header("Mi progreso")
    historial = get_historial_simulacros(user_id, oposicion_id)

    if not historial:
        st.caption(
            "Todavía no has hecho ningún simulacro. Prueba el Simulacro personal "
            "para ver aquí tu evolución."
        )
        return

    for h in historial:
        tipo_label = "Personal" if h["tipo"] == "personal" else "Academia"
        fecha = h["realizado_en"].strftime("%d/%m/%Y %H:%M")
        veredicto = "✅ Aprobado" if h["aprobado"] else "❌ No aprobado"
        st.markdown(
            f"**{fecha}** — {tipo_label} ({h['n_preguntas']} preguntas) — "
            f"nota **{h['nota']}** — {veredicto}"
        )
        st.caption(f"{h['aciertos']} aciertos · {h['errores']} fallos · {h['blancos']} en blanco")
        st.divider()


def _flujo_alumno(oposicion_id: int, alumno: dict) -> None:
    user_id = alumno["user_id"]
    stats   = get_stats_alumno(user_id, oposicion_id)
    es_nuevo = not stats["bloques"]

    st.title("🎓 Tu preparación")
    st.caption(f"{alumno['email']}")

    if es_nuevo:
        st.info(
            "**¡Bienvenido/a!** Esta plataforma te ayuda a preparar la oposición "
            "con preguntas tipo test adaptadas a tu nivel.\n\n"
            "Para empezar, te recomendamos hacer la **prueba de nivel**: 40 "
            "preguntas que nos permiten calibrar en qué bloques necesitas "
            "reforzar más. Si tienes cualquier problema, dínoslo directamente."
        )

    if "modo_alumno_radio" not in st.session_state:
        st.session_state.modo_alumno_radio = "Prueba de nivel" if es_nuevo else "Repaso"

    modo_alumno = st.radio(
        "¿Qué quieres hacer?",
        ["Prueba de nivel", "Repaso", "Simulacro personal", "Mi progreso"],
        key="modo_alumno_radio", horizontal=True,
    )
    st.divider()

    if modo_alumno == "Prueba de nivel":
        _modo_prueba_nivel(oposicion_id, user_id)
    elif modo_alumno == "Repaso":
        _modo_repaso(oposicion_id, user_id, stats)
    elif modo_alumno == "Simulacro personal":
        _modo_simulacro_personal(oposicion_id, user_id)
    else:
        _modo_mi_progreso(oposicion_id, user_id)

# ── Sidebar: Oposición ────────────────────────────────────────────────────────
ops_opciones = {f"{o['nombre_corto'] or o['codigo']}": o for o in oposiciones}
op_seleccion = st.sidebar.selectbox("Oposición", list(ops_opciones.keys()))
oposicion_seleccionada = ops_opciones[op_seleccion]
oposicion_id = oposicion_seleccionada["oposicion_id"]

st.sidebar.markdown("---")

# ── Sidebar: Acceso ────────────────────────────────────────────────────────────
# Único punto de bifurcación: Administración (Google OAuth → Editor/Q&A/Generar
# test) o Alumno (Supabase Auth → prueba de nivel/repaso adaptativo). Sin
# acceso anónimo: hasta elegir uno de los dos no se muestra ningún contenido.
if "acceso" not in st.session_state:
    st.session_state.acceso = None

st.sidebar.markdown("**Acceso**")
_cacc1, _cacc2 = st.sidebar.columns(2)
with _cacc1:
    if st.button("Administración", key="acceso_administracion", use_container_width=True):
        st.session_state.acceso = "administracion"
        st.rerun()
with _cacc2:
    if st.button("Alumno", key="acceso_alumno", use_container_width=True):
        st.session_state.acceso = "alumno"
        st.rerun()

if st.session_state.acceso:
    st.sidebar.caption(f"Acceso actual: **{st.session_state.acceso.capitalize()}**")
    if st.sidebar.button("← Cambiar acceso", key="acceso_reset"):
        st.session_state.acceso = None
        st.rerun()

if st.session_state.acceso is None:
    st.title("⚖️ Asistente Jurídico")
    st.info("Elige un tipo de acceso en la barra lateral: **Administración** o **Alumno**.")
    st.stop()

st.sidebar.markdown("---")

# ══════════════════════════════════════════════════════════════════════════
# Camino Alumno (Supabase Auth, email+contraseña)
# ══════════════════════════════════════════════════════════════════════════
if st.session_state.acceso == "alumno":
    if "alumno" not in st.session_state:
        st.session_state.alumno = None

    if st.session_state.alumno:
        st.sidebar.markdown(f"🎓 {st.session_state.alumno['email']}")
        if st.sidebar.button("Cerrar sesión (alumno)"):
            st.session_state.alumno = None
            st.rerun()
        _flujo_alumno(oposicion_id, st.session_state.alumno)
        st.stop()

    st.sidebar.markdown("**Acceso Alumno**")
    accion_alumno = st.sidebar.radio(
        "Acceso alumno", ["Iniciar sesión", "Registrarse"],
        horizontal=True, label_visibility="collapsed",
    )
    email_alumno = st.sidebar.text_input("Email", key="alumno_email")
    password_alumno = st.sidebar.text_input("Contraseña", type="password", key="alumno_password")
    if st.sidebar.button("Continuar", key="alumno_submit"):
        try:
            if accion_alumno == "Registrarse":
                datos = registrar_alumno(email_alumno, password_alumno)
                st.success("Registro completado.")
            else:
                datos = login_alumno(email_alumno, password_alumno)
            st.session_state.alumno = datos
            st.rerun()
        except Exception as e:
            st.error(_mensaje_error_alumno(e, accion_alumno))

    st.title("🎓 Acceso Alumno")
    st.info("Inicia sesión o regístrate en la barra lateral para continuar.")
    st.stop()

# ══════════════════════════════════════════════════════════════════════════
# Camino Administración (Google OAuth) — Editor, Q&A y Generar test
# ══════════════════════════════════════════════════════════════════════════
if not logged_in:
    st.sidebar.markdown("**Acceso Administración**")
    st.sidebar.caption("Requiere cuenta Google autorizada (editor/academia).")
    if st.sidebar.button("Iniciar sesión con Google", key="admin_login", type="primary"):
        st.login("google")

    st.title("⚖️ Área de Administración")
    st.info(
        "Inicia sesión con tu cuenta Google en la barra lateral para acceder "
        "al editor de preguntas, Q&A y generación de test."
    )
    st.stop()

st.sidebar.markdown(f"👤 {user['email']}")
if st.sidebar.button("Cerrar sesión"):
    st.logout()

st.sidebar.markdown("---")

bloques_disponibles = _cargar_bloques(oposicion_id)
st.sidebar.markdown("**Bloque**")
_cb1, _cb2 = st.sidebar.columns(2)
with _cb1:
    if st.button("Seleccionar todo", key="blq_todos", use_container_width=True):
        for b in bloques_disponibles:
            st.session_state[f"blq_{b}"] = True
        st.rerun()
with _cb2:
    if st.button("Elimina la selección", key="blq_ninguno", use_container_width=True):
        for b in bloques_disponibles:
            st.session_state[f"blq_{b}"] = False
        st.rerun()

bloques_sel = tuple(
    b for b in bloques_disponibles
    if st.sidebar.checkbox(_NOMBRES_BLOQUE.get(b, b), value=False, key=f"blq_{b}")
)

if not bloques_sel:
    st.sidebar.info("Selecciona al menos un bloque.")
    st.stop()

bloques_filtro = bloques_sel

try:
    leyes = _cargar_leyes(oposicion_id, bloques_filtro, excluir_test=True)
except Exception as e:
    st.error(f"Error al cargar las leyes: {e}")
    st.stop()

if not leyes:
    st.sidebar.warning("Esta oposición no tiene leyes asignadas.")
    st.stop()

st.sidebar.markdown("**Ley**")
_cl1, _cl2 = st.sidebar.columns(2)
with _cl1:
    if st.button("Seleccionar todo", key="ley_todas", use_container_width=True):
        for l in leyes:
            st.session_state[f"ley_{l['ley_id']}"] = True
        st.rerun()
with _cl2:
    if st.button("Elimina la selección", key="ley_ninguna", use_container_width=True):
        for l in leyes:
            st.session_state[f"ley_{l['ley_id']}"] = False
        st.rerun()

leyes_sel = [
    l for l in leyes
    if st.sidebar.checkbox(
        l['nombre_corto'] or l['nombre'],
        value=False,
        key=f"ley_{l['ley_id']}",
    )
]

if not leyes_sel:
    st.sidebar.info("Selecciona al menos una ley.")
    st.stop()

# Alias para modos que trabajan con una sola ley (Q&A, Gentest)
ley_id     = leyes_sel[0]["ley_id"]
ley_nombre = leyes_sel[0]["nombre"]

modo = st.sidebar.radio("Modo", ["Q&A", "Generar test", "Editor"])

# ── Cabecera ──────────────────────────────────────────────────────────────────
st.title("⚖️ Asistente Jurídico")
st.caption("Búsqueda semántica + Claude")

# ── Helpers BD — Editor ───────────────────────────────────────────────────────
def _get_pending(ley_ids: list[int]) -> list[dict]:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT pt.pregunta_id, pt.ley_id, l.codigo AS ley_codigo,
                       pt.articulo, pt.pregunta,
                       pt.opcion_a, pt.opcion_b, pt.opcion_c, pt.opcion_d,
                       pt.correcta, pt.explicacion
                FROM normas.preguntas_test pt
                JOIN normas.leyes l ON l.ley_id = pt.ley_id
                WHERE pt.ley_id = ANY(%s)
                  AND pt.fuente   = 'ia'
                  AND pt.revisada = FALSE
                ORDER BY pt.ley_id, pt.generada_en DESC
            """, (ley_ids,))
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

    if len(leyes_sel) > 1:
        ley_qa = st.selectbox(
            "Ley a consultar",
            options=leyes_sel,
            format_func=lambda l: f"{l['codigo']} — {l['nombre_corto'] or l['nombre']}",
        )
        ley_id     = ley_qa["ley_id"]
        ley_nombre = ley_qa["nombre"]

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

# ── Modo Generar test ──────────────────────────────────────────────────────────
elif modo == "Generar test":
    st.header("Práctica de test")
    st.caption(f"Repaso adaptativo · {user['email']}")

    # ── Estado de la sesión de práctica ───────────────────────────────────────
    if "quiz" not in st.session_state:
        st.session_state.quiz = {
            "preguntas":  [],
            "respuestas": {},   # pregunta_id → letra elegida
            "respondido": False,
            "vistos":     set(),
            "ok":         0,
            "err":        0,
        }
    quiz = st.session_state.quiz

    total = quiz["ok"] + quiz["err"]
    if total > 0:
        pct = round(quiz["ok"] / total * 100)
        st.caption(
            f"Sesión: **{quiz['ok']}** correctas · **{quiz['err']}** erróneas "
            f"· {pct}% acierto · {len(quiz['vistos'])} preguntas vistas"
        )

    # ── Sin tanda activa: botón de inicio ─────────────────────────────────────
    if not quiz["preguntas"]:
        bloques_label = " + ".join(_NOMBRES_BLOQUE.get(b, b) for b in bloques_sel)
        st.info(f"Bloque{'s' if len(bloques_sel) > 1 else ''} seleccionado{'s' if len(bloques_sel) > 1 else ''}: **{bloques_label}**")

        if st.button("Iniciar repaso", type="primary"):
            preguntas = get_preguntas_sm2(
                user["email"], oposicion_id, bloques_sel, n=10,
            )
            if not preguntas:
                st.warning("No hay más preguntas disponibles para esta selección. ¡Has visto todas!")
            else:
                quiz["preguntas"]  = preguntas
                quiz["respuestas"] = {}
                quiz["respondido"] = False
                quiz["vistos"].update(p["pregunta_id"] for p in preguntas)
                st.rerun()

    # ── Tanda activa ──────────────────────────────────────────────────────────
    else:
        for i, p in enumerate(quiz["preguntas"], 1):
            pid      = p["pregunta_id"]
            opciones = {
                "a": p["opcion_a"], "b": p["opcion_b"],
                "c": p["opcion_c"], "d": p["opcion_d"],
            }
            st.markdown(f"**{i}. [{p['ley_codigo']}] {p['pregunta']}**")

            if not quiz["respondido"]:
                resp = st.radio(
                    "",
                    options=list(opciones.keys()),
                    format_func=lambda x, op=opciones: f"{x}) {op[x]}",
                    key=f"q_{pid}",
                    index=None,
                    label_visibility="collapsed",
                )
                quiz["respuestas"][pid] = resp
            else:
                correcta = p["correcta"]
                elegida  = quiz["respuestas"].get(pid)
                for letra, texto in opciones.items():
                    if letra == correcta:
                        st.markdown(f"✅ **{letra}) {texto}**")
                    elif letra == elegida:
                        st.markdown(f"❌ {letra}) {texto}")
                    else:
                        st.markdown(f"{letra}) {texto}")
                if p.get("explicacion"):
                    st.info(p["explicacion"])

            st.divider()

        # ── Botones de acción ─────────────────────────────────────────────────
        if not quiz["respondido"]:
            if st.button("Comprobar respuestas", type="primary"):
                ok = err = 0
                for p in quiz["preguntas"]:
                    elegida = quiz["respuestas"].get(p["pregunta_id"])
                    if elegida == p["correcta"]:
                        ok += 1
                    elif elegida is not None:
                        err += 1
                    if elegida is not None:
                        try:
                            update_progreso_sm2(
                                user["email"],
                                p["pregunta_id"],
                                elegida == p["correcta"],
                            )
                        except Exception:
                            pass
                quiz["ok"]        += ok
                quiz["err"]       += err
                quiz["respondido"] = True
                st.rerun()
        else:
            ok_t = sum(
                1 for p in quiz["preguntas"]
                if quiz["respuestas"].get(p["pregunta_id"]) == p["correcta"]
            )
            st.success(f"Resultado de esta tanda: **{ok_t} / {len(quiz['preguntas'])}** correctas")
            st.caption("Progreso guardado. Las preguntas falladas volverán antes.")
            if st.button("Nueva tanda →", type="primary"):
                quiz["preguntas"]  = []
                quiz["respondido"] = False
                st.rerun()

# ── Modo Editor ────────────────────────────────────────────────────────────────
elif modo == "Editor":
    st.header("Editor de preguntas")
    st.caption(f"Sesión activa: {user["email"]}")

    tab_gen, tab_rev = st.tabs(["Generar", "Revisar"])

    # ── Tab Generar ───────────────────────────────────────────────────────────
    with tab_gen:
        nombres_sel = ", ".join(l["codigo"] for l in leyes_sel)
        st.subheader(f"Generar preguntas — {nombres_sel}")
        col_n, col_max = st.columns(2)
        with col_n:
            n_gen = st.slider("Preguntas por ley", min_value=1, max_value=50, value=10,
                              key="editor_n_gen")
        with col_max:
            max_por_art = st.slider("Máximo por artículo", min_value=1, max_value=5, value=1,
                                    key="editor_max_art",
                                    help="Cuántas preguntas IA puede tener un mismo artículo (pendientes + aprobadas)")

        if st.button("Generar y guardar en BD", type="primary", key="btn_generar"):
            client  = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
            ok = err = 0
            for ley_loop in leyes_sel:
                lid   = ley_loop["ley_id"]
                lnomb = ley_loop["nombre"]
                arts  = _fetch_articles(lid, n_gen, max_por_art)
                if not arts:
                    st.info(f"{ley_loop['codigo']}: sin artículos nuevos.")
                    continue
                few_shots = _fetch_few_shots(lid)
                progress  = st.progress(0, text=f"{ley_loop['codigo']} — iniciando…")
                for i, art in enumerate(arts, 1):
                    tiene_apartados = _has_numbered_paragraphs(art["contenido"])
                    try:
                        resp = client.messages.create(
                            model=CLAUDE_MODEL,
                            max_tokens=800,
                            messages=_build_prompt(
                                art, lnomb,
                                few_shots=few_shots,
                                tiene_apartados=tiene_apartados,
                            ),
                        )
                        parsed = _parse_and_validate(resp.content[0].text)
                        _save(lid, art, parsed)
                        ok += 1
                    except Exception as e:
                        err += 1
                        st.warning(f"{ley_loop['codigo']} — Art. {art['numero']}: {e}")
                    progress.progress(i / len(arts),
                                      text=f"{ley_loop['codigo']} — {i}/{len(arts)}")
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
        nombres_sel = ", ".join(l["codigo"] for l in leyes_sel)
        st.subheader(f"Pendientes de revisión — {nombres_sel}")

        pending = _get_pending([l["ley_id"] for l in leyes_sel])

        if not pending:
            st.info("No hay preguntas pendientes de revisión para esta ley.")
        else:
            st.caption(f"{len(pending)} pregunta{'s' if len(pending) > 1 else ''} pendiente{'s' if len(pending) > 1 else ''}")

            for p in pending:
                pid = p["pregunta_id"]
                with st.expander(f"[{p['ley_codigo']}] Art. {p['articulo']} — {p['pregunta'][:70]}…"):
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
