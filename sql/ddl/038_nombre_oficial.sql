-- ============================================================
-- Migración 038: normas.leyes.nombre_oficial (título oficial del BOE)
--
-- Motivo: el campo `nombre` no era homogéneo — 25 de las 60 leyes lo tenían SIN
-- la referencia oficial (LPAC era "Ley del Procedimiento Administrativo Común",
-- sin el "Ley 39/2015, de 1 de octubre"). Como el generador pasa ese campo al
-- prompt, Claude a veces completaba la referencia de memoria y a veces no: 18 de
-- las 70 preguntas pendientes incumplían la norma obligatoria nº2 ("el enunciado
-- cita la norma completa").
--
-- Modelo de nombres a partir de ahora:
--   nombre_oficial : título exacto del BOE. Lo usa TODO lo que cita la norma
--                    (generador de preguntas, Q&A) y las actualizaciones de
--                    legislación. Fuente única de verdad.
--   nombre         : nombre de trabajo (se deja como está, no se usa para citar).
--   nombre_corto   : etiqueta del sidebar ("Ley 39/2015 — Procedimiento Administrativo").
--
-- Los títulos NO están escritos de memoria: se descargaron del propio BOE
-- (cabecera `documento-tit` de cada url_boe) el 12/07/2026.
--
-- Ejecutar en Supabase: SQL Editor → New query → Run
-- ============================================================

ALTER TABLE normas.leyes
    ADD COLUMN IF NOT EXISTS nombre_oficial VARCHAR(500);

COMMENT ON COLUMN normas.leyes.nombre_oficial IS
    'Título oficial completo tal y como aparece en el BOE. Es el que deben usar los prompts que citan la norma (norma obligatoria nº2: el enunciado cita la norma completa). No confundir con nombre (de trabajo) ni nombre_corto (etiqueta de UI).';

-- ── Títulos descargados del BOE (56 leyes) ────────────────────────────────────
UPDATE normas.leyes SET nombre_oficial = 'Real Decreto 725/1989, de 16 de junio, sobre anticipos de Caja fija' WHERE ley_id = 65;  -- ACF
UPDATE normas.leyes SET nombre_oficial = 'Orden HFP/688/2017, de 20 de julio, por la que se establecen las bases comunes que regirán los procesos selectivos para el ingreso o el acceso en cuerpos o escalas de la Administración General del Estado' WHERE ley_id = 62;  -- BCPSA  -- ⚠️ REVISAR (ver nota al final)
UPDATE normas.leyes SET nombre_oficial = 'Real Decreto de 24 de julio de 1889 por el que se publica el Código Civil' WHERE ley_id = 57;  -- CC
UPDATE normas.leyes SET nombre_oficial = 'Real Decreto 4/2010, de 8 de enero, por el que se regula el Esquema Nacional de Interoperabilidad en el ámbito de la Administración Electrónica' WHERE ley_id = 53;  -- ENI
UPDATE normas.leyes SET nombre_oficial = 'Real Decreto Legislativo 2/2015, de 23 de octubre, por el que se aprueba el texto refundido de la Ley del Estatuto de los Trabajadores' WHERE ley_id = 49;  -- ET
UPDATE normas.leyes SET nombre_oficial = 'Real Decreto 2188/1995, de 28 de diciembre, por el que se desarrolla el régimen del control interno ejercido por la Intervención General de la Administración del Estado' WHERE ley_id = 64;  -- IGAE
UPDATE normas.leyes SET nombre_oficial = 'Real Decreto 2271/2004, de 3 de diciembre, por el que se regula el acceso al empleo público y la provisión de puestos de trabajo de las personas con discapacidad' WHERE ley_id = 69;  -- LAEPD
UPDATE normas.leyes SET nombre_oficial = 'Ley 2/2014, de 25 de marzo, de la Acción y del Servicio Exterior del Estado' WHERE ley_id = 51;  -- LASEE
UPDATE normas.leyes SET nombre_oficial = 'Ley 12/2009, de 30 de octubre, reguladora del derecho de asilo y de la protección subsidiaria' WHERE ley_id = 74;  -- LASIL
UPDATE normas.leyes SET nombre_oficial = 'Ley 7/1985, de 2 de abril, Reguladora de las Bases del Régimen Local' WHERE ley_id = 20;  -- LBRL
UPDATE normas.leyes SET nombre_oficial = 'Ley 9/2017, de 8 de noviembre, de Contratos del Sector Público, por la que se transponen al ordenamiento jurídico español las Directivas del Parlamento Europeo y del Consejo 2014/23/UE y 2014/24/UE, de 26 de febrero de 2014' WHERE ley_id = 12;  -- LCSP
UPDATE normas.leyes SET nombre_oficial = 'Real Decreto Legislativo 3/2015, de 23 de octubre, por el que se aprueba el texto refundido de la Ley de Empleo' WHERE ley_id = 71;  -- LDEP
UPDATE normas.leyes SET nombre_oficial = 'Ley 3/2023, de 28 de febrero, de Empleo' WHERE ley_id = 59;  -- LE
UPDATE normas.leyes SET nombre_oficial = 'Ley de 16 de diciembre de 1954 sobre expropiación forzosa' WHERE ley_id = 39;  -- LEF
UPDATE normas.leyes SET nombre_oficial = 'Ley 27/2022, de 20 de diciembre, de institucionalización de la evaluación de políticas públicas en la Administración General del Estado' WHERE ley_id = 79;  -- LEPP
UPDATE normas.leyes SET nombre_oficial = 'Ley 50/1997, de 27 de noviembre, del Gobierno' WHERE ley_id = 18;  -- LGOB
UPDATE normas.leyes SET nombre_oficial = 'Ley 47/2003, de 26 de noviembre, General Presupuestaria' WHERE ley_id = 9;  -- LGP
UPDATE normas.leyes SET nombre_oficial = 'Real Decreto Legislativo 1/2013, de 29 de noviembre, por el que se aprueba el Texto Refundido de la Ley General de derechos de las personas con discapacidad y de su inclusión social' WHERE ley_id = 68;  -- LGPD
UPDATE normas.leyes SET nombre_oficial = 'Ley 38/2003, de 17 de noviembre, General de Subvenciones' WHERE ley_id = 38;  -- LGS
UPDATE normas.leyes SET nombre_oficial = 'Real Decreto Legislativo 8/2015, de 30 de octubre, por el que se aprueba el texto refundido de la Ley General de la Seguridad Social' WHERE ley_id = 27;  -- LGSS
UPDATE normas.leyes SET nombre_oficial = 'Ley 58/2003, de 17 de diciembre, General Tributaria' WHERE ley_id = 31;  -- LGT
UPDATE normas.leyes SET nombre_oficial = 'Ley 11/2022, de 28 de junio, General de Telecomunicaciones' WHERE ley_id = 78;  -- LGT22
UPDATE normas.leyes SET nombre_oficial = 'Ley 20/2013, de 9 de diciembre, de garantía de la unidad de mercado' WHERE ley_id = 77;  -- LGUM
UPDATE normas.leyes SET nombre_oficial = 'Ley 29/1998, de 13 de julio, reguladora de la Jurisdicción Contencioso-administrativa' WHERE ley_id = 37;  -- LJCA
UPDATE normas.leyes SET nombre_oficial = 'Ley 30/1984, de 2 de agosto, de medidas para la reforma de la Función Pública' WHERE ley_id = 44;  -- LMRFP
UPDATE normas.leyes SET nombre_oficial = 'Ley Orgánica 4/2000, de 11 de enero, sobre derechos y libertades de los extranjeros en España y su integración social' WHERE ley_id = 73;  -- LO4000
UPDATE normas.leyes SET nombre_oficial = 'Ley Orgánica 3/1980, de 22 de abril, del Consejo de Estado' WHERE ley_id = 19;  -- LOCE
UPDATE normas.leyes SET nombre_oficial = 'Ley Orgánica 3/1981, de 6 de abril, del Defensor del Pueblo' WHERE ley_id = 15;  -- LODP
UPDATE normas.leyes SET nombre_oficial = 'Ley Orgánica 2/2006, de 3 de mayo, de Educación' WHERE ley_id = 72;  -- LOE
UPDATE normas.leyes SET nombre_oficial = 'Ley Orgánica 2/2012, de 27 de abril, de Estabilidad Presupuestaria y Sostenibilidad Financiera' WHERE ley_id = 23;  -- LOEPSF
UPDATE normas.leyes SET nombre_oficial = 'Ley Orgánica 3/2007, de 22 de marzo, para la igualdad efectiva de mujeres y hombres' WHERE ley_id = 35;  -- LOIEMH
UPDATE normas.leyes SET nombre_oficial = 'Ley 15/2022, de 12 de julio, integral para la igualdad de trato y la no discriminación' WHERE ley_id = 50;  -- LOIT
UPDATE normas.leyes SET nombre_oficial = 'Ley Orgánica 1/2004, de 28 de diciembre, de Medidas de Protección Integral contra la Violencia de Género' WHERE ley_id = 36;  -- LOIVG
UPDATE normas.leyes SET nombre_oficial = 'Ley Orgánica 3/2018, de 5 de diciembre, de Protección de Datos Personales y garantía de los derechos digitales' WHERE ley_id = 22;  -- LOPD
UPDATE normas.leyes SET nombre_oficial = 'Ley Orgánica 6/1985, de 1 de julio, del Poder Judicial' WHERE ley_id = 26;  -- LOPJ
UPDATE normas.leyes SET nombre_oficial = 'Ley Orgánica 2/1979, de 3 de octubre, del Tribunal Constitucional' WHERE ley_id = 17;  -- LOTC
UPDATE normas.leyes SET nombre_oficial = 'Ley Orgánica 2/1982, de 12 de mayo, del Tribunal de Cuentas' WHERE ley_id = 48;  -- LOTCU
UPDATE normas.leyes SET nombre_oficial = 'Ley 39/2015, de 1 de octubre, del Procedimiento Administrativo Común de las Administraciones Públicas' WHERE ley_id = 4;  -- LPAC
UPDATE normas.leyes SET nombre_oficial = 'Ley 33/2003, de 3 de noviembre, del Patrimonio de las Administraciones Públicas' WHERE ley_id = 40;  -- LPAP
UPDATE normas.leyes SET nombre_oficial = 'Ley 42/2007, de 13 de diciembre, del Patrimonio Natural y de la Biodiversidad' WHERE ley_id = 58;  -- LPNAT
UPDATE normas.leyes SET nombre_oficial = 'Ley 40/2015, de 1 de octubre, de Régimen Jurídico del Sector Público' WHERE ley_id = 7;  -- LRJSP
UPDATE normas.leyes SET nombre_oficial = 'Real Decreto Legislativo 4/2000, de 23 de junio, por el que se aprueba el texto refundido de la Ley sobre Seguridad Social de los Funcionarios Civiles del Estado' WHERE ley_id = 70;  -- LSSF
UPDATE normas.leyes SET nombre_oficial = 'Ley 19/2013, de 9 de diciembre, de transparencia, acceso a la información pública y buen gobierno' WHERE ley_id = 21;  -- LTBG
UPDATE normas.leyes SET nombre_oficial = 'Ley 8/1989, de 13 de abril, de Tasas y Precios Públicos' WHERE ley_id = 29;  -- LTPP
UPDATE normas.leyes SET nombre_oficial = 'Ley 4/2023, de 28 de febrero, para la igualdad real y efectiva de las personas trans y para la garantía de los derechos de las personas LGTBI' WHERE ley_id = 75;  -- LTRANS
UPDATE normas.leyes SET nombre_oficial = 'Real Decreto 375/2003, de 28 de marzo, por el que se aprueba el Reglamento General del Mutualismo Administrativo' WHERE ley_id = 43;  -- MUFACE
UPDATE normas.leyes SET nombre_oficial = 'Real Decreto 640/1987, de 8 de mayo, sobre pagos librados «a justificar»' WHERE ley_id = 66;  -- PLJ
UPDATE normas.leyes SET nombre_oficial = 'Real Decreto 33/1986, de 10 de enero, por el que se aprueba el Reglamento de Régimen Disciplinario de los Funcionarios de la Administración del Estado' WHERE ley_id = 46;  -- RDRD
UPDATE normas.leyes SET nombre_oficial = 'Real Decreto 365/1995, de 10 de marzo, por el que se aprueba el Reglamento de Situaciones Administrativas de los Funcionarios Civiles de la Administración General del Estado' WHERE ley_id = 45;  -- RDSA
UPDATE normas.leyes SET nombre_oficial = 'Real Decreto 364/1995, de 10 de marzo, por el que se aprueba el Reglamento General de Ingreso del Personal al servicio de la Administración general del Estado y de Provisión de Puestos de Trabajo y Promoción Profesional de los Funcionarios Civiles de la Administración general del Estado' WHERE ley_id = 47;  -- REGI
UPDATE normas.leyes SET nombre_oficial = 'Real Decreto 462/2002, de 24 de mayo, sobre indemnizaciones por razón del servicio' WHERE ley_id = 42;  -- RIRS
UPDATE normas.leyes SET nombre_oficial = 'Decreto de 26 de abril de 1957 por el que se aprueba el Reglamento de la Ley de Expropiación Forzosa' WHERE ley_id = 60;  -- RLEF
UPDATE normas.leyes SET nombre_oficial = 'Real Decreto 887/2006, de 21 de julio, por el que se aprueba el Reglamento de la Ley 38/2003, de 17 de noviembre, General de Subvenciones' WHERE ley_id = 61;  -- RLGS
UPDATE normas.leyes SET nombre_oficial = 'Real Decreto 1674/1980, de 18 de julio, por el que se aprueba el Reglamento Orgánico del Consejo de Estado' WHERE ley_id = 67;  -- ROCE
UPDATE normas.leyes SET nombre_oficial = 'Real Decreto 2073/1999, de 30 de diciembre, por el que se modifica el Reglamento del Registro Central de Personal y las normas de coordinación con los de las restantes Administraciones públicas' WHERE ley_id = 63;  -- RRCP  -- ⚠️ REVISAR (ver nota al final)
UPDATE normas.leyes SET nombre_oficial = 'Real Decreto Legislativo 5/2015, de 30 de octubre, por el que se aprueba el texto refundido de la Ley del Estatuto Básico del Empleado Público' WHERE ley_id = 8;  -- TREBEP

-- ── Normas que no proceden del BOE: se conserva su nombre actual ──────────────
-- CE1978 (Constitución), TUE y TFUE (EUR-Lex) y GACE_NORM (documento de la
-- convocatoria, excluido del test) ya tenían un nombre completo y correcto.
UPDATE normas.leyes
   SET nombre_oficial = nombre
 WHERE nombre_oficial IS NULL;

-- ── Verificación ──
SELECT COUNT(*) FILTER (WHERE nombre_oficial IS NULL) AS sin_oficial,
       COUNT(*)                                       AS total
FROM normas.leyes WHERE activa;

-- ⚠️ DOS LEYES QUEDAN PENDIENTES DE REVISIÓN HUMANA (no bloquean nada):
--
-- RRCP: su url_boe apunta al RD 2073/1999 "por el que se MODIFICA el Reglamento
--       del Registro Central de Personal" — es un decreto modificador, no el
--       reglamento en sí. Revisar cuál es la norma que se quiere citar.
--
-- BCPSA: el BOE devuelve "Orden HFP/688/2017, de 20 de julio"; en cambio la
--        columna numero_oficial dice "Real Decreto 364/2017, de 8 de abril".
--        Se contradicen: hay que decidir cuál es la correcta.
