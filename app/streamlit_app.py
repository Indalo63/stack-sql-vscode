import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

import time
from datetime import datetime, time as dtime
import anthropic
import streamlit as st
from app.qa_pipeline import run_qa
from app.test_pipeline import run_gentest
from app.retrieval import (get_leyes_disponibles, get_oposiciones,
                           get_bloques_por_oposicion, get_temas_por_bloque,
                           get_temas_por_bloques,
                           get_editor, listar_editores, alta_editor,
                           revocar_editor, cambiar_rol_editor,
                           pendientes_por_bloque, pendientes_por_tema,
                           get_bloque_y_epigrafes,
                           descartar_pregunta, listar_descartadas, restaurar_pregunta,
                           get_cobertura_banco, proponer_pesos_bloque,
                           get_alertas_calidad,
                           aplicar_pesos_bloque, get_historial_pesos,
                           get_preguntas_sm2, update_progreso_sm2,
                           registrar_respuesta, analisis_distractores,
                           get_calibracion, get_umbral_rentabilidad,
                           get_grupos_intercalados, get_preguntas_intercaladas,
                           get_fase_alumno, get_stats_alumno,
                           get_preguntas_adaptativo, get_preguntas_adaptativo_tema,
                           get_preguntas_prueba_nivel,
                           guardar_perfil_alumno, get_perfil_alumno, get_plan_partida,
                           get_preguntas_simulacro_personal, calificar_simulacro,
                           guardar_resultado_simulacro, get_historial_simulacros,
                           get_preguntas_simulacro_academia,
                           get_simulacros_academia_disponibles,
                           generar_simulacro_academia, autorizar_simulacro_academia,
                           listar_simulacros_academia)
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

st.markdown("""
<style>
  /* Sidebar compacto: sin esto, los 6 bloques no caben en un portátil (768px) y
     hay que hacer scroll para ver el último. */
  section[data-testid="stSidebar"] div[data-testid="stVerticalBlock"] { gap: .45rem; }
  section[data-testid="stSidebar"] hr { margin: .5rem 0; }
  section[data-testid="stSidebar"] [data-testid="stCheckbox"] { margin-bottom: -.35rem; }

  /* Pie del sidebar: compacto y discreto */
  .st-key-sidebar_footer {
      padding-top: .6rem;
      border-top: 1px solid rgba(128,128,128,.25);
  }
  .st-key-sidebar_footer p { font-size: .78rem; margin-bottom: .2rem; }
</style>
""", unsafe_allow_html=True)


# El pie va al final del sidebar. Como los selectores llaman a st.stop() cuando no
# hay nada marcado, un bloque escrito al final del script no llegaría a pintarse en
# ese caso: por eso _parar() lo pinta antes de detener la ejecución.
_pie_pintado = False


def _pie_sidebar() -> None:
    """Sesión activa + cerrar sesión, al fondo del sidebar. Idempotente."""
    global _pie_pintado
    if _pie_pintado or not st.session_state.get("_pie_datos"):
        return
    _pie_pintado = True
    email, rol = st.session_state["_pie_datos"]
    with st.sidebar.container(key="sidebar_footer"):
        st.caption(f"👤 {email} · {rol}")
        if st.button("Cerrar sesión", key="logout_admin", type="tertiary"):
            st.logout()


def _parar():
    """st.stop() que no se deja el pie del sidebar sin pintar."""
    _pie_sidebar()
    st.stop()


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
                  excluir_test: bool = False, temas: tuple[int, ...] | None = None):
    return get_leyes_disponibles(oposicion_id, bloques, excluir_test=excluir_test, temas=temas)


# ── Selectores del sidebar (Gestión banco de preguntas) ───────────────────────
# Cada modo monta su propio selector: el prefijo aísla su session_state, para que
# la selección de un modo no arrastre a la de otro.

def _etiqueta_tema(t: dict) -> str:
    return f"{t['bloque']}.{t['tema']}: {t['titulo'][:50]}{'…' if len(t['titulo']) > 50 else ''}"


def _checkboxes(items, key_de, etiqueta_de, prefix: str, titulo: str):
    """Multi-checkbox con 'Seleccionar todo' / 'Elimina la selección'. Solo para
    listas cortas (Bloque, 6 opciones): con listas largas usar _multiselect."""
    st.sidebar.markdown(f"**{titulo}**")
    _c1, _c2 = st.sidebar.columns(2)
    with _c1:
        if st.button("Seleccionar todo", key=f"{prefix}_todos", use_container_width=True):
            for it in items:
                st.session_state[f"{prefix}_{key_de(it)}"] = True
            st.rerun()
    with _c2:
        if st.button("Elimina la selección", key=f"{prefix}_ninguno", use_container_width=True):
            for it in items:
                st.session_state[f"{prefix}_{key_de(it)}"] = False
            st.rerun()

    return [
        it for it in items
        if st.sidebar.checkbox(etiqueta_de(it), value=False, key=f"{prefix}_{key_de(it)}")
    ]


def _multiselect(items, key_de, etiqueta_de, prefix: str, titulo: str):
    """
    Desplegable multiselección: ocupa una línea en vez de una casilla por opción.

    Necesario en Tema (hasta 58) y Ley (decenas): con casillas, el sidebar llegaba
    a 4.800px — más de 6 pantallas de scroll — y era imposible trabajar.
    """
    key = f"{prefix}_ms"
    ids = [key_de(it) for it in items]
    por_id = {key_de(it): it for it in items}

    # Al cambiar el filtro de arriba (p. ej. otro bloque), la selección guardada
    # puede contener ids que ya no existen: hay que limpiarla o Streamlit peta.
    if key in st.session_state:
        st.session_state[key] = [i for i in st.session_state[key] if i in por_id]

    _c1, _c2 = st.sidebar.columns(2)
    with _c1:
        if st.button("Seleccionar todo", key=f"{prefix}_todos", use_container_width=True):
            st.session_state[key] = ids
            st.rerun()
    with _c2:
        if st.button("Elimina la selección", key=f"{prefix}_ninguno", use_container_width=True):
            st.session_state[key] = []
            st.rerun()

    sel = st.sidebar.multiselect(
        titulo, options=ids, format_func=lambda i: etiqueta_de(por_id[i]),
        key=key, placeholder="Elige una o varias…",
    )
    return [por_id[i] for i in sel]


def _selector_bloque_tema_ley(oposicion_id: int, prefix: str):
    """Cascada Bloque → Tema → Ley (multi-selección en los tres niveles)."""
    bloques_sel = tuple(_checkboxes(
        _cargar_bloques(oposicion_id),
        key_de=lambda b: b, etiqueta_de=lambda b: _NOMBRES_BLOQUE.get(b, b),
        prefix=f"{prefix}_blq", titulo="Bloque",
    ))
    if not bloques_sel:
        st.sidebar.info("Selecciona al menos un bloque.")
        _parar()

    temas_sel = tuple(t["epigrafe_id"] for t in _multiselect(
        get_temas_por_bloques(oposicion_id, bloques_sel),
        key_de=lambda t: t["epigrafe_id"], etiqueta_de=_etiqueta_tema,
        prefix=f"{prefix}_tema", titulo="Tema",
    ))
    if not temas_sel:
        st.sidebar.info("Selecciona al menos un tema.")
        _parar()

    try:
        leyes = _cargar_leyes(oposicion_id, bloques_sel, excluir_test=True, temas=temas_sel)
    except Exception as e:
        st.error(f"Error al cargar las leyes: {e}")
        _parar()
    if not leyes:
        st.sidebar.warning("Ninguna ley cargada está asociada todavía a los temas seleccionados.")
        _parar()

    leyes_sel = _multiselect(
        leyes,
        key_de=lambda l: l["ley_id"], etiqueta_de=lambda l: l["nombre_corto"] or l["nombre"],
        prefix=f"{prefix}_ley", titulo="Ley",
    )
    if not leyes_sel:
        st.sidebar.info("Selecciona al menos una ley.")
        _parar()

    return bloques_sel, temas_sel, leyes_sel


