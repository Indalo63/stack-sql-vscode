-- ============================================================
-- SCHEMA v2: Repositorio Jurídico para Oposiciones
-- Schemas: normas | programa | alumnos | examenes
-- PostgreSQL 16 + pgvector
-- ============================================================

CREATE EXTENSION IF NOT EXISTS vector;

-- ============================================================
-- SCHEMA normas — Contenido jurídico y documental
-- ============================================================
CREATE SCHEMA IF NOT EXISTS normas;

-- Leyes y normas con rango legal
CREATE TABLE normas.leyes (
    ley_id          serial       PRIMARY KEY,
    codigo          text         NOT NULL UNIQUE,  -- 'CE', 'LPAC', 'TREBEP', 'LCSP'
    nombre          text         NOT NULL,
    nombre_corto    text,                          -- 'Ley 39/2015' (para UI)
    tipo            text         NOT NULL
                    CHECK (tipo IN (
                        'constitucion',
                        'ley_organica',
                        'ley_ordinaria',
                        'real_decreto_legislativo',
                        'real_decreto',
                        'orden_ministerial'
                    )),
    numero_oficial  text,                          -- 'Ley 39/2015', 'RDL 5/2015'
    fecha_pub       date         NOT NULL,
    url_boe         text,
    url_eli         text,
    token_count     int,                           -- estimado: decide estrategia RAG (full-text vs jerárquico)
    activa          boolean      NOT NULL DEFAULT true,
    created_at      timestamptz  NOT NULL DEFAULT now(),
    updated_at      timestamptz  NOT NULL DEFAULT now()
);

-- Versiones de las leyes (control de cambios vía BOE API)
CREATE TABLE normas.versiones_ley (
    version_id          serial       PRIMARY KEY,
    ley_id              int          NOT NULL REFERENCES normas.leyes ON DELETE CASCADE,
    fecha_version       date         NOT NULL,
    descripcion_cambio  text,
    url_boe_mod         text,
    activa              boolean      NOT NULL DEFAULT false,  -- solo una activa por ley
    created_at          timestamptz  NOT NULL DEFAULT now(),
    UNIQUE (ley_id, fecha_version)
);

-- Documentos no normativos (políticas públicas, planes, jurisprudencia UE/nacional)
CREATE TABLE normas.documentos (
    documento_id    serial       PRIMARY KEY,
    codigo          text         NOT NULL UNIQUE,  -- 'ESPANA_DIGITAL_2026', 'VAN_GEND_LOOS'
    titulo          text         NOT NULL,
    tipo            text         NOT NULL
                    CHECK (tipo IN (
                        'plan',
                        'estrategia',
                        'jurisprudencia_nacional',
                        'jurisprudencia_ue',
                        'circular',
                        'instruccion',
                        'otro'
                    )),
    organismo       text,                          -- 'Comisión Europea', 'Tribunal Supremo'
    fecha_pub       date,
    url_fuente      text,
    resumen         text,
    activo          boolean      NOT NULL DEFAULT true,
    created_at      timestamptz  NOT NULL DEFAULT now()
);

-- Jerarquía legal: Títulos (nivel 1)
CREATE TABLE normas.titulos (
    titulo_id       serial       PRIMARY KEY,
    ley_id          int          NOT NULL REFERENCES normas.leyes ON DELETE CASCADE,
    numero          text         NOT NULL,   -- 'PRELIMINAR', 'I', 'II' ... 'X'
    denominacion    text         NOT NULL,
    orden           int          NOT NULL,
    embedding       vector(1536),            -- para RAG jerárquico (nivel título)
    UNIQUE (ley_id, numero)
);

-- Capítulos (nivel 2)
CREATE TABLE normas.capitulos (
    capitulo_id     serial  PRIMARY KEY,
    titulo_id       int     NOT NULL REFERENCES normas.titulos ON DELETE CASCADE,
    numero          text    NOT NULL,
    denominacion    text    NOT NULL,
    orden           int     NOT NULL,
    UNIQUE (titulo_id, numero)
);

