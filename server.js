"use strict";

const express = require("express");
const http = require("http");
const { Server } = require("socket.io");
const QRCode = require("qrcode");

const app = express();
const server = http.createServer(app);
const io = new Server(server);

const PORT = Number(process.env.PORT || 3000);
const BASE_URL = process.env.BASE_URL ||
  process.env.RENDER_EXTERNAL_URL ||
  `http://localhost:${PORT}`;
const MAX_PLAYERS = 20;

const rooms = new Map();

const bingoWords = [
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
  "Stuffed animal"
];

const priceRounds = [
  {
    title: "Newborn Diapers",
    description: "One package of approximately 30 newborn-size diapers",
    price: 10.99
  },
  {
    title: "Baby Wipes",
    description: "A three-pack containing approximately 168 unscented wipes",
    price: 8.49
  },
  {
    title: "Three Baby Bodysuits",
    description: "A three-pack of short-sleeve cotton bodysuits",
    price: 14.99
  },
  {
    title: "Baby Shampoo",
    description: "One 13.6-fluid-ounce bottle of gentle baby shampoo",
    price: 6.49
  },
  {
    title: "Pacifier Two-Pack",
    description: "Two silicone pacifiers for newborn babies",
    price: 7.99
  },
  {
    title: "Digital Thermometer",
    description: "A basic digital baby thermometer",
    price: 16.99
  },
  {
    title: "Swaddle Blanket",
    description: "One soft muslin swaddle blanket",
    price: 19.99
  },
  {
    title: "Nursery Bundle",
    description: "A baby monitor, diaper bag, and soft infant carrier",
    price: 164.97
  }
];

const quizCategories = [
  {
    name: "Baby Basics",
    questions: [
      {
        value: 100,
        question: "What item is commonly fastened around a baby during feeding?",
        answer: "A bib"
      },
      {
        value: 200,
        question: "What furniture is specifically designed for a baby to sleep in?",
        answer: "A crib"
      },
      {
        value: 300,
        question: "What soft cloth is placed over a shoulder when burping a baby?",
        answer: "A burp cloth"
      },
      {
        value: 400,
        question: "What is the common name for wrapping a baby snugly in a blanket?",
        answer: "Swaddling"
      }
    ]
  },
  {
    name: "Tiny Animals",
    questions: [
      {
        value: 100,
        question: "What is a baby dog called?",
        answer: "A puppy"
      },
      {
        value: 200,
        question: "What is a baby cat called?",
        answer: "A kitten"
      },
      {
        value: 300,
        question: "What is a baby kangaroo called?",
        answer: "A joey"
      },
      {
        value: 400,
        question: "What is a baby swan called?",
        answer: "A cygnet"
      }
    ]
  },
  {
    name: "Story Time",
    questions: [
      {
        value: 100,
        question: "Which nursery-rhyme character sat on a wall?",
        answer: "Humpty Dumpty"
      },
      {
        value: 200,
        question: "Which little star is described as being wondered about?",
        answer: "Twinkle, Twinkle, Little Star"
      },
      {
        value: 300,
        question: "Which nursery-rhyme sheep was asked whether it had wool?",
        answer: "Baa, Baa, Black Sheep"
      },
      {
        value: 400,
        question: "Which character lost her sheep and did not know where to find them?",
        answer: "Little Bo-Peep"
      }
    ]
  },
  {
    name: "Parent Prep",
    questions: [
      {
        value: 100,
        question: "What portable bag usually holds diapers, wipes, and spare clothing?",
        answer: "A diaper bag"
      },
      {
        value: 200,
        question: "What padded surface is used during diaper changes?",
        answer: "A changing pad"
      },
      {
        value: 300,
        question: "What device lets caregivers hear or see a baby from another room?",
        answer: "A baby monitor"
      },
      {
        value: 400,
        question: "What seat is used to secure an infant while traveling in a vehicle?",
        answer: "An infant car seat"
      }
    ]
  }
];

function makeRoomCode() {
  const alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789";

  while (true) {
    let code = "";

    for (let i = 0; i < 5; i += 1) {
      code += alphabet[Math.floor(Math.random() * alphabet.length)];
    }

    if (!rooms.has(code)) {
      return code;
    }
  }
}

function shuffled(items) {
  const copy = [...items];

  for (let i = copy.length - 1; i > 0; i -= 1) {
    const j = Math.floor(Math.random() * (i + 1));
    [copy[i], copy[j]] = [copy[j], copy[i]];
  }

  return copy;
}

function makeBingoCard() {
  const words = shuffled(bingoWords).slice(0, 24);
  words.splice(12, 0, "FREE");

  return words.map((label, index) => ({
    index,
    label,
    marked: label === "FREE"
  }));
}

function cleanName(value) {
  return String(value || "")
    .replace(/[<>]/g, "")
    .trim()
    .slice(0, 24);
}

function cleanAnswer(value) {
  return String(value || "")
    .replace(/[<>]/g, "")
    .trim()
    .slice(0, 120);
}

function createRoom(hostSocketId) {
  const code = makeRoomCode();

  const room = {
    code,
    hostSocketId,
    createdAt: Date.now(),
    game: null,
    status: "lobby",
    players: new Map(),

    bingo: {
      called: [],
      current: null
    },

    price: {
      roundIndex: 0,
      open: false,
      answers: new Map(),
      revealed: false,
      results: []
    },

    quiz: {
      selected: null,
      open: false,
      answers: new Map(),
      used: new Set(),
      revealed: false
    }
  };

  rooms.set(code, room);
  return room;
}

function playerList(room) {
  return [...room.players.values()]
    .map(({ id, name, score, connected }) => ({
      id,
      name,
      score,
      connected
    }))
    .sort((a, b) => b.score - a.score || a.name.localeCompare(b.name));
}

function publicState(room) {
  return {
    code: room.code,
    game: room.game,
    status: room.status,
    players: playerList(room),

    bingo: {
      called: room.bingo.called,
      current: room.bingo.current
    },

    price: {
      roundIndex: room.price.roundIndex,
      round: priceRounds[room.price.roundIndex] || null,
      open: room.price.open,
      revealed: room.price.revealed,
      results: room.price.results,
      responseCount: room.price.answers.size
    },

    quiz: {
      categories: quizCategories,
      selected: room.quiz.selected,
      open: room.quiz.open,
      revealed: room.quiz.revealed,
      used: [...room.quiz.used],
      responseCount: room.quiz.answers.size
    }
  };
}

