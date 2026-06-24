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

En el dashboard de tu app: **Settings → Secrets** y pega:

```toml
OPENAI_API_KEY    = "sk-..."
ANTHROPIC_API_KEY = "sk-ant-..."

DB_HOST     = "db.cbiwhcfkaarnhenkryza.supabase.co"
DB_PORT     = "5432"
DB_NAME     = "postgres"
DB_USER     = "postgres"
DB_PASSWORD = "<tu-password-supabase>"
```

> Nota: para la **app en producción** se usa la conexión directa (no el session pooler), ya que Streamlit Cloud soporta IPv6 correctamente.

Pulsa **Save** y la app se redesplegará automáticamente.

### 2.4 Acceso para alumnos

La URL pública será `https://<tu-app>.streamlit.app`. Puedes compartirla directamente.

Para acceso restringido por contraseña, añade en los secrets:

```toml
[auth]
password = "una-clave-compartida"
```

Y en `app/streamlit_app.py`, añade al inicio (antes del título):

```python
import hmac

def check_password():
    def password_entered():
        if hmac.compare_digest(st.session_state["password"], st.secrets["auth"]["password"]):
            st.session_state["password_correct"] = True
        else:
            st.session_state["password_correct"] = False

    if st.session_state.get("password_correct", False):
        return True
    st.text_input("Contraseña", type="password", on_change=password_entered, key="password")
    if "password_correct" in st.session_state:
        st.error("Contraseña incorrecta")
    return False

if not check_password():
    st.stop()
```

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