-- Secciones (nivel 3 — solo en algunas leyes)
CREATE TABLE normas.secciones (
    seccion_id      serial  PRIMARY KEY,
    capitulo_id     int     NOT NULL REFERENCES normas.capitulos ON DELETE CASCADE,
    numero          text    NOT NULL,
    denominacion    text    NOT NULL,
    orden           int     NOT NULL,
    UNIQUE (capitulo_id, numero)
);

-- Artículos y disposiciones (unidad mínima de contenido legal)
CREATE TABLE normas.articulos (
    articulo_id     serial       PRIMARY KEY,
    ley_id          int          NOT NULL REFERENCES normas.leyes ON DELETE CASCADE,
    titulo_id       int          REFERENCES normas.titulos,
    capitulo_id     int          REFERENCES normas.capitulos,
    seccion_id      int          REFERENCES normas.secciones,
    numero          text         NOT NULL,   -- '1'...'169', 'DA-1', 'DT-1', 'DD', 'DF'
    tipo            text         NOT NULL DEFAULT 'articulo'
                    CHECK (tipo IN (
                        'preambulo',
                        'articulo',
                        'disposicion_adicional',
                        'disposicion_transitoria',
                        'disposicion_derogatoria',
                        'disposicion_final'
                    )),
    contenido       text         NOT NULL,
    orden_global    int          NOT NULL,
    embedding       vector(1536),
    texto_buscable  tsvector     GENERATED ALWAYS AS (
                        to_tsvector('spanish', contenido)
                    ) STORED,
    UNIQUE (ley_id, numero, tipo)
);

-- Fragmentos de documentos no normativos (chunking)
CREATE TABLE normas.fragmentos_documento (
    fragmento_id    serial       PRIMARY KEY,
    documento_id    int          NOT NULL REFERENCES normas.documentos ON DELETE CASCADE,
    numero          int          NOT NULL,   -- orden dentro del documento
    contenido       text         NOT NULL,
    embedding       vector(1536),
    texto_buscable  tsvector     GENERATED ALWAYS AS (
                        to_tsvector('spanish', contenido)
                    ) STORED,
    UNIQUE (documento_id, numero)
);

-- Índices de navegación
CREATE INDEX ON normas.leyes              (activa);
CREATE INDEX ON normas.titulos            (ley_id, orden);
CREATE INDEX ON normas.capitulos          (titulo_id, orden);
CREATE INDEX ON normas.secciones          (capitulo_id, orden);
CREATE INDEX ON normas.articulos          (ley_id, orden_global);
CREATE INDEX ON normas.articulos          (titulo_id);
CREATE INDEX ON normas.articulos          (tipo);
CREATE INDEX ON normas.fragmentos_documento (documento_id, numero);

-- Índices HNSW para búsqueda semántica (pgvector)
CREATE INDEX ON normas.articulos            USING hnsw (embedding vector_cosine_ops);
CREATE INDEX ON normas.titulos              USING hnsw (embedding vector_cosine_ops);
CREATE INDEX ON normas.fragmentos_documento USING hnsw (embedding vector_cosine_ops);

-- Índices GIN para búsqueda de texto completo
CREATE INDEX ON normas.articulos            USING gin (texto_buscable);
CREATE INDEX ON normas.fragmentos_documento USING gin (texto_buscable);


-- ============================================================
-- SCHEMA programa — Estructura de oposiciones y temarios
-- ============================================================
CREATE SCHEMA IF NOT EXISTS programa;

-- Oposiciones (programas de examen)
CREATE TABLE programa.oposiciones (
    oposicion_id    serial       PRIMARY KEY,
    codigo          text         NOT NULL UNIQUE,  -- 'GACE', 'TAI', 'CUERPO_JURIDICO'
    nombre          text         NOT NULL,
    organismo       text         NOT NULL,
    descripcion     text,
    activa          boolean      NOT NULL DEFAULT true,
    created_at      timestamptz  NOT NULL DEFAULT now()
);

-- Bloques del programa de cada oposición
CREATE TABLE programa.bloques (
    bloque_id       serial  PRIMARY KEY,
    oposicion_id    int     NOT NULL REFERENCES programa.oposiciones ON DELETE CASCADE,
    numero          int     NOT NULL,
    denominacion    text    NOT NULL,
    orden           int     NOT NULL,
    UNIQUE (oposicion_id, numero)
);

