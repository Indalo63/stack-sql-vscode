# Flujo completo del alumno

Diagrama de recorrido del alumno desde que entra en la app hasta cada uno de los
4 modos ya implementados (Pasos 1-8) más el **Simulacro de academia** diseñado
para el Paso 9 (pendiente de construir — nodos con borde discontinuo).

Fuente: `app/streamlit_app.py` (`_flujo_alumno` y funciones `_modo_*`),
`app/retrieval.py`, `TODO.md` (decisiones de diseño del hito "App de estudio
del alumno").

```mermaid
flowchart TD
    A["Alumno abre la app"] --> B["Selecciona Oposición<br/>(sidebar)"]
    B --> C{"Acceso"}
    C -->|"Administración"| ADM["Google OAuth<br/>Editor / Q&amp;A / Generar test"]
    C -->|"Alumno"| D{"¿Tiene sesión activa?"}

    D -->|"No"| E["Login / Registro<br/>email + contraseña (Supabase Auth)"]
    E -->|"Registro nuevo"| F["Onboarding de bienvenida"]
    E -->|"Login"| G
    D -->|"Sí"| G{"¿plan_estudio vacío?<br/>(alumno nuevo)"}
    F --> G

    G -->|"Sí, nuevo"| H["Preselecciona modo:<br/>Prueba de nivel"]
    G -->|"No, ya tiene progreso"| I["Preselecciona modo:<br/>Repaso (bloque más débil)"]
    H --> MENU
    I --> MENU

    MENU{"Menú del alumno"} --> M1["Prueba de nivel"]
    MENU --> M2["Repaso adaptativo"]
    MENU --> M3["Simulacro personal"]
    MENU --> M4["Mi progreso"]
    MENU -.->|"Paso 9 · pendiente"| M5["Simulacro de academia"]

    subgraph SG1["Prueba de nivel"]
        M1 --> N1["40 preguntas<br/>reparto por peso oficial x bloque<br/>dificultad creciente"]
        N1 --> N2["Comprobar respuestas"]
        N2 --> N3["Informe de partida por bloque<br/>+ fase inicial<br/>(UPSERT plan_estudio)"]
        N3 --> N4["Botón: Ir a Repaso →"]
    end

    subgraph SG2["Repaso adaptativo"]
        P1["Panel: estado actual por bloque<br/>(get_stats_alumno)"]
        P1 --> P2["Elegir bloque"]
        P2 --> P3["Tanda adaptativa<br/>mix débiles/oficial/nueva según fase<br/>(mensaje genérico, sin desglose visible)"]
        P3 --> P4["Comprobar respuestas"]
        P4 --> P5["SM-2: update_progreso_sm2<br/>+ recalcula fase y % del bloque"]
        P5 --> P6["Resultado: aciertos/fallos<br/>+ nuevo % del bloque"]
        P6 -->|"Nueva tanda"| P2
    end
    M2 --> P1
    N4 --> M2

    subgraph SG3["Simulacro personal"]
        Q0{"¿Prueba de nivel hecha<br/>y algún bloque ≥70%?"}
        Q0 -->|"No"| Q0X["Bloqueado<br/>(motivo explicado)"]
        Q0 -->|"Sí"| Q1["50 preguntas<br/>reparto proporcional<br/>solo bloques 'estudiado'"]
        Q1 --> Q2["Comprobar respuestas"]
        Q2 --> Q3["calificar_simulacro<br/>fórmula oficial A-(E/3)<br/>escala 0-50, NO toca<br/>progreso_usuario/plan_estudio"]
        Q3 --> Q4["Guardar en historial_simulacros<br/>tipo = personal"]
        Q4 --> Q5["Resultado: nota + aprobado/no"]
        Q5 -->|"Nuevo simulacro"| Q1
    end
    M3 --> Q0

    subgraph SG4["Mi progreso"]
        R1["get_historial_simulacros"]
        R1 --> R2["Lista de intentos<br/>fecha · tipo · nota · aprobado/no<br/>(personal + academia)"]
    end
    M4 --> R1
    Q4 -.-> R2

    subgraph SG5["Simulacro de academia — Paso 9 (diseño)"]
        S0{"¿Simulacro autorizado<br/>y dentro de ventana<br/>fecha_inicio/fecha_fin?"}
        S0 -->|"No"| S0X["Bloqueado / no disponible"]
        S0 -->|"Sí"| S1["Preguntas fijas<br/>(simulacro_academia_preguntas)<br/>mismas para todos, sin personalización"]
        S1 --> S2["Comprobar respuestas"]
        S2 --> S3["calificar_simulacro<br/>misma fórmula oficial"]
        S3 --> S4["Guardar en historial_simulacros<br/>tipo = academia<br/>+ simulacro_academia_id"]
    end
    M5 -.-> S0
    S4 -.-> R2

    classDef pendiente stroke-dasharray: 5 5,stroke:#999,color:#999;
    class M5,S0,S0X,S1,S2,S3,S4 pendiente;
```

## Notas de diseño relevantes al flujo

- **Sin acceso anónimo**: hasta elegir "Administración" o "Alumno" en el
  sidebar no se muestra contenido.
- **Simulacro personal vs. repaso**: el simulacro es una prueba aislada — su
  resultado nunca actualiza `progreso_usuario` (SM-2) ni `plan_estudio`, solo
  queda registrado en `historial_simulacros` (decisión explícita del usuario,
  Paso 8).
- **Regla de producto (Paso 7)**: el alumno nunca ve el desglose
  débiles/oficial/nueva ni la fase (inicio/aprendizaje/consolidación/pre-examen)
  de una tanda — ese dato es para el futuro análisis B2B de la academia, no
  para el alumno.
- **Simulacro de academia (Paso 9, sin construir)**: mismas preguntas para
  todos los alumnos de una ventana temporal, sin personalización; la academia
  nunca genera preguntas, solo autoriza el lote ya generado
  (`normas.simulacros_academia.estado`: generado → autorizado). Diseñado para
  escribir en la misma tabla `historial_simulacros` que el simulacro personal
  (columna `simulacro_academia_id`), de forma que "Mi progreso" ya sabe listar
  ambos tipos sin cambios futuros.
</content>