function emitState(room) {
  io.to(room.code).emit("room-state", publicState(room));
}

function getRoom(code) {
  return rooms.get(String(code || "").toUpperCase());
}

function getHostRoom(socket) {
  const code = socket.data.roomCode;
  const room = getRoom(code);

  if (!room || room.hostSocketId !== socket.id) {
    return null;
  }

  return room;
}

function getPlayer(room, socket) {
  const playerId = socket.data.playerId;
  return playerId ? room.players.get(playerId) : null;
}

function hasBingo(card) {
  const marked = card.map((space) => space.marked);

  const lines = [];

  for (let row = 0; row < 5; row += 1) {
    lines.push([0, 1, 2, 3, 4].map((column) => row * 5 + column));
  }

  for (let column = 0; column < 5; column += 1) {
    lines.push([0, 1, 2, 3, 4].map((row) => row * 5 + column));
  }

  lines.push([0, 6, 12, 18, 24]);
  lines.push([4, 8, 12, 16, 20]);

  return lines.some((line) => line.every((index) => marked[index]));
}

function resetScores(room) {
  for (const player of room.players.values()) {
    player.score = 0;
  }
}

app.get("/", (req, res) => {
  res.type("html").send(pageHtml);
});

app.get("/health", (req, res) => {
  res.json({ ok: true });
});

