"""
TTS module using ElevenLabs API.

Primary TTS backend for Daily Reflections. Uses the JEJ voice clone.
Falls back gracefully if API key is missing or request fails.
"""

import os
import requests

DEFAULT_VOICE_ID = "DihGQaIZuuqae0qMrsGF"  # JEJ clone
MAX_CHARS = 5000  # ElevenLabs limit per request for most models


def _chunk_text(text):
    """Split text into chunks under MAX_CHARS, splitting on paragraph then sentence boundaries."""
    paragraphs = text.split("\n\n")
    chunks = []
    current = ""

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        if len(current) + len(para) + 2 <= MAX_CHARS:
            current = f"{current}\n\n{para}" if current else para
        else:
            if current:
                chunks.append(current)
            if len(para) > MAX_CHARS:
                sentences = para.replace(". ", ".\n").split("\n")
                current = ""
                for sent in sentences:
                    sent = sent.strip()
                    if not sent:
                        continue
                    if len(current) + len(sent) + 1 <= MAX_CHARS:
                        current = f"{current} {sent}" if current else sent
                    else:
                        if current:
                            chunks.append(current)
                        current = sent
            else:
                current = para

    if current:
        chunks.append(current)

    return chunks


def text_to_speech(text, output_path, voice_id=None, model="eleven_v3"):
    """
    Generate speech via ElevenLabs API and save as MP3.
    Returns True on success, False on failure.
    """
    api_key = os.environ.get("ELEVENLABS_API_KEY")
    if not api_key:
        print("Error: ELEVENLABS_API_KEY not set.")
        return False

    if voice_id is None:
        voice_id = os.environ.get("ELEVENLABS_VOICE_ID", DEFAULT_VOICE_ID)

    chunks = _chunk_text(text)
    print(f"Generating speech via ElevenLabs (voice: {voice_id[:8]}..., {len(chunks)} chunk(s))...")

    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    headers = {
        "xi-api-key": api_key,
        "Content-Type": "application/json",
        "Accept": "audio/mpeg",
    }

    audio_parts = []

    try:
        for i, chunk in enumerate(chunks):
            print(f"  Chunk {i+1}/{len(chunks)} ({len(chunk)} chars)...")
            payload = {
                "text": chunk,
                "model_id": model,
            }
            resp = requests.post(url, json=payload, headers=headers, timeout=120)
            resp.raise_for_status()
            audio_parts.append(resp.content)

        if not audio_parts:
            print("No audio generated.")
            return False

        # Concatenate MP3 chunks (MP3 frames are independently decodable)
        with open(output_path, "wb") as f:
            for part in audio_parts:
                f.write(part)

        print(f"Audio saved to {output_path}")
        return True

    except requests.HTTPError as e:
        print(f"ElevenLabs API error: {e} — {e.response.text if e.response else ''}")
        return False
    except Exception as e:
        print(f"Error in ElevenLabs generation: {e}")
        return False


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    test_text = "Good morning Chris. This is a test of the ElevenLabs text to speech system."
    text_to_speech(test_text, "test_elevenlabs.mp3")
