"""
TTS module using mlx-audio (Qwen3-TTS) for local Apple Silicon generation.

Two modes:
  - VoiceDesign: describe any voice in natural language via `instruct` param
  - Voice Clone: clone from a reference audio clip via `ref_audio` param

Requires: pip install mlx-audio
"""

import os
import re
import time

VOICEDESIGN_MODEL = "mlx-community/Qwen3-TTS-12Hz-1.7B-VoiceDesign-bf16"
BASE_MODEL = "mlx-community/Qwen3-TTS-12Hz-1.7B-Base-bf16"
DEFAULT_SPEED = 0.75

# JEJ voice clone reference — 12.5s clip, slow deliberate cadence (185 wpm)
JEJ_REF_AUDIO = os.path.join(
    os.path.dirname(__file__), "..", "output", "tortoise_training", "jej", "jej_0006.wav"
)
JEJ_REF_TEXT = (
    "I think rage is a noble emotion. This is something else that's a bit of "
    "psychosis, I think. Well, you know, I did a speech at the Harp, at the Yale, "
    "at the Yale Political Union recently."
)

# Cache loaded model to avoid reloading on multi-chunk generation
_cached_model = None
_cached_model_path = None


def _strip_voice_tags(text):
    """Remove ElevenLabs voice direction tags — Qwen3-TTS doesn't understand them."""
    return re.sub(
        r'\[(?:sighs?|exhales?|whispers?|laughs?|curious|excited|sarcastic|mischievously|happy)\]\s*',
        '', text
    )


def _get_model(model_path):
    """Load and cache the TTS model."""
    global _cached_model, _cached_model_path
    if _cached_model is not None and _cached_model_path == model_path:
        return _cached_model

    from mlx_audio.tts.utils import load_model
    print(f"Loading Qwen3-TTS model: {model_path}...")
    _cached_model = load_model(model_path=model_path)
    _cached_model_path = model_path
    return _cached_model


def text_to_speech(text, output_path, instruct=None, ref_audio=None, ref_text=None,
                   voice=None, speed=None):
    """
    Generate speech via Qwen3-TTS (mlx-audio) and save as WAV.

    Two modes (set one):
      instruct="A warm British female..."  → VoiceDesign model
      ref_audio="path/to/clip.wav"         → Base model voice clone

    Returns True on success, False on failure.
    """
    if speed is None:
        speed = DEFAULT_SPEED

    # Determine mode from params
    if instruct:
        model_path = VOICEDESIGN_MODEL
        mode_label = f"VoiceDesign: {instruct[:60]}..."
    elif ref_audio:
        model_path = BASE_MODEL
        mode_label = f"Clone from {os.path.basename(ref_audio)}"
    else:
        # Default: JEJ voice clone
        model_path = BASE_MODEL
        ref_audio = JEJ_REF_AUDIO
        ref_text = JEJ_REF_TEXT
        mode_label = "Clone: JEJ"

    if voice is None:
        voice = "narrator"

    text = _strip_voice_tags(text)

    try:
        import mlx.core as mx
        import numpy as np
        from mlx_audio.audio_io import write as audio_write

        model = _get_model(model_path)

        print(f"Generating speech via Qwen3-TTS ({mode_label}, speed={speed})...")
        start = time.time()

        gen_kwargs = dict(
            text=text,
            voice=voice,
            speed=speed,
            lang_code="en",
            verbose=False,
        )
        if instruct:
            gen_kwargs["instruct"] = instruct
        if ref_audio:
            gen_kwargs["ref_audio"] = ref_audio
        if ref_text:
            gen_kwargs["ref_text"] = ref_text

        results = model.generate(**gen_kwargs)

        audio_list = []
        for result in results:
            audio_list.append(result.audio)

        if not audio_list:
            print("No audio generated.")
            return False

        audio = mx.concatenate(audio_list, axis=0)
        audio_np = np.array(audio)
        audio_write(output_path, audio_np, model.sample_rate, format="wav")

        elapsed = time.time() - start
        duration = len(audio_np) / model.sample_rate
        rtf = duration / elapsed if elapsed > 0 else 0
        print(f"Audio saved to {output_path} ({duration:.1f}s audio in {elapsed:.1f}s, RTF: {rtf:.2f}x)")
        return True

    except ImportError as e:
        print(f"mlx-audio not installed: {e}")
        print("Install with: pip install mlx-audio")
        return False
    except Exception as e:
        print(f"Error in Qwen3-TTS generation: {e}")
        import traceback
        traceback.print_exc()
        return False
