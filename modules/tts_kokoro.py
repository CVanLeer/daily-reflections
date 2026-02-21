
"""
DOC:START
Fast local text-to-speech using Kokoro-82M model.

Purpose:
- Converts text to audio using the Kokoro TTS pipeline
- Supports multiple voices (American/British, Male/Female)
- Caches pipelines per language code for efficiency

Inputs/Outputs:
- Input: text (str), output_path (str), voice (str, e.g. 'am_michael', 'bf_emma')
- Output: WAV audio file at output_path

Side effects:
- Downloads model on first run (~80MB)
- Writes audio file to disk

Run: python modules/tts_kokoro.py
See: modules/modules.md
DOC:END
"""

import os
import soundfile as sf
import numpy as np
import torch
from kokoro import KPipeline

# Initialize pipeline once (global cache)
# 'a' = American English
PIPELINES = {}

def init_pipeline(lang_code='a'):
    global PIPELINES
    if lang_code not in PIPELINES:
        try:
            print(f"Initializing Kokoro Pipeline for language '{lang_code}'...")
            PIPELINES[lang_code] = KPipeline(lang_code=lang_code) 
        except Exception as e:
            print(f"Error initializing Kokoro: {e}")
            return None
    return PIPELINES[lang_code]

def text_to_speech(text, output_path, voice='am_michael', speed=1.0):
    """
    Converts text to speech using Kokoro and saves to output_path.
    """
    # Derive language code from voice prefix (e.g. 'am_michael' -> 'a', 'bf_emma' -> 'b')
    lang_code = voice[0] if voice else 'a'
    
    pipeline = init_pipeline(lang_code)
    if not pipeline:
        return False
        
    try:
        # Generate audio
        # generate() returns a generator of (graphemes, phonemes, audio)
        generator = pipeline(text, voice=voice, speed=speed, split_pattern=r'\n+')
        
        all_audio = []
        
        print("Generating audio segments...")
        for i, (gs, ps, audio) in enumerate(generator):
            # audio is a 1D numpy array
            all_audio.append(audio)
            
        if not all_audio:
            print("No audio generated.")
            return False
            
        # Concatenate all segments
        final_audio = np.concatenate(all_audio)
        
        # Save to file (24khz is standard for Kokoro usually)
        sf.write(output_path, final_audio, 24000)
        
        print(f"Audio saved to {output_path}")
        return True
        
    except Exception as e:
        print(f"Error in TTS generation: {e}")
        return False

if __name__ == "__main__":
    # Test
    test_text = "Good morning Chris. This is a test of the Kokoro text to speech system."
    text_to_speech(test_text, "test_kokoro.wav")