io.on("connection", (socket) => {
  socket.on("create-room", async (callback) => {
    try {
      const room = createRoom(socket.id);
      socket.data.roomCode = room.code;
      socket.data.role = "host";
      socket.join(room.code);

      const joinUrl = `${BASE_URL}/?room=${room.code}`;
      const qrDataUrl = await QRCode.toDataURL(joinUrl, {
        width: 360,
        margin: 2,
        color: {
          dark: "#4b315f",
          light: "#ffffff"
        }
      });

      callback({
        ok: true,
        room: publicState(room),
        joinUrl,
        qrDataUrl
      });
    } catch (error) {
      console.error(error);
      callback({ ok: false, message: "Unable to create the room." });
    }
  });

  socket.on("join-room", ({ roomCode, name, playerId }, callback) => {
    const room = getRoom(roomCode);
    const safeName = cleanName(name);

    if (!room) {
      callback({ ok: false, message: "That room could not be found." });
      return;
    }

    if (!safeName) {
      callback({ ok: false, message: "Please enter your name." });
      return;
    }

    let player = playerId ? room.players.get(playerId) : null;

    if (!player && room.players.size >= MAX_PLAYERS) {
      callback({ ok: false, message: "This room already has 20 guests." });
      return;
    }

    if (!player) {
      const id = crypto.randomUUID();

      player = {
        id,
        socketId: socket.id,
        name: safeName,
        score: 0,
        connected: true,
        bingoCard: makeBingoCard(),
        bingoClaimed: false
      };

      room.players.set(id, player);
    } else {
      player.socketId = socket.id;
      player.name = safeName;
      player.connected = true;
    }

    socket.data.roomCode = room.code;
    socket.data.playerId = player.id;
    socket.data.role = "player";
    socket.join(room.code);

    callback({
      ok: true,
      playerId: player.id,
      player: {
        id: player.id,
        name: player.name,
        score: player.score,
        bingoCard: player.bingoCard
      },
      room: publicState(room)
    });

    emitState(room);
  });

  socket.on("select-game", ({ game }) => {
    const room = getHostRoom(socket);

    if (!room || !["bingo", "price", "quiz"].includes(game)) {
      return;
    }

    room.game = game;
    room.status = "playing";
    resetScores(room);

    room.bingo.called = [];
    room.bingo.current = null;

    for (const player of room.players.values()) {
      player.bingoCard = makeBingoCard();
      player.bingoClaimed = false;

      io.to(player.socketId).emit("bingo-card", player.bingoCard);
    }

    room.price.roundIndex = 0;
    room.price.open = false;
    room.price.revealed = false;
    room.price.answers.clear();
    room.price.results = [];

    room.quiz.selected = null;
    room.quiz.open = false;
    room.quiz.revealed = false;
    room.quiz.answers.clear();
    room.quiz.used.clear();

    emitState(room);
  });

  socket.on("call-bingo", () => {
    const room = getHostRoom(socket);

    if (!room || room.game !== "bingo") {
      return;
    }

    const available = bingoWords.filter(
      (word) => !room.bingo.called.includes(word)
    );

    if (!available.length) {
      return;
    }

    room.bingo.current =
      available[Math.floor(Math.random() * available.length)];

    room.bingo.called.push(room.bingo.current);
    emitState(room);
  });

  socket.on("toggle-bingo-space", ({ index }, callback) => {
    const room = getRoom(socket.data.roomCode);
    const player = room && getPlayer(room, socket);

    if (!room || !player || room.game !== "bingo") {
      return;
    }

    const space = player.bingoCard[Number(index)];

    if (!space || space.label === "FREE") {
      return;
    }

    if (!room.bingo.called.includes(space.label)) {
      callback?.({
        ok: false,
        message: "That item has not been called yet."
      });
      return;
    }

    space.marked = !space.marked;

    callback?.({
      ok: true,
      card: player.bingoCard,
      hasBingo: hasBingo(player.bingoCard)
    });
  });

  socket.on("claim-bingo", (callback) => {
    const room = getRoom(socket.data.roomCode);
    const player = room && getPlayer(room, socket);

    if (!room || !player || player.bingoClaimed) {
      return;
    }

    if (!hasBingo(player.bingoCard)) {
      callback?.({
        ok: false,
        message: "No completed row, column, or diagonal was found."
      });
      return;
    }

    player.bingoClaimed = true;
    player.score += 10;

    io.to(room.code).emit("celebration", {
      title: `${player.name} has Baby Bingo!`,
      message: "They completed a valid line and earned 10 points."
    });

    callback?.({ ok: true });
    emitState(room);
  });

  socket.on("open-price-round", () => {
    const room = getHostRoom(socket);

    if (!room || room.game !== "price") {
      return;
    }

    room.price.open = true;
    room.price.revealed = false;
    room.price.answers.clear();
    room.price.results = [];
    emitState(room);
  });

  socket.on("submit-price", ({ amount }, callback) => {
    const room = getRoom(socket.data.roomCode);
    const player = room && getPlayer(room, socket);
    const numericAmount = Number(amount);

    if (!room || !player || !room.price.open) {
      callback?.({ ok: false, message: "This round is not accepting guesses." });
      return;
    }

    if (!Number.isFinite(numericAmount) || numericAmount < 0) {
      callback?.({ ok: false, message: "Enter a valid price." });
      return;
    }

    room.price.answers.set(player.id, Math.round(numericAmount * 100) / 100);
    callback?.({ ok: true });
    emitState(room);
  });

  socket.on("reveal-price", () => {
    const room = getHostRoom(socket);
    const round = room && priceRounds[room.price.roundIndex];

    if (!room || !round) {
      return;
    }

    const entries = [...room.price.answers.entries()].map(
      ([playerId, guess]) => {
        const player = room.players.get(playerId);
        const over = guess > round.price;

        return {
          playerId,
          name: player?.name || "Guest",
          guess,
          difference: Math.abs(round.price - guess),
          over
        };
      }
    );

    let eligible = entries
      .filter((entry) => !entry.over)
      .sort((a, b) => a.difference - b.difference);

    if (!eligible.length) {
      eligible = entries.sort((a, b) => a.difference - b.difference);
    }

    const points = [3, 2, 1];

    eligible.slice(0, 3).forEach((entry, index) => {
      const player = room.players.get(entry.playerId);
      const exactBonus = entry.guess === round.price ? 2 : 0;
      const earned = points[index] + exactBonus;

      if (player) {
        player.score += earned;
      }

      entry.points = earned;
    });

    room.price.results = entries.sort(
      (a, b) =>
        (b.points || 0) - (a.points || 0) ||
        a.difference - b.difference
    );

    room.price.open = false;
    room.price.revealed = true;
    emitState(room);
  });

  socket.on("next-price-round", () => {
    const room = getHostRoom(socket);

    if (!room) {
      return;
    }

    room.price.roundIndex =
      (room.price.roundIndex + 1) % priceRounds.length;

    room.price.open = false;
    room.price.revealed = false;
    room.price.answers.clear();
    room.price.results = [];

    emitState(room);
  });

  socket.on("select-quiz-question", ({ categoryIndex, questionIndex }) => {
    const room = getHostRoom(socket);

    if (!room || room.game !== "quiz") {
      return;
    }

    const key = `${categoryIndex}-${questionIndex}`;
    const category = quizCategories[categoryIndex];
    const question = category?.questions[questionIndex];

    if (!question || room.quiz.used.has(key)) {
      return;
    }

    room.quiz.selected = {
      categoryIndex,
      questionIndex,
      category: category.name,
      ...question
    };

    room.quiz.open = true;
    room.quiz.revealed = false;
    room.quiz.answers.clear();
    emitState(room);
  });

  socket.on("submit-quiz", ({ answer }, callback) => {
    const room = getRoom(socket.data.roomCode);
    const player = room && getPlayer(room, socket);

    if (!room || !player || !room.quiz.open) {
      callback?.({ ok: false, message: "This question is closed." });
      return;
    }

    const safeAnswer = cleanAnswer(answer);

    if (!safeAnswer) {
      callback?.({ ok: false, message: "Enter an answer first." });
      return;
    }

    room.quiz.answers.set(player.id, safeAnswer);
    callback?.({ ok: true });
    emitState(room);
  });

  socket.on("reveal-quiz", () => {
    const room = getHostRoom(socket);

    if (!room || !room.quiz.selected) {
      return;
    }

    room.quiz.open = false;
    room.quiz.revealed = true;

    const key =
      `${room.quiz.selected.categoryIndex}-` +
      `${room.quiz.selected.questionIndex}`;

    room.quiz.used.add(key);

    const answers = [...room.quiz.answers.entries()].map(
      ([playerId, answer]) => ({
        playerId,
        name: room.players.get(playerId)?.name || "Guest",
        answer
      })
    );

    io.to(room.hostSocketId).emit("quiz-submissions", answers);
    emitState(room);
  });

  socket.on("score-quiz-answer", ({ playerId, correct }) => {
    const room = getHostRoom(socket);
    const player = room?.players.get(playerId);

    if (!room || !player || !room.quiz.selected) {
      return;
    }

    const value = room.quiz.selected.value;
    player.score += correct ? value : 0;
    emitState(room);
  });

  socket.on("close-quiz-question", () => {
    const room = getHostRoom(socket);

    if (!room) {
      return;
    }

    room.quiz.selected = null;
    room.quiz.open = false;
    room.quiz.revealed = false;
    room.quiz.answers.clear();
    emitState(room);
  });

  socket.on("disconnect", () => {
    const room = getRoom(socket.data.roomCode);

    if (!room) {
      return;
    }

    if (socket.data.role === "host") {
      io.to(room.code).emit("host-disconnected");
      setTimeout(() => {
        const latestRoom = rooms.get(room.code);

        if (latestRoom && latestRoom.hostSocketId === socket.id) {
          rooms.delete(room.code);
        }
      }, 60_000);

      return;
    }

    const player = getPlayer(room, socket);

    if (player) {
      player.connected = false;
      emitState(room);
    }
  });
});