def _selector_generar_test(oposicion_id: int) -> list[dict]:
    """Bloque (uno) → Por tema o Por ley (excluyente) → multi-selección dentro del
    bloque. El test nunca se genera sobre el bloque completo sin acotar."""
    bloque = st.sidebar.selectbox(
        "Bloque", _cargar_bloques(oposicion_id),
        format_func=lambda b: _NOMBRES_BLOQUE.get(b, b), key="gt_bloque",
    )
    if st.sidebar.radio("Generar por", ["Tema", "Ley"], key="gt_filtro") == "Tema":
        temas_sel = tuple(t["epigrafe_id"] for t in _multiselect(
            get_temas_por_bloques(oposicion_id, (bloque,)),
            key_de=lambda t: t["epigrafe_id"], etiqueta_de=_etiqueta_tema,
            prefix="gt_tema", titulo="Tema",
        ))
        if not temas_sel:
            st.sidebar.info("Selecciona al menos un tema.")
            _parar()
        leyes_sel = _cargar_leyes(oposicion_id, (bloque,), excluir_test=True, temas=temas_sel)
        if not leyes_sel:
            st.sidebar.warning("Ninguna ley cargada está asociada todavía a los temas seleccionados.")
            _parar()
    else:
        leyes_sel = _multiselect(
            _cargar_leyes(oposicion_id, (bloque,), excluir_test=True),
            key_de=lambda l: l["ley_id"], etiqueta_de=lambda l: l["nombre_corto"] or l["nombre"],
            prefix="gt_ley", titulo="Ley",
        )
        if not leyes_sel:
            st.sidebar.info("Selecciona al menos una ley.")
            _parar()

    return leyes_sel


def _selector_revisar(oposicion_id: int) -> list[dict]:
    """
    Filtro excluyente Por bloque / Por tema, selección única en ambos casos.

    Las etiquetas llevan el número de preguntas pendientes, para que el editor
    vea de un vistazo dónde está el trabajo: el contador de arriba es global,
    así que sin esto habría que ir probando bloques (o los 58 temas) a ciegas.
    """
    if st.sidebar.radio("Filtrar por", ["Bloque", "Tema"], key="rev_filtro") == "Bloque":
        por_bloque = pendientes_por_bloque(oposicion_id)

        def _etiqueta_bloque(b: str) -> str:
            n = por_bloque.get(b, 0)
            return f"{_NOMBRES_BLOQUE.get(b, b)}{f'  ·  {n}' if n else ''}"

        bloque = st.sidebar.selectbox(
            "Bloque", _cargar_bloques(oposicion_id),
            format_func=_etiqueta_bloque, key="rev_bloque",
        )
        leyes = _cargar_leyes(oposicion_id, (bloque,), excluir_test=True)
    else:
        temas = get_temas_por_bloques(oposicion_id, tuple(_cargar_bloques(oposicion_id)))
        if not temas:
            st.sidebar.warning("No hay temas cargados para esta oposición.")
            _parar()
        por_tema = pendientes_por_tema(oposicion_id)

        def _etiqueta_tema_pend(t: dict) -> str:
            n = por_tema.get(t["epigrafe_id"], 0)
            return f"{_etiqueta_tema(t)}{f'  ·  {n}' if n else ''}"

        tema = st.sidebar.selectbox(
            "Tema", temas, format_func=_etiqueta_tema_pend, key="rev_tema",
        )
        leyes = _cargar_leyes(
            oposicion_id, None, excluir_test=True, temas=(tema["epigrafe_id"],),
        )

    st.sidebar.caption("El número indica las preguntas pendientes de revisión.")

    if not leyes:
        st.sidebar.warning("Ninguna ley cargada está asociada todavía a esta selección.")
        _parar()
    return leyes


try:
    oposiciones = _cargar_oposiciones()
except Exception as e:
    st.error(f"No se puede conectar a la base de datos: {e}")
    _parar()

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


_ETIQUETA_CONFIANZA = {
    "seguro":  "🟢 Lo sé",
    "dudo":    "🟡 Dudo",
    "ni_idea": "🔴 Ni idea",
}


def _render_preguntas(preguntas: list[dict], respuestas: dict, key_prefix: str,
                      respondido: bool, confianzas: dict | None = None) -> None:
    """
    Renderiza una tanda de preguntas a/b/c/d; si `respondido`, muestra corrección.

    Si se pasa `confianzas`, se pide además —**antes** de corregir— cómo de
    seguro está el alumno. Sin ese dato, acertar por saberlo y acertar por suerte
    se ven idénticos, y no hay forma de detectar ni el exceso de confianza ni el
    de prudencia (migración 050). Es opcional: quien no la declare, no la declara.
    """
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

            if confianzas is not None:
                conf = st.radio(
                    "¿Cómo de seguro estás?",
                    options=list(_ETIQUETA_CONFIANZA.keys()),
                    format_func=lambda c: _ETIQUETA_CONFIANZA[c],
                    key=f"{key_prefix}_conf_{pid}",
                    index=None,
                    horizontal=True,
                )
                confianzas[pid] = conf
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

            # El fallo estando seguro es el más caro: no se repasa, porque el
            # alumno cree que lo domina. Se le señala en el sitio, no en un panel.
            conf = (confianzas or {}).get(pid)
            if conf == "seguro" and elegida != correcta:
                st.warning(
                    "⚠️ Dijiste que lo sabías y has fallado. Estas son las que "
                    "más cuestan: nunca las repasarías por tu cuenta."
                )
            elif conf == "ni_idea" and elegida == correcta:
                st.caption(
                    "🎲 Has acertado diciendo «ni idea». Si esto te pasa a menudo, "
                    "responder a ciegas te sale a cuenta — lo verás en Mi progreso."
                )

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
            temas_tocados = set()
            for p in nivel["preguntas"]:
                elegida = nivel["respuestas"].get(p["pregunta_id"])
                # Se registra SIEMPRE, incluso en blanco: dejar en blanco es una
                # decisión (la fórmula A−E/3 penaliza fallar), no una no-respuesta.
                registrar_respuesta(user_id, p["pregunta_id"], elegida,
                                    elegida == p["correcta"], "prueba_nivel")
                if elegida is not None:
                    update_progreso_sm2(user_id, p["pregunta_id"], elegida == p["correcta"])
                    if p.get("epigrafe_id"):
                        temas_tocados.add(p["epigrafe_id"])
            for epigrafe_id in temas_tocados:
                get_fase_alumno(user_id, oposicion_id, epigrafe_id)
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
            st.markdown(f"**{nombre}** — {b['porcentaje_acierto']}% de acierto")
        st.info(stats["proxima_accion"]["motivo"])

        if st.button("Ir a Repaso →", type="primary"):
            st.session_state.nivel = {"preguntas": [], "respuestas": {}, "respondido": False}
            st.session_state["_forzar_modo_alumno"] = "Repaso"
            st.rerun()


_TEMA_TODO_BLOQUE = "__todo_bloque__"


def _panel_estado_bloques(stats: dict) -> None:
    """Momento 1: estado actual por bloque y, dentro, por cada tema oficial."""
    if not stats["bloques"]:
        st.caption("Todavía no tienes datos de progreso. Empieza una tanda para ver tu evolución.")
        return
    for b in stats["bloques"]:
        nombre = _NOMBRES_BLOQUE.get(b["bloque"], b["bloque"])
        estado = "✅ estudiado" if b["estudiado"] else "en progreso"
        st.markdown(f"**{nombre}** — {b['porcentaje_acierto']}% de acierto ({estado})")
        for t in b["temas"]:
            marca = "✅" if t["estudiado"] else ("· " if t["preguntas_vistas"] > 0 else "—")
            titulo_corto = t["titulo"] if len(t["titulo"]) <= 70 else t["titulo"][:70] + "…"
            st.caption(f"{marca} Tema {t['tema']}: {titulo_corto} — {t['porcentaje_acierto']}%")
        st.markdown("")


