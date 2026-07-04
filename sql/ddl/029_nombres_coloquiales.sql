-- ============================================================
-- Migración 029: Etiquetas de visualización en nombre_corto
-- Formato: "Ref oficial — Nombre coloquial"
-- Ejecutar en Supabase: SQL Editor → New query → Run
-- ============================================================

UPDATE normas.leyes AS l
SET nombre_corto = v.etiqueta
FROM (VALUES
    -- Bloque I — Organización del Estado
    ('CE',       'Constitución Española 1978'),
    ('GACE_NORM','Normativa Convocatoria GACE'),
    ('LODP',     'LO 3/1981 — Defensor del Pueblo'),
    ('LOTC',     'LO 2/1979 — Tribunal Constitucional'),
    ('LGOB',     'Ley 50/1997 — Ley del Gobierno'),
    ('LOCE',     'LO 3/1980 — Consejo de Estado'),
    ('LBRL',     'Ley 7/1985 — Régimen Local'),
    ('LOPJ',     'LO 6/1985 — Poder Judicial'),
    ('ROCE',     'RD 1674/1980 — Reglamento del Consejo de Estado'),
    -- Bloque II — Unión Europea
    ('TUE',      'TUE — Tratado de la Unión Europea'),
    ('TFUE',     'TFUE — Tratado de Funcionamiento de la UE'),
    -- Bloque III — Políticas Públicas
    ('LTBG',     'Ley 19/2013 — Transparencia y Buen Gobierno'),
    ('LOPD',     'LO 3/2018 — Protección de Datos'),
    ('LGSS',     'RDL 8/2015 — Seguridad Social'),
    ('LOIEMH',   'LO 3/2007 — Igualdad entre Mujeres y Hombres'),
    ('LOIVG',    'LO 1/2004 — Violencia de Género'),
    ('LOIT',     'Ley 15/2022 — Igualdad de Trato'),
    ('LASEE',    'Ley 2/2014 — Acción Exterior del Estado'),
    ('ENI',      'RD 4/2010 — Interoperabilidad Digital'),
    ('LPNAT',    'Ley 42/2007 — Patrimonio Natural y Biodiversidad'),
    ('LE',       'Ley 3/2023 — Empleo'),
    ('LGPD',     'RDL 1/2013 — Personas con Discapacidad'),
    ('LDEP',     'Ley 39/2022 — Deporte'),
    ('LOE',      'LO 2/2006 — Educación'),
    ('LO4000',   'LO 4/2000 — Extranjería e Inmigración'),
    ('LASIL',    'LO 12/2009 — Asilo y Refugio'),
    ('LTRANS',   'Ley 16/1987 — Transportes Terrestres'),
    ('LGUM',     'Ley 20/2013 — Unidad de Mercado'),
    ('LGT22',    'Ley 11/2022 — Telecomunicaciones'),
    ('LEPP',     'Ley 27/2022 — Evaluación de Políticas Públicas'),
    -- Bloque IV — Derecho Administrativo
    ('LPAC',     'Ley 39/2015 — Procedimiento Administrativo'),
    ('LRJSP',    'Ley 40/2015 — Régimen Jurídico del Sector Público'),
    ('LCSP',     'Ley 9/2017 — Contratos del Sector Público'),
    ('LJCA',     'Ley 29/1998 — Justicia Contencioso-Administrativa'),
    ('LGS',      'Ley 38/2003 — Subvenciones'),
    ('LEF',      'Ley 1954 — Expropiación Forzosa'),
    ('LPAP',     'Ley 33/2003 — Patrimonio de las Administraciones'),
    ('CC',       'CC 1889 — Código Civil'),
    ('RLEF',     'D 1957 — Reglamento de Expropiación Forzosa'),
    ('RLGS',     'RD 887/2006 — Reglamento de Subvenciones'),
    -- Bloque V — Recursos Humanos
    ('TREBEP',   'RDL 5/2015 — Estatuto del Empleado Público'),
    ('RIRS',     'Ley 53/1984 — Incompatibilidades de Funcionarios'),
    ('MUFACE',   'RDL 4/2000 — Mutualidad de Funcionarios'),
    ('LMRFP',   'Ley 30/1984 — Reforma de la Función Pública'),
    ('RDSA',     'RD 365/1995 — Situaciones Administrativas'),
    ('RDRD',     'RD 33/1986 — Régimen Disciplinario'),
    ('REGI',     'RD 2668/1998 — Registro Central de Personal'),
    ('ET',       'RDL 2/2015 — Estatuto de los Trabajadores'),
    ('BCPSA',    'RDL 670/1987 — Clases Pasivas del Estado'),
    ('RRCP',     'RD 172/1988 — Reglamento de Clases Pasivas'),
    ('LAEPD',    'RD 428/1993 — Agencia de Protección de Datos'),
    ('LSSF',     'RDLeg 3/2000 — Seguridad Social Justicia'),
    -- Bloque VI — Gestión Financiera
    ('LGP',      'Ley 47/2003 — Presupuestos Generales del Estado'),
    ('LOEPSF',   'LO 2/2012 — Estabilidad Presupuestaria'),
    ('LTPP',     'Ley 8/1989 — Tasas y Precios Públicos'),
    ('LGT',      'Ley 58/2003 — Ley General Tributaria'),
    ('LOTCU',    'LO 2/1982 — Tribunal de Cuentas'),
    ('IGAE',     'RD 2188/1995 — Intervención General del Estado'),
    ('ACF',      'RD 725/1989 — Anticipos de Caja Fija'),
    ('PLJ',      'RD 640/1987 — Pagos a Justificar')
) AS v(codigo, etiqueta)
WHERE l.codigo = v.codigo;

-- Verificación: filas actualizadas deben ser 60
SELECT COUNT(*) AS leyes_actualizadas
FROM normas.leyes
WHERE codigo IN (
    'CE','GACE_NORM','LODP','LOTC','LGOB','LOCE','LBRL','LOPJ','ROCE',
    'TUE','TFUE',
    'LTBG','LOPD','LGSS','LOIEMH','LOIVG','LOIT','LASEE','ENI','LPNAT',
    'LE','LGPD','LDEP','LOE','LO4000','LASIL','LTRANS','LGUM','LGT22','LEPP',
    'LPAC','LRJSP','LCSP','LJCA','LGS','LEF','LPAP','CC','RLEF','RLGS',
    'TREBEP','RIRS','MUFACE','LMRFP','RDSA','RDRD','REGI','ET',
    'BCPSA','RRCP','LAEPD','LSSF',
    'LGP','LOEPSF','LTPP','LGT','LOTCU','IGAE','ACF','PLJ'
);
