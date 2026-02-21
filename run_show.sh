#!/bin/bash

# Navigate to directory
cd "$(dirname "$0")"

# Activate venv
source venv/bin/activate

# Run the main script with any arguments passed to this shell script
python main.py "$@"

# Optional: Copy to iCloud (Uncomment and update path if you want auto-sync)
# cp output/*.wav ~/Library/Mobile\ Documents/com~apple~CloudDocs/Reflections/
