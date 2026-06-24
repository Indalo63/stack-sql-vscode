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

## Fase 1 — Supabase (base de datos en la nube)

### 1.1 Crear el proyecto

1. Entra en [supabase.com](https://supabase.com) y crea una cuenta gratuita.
2. **New project** → elige nombre (`asistente-juridico`), contraseña segura, región **West EU (Ireland)**.
3. Espera ~2 minutos a que el proyecto arranque.

### 1.2 Anotar las credenciales

Ve a **Project Settings → Database → Connection string → URI** y copia:

```
postgresql://postgres:<PASSWORD>@db.<PROJECT_REF>.supabase.co:5432/postgres
```

También anota los valores individuales (los necesitarás en `.streamlit/secrets.toml`):
- `DB_HOST`: `db.<PROJECT_REF>.supabase.co`
- `DB_PORT`: `5432`
- `DB_NAME`: `postgres`
- `DB_USER`: `postgres`
- `DB_PASSWORD`: tu contraseña

### 1.3 Migrar el schema y los datos

Desde WSL2, con Docker local en marcha:

```bash
# Instala el cliente PostgreSQL si no lo tienes
sudo apt install postgresql-client -y

# Ejecuta la migración
export SUPABASE_URL="postgresql://postgres:<PASSWORD>@db.<REF>.supabase.co:5432/postgres"
bash scripts/migrate_to_supabase.sh
```

El script:
1. Hace `pg_dump` del schema `normas.*` en local
2. Habilita la extensión `vector` en Supabase
3. Carga el dump en Supabase
4. Verifica el conteo de artículos por ley

### 1.4 Verificar en Supabase

En el **Table Editor** de Supabase deberías ver las tablas `normas.leyes`, `normas.articulos`, etc. con todos los datos.

---

## Fase 2 — Streamlit Cloud (frontend)

### 2.1 Subir el código a GitHub

```bash
git add app/config.py app/retrieval.py app/qa_pipeline.py app/test_pipeline.py
git add requirements.txt .gitignore .streamlit/
git add scripts/migrate_to_supabase.sh
git commit -m "Prepara el proyecto para deploy en Streamlit Cloud + Supabase"
git push origin main
```

> El archivo `.streamlit/secrets.toml` está en `.gitignore` y NO se sube. Las credenciales van en el dashboard de Streamlit Cloud.

### 2.2 Crear la app en Streamlit Cloud

1. Ve a [share.streamlit.io](https://share.streamlit.io) e inicia sesión con GitHub.
2. **New app** → selecciona el repositorio `stack-sql-vscode`.
3. Configura:
   - **Main file path**: `app/streamlit_app.py`
   - **Branch**: `main`
4. Pulsa **Deploy** (fallará porque aún no hay secrets — es normal).

### 2.3 Configurar los secrets en Streamlit Cloud

En el dashboard de tu app: **Settings → Secrets** y pega:

```toml
OPENAI_API_KEY    = "sk-..."
ANTHROPIC_API_KEY = "sk-ant-..."

DB_HOST     = "db.<PROJECT_REF>.supabase.co"
DB_PORT     = "5432"
DB_NAME     = "postgres"
DB_USER     = "postgres"
DB_PASSWORD = "<tu-password-supabase>"
```

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