def _repaso_intercalado(oposicion_id: int, user_id: str, repaso: dict) -> None:
    """
    Práctica intercalada: mezcla dos leyes que se confunden, alternándolas.

    Lo que entrena esto y el repaso por tema NO entrena: **distinguir qué norma
    aplica**. Practicando LPAC seguida, el alumno tiene el esquema de LPAC cargado
    y acierta — y concluye que se la sabe. El examen se la mezcla con la LRJSP y
    ahí se ve que no. La práctica en bloque produce **fluidez falsa**.

    Hay que avisarle de que **va a fallar más**: es una "dificultad deseable" (peor
    rendimiento mientras practica, mejor el día del examen). Si no se lo decimos,
    creerá que la app ha empeorado y se volverá al modo que le engaña.
    """
    grupos = get_grupos_intercalados(user_id, oposicion_id)

    if not grupos and not repaso["preguntas"]:
        st.info(
            "Todavía no hay ningún par de leyes que puedas intercalar. "
            "**Y es a propósito.**"
        )
        st.markdown(
            "Intercalar sirve para **distinguir** dos normas que ya conoces por "
            "separado. Si aún no tienes base en ninguna de las dos, mezclarlas no "
            "te enseña a diferenciarlas: te impide aprender la primera.\n\n"
            "Practica un poco **Por tema** y, en cuanto tengas recorrido en dos "
            "leyes que el temario estudia juntas (por ejemplo la LPAC y la LRJSP), "
            "aparecerán aquí."
        )
        return

    if grupos:
        opciones = {g["etiqueta"]: g for g in grupos}
        etiqueta = st.selectbox("Leyes que se confunden", list(opciones.keys()))
        grupo = opciones[etiqueta]
        st.caption(
            f"Comparten **{grupo['temas_compartidos']} temas** del programa oficial. "
            f"Por eso se confunden — y por eso el tribunal las cruza."
        )

        if not repaso["preguntas"]:
            st.warning(
                "⚠️ **Vas a fallar más que en el repaso por tema. Es la idea.** "
                "Cuando practicas una ley seguida, tienes su esquema cargado y "
                "aciertas sin esforzarte en recordar cuál es. Al mezclarlas, tienes "
                "que decidir **qué norma aplica** en cada pregunta — que es "
                "exactamente lo que te van a pedir en el examen. Cuesta más y se "
                "retiene mejor."
            )
            if st.button("Iniciar práctica intercalada", type="primary"):
                preguntas = get_preguntas_intercaladas(
                    user_id, oposicion_id, grupo["ley_ids"], n=10
                )
                if not preguntas:
                    st.warning("No hay preguntas suficientes de estas dos leyes todavía.")
                else:
                    repaso.update(
                        preguntas=preguntas, respuestas={}, confianzas={},
                        respondido=False, intercalada=True,
                        bloque=None, epigrafe_id=None, tema_label=etiqueta,
                    )
                    st.rerun()
            return

    if not repaso["preguntas"]:
        return

    if not repaso["respondido"]:
        st.caption(f"🔀 Práctica intercalada — {repaso['tema_label']}.")
        _render_preguntas(repaso["preguntas"], repaso["respuestas"], "repaso",
                          respondido=False, confianzas=repaso["confianzas"])
        if st.button("Comprobar respuestas", type="primary"):
            temas_tocados = set()
            for p in repaso["preguntas"]:
                elegida = repaso["respuestas"].get(p["pregunta_id"])
                registrar_respuesta(user_id, p["pregunta_id"], elegida,
                                    elegida == p["correcta"], "repaso",
                                    confianza=repaso["confianzas"].get(p["pregunta_id"]))
                if elegida is not None:
                    update_progreso_sm2(user_id, p["pregunta_id"], elegida == p["correcta"])
                    if p.get("epigrafe_id"):
                        temas_tocados.add(p["epigrafe_id"])
            for epigrafe_id in temas_tocados:
                get_fase_alumno(user_id, oposicion_id, epigrafe_id)
            repaso["respondido"] = True
            st.rerun()
        return

    _render_preguntas(repaso["preguntas"], repaso["respuestas"], "repaso",
                      respondido=True, confianzas=repaso["confianzas"])

    # El acierto por ley es lo que importa aquí: si una de las dos se hunde al
    # mezclarlas, ahí está justo la confusión que hay que trabajar.
    por_ley: dict[str, list[bool]] = {}
    for p in repaso["preguntas"]:
        ok = repaso["respuestas"].get(p["pregunta_id"]) == p["correcta"]
        por_ley.setdefault(p["ley_codigo"], []).append(ok)

    ok_total = sum(1 for v in por_ley.values() for x in v if x)
    st.success(
        f"Resultado: **{ok_total} / {len(repaso['preguntas'])}** correctas — "
        f"{repaso['tema_label']}"
    )
    detalle = " · ".join(
        f"**{cod}**: {sum(v)}/{len(v)}" for cod, v in sorted(por_ley.items())
    )
    st.info(
        f"Por ley — {detalle}\n\nSi una de las dos va claramente peor que la otra, "
        f"ahí está la confusión: no es que no te la sepas, es que **se te va detrás "
        f"de la otra**."
    )

    if st.button("Nueva tanda intercalada →", type="primary"):
        repaso.update(preguntas=[], respondido=False, confianzas={})
        st.rerun()


def _modo_repaso(oposicion_id: int, user_id: str, stats: dict) -> None:
    st.header("Repaso adaptativo")

    bloques_disponibles = get_bloques_por_oposicion(oposicion_id)
    if not bloques_disponibles:
        st.warning("Esta oposición no tiene bloques configurados.")
        return

    if "repaso" not in st.session_state:
        st.session_state.repaso = {
            "preguntas": [], "respuestas": {}, "confianzas": {}, "respondido": False,
            "bloque": None, "epigrafe_id": None, "tema_label": None, "intercalada": False,
        }
    repaso = st.session_state.repaso
    repaso.setdefault("confianzas", {})
    repaso.setdefault("intercalada", False)

    with st.expander("📊 Tu estado actual por bloque y tema", expanded=not repaso["preguntas"]):
        _panel_estado_bloques(stats)

    tipo = st.radio(
        "Tipo de práctica",
        ["Por tema", "Intercalada"],
        horizontal=True,
        key="repaso_tipo",
        help=(
            "Por tema: practicas una materia seguida. Intercalada: mezclas dos leyes "
            "que se parecen, para entrenar a distinguirlas."
        ),
    )
    if tipo == "Intercalada":
        _repaso_intercalado(oposicion_id, user_id, repaso)
        return

    # Volver a "Por tema" con una tanda intercalada a medias: se descarta, o se
    # renderizaría con el flujo equivocado (bloque/tema que esa tanda no tiene).
    if repaso["intercalada"]:
        repaso.update(preguntas=[], respondido=False, confianzas={}, intercalada=False)

    accion = stats["proxima_accion"]
    bloque_recomendado = (
        accion["bloque"] if accion["tipo"] == "practicar_tema" else bloques_disponibles[0]
    )
    if "repaso_bloque" not in st.session_state:
        st.session_state.repaso_bloque = bloque_recomendado

    bloque_sel = st.selectbox(
        "Bloque", bloques_disponibles,
        format_func=lambda b: _NOMBRES_BLOQUE.get(b, b),
        key="repaso_bloque",
    )

    temas_bloque = get_temas_por_bloque(oposicion_id, bloque_sel)
    opciones_tema = {_TEMA_TODO_BLOQUE: "Todo el bloque"}
    for t in temas_bloque:
        titulo_corto = t["titulo"] if len(t["titulo"]) <= 70 else t["titulo"][:70] + "…"
        opciones_tema[t["epigrafe_id"]] = f"Tema {t['tema']}: {titulo_corto}"

    tema_key = f"repaso_tema_{bloque_sel}"
    if tema_key not in st.session_state:
        if accion["tipo"] == "practicar_tema" and accion["bloque"] == bloque_sel:
            st.session_state[tema_key] = accion["epigrafe_id"]
        else:
            st.session_state[tema_key] = _TEMA_TODO_BLOQUE

    tema_sel = st.selectbox(
        "Tema", list(opciones_tema.keys()),
        format_func=lambda k: opciones_tema[k],
        key=tema_key,
    )
    if accion["tipo"] == "practicar_tema" and accion["bloque"] == bloque_sel:
        st.caption(f"💡 {accion['motivo']}")

    if not repaso["preguntas"]:
        if st.button("Iniciar repaso", type="primary"):
            if tema_sel == _TEMA_TODO_BLOQUE:
                preguntas = get_preguntas_adaptativo(user_id, oposicion_id, bloque_sel, n=10)
            else:
                preguntas = get_preguntas_adaptativo_tema(user_id, oposicion_id, tema_sel, n=10)
            if not preguntas:
                st.warning("No hay preguntas disponibles todavía para esta selección.")
            else:
                repaso.update(
                    preguntas=preguntas, respuestas={}, confianzas={},
                    respondido=False, bloque=bloque_sel,
                    epigrafe_id=(None if tema_sel == _TEMA_TODO_BLOQUE else tema_sel),
                    tema_label=opciones_tema[tema_sel],
                )
                st.rerun()
        return

    if not repaso["respondido"]:
        # Momento 2: composición de la tanda — mensaje genérico, sin desglose.
        st.caption(f"🎯 Tanda personalizada según tu progreso — {repaso['tema_label']}.")
        _render_preguntas(repaso["preguntas"], repaso["respuestas"], "repaso",
                          respondido=False, confianzas=repaso["confianzas"])
        if st.button("Comprobar respuestas", type="primary"):
            temas_tocados = set()
            for p in repaso["preguntas"]:
                elegida = repaso["respuestas"].get(p["pregunta_id"])
                registrar_respuesta(user_id, p["pregunta_id"], elegida,
                                    elegida == p["correcta"], "repaso",
                                    confianza=repaso["confianzas"].get(p["pregunta_id"]))
                if elegida is not None:
                    update_progreso_sm2(user_id, p["pregunta_id"], elegida == p["correcta"])
                    if p.get("epigrafe_id"):
                        temas_tocados.add(p["epigrafe_id"])
            for epigrafe_id in temas_tocados:
                get_fase_alumno(user_id, oposicion_id, epigrafe_id)
            repaso["respondido"] = True
            st.rerun()
    else:
        _render_preguntas(repaso["preguntas"], repaso["respuestas"], "repaso",
                          respondido=True, confianzas=repaso["confianzas"])
        ok = sum(
            1 for p in repaso["preguntas"]
            if repaso["respuestas"].get(p["pregunta_id"]) == p["correcta"]
        )
        fallos = len(repaso["preguntas"]) - ok
        st.success(
            f"Resultado de esta tanda: **{ok} / {len(repaso['preguntas'])}** correctas "
            f"({fallos} fallos)"
        )

        # Momento 3: cómo queda el % de acierto del bloque (y del tema, si aplica) tras esta tanda.
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
            if repaso["epigrafe_id"]:
                tema_actualizado = next(
                    (t for t in bloque_actualizado["temas"] if t["epigrafe_id"] == repaso["epigrafe_id"]),
                    None,
                )
                if tema_actualizado:
                    st.caption(
                        f"Tema {tema_actualizado['tema']}: "
                        f"{tema_actualizado['porcentaje_acierto']}% de acierto."
                    )

        if st.button("Nueva tanda →", type="primary"):
            repaso.update(preguntas=[], respondido=False, confianzas={})
            st.rerun()


