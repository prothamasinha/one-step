"""One Step: local coursework prototype; fictional scenarios only."""
import json
import os
import sqlite3
import urllib.error
import urllib.request
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from typing import Literal

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = Path(os.environ.get("ONE_STEP_DB", str(ROOT / "one_step.sqlite3")))
FRONTEND = ROOT / "frontend"
app = FastAPI(title="One Step — coursework prototype")
app.mount("/static", StaticFiles(directory=FRONTEND), name="static")

SKILL_DESCRIPTIONS = {
    "breathing": "4–6 paced breathing: breathe in for four seconds and out for six seconds, six cycles. The app controls the timing.",
}
FALLBACK = "The chat is unavailable right now. You can return home, review your activity, or open Crisis support at any time."
CRISIS_REPLY = "This coursework app cannot provide crisis help and is not monitored. You can open Crisis support for public resources, or leave this chat."


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@contextmanager
def db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with db() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            skill_type TEXT NOT NULL CHECK(skill_type IN ('breathing')),
            started_at TEXT NOT NULL,
            ended_at TEXT,
            status TEXT NOT NULL CHECK(status IN ('in_progress','completed','left_early','interrupted')),
            planned_seconds INTEGER NOT NULL,
            actual_exercise_seconds REAL,
            paused_seconds REAL NOT NULL DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL REFERENCES sessions(id),
            role TEXT NOT NULL CHECK(role IN ('user','assistant')),
            content TEXT NOT NULL,
            response_mode TEXT NOT NULL CHECK(response_mode IN ('user','mock','live','fallback','safety')),
            created_at TEXT NOT NULL
        );
        """)


init_db()


class SessionStart(BaseModel):
    skill_type: Literal["breathing"]


class SessionUpdate(BaseModel):
    status: Literal["completed", "left_early", "interrupted"]
    actual_exercise_seconds: float = Field(ge=0, le=86400)
    paused_seconds: float = Field(default=0, ge=0, le=86400)


class ChatRequest(BaseModel):
    session_id: int = Field(gt=0)
    text: str = Field(min_length=1, max_length=400)


def get_session(conn, sid):
    row = conn.execute("SELECT * FROM sessions WHERE id=?", (sid,)).fetchone()
    if row is None:
        raise HTTPException(404, "Session not found")
    return dict(row)


@app.get("/api/health")
def health():
    return {"ok": True, "mode": os.environ.get("ONE_STEP_MODEL_MODE", "mock")}


@app.post("/api/sessions", status_code=201)
def start_session(payload: SessionStart):
    with db() as conn:
        cur = conn.execute("INSERT INTO sessions(skill_type,started_at,status,planned_seconds) VALUES(?,?,?,?)",
                           (payload.skill_type, now(), "in_progress", 70))
        return get_session(conn, cur.lastrowid)


@app.patch("/api/sessions/{session_id}")
def update_session(session_id: int, payload: SessionUpdate):
    with db() as conn:
        old = get_session(conn, session_id)
        if old["status"] != "in_progress":
            raise HTTPException(409, "Session already ended")
        conn.execute("UPDATE sessions SET ended_at=?,status=?,actual_exercise_seconds=?,paused_seconds=? WHERE id=?",
                     (now(), payload.status, round(payload.actual_exercise_seconds, 2),
                      round(payload.paused_seconds, 2), session_id))
        return get_session(conn, session_id)


@app.get("/api/sessions")
def list_sessions():
    with db() as conn:
        return [dict(r) for r in conn.execute("SELECT * FROM sessions ORDER BY id DESC LIMIT 40")]


@app.get("/api/messages")
def list_messages(session_id: int):
    with db() as conn:
        get_session(conn, session_id)
        return [dict(r) for r in conn.execute("SELECT * FROM messages WHERE session_id=? ORDER BY id", (session_id,))]


def live_model_reply(skill_type, context):
    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is missing")
    # Only use fictional context: this is not a deployed mental health service.
    messages = [{"role": "system", "content": (
        "You are a very brief optional interface companion in a university COURSEWORK PROTOTYPE. "
        "Only acknowledge the fictional user's message and suggest existing app options. "
        "Do not diagnose, assess risk, promise monitoring, provide clinical advice, "
        "invent skill steps, or claim the app is therapy. Use at most 55 words. "
        "Approved skill: " + SKILL_DESCRIPTIONS[skill_type])}]
    messages += [{"role": m["role"], "content": m["content"]} for m in context]
    payload = json.dumps({"model": os.environ.get("ONE_STEP_MODEL", "gpt-4.1-mini"),
                          "input": messages, "max_output_tokens": 100}).encode()
    request = urllib.request.Request("https://api.openai.com/v1/responses", data=payload,
                                     headers={"Authorization": f"Bearer {api_key}",
                                              "Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(request, timeout=8) as res:
        result = json.load(res)
    pieces = []
    for output in result.get("output", []):
        for item in output.get("content", []):
            if item.get("type") == "output_text":
                pieces.append(item.get("text", ""))
    reply = " ".join(pieces).strip()
    if not reply or len(reply) > 450:
        raise ValueError("Empty or oversized model response")
    # No prompt-only safety guarantee: deterministic crisis UI remains separate.
    return reply


@app.post("/api/chat")
def chat(payload: ChatRequest):
    user_text = payload.text.strip()
    if not user_text:
        raise HTTPException(422, "Message cannot be blank")
    with db() as conn:
        session = get_session(conn, payload.session_id)
        if session["status"] == "in_progress":
            raise HTTPException(409, "Finish or leave the skill before chatting")
        conn.execute("INSERT INTO messages(session_id,role,content,response_mode,created_at) VALUES(?,?,?,?,?)",
                     (payload.session_id, "user", user_text, "user", now()))
        rows = conn.execute("SELECT role,content FROM messages WHERE session_id=? ORDER BY id DESC LIMIT 5",
                            (payload.session_id,)).fetchall()
        context = [dict(r) for r in reversed(rows)]
        # This is a deliberately narrow demo keyword rule, NOT a risk classifier.
        crisis_terms = ("suicide", "kill myself", "hurt myself", "self-harm", "end my life")
        if any(term in user_text.lower() for term in crisis_terms):
            reply, mode = CRISIS_REPLY, "safety"
        elif os.environ.get("ONE_STEP_MODEL_MODE", "mock") == "mock":
            reply, mode = "Thanks for sharing that fictional example. You can practice the breathing exercise again or finish here.", "mock"
        else:
            try:
                if os.environ.get("ONE_STEP_MODEL_MODE") == "fail":
                    raise ConnectionError("Simulated model service outage")
                reply = live_model_reply(session["skill_type"], context)
                mode = "live"
            except (Exception):
                reply, mode = FALLBACK, "fallback"
        conn.execute("INSERT INTO messages(session_id,role,content,response_mode,created_at) VALUES(?,?,?,?,?)",
                     (payload.session_id, "assistant", reply, mode, now()))
        return {"reply": reply, "response_mode": mode}


@app.get("/support.html", include_in_schema=False)
def support():
    return FileResponse(FRONTEND / "support.html", media_type="text/html")


@app.get("/", include_in_schema=False)
def index():
    return FileResponse(FRONTEND / "index.html", media_type="text/html")
