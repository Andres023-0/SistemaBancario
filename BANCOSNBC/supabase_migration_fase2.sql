-- =============================================================================
-- BANCOSNBC — Migración Fase 2 (ejecutar DESPUÉS de supabase_schema.sql)
-- Supabase Dashboard → SQL Editor → New query → Run
--
-- Todo es ADITIVO: no se elimina ni se reescribe ninguna tabla ni política
-- existente. Solo se agregan columnas y se ajustan las FK para que borrar
-- un usuario (con sus cuentas) desde eliminar_usuario() no falle por
-- restricción de integridad referencial.
-- =============================================================================

-- -----------------------------------------------------------------------------
-- 1. CASCADAS DE BORRADO
--    eliminar_usuario() en usuario_facade.py desvincula las cuentas del
--    usuario y las descarta de memoria. En Supabase eso se traduce en
--    borrar también sus filas de cuentas/transacciones/prestamos.
-- -----------------------------------------------------------------------------
alter table public.cuentas
    drop constraint cuentas_documento_fkey,
    add constraint cuentas_documento_fkey
        foreign key (documento) references public.usuarios(documento)
        on delete cascade;

alter table public.transacciones
    drop constraint transacciones_cuenta_origen_fkey,
    add constraint transacciones_cuenta_origen_fkey
        foreign key (cuenta_origen) references public.cuentas(numero)
        on delete cascade;

alter table public.transacciones
    drop constraint transacciones_cuenta_destino_fkey,
    add constraint transacciones_cuenta_destino_fkey
        foreign key (cuenta_destino) references public.cuentas(numero)
        on delete cascade;

alter table public.prestamos
    drop constraint prestamos_documento_fkey,
    add constraint prestamos_documento_fkey
        foreign key (documento) references public.usuarios(documento)
        on delete cascade;

alter table public.prestamos
    drop constraint prestamos_numero_cuenta_fkey,
    add constraint prestamos_numero_cuenta_fkey
        foreign key (numero_cuenta) references public.cuentas(numero)
        on delete cascade;

-- -----------------------------------------------------------------------------
-- 2. COLUMNAS ADICIONALES EN "prestamos"
--    El schema original solo guardaba el snapshot inicial (saldo_pendiente).
--    Para reconstruir el objeto Prestamo completo al reiniciar el servidor
--    (cuotas_pagadas, total_pagado, estado, historial de pagos) se agregan
--    estas columnas. La clase Prestamo (Strategy) no cambia: esto es
--    solo "dónde vive el dato".
-- -----------------------------------------------------------------------------
alter table public.prestamos
    add column if not exists cuota_mensual    numeric(14,2) not null default 0,
    add column if not exists total_intereses  numeric(14,2) not null default 0,
    add column if not exists total_a_pagar    numeric(14,2) not null default 0,
    add column if not exists cuotas_pagadas   integer       not null default 0,
    add column if not exists total_pagado     numeric(14,2) not null default 0,
    add column if not exists estado           text          not null default 'activo'
        check (estado in ('activo', 'pagado')),
    add column if not exists pagos            jsonb         not null default '[]'::jsonb;

-- =============================================================================
-- FIN DE LA MIGRACIÓN.
-- =============================================================================