def _modo_simulacro_personal(oposicion_id: int, user_id: str) -> None:
    st.header("Simulacro personal")
    st.caption(
        "50 preguntas de los bloques que ya tienes estudiados (≥70% de acierto), "
        "corregidas con la fórmula oficial. Este resultado no afecta a tu progreso "
        "de repaso: es una prueba de examen completo aparte, que se guarda en "
        "\"Mi progreso\"."
    )

    rent = get_umbral_rentabilidad(oposicion_id)
    if rent["disponible"]:
        st.caption(
            f"📐 Con la fórmula oficial, responder sale a cuenta si aciertas más "
            f"del **{rent['umbral_pct']}%** de las veces. Ese es justo el azar de "
            f"cuatro opciones: **si puedes descartar una sola opción, contestar ya "
            f"te suma**. Declara tu confianza en cada pregunta y en \"Mi progreso\" "
            f"verás si tu instinto acierta o te está costando puntos."
        )

    if "simulacro" not in st.session_state:
        st.session_state.simulacro = {
            "preguntas": [], "respuestas": {}, "confianzas": {},
            "respondido": False, "guardado": False,
        }
    simulacro = st.session_state.simulacro
    simulacro.setdefault("confianzas", {})

    if not simulacro["preguntas"]:
        if st.button("Empezar simulacro personal", type="primary"):
            resultado = get_preguntas_simulacro_personal(user_id, oposicion_id, n=50)
            if not resultado["disponible"]:
                st.warning(resultado["motivo"])
            else:
                simulacro.update(
                    preguntas=resultado["preguntas"], respuestas={}, confianzas={},
                    respondido=False, guardado=False,
                )
                st.rerun()
        return

    if not simulacro["respondido"]:
        _render_preguntas(simulacro["preguntas"], simulacro["respuestas"], "simulacro",
                          respondido=False, confianzas=simulacro["confianzas"])
        respondidas = sum(1 for v in simulacro["respuestas"].values() if v is not None)
        st.caption(f"{respondidas} / {len(simulacro['preguntas'])} respondidas")
        if st.button("Comprobar respuestas", type="primary"):
            simulacro["respondido"] = True
            st.rerun()
    else:
        _render_preguntas(simulacro["preguntas"], simulacro["respuestas"], "simulacro",
                          respondido=True, confianzas=simulacro["confianzas"])
        preguntas = simulacro["preguntas"]
        if not simulacro["guardado"]:
            for p in preguntas:
                elegida = simulacro["respuestas"].get(p["pregunta_id"])
                registrar_respuesta(user_id, p["pregunta_id"], elegida,
                                    elegida == p["correcta"], "simulacro_personal",
                                    confianza=simulacro["confianzas"].get(p["pregunta_id"]))
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
                "preguntas": [], "respuestas": {}, "confianzas": {},
                "respondido": False, "guardado": False,
            }
            st.rerun()


def _modo_simulacro_academia(oposicion_id: int, user_id: str) -> None:
    st.header("Simulacro de academia")
    st.caption(
        "Mismas preguntas para todos los alumnos, dentro de la ventana de tiempo "
        "fijada por la academia. Un único intento por simulacro."
    )

    if "simulacro_academia" not in st.session_state:
        st.session_state.simulacro_academia = {
            "simulacro_id": None, "preguntas": [], "respuestas": {},
            "respondido": False, "guardado": False,
        }
    sa = st.session_state.simulacro_academia

    if not sa["preguntas"]:
        disponibles = get_simulacros_academia_disponibles(oposicion_id, user_id)
        pendientes = [s for s in disponibles if not s["ya_realizado"]]
        if not pendientes:
            if disponibles:
                st.info("Ya has realizado todos los simulacros de academia disponibles ahora mismo.")
            else:
                st.info("No hay ningún simulacro de academia abierto en este momento.")
            return

        opciones = {
            f"{s['nombre']} (cierra {s['fecha_fin'].strftime('%d/%m/%Y %H:%M')})": s["simulacro_id"]
            for s in pendientes
        }
        elegido = st.selectbox("Simulacro disponible", list(opciones.keys()))
        if st.button("Empezar simulacro de academia", type="primary"):
            simulacro_id = opciones[elegido]
            resultado = get_preguntas_simulacro_academia(simulacro_id)
            if not resultado["disponible"]:
                st.warning(resultado["motivo"])
            else:
                sa.update(
                    simulacro_id=simulacro_id, preguntas=resultado["preguntas"],
                    respuestas={}, respondido=False, guardado=False,
                )
                st.rerun()
        return

    if not sa["respondido"]:
        _render_preguntas(sa["preguntas"], sa["respuestas"], "simulacro_academia", respondido=False)
        respondidas = sum(1 for v in sa["respuestas"].values() if v is not None)
        st.caption(f"{respondidas} / {len(sa['preguntas'])} respondidas")
        if st.button("Comprobar respuestas", type="primary", key="btn_comprobar_academia"):
            sa["respondido"] = True
            st.rerun()
    else:
        _render_preguntas(sa["preguntas"], sa["respuestas"], "simulacro_academia", respondido=True)
        preguntas = sa["preguntas"]
        if not sa["guardado"]:
            for p in preguntas:
                elegida = sa["respuestas"].get(p["pregunta_id"])
                registrar_respuesta(user_id, p["pregunta_id"], elegida,
                                    elegida == p["correcta"], "simulacro_academia")
        aciertos = sum(
            1 for p in preguntas if sa["respuestas"].get(p["pregunta_id"]) == p["correcta"]
        )
        blancos = sum(1 for p in preguntas if sa["respuestas"].get(p["pregunta_id"]) is None)
        errores = len(preguntas) - aciertos - blancos

        resultado = calificar_simulacro(oposicion_id, aciertos, errores, blancos, len(preguntas))
        if resultado["disponible"]:
            if not sa["guardado"]:
                guardar_resultado_simulacro(
                    user_id, oposicion_id, "academia", len(preguntas),
                    aciertos, errores, blancos, resultado["nota"], resultado["aprobado"],
                    simulacro_academia_id=sa["simulacro_id"],
                )
                sa["guardado"] = True

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
        else:
            st.warning(resultado["motivo"])

        st.caption("Este intento ya ha quedado registrado en \"Mi progreso\" — no se permite repetirlo.")