-- Temas dentro de cada bloque
CREATE TABLE programa.temas (
    tema_id         serial  PRIMARY KEY,
    bloque_id       int     NOT NULL REFERENCES programa.bloques ON DELETE CASCADE,
    numero          int     NOT NULL,   -- número global en la oposición (1..58 en GACE)
    titulo          text    NOT NULL,
    descripcion     text,               -- texto exacto del temario oficial
    orden           int     NOT NULL,
    UNIQUE (bloque_id, numero)
);

-- Normas que cubre cada tema (leyes o documentos, completas o parciales)
CREATE TABLE programa.tema_normas (
    id                  serial  PRIMARY KEY,
    tema_id             int     NOT NULL REFERENCES programa.temas ON DELETE CASCADE,
    ley_id              int     REFERENCES normas.leyes ON DELETE CASCADE,
    documento_id        int     REFERENCES normas.documentos ON DELETE CASCADE,
    articulos_incluidos text[], -- NULL = norma completa; ej: ARRAY['23','24','25'] = solo esos artículos
    CHECK (
        (ley_id IS NOT NULL AND documento_id IS NULL) OR
        (ley_id IS NULL     AND documento_id IS NOT NULL)
    )
);

-- Evita duplicados (índices parciales por la presencia de NULLs en UNIQUE)
CREATE UNIQUE INDEX ON programa.tema_normas (tema_id, ley_id)       WHERE ley_id IS NOT NULL;
CREATE UNIQUE INDEX ON programa.tema_normas (tema_id, documento_id)  WHERE documento_id IS NOT NULL;

-- Baremo del 1er ejercicio (test MCQ) por oposición
CREATE TABLE programa.baremos_test (
    baremo_id               serial        PRIMARY KEY,
    oposicion_id            int           NOT NULL REFERENCES programa.oposiciones ON DELETE CASCADE,
    n_preguntas             int           NOT NULL DEFAULT 100,
    tiempo_minutos          int           NOT NULL DEFAULT 90,
    puntuacion_max          numeric(5,2)  NOT NULL DEFAULT 50,
    puntuacion_minima       numeric(5,2)  NOT NULL DEFAULT 25,
    penalizacion_fraccion   numeric(6,4)  NOT NULL DEFAULT 0.3333,  -- fracción de la pregunta: 1/3
    vigente_desde           date          NOT NULL DEFAULT CURRENT_DATE,
    UNIQUE (oposicion_id, vigente_desde)
);

-- Baremo del 2do ejercicio (supuesto práctico) por oposición
CREATE TABLE programa.baremos_supuesto (
    baremo_id               serial        PRIMARY KEY,
    oposicion_id            int           NOT NULL REFERENCES programa.oposiciones ON DELETE CASCADE,
    n_preguntas             int           NOT NULL DEFAULT 5,
    tiempo_minutos          int           NOT NULL DEFAULT 150,
    puntuacion_max          numeric(5,2)  NOT NULL DEFAULT 50,
    -- Criterios GACE: a) aplicación 30 pts, b) análisis 10, c) sistemática 5, d) expresión 5
    puntos_aplicacion       numeric(5,2)  NOT NULL DEFAULT 30,
    puntos_analisis         numeric(5,2)  NOT NULL DEFAULT 10,
    puntos_sistematica      numeric(5,2)  NOT NULL DEFAULT 5,
    puntos_expresion        numeric(5,2)  NOT NULL DEFAULT 5,
    descripcion_criterios   jsonb,        -- rúbrica completa para el prompt de evaluación de Claude
    vigente_desde           date          NOT NULL DEFAULT CURRENT_DATE,
    UNIQUE (oposicion_id, vigente_desde)
);

