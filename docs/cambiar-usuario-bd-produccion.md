# Cambiar la app al usuario de BD con permisos mínimos (producción)

Guía para llevar a producción la **migración 040**: que Streamlit Cloud deje de conectar como
`postgres` y pase a usar `app_asistente`.

> **Estado:** el rol `app_asistente` **ya está creado en Supabase** y **ya está probado**
> (la app funciona entera con él, y no puede borrar tablas ni datos). Lo único que falta es
> cambiar dos valores en los secrets de Streamlit Cloud. **Producción sigue conectando como
> `postgres` hasta que hagas este cambio.**

---

## Por qué

| Hoy (`postgres`) | Después (`app_asistente`) |
|---|---|
| Puede **borrar tablas** (`DROP`) | ❌ No puede |
| Puede **borrar datos** (`DELETE`, `TRUNCATE`) | ❌ No puede |
| Se **salta** el Row Level Security | ❌ No se lo salta |

La app **no necesita ninguno de esos permisos** (se comprobó: no hace ningún `DELETE` ni
ningún DDL). Con este cambio, un bug o una inyección SQL ya no pueden destruir el esquema.

---

## Pasos

### 1. Consigue la contraseña

La contraseña se generó al azar al crear el rol y **no está en este repositorio** (a
propósito). Si no la tienes a mano, genera una nueva desde el **SQL Editor de Supabase**:

```sql
ALTER ROLE app_asistente PASSWORD 'pon-aqui-una-contrasena-larga-y-aleatoria';
```

### 2. Cambia dos valores en los secrets de Streamlit Cloud

En el dashboard de tu app: **Settings → Secrets**. Cambia **solo estas dos líneas**:

```toml
DB_USER     = "app_asistente"          # antes: "postgres"
DB_PASSWORD = "<la contraseña del paso 1>"
```

⚠️ **No toques `DB_HOST`, `DB_PORT` ni `DB_NAME`.** Y respeta el orden del fichero: las claves
sueltas van **antes** de `[auth]` (ver `deploy-supabase-streamlit.md` §2.3).

> **Si tu producción conectara por el Session Pooler** (no es el caso hoy: usa conexión
> directa), el usuario tendría que escribirse como `app_asistente.<ref-del-proyecto>`, no
> como `app_asistente` a secas.

Pulsa **Save**. La app se redesplegará sola.

### 3. Comprueba que sigue funcionando

Entra en la app y verifica lo básico:
- Carga la lista de leyes (lee la BD).
- **Revisar preguntas**: se ve la cola de pendientes.
- **Aprobar** una pregunta (escribe en la BD).
- **Editores**: se ve el listado.

Si algo falla con un error de permisos, avisa: significa que la app necesita un permiso que
no le concedimos, y basta con añadir ese `GRANT` concreto (no hay que volver a `postgres`).

### 4. Rollback (si hiciera falta)

Vuelve a poner en los secrets el usuario y contraseña anteriores:

```toml
DB_USER     = "postgres"
DB_PASSWORD = "<la contraseña de postgres de siempre>"
```

La app vuelve a funcionar como antes. El rol `app_asistente` puede quedarse creado sin causar
ningún problema.

---

## Qué NO cambia

- **Las migraciones se siguen aplicando como `postgres`** desde el SQL Editor de Supabase.
  `app_asistente` no puede (ni debe) crear ni alterar tablas.
- Los scripts de mantenimiento del repo (`scripts/*.py` con `--supabase`) leen
  `.streamlit/secrets.toml`. Si cambias también el fichero local, los que necesiten borrar
  filas dejarán de funcionar — eso es lo esperado, y para esas tareas se usa `postgres`.