def _panel_calibracion(oposicion_id: int, user_id: str) -> None:
    """
    ¿Sabe el alumno lo que sabe? (migración 050)

    Es la única parte de la app que no le dice si acierta, sino si **acierta
    cuando cree que va a acertar**. De ahí salen las dos decisiones que la
    fórmula A−E/3 convierte en puntos: qué repasar (lo que falla creyendo
    saberlo) y cuándo contestar a ciegas.
    """
    cal = get_calibracion(user_id, oposicion_id)
    rent = cal["rentabilidad"]

    st.subheader("🎯 ¿Sabes lo que sabes?")

    if rent["disponible"]:
        st.info(
            f"La fórmula oficial resta **{rent['penalizacion_error']:.2f}** por cada "
            f"fallo y **{rent['penalizacion_blanco']:.2f}** por cada blanco. Haciendo "
            f"la cuenta, responder te compensa siempre que aciertes más del "
            f"**{rent['umbral_pct']}%** de las veces — que es exactamente lo que "
            f"acertarías al azar entre cuatro opciones. Conclusión: **«ante la duda, "
            f"en blanco» es falso**. Si logras descartar una sola opción, tu acierto "
            f"sube al 33% y contestar ya te suma puntos."
        )

    if not cal["disponible"]:
        st.caption(
            f"{cal['motivo']} Al responder en Repaso o en el Simulacro personal, "
            f"marca 🟢 Lo sé / 🟡 Dudo / 🔴 Ni idea antes de corregir: es lo que "
            f"permite medir esto."
        )
        return

    filas = []
    for n in cal["niveles"]:
        if not n["total"]:
            continue
        pct = f"{n['pct_acierto']}%" if n["pct_acierto"] is not None else "—"
        ve = f"{n['valor_esperado']:+.2f}" if n["valor_esperado"] is not None else "—"
        filas.append({
            "Dijiste":       _ETIQUETA_CONFIANZA[n["confianza"]],
            "Veces":         n["total"],
            "En blanco":     n["blancos"],
            "Acierto":       pct + ("" if n["fiable"] else " (pocos datos)"),
            "Puntos/pregunta": ve,
        })
    if filas:
        st.dataframe(filas, hide_index=True, use_container_width=True)
        st.caption(
            "«Puntos/pregunta» es lo que ganas (o pierdes) de media cada vez que "
            "contestas con esa confianza, en la escala de la fórmula oficial. "
            "Si es negativo, esas preguntas te están restando: mejor en blanco."
        )

    graves = [d for d in cal["diagnosticos"] if d["gravedad"] == "alta"]
    otros  = [d for d in cal["diagnosticos"] if d["gravedad"] != "alta"]
    for d in graves:
        st.warning(d["texto"])
    for d in otros:
        (st.success if d["gravedad"] == "ok" else st.info)(d["texto"])

    if not cal["diagnosticos"]:
        st.caption(
            f"Aún no hay muestra suficiente para darte un diagnóstico fiable "
            f"(hacen falta {cal['min_respuestas']} respuestas en cada nivel). "
            f"Llevas {cal['total_declaradas']}. Un consejo mal fundado es peor "
            f"que ninguno, así que esperamos."
        )


def _modo_mi_progreso(oposicion_id: int, user_id: str) -> None:
    st.header("Mi progreso")

    _panel_calibracion(oposicion_id, user_id)
    st.divider()

    st.subheader("📈 Simulacros")
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


def _onboarding_perfil(user_id: str) -> bool:
    """
    Pregunta UNA sola cosa: si es su primera oposición. Devuelve True si ya está
    contestada (y se puede seguir), False si hay que esperar.

    De esta respuesta depende TODO el arranque (migración 046): a un principiante
    no se le hace la prueba de nivel (mediría el ~25% del azar y le desmotivaría
    justo en el momento más frágil), mientras que a quien viene de otra oposición
    sí — tiene conocimiento previo REAL y DESIGUAL, que es justo lo que la prueba
    detecta.
    """
    st.title("🎓 Bienvenido/a")
    st.markdown(
        "Antes de empezar, **una sola pregunta**. Nos sirve para no hacerte "
        "perder el tiempo."
    )
    exp = st.radio(
        "¿Es la primera oposición que preparas?",
        ["Sí, es mi primera oposición", "No, ya me he presentado a otras"],
        index=None,
    )
    if exp and st.button("Empezar", type="primary"):
        valor = "primera" if exp.startswith("Sí") else "otras_oposiciones"
        error = guardar_perfil_alumno(user_id, valor)
        if error:
            st.error(error)
        else:
            st.rerun()
    return False


def _bienvenida_principiante(oposicion_id: int) -> None:
    """
    Plan de partida en vez de prueba de nivel.

    A quien empieza de cero no hay nada que diagnosticarle: un test solo
    diagnostica cuando hay algo que diferenciar. Lo que sí necesita es saber
    POR DÓNDE EMPEZAR, y eso se responde con datos objetivos que ya tenemos:
    la frecuencia real de cada tema en los exámenes oficiales.
    """
    st.success(
        "**Empiezas de cero, y eso está bien.** No te vamos a hacer un examen "
        "para decirte lo que ya sabes: que aún no dominas el temario. "
        "Vamos directos a lo que importa — **por dónde empezar**."
    )
    plan = get_plan_partida(oposicion_id, n_temas=5)
    if plan:
        st.markdown("#### Tu plan de partida")
        st.caption(
            "Ordenado por lo que **más ha caído en los exámenes oficiales**. "
            "No es una estimación: es la frecuencia real."
        )
        for i, t in enumerate(plan, 1):
            veces = t["veces_en_examen"]
            st.markdown(f"**{i}. Tema {t['bloque']}.{t['tema']}** — {t['titulo'][:70]}")
            st.caption(
                f"Ha caído **{veces} vece{'s' if veces != 1 else ''}** en los últimos "
                f"exámenes · el bloque {t['bloque']} es el {t['peso_examen']}% del examen"
            )
    st.info(
        "Ve a **Repaso** y empieza por el primero. El sistema irá aprendiendo tu "
        "nivel según respondas: no hace falta que te examines antes.\n\n"
        "Si algún día quieres medirte, la **prueba de nivel** estará ahí."
    )


def _flujo_alumno(oposicion_id: int, alumno: dict) -> None:
    user_id = alumno["user_id"]

    # El perfil decide el arranque: sin él no se puede continuar (migración 046)
    perfil = get_perfil_alumno(user_id)
    if not perfil:
        _onboarding_perfil(user_id)
        return

    stats   = get_stats_alumno(user_id, oposicion_id)
    es_nuevo = not any(b["preguntas_vistas"] for b in stats["bloques"])
    principiante = perfil["experiencia"] == "primera"

    st.title("🎓 Tu preparación")
    st.caption(f"{alumno['email']}")

    if es_nuevo and principiante:
        _bienvenida_principiante(oposicion_id)
    elif es_nuevo:
        # Viene de otra oposición: aquí la prueba SÍ vale, y mucho. Tiene base
        # previa desigual (suele dominar Derecho Administrativo y no saber nada
        # de UE). Se le empuja fuerte, pero no se le obliga.
        st.info(
            "**Vienes de otra oposición**, así que ya traes base — probablemente "
            "desigual: hay bloques que dominarás y otros que verás por primera vez.\n\n"
            "Te recomendamos **encarecidamente** hacer la **prueba de nivel** (40 "
            "preguntas). Así no te haremos repetir lo que ya sabes y podremos ir "
            "directos a tus lagunas. Puedes saltártela, pero tardaremos más en "
            "descubrir tu nivel."
        )

    if "modo_alumno_radio" not in st.session_state:
        # Al principiante NO se le lleva a la prueba de nivel: se le lleva a Repaso.
        if es_nuevo and not principiante:
            st.session_state.modo_alumno_radio = "Prueba de nivel"
        else:
            st.session_state.modo_alumno_radio = "Repaso"
    if "_forzar_modo_alumno" in st.session_state:
        # No se puede reasignar la key de un widget ya instanciado en el mismo
        # rerun (StreamlitAPIException) — se consume ANTES de crear el radio.
        st.session_state.modo_alumno_radio = st.session_state.pop("_forzar_modo_alumno")

    modo_alumno = st.radio(
        "¿Qué quieres hacer?",
        ["Prueba de nivel", "Repaso", "Simulacro personal", "Simulacro academia", "Mi progreso"],
        key="modo_alumno_radio", horizontal=True,
    )
    st.divider()

    if modo_alumno == "Prueba de nivel":
        _modo_prueba_nivel(oposicion_id, user_id)
    elif modo_alumno == "Repaso":
        _modo_repaso(oposicion_id, user_id, stats)
    elif modo_alumno == "Simulacro personal":
        _modo_simulacro_personal(oposicion_id, user_id)
    elif modo_alumno == "Simulacro academia":
        _modo_simulacro_academia(oposicion_id, user_id)
    else:
        _modo_mi_progreso(oposicion_id, user_id)

# ── Sidebar: Oposición ────────────────────────────────────────────────────────
ops_opciones = {f"{o['nombre_corto'] or o['codigo']}": o for o in oposiciones}
op_seleccion = st.sidebar.selectbox("Oposición", list(ops_opciones.keys()))
oposicion_seleccionada = ops_opciones[op_seleccion]
oposicion_id = oposicion_seleccionada["oposicion_id"]

st.sidebar.markdown("---")

# ── Sidebar: Acceso ────────────────────────────────────────────────────────────
# Único punto de bifurcación: Gestión banco de preguntas (Google OAuth → Q&A,
# nuevas preguntas, revisión, test) o Alumno (Supabase Auth → prueba de nivel/
# repaso adaptativo). Sin acceso anónimo: hasta elegir uno de los dos no se
# muestra ningún contenido.
_ETIQUETA_ACCESO = {
    "administracion": "Gestión banco de preguntas",
    "alumno":         "Alumno",
}

