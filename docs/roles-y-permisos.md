# Roles y permisos — auditoría del estado actual

> **Qué es esto:** radiografía de lo que existe **hoy** (12/07/2026), no de lo que debería
> existir. Todo lo aquí descrito está verificado contra la base de datos y el código, no
> asumido. Si cambias los permisos, actualiza este documento.

---

## Resumen en una frase

Solo existen **dos roles reales**: `admin` y `editor` (tabla `normas.editores`). **"Alumno"
no es un rol** —es una cuenta de Supabase Auth sin tabla ni rol propio— y **"academia" no
existe como perfil**: generar sus simulacros lo hace un editor, y autorizarlos, un administrador.

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
| Ver y **restaurar** preguntas descartadas (con su motivo y autor) | Modo **Revisar preguntas** |
| **Autorizar** simulacros de academia (los abre a todos los alumnos) | Modo **Simulacros academia** |

**Límites (protección anti-bloqueo, en `retrieval.py`, no solo en los botones):**
- No puede revocarse a sí mismo.
- No puede dejar **cero administradores activos** (ni revocando ni degradando al último).

### Editor (`rol = 'editor'`)

| Acción | Dónde | Nota |
|---|---|---|
| Consultar la normativa (Q&A) | Modo **Q&A** | Consume API de Claude |
| **Generar** preguntas con IA | Modo **Nuevas preguntas** | Consume API de Claude; escribe en `preguntas_test` |
| **Aprobar** preguntas | Modo **Revisar preguntas** | Marca `revisada = TRUE`; queda registrado en `revisado_por` |
| **Rechazar** preguntas | Modo **Revisar preguntas** | Borrado **lógico** con justificación obligatoria (039). No destruye: queda registrado quién, cuándo y por qué |
| Practicar test (repaso SM-2) | Modo **Generar test** | |
| **Generar** simulacros de academia | Modo **Simulacros academia** | |

**No puede:**
- Ver ni tocar el modo "Editores" (no aparece en su barra lateral).
- **Autorizar** simulacros de academia (botón deshabilitado): publicarlos a todos los alumnos
  es cosa de administradores.
- Ver ni restaurar las preguntas descartadas.
- **Borrar nada de la base de datos** (el usuario `app_asistente` no tiene permiso de `DELETE`).

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

## 3. Capa de base de datos

| Aspecto | Estado |
|---|---|
| **Usuario de conexión de la app** | `app_asistente` — permisos mínimos (migración 040) |
| **Row Level Security (RLS)** | ❌ No activado — **y hoy no serviría de nada** (ver abajo) |
| **`SUPABASE_ANON_KEY`** | Solo para Supabase Auth (registro/login). **No** puede leer datos: el esquema `normas` **no está expuesto** por la API REST (solo lo están `public` y `graphql_public`) |
| **Roles de Postgres** | `app_asistente` (la app) + los de Supabase. **Ninguno modela** admin/editor/alumno: eso es lógica de aplicación |

### Qué puede y qué no puede el usuario de la app (`app_asistente`)

| Puede | No puede |
|---|---|
| `SELECT` en todo el esquema `normas` | ❌ `DELETE` (en ninguna tabla) |
| `INSERT`/`UPDATE` solo en las 7 tablas que la app escribe | ❌ `TRUNCATE` |
| | ❌ `CREATE`/`ALTER`/`DROP` (DDL) |
| | ❌ Ser superusuario o saltarse el RLS |

Se comprobó que la app **no hace ningún `DELETE` ni ningún DDL** (rechazar una pregunta es un
borrado lógico desde la migración 039), así que esos permisos simplemente no se conceden. Un
bug o una inyección SQL no pueden destruir el esquema.

**Las migraciones no usan este rol**: se siguen aplicando como `postgres` desde el SQL Editor
de Supabase.

### Por qué NO se ha activado RLS (decisión consciente, no un olvido)

Sería **seguridad decorativa**:

1. El esquema `normas` **no está expuesto** por la API REST de Supabase, así que la clave
   `anon` no puede alcanzar los datos ni intentándolo (`PGRST106: Only the following schemas
   are exposed: public, graphql_public`).
2. El único cliente es Streamlit, y las políticas RLS tendrían que permitirle **todo lo que
   la app hace** — con lo cual no protegerían de nada.

**Cuándo será imprescindible:** el día que exista un frontend propio (línea B2C) que hable
**directamente** con Supabase usando la clave `anon` o `authenticated`. Entonces sí hay que
exponer el esquema *y* proteger cada tabla con RLS **antes** de abrirlo. `app_asistente` ya
está creado con `NOBYPASSRLS`, así que las políticas le aplicarán desde el primer día.

### Lo que sigue sin garantizar la base de datos

El aislamiento de los datos de un alumno lo garantiza **el código**, que le pasa su propio
email — no una política de base de datos. Un error de programación podría exponer datos de
otro alumno.

---

## 4. "Academia": no es un perfil

No existe ningún rol de academia. Lo que hay son dos columnas sueltas:

| Dónde | Qué es | Estado |
|---|---|---|
| `normas.editores.academia` | Columna reservada para el futuro modelo B2B (multi-academia) | **Vacía**, sin usar |
| `normas.simulacros_academia.academia` | Un texto con el nombre de la academia del simulacro | Descriptivo, no da permisos |

**Quién ejerce hoy las funciones de "academia":** un **editor** puede *generar* un simulacro,
pero solo un **administrador** puede *autorizarlo* (desde el 12/07/2026). Autorizar uno lo abre
a **todos** los alumnos de la oposición, sin distinguir a qué academia pertenecen — porque esa
relación alumno↔academia **no existe** en el esquema.

---

## 5. Puntos de atención (hechos, no propuestas)

Corregidos el 12/07/2026 (migraciones 039 y 040):
- ~~Cualquier editor podía borrar preguntas de forma irreversible~~ → ahora "Rechazar" es un
  **borrado lógico con justificación obligatoria**, y solo un admin puede restaurarlas.
- ~~Cualquier editor podía autorizar simulacros~~ → **solo administradores**.
- ~~La app conectaba como `postgres`~~ → ahora usa `app_asistente`, **sin permisos de borrado
  ni de DDL**.

Siguen abiertos:
1. **No hay relación alumno↔academia**, así que no se puede acotar un simulacro a los alumnos
   de una academia concreta. Un simulacro autorizado se abre a **todos** los alumnos.
2. **El registro de alumnos es abierto**: cualquiera con la URL puede crearse una cuenta
   (es intencionado).
3. **El aislamiento de los datos de un alumno depende del código**, no de la base de datos (§3).
4. **No hay auditoría de quién genera preguntas** (sí de quién aprueba y de quién descarta).

---

## Cómo comprobar esto tú mismo

```sql
-- Roles reales y quién los tiene
SELECT email, nombre, rol, activo FROM normas.editores ORDER BY rol, email;

-- Permisos reales del usuario de la app (deben ser todos 'false')
SELECT rolname, rolsuper AS superusuario, rolbypassrls AS salta_rls,
       has_schema_privilege('app_asistente','normas','CREATE') AS puede_ddl
FROM pg_roles WHERE rolname = 'app_asistente';

-- ¿Puede borrar algo?  (debe devolver 0 filas)
SELECT table_name, privilege_type FROM information_schema.table_privileges
WHERE grantee = 'app_asistente' AND privilege_type IN ('DELETE','TRUNCATE');
```
