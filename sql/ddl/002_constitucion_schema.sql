-- Esquema legislativo para la Constitución Española (1978)
-- Fuente: https://www.boe.es/eli/es/c/1978/12/27/(1)/con

CREATE SCHEMA IF NOT EXISTS legislacion;

-- Leyes fuente
CREATE TABLE legislacion.leyes (
    ley_id      serial  PRIMARY KEY,
    codigo      text    NOT NULL UNIQUE,
    nombre      text    NOT NULL,
    fecha_pub   date    NOT NULL,
    url_eli     text,
    activa      boolean NOT NULL DEFAULT true
);

-- Títulos (nivel 1 de la jerarquía)
CREATE TABLE legislacion.titulos (
    titulo_id    serial PRIMARY KEY,
    ley_id       int    NOT NULL REFERENCES legislacion.leyes ON DELETE CASCADE,
    numero       text   NOT NULL,  -- 'PRELIMINAR', 'I', 'II' ... 'X'
    denominacion text   NOT NULL,
    orden        int    NOT NULL
);

-- Capítulos (nivel 2 — no todos los títulos tienen capítulos)
CREATE TABLE legislacion.capitulos (
    capitulo_id  serial PRIMARY KEY,
    titulo_id    int    NOT NULL REFERENCES legislacion.titulos ON DELETE CASCADE,
    numero       text   NOT NULL,  -- 'PRIMERO', 'SEGUNDO' ...
    denominacion text   NOT NULL,
    orden        int    NOT NULL
);

-- Secciones (nivel 3 — solo en algunos capítulos del Título I)
CREATE TABLE legislacion.secciones (
    seccion_id   serial PRIMARY KEY,
    capitulo_id  int    NOT NULL REFERENCES legislacion.capitulos ON DELETE CASCADE,
    numero       text   NOT NULL,  -- '1.ª', '2.ª'
    denominacion text   NOT NULL,
    orden        int    NOT NULL
);

-- Artículos y disposiciones (unidad mínima de contenido)
CREATE TABLE legislacion.articulos (
    articulo_id  serial PRIMARY KEY,
    ley_id       int    NOT NULL REFERENCES legislacion.leyes ON DELETE CASCADE,
    titulo_id    int    REFERENCES legislacion.titulos,
    capitulo_id  int    REFERENCES legislacion.capitulos,
    seccion_id   int    REFERENCES legislacion.secciones,
    numero       text   NOT NULL,  -- '1' ... '169', 'DA-1', 'DT-1', 'DD', 'DF'
    tipo         text   NOT NULL DEFAULT 'articulo'
                        CHECK (tipo IN (
                            'preambulo',
                            'articulo',
                            'disposicion_adicional',
                            'disposicion_transitoria',
                            'disposicion_derogatoria',
                            'disposicion_final'
                        )),
    contenido    text   NOT NULL,
    orden_global int    NOT NULL,
    embedding    vector(768)
);

-- Índices de navegación
CREATE INDEX ON legislacion.titulos (ley_id, orden);
CREATE INDEX ON legislacion.capitulos (titulo_id, orden);
CREATE INDEX ON legislacion.secciones (capitulo_id, orden);
CREATE INDEX ON legislacion.articulos (ley_id, orden_global);
CREATE INDEX ON legislacion.articulos (titulo_id);
CREATE INDEX ON legislacion.articulos (tipo);

-- Índice HNSW para búsqueda semántica por similitud (pgvector)
CREATE INDEX ON legislacion.articulos
    USING hnsw (embedding vector_cosine_ops);