if "acceso" not in st.session_state:
    st.session_state.acceso = None

# La elección de acceso solo ocupa sitio mientras haga falta: una vez dentro, el
# título de la página ya dice dónde estás, así que estos botones (y el rótulo
# "Acceso actual") desaparecen. Liberan ~200px justo encima de los selectores de
# trabajo, que es lo que impedía ver los 6 bloques sin hacer scroll.
if st.session_state.acceso is None:
    st.sidebar.markdown("**Acceso**")
    _cacc1, _cacc2 = st.sidebar.columns(2)
    with _cacc1:
        if st.button("Gestión banco", key="acceso_administracion", use_container_width=True):
            st.session_state.acceso = "administracion"
            st.rerun()
    with _cacc2:
        if st.button("Alumno", key="acceso_alumno", use_container_width=True):
            st.session_state.acceso = "alumno"
            st.rerun()

    st.title("⚖️ Asistente Jurídico")
    st.info(
        "Elige un tipo de acceso en la barra lateral: "
        "**Gestión banco de preguntas** o **Alumno**."
    )
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
# Camino Gestión banco de preguntas (Google OAuth)
# ══════════════════════════════════════════════════════════════════════════
if not logged_in:
    st.sidebar.markdown("**Acceso Gestión banco de preguntas**")
    st.sidebar.caption("Requiere cuenta Google autorizada (editor/academia).")
    if st.sidebar.button("Iniciar sesión con Google", key="admin_login", type="primary"):
        st.login("google")

    st.title("⚖️ Gestión banco de preguntas")
    st.info(
        "Inicia sesión con tu cuenta Google en la barra lateral para acceder "
        "a la generación y revisión de preguntas, Q&A y test."
    )
    st.stop()

# Una sesión Google válida no basta: el email debe estar en la lista blanca
# (normas.editores, migración 036). Sin esto, cualquier cuenta de Google que
# completase el OAuth tendría acceso completo de gestión.
try:
    editor = get_editor(user["email"])
except Exception as e:
    st.error(f"No se pudo verificar la autorización: {e}")
    st.stop()

if not editor:
    st.sidebar.markdown(f"👤 {user['email']}")
    if st.sidebar.button("Cerrar sesión", key="denegado_logout"):
        st.logout()

    st.title("⛔ Acceso denegado")
    st.error(
        f"La cuenta **{user['email']}** no está autorizada para gestionar el banco "
        "de preguntas. Si crees que es un error, pide al administrador que dé de "
        "alta tu cuenta."
    )
    st.info("¿Eres opositor? Pulsa **Alumno** en la barra lateral.")
    st.stop()

es_admin = editor["rol"] == "admin"

# Datos del pie; se pinta al final del sidebar (o en _parar(), si algún selector
# detiene la ejecución antes de llegar al final del script).
st.session_state["_pie_datos"] = (
    user["email"], "Administrador" if es_admin else "Editor",
)

# El modo se elige antes que nada: cada uno monta después su propio selector.
# "Editores" y "Banco y pesos" solo los ven los administradores (migración 037):
# recalcular los pesos cambia el motor y el objetivo del banco, no es cosa de un
# editor cualquiera.
_MODOS = ["Q&A", "Nuevas preguntas", "Revisar preguntas", "Generar test", "Simulacros academia"]
if es_admin:
    _MODOS += ["Banco y pesos", "Editores"]

modo = st.sidebar.radio("Modo", _MODOS)

# ── Cabecera ──────────────────────────────────────────────────────────────────
st.title("⚖️ Asistente Jurídico")
st.caption("Búsqueda semántica + Claude")

# ── Helpers BD — Banco de preguntas ───────────────────────────────────────────
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
                  AND NOT pt.descartada
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


# Nota: aquí vivía _reject(), que hacía DELETE FROM preguntas_test. Se eliminó en la
# migración 039: rechazar ya no destruye, usa retrieval.descartar_pregunta().


def _get_review_stats() -> dict:
    """Progreso de revisión global (todo el banco IA), independiente de la
    selección de leyes del sidebar — para que un supervisor vea de un
    vistazo cuánto queda y quién ha revisado qué, sin importar la sesión."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT COUNT(*) FILTER (WHERE NOT revisada) AS pendientes,
                       COUNT(*) FILTER (WHERE revisada)     AS revisadas
                FROM normas.preguntas_test
                WHERE fuente = 'ia' AND NOT descartada
            """)
            pendientes, revisadas = cur.fetchone()

            cur.execute("""
                SELECT revisado_por, COUNT(*) AS n, MAX(revisado_en) AS ultima
                FROM normas.preguntas_test
                WHERE fuente = 'ia' AND revisada AND revisado_por IS NOT NULL
                GROUP BY revisado_por
                ORDER BY n DESC
            """)
            cols = [d[0] for d in cur.description]
            por_revisor = [dict(zip(cols, row)) for row in cur.fetchall()]

    return {"pendientes": pendientes, "revisadas": revisadas, "por_revisor": por_revisor}


# ── Modo Q&A ──────────────────────────────────────────────────────────────────
if modo == "Q&A":
    _, _, leyes_sel = _selector_bloque_tema_ley(oposicion_id, "qa")
    ley_id     = leyes_sel[0]["ley_id"]
    ley_nombre = leyes_sel[0]["nombre"]

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
    leyes_sel = _selector_generar_test(oposicion_id)

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
        leyes_label = " + ".join(l["nombre_corto"] or l["nombre"] for l in leyes_sel)
        st.info(f"Ley{'es' if len(leyes_sel) > 1 else ''}: **{leyes_label}**")

        if st.button("Iniciar repaso", type="primary"):
            preguntas = get_preguntas_sm2(
                user["email"], oposicion_id,
                tuple(l["ley_id"] for l in leyes_sel), n=10,
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

# ── Modo Nuevas preguntas ─────────────────────────────────────────────────────
elif modo == "Nuevas preguntas":
    _, _, leyes_sel = _selector_bloque_tema_ley(oposicion_id, "nq")

    st.header("Nuevas preguntas")
    st.caption(f"Sesión activa: {user['email']}")

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
        ok = err = sin_tema = 0
        for ley_loop in leyes_sel:
            lid   = ley_loop["ley_id"]
            # Título oficial del BOE (migración 038). La norma obligatoria nº2 exige
            # que el enunciado cite la norma completa: con el nombre de trabajo,
            # Claude completaba la referencia de memoria unas veces sí y otras no.
            lnomb = ley_loop.get("nombre_oficial") or ley_loop["nombre"]
            arts  = _fetch_articles(lid, n_gen, max_por_art)
            if not arts:
                st.info(f"{ley_loop['codigo']}: sin artículos nuevos.")
                continue
            few_shots = _fetch_few_shots(lid)

            # Claude elige el tema oficial de cada pregunta dentro del mismo prompt
            # que la genera, y se valida contra los temas del bloque de la ley. Sin
            # esto la pregunta nace sin tema y el plan de estudio del alumno (que va
            # por tema) no la ve; era el motivo del backfill del 12/07/2026.
            bloque_ley, epigrafes = get_bloque_y_epigrafes(
                lid, oposicion_codigo=oposicion_seleccionada["codigo"],
            )
            temas_validos = {e["tema"] for e in epigrafes} if epigrafes else None
            if not epigrafes:
                st.warning(
                    f"{ley_loop['codigo']}: sin temas asociados en el programa; "
                    "sus preguntas se guardarán sin tema."
                )

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
                            epigrafes=epigrafes,
                        ),
                    )
                    parsed = _parse_and_validate(resp.content[0].text,
                                                 temas_validos=temas_validos)

                    epigrafe_id = None
                    if epigrafes and "tema" in parsed:
                        epigrafe_id = next(
                            e["epigrafe_id"] for e in epigrafes
                            if e["tema"] == parsed["tema"]
                        )
                    if epigrafe_id is None:
                        sin_tema += 1

                    _save(lid, art, parsed, epigrafe_id=epigrafe_id)
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
        if sin_tema:
            st.warning(
                f"{sin_tema} sin tema asignado. Puedes clasificarlas después con "
                "`scripts/asignar_epigrafes.py`."
            )
        if err:
            st.error(f"{err} error{'es' if err > 1 else ''} durante la generación.")
        st.cache_data.clear()

