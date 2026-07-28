from __future__ import annotations

import html
import json
import random
import secrets
import string
import time
import uuid
from datetime import datetime, timezone
from typing import Any

import qrcode
import streamlit as st
from supabase import Client, create_client


# =========================================================
# App configuration
# =========================================================

st.set_page_config(
    page_title="BB Games",
    page_icon="🧸",
    layout="wide",
    initial_sidebar_state="collapsed",
)

MAX_PLAYERS = 20
ROOM_CODE_LENGTH = 5

GAME_NAMES = {
    "bingo": "Baby Bingo",
    "price": "Baby Price Challenge",
    "quiz": "Baby Brain Board",
}


# =========================================================
# Game content
# =========================================================

BINGO_WORDS = [
    "Baby bottle",
    "Diaper bag",
    "Pacifier",
    "Stroller",
    "Baby monitor",
    "Crib",
    "High chair",
    "Swaddle",
    "Baby wipes",
    "Rattle",
    "Teddy bear",
    "Onesie",
    "Bib",
    "Nursery",
    "Storybook",
    "Bath time",
    "Baby socks",
    "Teething ring",
    "Changing pad",
    "Lullaby",
    "Car seat",
    "Baby shampoo",
    "Burp cloth",
    "Blanket",
    "Rubber duck",
    "Diapers",
    "Night-light",
    "Baby carrier",
    "Hooded towel",
    "Stuffed animal",
]

PRICE_ROUNDS = [
    {
        "title": "Newborn Diapers",
        "description": "One package of approximately 30 newborn-size diapers.",
        "price": 10.99,
        "emoji": "🧷",
    },
    {
        "title": "Baby Wipes",
        "description": "A three-pack containing approximately 168 unscented wipes.",
        "price": 8.49,
        "emoji": "🫧",
    },
    {
        "title": "Three Baby Bodysuits",
        "description": "A three-pack of short-sleeve cotton bodysuits.",
        "price": 14.99,
        "emoji": "👕",
    },
    {
        "title": "Baby Shampoo",
        "description": "One 13.6-fluid-ounce bottle of gentle baby shampoo.",
        "price": 6.49,
        "emoji": "🛁",
    },
    {
        "title": "Pacifier Two-Pack",
        "description": "Two silicone pacifiers for newborn babies.",
        "price": 7.99,
        "emoji": "🍼",
    },
    {
        "title": "Digital Thermometer",
        "description": "A basic digital baby thermometer.",
        "price": 16.99,
        "emoji": "🌡️",
    },
    {
        "title": "Muslin Swaddle",
        "description": "One soft muslin swaddle blanket.",
        "price": 19.99,
        "emoji": "🧸",
    },
    {
        "title": "Nursery Bundle",
        "description": "A baby monitor, diaper bag, and soft infant carrier.",
        "price": 164.97,
        "emoji": "🎁",
    },
]

QUIZ_CATEGORIES = [
    {
        "name": "Baby Basics",
        "questions": [
            {
                "value": 100,
                "question": "What item is fastened around a baby during feeding?",
                "answer": "A bib",
            },
            {
                "value": 200,
                "question": "What furniture is designed for a baby to sleep in?",
                "answer": "A crib",
            },
            {
                "value": 300,
                "question": "What cloth is placed over a shoulder while burping a baby?",
                "answer": "A burp cloth",
            },
            {
                "value": 400,
                "question": "What is wrapping a baby snugly in a blanket called?",
                "answer": "Swaddling",
            },
        ],
    },
    {
        "name": "Tiny Animals",
        "questions": [
            {
                "value": 100,
                "question": "What is a baby dog called?",
                "answer": "A puppy",
            },
            {
                "value": 200,
                "question": "What is a baby cat called?",
                "answer": "A kitten",
            },
            {
                "value": 300,
                "question": "What is a baby kangaroo called?",
                "answer": "A joey",
            },
            {
                "value": 400,
                "question": "What is a baby swan called?",
                "answer": "A cygnet",
            },
        ],
    },
    {
        "name": "Story Time",
        "questions": [
            {
                "value": 100,
                "question": "Which nursery-rhyme character sat on a wall?",
                "answer": "Humpty Dumpty",
            },
            {
                "value": 200,
                "question": "Which little star is described as being wondered about?",
                "answer": "Twinkle, Twinkle, Little Star",
            },
            {
                "value": 300,
                "question": "Which nursery-rhyme sheep was asked whether it had wool?",
                "answer": "Baa, Baa, Black Sheep",
            },
            {
                "value": 400,
                "question": "Which character lost her sheep?",
                "answer": "Little Bo-Peep",
            },
        ],
    },
    {
        "name": "Parent Prep",
        "questions": [
            {
                "value": 100,
                "question": "What portable bag holds diapers, wipes, and spare clothes?",
                "answer": "A diaper bag",
            },
            {
                "value": 200,
                "question": "What padded surface is used during diaper changes?",
                "answer": "A changing pad",
            },
            {
                "value": 300,
                "question": "What device lets caregivers hear or see a baby from another room?",
                "answer": "A baby monitor",
            },
            {
                "value": 400,
                "question": "What seat secures an infant while traveling in a vehicle?",
                "answer": "An infant car seat",
            },
        ],
    },
]


# =========================================================
# Styling
# =========================================================