-- Banco de supuestos prácticos (casos modelo + exámenes reales)
CREATE TABLE programa.supuestos_practicos (
    supuesto_id         serial       PRIMARY KEY,
    oposicion_id        int          NOT NULL REFERENCES programa.oposiciones ON DELETE CASCADE,
    bloque_id           int          REFERENCES programa.bloques,   -- bloque al que pertenece
    titulo              text         NOT NULL,
    enunciado           text         NOT NULL,
    anyo_convocatoria   int,
    es_oficial          boolean      NOT NULL DEFAULT false,         -- true si es de examen real
    activo              boolean      NOT NULL DEFAULT true,
    created_at          timestamptz  NOT NULL DEFAULT now()
);

-- Preguntas individuales de un supuesto práctico (habitualmente 5)
CREATE TABLE programa.preguntas_supuesto (
    pregunta_supuesto_id    serial  PRIMARY KEY,
    supuesto_id             int     NOT NULL REFERENCES programa.supuestos_practicos ON DELETE CASCADE,
    numero                  int     NOT NULL,   -- 1 a 5
    enunciado               text    NOT NULL,
    respuesta_modelo        text,               -- referencia para calibrar la evaluación de Claude
    orden                   int     NOT NULL,
    UNIQUE (supuesto_id, numero)
);

CREATE INDEX ON programa.bloques          (oposicion_id, orden);
CREATE INDEX ON programa.temas            (bloque_id, orden);
CREATE INDEX ON programa.tema_normas      (ley_id);
CREATE INDEX ON programa.tema_normas      (documento_id);
CREATE INDEX ON programa.supuestos_practicos (oposicion_id, bloque_id);


-- ============================================================
-- SCHEMA alumnos — Gestión de usuarios y suscripciones
-- ============================================================
CREATE SCHEMA IF NOT EXISTS alumnos;

-- Perfiles de alumno (provistos por el LMS vía autenticación)
CREATE TABLE alumnos.alumnos (
    alumno_id       serial       PRIMARY KEY,
    lms_user_id     text         UNIQUE,         -- ID en Moodle u otro LMS
    email           text         NOT NULL UNIQUE,
    nombre          text         NOT NULL,
    apellidos       text,
    activo          boolean      NOT NULL DEFAULT true,
    created_at      timestamptz  NOT NULL DEFAULT now(),
    last_login      timestamptz
);

-- Suscripciones: acceso a leyes sueltas o packs de oposición
CREATE TABLE alumnos.suscripciones (
    suscripcion_id  serial       PRIMARY KEY,
    alumno_id       int          NOT NULL REFERENCES alumnos.alumnos ON DELETE CASCADE,
    tipo            text         NOT NULL CHECK (tipo IN ('ley_suelta', 'oposicion')),
    ley_id          int          REFERENCES normas.leyes,
    oposicion_id    int          REFERENCES programa.oposiciones,
    fecha_inicio    date         NOT NULL DEFAULT CURRENT_DATE,
    fecha_fin       date,        -- NULL = sin expiración
    activa          boolean      NOT NULL DEFAULT true,
    CHECK (
        (tipo = 'ley_suelta' AND ley_id IS NOT NULL      AND oposicion_id IS NULL) OR
        (tipo = 'oposicion'  AND oposicion_id IS NOT NULL AND ley_id IS NULL)
    )
);

CREATE INDEX ON alumnos.suscripciones (alumno_id, activa);
CREATE INDEX ON alumnos.suscripciones (ley_id);
CREATE INDEX ON alumnos.suscripciones (oposicion_id);


-- ============================================================
-- SCHEMA examenes — Motor de tests y supuestos prácticos
-- ============================================================
CREATE SCHEMA IF NOT EXISTS examenes;

-- Banco de preguntas MCQ generadas por Claude (reutilizables entre sesiones)
CREATE TABLE examenes.banco_preguntas (
    banco_id            serial       PRIMARY KEY,
    articulo_id         int          REFERENCES normas.articulos,
    fragmento_id        int          REFERENCES normas.fragmentos_documento,
    ley_id              int          REFERENCES normas.leyes,
    bloque_id           int          REFERENCES programa.bloques,
    tema_id             int          REFERENCES programa.temas,
    enunciado           text         NOT NULL,
    opcion_a            text         NOT NULL,
    opcion_b            text         NOT NULL,
    opcion_c            text         NOT NULL,
    opcion_d            text         NOT NULL,
    respuesta_correcta  char(1)      NOT NULL CHECK (respuesta_correcta IN ('A','B','C','D')),
    explicacion         text,
    dificultad          text         CHECK (dificultad IN ('basica', 'media', 'avanzada')),
    veces_usada         int          NOT NULL DEFAULT 0,
    tasa_acierto        numeric(4,3),  -- se recalcula al cerrar cada sesión
    validada            boolean      NOT NULL DEFAULT false,
    created_at          timestamptz  NOT NULL DEFAULT now(),
    CHECK (articulo_id IS NOT NULL OR fragmento_id IS NOT NULL)
);

