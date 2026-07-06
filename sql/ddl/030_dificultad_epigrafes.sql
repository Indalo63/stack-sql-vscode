-- ============================================================
-- Migración 030: campo dificultad en preguntas_test + tabla epigrafes
-- Ejecutar en Supabase: SQL Editor → New query → Run
-- ============================================================

-- ── 1. Dificultad de la pregunta (prueba de nivel + mix adaptativo) ──────────
ALTER TABLE normas.preguntas_test
    ADD COLUMN IF NOT EXISTS dificultad SMALLINT NOT NULL DEFAULT 2
        CHECK (dificultad IN (1, 2, 3));

COMMENT ON COLUMN normas.preguntas_test.dificultad IS
    '1 = fácil, 2 = media, 3 = difícil. Asignada por el editor en revisión; default 2 hasta reclasificar.';

CREATE INDEX IF NOT EXISTS idx_preguntas_dificultad
    ON normas.preguntas_test (dificultad);

-- ── 2. Epígrafes del temario oficial (Bloque + Tema) ─────────────────────────
CREATE TABLE IF NOT EXISTS normas.epigrafes (
    epigrafe_id   SERIAL      PRIMARY KEY,
    oposicion_id  INTEGER     NOT NULL REFERENCES normas.oposiciones(oposicion_id) ON DELETE CASCADE,
    bloque        VARCHAR(5)  NOT NULL,
    tema          INTEGER     NOT NULL,
    titulo        TEXT        NOT NULL,
    orden         INTEGER     NOT NULL,
    UNIQUE (oposicion_id, bloque, tema)
);

COMMENT ON TABLE normas.epigrafes IS
    'Temario oficial dividido en epígrafes (bloque.tema), según el programa de la convocatoria (58 temas GACE 2025).';

CREATE INDEX IF NOT EXISTS idx_epigrafes_oposicion_bloque
    ON normas.epigrafes (oposicion_id, bloque, orden);

