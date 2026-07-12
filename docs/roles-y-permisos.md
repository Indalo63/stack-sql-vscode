# Roles y permisos — auditoría del estado actual

> **Qué es esto:** radiografía de lo que existe **hoy** (12/07/2026), no de lo que debería
> existir. Todo lo aquí descrito está verificado contra la base de datos y el código, no
> asumido. Si cambias los permisos, actualiza este documento.

---

## Resumen en una frase

Solo existen **dos roles reales**: `admin` y `editor` (tabla `normas.editores`). **"Alumno"
no es un rol** —es una cuenta de Supabase Auth sin tabla ni rol propio— y **"academia" no
existe como perfil**: sus funciones las ejerce cualquier editor.

---

## 1. Roles que existen de verdad

| Perfil | ¿Dónde vive? | ¿Es un rol? |
|---|---|---|
| **Administrador** | `normas.editores.rol = 'admin'` | ✅ Sí |
| **Editor** | `normas.editores.rol = 'editor'` | ✅ Sí |
| **Alumno** | Supabase Auth (`auth.users`) | ❌ No — no hay tabla ni rol; solo una cuenta |
| **Academia** | — | ❌ **No existe** (ver §4) |

**Estado actual de la tabla:** 1 administrador activo, 0 editores.

Cómo se aplica el control (`app/streamlit_app.py`):
1. Google OAuth válido → hay sesión.
2. `get_editor(email)` → el email debe estar en `normas.editores` con `activo = TRUE`. Si no,
   **"⛔ Acceso denegado"** y no ve nada.
3. `es_admin = editor["rol"] == "admin"` → decide si aparece el modo "Editores".

---

## 2. Qué puede hacer cada perfil

### Administrador (`rol = 'admin'`)
Todo lo del editor, **más**:

| Acción | Dónde |
|---|---|
| Dar de alta editores (y elegir su rol) | Modo **Editores** |
| Revocar y reactivar editores | Modo **Editores** |
| Cambiar el rol de otros (admin ↔ editor) | Modo **Editores** |

**Límites (protección anti-bloqueo, en `retrieval.py`, no solo en los botones):**
- No puede revocarse a sí mismo.
- No puede dejar **cero administradores activos** (ni revocando ni degradando al último).

### Editor (`rol = 'editor'`)

| Acción | Dónde | Nota |
|---|---|---|
| Consultar la normativa (Q&A) | Modo **Q&A** | Consume API de Claude |
| **Generar** preguntas con IA | Modo **Nuevas preguntas** | Consume API de Claude; escribe en `preguntas_test` |
| **Aprobar** preguntas | Modo **Revisar preguntas** | Marca `revisada = TRUE`; queda registrado en `revisado_por` |
| **Borrar** preguntas ⚠️ | Modo **Revisar preguntas** | El botón "Rechazar" hace `DELETE`, **no** es reversible |
| Practicar test (repaso SM-2) | Modo **Generar test** | |
| **Generar** simulacros de academia | Modo **Simulacros academia** | |
| **Autorizar** simulacros de academia ⚠️ | Modo **Simulacros academia** | Los abre a **todos** los alumnos |

**No puede:** ver ni tocar el modo "Editores" (no aparece en su barra lateral).

### Alumno (cuenta de Supabase Auth, sin rol)

Se registra solo con email y contraseña. No requiere autorización de nadie.

| Puede | No puede |
|---|---|
| Hacer la prueba de nivel | Ver preguntas **no revisadas** (todas las consultas exigen `revisada = TRUE`) |
| Repaso adaptativo por tema/bloque | Generar, editar ni aprobar preguntas |
| Simulacro personal | Acceder a ningún modo de gestión |
| Simulacro de academia (si está autorizado y en ventana) | Repetir un simulacro de academia (1 intento) |
| Ver su progreso e historial | |

Escribe en: `progreso_usuario`, `plan_estudio`, `historial_simulacros` — siempre con su
propio email como `user_id`.

---

## 3. Capa de base de datos: **no aplica ningún permiso**

Esto es lo más importante del documento.

| Aspecto | Estado |
|---|---|
| **Row Level Security (RLS)** | ❌ **Ninguna tabla de `normas.*` lo tiene activado** |
| **Usuario de conexión de la app** | `postgres` (permisos totales sobre el esquema) |
| **`SUPABASE_ANON_KEY`** | Se usa **solo** para Supabase Auth (registro y login), no para leer/escribir datos |
| **Roles de Postgres** | Solo los que crea Supabase por defecto (`postgres`, `authenticator`, `supabase_*`); **ninguno modela** admin/editor/alumno |

**Consecuencia:** *toda* la autorización vive en el código de Streamlit. La base de datos no
distingue entre un administrador, un editor y un alumno — cualquiera que tenga la contraseña
de `DB_PASSWORD` tiene acceso total.

Esto no es necesariamente un fallo (es una app monolítica con un único backend de confianza),
pero conviene tenerlo presente:
- El aislamiento de los datos de un alumno **no lo garantiza la base de datos**: lo garantiza
  que la app le pase su propio email. Un error de código podría exponer datos de otro alumno.
- Un futuro frontend que hablara con Supabase directamente (sin pasar por Streamlit) **no
  tendría ninguna protección**. Ahí sí haría falta RLS.

---

## 4. "Academia": no es un perfil

No existe ningún rol de academia. Lo que hay son dos columnas sueltas:

| Dónde | Qué es | Estado |
|---|---|---|
| `normas.editores.academia` | Columna reservada para el futuro modelo B2B (multi-academia) | **Vacía**, sin usar |
| `normas.simulacros_academia.academia` | Un texto con el nombre de la academia del simulacro | Descriptivo, no da permisos |

**Quién ejerce hoy las funciones de "academia":** cualquier **editor** (no hace falta ser
admin) puede generar y autorizar simulacros de academia. Autorizar uno lo abre a **todos**
los alumnos de la oposición, sin distinguir a qué academia pertenecen — porque esa relación
alumno↔academia **no existe** en el esquema.

---

## 5. Puntos de atención (hechos, no propuestas)

1. **Cualquier editor puede borrar preguntas de forma irreversible.** El botón "Rechazar" del
   modo Revisar hace un `DELETE`, no un borrado lógico. No hay papelera ni auditoría de quién
   borró qué (sí la hay de quién *aprobó*: `revisado_por` / `revisado_en`).
2. **Cualquier editor puede autorizar un simulacro de academia**, lo que lo abre a todos los
   alumnos. No está restringido a administradores.
3. **No hay relación alumno↔academia**, así que no se puede acotar un simulacro a los alumnos
   de una academia concreta.
4. **El registro de alumnos es abierto**: cualquiera con la URL puede crearse una cuenta.
5. **La base de datos no aplica permisos** (§3).

---

## Cómo comprobar esto tú mismo

```sql
-- Roles reales y quién los tiene
SELECT email, nombre, rol, activo FROM normas.editores ORDER BY rol, email;

-- ¿Alguna tabla protegida con RLS?  (hoy: ninguna)
SELECT c.relname, c.relrowsecurity
FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
WHERE n.nspname = 'normas' AND c.relkind = 'r' AND c.relrowsecurity;
```
