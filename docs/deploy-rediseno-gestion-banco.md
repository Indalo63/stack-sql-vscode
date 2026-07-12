# Puesta en producción — Rediseño "Gestión banco de preguntas" (12/07/2026)

Guía paso a paso para llevar a Streamlit Cloud el rediseño de navegación del perfil
de gestión (commits `75da266` y `36bc635`).

## Resumen: qué hace falta realmente

**Este cambio no necesita ni migraciones de base de datos ni secrets nuevos.**
Es solo código Python. Conviene tenerlo claro antes de tocar el dashboard:

| ¿Hace falta…? | | Por qué |
|---|---|---|
| Migración SQL | ❌ No | No hay tablas ni columnas nuevas. `get_preguntas_sm2` cambia de firma, pero consulta columnas que ya existían (`preguntas_test.ley_id`). |
| Secret nuevo | ❌ No | No se ha añadido ninguna variable de entorno ni clave de API. |
| Cambiar `DB_*` | ❌ No | Producción sigue conectando igual que antes. **No lo toques si la app funciona** (ver "Errores comunes" abajo). |
| Push a `master` | ✅ Sí | **Ya hecho** (`36bc635`). Es el único paso que despliega algo. |

Es decir: el despliegue ya está lanzado. Los pasos siguientes son **confirmar que
llegó bien** y **verificar que funciona**.

---

## Paso 1 — Confirmar que Streamlit Cloud ha redesplegado

Streamlit Cloud vigila la rama `master` y redespliega solo al detectar un push.

1. Entra en [share.streamlit.io](https://share.streamlit.io) con tu cuenta GitHub.
2. Abre la app y pulsa **Manage app** (abajo a la derecha) para ver los logs.
3. Busca en los logs que haya arrancado con el commit nuevo. Señales de que fue bien:
   - No aparecen tracebacks de Python.
   - Se ve el arranque de Uvicorn / "You can now view your Streamlit app".

**Si sigue mostrando la versión antigua** tras un par de minutos: en el menú de la app,
**Reboot app**. Eso fuerza a releer el repositorio.

> Nota: no basta con recargar el navegador ni con cerrar sesión. Si el contenedor de
> la app no se ha reiniciado, seguirá ejecutando el código viejo.

## Paso 2 — Verificar el cambio en la interfaz

Entra en la app y comprueba, en este orden:

1. **Pantalla de acceso**: el botón dice **"Gestión banco de preguntas"** (antes decía
   "Administración"). Si sigue diciendo "Administración", el redespliegue no ha ocurrido
   → vuelve al Paso 1.
2. **Inicia sesión con Google** (cuenta de editor/academia autorizada).
3. **Sidebar → Modo**: deben aparecer **cinco** opciones y ninguna llamada "Editor":
   - Q&A
   - Nuevas preguntas
   - Revisar preguntas
   - Generar test
   - Simulacros academia
4. **Revisar preguntas**: arriba el panel con *Pendientes / Revisadas (todo el banco)*, y
   en el sidebar un filtro **"Filtrar por"** con Bloque / Tema (excluyentes).
   Aquí es donde revisas las 60-70 preguntas pendientes.
5. **Generar test**: en el sidebar debe pedir **Bloque** (uno solo) → **"Generar por"**
   Tema o Ley → y luego marcar varios temas o leyes. Nunca genera sobre el bloque
   completo sin acotar.
6. **Nuevas preguntas**: cascada Bloque → Tema → Ley, con multi-selección en los tres.

## Paso 3 — Comprobar los Secrets (solo si algo falla)

El orden que ya tienes es **correcto** (verificado contra el fichero local que funciona):

```toml
OPENAI_API_KEY    = "..."
ANTHROPIC_API_KEY = "..."

DB_HOST     = "..."
DB_PORT     = "..."
DB_NAME     = "..."
DB_USER     = "..."
DB_PASSWORD = "..."

SUPABASE_URL      = "..."
SUPABASE_ANON_KEY = "..."

[auth]
redirect_uri  = "https://<tu-app>.streamlit.app/oauth2callback"
cookie_secret = "..."

[auth.google]
client_id           = "..."
client_secret       = "..."
server_metadata_url = "..."
```

**La regla de TOML que importa**: todas las claves sueltas (`OPENAI_API_KEY`, `DB_*`,
`SUPABASE_*`) tienen que ir **antes** de la primera cabecera `[seccion]`. En cuanto se
abre `[auth]`, todo lo que venga detrás se anida dentro de esa sección. Si
`SUPABASE_URL` cayera debajo de `[auth]`, el código no la encontraría y el registro de
alumnos fallaría con "no configurados" (este bug ya ocurrió en local, ver CLAUDE.md).

## Paso 4 — Si algo sale mal: volver atrás

El rollback es un `git revert` del commit de navegación (no borres historial):

```bash
git revert 36bc635        # deshace el rediseño de navegación
git push
```

Streamlit Cloud redesplegará solo con la versión anterior. El commit `75da266`
(helper de conexión) es independiente y no afecta a producción — no hace falta revertirlo.

---

## Errores comunes

**"He cambiado el código pero producción sigue igual."**
Casi siempre significa que los cambios no están en GitHub. Streamlit Cloud despliega
desde el repositorio, no desde tu máquina: si el commit no está pusheado a `master`,
producción no puede verlo por mucho que reinicies la app.

**No cambies `DB_HOST`/`DB_USER` a los del Session Pooler "por si acaso".**
En **producción** se usa la conexión **directa** a propósito: Streamlit Cloud resuelve
IPv6 correctamente. El rodeo por el Session Pooler
(`aws-1-eu-west-2.pooler.supabase.com`, usuario `postgres.<ref>`) es necesario **solo en
desarrollo** (WSL2 y el devcontainer no tienen salida IPv6). Cambiarlo en producción sin
motivo puede romper una conexión que funciona.

**El login de Google falla en producción pero va en local.**
Revisa que `redirect_uri` en `[auth]` apunte a la URL de Streamlit Cloud (no a
`localhost`) y que esa misma URL esté dada de alta en Google Cloud Console →
Credenciales → OAuth → *URIs de redirección autorizados*.
