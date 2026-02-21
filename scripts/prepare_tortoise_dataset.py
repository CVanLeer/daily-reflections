#!/usr/bin/env python3
"""
Prepare audio and transcript data for Tortoise TTS fine-tuning.

Tortoise TTS training requires:
1. Audio clips of 5-15 seconds each
2. Corresponding transcript text files
3. Consistent audio format (22050Hz mono WAV recommended)

This script segments the source audio based on Whisper timestamps
and creates the required file structure.
"""
"""
DOC:START
[One-sentence descriptor]

Purpose:
- [What this file does]

Inputs/Outputs:
- [If applicable]

Side effects:
- [DB writes, network calls, file writes]

Run: [How to run/test]
See: [Pointer to folder doc]
DOC:END
"""


import json
import os
from pathlib import Path
from pydub import AudioSegment
from pydub.silence import detect_nonsilent
import argparse


def load_formatted_transcript(json_path):
    """Load formatted Whisper transcript with segments."""
    with open(json_path, 'r') as f:
        return json.load(f)


def segment_audio_by_whisper(
    audio_path: str,
    transcript_json_path: str,
    output_dir: str,
    min_duration: float = 5.0,
    max_duration: float = 15.0,
    target_sample_rate: int = 22050,
    speaker_name: str = "jej"
):
    """
    Segment audio based on Whisper timestamps for Tortoise TTS training.

    Args:
        audio_path: Path to source audio file
        transcript_json_path: Path to formatted Whisper JSON with timestamps
        output_dir: Directory to save audio clips and transcripts
        min_duration: Minimum clip duration in seconds
        max_duration: Maximum clip duration in seconds
        target_sample_rate: Target sample rate for output (Tortoise uses 22050)
        speaker_name: Name for the speaker directory
    """
    output_dir = Path(output_dir)
    speaker_dir = output_dir / speaker_name
    speaker_dir.mkdir(parents=True, exist_ok=True)

    print(f"Loading audio from: {audio_path}")
    audio = AudioSegment.from_file(audio_path)

    # Convert to mono and target sample rate
    audio = audio.set_channels(1).set_frame_rate(target_sample_rate)

    print(f"Loading transcript from: {transcript_json_path}")
    transcript_data = load_formatted_transcript(transcript_json_path)
    segments = transcript_data.get('segments', [])

    if not segments:
        print("No segments found in transcript!")
        return

    # Merge short segments and split long ones
    processed_segments = []
    current_segment = None

    for segment in segments:
        start = segment['start']
        end = segment['end']
        text = segment['text'].strip()
        duration = end - start

        if not text:  # Skip empty segments
            continue

        if current_segment is None:
            current_segment = {
                'start': start,
                'end': end,
                'text': text
            }
        else:
            # Check if we should merge with current segment
            combined_duration = end - current_segment['start']

            if combined_duration <= max_duration:
                # Merge segments
                current_segment['end'] = end
                current_segment['text'] += ' ' + text
            else:
                # Save current segment if it's long enough
                if current_segment['end'] - current_segment['start'] >= min_duration:
                    processed_segments.append(current_segment)
                # Start new segment
                current_segment = {
                    'start': start,
                    'end': end,
                    'text': text
                }

        # If current segment is long enough and close to max, save it
        if current_segment and (current_segment['end'] - current_segment['start']) >= max_duration * 0.8:
            processed_segments.append(current_segment)
            current_segment = None

    # Don't forget the last segment
    if current_segment and (current_segment['end'] - current_segment['start']) >= min_duration:
        processed_segments.append(current_segment)

    print(f"Created {len(processed_segments)} training segments")

    # Extract and save audio clips
    manifest = []

    for i, segment in enumerate(processed_segments):
        start_ms = int(segment['start'] * 1000)
        end_ms = int(segment['end'] * 1000)
        text = segment['text']
        duration = (end_ms - start_ms) / 1000

        # Extract audio clip
        clip = audio[start_ms:end_ms]

        # Generate filenames
        clip_name = f"{speaker_name}_{i:04d}"
        audio_filename = f"{clip_name}.wav"
        text_filename = f"{clip_name}.txt"

        # Save audio clip
        audio_path_out = speaker_dir / audio_filename
        clip.export(audio_path_out, format="wav")

        # Save transcript text
        text_path_out = speaker_dir / text_filename
        with open(text_path_out, 'w') as f:
            f.write(text)

        manifest.append({
            'audio': str(audio_path_out),
            'text': str(text_path_out),
            'transcript': text,
            'duration': duration
        })

        if (i + 1) % 10 == 0:
            print(f"Processed {i + 1}/{len(processed_segments)} clips")

    # Save manifest
    manifest_path = output_dir / f"{speaker_name}_manifest.json"
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)

    print(f"\nDataset prepared successfully!")
    print(f"  - Total clips: {len(manifest)}")
    print(f"  - Audio files: {speaker_dir}")
    print(f"  - Manifest: {manifest_path}")

    # Calculate total duration
    total_duration = sum(item['duration'] for item in manifest)
    print(f"  - Total audio duration: {total_duration / 60:.1f} minutes")

    return manifest


def create_tortoise_training_config(
    output_dir: str,
    speaker_name: str,
    epochs: int = 500,
    batch_size: int = 4
):
    """
    Create a training configuration file for Tortoise TTS.

    Note: Tortoise doesn't have a built-in fine-tuning script like some other TTS systems.
    This creates a config that can be used with community fine-tuning implementations.
    """
    config = {
        "speaker_name": speaker_name,
        "training": {
            "epochs": epochs,
            "batch_size": batch_size,
            "learning_rate": 1e-5,
            "warmup_steps": 100,
            "save_every": 50
        },
        "data": {
            "data_dir": str(Path(output_dir) / speaker_name),
            "sample_rate": 22050,
            "min_duration": 5.0,
            "max_duration": 15.0
        },
        "model": {
            "model_type": "tortoise",
            "use_deepspeed": False,
            "precision": "fp16"
        }
    }

    config_path = Path(output_dir) / f"{speaker_name}_training_config.json"
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)

    print(f"Training config saved to: {config_path}")
    return config_path


def main():
    parser = argparse.ArgumentParser(
        description='Prepare audio dataset for Tortoise TTS fine-tuning'
    )
    parser.add_argument('audio', help='Path to source audio file')
    parser.add_argument('transcript', help='Path to formatted Whisper JSON')
    parser.add_argument('--output', '-o', default='./tortoise_training',
                        help='Output directory for training data')
    parser.add_argument('--speaker', '-s', default='speaker',
                        help='Speaker name for the dataset')
    parser.add_argument('--min-duration', type=float, default=5.0,
                        help='Minimum clip duration in seconds')
    parser.add_argument('--max-duration', type=float, default=15.0,
                        help='Maximum clip duration in seconds')

    args = parser.parse_args()

    manifest = segment_audio_by_whisper(
        audio_path=args.audio,
        transcript_json_path=args.transcript,
        output_dir=args.output,
        min_duration=args.min_duration,
        max_duration=args.max_duration,
        speaker_name=args.speaker
    )

    if manifest:
        create_tortoise_training_config(
            output_dir=args.output,
            speaker_name=args.speaker
        )


if __name__ == '__main__':
    main()
