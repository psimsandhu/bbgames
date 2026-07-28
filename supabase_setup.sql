-- ========================================================
-- BB Games database
-- Run this once in the Supabase SQL Editor.
-- ========================================================

create table if not exists public.rooms (
    code text primary key,
    host_key text not null,
    active_game text,
    status text not null default 'lobby',
    game_state jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table if not exists public.players (
    id uuid primary key,
    room_code text not null
        references public.rooms(code)
        on delete cascade,
    name text not null,
    score integer not null default 0,
    bingo_card jsonb not null default '[]'::jsonb,
    bingo_claimed boolean not null default false,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table if not exists public.responses (
    id uuid primary key,
    room_code text not null
        references public.rooms(code)
        on delete cascade,
    player_id uuid not null
        references public.players(id)
        on delete cascade,
    game text not null,
    round_key text not null,
    answer jsonb not null default '{}'::jsonb,
    graded boolean not null default false,
    points_awarded integer not null default 0,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),

    constraint unique_player_round_response
        unique (room_code, player_id, game, round_key)
);

create index if not exists players_room_code_index
    on public.players(room_code);

create index if not exists responses_room_round_index
    on public.responses(room_code, game, round_key);

-- The Streamlit app connects using the server-side service-role key.
-- Browser users never receive the database key directly.
alter table public.rooms enable row level security;
alter table public.players enable row level security;
alter table public.responses enable row level security;

-- No public anon policies are added.
-- The service-role key bypasses RLS from the Streamlit server.
