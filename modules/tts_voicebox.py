"""
DOC:START
TTS module using Voicebox (Qwen3-TTS + MLX) via REST API.

Purpose:
- Generates speech using a cloned voice profile via the Voicebox server
- Supports voice cloning through pre-configured voice profiles
- Chunks long text to stay within API limits, then concatenates audio
- Falls back gracefully when server is unavailable

Inputs/Outputs:
- Input: text (str), output_path (str), optional profile_id, language, seed
- Output: WAV audio file at output_path

Side effects:
- Network calls to local Voicebox server (default localhost:8001)
- Writes audio file to disk

Run: python modules/tts_voicebox.py
See: modules/modules.md, ~/Projects/voicebox/backend/example_usage.py
DOC:END
"""

import os
import io
import requests
import soundfile as sf
import numpy as np

MAX_CHARS = 4500  # Voicebox limit is 5000, leave headroom


def _chunk_text(text):
    """Split text into chunks under MAX_CHARS, splitting on paragraph then sentence boundaries."""
    paragraphs = text.split("\n\n")
    chunks = []
    current = ""

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        # If a single paragraph fits, accumulate
        if len(current) + len(para) + 2 <= MAX_CHARS:
            current = f"{current}\n\n{para}" if current else para
        else:
            # Flush current
            if current:
                chunks.append(current)
            # If paragraph itself exceeds limit, split by sentence
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


def text_to_speech(text, output_path, profile_id=None, language="en", seed=None):
    """
    Generates speech via the Voicebox REST API and saves to output_path.
    Chunks long text automatically. Returns True on success, False on failure.
    """
    base_url = os.environ.get("VOICEBOX_URL", "http://localhost:8001")
    if profile_id is None:
        profile_id = os.environ.get("VOICEBOX_PROFILE_ID")

    if not profile_id:
        print("Error: No Voicebox profile ID. Set VOICEBOX_PROFILE_ID in .env.")
        return False

    # Health check
    try:
        resp = requests.get(f"{base_url}/health", timeout=5)
        resp.raise_for_status()
    except (requests.ConnectionError, requests.Timeout, requests.HTTPError) as e:
        print(f"Voicebox server unreachable at {base_url}: {e}")
        return False

    # Chunk text if needed
    chunks = _chunk_text(text)
    print(f"Generating speech via Voicebox (profile: {profile_id[:8]}..., {len(chunks)} chunk(s))...")

    all_audio = []
    sample_rate = None

    try:
        for i, chunk in enumerate(chunks):
            payload = {
                "profile_id": profile_id,
                "text": chunk,
                "language": language,
            }
            if seed is not None:
                payload["seed"] = seed

            print(f"  Chunk {i+1}/{len(chunks)} ({len(chunk)} chars)...")
            resp = requests.post(f"{base_url}/generate", json=payload, timeout=300)
            resp.raise_for_status()
            generation = resp.json()
            generation_id = generation["id"]
            duration = generation.get("duration", 0)
            print(f"    {duration:.1f}s of audio")

            # Download audio
            resp = requests.get(f"{base_url}/audio/{generation_id}", timeout=120)
            resp.raise_for_status()

            audio_data, sr = sf.read(io.BytesIO(resp.content))
            all_audio.append(audio_data)
            if sample_rate is None:
                sample_rate = sr

        if not all_audio:
            print("No audio generated.")
            return False

        # Concatenate all chunks
        final_audio = np.concatenate(all_audio)
        sf.write(output_path, final_audio, sample_rate)

        total_duration = len(final_audio) / sample_rate
        print(f"Audio saved to {output_path} ({total_duration:.1f}s total)")
        return True

    except Exception as e:
        print(f"Error in Voicebox generation: {e}")
        return False


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    test_text = "Good morning Chris. This is a test of the Voicebox text to speech system."
    text_to_speech(test_text, "test_voicebox.wav")