const pageHtml = String.raw`
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta
    name="viewport"
    content="width=device-width, initial-scale=1, viewport-fit=cover"
  >
  <title>Tiny Party Games</title>

  <style>
    :root {
      --cream: #fffaf2;
      --pink: #ef8fa9;
      --pink-dark: #c95478;
      --purple: #654274;
      --purple-dark: #41294e;
      --mint: #b8ead9;
      --yellow: #ffd978;
      --blue: #a9d8ef;
      --white: #ffffff;
      --ink: #33283a;
      --muted: #74697b;
      --danger: #c43d55;
      --shadow: 0 14px 38px rgba(65, 41, 78, 0.13);
    }

    * {
      box-sizing: border-box;
    }

    body {
      margin: 0;
      min-height: 100vh;
      color: var(--ink);
      font-family:
        Inter, ui-rounded, "SF Pro Rounded", system-ui, -apple-system,
        BlinkMacSystemFont, "Segoe UI", sans-serif;
      background:
        radial-gradient(circle at 10% 0%, #ffe1e9 0, transparent 28%),
        radial-gradient(circle at 95% 15%, #d8f4eb 0, transparent 25%),
        var(--cream);
    }

    button,
    input {
      font: inherit;
    }

    button {
      cursor: pointer;
    }

    .shell {
      width: min(1180px, calc(100% - 28px));
      margin: 0 auto;
      padding: 26px 0 60px;
    }

    .brand {
      display: flex;
      align-items: center;
      gap: 12px;
      margin-bottom: 24px;
    }

    .brand-mark {
      display: grid;
      width: 52px;
      height: 52px;
      place-items: center;
      border-radius: 18px;
      background: var(--purple);
      box-shadow: var(--shadow);
      font-size: 27px;
    }

    .brand h1 {
      margin: 0;
      color: var(--purple-dark);
      font-size: clamp(25px, 4vw, 38px);
    }

    .brand p {
      margin: 2px 0 0;
      color: var(--muted);
    }

    .card {
      padding: clamp(18px, 4vw, 30px);
      border: 1px solid rgba(101, 66, 116, 0.1);
      border-radius: 26px;
      background: rgba(255, 255, 255, 0.94);
      box-shadow: var(--shadow);
    }

    .hero {
      display: grid;
      grid-template-columns: 1.2fr 0.8fr;
      gap: 24px;
      align-items: center;
    }

    h2,
    h3 {
      margin-top: 0;
      color: var(--purple-dark);
    }

    .hero h2 {
      margin-bottom: 12px;
      font-size: clamp(35px, 7vw, 70px);
      line-height: 0.98;
    }

    .hero p {
      max-width: 650px;
      color: var(--muted);
      font-size: 18px;
      line-height: 1.6;
    }

    .button-row {
      display: flex;
      flex-wrap: wrap;
      gap: 12px;
      margin-top: 22px;
    }

    .button {
      min-height: 48px;
      padding: 12px 20px;
      border: 0;
      border-radius: 15px;
      color: white;
      background: var(--purple);
      font-weight: 800;
      transition: transform 0.15s, opacity 0.15s;
    }

    .button:hover {
      transform: translateY(-1px);
    }

    .button:disabled {
      cursor: not-allowed;
      opacity: 0.45;
      transform: none;
    }

    .button.pink {
      background: var(--pink-dark);
    }

    .button.mint {
      color: var(--purple-dark);
      background: var(--mint);
    }

    .button.yellow {
      color: var(--purple-dark);
      background: var(--yellow);
    }

    .button.ghost {
      color: var(--purple);
      border: 2px solid #eadfee;
      background: white;
    }

    .baby-art {
      display: grid;
      min-height: 300px;
      place-items: center;
      border-radius: 28px;
      background:
        linear-gradient(145deg, rgba(239,143,169,.27), rgba(184,234,217,.45));
      font-size: clamp(100px, 18vw, 190px);
    }

    .join-box {
      display: grid;
      grid-template-columns: 1fr auto;
      gap: 10px;
      margin-top: 20px;
    }

    input {
      width: 100%;
      min-height: 50px;
      padding: 12px 15px;
      color: var(--ink);
      border: 2px solid #eadfee;
      border-radius: 14px;
      outline: none;
      background: white;
    }

    input:focus {
      border-color: var(--pink);
      box-shadow: 0 0 0 4px rgba(239, 143, 169, 0.16);
    }

    .hidden {
      display: none !important;
    }

    .host-grid {
      display: grid;
      grid-template-columns: minmax(0, 1fr) 310px;
      gap: 20px;
    }

    .topline {
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      justify-content: space-between;
      gap: 14px;
      margin-bottom: 18px;
    }

    .room-code {
      display: inline-flex;
      align-items: center;
      gap: 9px;
      padding: 9px 14px;
      border-radius: 999px;
      color: var(--purple-dark);
      background: #f3eaf6;
      font-weight: 900;
      letter-spacing: 2px;
    }

    .qr {
      width: min(100%, 260px);
      padding: 10px;
      border-radius: 20px;
      background: white;
    }

    .join-url {
      overflow-wrap: anywhere;
      color: var(--muted);
      font-size: 13px;
    }

    .game-picker {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 14px;
    }

    .game-tile {
      min-height: 190px;
      padding: 20px;
      border: 0;
      border-radius: 22px;
      text-align: left;
      color: var(--purple-dark);
      background: #fff3f6;
      box-shadow: inset 0 0 0 2px transparent;
    }

    .game-tile:nth-child(2) {
      background: #eefaf6;
    }

    .game-tile:nth-child(3) {
      background: #fff8df;
    }

    .game-tile:hover {
      box-shadow: inset 0 0 0 2px var(--purple);
    }

    .game-icon {
      display: block;
      margin-bottom: 10px;
      font-size: 42px;
    }

    .game-title {
      display: block;
      font-size: 22px;
      font-weight: 900;
    }

    .game-copy {
      display: block;
      margin-top: 7px;
      color: var(--muted);
      line-height: 1.45;
    }

    .players {
      display: grid;
      gap: 8px;
    }

    .player-row {
      display: grid;
      grid-template-columns: 1fr auto;
      gap: 10px;
      padding: 11px 13px;
      border-radius: 14px;
      background: #faf6fb;
    }

    .offline {
      opacity: 0.48;
    }

    .score {
      color: var(--pink-dark);
      font-weight: 900;
    }

    .bingo-card {
      display: grid;
      grid-template-columns: repeat(5, 1fr);
      gap: 6px;
      margin-top: 20px;
    }

    .bingo-space {
      display: grid;
      min-height: 78px;
      padding: 5px;
      place-items: center;
      border: 0;
      border-radius: 12px;
      color: var(--purple-dark);
      background: #f6edf8;
      text-align: center;
      font-size: clamp(10px, 3vw, 14px);
      font-weight: 800;
    }

    .bingo-space.marked {
      color: white;
      background: var(--pink-dark);
    }

    .called-word {
      padding: 30px;
      border-radius: 24px;
      color: var(--purple-dark);
      background: var(--mint);
      text-align: center;
      font-size: clamp(32px, 8vw, 70px);
      font-weight: 950;
    }

    .called-list {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-top: 15px;
    }

    .pill {
      padding: 7px 11px;
      border-radius: 999px;
      color: var(--purple-dark);
      background: #f2eaf4;
      font-size: 13px;
      font-weight: 800;
    }

    .price-display {
      padding: 30px;
      border-radius: 24px;
      background: #fff5d7;
      text-align: center;
    }

    .price-display h2 {
      font-size: clamp(30px, 7vw, 62px);
    }

    .actual-price {
      color: var(--pink-dark);
      font-size: clamp(45px, 9vw, 90px);
      font-weight: 950;
    }

    .results {
      display: grid;
      gap: 9px;
      margin-top: 18px;
    }

    .result {
      display: grid;
      grid-template-columns: 1fr auto auto;
      gap: 14px;
      padding: 13px;
      border-radius: 14px;
      background: #faf6fb;
    }

    .quiz-board {
      display: grid;
      grid-template-columns: repeat(4, minmax(120px, 1fr));
      gap: 8px;
      overflow-x: auto;
    }

    .quiz-category {
      padding: 12px 8px;
      border-radius: 12px;
      color: white;
      background: var(--purple-dark);
      text-align: center;
      font-weight: 900;
    }

    .quiz-cell {
      min-height: 88px;
      border: 0;
      border-radius: 12px;
      color: var(--purple-dark);
      background: var(--yellow);
      font-size: 24px;
      font-weight: 950;
    }

    .quiz-cell.used {
      color: #aaa0ad;
      background: #eee8ef;
    }

    .question-card {
      padding: 28px;
      border-radius: 24px;
      color: var(--purple-dark);
      background: #e7f5fb;
      text-align: center;
    }

    .question-card h2 {
      font-size: clamp(27px, 5vw, 50px);
      line-height: 1.15;
    }

    .answer-key {
      padding: 18px;
      border-radius: 16px;
      background: var(--mint);
      font-size: 21px;
      font-weight: 900;
    }

    .submission {
      display: grid;
      grid-template-columns: 120px 1fr auto auto;
      gap: 10px;
      align-items: center;
      padding: 10px;
      border-radius: 13px;
      background: #faf6fb;
    }

    .notice {
      margin: 12px 0;
      padding: 12px 14px;
      border-radius: 13px;
      color: var(--purple-dark);
      background: #f3eaf6;
    }

    .status {
      min-height: 22px;
      margin-top: 10px;
      color: var(--pink-dark);
      font-weight: 800;
    }

    .modal {
      position: fixed;
      z-index: 20;
      inset: 0;
      display: grid;
      padding: 20px;
      place-items: center;
      background: rgba(51, 40, 58, 0.72);
    }

    .modal-card {
      width: min(520px, 100%);
      padding: 34px;
      border-radius: 28px;
      background: white;
      box-shadow: var(--shadow);
      text-align: center;
    }

    .modal-card .emoji {
      font-size: 72px;
    }

    @media (max-width: 800px) {
      .hero,
      .host-grid {
        grid-template-columns: 1fr;
      }

      .game-picker {
        grid-template-columns: 1fr;
      }

      .baby-art {
        min-height: 210px;
      }

      .host-sidebar {
        order: -1;
      }
    }

    @media (max-width: 560px) {
      .shell {
        width: min(100% - 18px, 1180px);
        padding-top: 14px;
      }

      .card {
        border-radius: 20px;
      }

      .join-box {
        grid-template-columns: 1fr;
      }

      .submission {
        grid-template-columns: 1fr 1fr;
      }

      .result {
        grid-template-columns: 1fr auto;
      }
    }
  </style>
</head>

<body>
  <main class="shell">
    <header class="brand">
      <div class="brand-mark">🧸</div>
      <div>
        <h1>Tiny Party Games</h1>
        <p>Live baby-shower fun for every guest</p>
      </div>
    </header>

    <section id="homeView" class="card hero">
      <div>
        <h2>Ready, set, baby!</h2>

        <p>
          Host a room on the big screen, then let up to 20 guests join
          from their phones using a QR code or five-character room code.
        </p>

        <div class="button-row">
          <button id="hostButton" class="button pink">
            Host a Game
          </button>
        </div>

        <div class="join-box">
          <input
            id="roomCodeInput"
            maxlength="5"
            autocomplete="off"
            placeholder="Room code"
          >

          <button id="showJoinButton" class="button">
            Join Game
          </button>
        </div>

        <div id="homeStatus" class="status"></div>
      </div>

      <div class="baby-art">👶</div>
    </section>

    <section id="joinView" class="card hidden">
      <h2>Join the celebration</h2>

      <p class="notice">
        Enter the name you would like shown on the scoreboard.
      </p>

      <div class="join-box">
        <input
          id="playerNameInput"
          maxlength="24"
          autocomplete="name"
          placeholder="Your name"
        >

        <button id="joinButton" class="button pink">
          Enter Room
        </button>
      </div>

      <div id="joinStatus" class="status"></div>
    </section>

    <section id="hostView" class="hidden">
      <div class="topline">
        <div>
          <h2>Host Dashboard</h2>
          <div class="room-code">
            ROOM <span id="hostRoomCode"></span>
          </div>
        </div>

        <button id="changeGameButton" class="button ghost hidden">
          Game Menu
        </button>
      </div>

      <div class="host-grid">
        <div>
          <section id="gamePicker" class="card">
            <h2>Choose a game</h2>

            <div class="game-picker">
              <button class="game-tile" data-game="bingo">
                <span class="game-icon">🍼</span>
                <span class="game-title">Baby Bingo</span>
                <span class="game-copy">
                  Call baby-themed words while guests mark unique cards.
                </span>
              </button>

              <button class="game-tile" data-game="price">
                <span class="game-icon">🏷️</span>
                <span class="game-title">Tiny Price Challenge</span>
                <span class="game-copy">
                  Guests estimate baby-product prices without going over.
                </span>
              </button>

              <button class="game-tile" data-game="quiz">
                <span class="game-icon">🧠</span>
                <span class="game-title">Baby Brain Board</span>
                <span class="game-copy">
                  Pick categories and values from an original quiz board.
                </span>
              </button>
            </div>
          </section>

          <section id="hostGame" class="card hidden"></section>
        </div>

        <aside class="host-sidebar">
          <section class="card">
            <h3>Scan to join</h3>
            <img id="qrImage" class="qr" alt="Guest join QR code">
            <p id="joinUrl" class="join-url"></p>
          </section>

          <section class="card" style="margin-top: 18px">
            <h3>
              Guests
              <span id="playerCount">0/20</span>
            </h3>

            <div id="hostPlayers" class="players"></div>
          </section>
        </aside>
      </div>
    </section>

    <section id="playerView" class="hidden">
      <div class="topline">
        <div>
          <h2 id="playerGreeting">Welcome!</h2>
          <div class="room-code">
            ROOM <span id="playerRoomCode"></span>
          </div>
        </div>

        <div class="room-code">
          SCORE <span id="playerScore">0</span>
        </div>
      </div>

      <section id="playerGame" class="card">
        <h2>Waiting for the host</h2>
        <p>The game will appear here when it begins.</p>
      </section>
    </section>
  </main>

  <div id="celebrationModal" class="modal hidden">
    <div class="modal-card">
      <div class="emoji">🎉</div>
      <h2 id="celebrationTitle"></h2>
      <p id="celebrationMessage"></p>
      <button id="closeCelebration" class="button pink">
        Hooray!
      </button>
    </div>
  </div>

  <script src="/socket.io/socket.io.js"></script>

  <script>
    const socket = io();

    const state = {
      role: null,
      room: null,
      playerId: localStorage.getItem("tinyPartyPlayerId"),
      bingoCard: [],
      submittedPrice: false,
      submittedQuiz: false,
      quizSubmissions: []
    };

    const $ = (selector) => document.querySelector(selector);

    const money = new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD"
    });

    function showOnly(id) {
      ["homeView", "joinView", "hostView", "playerView"].forEach((viewId) => {
        document.getElementById(viewId).classList.toggle(
          "hidden",
          viewId !== id
        );
      });
    }

    function escapeHtml(value) {
      return String(value ?? "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
    }

    function queryRoomCode() {
      return new URLSearchParams(location.search)
        .get("room")
        ?.toUpperCase();
    }

    function setJoinScreen(roomCode) {
      $("#roomCodeInput").value = roomCode || "";
      showOnly("joinView");
      $("#playerNameInput").focus();
    }

    function renderPlayers() {
      if (!state.room) return;

      $("#playerCount").textContent =
        state.room.players.length + "/${MAX_PLAYERS}";

      $("#hostPlayers").innerHTML =
        state.room.players.length
          ? state.room.players.map((player) => \`
              <div class="player-row \${player.connected ? "" : "offline"}">
                <span>\${escapeHtml(player.name)}</span>
                <span class="score">\${player.score}</span>
              </div>
            \`).join("")
          : "<p>No guests yet.</p>";

      if (state.role === "player") {
        const player = state.room.players.find(
          (entry) => entry.id === state.playerId
        );

        if (player) {
          $("#playerScore").textContent = player.score;
        }
      }
    }

    function renderHost() {
      if (!state.room || state.role !== "host") return;

      renderPlayers();

      const hasGame = Boolean(state.room.game);
      $("#gamePicker").classList.toggle("hidden", hasGame);
      $("#hostGame").classList.toggle("hidden", !hasGame);
      $("#changeGameButton").classList.toggle("hidden", !hasGame);

      if (!hasGame) return;

      if (state.room.game === "bingo") renderHostBingo();
      if (state.room.game === "price") renderHostPrice();
      if (state.room.game === "quiz") renderHostQuiz();
    }

    function renderPlayer() {
      if (!state.room || state.role !== "player") return;

      renderPlayers();

      if (!state.room.game) {
        $("#playerGame").innerHTML = \`
          <h2>Waiting for the host</h2>
          <p>Choose your luckiest baby-themed game face.</p>
        \`;
        return;
      }

      if (state.room.game === "bingo") renderPlayerBingo();
      if (state.room.game === "price") renderPlayerPrice();
      if (state.room.game === "quiz") renderPlayerQuiz();
    }

    function renderHostBingo() {
      const bingo = state.room.bingo;

      $("#hostGame").innerHTML = \`
        <h2>Baby Bingo</h2>

        <div class="called-word">
          \${escapeHtml(bingo.current || "Ready to call?")}
        </div>

        <div class="button-row">
          <button id="callBingoButton" class="button pink">
            Call Next Item
          </button>
        </div>

        <h3 style="margin-top: 24px">
          Called Items (\${bingo.called.length})
        </h3>

        <div class="called-list">
          \${bingo.called.map((word) =>
            \`<span class="pill">\${escapeHtml(word)}</span>\`
          ).join("") || "<p>Nothing has been called yet.</p>"}
        </div>
      \`;

      $("#callBingoButton").onclick = () => socket.emit("call-bingo");
    }

    function renderPlayerBingo() {
      const current = state.room.bingo.current;

      $("#playerGame").innerHTML = \`
        <h2>Baby Bingo</h2>

        <div class="notice">
          Latest call:
          <strong>\${escapeHtml(current || "Waiting…")}</strong>
        </div>

        <div class="bingo-card">
          \${state.bingoCard.map((space) => \`
            <button
              class="bingo-space \${space.marked ? "marked" : ""}"
              data-index="\${space.index}"
            >
              \${escapeHtml(space.label)}
            </button>
          \`).join("")}
        </div>

        <div class="button-row">
          <button id="claimBingoButton" class="button pink">
            I Have Bingo!
          </button>
        </div>

        <div id="playerActionStatus" class="status"></div>
      \`;

      document.querySelectorAll(".bingo-space").forEach((button) => {
        button.onclick = () => {
          socket.emit(
            "toggle-bingo-space",
            { index: Number(button.dataset.index) },
            (response) => {
              if (!response?.ok) {
                $("#playerActionStatus").textContent =
                  response?.message || "Unable to mark that space.";
                return;
              }

              state.bingoCard = response.card;
              renderPlayerBingo();
            }
          );
        };
      });

      $("#claimBingoButton").onclick = () => {
        socket.emit("claim-bingo", (response) => {
          if (!response?.ok) {
            $("#playerActionStatus").textContent =
              response?.message || "No bingo yet.";
          }
        });
      };
    }

    function renderHostPrice() {
      const price = state.room.price;
      const round = price.round;

      if (!round) return;

      const results = price.results.map((result) => \`
        <div class="result">
          <strong>\${escapeHtml(result.name)}</strong>
          <span>\${money.format(result.guess)}</span>
          <span class="score">
            \${result.points ? "+" + result.points : result.over ? "Over" : "—"}
          </span>
        </div>
      \`).join("");

      $("#hostGame").innerHTML = \`
        <h2>
          Tiny Price Challenge
          <small>Round \${price.roundIndex + 1}</small>
        </h2>

        <div class="price-display">
          <h2>\${escapeHtml(round.title)}</h2>
          <p>\${escapeHtml(round.description)}</p>

          \${price.revealed
            ? \`<div class="actual-price">\${money.format(round.price)}</div>\`
            : \`<div class="notice">
                 \${price.responseCount} guest response(s)
               </div>\`
          }
        </div>

        <div class="button-row">
          <button
            id="openPriceButton"
            class="button mint"
            \${price.open || price.revealed ? "disabled" : ""}
          >
            Open Guessing
          </button>

          <button
            id="revealPriceButton"
            class="button pink"
            \${!price.open ? "disabled" : ""}
          >
            Reveal Price
          </button>

          <button
            id="nextPriceButton"
            class="button yellow"
            \${!price.revealed ? "disabled" : ""}
          >
            Next Item
          </button>
        </div>

        <div class="results">\${results}</div>
      \`;

      $("#openPriceButton").onclick =
        () => socket.emit("open-price-round");

      $("#revealPriceButton").onclick =
        () => socket.emit("reveal-price");

      $("#nextPriceButton").onclick = () => {
        state.submittedPrice = false;
        socket.emit("next-price-round");
      };
    }

    function renderPlayerPrice() {
      const price = state.room.price;
      const round = price.round;

      if (!round) return;

      if (!price.open && !price.revealed) {
        $("#playerGame").innerHTML = \`
          <h2>Tiny Price Challenge</h2>
          <p>Waiting for the host to open round \${price.roundIndex + 1}.</p>
        \`;
        return;
      }

      if (price.revealed) {
        const ownResult = price.results.find(
          (result) => result.playerId === state.playerId
        );

        $("#playerGame").innerHTML = \`
          <h2>\${escapeHtml(round.title)}</h2>

          <div class="price-display">
            <p>The actual retail price was</p>
            <div class="actual-price">\${money.format(round.price)}</div>
          </div>

          <div class="notice">
            Your guess:
            <strong>
              \${ownResult ? money.format(ownResult.guess) : "No guess"}
            </strong>

            \${ownResult?.points
              ? " — You earned " + ownResult.points + " points!"
              : ""}
          </div>
        \`;
        return;
      }

      $("#playerGame").innerHTML = \`
        <h2>\${escapeHtml(round.title)}</h2>
        <p>\${escapeHtml(round.description)}</p>

        <label for="priceInput"><strong>Your price guess</strong></label>

        <div class="join-box">
          <input
            id="priceInput"
            type="number"
            inputmode="decimal"
            min="0"
            step="0.01"
            placeholder="$0.00"
            \${state.submittedPrice ? "disabled" : ""}
          >

          <button
            id="submitPriceButton"
            class="button pink"
            \${state.submittedPrice ? "disabled" : ""}
          >
            \${state.submittedPrice ? "Submitted" : "Lock In"}
          </button>
        </div>

        <div id="playerActionStatus" class="status">
          \${state.submittedPrice ? "Your guess is locked in." : ""}
        </div>
      \`;

      if (!state.submittedPrice) {
        $("#submitPriceButton").onclick = () => {
          socket.emit(
            "submit-price",
            { amount: $("#priceInput").value },
            (response) => {
              if (!response?.ok) {
                $("#playerActionStatus").textContent =
                  response?.message || "Unable to submit.";
                return;
              }

              state.submittedPrice = true;
              renderPlayerPrice();
            }
          );
        };
      }
    }

    function renderHostQuiz() {
      const quiz = state.room.quiz;

      if (!quiz.selected) {
        const headers = quiz.categories.map((category) =>
          \`<div class="quiz-category">\${escapeHtml(category.name)}</div>\`
        ).join("");

        let cells = "";

        for (let row = 0; row < 4; row += 1) {
          quiz.categories.forEach((category, categoryIndex) => {
            const key = categoryIndex + "-" + row;
            const question = category.questions[row];
            const used = quiz.used.includes(key);

            cells += \`
              <button
                class="quiz-cell \${used ? "used" : ""}"
                data-category="\${categoryIndex}"
                data-question="\${row}"
                \${used ? "disabled" : ""}
              >
                \${question.value}
              </button>
            \`;
          });
        }

        $("#hostGame").innerHTML = \`
          <h2>Baby Brain Board</h2>
          <div class="quiz-board">\${headers}\${cells}</div>
        \`;

        document.querySelectorAll(".quiz-cell").forEach((button) => {
          button.onclick = () => {
            state.submittedQuiz = false;

            socket.emit("select-quiz-question", {
              categoryIndex: Number(button.dataset.category),
              questionIndex: Number(button.dataset.question)
            });
          };
        });

        return;
      }

      const selected = quiz.selected;

      const submissions = state.quizSubmissions.map((submission) => \`
        <div class="submission">
          <strong>\${escapeHtml(submission.name)}</strong>
          <span>\${escapeHtml(submission.answer)}</span>

          <button
            class="button mint score-answer"
            data-player="\${submission.playerId}"
            data-correct="true"
          >
            Correct
          </button>

          <button
            class="button ghost score-answer"
            data-player="\${submission.playerId}"
            data-correct="false"
          >
            Miss
          </button>
        </div>
      \`).join("");

      $("#hostGame").innerHTML = \`
        <div class="question-card">
          <p>
            \${escapeHtml(selected.category)}
            · \${selected.value} points
          </p>

          <h2>\${escapeHtml(selected.question)}</h2>

          <div class="notice">
            \${quiz.responseCount} response(s)
          </div>

          \${quiz.revealed
            ? \`<div class="answer-key">
                 Answer: \${escapeHtml(selected.answer)}
               </div>\`
            : ""}
        </div>

        <div class="button-row">
          <button
            id="revealQuizButton"
            class="button pink"
            \${!quiz.open ? "disabled" : ""}
          >
            Reveal Answer
          </button>

          <button
            id="closeQuizButton"
            class="button yellow"
            \${!quiz.revealed ? "disabled" : ""}
          >
            Back to Board
          </button>
        </div>

        <div class="results">
          \${quiz.revealed
            ? submissions || "<p>No answers were submitted.</p>"
            : ""}
        </div>
      \`;

      $("#revealQuizButton").onclick =
        () => socket.emit("reveal-quiz");

      $("#closeQuizButton").onclick = () => {
        state.quizSubmissions = [];
        socket.emit("close-quiz-question");
      };

      document.querySelectorAll(".score-answer").forEach((button) => {
        button.onclick = () => {
          socket.emit("score-quiz-answer", {
            playerId: button.dataset.player,
            correct: button.dataset.correct === "true"
          });

          button.parentElement.style.opacity = "0.45";
          button.parentElement
            .querySelectorAll("button")
            .forEach((item) => item.disabled = true);
        };
      });
    }

    function renderPlayerQuiz() {
      const quiz = state.room.quiz;

      if (!quiz.selected) {
        $("#playerGame").innerHTML = \`
          <h2>Baby Brain Board</h2>
          <p>Waiting for the host to choose a question.</p>
        \`;
        return;
      }

      const selected = quiz.selected;

      if (quiz.revealed) {
        $("#playerGame").innerHTML = \`
          <div class="question-card">
            <p>\${escapeHtml(selected.category)} · \${selected.value}</p>
            <h2>\${escapeHtml(selected.question)}</h2>

            <div class="answer-key">
              Answer: \${escapeHtml(selected.answer)}
            </div>
          </div>
        \`;
        return;
      }

      $("#playerGame").innerHTML = \`
        <div class="question-card">
          <p>\${escapeHtml(selected.category)} · \${selected.value}</p>
          <h2>\${escapeHtml(selected.question)}</h2>
        </div>

        <div class="join-box">
          <input
            id="quizAnswerInput"
            maxlength="120"
            placeholder="Type your answer"
            \${state.submittedQuiz ? "disabled" : ""}
          >

          <button
            id="submitQuizButton"
            class="button pink"
            \${state.submittedQuiz ? "disabled" : ""}
          >
            \${state.submittedQuiz ? "Submitted" : "Submit"}
          </button>
        </div>

        <div id="playerActionStatus" class="status">
          \${state.submittedQuiz ? "Your answer is locked in." : ""}
        </div>
      \`;

      if (!state.submittedQuiz) {
        $("#submitQuizButton").onclick = () => {
          socket.emit(
            "submit-quiz",
            { answer: $("#quizAnswerInput").value },
            (response) => {
              if (!response?.ok) {
                $("#playerActionStatus").textContent =
                  response?.message || "Unable to submit.";
                return;
              }

              state.submittedQuiz = true;
              renderPlayerQuiz();
            }
          );
        };
      }
    }

    $("#hostButton").onclick = () => {
      socket.emit("create-room", (response) => {
        if (!response?.ok) {
          $("#homeStatus").textContent =
            response?.message || "Unable to create a room.";
          return;
        }

        state.role = "host";
        state.room = response.room;

        $("#hostRoomCode").textContent = response.room.code;
        $("#qrImage").src = response.qrDataUrl;
        $("#joinUrl").textContent = response.joinUrl;

        history.replaceState(
          {},
          "",
          "/?host=" + response.room.code
        );

        showOnly("hostView");
        renderHost();
      });
    };

    $("#showJoinButton").onclick = () => {
      const roomCode = $("#roomCodeInput").value.trim().toUpperCase();

      if (roomCode.length !== 5) {
        $("#homeStatus").textContent =
          "Enter the five-character room code.";
        return;
      }

      history.replaceState({}, "", "/?room=" + roomCode);
      setJoinScreen(roomCode);
    };

    $("#joinButton").onclick = () => {
      const roomCode =
        queryRoomCode() || $("#roomCodeInput").value.trim().toUpperCase();

      socket.emit(
        "join-room",
        {
          roomCode,
          name: $("#playerNameInput").value,
          playerId: state.playerId
        },
        (response) => {
          if (!response?.ok) {
            $("#joinStatus").textContent =
              response?.message || "Unable to join.";
            return;
          }

          state.role = "player";
          state.room = response.room;
          state.playerId = response.playerId;
          state.bingoCard = response.player.bingoCard;

          localStorage.setItem(
            "tinyPartyPlayerId",
            response.playerId
          );

          localStorage.setItem(
            "tinyPartyPlayerName",
            response.player.name
          );

          $("#playerGreeting").textContent =
            "Hi, " + response.player.name + "!";

          $("#playerRoomCode").textContent = response.room.code;

          showOnly("playerView");
          renderPlayer();
        }
      );
    };

    $("#changeGameButton").onclick = () => {
      state.room.game = null;
      renderHost();
    };

    document.querySelectorAll("[data-game]").forEach((button) => {
      button.onclick = () => {
        state.submittedPrice = false;
        state.submittedQuiz = false;
        state.quizSubmissions = [];

        socket.emit("select-game", {
          game: button.dataset.game
        });
      };
    });

    $("#closeCelebration").onclick = () => {
      $("#celebrationModal").classList.add("hidden");
    };

    socket.on("room-state", (room) => {
      const previousPriceRound = state.room?.price?.roundIndex;
      const previousQuizKey = state.room?.quiz?.selected
        ? state.room.quiz.selected.categoryIndex +
          "-" +
          state.room.quiz.selected.questionIndex
        : null;

      state.room = room;

      if (
        previousPriceRound !== undefined &&
        previousPriceRound !== room.price.roundIndex
      ) {
        state.submittedPrice = false;
      }

      const newQuizKey = room.quiz.selected
        ? room.quiz.selected.categoryIndex +
          "-" +
          room.quiz.selected.questionIndex
        : null;

      if (newQuizKey !== previousQuizKey) {
        state.submittedQuiz = false;
      }

      renderHost();
      renderPlayer();
    });

    socket.on("bingo-card", (card) => {
      state.bingoCard = card;
      renderPlayer();
    });

    socket.on("quiz-submissions", (submissions) => {
      state.quizSubmissions = submissions;
      renderHost();
    });

    socket.on("celebration", ({ title, message }) => {
      $("#celebrationTitle").textContent = title;
      $("#celebrationMessage").textContent = message;
      $("#celebrationModal").classList.remove("hidden");
    });

    socket.on("host-disconnected", () => {
      if (state.role === "player") {
        $("#playerGame").innerHTML = \`
          <h2>The host disconnected</h2>
          <p>The room may return if the host reconnects shortly.</p>
        \`;
      }
    });

    const roomFromUrl = queryRoomCode();

    if (roomFromUrl) {
      setJoinScreen(roomFromUrl);

      const savedName = localStorage.getItem("tinyPartyPlayerName");

      if (savedName) {
        $("#playerNameInput").value = savedName;
      }
    }
  </script>
</body>
</html>
`;

server.listen(PORT, "0.0.0.0", () => {
  console.log(`Tiny Party Games is running at ${BASE_URL}`);
});