st.markdown(
    """
    <style>
        :root {
            --bb-cream: #fffaf3;
            --bb-pink: #e8799a;
            --bb-pink-dark: #c64f75;
            --bb-purple: #60406f;
            --bb-purple-dark: #3e2949;
            --bb-mint: #bce9d9;
            --bb-yellow: #ffdc82;
            --bb-blue: #b8dff1;
            --bb-ink: #34293a;
        }

        .stApp {
            background:
                radial-gradient(circle at 5% 0%, #ffe3ea 0, transparent 26%),
                radial-gradient(circle at 95% 5%, #dcf4ec 0, transparent 24%),
                var(--bb-cream);
            color: var(--bb-ink);
        }

        [data-testid="stHeader"] {
            background: transparent;
        }

        [data-testid="stToolbar"] {
            right: 1rem;
        }

        .block-container {
            max-width: 1180px;
            padding-top: 1.4rem;
            padding-bottom: 4rem;
        }

        h1, h2, h3 {
            color: var(--bb-purple-dark);
        }

        .bb-brand {
            display: flex;
            align-items: center;
            gap: 0.8rem;
            margin-bottom: 1.2rem;
        }

        .bb-logo {
            display: grid;
            width: 3.2rem;
            height: 3.2rem;
            place-items: center;
            border-radius: 1rem;
            color: white;
            background: var(--bb-purple);
            font-size: 1.75rem;
            box-shadow: 0 12px 28px rgba(62, 41, 73, 0.18);
        }

        .bb-brand-name {
            margin: 0;
            color: var(--bb-purple-dark);
            font-size: 2rem;
            font-weight: 900;
            line-height: 1;
        }

        .bb-brand-copy {
            margin: 0.25rem 0 0;
            color: #766b7b;
        }

        .bb-card {
            padding: clamp(1.2rem, 4vw, 2rem);
            border: 1px solid rgba(96, 64, 111, 0.1);
            border-radius: 1.5rem;
            background: rgba(255, 255, 255, 0.95);
            box-shadow: 0 14px 38px rgba(62, 41, 73, 0.11);
        }

        .bb-hero {
            padding: clamp(1.5rem, 5vw, 3.2rem);
            border-radius: 1.75rem;
            background:
                linear-gradient(
                    135deg,
                    rgba(255,255,255,0.96),
                    rgba(255,248,250,0.96)
                );
            box-shadow: 0 16px 44px rgba(62, 41, 73, 0.12);
        }

        .bb-hero h1 {
            margin: 0 0 0.7rem;
            font-size: clamp(2.8rem, 8vw, 5.7rem);
            line-height: 0.95;
        }

        .bb-subtitle {
            max-width: 42rem;
            color: #74697b;
            font-size: 1.08rem;
            line-height: 1.6;
        }

        .bb-room-code {
            display: inline-block;
            padding: 0.7rem 1rem;
            border-radius: 999px;
            color: var(--bb-purple-dark);
            background: #f2e8f5;
            font-size: 1.15rem;
            font-weight: 900;
            letter-spacing: 0.18rem;
        }

        .bb-game-card {
            min-height: 10rem;
            padding: 1.2rem;
            border-radius: 1.3rem;
            background: #fff2f6;
        }

        .bb-game-card.mint {
            background: #edf9f5;
        }

        .bb-game-card.yellow {
            background: #fff8df;
        }

        .bb-game-icon {
            font-size: 2.5rem;
        }

        .bb-game-title {
            margin-top: 0.4rem;
            color: var(--bb-purple-dark);
            font-size: 1.3rem;
            font-weight: 900;
        }

        .bb-muted {
            color: #766b7b;
        }

        .bb-called {
            display: grid;
            min-height: 12rem;
            padding: 2rem;
            place-items: center;
            border-radius: 1.5rem;
            color: var(--bb-purple-dark);
            background: var(--bb-mint);
            text-align: center;
            font-size: clamp(2rem, 8vw, 4.8rem);
            font-weight: 950;
        }

        .bb-price {
            padding: 2rem;
            border-radius: 1.5rem;
            background: #fff5d8;
            text-align: center;
        }

        .bb-product-emoji {
            font-size: 4rem;
        }

        .bb-actual-price {
            color: var(--bb-pink-dark);
            font-size: clamp(3rem, 9vw, 6rem);
            font-weight: 950;
        }

        .bb-question {
            padding: 2rem;
            border-radius: 1.5rem;
            background: #e9f6fb;
            text-align: center;
        }

        .bb-question-text {
            color: var(--bb-purple-dark);
            font-size: clamp(1.6rem, 5vw, 3rem);
            font-weight: 900;
            line-height: 1.15;
        }

        .bb-answer {
            margin-top: 1rem;
            padding: 1rem;
            border-radius: 1rem;
            background: var(--bb-mint);
            color: var(--bb-purple-dark);
            font-size: 1.2rem;
            font-weight: 900;
        }

        .bb-score-row {
            display: flex;
            justify-content: space-between;
            gap: 1rem;
            padding: 0.7rem 0.9rem;
            margin-bottom: 0.45rem;
            border-radius: 0.85rem;
            background: #faf5fb;
        }

        .bb-score-value {
            color: var(--bb-pink-dark);
            font-weight: 900;
        }

        .bb-pill {
            display: inline-block;
            padding: 0.4rem 0.65rem;
            margin: 0.2rem;
            border-radius: 999px;
            color: var(--bb-purple-dark);
            background: #f1e8f4;
            font-size: 0.84rem;
            font-weight: 800;
        }

        .bb-bingo-grid {
            display: grid;
            grid-template-columns: repeat(5, minmax(0, 1fr));
            gap: 0.35rem;
            margin: 1rem 0;
        }

        .bb-bingo-space {
            display: grid;
            min-height: 5rem;
            padding: 0.3rem;
            place-items: center;
            border-radius: 0.75rem;
            color: var(--bb-purple-dark);
            background: #f4ebf6;
            text-align: center;
            font-size: clamp(0.58rem, 2.5vw, 0.85rem);
            font-weight: 800;
        }

        .bb-bingo-space.marked {
            color: white;
            background: var(--bb-pink-dark);
        }

        .bb-quiz-header {
            min-height: 4rem;
            display: grid;
            place-items: center;
            padding: 0.5rem;
            border-radius: 0.7rem;
            color: white;
            background: var(--bb-purple-dark);
            text-align: center;
            font-weight: 900;
        }

        .stButton > button {
            min-height: 2.9rem;
            border: 0;
            border-radius: 0.85rem;
            font-weight: 800;
        }

        .stButton > button[kind="primary"] {
            background: var(--bb-pink-dark);
        }

        .stTextInput input,
        .stNumberInput input {
            border-radius: 0.8rem;
        }

        @media (max-width: 640px) {
            .block-container {
                padding-left: 0.7rem;
                padding-right: 0.7rem;
            }

            .bb-card {
                border-radius: 1.1rem;
            }

            .bb-bingo-space {
                min-height: 4.2rem;
            }
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# Supabase connection
# =========================================================

@st.cache_resource
def get_database() -> Client:
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_SERVICE_KEY"]
    except KeyError as exc:
        raise RuntimeError(
            "Missing SUPABASE_URL or SUPABASE_SERVICE_KEY in Streamlit secrets."
        ) from exc

    return create_client(url, key)


db = get_database()


# =========================================================
# Utilities
# =========================================================

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def safe_text(value: Any, length: int = 100) -> str:
    return str(value or "").strip()[:length]


def money(value: float) -> str:
    return f"${value:,.2f}"


def make_room_code() -> str:
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"

    for _ in range(100):
        code = "".join(
            secrets.choice(alphabet)
            for _ in range(ROOM_CODE_LENGTH)
        )

        existing = (
            db.table("rooms")
            .select("code")
            .eq("code", code)
            .execute()
            .data
        )

        if not existing:
            return code

    raise RuntimeError("Unable to generate a unique room code.")


def make_host_key() -> str:
    return secrets.token_urlsafe(24)


def make_bingo_card() -> list[dict[str, Any]]:
    selected = random.sample(BINGO_WORDS, 24)
    selected.insert(12, "FREE")

    return [
        {
            "label": label,
            "marked": label == "FREE",
        }
        for label in selected
    ]


def default_game_state() -> dict[str, Any]:
    return {
        "bingo": {
            "called": [],
            "current": None,
            "winner_ids": [],
        },
        "price": {
            "round_index": 0,
            "open": False,
            "revealed": False,
            "results": [],
        },
        "quiz": {
            "selected": None,
            "open": False,
            "revealed": False,
            "used": [],
        },
    }


def get_room(room_code: str) -> dict[str, Any] | None:
    code = safe_text(room_code, ROOM_CODE_LENGTH).upper()

    response = (
        db.table("rooms")
        .select("*")
        .eq("code", code)
        .limit(1)
        .execute()
    )

    return response.data[0] if response.data else None


def get_players(room_code: str) -> list[dict[str, Any]]:
    response = (
        db.table("players")
        .select("*")
        .eq("room_code", room_code)
        .order("score", desc=True)
        .order("name")
        .execute()
    )

    return response.data or []


def get_player(
    room_code: str,
    player_id: str,
) -> dict[str, Any] | None:
    response = (
        db.table("players")
        .select("*")
        .eq("room_code", room_code)
        .eq("id", player_id)
        .limit(1)
        .execute()
    )

    return response.data[0] if response.data else None


def update_room(
    room_code: str,
    values: dict[str, Any],
) -> None:
    values["updated_at"] = now_iso()

    (
        db.table("rooms")
        .update(values)
        .eq("code", room_code)
        .execute()
    )


def update_player(
    player_id: str,
    values: dict[str, Any],
) -> None:
    values["updated_at"] = now_iso()

    (
        db.table("players")
        .update(values)
        .eq("id", player_id)
        .execute()
    )


def get_responses(
    room_code: str,
    game: str,
    round_key: str,
) -> list[dict[str, Any]]:
    response = (
        db.table("responses")
        .select("*")
        .eq("room_code", room_code)
        .eq("game", game)
        .eq("round_key", round_key)
        .order("created_at")
        .execute()
    )

    return response.data or []


def save_response(
    room_code: str,
    player_id: str,
    game: str,
    round_key: str,
    answer: dict[str, Any],
) -> None:
    row = {
        "id": str(uuid.uuid4()),
        "room_code": room_code,
        "player_id": player_id,
        "game": game,
        "round_key": round_key,
        "answer": answer,
        "graded": False,
        "points_awarded": 0,
        "created_at": now_iso(),
        "updated_at": now_iso(),
    }

    (
        db.table("responses")
        .upsert(
            row,
            on_conflict="room_code,player_id,game,round_key",
        )
        .execute()
    )


def clear_responses(
    room_code: str,
    game: str | None = None,
) -> None:
    query = (
        db.table("responses")
        .delete()
        .eq("room_code", room_code)
    )

    if game:
        query = query.eq("game", game)

    query.execute()


def reset_scores(room_code: str) -> None:
    players = get_players(room_code)

    for player in players:
        update_player(player["id"], {"score": 0})


def build_join_url(room_code: str) -> str:
    app_url = st.secrets.get(
        "APP_URL",
        "https://your-app-name.streamlit.app",
    ).rstrip("/")

    return f"{app_url}/?room={room_code}"


def create_qr(join_url: str):
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=2,
    )
    qr.add_data(join_url)
    qr.make(fit=True)

    return qr.make_image(
        fill_color="#4b315f",
        back_color="white",
    )


def render_brand() -> None:
    st.markdown(
        """
        <div class="bb-brand">
            <div class="bb-logo">🧸</div>
            <div>
                <div class="bb-brand-name">BB Games</div>
                <p class="bb-brand-copy">
                    Live baby-shower games for every guest
                </p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_scoreboard(players: list[dict[str, Any]]) -> None:
    st.subheader(f"Guests · {len(players)}/{MAX_PLAYERS}")

    if not players:
        st.caption("No guests have joined yet.")
        return

    for position, player in enumerate(players, start=1):
        name = html.escape(player["name"])
        score = int(player.get("score", 0))

        st.markdown(
            f"""
            <div class="bb-score-row">
                <span>{position}. {name}</span>
                <span class="bb-score-value">{score}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )


def valid_bingo(card: list[dict[str, Any]]) -> bool:
    marked = [bool(space.get("marked")) for space in card]

    lines: list[list[int]] = []

    for row in range(5):
        lines.append([row * 5 + column for column in range(5)])

    for column in range(5):
        lines.append([row * 5 + column for row in range(5)])

    lines.append([0, 6, 12, 18, 24])
    lines.append([4, 8, 12, 16, 20])

    return any(
        all(marked[index] for index in line)
        for line in lines
    )


def verify_host(room: dict[str, Any]) -> bool:
    supplied_key = safe_text(st.query_params.get("key"), 200)
    return bool(supplied_key) and secrets.compare_digest(
        supplied_key,
        room["host_key"],
    )


def current_role() -> tuple[str, str | None]:
    host_code = safe_text(st.query_params.get("host"), ROOM_CODE_LENGTH).upper()
    room_code = safe_text(st.query_params.get("room"), ROOM_CODE_LENGTH).upper()

    if host_code:
        return "host", host_code

    if room_code:
        return "player", room_code

    return "home", None


# =========================================================
# Home screen
# =========================================================

def render_home() -> None:
    st.markdown(
        """
        <div class="bb-hero">
            <h1>Ready, set, baby!</h1>
            <p class="bb-subtitle">
                Host a live baby-shower game on a shared screen.
                Up to 20 guests can scan the room QR code and submit
                answers from their phones.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.write("")

    host_column, join_column = st.columns(2, gap="large")

    with host_column:
        st.markdown('<div class="bb-card">', unsafe_allow_html=True)
        st.subheader("Host a game")
        st.write(
            "Create a new room, display the QR code, and control each round."
        )

        if st.button(
            "Create Host Room",
            type="primary",
            use_container_width=True,
        ):
            code = make_room_code()
            host_key = make_host_key()

            room = {
                "code": code,
                "host_key": host_key,
                "active_game": None,
                "status": "lobby",
                "game_state": default_game_state(),
                "created_at": now_iso(),
                "updated_at": now_iso(),
            }

            db.table("rooms").insert(room).execute()

            st.query_params.clear()
            st.query_params["host"] = code
            st.query_params["key"] = host_key
            st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

    with join_column:
        st.markdown('<div class="bb-card">', unsafe_allow_html=True)
        st.subheader("Join a game")

        with st.form("home_join_form"):
            code = st.text_input(
                "Room code",
                max_chars=ROOM_CODE_LENGTH,
                placeholder="ABC12",
            )

            submitted = st.form_submit_button(
                "Join Room",
                use_container_width=True,
            )

        if submitted:
            code = safe_text(code, ROOM_CODE_LENGTH).upper()
            room = get_room(code)

            if not room:
                st.error("That room could not be found.")
            else:
                st.query_params.clear()
                st.query_params["room"] = code
                st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)


# =========================================================
# Host screen
# =========================================================

def start_game(room: dict[str, Any], game: str) -> None:
    state = default_game_state()
    reset_scores(room["code"])
    clear_responses(room["code"])

    if game == "bingo":
        players = get_players(room["code"])

        for player in players:
            update_player(
                player["id"],
                {
                    "bingo_card": make_bingo_card(),
                    "bingo_claimed": False,
                },
            )

    update_room(
        room["code"],
        {
            "active_game": game,
            "status": "playing",
            "game_state": state,
        },
    )


def render_game_picker(room: dict[str, Any]) -> None:
    st.subheader("Choose a game")

    columns = st.columns(3, gap="medium")

    game_options = [
        (
            "bingo",
            "🍼",
            "Baby Bingo",
            "Call baby-themed words while guests mark unique cards.",
            "",
        ),
        (
            "price",
            "🏷️",
            "Baby Price Challenge",
            "Guests estimate baby-product prices without going over.",
            "mint",
        ),
        (
            "quiz",
            "🧠",
            "Baby Brain Board",
            "Choose questions from an original baby-themed quiz board.",
            "yellow",
        ),
    ]

    for column, option in zip(columns, game_options):
        game, icon, title, description, css_class = option

        with column:
            st.markdown(
                f"""
                <div class="bb-game-card {css_class}">
                    <div class="bb-game-icon">{icon}</div>
                    <div class="bb-game-title">{title}</div>
                    <p class="bb-muted">{description}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

            if st.button(
                f"Start {title}",
                key=f"start_{game}",
                use_container_width=True,
            ):
                start_game(room, game)
                st.rerun()


def host_bingo(room: dict[str, Any]) -> None:
    state = room["game_state"]
    bingo = state["bingo"]
    called = bingo.get("called", [])
    current = bingo.get("current")

    st.subheader("Baby Bingo")

    st.markdown(
        f"""
        <div class="bb-called">
            {html.escape(current or "Ready to call?")}
        </div>
        """,
        unsafe_allow_html=True,
    )

    button_column, reset_column = st.columns(2)

    with button_column:
        if st.button(
            "Call Next Item",
            type="primary",
            use_container_width=True,
            disabled=len(called) >= len(BINGO_WORDS),
        ):
            available = [
                word for word in BINGO_WORDS
                if word not in called
            ]

            if available:
                selected = random.choice(available)
                called.append(selected)
                bingo["current"] = selected
                bingo["called"] = called
                state["bingo"] = bingo

                update_room(
                    room["code"],
                    {"game_state": state},
                )
                st.rerun()

    with reset_column:
        if st.button(
            "Reset Bingo",
            use_container_width=True,
        ):
            players = get_players(room["code"])

            for player in players:
                update_player(
                    player["id"],
                    {
                        "bingo_card": make_bingo_card(),
                        "bingo_claimed": False,
                    },
                )

            state["bingo"] = {
                "called": [],
                "current": None,
                "winner_ids": [],
            }

            update_room(
                room["code"],
                {"game_state": state},
            )
            st.rerun()

    st.write(f"**Called items:** {len(called)}")

    if called:
        pills = "".join(
            f'<span class="bb-pill">{html.escape(word)}</span>'
            for word in called
        )
        st.markdown(pills, unsafe_allow_html=True)


def host_price(room: dict[str, Any]) -> None:
    state = room["game_state"]
    price_state = state["price"]
    round_index = int(price_state.get("round_index", 0))
    round_data = PRICE_ROUNDS[round_index]
    round_key = f"price-{round_index}"

    responses = get_responses(
        room["code"],
        "price",
        round_key,
    )

    st.subheader(
        f"Baby Price Challenge · Round {round_index + 1}"
    )

    st.markdown(
        f"""
        <div class="bb-price">
            <div class="bb-product-emoji">{round_data["emoji"]}</div>
            <h2>{html.escape(round_data["title"])}</h2>
            <p>{html.escape(round_data["description"])}</p>
            {
                f'<div class="bb-actual-price">'
                f'{money(round_data["price"])}</div>'
                if price_state.get("revealed")
                else f'<strong>{len(responses)} response(s)</strong>'
            }
        </div>
        """,
        unsafe_allow_html=True,
    )

    open_column, reveal_column, next_column = st.columns(3)

    with open_column:
        if st.button(
            "Open Guessing",
            use_container_width=True,
            disabled=(
                price_state.get("open")
                or price_state.get("revealed")
            ),
        ):
            price_state["open"] = True
            price_state["revealed"] = False
            price_state["results"] = []
            state["price"] = price_state

            update_room(
                room["code"],
                {"game_state": state},
            )
            st.rerun()

    with reveal_column:
        if st.button(
            "Reveal Price",
            type="primary",
            use_container_width=True,
            disabled=not price_state.get("open"),
        ):
            scored_results = []

            for response in responses:
                guess = float(response["answer"]["amount"])
                actual = float(round_data["price"])

                scored_results.append(
                    {
                        "response_id": response["id"],
                        "player_id": response["player_id"],
                        "guess": guess,
                        "difference": abs(actual - guess),
                        "over": guess > actual,
                        "points": 0,
                    }
                )

            eligible = sorted(
                [
                    result for result in scored_results
                    if not result["over"]
                ],
                key=lambda item: item["difference"],
            )

            if not eligible:
                eligible = sorted(
                    scored_results,
                    key=lambda item: item["difference"],
                )

            points_by_place = [3, 2, 1]

            for place, result in enumerate(eligible[:3]):
                earned = points_by_place[place]

                if result["guess"] == round_data["price"]:
                    earned += 2

                result["points"] = earned
                player = get_player(
                    room["code"],
                    result["player_id"],
                )

                if player:
                    update_player(
                        player["id"],
                        {
                            "score": int(player["score"]) + earned,
                        },
                    )

                (
                    db.table("responses")
                    .update(
                        {
                            "graded": True,
                            "points_awarded": earned,
                            "updated_at": now_iso(),
                        }
                    )
                    .eq("id", result["response_id"])
                    .execute()
                )

            price_state["open"] = False
            price_state["revealed"] = True
            price_state["results"] = scored_results
            state["price"] = price_state

            update_room(
                room["code"],
                {"game_state": state},
            )
            st.rerun()

    with next_column:
        if st.button(
            "Next Item",
            use_container_width=True,
            disabled=not price_state.get("revealed"),
        ):
            price_state["round_index"] = (
                round_index + 1
            ) % len(PRICE_ROUNDS)

            price_state["open"] = False
            price_state["revealed"] = False
            price_state["results"] = []
            state["price"] = price_state

            update_room(
                room["code"],
                {"game_state": state},
            )
            st.rerun()

    if price_state.get("revealed"):
        players_by_id = {
            player["id"]: player
            for player in get_players(room["code"])
        }

        results = sorted(
            price_state.get("results", []),
            key=lambda item: (
                -int(item.get("points", 0)),
                float(item["difference"]),
            ),
        )

        st.subheader("Round results")

        for result in results:
            player = players_by_id.get(result["player_id"])
            name = player["name"] if player else "Guest"

            label = (
                f"+{result['points']} points"
                if result.get("points")
                else "Over" if result["over"] else "—"
            )

            st.markdown(
                f"""
                <div class="bb-score-row">
                    <span>
                        {html.escape(name)} ·
                        {money(float(result["guess"]))}
                    </span>
                    <span class="bb-score-value">{label}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )


def quiz_key(category_index: int, question_index: int) -> str:
    return f"{category_index}-{question_index}"


def host_quiz(room: dict[str, Any]) -> None:
    state = room["game_state"]
    quiz = state["quiz"]
    selected = quiz.get("selected")

    st.subheader("Baby Brain Board")

    if not selected:
        header_columns = st.columns(len(QUIZ_CATEGORIES))

        for column, category in zip(
            header_columns,
            QUIZ_CATEGORIES,
        ):
            with column:
                st.markdown(
                    f"""
                    <div class="bb-quiz-header">
                        {html.escape(category["name"])}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        for question_index in range(4):
            row_columns = st.columns(len(QUIZ_CATEGORIES))

            for category_index, column in enumerate(row_columns):
                question = QUIZ_CATEGORIES[
                    category_index
                ]["questions"][question_index]

                key = quiz_key(
                    category_index,
                    question_index,
                )

                used = key in quiz.get("used", [])

                with column:
                    if st.button(
                        str(question["value"]),
                        key=f"quiz_{key}",
                        use_container_width=True,
                        disabled=used,
                    ):
                        quiz["selected"] = {
                            "category_index": category_index,
                            "question_index": question_index,
                            "category": QUIZ_CATEGORIES[
                                category_index
                            ]["name"],
                            **question,
                        }
                        quiz["open"] = True
                        quiz["revealed"] = False
                        state["quiz"] = quiz

                        update_room(
                            room["code"],
                            {"game_state": state},
                        )
                        st.rerun()

        return

    round_key = (
        f"quiz-{selected['category_index']}-"
        f"{selected['question_index']}"
    )

    responses = get_responses(
        room["code"],
        "quiz",
        round_key,
    )

    answer_markup = ""

    if quiz.get("revealed"):
        answer_markup = (
            f'<div class="bb-answer">'
            f'Answer: {html.escape(selected["answer"])}'
            f'</div>'
        )

    st.markdown(
        f"""
        <div class="bb-question">
            <p>
                {html.escape(selected["category"])}
                · {selected["value"]} points
            </p>
            <div class="bb-question-text">
                {html.escape(selected["question"])}
            </div>
            <p>{len(responses)} response(s)</p>
            {answer_markup}
        </div>
        """,
        unsafe_allow_html=True,
    )

    reveal_column, board_column = st.columns(2)

    with reveal_column:
        if st.button(
            "Reveal Answer",
            type="primary",
            use_container_width=True,
            disabled=not quiz.get("open"),
        ):
            quiz["open"] = False
            quiz["revealed"] = True

            selected_key = quiz_key(
                selected["category_index"],
                selected["question_index"],
            )

            used = quiz.get("used", [])

            if selected_key not in used:
                used.append(selected_key)

            quiz["used"] = used
            state["quiz"] = quiz

            update_room(
                room["code"],
                {"game_state": state},
            )
            st.rerun()

    with board_column:
        if st.button(
            "Back to Board",
            use_container_width=True,
            disabled=not quiz.get("revealed"),
        ):
            quiz["selected"] = None
            quiz["open"] = False
            quiz["revealed"] = False
            state["quiz"] = quiz

            update_room(
                room["code"],
                {"game_state": state},
            )
            st.rerun()

    if quiz.get("revealed"):
        players_by_id = {
            player["id"]: player
            for player in get_players(room["code"])
        }

        st.subheader("Grade responses")

        for response in responses:
            player = players_by_id.get(response["player_id"])
            name = player["name"] if player else "Guest"
            answer = safe_text(
                response["answer"].get("text"),
                150,
            )

            response_column, correct_column, miss_column = st.columns(
                [5, 1.4, 1.2]
            )

            with response_column:
                st.write(f"**{name}:** {answer}")

            if response.get("graded"):
                with correct_column:
                    st.success(
                        f"{response.get('points_awarded', 0)} pts"
                    )
                continue

            with correct_column:
                if st.button(
                    "Correct",
                    key=f"correct_{response['id']}",
                    use_container_width=True,
                ):
                    points = int(selected["value"])

                    if player:
                        update_player(
                            player["id"],
                            {
                                "score": int(player["score"]) + points,
                            },
                        )

                    (
                        db.table("responses")
                        .update(
                            {
                                "graded": True,
                                "points_awarded": points,
                                "updated_at": now_iso(),
                            }
                        )
                        .eq("id", response["id"])
                        .execute()
                    )
                    st.rerun()

            with miss_column:
                if st.button(
                    "Miss",
                    key=f"miss_{response['id']}",
                    use_container_width=True,
                ):
                    (
                        db.table("responses")
                        .update(
                            {
                                "graded": True,
                                "points_awarded": 0,
                                "updated_at": now_iso(),
                            }
                        )
                        .eq("id", response["id"])
                        .execute()
                    )
                    st.rerun()


@st.fragment(run_every="2s")
def host_live_area(room_code: str) -> None:
    room = get_room(room_code)

    if not room:
        st.error("This room no longer exists.")
        return

    players = get_players(room_code)

    game_column, sidebar_column = st.columns(
        [3, 1],
        gap="large",
    )

    with game_column:
        if not room.get("active_game"):
            render_game_picker(room)
        elif room["active_game"] == "bingo":
            host_bingo(room)
        elif room["active_game"] == "price":
            host_price(room)
        elif room["active_game"] == "quiz":
            host_quiz(room)

    with sidebar_column:
        render_scoreboard(players)


def render_host(room_code: str) -> None:
    room = get_room(room_code)

    if not room:
        st.error("That host room could not be found.")
        if st.button("Return Home"):
            st.query_params.clear()
            st.rerun()
        return

    if not verify_host(room):
        st.error("The host key is missing or invalid.")
        st.write(
            "Open the original host link used when this room was created."
        )
        return

    top_left, top_right = st.columns([3, 1])

    with top_left:
        st.markdown(
            f"""
            <div class="bb-room-code">
                ROOM {html.escape(room_code)}
            </div>
            """,
            unsafe_allow_html=True,
        )

    with top_right:
        if room.get("active_game"):
            if st.button(
                "Game Menu",
                use_container_width=True,
            ):
                update_room(
                    room_code,
                    {
                        "active_game": None,
                        "status": "lobby",
                    },
                )
                st.rerun()

    st.write("")

    join_url = build_join_url(room_code)
    qr_image = create_qr(join_url)

    with st.expander(
        "Guest QR code and join link",
        expanded=not bool(room.get("active_game")),
    ):
        qr_column, instructions_column = st.columns(
            [1, 2],
            gap="large",
        )

        with qr_column:
            st.image(
                qr_image,
                caption=f"Room {room_code}",
                width=280,
            )

        with instructions_column:
            st.subheader("Scan to join")
            st.code(join_url, language=None)
            st.write(
                "Guests can also open the BB Games website and enter "
                f"room code **{room_code}**."
            )

    host_live_area(room_code)


# =========================================================
# Player screen
# =========================================================

def join_player_form(room: dict[str, Any]) -> None:
    st.markdown(
        f"""
        <div class="bb-card">
            <h2>Join room {html.escape(room["code"])}</h2>
            <p class="bb-muted">
                Enter the name that should appear on the scoreboard.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.write("")

    with st.form("player_join_form"):
        player_name = st.text_input(
            "Your name",
            max_chars=24,
            placeholder="Guest name",
        )

        submitted = st.form_submit_button(
            "Enter Room",
            type="primary",
            use_container_width=True,
        )

    if not submitted:
        return

    player_name = safe_text(player_name, 24)

    if not player_name:
        st.error("Please enter your name.")
        return

    players = get_players(room["code"])

    if len(players) >= MAX_PLAYERS:
        st.error("This room already has 20 guests.")
        return

    player_id = str(uuid.uuid4())

    db.table("players").insert(
        {
            "id": player_id,
            "room_code": room["code"],
            "name": player_name,
            "score": 0,
            "bingo_card": make_bingo_card(),
            "bingo_claimed": False,
            "created_at": now_iso(),
            "updated_at": now_iso(),
        }
    ).execute()

    st.query_params["pid"] = player_id
    st.rerun()


def player_bingo(
    room: dict[str, Any],
    player: dict[str, Any],
) -> None:
    state = room["game_state"]["bingo"]
    called = state.get("called", [])
    current = state.get("current")
    card = player.get("bingo_card") or make_bingo_card()

    st.subheader("Baby Bingo")
    st.info(f"Latest call: {current or 'Waiting for the host…'}")

    for row in range(5):
        columns = st.columns(5, gap="small")

        for column_index, column in enumerate(columns):
            index = row * 5 + column_index
            space = card[index]
            marked = bool(space.get("marked"))
            label = space["label"]

            with column:
                button_label = f"✓ {label}" if marked else label

                if st.button(
                    button_label,
                    key=f"bingo_{player['id']}_{index}",
                    use_container_width=True,
                    disabled=label == "FREE",
                ):
                    if label not in called:
                        st.warning(
                            "That item has not been called yet."
                        )
                    else:
                        card[index]["marked"] = not marked

                        update_player(
                            player["id"],
                            {"bingo_card": card},
                        )
                        st.rerun()

    if st.button(
        "I Have Bingo!",
        type="primary",
        use_container_width=True,
        disabled=bool(player.get("bingo_claimed")),
    ):
        if not valid_bingo(card):
            st.error(
                "No completed row, column, or diagonal was found."
            )
        else:
            update_player(
                player["id"],
                {
                    "score": int(player["score"]) + 10,
                    "bingo_claimed": True,
                },
            )

            state_data = room["game_state"]
            winner_ids = state.get("winner_ids", [])

            if player["id"] not in winner_ids:
                winner_ids.append(player["id"])

            state["winner_ids"] = winner_ids
            state_data["bingo"] = state

            update_room(
                room["code"],
                {"game_state": state_data},
            )

            st.balloons()
            st.success("Baby Bingo! You earned 10 points.")
            time.sleep(1)
            st.rerun()


def player_price(
    room: dict[str, Any],
    player: dict[str, Any],
) -> None:
    price_state = room["game_state"]["price"]
    round_index = int(price_state.get("round_index", 0))
    round_data = PRICE_ROUNDS[round_index]
    round_key = f"price-{round_index}"

    responses = get_responses(
        room["code"],
        "price",
        round_key,
    )

    own_response = next(
        (
            response
            for response in responses
            if response["player_id"] == player["id"]
        ),
        None,
    )

    st.subheader("Baby Price Challenge")

    st.markdown(
        f"""
        <div class="bb-price">
            <div class="bb-product-emoji">{round_data["emoji"]}</div>
            <h2>{html.escape(round_data["title"])}</h2>
            <p>{html.escape(round_data["description"])}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if price_state.get("revealed"):
        st.markdown(
            f"""
            <div class="bb-actual-price">
                {money(round_data["price"])}
            </div>
            """,
            unsafe_allow_html=True,
        )

        if own_response:
            points = int(own_response.get("points_awarded", 0))
            st.info(
                f"Your guess: "
                f"{money(float(own_response['answer']['amount']))}"
                + (
                    f" · You earned {points} points!"
                    if points
                    else ""
                )
            )
        else:
            st.info("You did not submit a guess this round.")

        return

    if not price_state.get("open"):
        st.info("Waiting for the host to open guessing.")
        return

    if own_response:
        st.success(
            "Your guess is locked in: "
            f"{money(float(own_response['answer']['amount']))}"
        )
        return

    with st.form(f"price_form_{round_index}"):
        guess = st.number_input(
            "Your price guess",
            min_value=0.00,
            max_value=10000.00,
            value=None,
            step=0.01,
            format="%.2f",
            placeholder="0.00",
        )

        submitted = st.form_submit_button(
            "Lock In Guess",
            type="primary",
            use_container_width=True,
        )

    if submitted:
        if guess is None:
            st.error("Enter a valid price.")
        else:
            save_response(
                room["code"],
                player["id"],
                "price",
                round_key,
                {"amount": round(float(guess), 2)},
            )
            st.success("Your guess is locked in.")
            st.rerun()


def player_quiz(
    room: dict[str, Any],
    player: dict[str, Any],
) -> None:
    quiz = room["game_state"]["quiz"]
    selected = quiz.get("selected")

    st.subheader("Baby Brain Board")

    if not selected:
        st.info("Waiting for the host to choose a question.")
        return

    round_key = (
        f"quiz-{selected['category_index']}-"
        f"{selected['question_index']}"
    )

    responses = get_responses(
        room["code"],
        "quiz",
        round_key,
    )

    own_response = next(
        (
            response
            for response in responses
            if response["player_id"] == player["id"]
        ),
        None,
    )

    answer_markup = ""

    if quiz.get("revealed"):
        answer_markup = (
            f'<div class="bb-answer">'
            f'Answer: {html.escape(selected["answer"])}'
            f'</div>'
        )

    st.markdown(
        f"""
        <div class="bb-question">
            <p>
                {html.escape(selected["category"])}
                · {selected["value"]} points
            </p>
            <div class="bb-question-text">
                {html.escape(selected["question"])}
            </div>
            {answer_markup}
        </div>
        """,
        unsafe_allow_html=True,
    )

    if quiz.get("revealed"):
        if own_response:
            points = int(own_response.get("points_awarded", 0))
            st.info(
                f'Your answer: {own_response["answer"]["text"]}'
                + (
                    f" · {points} points"
                    if own_response.get("graded")
                    else " · Waiting for grading"
                )
            )
        return

    if not quiz.get("open"):
        st.info("This question is closed.")
        return

    if own_response:
        st.success(
            f'Your answer is locked in: '
            f'{own_response["answer"]["text"]}'
        )
        return

    with st.form(f"quiz_form_{round_key}"):
        answer = st.text_input(
            "Your answer",
            max_chars=120,
            placeholder="Type your answer",
        )

        submitted = st.form_submit_button(
            "Submit Answer",
            type="primary",
            use_container_width=True,
        )

    if submitted:
        answer = safe_text(answer, 120)

        if not answer:
            st.error("Enter an answer first.")
        else:
            save_response(
                room["code"],
                player["id"],
                "quiz",
                round_key,
                {"text": answer},
            )
            st.success("Your answer is locked in.")
            st.rerun()


@st.fragment(run_every="2s")
def player_live_area(
    room_code: str,
    player_id: str,
) -> None:
    room = get_room(room_code)
    player = get_player(room_code, player_id)

    if not room:
        st.error("This room is no longer available.")
        return

    if not player:
        st.error("Your player record could not be found.")
        return

    top_left, top_right = st.columns([3, 1])

    with top_left:
        st.markdown(
            f"""
            <div class="bb-room-code">
                ROOM {html.escape(room_code)}
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.subheader(f"Hi, {player['name']}!")

    with top_right:
        st.metric("Score", int(player.get("score", 0)))

    active_game = room.get("active_game")

    if not active_game:
        st.info("Waiting for the host to choose a game.")
        return

    if active_game == "bingo":
        player_bingo(room, player)
    elif active_game == "price":
        player_price(room, player)
    elif active_game == "quiz":
        player_quiz(room, player)


def render_player(room_code: str) -> None:
    room = get_room(room_code)

    if not room:
        st.error("That room could not be found.")

        if st.button("Return Home"):
            st.query_params.clear()
            st.rerun()

        return

    player_id = safe_text(st.query_params.get("pid"), 100)

    if not player_id:
        join_player_form(room)
        return

    player = get_player(room_code, player_id)

    if not player:
        st.query_params.pop("pid", None)
        st.rerun()

    player_live_area(room_code, player_id)


# =========================================================
# App router
# =========================================================

render_brand()

role, code = current_role()

if role == "home":
    render_home()
elif role == "host" and code:
    render_host(code)
elif role == "player" and code:
    render_player(code)
