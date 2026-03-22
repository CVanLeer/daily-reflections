#!/bin/bash
# Play the latest daily reflection audio on the Echo Bluetooth speaker.
# Reconnects Bluetooth if needed, switches audio output, plays the show.

AUDIO_DIR="$HOME/Projects/daily-reflections/output/audio"
ECHO_MAC="08-91-a3-aa-1d-00"
ECHO_NAME="Echo-0NR"
LOG="$HOME/Library/Logs/daily-reflections-playback.log"
VOLUME="${1:-0.8}"  # Default volume 0.8, override with first arg

log() { echo "$(date '+%Y-%m-%d %H:%M:%S') $1" >> "$LOG"; }

log "--- Playback starting ---"

# Find the latest audio file
LATEST=$(ls -t "$AUDIO_DIR"/daily_reflection_*.mp3 "$AUDIO_DIR"/daily_reflection_*.wav 2>/dev/null | head -1)

if [ -z "$LATEST" ]; then
    log "ERROR: No audio files found in $AUDIO_DIR"
    exit 1
fi

log "Playing: $LATEST"

# Ensure Echo is connected via Bluetooth
if ! /opt/homebrew/bin/blueutil --is-connected "$ECHO_MAC" 2>/dev/null | grep -q 1; then
    log "Echo not connected, attempting reconnect..."
    /opt/homebrew/bin/blueutil --connect "$ECHO_MAC" 2>> "$LOG"
    sleep 3

    if ! /opt/homebrew/bin/blueutil --is-connected "$ECHO_MAC" 2>/dev/null | grep -q 1; then
        log "ERROR: Could not connect to Echo speaker"
        exit 1
    fi
    log "Echo reconnected"
fi

# Switch audio output to Echo
/opt/homebrew/bin/SwitchAudioSource -s "$ECHO_NAME" >> "$LOG" 2>&1
log "Audio output set to $ECHO_NAME"

# Brief pause for audio route to settle
sleep 2

# Play the show
afplay -v "$VOLUME" "$LATEST" >> "$LOG" 2>&1
EXIT_CODE=$?

# Switch audio back to Mac mini speakers
/opt/homebrew/bin/SwitchAudioSource -s "Mac mini Speakers" >> "$LOG" 2>&1

if [ $EXIT_CODE -eq 0 ]; then
    log "Playback complete"
else
    log "ERROR: afplay exited with code $EXIT_CODE"
fi
