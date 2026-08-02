from __future__ import annotations

import html
import random
import secrets
import time
import uuid
from datetime import datetime, timezone
from io import BytesIO
from typing import Any

import qrcode
import streamlit as st
from postgrest.exceptions import APIError
from supabase import Client, create_client


# ============================================================
# App configuration
# ============================================================

st.set_page_config(
    page_title="BB Games",
    page_icon="🍉",
    layout="wide",
    initial_sidebar_state="collapsed",
)

MAX_PLAYERS = 20
ROOM_CODE_LENGTH = 5


# ============================================================
# Game content
# ============================================================

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
        "title": "Baby Bodysuits",
        "description": "A three-pack of short-sleeve cotton baby bodysuits.",
        "price": 14.99,
        "emoji": "👕",
    },
    {
        "title": "Baby Shampoo",
        "description": "One bottle of gentle baby shampoo.",
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
        "description": "One basic digital baby thermometer.",
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


# ============================================================
# Watermelon styling
# ============================================================

st.markdown(
    """
    <style>
        :root {
            --wm-red: #ef476f;
            --wm-red-dark: #c72c50;
            --wm-green: #2a9d62;
            --wm-green-dark: #176b43;
            --wm-green-light: #bce9c8;
            --wm-cream: #fffaf5;
            --wm-seed: #2a2024;
            --wm-muted: #74666b;
        }

        * {
            box-sizing: border-box;
        }

        .stApp {
            color: var(--wm-seed);
            background:
                radial-gradient(
                    circle at 10% 0%,
                    rgba(255, 128, 153, 0.28) 0,
                    transparent 28%
                ),
                radial-gradient(
                    circle at 96% 7%,
                    rgba(118, 200, 147, 0.32) 0,
                    transparent 27%
                ),
                linear-gradient(180deg, #fffdf8 0%, var(--wm-cream) 100%);
        }

        [data-testid="stHeader"] {
            background: transparent;
        }

        .block-container {
            max-width: 1180px;
            padding-top: 1.2rem;
            padding-bottom: 4rem;
        }

        h1,
        h2,
        h3 {
            color: var(--wm-green-dark);
        }

        .wm-brand {
            display: flex;
            align-items: center;
            gap: 0.85rem;
            margin-bottom: 1.3rem;
        }

        .wm-logo {
            display: grid;
            width: 3.5rem;
            height: 3.5rem;
            place-items: center;
            border: 4px solid var(--wm-green);
            border-radius: 50%;
            background: var(--wm-red);
            box-shadow: 0 12px 28px rgba(42, 157, 98, 0.22);
            font-size: 2rem;
        }

        .wm-brand-name {
            color: var(--wm-green-dark);
            font-size: 2.1rem;
            font-weight: 950;
            line-height: 1;
        }

        .wm-brand-copy {
            margin: 0.3rem 0 0;
            color: var(--wm-muted);
        }

        .wm-hero {
            padding: clamp(1.5rem, 6vw, 3.6rem);
            border: 5px solid var(--wm-green);
            border-radius: 2rem;
            color: white;
            background:
                radial-gradient(circle at 86% 20%, #2a2024 0 5px, transparent 6px),
                radial-gradient(circle at 92% 48%, #2a2024 0 5px, transparent 6px),
                radial-gradient(circle at 80% 72%, #2a2024 0 5px, transparent 6px),
                linear-gradient(135deg, var(--wm-red), #ff708d);
            box-shadow:
                0 0 0 9px var(--wm-green-light),
                0 18px 44px rgba(42, 32, 36, 0.16);
        }

        .wm-hero h1 {
            max-width: 720px;
            margin: 0 0 0.8rem;
            color: white;
            font-size: clamp(3rem, 8vw, 6rem);
            line-height: 0.92;
        }

        .wm-hero p {
            max-width: 700px;
            margin: 0;
            color: white;
            font-size: 1.1rem;
            line-height: 1.6;
        }

        .wm-card {
            padding: clamp(1.1rem, 4vw, 2rem);
            border: 2px solid rgba(42, 157, 98, 0.16);
            border-radius: 1.5rem;
            background: rgba(255, 255, 255, 0.96);
            box-shadow: 0 14px 34px rgba(42, 32, 36, 0.09);
        }

        .wm-room-code {
            display: inline-block;
            padding: 0.72rem 1.05rem;
            border: 3px solid var(--wm-green);
            border-radius: 999px;
            color: var(--wm-green-dark);
            background: var(--wm-green-light);
            font-size: 1.1rem;
            font-weight: 950;
            letter-spacing: 0.18rem;
        }

        .wm-game-card {
            min-height: 11rem;
            padding: 1.25rem;
            border: 3px solid #76c893;
            border-radius: 1.4rem;
            background: #fff1f4;
        }

        .wm-game-card.green {
            background: #edf9f1;
        }

        .wm-game-card.yellow {
            background: #fff8df;
        }

        .wm-game-icon {
            font-size: 2.6rem;
        }

        .wm-game-title {
            margin-top: 0.45rem;
            color: var(--wm-green-dark);
            font-size: 1.3rem;
            font-weight: 950;
        }

        .wm-muted {
            color: var(--wm-muted);
        }

        .wm-called {
            display: grid;
            min-height: 12rem;
            padding: 2rem;
            place-items: center;
            border: 6px solid var(--wm-green);
            border-radius: 1.7rem;
            color: white;
            background: var(--wm-red);
            text-align: center;
            font-size: clamp(2rem, 8vw, 4.8rem);
            font-weight: 950;
        }

        .wm-price,
        .wm-question {
            padding: 2rem;
            border: 5px solid var(--wm-green);
            border-radius: 1.6rem;
            background: #fff0f3;
            text-align: center;
        }

        .wm-product-emoji {
            font-size: 4.3rem;
        }

        .wm-actual-price {
            color: var(--wm-red-dark);
            font-size: clamp(3rem, 9vw, 6rem);
            font-weight: 950;
            text-align: center;
        }

        .wm-question-text {
            color: var(--wm-green-dark);
            font-size: clamp(1.6rem, 5vw, 3rem);
            font-weight: 950;
            line-height: 1.15;
        }

        .wm-answer {
            margin-top: 1rem;
            padding: 1rem;
            border-radius: 1rem;
            color: white;
            background: var(--wm-green);
            font-size: 1.2rem;
            font-weight: 900;
        }

        .wm-score-row {
            display: flex;
            justify-content: space-between;
            gap: 1rem;
            padding: 0.72rem 0.9rem;
            margin-bottom: 0.45rem;
            border-left: 5px solid var(--wm-green);
            border-radius: 0.85rem;
            background: #fff2f4;
        }

        .wm-score-value {
            color: var(--wm-red-dark);
            font-weight: 950;
        }

        .wm-pill {
            display: inline-block;
            padding: 0.42rem 0.7rem;
            margin: 0.22rem;
            border: 1px solid var(--wm-green);
            border-radius: 999px;
            color: var(--wm-green-dark);
            background: var(--wm-green-light);
            font-size: 0.84rem;
            font-weight: 850;
        }

        .wm-quiz-header {
            display: grid;
            min-height: 4.1rem;
            padding: 0.5rem;
            place-items: center;
            border-radius: 0.75rem;
            color: white;
            background: var(--wm-green-dark);
            text-align: center;
            font-weight: 950;
        }

        .stButton > button {
            min-height: 2.95rem;
            border: 0;
            border-radius: 0.9rem;
            color: white;
            background: var(--wm-green);
            font-weight: 850;
        }

        .stButton > button[kind="primary"] {
            color: white;
            background: var(--wm-red-dark);
        }

        .stTextInput input,
        .stNumberInput input {
            border: 2px solid var(--wm-green-light);
            border-radius: 0.85rem;
        }

        [data-testid="stMetric"] {
            padding: 0.7rem 1rem;
            border: 2px solid var(--wm-green);
            border-radius: 1rem;
            background: white;
        }

        @media (max-width: 640px) {
            .block-container {
                padding-left: 0.7rem;
                padding-right: 0.7rem;
            }

            .wm-card {
                border-radius: 1.1rem;
            }
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# Supabase
# ============================================================

@st.cache_resource
def get_database() -> Client:
    url = str(st.secrets.get("SUPABASE_URL", "")).strip()

    key = str(
        st.secrets.get(
            "SUPABASE_SECRET_KEY",
            st.secrets.get("SUPABASE_SERVICE_KEY", ""),
        )
    ).strip()

    if not url:
        raise RuntimeError("SUPABASE_URL is missing from Streamlit secrets.")

    if not url.startswith("https://") or ".supabase.co" not in url:
        raise RuntimeError("SUPABASE_URL is not a valid Supabase project URL.")

    if not key:
        raise RuntimeError(
            "SUPABASE_SECRET_KEY is missing from Streamlit secrets."
        )

    if key.startswith("sb_publishable_"):
        raise RuntimeError(
            "Use an sb_secret_ server key, not an sb_publishable_ key."
        )

    return create_client(url, key)


try:
    db = get_database()
except Exception as exc:
    st.error("BB Games could not connect to Supabase.")
    st.exception(exc)
    st.stop()


def display_api_error(exc: APIError) -> None:
    data = exc.args[0] if exc.args and isinstance(exc.args[0], dict) else {}

    code = str(data.get("code", "unknown"))
    message = str(data.get("message", "Supabase rejected the request."))
    details = str(data.get("details") or "")
    hint = str(data.get("hint") or "")

    st.error(f"Supabase error {code}: {message}")

    if code in {"42P01", "PGRST205"}:
        st.warning(
            "The BB Games tables were not found. Run the SQL setup script."
        )

    if code == "42501":
        st.warning(
            "The database blocked the request. Confirm the app uses an "
            "sb_secret_ key."
        )

    if details:
        st.caption(f"Details: {details}")

    if hint:
        st.caption(f"Hint: {hint}")


# ============================================================
# Database helpers
# ============================================================

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def safe_text(value: Any, maximum: int = 100) -> str:
    return (
        str(value or "")
        .replace("<", "")
        .replace(">", "")
        .strip()[:maximum]
    )


def money(value: float) -> str:
    return f"${value:,.2f}"


def make_room_code() -> str:
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"

    for _ in range(100):
        code = "".join(
            secrets.choice(alphabet)
            for _ in range(ROOM_CODE_LENGTH)
        )

        try:
            existing = (
                db.table("rooms")
                .select("code")
                .eq("code", code)
                .limit(1)
                .execute()
                .data
            )
        except APIError as exc:
            display_api_error(exc)
            st.stop()

        if not existing:
            return code

    raise RuntimeError("Unable to generate a unique room code.")


def make_bingo_card() -> list[dict[str, Any]]:
    words = random.sample(BINGO_WORDS, 24)
    words.insert(12, "FREE")

    return [
        {
            "label": word,
            "marked": word == "FREE",
        }
        for word in words
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
    try:
        response = (
            db.table("rooms")
            .select("*")
            .eq("code", room_code.upper())
            .limit(1)
            .execute()
        )
    except APIError as exc:
        display_api_error(exc)
        return None

    return response.data[0] if response.data else None


def get_players(room_code: str) -> list[dict[str, Any]]:
    try:
        response = (
            db.table("players")
            .select("*")
            .eq("room_code", room_code)
            .order("score", desc=True)
            .order("name")
            .execute()
        )
    except APIError as exc:
        display_api_error(exc)
        return []

    return response.data or []


def get_player(
    room_code: str,
    player_id: str,
) -> dict[str, Any] | None:
    try:
        response = (
            db.table("players")
            .select("*")
            .eq("room_code", room_code)
            .eq("id", player_id)
            .limit(1)
            .execute()
        )
    except APIError as exc:
        display_api_error(exc)
        return None

    return response.data[0] if response.data else None


def update_room(
    room_code: str,
    values: dict[str, Any],
) -> bool:
    values["updated_at"] = now_iso()

    try:
        (
            db.table("rooms")
            .update(values)
            .eq("code", room_code)
            .execute()
        )
        return True
    except APIError as exc:
        display_api_error(exc)
        return False


def update_player(
    player_id: str,
    values: dict[str, Any],
) -> bool:
    values["updated_at"] = now_iso()

    try:
        (
            db.table("players")
            .update(values)
            .eq("id", player_id)
            .execute()
        )
        return True
    except APIError as exc:
        display_api_error(exc)
        return False


def get_responses(
    room_code: str,
    game: str,
    round_key: str,
) -> list[dict[str, Any]]:
    try:
        response = (
            db.table("responses")
            .select("*")
            .eq("room_code", room_code)
            .eq("game", game)
            .eq("round_key", round_key)
            .order("created_at")
            .execute()
        )
    except APIError as exc:
        display_api_error(exc)
        return []

    return response.data or []


def save_response(
    room_code: str,
    player_id: str,
    game: str,
    round_key: str,
    answer: dict[str, Any],
) -> bool:
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

    try:
        (
            db.table("responses")
            .upsert(
                row,
                on_conflict="room_code,player_id,game,round_key",
            )
            .execute()
        )
        return True
    except APIError as exc:
        display_api_error(exc)
        return False


def clear_responses(room_code: str) -> None:
    try:
        (
            db.table("responses")
            .delete()
            .eq("room_code", room_code)
            .execute()
        )
    except APIError as exc:
        display_api_error(exc)


def reset_scores(room_code: str) -> None:
    for player in get_players(room_code):
        update_player(player["id"], {"score": 0})


# ============================================================
# QR code
# ============================================================

def build_join_url(room_code: str) -> str:
    app_url = str(
        st.secrets.get(
            "APP_URL",
            "https://your-app-name.streamlit.app",
        )
    ).strip().rstrip("/")

    return f"{app_url}/?room={room_code}"


def create_qr(join_url: str) -> BytesIO:
    """
    Return actual PNG bytes instead of a qrcode PilImage wrapper.

    This prevents Streamlit's BytesIO TypeError.
    """

    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=3,
    )

    qr.add_data(join_url)
    qr.make(fit=True)

    qr_image = qr.make_image(
        fill_color="#176b43",
        back_color="#ffffff",
    )

    image_buffer = BytesIO()
    qr_image.save(image_buffer, format="PNG")
    image_buffer.seek(0)

    return image_buffer


# ============================================================
# Shared components
# ============================================================

def render_brand() -> None:
    st.markdown(
        """
        <div class="wm-brand">
            <div class="wm-logo">🍉</div>
            <div>
                <div class="wm-brand-name">BB Games</div>
                <p class="wm-brand-copy">
                    Sweet baby-shower games for every guest
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
        st.markdown(
            f"""
            <div class="wm-score-row">
                <span>
                    {position}. {html.escape(str(player["name"]))}
                </span>
                <span class="wm-score-value">
                    {int(player.get("score", 0))}
                </span>
            </div>
            """,
            unsafe_allow_html=True,
        )


def valid_bingo(card: list[dict[str, Any]]) -> bool:
    if len(card) != 25:
        return False

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


def current_role() -> tuple[str, str | None]:
    host_code = safe_text(
        st.query_params.get("host"),
        ROOM_CODE_LENGTH,
    ).upper()

    room_code = safe_text(
        st.query_params.get("room"),
        ROOM_CODE_LENGTH,
    ).upper()

    if host_code:
        return "host", host_code

    if room_code:
        return "player", room_code

    return "home", None


def verify_host(room: dict[str, Any]) -> bool:
    supplied_key = safe_text(st.query_params.get("key"), 300)
    stored_key = str(room.get("host_key", ""))

    return bool(supplied_key) and secrets.compare_digest(
        supplied_key,
        stored_key,
    )


# ============================================================
# Home
# ============================================================

def create_host_room() -> None:
    code = make_room_code()
    host_key = secrets.token_urlsafe(32)

    room = {
        "code": code,
        "host_key": host_key,
        "active_game": None,
        "status": "lobby",
        "game_state": default_game_state(),
        "created_at": now_iso(),
        "updated_at": now_iso(),
    }

    try:
        db.table("rooms").insert(room).execute()
    except APIError as exc:
        display_api_error(exc)
        st.stop()

    st.query_params.clear()
    st.query_params["host"] = code
    st.query_params["key"] = host_key
    st.rerun()


def render_home() -> None:
    st.markdown(
        """
        <div class="wm-hero">
            <h1>Sweet games. Tiny guest of honor.</h1>
            <p>
                Host three live baby-shower games on a shared screen.
                Up to 20 guests can scan a QR code and play from
                their phones.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.write("")

    host_column, join_column = st.columns(2, gap="large")

    with host_column:
        st.markdown('<div class="wm-card">', unsafe_allow_html=True)
        st.subheader("Host BB Games")
        st.write(
            "Create a room, display the QR code, and control every round."
        )

        if st.button(
            "Create Host Room",
            type="primary",
            use_container_width=True,
        ):
            create_host_room()

        st.markdown("</div>", unsafe_allow_html=True)

    with join_column:
        st.markdown('<div class="wm-card">', unsafe_allow_html=True)
        st.subheader("Join a Game")

        with st.form("home_join_form"):
            room_code = st.text_input(
                "Room code",
                max_chars=ROOM_CODE_LENGTH,
                placeholder="ABC12",
            )

            submitted = st.form_submit_button(
                "Join Room",
                use_container_width=True,
            )

        if submitted:
            room_code = safe_text(
                room_code,
                ROOM_CODE_LENGTH,
            ).upper()

            if len(room_code) != ROOM_CODE_LENGTH:
                st.error("Enter the five-character room code.")
            elif not get_room(room_code):
                st.error("That room could not be found.")
            else:
                st.query_params.clear()
                st.query_params["room"] = room_code
                st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)


# ============================================================
# Host games
# ============================================================

def start_game(
    room: dict[str, Any],
    game: str,
) -> None:
    reset_scores(room["code"])
    clear_responses(room["code"])

    if game == "bingo":
        for player in get_players(room["code"]):
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
            "game_state": default_game_state(),
        },
    )


def render_game_picker(room: dict[str, Any]) -> None:
    st.subheader("Choose a baby-shower game")

    columns = st.columns(3, gap="medium")

    games = [
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
            "green",
        ),
        (
            "quiz",
            "🧠",
            "Baby Brain Board",
            "Choose questions from a baby-themed quiz board.",
            "yellow",
        ),
    ]

    for column, game_data in zip(columns, games):
        game, icon, title, description, css_class = game_data

        with column:
            st.markdown(
                f"""
                <div class="wm-game-card {css_class}">
                    <div class="wm-game-icon">{icon}</div>
                    <div class="wm-game-title">{title}</div>
                    <p class="wm-muted">{description}</p>
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
    game_state = room["game_state"]
    bingo = game_state["bingo"]

    called = bingo.get("called", [])
    current = bingo.get("current")

    st.subheader("Baby Bingo")

    st.markdown(
        f"""
        <div class="wm-called">
            {html.escape(current or "Ready to call?")}
        </div>
        """,
        unsafe_allow_html=True,
    )

    call_column, reset_column = st.columns(2)

    with call_column:
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
                game_state["bingo"] = bingo

                update_room(
                    room["code"],
                    {"game_state": game_state},
                )
                st.rerun()

    with reset_column:
        if st.button(
            "Reset Bingo",
            use_container_width=True,
        ):
            for player in get_players(room["code"]):
                update_player(
                    player["id"],
                    {
                        "bingo_card": make_bingo_card(),
                        "bingo_claimed": False,
                    },
                )

            game_state["bingo"] = {
                "called": [],
                "current": None,
                "winner_ids": [],
            }

            update_room(
                room["code"],
                {"game_state": game_state},
            )
            st.rerun()

    st.write(f"**Called items:** {len(called)}")

    if called:
        st.markdown(
            "".join(
                f'<span class="wm-pill">{html.escape(word)}</span>'
                for word in called
            ),
            unsafe_allow_html=True,
        )


def host_price(room: dict[str, Any]) -> None:
    game_state = room["game_state"]
    price_state = game_state["price"]

    round_index = int(price_state.get("round_index", 0))
    round_data = PRICE_ROUNDS[round_index]
    round_key = f"price-{round_index}"

    responses = get_responses(
        room["code"],
        "price",
        round_key,
    )

    revealed = bool(price_state.get("revealed"))

    content = (
        f'<div class="wm-actual-price">'
        f'{money(float(round_data["price"]))}'
        f"</div>"
        if revealed
        else f"<strong>{len(responses)} response(s)</strong>"
    )

    st.subheader(
        f"Baby Price Challenge · Round {round_index + 1}"
    )

    st.markdown(
        f"""
        <div class="wm-price">
            <div class="wm-product-emoji">{round_data["emoji"]}</div>
            <h2>{html.escape(round_data["title"])}</h2>
            <p>{html.escape(round_data["description"])}</p>
            {content}
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
                bool(price_state.get("open"))
                or revealed
            ),
        ):
            price_state["open"] = True
            price_state["revealed"] = False
            price_state["results"] = []
            game_state["price"] = price_state

            update_room(
                room["code"],
                {"game_state": game_state},
            )
            st.rerun()

    with reveal_column:
        if st.button(
            "Reveal Price",
            type="primary",
            use_container_width=True,
            disabled=not bool(price_state.get("open")),
        ):
            actual = float(round_data["price"])
            results: list[dict[str, Any]] = []

            for response in responses:
                guess = float(response["answer"]["amount"])

                results.append(
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
                    result for result in results
                    if not result["over"]
                ],
                key=lambda item: item["difference"],
            )

            if not eligible:
                eligible = sorted(
                    results,
                    key=lambda item: item["difference"],
                )

            points_by_place = [3, 2, 1]

            for place, result in enumerate(eligible[:3]):
                earned = points_by_place[place]

                if result["guess"] == actual:
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
                            "score": (
                                int(player.get("score", 0))
                                + earned
                            )
                        },
                    )

                try:
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
                except APIError as exc:
                    display_api_error(exc)

            price_state["open"] = False
            price_state["revealed"] = True
            price_state["results"] = results
            game_state["price"] = price_state

            update_room(
                room["code"],
                {"game_state": game_state},
            )
            st.rerun()

    with next_column:
        if st.button(
            "Next Item",
            use_container_width=True,
            disabled=not revealed,
        ):
            price_state["round_index"] = (
                round_index + 1
            ) % len(PRICE_ROUNDS)

            price_state["open"] = False
            price_state["revealed"] = False
            price_state["results"] = []
            game_state["price"] = price_state

            update_room(
                room["code"],
                {"game_state": game_state},
            )
            st.rerun()

    if revealed:
        players_by_id = {
            player["id"]: player
            for player in get_players(room["code"])
        }

        st.subheader("Round Results")

        for result in sorted(
            price_state.get("results", []),
            key=lambda item: (
                -int(item.get("points", 0)),
                float(item.get("difference", 0)),
            ),
        ):
            player = players_by_id.get(result["player_id"])
            name = player["name"] if player else "Guest"

            label = (
                f"+{result['points']} points"
                if result.get("points")
                else "Over"
                if result.get("over")
                else "—"
            )

            st.markdown(
                f"""
                <div class="wm-score-row">
                    <span>
                        {html.escape(name)} ·
                        {money(float(result["guess"]))}
                    </span>
                    <span class="wm-score-value">{label}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )


def quiz_key(
    category_index: int,
    question_index: int,
) -> str:
    return f"{category_index}-{question_index}"


def host_quiz(room: dict[str, Any]) -> None:
    game_state = room["game_state"]
    quiz_state = game_state["quiz"]
    selected = quiz_state.get("selected")

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
                    <div class="wm-quiz-header">
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

                used = key in quiz_state.get("used", [])

                with column:
                    if st.button(
                        str(question["value"]),
                        key=f"quiz_{key}",
                        use_container_width=True,
                        disabled=used,
                    ):
                        quiz_state["selected"] = {
                            "category_index": category_index,
                            "question_index": question_index,
                            "category": QUIZ_CATEGORIES[
                                category_index
                            ]["name"],
                            **question,
                        }

                        quiz_state["open"] = True
                        quiz_state["revealed"] = False
                        game_state["quiz"] = quiz_state

                        update_room(
                            room["code"],
                            {"game_state": game_state},
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

    if quiz_state.get("revealed"):
        answer_markup = (
            '<div class="wm-answer">'
            f'Answer: {html.escape(selected["answer"])}'
            "</div>"
        )

    st.markdown(
        f"""
        <div class="wm-question">
            <p>
                {html.escape(selected["category"])}
                · {selected["value"]} points
            </p>
            <div class="wm-question-text">
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
            disabled=not bool(quiz_state.get("open")),
        ):
            quiz_state["open"] = False
            quiz_state["revealed"] = True

            selected_key = quiz_key(
                selected["category_index"],
                selected["question_index"],
            )

            used = quiz_state.get("used", [])

            if selected_key not in used:
                used.append(selected_key)

            quiz_state["used"] = used
            game_state["quiz"] = quiz_state

            update_room(
                room["code"],
                {"game_state": game_state},
            )
            st.rerun()

    with board_column:
        if st.button(
            "Back to Board",
            use_container_width=True,
            disabled=not bool(quiz_state.get("revealed")),
        ):
            quiz_state["selected"] = None
            quiz_state["open"] = False
            quiz_state["revealed"] = False
            game_state["quiz"] = quiz_state

            update_room(
                room["code"],
                {"game_state": game_state},
            )
            st.rerun()

    if quiz_state.get("revealed"):
        players_by_id = {
            player["id"]: player
            for player in get_players(room["code"])
        }

        st.subheader("Grade Responses")

        for response in responses:
            player = players_by_id.get(response["player_id"])
            name = player["name"] if player else "Guest"
            answer = safe_text(
                response["answer"].get("text"),
                150,
            )

            answer_column, correct_column, miss_column = st.columns(
                [5, 1.4, 1.2]
            )

            with answer_column:
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
                                "score": (
                                    int(player.get("score", 0))
                                    + points
                                )
                            },
                        )

                    try:
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
                    except APIError as exc:
                        display_api_error(exc)

                    st.rerun()

            with miss_column:
                if st.button(
                    "Miss",
                    key=f"miss_{response['id']}",
                    use_container_width=True,
                ):
                    try:
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
                    except APIError as exc:
                        display_api_error(exc)

                    st.rerun()


@st.fragment(run_every="2s")
def host_live_area(room_code: str) -> None:
    room = get_room(room_code)

    if not room:
        st.error("This room no longer exists.")
        return

    game_column, scoreboard_column = st.columns(
        [3, 1],
        gap="large",
    )

    with game_column:
        active_game = room.get("active_game")

        if not active_game:
            render_game_picker(room)
        elif active_game == "bingo":
            host_bingo(room)
        elif active_game == "price":
            host_price(room)
        elif active_game == "quiz":
            host_quiz(room)

    with scoreboard_column:
        render_scoreboard(get_players(room_code))


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
        return

    title_column, menu_column = st.columns([3, 1])

    with title_column:
        st.markdown(
            f"""
            <div class="wm-room-code">
                ROOM {html.escape(room_code)}
            </div>
            """,
            unsafe_allow_html=True,
        )

    with menu_column:
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

    with st.expander(
        "Guest QR code and join link",
        expanded=not bool(room.get("active_game")),
    ):
        qr_column, instruction_column = st.columns(
            [1, 2],
            gap="large",
        )

        with qr_column:
            qr_png = create_qr(join_url)

            st.image(
                qr_png,
                caption=f"Room {room_code}",
                width=280,
            )

        with instruction_column:
            st.subheader("Scan to Join")
            st.code(join_url, language=None)
            st.write(
                "Guests can also visit BB Games and enter room code "
                f"**{room_code}**."
            )

    host_live_area(room_code)


# ============================================================
# Player
# ============================================================

def join_player_form(room: dict[str, Any]) -> None:
    st.markdown(
        f"""
        <div class="wm-card">
            <h2>Join room {html.escape(room["code"])}</h2>
            <p class="wm-muted">
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

    if len(get_players(room["code"])) >= MAX_PLAYERS:
        st.error("This room already has 20 guests.")
        return

    player_id = str(uuid.uuid4())

    try:
        (
            db.table("players")
            .insert(
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
            )
            .execute()
        )
    except APIError as exc:
        display_api_error(exc)
        return

    st.query_params["pid"] = player_id
    st.rerun()


def player_bingo(
    room: dict[str, Any],
    player: dict[str, Any],
) -> None:
    bingo_state = room["game_state"]["bingo"]
    called = bingo_state.get("called", [])
    current = bingo_state.get("current")
    card = player.get("bingo_card") or make_bingo_card()

    st.subheader("Baby Bingo")
    st.info(
        f"Latest call: {current or 'Waiting for the host…'}"
    )

    for row in range(5):
        columns = st.columns(5, gap="small")

        for column_index, column in enumerate(columns):
            index = row * 5 + column_index
            space = card[index]
            label = str(space["label"])
            marked = bool(space.get("marked"))

            with column:
                if st.button(
                    f"✓ {label}" if marked else label,
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
                    "score": int(player.get("score", 0)) + 10,
                    "bingo_claimed": True,
                },
            )

            game_state = room["game_state"]
            winners = bingo_state.get("winner_ids", [])

            if player["id"] not in winners:
                winners.append(player["id"])

            bingo_state["winner_ids"] = winners
            game_state["bingo"] = bingo_state

            update_room(
                room["code"],
                {"game_state": game_state},
            )

            st.balloons()
            st.success("Baby Bingo! You earned 10 points.")
            time.sleep(0.8)
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
        <div class="wm-price">
            <div class="wm-product-emoji">{round_data["emoji"]}</div>
            <h2>{html.escape(round_data["title"])}</h2>
            <p>{html.escape(round_data["description"])}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if price_state.get("revealed"):
        st.markdown(
            f"""
            <div class="wm-actual-price">
                {money(float(round_data["price"]))}
            </div>
            """,
            unsafe_allow_html=True,
        )

        if own_response:
            points = int(
                own_response.get("points_awarded", 0)
            )

            message = (
                "Your guess: "
                f"{money(float(own_response['answer']['amount']))}"
            )

            if points:
                message += f" · You earned {points} points!"

            st.info(message)
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
        elif save_response(
            room["code"],
            player["id"],
            "price",
            round_key,
            {"amount": round(float(guess), 2)},
        ):
            st.success("Your guess is locked in.")
            st.rerun()


def player_quiz(
    room: dict[str, Any],
    player: dict[str, Any],
) -> None:
    quiz_state = room["game_state"]["quiz"]
    selected = quiz_state.get("selected")

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

    if quiz_state.get("revealed"):
        answer_markup = (
            '<div class="wm-answer">'
            f'Answer: {html.escape(selected["answer"])}'
            "</div>"
        )

    st.markdown(
        f"""
        <div class="wm-question">
            <p>
                {html.escape(selected["category"])}
                · {selected["value"]} points
            </p>
            <div class="wm-question-text">
                {html.escape(selected["question"])}
            </div>
            {answer_markup}
        </div>
        """,
        unsafe_allow_html=True,
    )

    if quiz_state.get("revealed"):
        if own_response:
            points = int(
                own_response.get("points_awarded", 0)
            )

            message = (
                "Your answer: "
                f'{own_response["answer"]["text"]}'
            )

            if own_response.get("graded"):
                message += f" · {points} points"
            else:
                message += " · Waiting for grading"

            st.info(message)

        return

    if not quiz_state.get("open"):
        st.info("This question is closed.")
        return

    if own_response:
        st.success(
            "Your answer is locked in: "
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
        elif save_response(
            room["code"],
            player["id"],
            "quiz",
            round_key,
            {"text": answer},
        ):
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

    greeting_column, score_column = st.columns([3, 1])

    with greeting_column:
        st.markdown(
            f"""
            <div class="wm-room-code">
                ROOM {html.escape(room_code)}
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.subheader(f"Hi, {player['name']}!")

    with score_column:
        st.metric(
            "Score",
            int(player.get("score", 0)),
        )

    active_game = room.get("active_game")

    if not active_game:
        st.info("Waiting for the host to choose a game.")
    elif active_game == "bingo":
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

    player_id = safe_text(
        st.query_params.get("pid"),
        100,
    )

    if not player_id:
        join_player_form(room)
        return

    player = get_player(room_code, player_id)

    if not player:
        try:
            del st.query_params["pid"]
        except KeyError:
            pass

        st.rerun()

    player_live_area(room_code, player_id)


# ============================================================
# Router
# ============================================================

render_brand()

role, room_code = current_role()

if role == "home":
    render_home()

elif role == "host" and room_code:
    render_host(room_code)

elif role == "player" and room_code:
    render_player(room_code)