-- ── 3. Vincular preguntas_test con su epígrafe (nullable: aún no mapeadas) ───
ALTER TABLE normas.preguntas_test
    ADD COLUMN IF NOT EXISTS epigrafe_id INTEGER
        REFERENCES normas.epigrafes(epigrafe_id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_preguntas_epigrafe
    ON normas.preguntas_test (epigrafe_id);

-- ── 4. Poblar los 58 epígrafes del temario oficial GACE 2025 ─────────────────
INSERT INTO normas.epigrafes (oposicion_id, bloque, tema, titulo, orden)
SELECT o.oposicion_id, v.bloque, v.tema, v.titulo, v.orden
FROM normas.oposiciones o
CROSS JOIN (VALUES
    ('I', 1, 'La Constitución Española de 1978: estructura y contenido. La reforma de la Constitución.', 1),
    ('I', 2, 'Derechos y deberes fundamentales. Su garantía y suspensión. El Defensor del Pueblo.', 2),
    ('I', 3, 'El Tribunal Constitucional. Organización, composición y atribuciones.', 3),
    ('I', 4, 'La Corona. Funciones constitucionales del Rey. Sucesión y regencia. El refrendo.', 4),
    ('I', 5, 'El poder legislativo. Las Cortes Generales. Composición y atribuciones del Congreso de los Diputados y del Senado.', 5),
    ('I', 6, 'El poder ejecutivo. El Presidente del Gobierno y el Consejo de Ministros. Relaciones entre el Gobierno y las Cortes Generales. Designación, causas de cese y responsabilidad del Gobierno. El Consejo de Estado.', 6),
    ('I', 7, 'El Poder Judicial. El principio de unidad jurisdiccional. El Consejo General del Poder Judicial. La organización judicial española.', 7),
    ('I', 8, 'La Administración General del Estado. Principios de organización y funcionamiento. Órganos centrales. Órganos superiores y órganos directivos: creación, nombramiento, cese y funciones. Los servicios comunes de los ministerios. Órganos territoriales. La Administración del Estado en el Exterior.', 8),
    ('I', 9, 'El sector público institucional: entidades que lo integran y régimen jurídico.', 9),
    ('I', 10, 'Organización territorial (I): las Comunidades Autónomas. Los Estatutos de Autonomía. Organización política y administrativa. La delimitación de competencias entre el Estado y las Comunidades Autónomas en la Constitución y en los Estatutos de Autonomía.', 10),
    ('I', 11, 'Organización territorial (II): la Administración local: entidades que la integran. La autonomía local. El municipio: organización y competencias. La provincia: organización y competencias.', 11),
    ('II', 1, 'La Unión Europea: Antecedentes. Objetivos y naturaleza jurídica. Los Tratados originarios y modificativos. El Tratado de la Unión Europea y el Tratado de Funcionamiento de la Unión Europea. El proceso de ampliación. Las cooperaciones reforzadas.', 12),
    ('II', 2, 'La organización de la Unión Europea (I): el Consejo Europeo, el Consejo y la Comisión Europea. Composición y funciones. El procedimiento decisorio. La participación de los Estados miembros en las diferentes fases del proceso.', 13),
    ('II', 3, 'La organización de la Unión Europea (II): el Parlamento Europeo. El Tribunal de Justicia de la Unión Europea. El Tribunal de Cuentas. El Banco Central Europeo.', 14),
    ('II', 4, 'Las fuentes del derecho de la Unión Europea. Derecho originario. Derecho derivado: Reglamentos, directivas y decisiones. Otras fuentes. Las relaciones entre el Derecho de la Unión Europea y el ordenamiento jurídico de los Estados miembros.', 15),
    ('II', 5, 'El presupuesto comunitario. Los fondos europeos. La cohesión económica y social.', 16),
    ('II', 6, 'Políticas de la Unión Europea: mercado interior. Política económica y monetaria. Política exterior y de seguridad común. El espacio de seguridad, libertad y justicia. Defensa de la competencia. Política agrícola y pesquera.', 17),
    ('III', 1, 'Políticas de modernización de la Administración General del Estado. La Administración electrónica. Acceso electrónico de los ciudadanos a los servicios públicos. La Agenda Digital para España. La calidad de los servicios públicos y de atención al ciudadano. Mejora Regulatoria y Análisis de Impacto Normativo.', 18),
    ('III', 2, 'Política económica actual. Política presupuestaria. Evolución y distribución actual del gasto público. Política fiscal. La unidad de mercado.', 19),
    ('III', 3, 'Política ambiental. Distribución de competencias. Conservación de la biodiversidad. Prevención de la contaminación y el cambio climático.', 20),
    ('III', 4, 'La Seguridad Social: estructura y financiación. Problemas actuales y líneas de actuación. El régimen general y los regímenes especiales. La acción protectora de la Seguridad Social. Tipos y características de las prestaciones.', 21),
    ('III', 5, 'La evolución del empleo en España. Los servicios públicos de empleo: régimen de prestaciones y políticas de empleo.', 22),
    ('III', 6, 'Política de inmigración. Régimen de los extranjeros en España. Derecho de asilo y condición de refugiado.', 23),
    ('III', 7, 'El Gobierno Abierto: concepto, principios informadores y planes de acción de España. La Ley 19/2013, de 9 de diciembre, de transparencia, acceso a la información pública y buen gobierno.', 24),
    ('III', 8, 'La protección de datos personales y su régimen jurídico: principios, derechos, responsable y encargado del tratamiento, delegado y autoridades de protección de datos. Derechos digitales.', 25),
    ('III', 9, 'Políticas de igualdad y contra la violencia de género: régimen jurídico. Políticas de igualdad de trato y no discriminación de las personas LGTBI. Discapacidad y dependencia: régimen jurídico.', 26),
    ('III', 10, 'Otras políticas públicas. El sistema sanitario: distribución de competencias, gestión y financiación. Política exterior y de cooperación al desarrollo. Régimen de telecomunicaciones y desarrollo de la sociedad de la información. La Agenda 2030 y los Objetivos de Desarrollo Sostenible.', 27),
    ('IV', 1, 'Las fuentes del derecho administrativo: concepto y clases. La jerarquía de las fuentes.', 28),
    ('IV', 2, 'La ley. Tipos de leyes. Reserva de ley. Disposiciones del Gobierno con fuerza de ley: decreto-ley y decreto legislativo.', 29),
    ('IV', 3, 'El reglamento: concepto, clases y límites. Los principios generales del Derecho. Los tratados internacionales.', 30),
    ('IV', 4, 'El acto administrativo: concepto, clases y elementos. Eficacia y validez de los actos administrativos. Su motivación y notificación.', 31),
    ('IV', 5, 'Los contratos del sector público (I): concepto, clases y elementos. Preparación, adjudicación, efectos, cumplimiento y extinción. La revisión de precios y otras alteraciones contractuales. Régimen de invalidez y recursos.', 32),
    ('IV', 6, 'Los contratos regulados por la Ley de Contratos del Sector Público (II). Tipos. Características generales.', 33),
    ('IV', 7, 'Procedimientos y formas de la actividad administrativa. La actividad de intervención, arbitral, de servicio público y de fomento. Formas de gestión de los servicios públicos. Ayudas y subvenciones públicas: régimen jurídico.', 34),
    ('IV', 8, 'La expropiación forzosa: concepto, naturaleza y elementos. Procedimientos de expropiación. Garantías jurisdiccionales.', 35),
    ('IV', 9, 'El régimen patrimonial de las Administraciones públicas. El dominio público. Los bienes patrimoniales del Estado. El Patrimonio Nacional. Los bienes comunales.', 36),
    ('IV', 10, 'La responsabilidad patrimonial de las Administraciones públicas. Procedimiento de responsabilidad patrimonial.', 37),
    ('IV', 11, 'Las Leyes del Procedimiento Administrativo Común de las Administraciones Públicas y del Régimen Jurídico del Sector Público. Procedimiento administrativo común y su alcance: iniciación, ordenación, instrucción y terminación. La obligación de resolver. El silencio administrativo.', 38),
    ('IV', 12, 'Los derechos de los ciudadanos en el procedimiento administrativo. Las garantías en el desarrollo del procedimiento. La revisión de los actos en vía administrativa: revisión de oficio y recursos administrativos.', 39),
    ('IV', 13, 'La jurisdicción contencioso-administrativa: funciones, órganos y competencias. El recurso contencioso-administrativo. Actividad administrativa impugnable. Las partes: capacidad, legitimación, representación y defensa.', 40),
    ('V', 1, 'El personal al servicio de las Administraciones públicas: concepto y clases. Adquisición y pérdida de la relación de servicio. Régimen jurídico.', 41),
    ('V', 2, 'Derechos y deberes del personal al servicio de las Administraciones Públicas. Régimen disciplinario.', 42),
    ('V', 3, 'Planificación de recursos humanos. Ofertas de empleo público. Selección de personal. Las competencias en materia de personal.', 43),
    ('V', 4, 'Formas de provisión de puestos de trabajo y movilidad en la Administración del Estado. Promoción interna y carrera profesional.', 44),
    ('V', 5, 'Situaciones administrativas del personal al servicio de las administraciones públicas. Incompatibilidades.', 45),
    ('V', 6, 'El sistema de retribuciones de los funcionarios. Retribuciones básicas y retribuciones complementarias. Las indemnizaciones por razón del servicio.', 46),
    ('V', 7, 'El personal laboral al servicio de las Administraciones públicas: su régimen jurídico. El IV Convenio Único para el personal laboral al servicio de la Administración General del Estado: ámbito de aplicación y sistema de clasificación.', 47),
    ('V', 8, 'Negociación colectiva, representación y participación institucional de los empleados públicos. El derecho de huelga y su ejercicio.', 48),
    ('V', 9, 'El régimen especial de la Seguridad Social de los funcionarios civiles del Estado. MUFACE y las clases pasivas: acción protectora. Concepto y clases de prestaciones. Derechos pasivos.', 49),
    ('V', 10, 'Acceso al empleo público y provisión de puestos de trabajo de las personas con discapacidad.', 50),
    ('VI', 1, 'El presupuesto. Concepto y clases. La Ley General Presupuestaria: principios generales y estructura. Las leyes de estabilidad presupuestaria.', 51),
    ('VI', 2, 'Las leyes anuales de presupuestos. Su contenido. El presupuesto del Estado. Principios de programación y de gestión. Contenido, elaboración y estructura. Desglose de aplicaciones presupuestarias.', 52),
    ('VI', 3, 'Gastos plurianuales. Modificaciones de los créditos iniciales. Transferencias de crédito. Créditos extraordinarios. Suplementos de crédito. Ampliaciones de créditos. Incorporaciones de créditos. Generaciones de créditos.', 53),
    ('VI', 4, 'Control del gasto público en España. La Intervención General de la Administración del Estado. Función interventora, control financiero permanente y auditoría pública. El Tribunal de Cuentas.', 54),
    ('VI', 5, 'El procedimiento administrativo de ejecución del presupuesto de gasto. Órganos competentes. Fases del procedimiento y su relación con la actuación administrativa. Especial referencia a la contratación administrativa y la gestión de subvenciones. Documentos contables que intervienen en la ejecución de los gastos y de los pagos. Gestión de la tesorería del Estado.', 55),
    ('VI', 6, 'Gastos para la compra de bienes y servicios. Gastos de inversión. Gastos de transferencias: corrientes y de capital. Anticipos de caja fija. Pagos «a justificar». Justificación de libramientos.', 56),
    ('VI', 7, 'Los ingresos públicos: concepto y clasificación. El sistema tributario español: régimen actual. Especial referencia al régimen de tasas y precios públicos.', 57),
    ('VI', 8, 'Retribuciones de los funcionarios públicos. Nóminas: estructura y normas de confección. Altas y bajas, su justificación. Ingresos en formalización. Devengo y liquidación de derechos económicos.', 58)
) AS v(bloque, tema, titulo, orden)
WHERE o.codigo = 'GACE'
ON CONFLICT (oposicion_id, bloque, tema) DO UPDATE
    SET titulo = EXCLUDED.titulo, orden = EXCLUDED.orden;

-- ── 5. Verificación ───────────────────────────────────────────────────────────
SELECT bloque, COUNT(*) AS n_temas
FROM normas.epigrafes
GROUP BY bloque ORDER BY bloque;

SELECT COUNT(*) AS total_epigrafes FROM normas.epigrafes;

