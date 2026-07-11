-- ============================================================
-- Migración 035: normas.epigrafe_leyes (relación tema ↔ ley)
-- Necesaria para el sidebar de Administración: Bloque → Tema → Ley,
-- que filtra las leyes candidatas por el tema oficial elegido. Se puebla
-- con scripts/asignar_epigrafe_leyes.py (clasificación por IA, revisable).
-- Ejecutar en Supabase: SQL Editor → New query → Run
-- ============================================================

CREATE TABLE IF NOT EXISTS normas.epigrafe_leyes (
    epigrafe_id INTEGER NOT NULL REFERENCES normas.epigrafes(epigrafe_id) ON DELETE CASCADE,
    ley_id      INTEGER NOT NULL REFERENCES normas.leyes(ley_id) ON DELETE CASCADE,
    PRIMARY KEY (epigrafe_id, ley_id)
);

COMMENT ON TABLE normas.epigrafe_leyes IS
    'Relación muchos-a-muchos tema oficial (epígrafe) ↔ ley: qué leyes son relevantes para cada tema del programa. Poblada por scripts/asignar_epigrafe_leyes.py (clasificación por IA sobre el título del tema y el catálogo de leyes de su bloque), no hardcodeada. Usada por el sidebar de Administración para filtrar "Ley" una vez elegido un "Tema".';

CREATE INDEX IF NOT EXISTS idx_epigrafe_leyes_ley
    ON normas.epigrafe_leyes (ley_id);

-- Verificación
SELECT COUNT(*) AS filas_epigrafe_leyes FROM normas.epigrafe_leyes;
