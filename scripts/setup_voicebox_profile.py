#!/usr/bin/env python3
"""
One-time setup script to create a James Earl Jones voice profile in Voicebox.

Uploads all 91 WAV/TXT training pairs from output/tortoise_training/jej/.
Idempotent — checks if profile already exists before creating.

Usage:
    cd ~/Projects/daily-reflections
    source venv/bin/activate
    python scripts/setup_voicebox_profile.py
"""

import os
import sys
import requests
from pathlib import Path

BASE_URL = os.environ.get("VOICEBOX_URL", "http://localhost:8001")
TRAINING_DIR = Path(__file__).parent.parent / "output" / "tortoise_training" / "jej"
PROFILE_NAME = "James Earl Jones"
ENV_FILE = Path(__file__).parent.parent / ".env"


def get_existing_profile():
    """Check if the JEJ profile already exists."""
    resp = requests.get(f"{BASE_URL}/profiles")
    resp.raise_for_status()
    for profile in resp.json():
        if profile["name"] == PROFILE_NAME:
            return profile
    return None


def create_profile():
    """Create a new voice profile."""
    resp = requests.post(
        f"{BASE_URL}/profiles",
        json={
            "name": PROFILE_NAME,
            "description": "James Earl Jones voice clone from To Be A Drum audiobook",
            "language": "en",
        },
    )
    resp.raise_for_status()
    return resp.json()


def add_sample(profile_id, wav_path, transcript):
    """Upload a single WAV + transcript to the profile."""
    with open(wav_path, "rb") as f:
        resp = requests.post(
            f"{BASE_URL}/profiles/{profile_id}/samples",
            files={"file": f},
            data={"reference_text": transcript},
        )
    resp.raise_for_status()
    return resp.json()


def save_profile_id_to_env(profile_id):
    """Append or update VOICEBOX_PROFILE_ID in .env file."""
    env_lines = []
    found = False

    if ENV_FILE.exists():
        with open(ENV_FILE, "r") as f:
            env_lines = f.readlines()

        for i, line in enumerate(env_lines):
            if line.startswith("VOICEBOX_PROFILE_ID="):
                env_lines[i] = f"VOICEBOX_PROFILE_ID={profile_id}\n"
                found = True
                break

    if not found:
        env_lines.append(f"VOICEBOX_PROFILE_ID={profile_id}\n")

    with open(ENV_FILE, "w") as f:
        f.writelines(env_lines)

    print(f"Saved VOICEBOX_PROFILE_ID={profile_id} to {ENV_FILE}")


def test_generation(profile_id):
    """Run a quick test generation to verify the voice works."""
    print("\nRunning test generation...")
    resp = requests.post(
        f"{BASE_URL}/generate",
        json={
            "profile_id": profile_id,
            "text": "Good morning. This is a test of the voice profile.",
            "language": "en",
            "seed": 42,
        },
        timeout=120,
    )
    resp.raise_for_status()
    gen = resp.json()
    print(f"Test generation OK — {gen.get('duration', 0):.1f}s of audio (ID: {gen['id']})")
    return True


def main():
    # 1. Health check
    print(f"Checking Voicebox server at {BASE_URL}...")
    try:
        resp = requests.get(f"{BASE_URL}/health", timeout=5)
        resp.raise_for_status()
        health = resp.json()
        print(f"Server OK — backend: {health.get('backend_type', 'unknown')}")
    except Exception as e:
        print(f"Error: Voicebox server not reachable at {BASE_URL}: {e}")
        sys.exit(1)

    # 2. Check for existing profile
    print(f"\nLooking for existing '{PROFILE_NAME}' profile...")
    profile = get_existing_profile()

    if profile:
        print(f"Profile already exists: {profile['id']}")
        profile_id = profile["id"]
    else:
        print("Creating new profile...")
        profile = create_profile()
        profile_id = profile["id"]
        print(f"Created profile: {profile_id}")

    # 3. Gather training pairs
    if not TRAINING_DIR.exists():
        print(f"Error: Training directory not found: {TRAINING_DIR}")
        sys.exit(1)

    wav_files = sorted(TRAINING_DIR.glob("jej_*.wav"))
    print(f"\nFound {len(wav_files)} WAV files in {TRAINING_DIR}")

    # 4. Upload samples
    uploaded = 0
    skipped = 0
    for wav_path in wav_files:
        txt_path = wav_path.with_suffix(".txt")
        if not txt_path.exists():
            print(f"  SKIP {wav_path.name} — no matching .txt")
            skipped += 1
            continue

        transcript = txt_path.read_text().strip()
        if not transcript:
            print(f"  SKIP {wav_path.name} — empty transcript")
            skipped += 1
            continue

        try:
            add_sample(profile_id, wav_path, transcript)
            uploaded += 1
            print(f"  [{uploaded}/{len(wav_files)}] {wav_path.name}")
        except requests.HTTPError as e:
            # If sample already exists, server may return 409
            if e.response is not None and e.response.status_code == 409:
                skipped += 1
                print(f"  SKIP {wav_path.name} — already uploaded")
            else:
                print(f"  ERROR {wav_path.name}: {e}")
                skipped += 1

    print(f"\nUpload complete: {uploaded} uploaded, {skipped} skipped")

    # 5. Save profile ID
    save_profile_id_to_env(profile_id)

    # 6. Test generation
    try:
        test_generation(profile_id)
    except Exception as e:
        print(f"Test generation failed (non-critical): {e}")

    print(f"\nDone! Profile ID: {profile_id}")
    print("You can now run: python main.py")


if __name__ == "__main__":
    main()
