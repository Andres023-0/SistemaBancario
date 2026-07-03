-- =============================================================================
-- BANCOSNBC — Esquema Supabase (Fase 2)
-- Ejecutar completo en: Supabase Dashboard → SQL Editor → New query → Run
-- =============================================================================

-- -----------------------------------------------------------------------------
-- 1. PERFILES — conecta auth.users con rol y documento
-- -----------------------------------------------------------------------------
create table public.perfiles (
    id          uuid primary key references auth.users(id) on delete cascade,
    rol         text not null check (rol in ('admin', 'usuario')),
    documento   text,                       -- null para admins
    creado_en   timestamptz not null default now()
);

alter table public.perfiles enable row level security;

-- Cada quien puede leer su propio perfil; los admins pueden leer todos.
create policy "perfiles_select_propio_o_admin"
    on public.perfiles for select
    using (
        id = auth.uid()
        or exists (select 1 from public.perfiles p where p.id = auth.uid() and p.rol = 'admin')
    );

-- Nadie inserta/edita perfiles directamente desde el cliente (lo hace el trigger de abajo).

-- -----------------------------------------------------------------------------
-- 2. USUARIOS (clientes del banco, equivalente a tu clase Usuario)
-- -----------------------------------------------------------------------------
create table public.usuarios (
    documento       text primary key,
    nombre          text not null,
    celular         text default '',
    correo          text default '',
    verificado_kyc  boolean not null default false,
    creado_en       timestamptz not null default now()
);

alter table public.usuarios enable row level security;

create policy "usuarios_select_propio_o_admin"
    on public.usuarios for select
    using (
        documento = (select documento from public.perfiles where id = auth.uid())
        or exists (select 1 from public.perfiles p where p.id = auth.uid() and p.rol = 'admin')
    );

create policy "usuarios_insert_solo_admin"
    on public.usuarios for insert
    with check (exists (select 1 from public.perfiles p where p.id = auth.uid() and p.rol = 'admin'));

create policy "usuarios_update_solo_admin"
    on public.usuarios for update
    using (exists (select 1 from public.perfiles p where p.id = auth.uid() and p.rol = 'admin'));

-- -----------------------------------------------------------------------------
-- 3. SUCURSALES
-- -----------------------------------------------------------------------------
create table public.sucursales (
    id      bigint generated always as identity primary key,
    nombre  text not null unique
);

alter table public.sucursales enable row level security;

-- Cualquier usuario autenticado puede ver la lista de sucursales (dato público del banco).
create policy "sucursales_select_autenticado"
    on public.sucursales for select
    using (auth.role() = 'authenticated');

create policy "sucursales_insert_solo_admin"
    on public.sucursales for insert
    with check (exists (select 1 from public.perfiles p where p.id = auth.uid() and p.rol = 'admin'));

-- -----------------------------------------------------------------------------
-- 4. CUENTAS (equivalente a tu clase Cuenta)
-- -----------------------------------------------------------------------------
create table public.cuentas (
    numero          text primary key,
    documento       text not null references public.usuarios(documento),
    sucursal_id     bigint references public.sucursales(id),
    tipo            text not null check (tipo in ('corriente', 'ahorros')),
    saldo           numeric(14,2) not null default 0,
    estado          text not null default 'activa'
                    check (estado in ('activa', 'bloqueada', 'suspendida', 'cerrada')),
    creado_en       timestamptz not null default now()
);

alter table public.cuentas enable row level security;

create policy "cuentas_select_propia_o_admin"
    on public.cuentas for select
    using (
        documento = (select documento from public.perfiles where id = auth.uid())
        or exists (select 1 from public.perfiles p where p.id = auth.uid() and p.rol = 'admin')
    );

create policy "cuentas_insert_solo_admin"
    on public.cuentas for insert
    with check (exists (select 1 from public.perfiles p where p.id = auth.uid() and p.rol = 'admin'));

create policy "cuentas_update_propia_o_admin"
    on public.cuentas for update
    using (
        documento = (select documento from public.perfiles where id = auth.uid())
        or exists (select 1 from public.perfiles p where p.id = auth.uid() and p.rol = 'admin')
    );

-- -----------------------------------------------------------------------------
-- 5. TRANSACCIONES (historial de depósitos, retiros, transferencias)
-- -----------------------------------------------------------------------------
create table public.transacciones (
    id                  bigint generated always as identity primary key,
    cuenta_origen       text references public.cuentas(numero),
    cuenta_destino      text references public.cuentas(numero),
    tipo                text not null check (tipo in ('deposito', 'retiro', 'transferencia')),
    monto               numeric(14,2) not null check (monto > 0),
    canal               text not null check (canal in ('web', 'movil', 'cajero')),
    alertas_fraude      text[],                 -- array de alertas generadas por DetectorFraude
    creado_en           timestamptz not null default now()
);

alter table public.transacciones enable row level security;

create policy "transacciones_select_propia_o_admin"
    on public.transacciones for select
    using (
        exists (
            select 1 from public.cuentas c
            where (c.numero = cuenta_origen or c.numero = cuenta_destino)
            and c.documento = (select documento from public.perfiles where id = auth.uid())
        )
        or exists (select 1 from public.perfiles p where p.id = auth.uid() and p.rol = 'admin')
    );

-- Las transacciones se insertan solo desde el backend (con la secret key),
-- nunca directo desde el navegador. Por eso no hay policy de insert para
-- el rol authenticated — el backend usa la service_role / secret key,
-- que se salta RLS por diseño.

-- -----------------------------------------------------------------------------
-- 6. PRESTAMOS (equivalente a tu clase Prestamo)
-- -----------------------------------------------------------------------------
create table public.prestamos (
    id                  uuid primary key default gen_random_uuid(),
    documento           text not null references public.usuarios(documento),
    numero_cuenta       text not null references public.cuentas(numero),
    monto               numeric(14,2) not null check (monto > 0),
    num_cuotas          integer not null check (num_cuotas > 0),
    tasa_anual          numeric(6,3) not null check (tasa_anual > 0),
    tipo_interes        text not null default 'fijo',
    saldo_pendiente     numeric(14,2) not null,
    creado_en           timestamptz not null default now()
);

alter table public.prestamos enable row level security;

create policy "prestamos_select_propio_o_admin"
    on public.prestamos for select
    using (
        documento = (select documento from public.perfiles where id = auth.uid())
        or exists (select 1 from public.perfiles p where p.id = auth.uid() and p.rol = 'admin')
    );

-- -----------------------------------------------------------------------------
-- 7. TRIGGER — crea automáticamente un perfil cuando alguien se registra
--    (por defecto como 'usuario'; los admins se promueven manualmente,
--    ver instrucciones al final)
-- -----------------------------------------------------------------------------
create or replace function public.crear_perfil_nuevo_usuario()
returns trigger
language plpgsql
security definer set search_path = public
as $$
begin
    insert into public.perfiles (id, rol, documento)
    values (
        new.id,
        coalesce(new.raw_user_meta_data->>'rol', 'usuario'),
        new.raw_user_meta_data->>'documento'
    );
    return new;
end;
$$;

create trigger al_registrarse_crear_perfil
    after insert on auth.users
    for each row execute function public.crear_perfil_nuevo_usuario();

-- =============================================================================
-- FIN DEL ESQUEMA.
--
-- Para promover manualmente al primer admin, después de que se registre
-- con Supabase Auth, corre esto reemplazando el email:
--
--   update public.perfiles set rol = 'admin'
--   where id = (select id from auth.users where email = 'admin@bancosnbc.com');
-- =============================================================================
