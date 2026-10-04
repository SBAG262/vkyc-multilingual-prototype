"""
VKYC Multilingual Prototype — backend with speech.
Run with:  uvicorn main:app --reload --port 8000
Then open: http://localhost:8000
"""

import os
import tempfile
from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from translator import translate_text, speech_to_english, text_to_speech, speech_to_text_english
from rag import answer_question

load_dotenv()  # read SARVAM_API_KEY from the .env file at startup

app = FastAPI(title="VKYC Translation Prototype")


class TranslateRequest(BaseModel):
    text: str
    source_lang: str = "auto"
    target_lang: str = "en-IN"


class SpeakRequest(BaseModel):
    text: str
    target_lang: str = "ta-IN"


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "vkyc-translation-prototype",
        "key_loaded": bool(os.environ.get("SARVAM_API_KEY")),
    }


@app.post("/translate")
def translate(req: TranslateRequest):
    try:
        result = translate_text(req.text, req.source_lang, req.target_lang)
        return {"ok": True, **result}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@app.post("/listen")
async def listen(audio: UploadFile = File(...)):
    """CUSTOMER LEG: receive a recording, return English text."""
    tmp_path = None
    try:
        # Save the uploaded recording to a temporary file on disk.
        suffix = os.path.splitext(audio.filename or "clip.wav")[1] or ".wav"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(await audio.read())
            tmp_path = tmp.name

        result = speech_to_english(tmp_path)
        return {"ok": True, **result}
    except Exception as e:
        return {"ok": False, "error": str(e)}
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)


@app.post("/speak")
def speak(req: SpeakRequest):
    """AGENT LEG: turn text into spoken audio in the customer's language."""
    try:
        audio_b64 = text_to_speech(req.text, req.target_lang)
        return {"ok": True, "audio": audio_b64}
    except Exception as e:
        return {"ok": False, "error": str(e)}

class AskRequest(BaseModel):
    question: str


@app.post("/ask")
def ask(req: AskRequest):
    """AGENT ASSIST: answer a policy question, grounded in the knowledge base."""
    try:
        result = answer_question(req.question)
        return {"ok": True, **result}
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.post("/listen-officer")
async def listen_officer(audio: UploadFile = File(...)):
    """OFFICER LEG step 1: receive the officer's English speech, return English text."""
    tmp_path = None
    try:
        suffix = os.path.splitext(audio.filename or "clip.wav")[1] or ".wav"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(await audio.read())
            tmp_path = tmp.name

        text = speech_to_text_english(tmp_path)
        return {"ok": True, "text": text}
    except Exception as e:
        return {"ok": False, "error": str(e)}
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)
@app.get("/")
def index():
    return FileResponse(os.path.join("static", "index.html"))


app.mount("/static", StaticFiles(directory="static"), name="static")