# ── Modo Revisar preguntas ────────────────────────────────────────────────────
elif modo == "Revisar preguntas":
    leyes_sel = _selector_revisar(oposicion_id)

    st.header("Revisar preguntas")
    st.caption(f"Sesión activa: {user['email']}")

    stats = _get_review_stats()
    col_pend, col_rev = st.columns(2)
    col_pend.metric("Pendientes (todo el banco)", stats["pendientes"])
    col_rev.metric("Revisadas (todo el banco)", stats["revisadas"])
    if stats["por_revisor"]:
        with st.expander(f"Desglose por supervisor ({len(stats['por_revisor'])})"):
            st.dataframe(
                [
                    {
                        "Supervisor": r["revisado_por"],
                        "Revisadas": r["n"],
                        "Última revisión": r["ultima"],
                    }
                    for r in stats["por_revisor"]
                ],
                hide_index=True,
                use_container_width=True,
            )

    pending = _get_pending([l["ley_id"] for l in leyes_sel])

    if not pending:
        st.subheader("Pendientes de revisión")
        st.info("No hay preguntas pendientes de revisión para esta selección.")
        # El contador de arriba es global: si hay trabajo en otro sitio, decir dónde
        # en vez de dejar al editor probando bloques a ciegas.
        otros = {b: n for b, n in pendientes_por_bloque(oposicion_id).items() if n}
        if otros:
            donde = " · ".join(
                f"**{_NOMBRES_BLOQUE.get(b, b)}**: {n}"
                for b, n in sorted(otros.items())
            )
            st.caption(f"Sí hay pendientes en: {donde}")
    else:
        # Solo las leyes que realmente aportan preguntas: listar las 8 del bloque
        # cuando solo 3 tienen trabajo era ruido.
        con_pendientes = sorted({p["ley_codigo"] for p in pending})
        st.subheader(f"Pendientes de revisión — {', '.join(con_pendientes)}")
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
                    # Rechazar ya NO borra (migración 039): descarta con justificación
                    # obligatoria y queda recuperable por un administrador.
                    if st.button("❌ Rechazar", key=f"ko_{pid}"):
                        st.session_state[f"confirmar_ko_{pid}"] = True

                if st.session_state.get(f"confirmar_ko_{pid}"):
                    st.warning("Vas a descartar esta pregunta. Explica por qué:")
                    motivo = st.text_area(
                        "Motivo del rechazo", key=f"motivo_{pid}",
                        placeholder="Ej.: el artículo citado no corresponde; los distractores son triviales…",
                    )
                    col_si, col_no = st.columns(2)
                    with col_si:
                        if st.button("Confirmar rechazo", key=f"ko_ok_{pid}", type="primary"):
                            error = descartar_pregunta(pid, motivo, user["email"])
                            if error:
                                st.error(error)
                            else:
                                st.session_state.pop(f"confirmar_ko_{pid}", None)
                                st.rerun()
                    with col_no:
                        if st.button("Cancelar", key=f"ko_no_{pid}"):
                            st.session_state.pop(f"confirmar_ko_{pid}", None)
                            st.rerun()

    # ── Descartadas: solo administradores (ver motivo y restaurar) ────────────
    if es_admin:
        descartadas = listar_descartadas()
        if descartadas:
            with st.expander(f"🗑️ Preguntas descartadas ({len(descartadas)})"):
                st.caption(
                    "Rechazar no borra: la pregunta queda aquí con su motivo y se "
                    "puede devolver a la cola de revisión."
                )
                for d in descartadas:
                    col_txt, col_btn = st.columns([4, 1])
                    with col_txt:
                        st.markdown(f"**[{d['ley_codigo']}] Art. {d['articulo']}** — {d['pregunta'][:90]}…")
                        st.caption(
                            f"Motivo: *{d['motivo_descarte']}* · {d['descartada_por']} · "
                            f"{d['descartada_en'].strftime('%d/%m/%Y %H:%M')}"
                        )
                    with col_btn:
                        if st.button("Restaurar", key=f"rest_{d['pregunta_id']}"):
                            error = restaurar_pregunta(d["pregunta_id"])
                            if error:
                                st.error(error)
                            else:
                                st.rerun()
                    st.divider()

# ── Modo Simulacros academia ─────────────────────────────────────────────────
elif modo == "Simulacros academia":
    st.header("Simulacros de academia")
    st.caption(
        "La academia nunca elige preguntas: al generar, la plataforma reparte "
        "proporcionalmente por el peso oficial de cada bloque, igual que el "
        "simulacro personal pero sobre todos los bloques. Autoriza el simulacro "
        "para abrir su ventana temporal a los alumnos."
    )

    with st.form("form_generar_simulacro_academia"):
        nombre_sim = st.text_input("Nombre", placeholder="Simulacro academia — julio 2026")
        n_sim = st.slider("Número de preguntas", min_value=10, max_value=100, value=50)
        col_fi, col_ff = st.columns(2)
        with col_fi:
            fecha_inicio_sim = st.date_input("Fecha inicio")
            hora_inicio_sim = st.time_input("Hora inicio", value=dtime(0, 0))
        with col_ff:
            fecha_fin_sim = st.date_input("Fecha fin")
            hora_fin_sim = st.time_input("Hora fin", value=dtime(23, 59))

        if st.form_submit_button("Generar", type="primary"):
            inicio_dt = datetime.combine(fecha_inicio_sim, hora_inicio_sim)
            fin_dt = datetime.combine(fecha_fin_sim, hora_fin_sim)
            if not nombre_sim.strip():
                st.error("Indica un nombre para el simulacro.")
            elif fin_dt <= inicio_dt:
                st.error("La fecha fin debe ser posterior a la fecha inicio.")
            else:
                simulacro_id = generar_simulacro_academia(
                    oposicion_id, nombre_sim.strip(), n_sim, inicio_dt, fin_dt,
                )
                st.success(
                    f"Simulacro #{simulacro_id} generado con {n_sim} preguntas. "
                    "Autorízalo abajo para abrirlo a los alumnos."
                )
                st.rerun()

    st.divider()
    st.subheader("Simulacros existentes")
    simulacros = listar_simulacros_academia(oposicion_id)
    if not simulacros:
        st.caption("Todavía no hay simulacros generados para esta oposición.")
    for s in simulacros:
        estado_label = "🟢 Autorizado" if s["estado"] == "autorizado" else "🟡 Generado (pendiente de autorizar)"
        st.markdown(f"**#{s['simulacro_id']} — {s['nombre']}** ({s['n_preguntas']} preguntas) — {estado_label}")
        st.caption(
            f"Ventana: {s['fecha_inicio'].strftime('%d/%m/%Y %H:%M')} → "
            f"{s['fecha_fin'].strftime('%d/%m/%Y %H:%M')}"
        )
        if s["estado"] == "generado":
            # Autorizar publica el simulacro a TODOS los alumnos: acción sensible,
            # reservada a administradores. Generar sí puede hacerlo un editor.
            if st.button("Autorizar", key=f"autorizar_sim_{s['simulacro_id']}",
                         type="primary", disabled=not es_admin,
                         help=None if es_admin else
                              "Solo un administrador puede autorizar un simulacro: "
                              "al hacerlo queda abierto a todos los alumnos."):
                autorizar_simulacro_academia(s["simulacro_id"], user["email"])
                st.rerun()
        else:
            st.caption(f"Autorizado por {s['autorizado_por']} — {s['autorizado_en'].strftime('%d/%m/%Y %H:%M')}")
        st.divider()

