"""
Translation + speech services for the VKYC prototype.
All calls to the AI provider live in this one file, so swapping
Sarvam for Bhashini later means changing only this file.
"""

import os
import requests
from sarvamai import SarvamAI

SARVAM_TRANSLATE_URL = "https://api.sarvam.ai/translate"


def _client():
    """Create a Sarvam client using the key from the .env file."""
    api_key = os.environ.get("SARVAM_API_KEY")
    if not api_key:
        raise RuntimeError("SARVAM_API_KEY not set - add it to your .env file")
    return SarvamAI(api_subscription_key=api_key)


def translate_text(text: str, source_lang: str = "auto", target_lang: str = "en-IN") -> dict:
    """Text in, translated text out."""
    api_key = os.environ.get("SARVAM_API_KEY")
    if not api_key:
        raise RuntimeError("SARVAM_API_KEY not set - add it to your .env file")

    payload = {
        "input": text,
        "source_language_code": source_lang,
        "target_language_code": target_lang,
        "model": "mayura:v1",
    }
    headers = {"api-subscription-key": api_key, "Content-Type": "application/json"}
    resp = requests.post(SARVAM_TRANSLATE_URL, json=payload, headers=headers, timeout=30)

    if resp.status_code != 200:
        raise RuntimeError(f"Sarvam API error {resp.status_code}: {resp.text}")

    data = resp.json()
    return {
        "translated_text": data.get("translated_text", ""),
        "detected_source": data.get("source_language_code", source_lang),
    }


def speech_to_english(audio_path: str) -> dict:
    """
    THE CUSTOMER LEG.
    Takes a recording of the customer speaking any Indian language and
    returns English text. Sarvam detects the language automatically.
    """
    client = _client()
    with open(audio_path, "rb") as f:
        resp = client.speech_to_text.translate(file=f, model="saaras:v2.5")

    transcript = getattr(resp, "transcript", None)
    if transcript is None and isinstance(resp, dict):
        transcript = resp.get("transcript", "")

    detected = getattr(resp, "language_code", None)
    if detected is None and isinstance(resp, dict):
        detected = resp.get("language_code", "")

    return {"english_text": transcript or "", "detected_source": detected or "auto"}


def speech_to_text_english(audio_path: str) -> str:
    """
    THE OFFICER LEG, step 1.
    Takes a recording of the officer speaking English and returns
    English text (transcribed as spoken, not translated).
    """
    client = _client()
    with open(audio_path, "rb") as f:
        resp = client.speech_to_text.transcribe(
            file=f,
            model="saarika:v2.5",
            language_code="en-IN",
        )

    transcript = getattr(resp, "transcript", None)
    if transcript is None and isinstance(resp, dict):
        transcript = resp.get("transcript", "")
    return transcript or ""


def text_to_speech(text: str, language: str = "ta-IN") -> str:
    """
    THE AGENT LEG, step 2.
    Turns text into spoken audio in the customer's language.
    Returns the audio as a base64 string the browser can play.
    """
    client = _client()
    resp = client.text_to_speech.convert(
        text=text,
        target_language_code=language,
        speaker="anushka",
        model="bulbul:v2",
    )

    audios = getattr(resp, "audios", None)
    if audios is None and isinstance(resp, dict):
        audios = resp.get("audios", [])

    if not audios:
        raise RuntimeError("No audio returned by Sarvam")
    return audios[0]