-- Sesiones de examen (práctica libre, simulacro completo, supuesto práctico)
CREATE TABLE examenes.sesiones (
    sesion_id           serial       PRIMARY KEY,
    alumno_id           int          NOT NULL REFERENCES alumnos.alumnos ON DELETE CASCADE,
    tipo                text         NOT NULL
                        CHECK (tipo IN ('practica', 'simulacro', 'supuesto')),
    oposicion_id        int          REFERENCES programa.oposiciones,
    filtro_ley_ids      int[],       -- leyes incluidas (NULL = sin filtro)
    filtro_bloque_ids   int[],       -- bloques incluidos
    filtro_tema_ids     int[],       -- temas incluidos
    n_preguntas         int,
    tiempo_limite_min   int,
    started_at          timestamptz  NOT NULL DEFAULT now(),
    ended_at            timestamptz,
    -- resultados calculados al finalizar la sesión
    n_correctas         int,
    n_incorrectas       int,
    n_en_blanco         int,
    puntuacion_bruta    numeric(6,3),
    puntuacion_final    numeric(6,3),
    aprobado            boolean
);

-- Preguntas incluidas en cada sesión + respuesta del alumno
CREATE TABLE examenes.preguntas_sesion (
    pregunta_sesion_id  serial       PRIMARY KEY,
    sesion_id           int          NOT NULL REFERENCES examenes.sesiones ON DELETE CASCADE,
    banco_id            int          NOT NULL REFERENCES examenes.banco_preguntas,
    numero_en_sesion    int          NOT NULL,   -- posición en el examen: 1..100
    respuesta_alumno    char(1)      CHECK (respuesta_alumno IN ('A','B','C','D')),
    respondida_at       timestamptz,
    es_correcta         boolean,     -- NULL mientras no se responde
    UNIQUE (sesion_id, numero_en_sesion)
);

-- Resoluciones de supuestos prácticos (2do ejercicio)
CREATE TABLE examenes.resoluciones_supuesto (
    resolucion_id           serial       PRIMARY KEY,
    sesion_id               int          NOT NULL REFERENCES examenes.sesiones ON DELETE CASCADE,
    supuesto_id             int          NOT NULL REFERENCES programa.supuestos_practicos,
    started_at              timestamptz  NOT NULL DEFAULT now(),
    ended_at                timestamptz,
    -- respuestas del alumno: [{pregunta_num: 1, respuesta: "...texto..."}, ...]
    respuestas              jsonb,
    -- evaluación de Claude aplicando el baremo oficial
    puntuacion_aplicacion   numeric(5,2),
    puntuacion_analisis     numeric(5,2),
    puntuacion_sistematica  numeric(5,2),
    puntuacion_expresion    numeric(5,2),
    puntuacion_total        numeric(5,2),
    feedback_ia             text,
    evaluado_at             timestamptz
);

CREATE INDEX ON examenes.sesiones           (alumno_id, tipo, started_at DESC);
CREATE INDEX ON examenes.sesiones           (oposicion_id);
CREATE INDEX ON examenes.preguntas_sesion   (sesion_id);
CREATE INDEX ON examenes.preguntas_sesion   (banco_id);
CREATE INDEX ON examenes.banco_preguntas    (ley_id);
CREATE INDEX ON examenes.banco_preguntas    (bloque_id);
CREATE INDEX ON examenes.banco_preguntas    (tema_id);
CREATE INDEX ON examenes.banco_preguntas    (validada);
CREATE INDEX ON examenes.resoluciones_supuesto (sesion_id);