# ── Modo Editores (solo administradores) ─────────────────────────────────────
elif modo == "Editores":
    st.header("Editores")
    st.caption(
        "Quién puede acceder a Gestión banco de preguntas. Una cuenta Google no "
        "basta: debe estar dada de alta aquí."
    )

    # El aviso se guarda en session_state porque el st.rerun() posterior borraría
    # cualquier st.success() emitido en la misma ejecución.
    if _flash := st.session_state.pop("editores_flash", None):
        st.success(_flash)

    # ── Alta ──────────────────────────────────────────────────────────────────
    with st.form("form_alta_editor"):
        st.subheader("Dar de alta")
        col_e, col_n = st.columns(2)
        with col_e:
            nuevo_email = st.text_input(
                "Email de Google", placeholder="editor@gmail.com",
                help="La cuenta Google con la que iniciará sesión.",
            )
        with col_n:
            nuevo_nombre = st.text_input("Nombre", placeholder="Nombre Apellido")
        nuevo_rol = st.radio(
            "Rol", ["editor", "admin"], horizontal=True,
            help="admin también puede gestionar esta lista de editores.",
        )
        if st.form_submit_button("Dar de alta", type="primary"):
            error = alta_editor(nuevo_email, nuevo_nombre, nuevo_rol, user["email"])
            if error:
                st.error(error)
            else:
                st.session_state["editores_flash"] = (
                    f"{nuevo_email.strip().lower()} autorizado. Ya puede entrar con su "
                    "cuenta Google: envíale la URL de la app."
                )
                st.rerun()

    st.divider()

    # ── Listado ───────────────────────────────────────────────────────────────
    st.subheader("Editores dados de alta")
    editores = listar_editores()
    # Si solo queda un administrador activo, no puede degradarse ni revocarse: la
    # app se quedaría sin nadie capaz de gestionarla (solo recuperable por SQL).
    # La regla ya se aplica en retrieval.py; aquí solo se refleja en los botones,
    # para no ofrecer una acción que va a fallar.
    n_admins = sum(1 for x in editores if x["activo"] and x["rol"] == "admin")

    for e in editores:
        activo = e["activo"]
        soy_yo = e["email"].lower() == user["email"].lower()
        ultimo_admin = activo and e["rol"] == "admin" and n_admins == 1

        col_info, col_rol, col_accion = st.columns([3, 1.4, 1.2])
        with col_info:
            marca = "🟢" if activo else "⚪"
            etiqueta = "Administrador" if e["rol"] == "admin" else "Editor"
            nombre = e["nombre"] or "—"
            st.markdown(f"{marca} **{nombre}** · {e['email']}")
            st.caption(
                f"{etiqueta}{' · tú' if soy_yo else ''}"
                f"{'' if activo else ' · revocado'}"
            )

        if activo:
            with col_rol:
                otro_rol = "editor" if e["rol"] == "admin" else "admin"
                if st.button(f"Hacer {otro_rol}", key=f"rol_{e['email']}",
                             disabled=ultimo_admin,
                             help=("Eres el único administrador: si te quitas el rol, "
                                   "nadie podría gestionar la lista de editores. Da de "
                                   "alta a otro administrador primero.")
                                  if ultimo_admin else None):
                    error = cambiar_rol_editor(e["email"], otro_rol, user["email"])
                    if error:
                        st.error(error)
                    else:
                        st.session_state["editores_flash"] = f"{e['email']} ahora es {otro_rol}."
                        st.rerun()
            with col_accion:
                if st.button("Revocar", key=f"rev_{e['email']}",
                             disabled=soy_yo or ultimo_admin,
                             help=("No puedes revocar tu propia cuenta." if soy_yo else
                                   "Es el único administrador activo." if ultimo_admin
                                   else None)):
                    error = revocar_editor(e["email"], user["email"])
                    if error:
                        st.error(error)
                    else:
                        st.session_state["editores_flash"] = f"Acceso revocado a {e['email']}."
                        st.rerun()
        else:
            with col_accion:
                if st.button("Reactivar", key=f"react_{e['email']}"):
                    error = alta_editor(e["email"], e["nombre"], e["rol"], user["email"])
                    if error:
                        st.error(error)
                    else:
                        st.session_state["editores_flash"] = f"Acceso reactivado para {e['email']}."
                        st.rerun()
        st.divider()

    st.caption(
        "Revocar no borra la fila: conserva el rastro de qué preguntas revisó esa "
        "persona. La app impide revocar tu propia cuenta y quedarse sin ningún "
        "administrador activo."
    )

# ── Modo Banco y pesos (solo administradores) ────────────────────────────────
elif modo == "Banco y pesos":
    st.header("Banco y pesos del examen")

    # ── Cobertura del banco frente al objetivo ────────────────────────────────
    st.subheader("Cobertura del banco")
    st.caption(
        "El objetivo por bloque refleja el peso real del examen (migración 043). "
        "Sin esto, el banco se sesga hacia donde es cómodo generar, no hacia donde "
        "cae el examen. **No se cuentan las preguntas marcadas como prueba.**"
    )
    cob = get_cobertura_banco(oposicion_id)
    st.dataframe(
        [
            {
                "Bloque":      _NOMBRES_BLOQUE.get(c["bloque"], c["bloque"]),
                "% examen":    f"{c['peso_examen']}%",
                "En el banco": c["actual"],
                "Objetivo":    c["objetivo"],
                "Faltan":      c["faltan"],
                "Cobertura":   f"{c['cobertura']}%",
                "Desfase":     f"{c['desfase_pct']:+.1f} pts",
            }
            for c in cob
        ],
        hide_index=True, use_container_width=True,
    )
    _falt = sum(c["faltan"] for c in cob)
    st.caption(
        f"Banco real: **{sum(c['actual'] for c in cob)}** · "
        f"Objetivo: **{sum(c['objetivo'] for c in cob)}** · Faltan: **{_falt}**"
    )

    st.divider()

    # ── Calidad del banco: preguntas que el análisis marca como defectuosas ───
    st.subheader("Calidad del banco")
    alertas = get_alertas_calidad()
    if not alertas:
        st.caption(
            "Sin alertas. El análisis psicométrico (`scripts/analisis_items.py`) "
            "necesita respuestas de alumnos: hasta que las haya, no puede decir nada."
        )
    else:
        _ETIQ = {
            "clave_sospechosa":  ("🔴", "Clave sospechosa — puede estar MAL MARCADA"),
            "no_discrimina":     ("🟡", "No discrimina — no distingue al que sabe del que no"),
            "distractor_muerto": ("⚪", "Distractor muerto — una opción no la elige nadie"),
        }
        graves = sum(1 for a in alertas if a["alerta_calidad"] == "clave_sospechosa")
        if graves:
            st.error(
                f"**{graves} pregunta{'s' if graves > 1 else ''} con la clave sospechosa.** "
                "Los alumnos que dominan la materia las fallan más que los que no: "
                "lo más probable es que **la respuesta correcta esté mal marcada**."
            )
        for a in alertas:
            icono, texto = _ETIQ.get(a["alerta_calidad"], ("•", a["alerta_calidad"]))
            with st.expander(f"{icono} [{a['ley_codigo']}] {a['pregunta'][:70]}…"):
                st.caption(f"**{texto}**")
                st.markdown(a["pregunta"])
                st.caption(
                    f"Correcta marcada: **{a['correcta']}** · "
                    f"discriminación: **{a['discriminacion']}** "
                    f"(sobre {a['discriminacion_n']} respuestas)"
                )

    st.divider()

    # ── Recálculo de pesos: se propone, el admin autoriza ─────────────────────
    st.subheader("Recalcular los pesos del examen")
    st.caption(
        "Los pesos salen de los exámenes oficiales cargados. Si cargas un examen "
        "de otro año, el reparto real cambia. **No se recalcula solo**: un examen "
        "cargado con errores desviaría en silencio el motor y el objetivo del banco."
    )

    prop = proponer_pesos_bloque(oposicion_id)
    if not prop["posible"]:
        st.warning(prop["motivo"])
    else:
        st.markdown(
            f"Calculado sobre **{prop['n_preguntas']}** preguntas de: "
            f"**{', '.join(prop['examenes'])}** "
            f"(suelo del bloque menor: {prop['suelo']} preguntas)."
        )
        st.dataframe(
            [
                {
                    "Bloque":     _NOMBRES_BLOQUE.get(b, b),
                    "Peso ahora": prop["pesos_antes"].get(b, "—"),
                    "Propuesto":  prop["pesos"][b],
                    "Objetivo":   prop["objetivos"][b],
                }
                for b in ("I", "II", "III", "IV", "V", "VI")
            ],
            hide_index=True, use_container_width=True,
        )

        if not prop["cambia"]:
            st.success("Los pesos vigentes ya coinciden con los exámenes cargados. No hay nada que aplicar.")
        else:
            st.warning(
                "Aplicar esto cambia **el reparto de la prueba de nivel y de los "
                "simulacros** y **el objetivo del banco**. Revisa la tabla antes de continuar."
            )
            if st.button("Aplicar los pesos propuestos", type="primary", key="btn_aplicar_pesos"):
                error = aplicar_pesos_bloque(oposicion_id, prop, user["email"])
                if error:
                    st.error(error)
                else:
                    st.success("Pesos aplicados y registrados en el histórico.")
                    st.rerun()

    # ── Histórico de recálculos (auditoría) ───────────────────────────────────
    hist = get_historial_pesos(oposicion_id)
    if hist:
        with st.expander(f"Histórico de recálculos ({len(hist)})"):
            for h in hist:
                st.markdown(
                    f"**{h['aplicado_en'].strftime('%d/%m/%Y %H:%M')}** — {h['aplicado_por']}"
                )
                st.caption(
                    f"Sobre {h['n_preguntas']} preguntas de: {h['examenes']} · "
                    f"suelo {h['suelo']}"
                )
                st.caption(f"Antes: {h['pesos_antes']} → Después: {h['pesos_despues']}")
                st.divider()


# ── Pie del sidebar (siempre el último) ──────────────────────────────────────
_pie_sidebar()
