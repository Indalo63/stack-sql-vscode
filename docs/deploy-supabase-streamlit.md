# Deploy: Supabase + Streamlit Cloud

Guía para llevar el Asistente Jurídico de Docker local a producción en la nube.

## Arquitectura objetivo

```
Alumno (navegador)
      ↓
Streamlit Cloud  (app/streamlit_app.py)
      ↓
Supabase PostgreSQL + pgvector  (schema normas.*)
```

---

## Fase 1 — Supabase (base de datos en la nube) ✅ COMPLETADA

### 1.1 Crear el proyecto ✅

1. Cuenta creada en [supabase.com](https://supabase.com) con GitHub (`Indalo63`).
2. Proyecto creado: `asistente-juridico`, región **Europe (West EU)**.
3. Referencia del proyecto: `cbiwhcfkaarnhenkryza`

### 1.2 Credenciales ✅

Guardadas en `.streamlit/secrets.toml` (excluido de Git):
- `DB_HOST`: `db.cbiwhcfkaarnhenkryza.supabase.co`
- `DB_PORT`: `5432`
- `DB_NAME`: `postgres`
- `DB_USER`: `postgres`
- `DB_PASSWORD`: (en secrets.toml local)

Para la conexión directa desde la app se usa el host de conexión directa (soporta IPv6, funciona en Streamlit Cloud).

### 1.3 Migrar el schema y los datos ✅

**Problema conocido — IPv6 en WSL2**: la conexión directa de Supabase usa IPv6 por defecto. WSL2 no lo soporta. Solución: usar el **Session pooler** para la migración y mover la extensión `vector` al schema `public`.

Pasos realizados:

```bash
# 1. Instalar cliente PostgreSQL
sudo apt install postgresql-client -y

# 2. Habilitar extensión vector en Supabase (desde el dashboard)
# Database → Extensions → vector → Enable (schema: extensions)

# 3. Mover vector al schema public (necesario porque el dump referencia public.vector)
psql "$SUPABASE_URL" -c "ALTER EXTENSION vector SET SCHEMA public;"

# 4. Ejecutar migración usando Session pooler (IPv4)
export SUPABASE_URL="postgresql://postgres.cbiwhcfkaarnhenkryza:<PASSWORD>@aws-1-eu-west-2.pooler.supabase.com:5432/postgres"
bash scripts/migrate_to_supabase.sh
```

Dump resultante: 28 MB, 6 leyes con embeddings, migración exitosa.

### 1.4 Verificación ✅

Schema `normas.*` en Supabase con tablas: `leyes`, `articulos`, `capitulos`, `secciones`, `titulos`, `fragmentos_documento`, `documentos`, `versiones_ley`.

---

## Fase 2 — Streamlit Cloud (frontend)

### 2.1 Subir el código a GitHub ✅

Repositorio: `https://github.com/Indalo63/stack-sql-vscode` (rama `master`)

```bash
git add app/config.py app/retrieval.py app/qa_pipeline.py app/test_pipeline.py
git add requirements.txt .gitignore
git add scripts/migrate_to_supabase.sh docs/deploy-supabase-streamlit.md
git commit -m "Prepara deploy en Streamlit Cloud + Supabase"
git push -u origin master
```

> El archivo `.streamlit/secrets.toml` está en `.gitignore` y NO se sube. Las credenciales van en el dashboard de Streamlit Cloud.

### 2.2 Crear la app en Streamlit Cloud

1. Ve a [share.streamlit.io](https://share.streamlit.io) e inicia sesión con GitHub (`Indalo63`).
2. **Create app** → **Deploy a public app from GitHub**.
3. Configura:
   - **Repository**: `Indalo63/stack-sql-vscode`
   - **Branch**: `master`
   - **Main file path**: `app/streamlit_app.py`
4. Pulsa **Deploy** (puede fallar hasta configurar los secrets — es normal).

### 2.3 Configurar los secrets en Streamlit Cloud

En el dashboard de tu app: **Settings → Secrets**. El contenido completo (los valores
reales viven en tu `.streamlit/secrets.toml` local, nunca en este repositorio):

```toml
OPENAI_API_KEY    = "sk-..."
ANTHROPIC_API_KEY = "sk-ant-..."

DB_HOST     = "db.<ref>.supabase.co"
DB_PORT     = "5432"
DB_NAME     = "postgres"
DB_USER     = "postgres"
DB_PASSWORD = "<tu-password-supabase>"

SUPABASE_URL      = "https://<ref>.supabase.co"
SUPABASE_ANON_KEY = "<clave-anon>"

[auth]
redirect_uri  = "https://<tu-app>.streamlit.app/oauth2callback"
cookie_secret = "<cadena-aleatoria-larga>"

[auth.google]
client_id           = "<client-id>.apps.googleusercontent.com"
client_secret       = "<client-secret>"
server_metadata_url = "https://accounts.google.com/.well-known/openid-configuration"
```

> ⚠️ **El orden importa (regla de TOML).** Todas las claves sueltas (`OPENAI_API_KEY`,
> `DB_*`, `SUPABASE_*`) deben ir **antes** de la primera cabecera `[seccion]`. En cuanto
> se abre `[auth]`, todo lo que venga detrás se anida dentro de esa sección: si
> `SUPABASE_URL` cayera debajo, el código la buscaría en la raíz, no la encontraría, y el
> registro de alumnos fallaría con "no configurados". Este bug ya ocurrió una vez en local.

> Nota sobre la conexión: en **producción** se usa la conexión **directa**, porque
> Streamlit Cloud resuelve IPv6 correctamente. El rodeo por el **Session Pooler**
> (`aws-1-eu-west-2.pooler.supabase.com`, usuario `postgres.<ref>`) hace falta **solo en
> desarrollo** (WSL2 y el devcontainer no tienen salida IPv6). No cambies `DB_HOST`/
> `DB_USER` en producción si la app conecta bien.

Pulsa **Save** y la app se redesplegará automáticamente.

### 2.4 Acceso a la app

**No hay acceso anónimo.** Al entrar, el sidebar obliga a elegir uno de los dos perfiles,
y hasta entonces la app no muestra ningún contenido. Cada perfil usa su propio sistema de
autenticación:

| Perfil | Quién | Autenticación | Configuración |
|---|---|---|---|
| **Gestión banco de preguntas** | Editor / academia | **Google OAuth** (`st.login("google")`) | Secciones `[auth]` y `[auth.google]` de los secrets |
| **Alumno** | Opositor | **Supabase Auth** (email + contraseña) | Claves `SUPABASE_URL` y `SUPABASE_ANON_KEY` |

La URL pública (`https://<tu-app>.streamlit.app`) se puede compartir con los alumnos:
ellos se registran solos con email y contraseña. El acceso de gestión queda protegido por
Google OAuth aunque la URL sea pública.

> ⚠️ **`[auth]` es una sección reservada de Streamlit** (su OAuth nativo). No metas ahí
> claves propias: manipular esa sección puede invalidar el login de Google. En particular,
> **no existe ninguna contraseña compartida** en esta app — versiones antiguas de este
> documento proponían una función `check_password()` que **nunca se implementó** y quedó
> obsoleta al llegar Google OAuth y Supabase Auth.

**Para que el login de Google funcione en producción**, la `redirect_uri` debe estar
registrada en Google Cloud Console → Credenciales → OAuth → *URIs de redirección
autorizados*. Si no, fallará en producción aunque funcione en local.

#### Quién puede entrar como editor: lista blanca en BD

**Una sesión Google válida no basta.** El email debe estar además en la tabla
`normas.editores` con `activo = TRUE` (migración 036). Si no lo está, la app muestra
"⛔ Acceso denegado" y no deja ver ningún dato ni opción de gestión.

Hay dos roles (columna `rol`, migración 037):

- **`admin`** — además de todo lo anterior, gestiona la lista de editores desde la app.
- **`editor`** — genera y revisa preguntas, pero no ve la pantalla de gestión.

**Dar de alta a un editor nuevo:** desde la app, modo **"Editores"** (solo visible para
admins). No se generan ni se envían credenciales: el editor entra con **su propia cuenta
de Google**. El flujo es:

1. El editor te dice con qué cuenta de Google va a entrar.
2. Lo das de alta en "Editores" (email + nombre + rol).
3. Si la pantalla de consentimiento de OAuth sigue en modo *Testing*, añádelo **también**
   como usuario de prueba en Google Cloud Console, o Google le cortará el paso antes
   siquiera de llegar a la app.
4. Le envías la URL. **Autoriza antes de enviarla**, o verá "Acceso denegado".

**Revocar el acceso:** botón "Revocar" en esa misma pantalla. No borra la fila (conserva
el rastro de qué preguntas revisó, `preguntas_test.revisado_por`) y se puede reactivar.
La app impide revocar tu propia cuenta y quedarse sin ningún administrador activo.

> Esto no exime de configurar bien la pantalla de consentimiento de OAuth en Google Cloud
> Console, pero ya no es la única barrera: aunque esa pantalla se publicara a producción y
> cualquier usuario de Google pudiera completar el OAuth, una cuenta que no esté en
> `normas.editores` no pasaría de "Acceso denegado".

---

## Fase 3 — Sincronización BOE automática (opcional)

El script `scripts/sync_boe.py` puede ejecutarse como tarea programada en GitHub Actions:

Crea el archivo `.github/workflows/sync_boe.yml`:

```yaml
name: Sincronización BOE semanal
on:
  schedule:
    - cron: '0 6 * * 1'  # Lunes a las 06:00 UTC
  workflow_dispatch:

jobs:
  sync:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - run: python scripts/sync_boe.py
        env:
          DB_HOST: ${{ secrets.DB_HOST }}
          DB_PORT: ${{ secrets.DB_PORT }}
          DB_NAME: ${{ secrets.DB_NAME }}
          DB_USER: ${{ secrets.DB_USER }}
          DB_PASSWORD: ${{ secrets.DB_PASSWORD }}
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
```

Añade los mismos secrets en **GitHub → Settings → Secrets → Actions**.

---

## Resumen de costes estimados

| Servicio | Plan | Coste |
|---|---|---|
| Supabase | Free (500 MB, 2 proyectos) | 0 €/mes |
| Streamlit Cloud | Community (1 app pública) | 0 €/mes |
| GitHub Actions | Free (2000 min/mes) | 0 €/mes |
| OpenAI embeddings | ~0,02 € / 1M tokens | < 1 €/mes |
| Claude API | Según uso Q&A/test | ~1–5 €/mes |
