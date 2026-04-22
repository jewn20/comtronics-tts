from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
import edge_tts
import io

import firebase_admin
from firebase_admin import credentials, firestore
from datetime import date

cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

FREE_LIMIT = 3

# 🎤 VOICES
@app.get("/voices")
async def voices():
    voices = await edge_tts.list_voices()
    return {"voices": [
        {"name": v["ShortName"], "lang": v["Locale"], "gender": v["Gender"]}
        for v in voices
    ]}

# 📊 GET USAGE
@app.get("/usage")
async def usage(user_id: str):

    user_ref = db.collection("users").document(user_id)
    user = user_ref.get()
    today = str(date.today())

    if not user.exists:
        user_ref.set({
            "plan": "free",
            "usage_today": 0,
            "last_reset": today
        })
        return {"plan": "free", "usage": 0, "limit": FREE_LIMIT}

    data = user.to_dict()

    # reset daily
    if data.get("last_reset") != today:
        user_ref.update({
            "usage_today": 0,
            "last_reset": today
        })
        return {"plan": data.get("plan", "free"), "usage": 0, "limit": FREE_LIMIT}

    return {
        "plan": data.get("plan", "free"),
        "usage": data.get("usage_today", 0),
        "limit": FREE_LIMIT
    }

# 🔊 TTS
@app.get("/tts")
async def tts(text: str, voice: str, rate: str, pitch: str, user_id: str):

    user_ref = db.collection("users").document(user_id)
    user = user_ref.get()
    today = str(date.today())

    if not user.exists:
        user_ref.set({
            "plan": "free",
            "usage_today": 0,
            "last_reset": today
        })
        usage = 0
        plan = "free"
    else:
        data = user.to_dict()
        usage = data.get("usage_today", 0)
        plan = data.get("plan", "free")

        if data.get("last_reset") != today:
            usage = 0
            user_ref.update({
                "usage_today": 0,
                "last_reset": today
            })

    # 🚫 LIMIT
    if plan == "free" and usage >= FREE_LIMIT:
        return JSONResponse({"error": "Limit reached (3/day). Upgrade to Pro."})

    # ✅ INCREMENT
    user_ref.set({
        "plan": plan,
        "usage_today": usage + 1,
        "last_reset": today
    }, merge=True)

    communicate = edge_tts.Communicate(
        text=text,
        voice=voice,
        rate=f"{rate}%",
        pitch=f"{pitch}Hz"
    )

    audio_bytes = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_bytes += chunk["data"]

    return StreamingResponse(io.BytesIO(audio_bytes), media_type="audio/mpeg")