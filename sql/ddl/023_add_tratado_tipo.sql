-- Migración 023: añade 'tratado_internacional' al check constraint de normas.leyes.tipo
-- Necesario para cargar TUE y TFUE desde EUR-Lex

ALTER TABLE normas.leyes
    DROP CONSTRAINT IF EXISTS leyes_tipo_check;

ALTER TABLE normas.leyes
    ADD CONSTRAINT leyes_tipo_check
    CHECK (tipo IN (
        'constitucion',
        'ley_organica',
        'ley_ordinaria',
        'real_decreto_legislativo',
        'real_decreto',
        'orden_ministerial',
        'tratado_internacional'
    ));
