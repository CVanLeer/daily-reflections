
"""
DOC:START
High-quality conversational TTS using Sesame CSM-1B model.

Purpose:
- Generates realistic speech from text using Sesame's 1B parameter model
- Chunks long text into sentences to avoid model context limits
- Implements voice chaining for consistent speaker identity across chunks

Inputs/Outputs:
- Input: text (str), output_path (str)
- Output: WAV audio file at output_path

Side effects:
- Downloads model on first run (~1GB, requires HuggingFace login)
- Writes audio file to disk
- WARNING: Very slow on CPU/standard Mac (~1min per 10s of audio)

Run: python modules/tts_sesame.py
See: modules/modules.md
DOC:END
"""

import torch
from transformers import AutoProcessor, CsmForConditionalGeneration
import soundfile as sf
import os
import sys

# Monkey patch for torch.compiler.is_compiling if missing (common on some Mac builds)
if not hasattr(torch, "compiler"):
    import types
    torch.compiler = types.SimpleNamespace()
    torch.compiler.is_compiling = lambda: False
elif not hasattr(torch.compiler, "is_compiling"):
    torch.compiler.is_compiling = lambda: False

# Global cache
MODEL = None
PROCESSOR = None

def init_model():
    global MODEL, PROCESSOR
    if MODEL is None:
        try:
            print("Loading Sesame CSM-1B (Production Mode)...")
            model_id = "sesame/csm-1b"
            
            # Use MPS if available
            device = "mps" if torch.backends.mps.is_available() else "cpu"
            print(f"Using device: {device}")
            
            # Trust remote code is crucial for new/custom architectures
            try:
                PROCESSOR = AutoProcessor.from_pretrained(model_id)
                MODEL = CsmForConditionalGeneration.from_pretrained(model_id, device_map=device)
            except Exception as e:
                print(f"Error loading model: {e}")
                return False
            
            return True
        except Exception as e:
            print(f"Error initializing Sesame CSM-1B: {e}")
            return False
    return True

def text_to_speech(text, output_path):
    """
    Generates audio using Sesame CSM-1B, chunking by sentence to handle long scripts.
    """
    if not init_model():
        return False
        
    try:
        import numpy as np
        device = MODEL.device
        sampling_rate = MODEL.config.sampling_rate if hasattr(MODEL.config, 'sampling_rate') else 24000
        
        # Simple splitting by newline first (preserves structure) then by period
        # This is a rough heuristic.
        raw_chunks = text.replace('\n', '. ').split('.')
        chunks = [c.strip() for c in raw_chunks if c.strip()]
        
        all_audio_segments = []
        
        print(f"Generating audio in {len(chunks)} segments...")
        
        for i, chunk in enumerate(chunks):
            # Sesame expects a speaker token. [0] is default.
            if not chunk.startswith("["):
                csm_input_text = f"[0]{chunk}"
            else:
                csm_input_text = chunk
            
            print(f"  Segment {i+1}/{len(chunks)}: {chunk[:30]}...")
            
            # 1. Process inputs
            inputs = PROCESSOR(text=csm_input_text, add_special_tokens=True).to(device)
            
            # 2. Generate
            with torch.no_grad():
                # Increased max_new_tokens just in case, though chunking helps most
                output = MODEL.generate(**inputs, output_audio=True, max_new_tokens=2048)
            
            # 3. Extract audio
            # Output audio is usually a tensor [1, T] or similar.
            # We need to grab the waveform values.
            # The structure from generate(output_audio=True) returns a wrapper or tensor depending on version.
            # But earlier successful run suggested it returned something PROCESSOR.save_audio accepted.
            # Usually it's output[0] or .audio
            
            # Let's inspect what PROCESSOR.save_audio does: it just writes the tensor.
            # We will grab the tensor to CPU numpy for concatenation.
            audio_tensor = output[0].cpu().float()
            
            # Remove batch dim if present [1, T]
            if audio_tensor.dim() == 2:
                audio_tensor = audio_tensor.squeeze(0)
                
            all_audio_segments.append(audio_tensor.numpy())
            
        # 4. Concatenate all segments
        if not all_audio_segments:
            print("No audio generated.")
            return False
            
        final_audio = np.concatenate(all_audio_segments)
        
        # 5. Save
        sf.write(output_path, final_audio, sampling_rate)
        
        print(f"Full Audio saved to {output_path}")
        return True
        
    except Exception as e:
        print(f"Error in Sesame generation: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    # Test
    text_to_speech("Good Morning Chris. This is a production test.", "test_sesame_v3.wav")
