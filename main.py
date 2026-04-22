from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import edge_tts
import uuid
import subprocess
from datetime import datetime

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
def home():
    return FileResponse("static/index.html")


# =========================
# FORMAT FIX
# =========================
def fix_rate(rate: str):
    if not rate.startswith("+") and not rate.startswith("-"):
        rate = "+" + rate
    if not rate.endswith("%"):
        rate += "%"
    return rate


def fix_pitch(pitch: str):
    if not pitch.startswith("+") and not pitch.startswith("-"):
        pitch = "+" + pitch
    if not pitch.endswith("Hz"):
        pitch += "Hz"
    return pitch


# =========================
# USER LIMIT (TEMP)
# =========================
user_usage = {}

def check_limit(user_id):
    today = str(datetime.now().date())

    if user_id not in user_usage:
        user_usage[user_id] = {"date": today, "count": 0}

    if user_usage[user_id]["date"] != today:
        user_usage[user_id] = {"date": today, "count": 0}

    if user_usage[user_id]["count"] >= 10:
        return False

    user_usage[user_id]["count"] += 1
    return True


# =========================
# VOICES
# =========================
@app.get("/voices")
def get_voices():
    result = subprocess.run(
        ["edge-tts", "--list-voices"],
        capture_output=True,
        text=True,
        encoding="utf-8"
    )

    lines = result.stdout.split("\n")[2:]

    voices = []

    for line in lines:
        if line.strip() == "":
            continue

        parts = line.split()

        name = parts[0]
        gender = parts[1]
        lang = name.split("-")[0] + "-" + name.split("-")[1]

        voices.append({
            "name": name,
            "gender": gender,
            "lang": lang
        })

    return {"voices": voices}


# =========================
# TTS
# =========================
@app.get("/tts")
async def tts(text: str, voice: str, rate: str, pitch: str, user_id: str = "guest"):

    if not check_limit(user_id):
        return {"error": "Daily limit reached (10/day)"}

    rate = fix_rate(rate)
    pitch = fix_pitch(pitch)

    filename = f"output_{uuid.uuid4().hex}.mp3"

    communicate = edge_tts.Communicate(
        text=text,
        voice=voice,
        rate=rate,
        pitch=pitch
    )

    await communicate.save(filename)

    return FileResponse(filename, media_type="audio/mpeg", filename="tts.mp3")