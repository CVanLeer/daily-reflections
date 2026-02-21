---
important: true
status: stable
last_reviewed: 2026-01-18
review_interval_days: 90
---

This folder contains utility scripts for data preparation, documentation enforcement, and audio processing.

## Purpose
Houses standalone scripts that support the main application:
- Documentation enforcement (`check_docs.py`)
- Audio/transcript preprocessing for TTS training
- Dataset preparation utilities

## What's inside
- `check_docs.py`: Enforces CLAUDE.md documentation standards (auto-creates stubs, validates headers)
- `phonetic_preprocessor.py`: Processes phonetic data for TTS
- `tts_preprocessor.py`: Prepares text for TTS synthesis
- `prepare_tortoise_dataset.py`: Formats audio data for Tortoise TTS training
- `format_transcript_for_tts.py`: Cleans and formats transcripts

## How it connects
- `check_docs.py` is called by pre-commit hooks and CI
- Preprocessing scripts are run manually before TTS training
- Outputs go to `output/` or `data/`

## Key workflows
1. **Check all docs**: `python scripts/check_docs.py`
2. **Check docs (strict mode)**: `python scripts/check_docs.py --strict`
3. **Prepare TTS dataset**: `python scripts/prepare_tortoise_dataset.py`

## Verification
- Run `python scripts/check_docs.py` and ensure exit 0
- Check that pre-commit hooks are installed: `pre-commit install`
