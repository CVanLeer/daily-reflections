#!/usr/bin/env python3
"""
Format Whisper transcription for TTS fine-tuning.

Converts numbers to words, handles special cases for natural speech,
and prepares the data for Tortoise TTS training.
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
import re
from pathlib import Path
from num2words import num2words


def number_to_words(match):
    """Convert a number match to words."""
    num_str = match.group(0)

    # Remove commas from numbers like 1,000
    num_str_clean = num_str.replace(',', '')

    try:
        num = float(num_str_clean) if '.' in num_str_clean else int(num_str_clean)

        # Handle years specially (1900-2099)
        if isinstance(num, int) and 1900 <= num <= 2099:
            # Read as year: 2026 -> "twenty twenty-six"
            century = num // 100
            year_part = num % 100
            if year_part == 0:
                return num2words(century) + " hundred"
            elif year_part < 10:
                return num2words(century) + " oh " + num2words(year_part)
            else:
                return num2words(century) + " " + num2words(year_part)

        # Handle ordinals (1st, 2nd, 3rd, etc.) - handled separately

        # Regular numbers
        return num2words(num)

    except (ValueError, OverflowError):
        return num_str  # Return original if conversion fails


def format_ordinal(match):
    """Convert ordinal numbers like 1st, 2nd, 3rd to words."""
    num = int(match.group(1))
    return num2words(num, to='ordinal')


def format_transcript(text):
    """
    Format transcript text for TTS training.

    - Converts numbers to words
    - Handles ordinals (1st -> first)
    - Normalizes whitespace
    - Keeps punctuation for natural speech patterns
    """
    # Handle ordinals first (1st, 2nd, 3rd, 21st, etc.)
    text = re.sub(r'(\d+)(?:st|nd|rd|th)\b', format_ordinal, text, flags=re.IGNORECASE)

    # Handle time formats (3:30 -> three thirty)
    def time_to_words(match):
        hour = int(match.group(1))
        minute = int(match.group(2))
        if minute == 0:
            return num2words(hour) + " o'clock"
        elif minute < 10:
            return num2words(hour) + " oh " + num2words(minute)
        else:
            return num2words(hour) + " " + num2words(minute)

    text = re.sub(r'\b(\d{1,2}):(\d{2})\b', time_to_words, text)

    # Handle percentages (50% -> fifty percent)
    text = re.sub(r'(\d+(?:\.\d+)?)\s*%', lambda m: num2words(float(m.group(1))) + " percent", text)

    # Handle currency ($100 -> one hundred dollars)
    def currency_to_words(match):
        num = float(match.group(1).replace(',', ''))
        if num == int(num):
            return num2words(int(num)) + " dollars"
        else:
            dollars = int(num)
            cents = int(round((num - dollars) * 100))
            if cents == 0:
                return num2words(dollars) + " dollars"
            else:
                return num2words(dollars) + " dollars and " + num2words(cents) + " cents"

    text = re.sub(r'\$(\d+(?:,\d{3})*(?:\.\d{2})?)', currency_to_words, text)

    # Handle all remaining numbers
    text = re.sub(r'\b\d+(?:,\d{3})*(?:\.\d+)?\b', number_to_words, text)

    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text).strip()

    return text


def process_whisper_output(input_path, output_text_path, output_json_path=None):
    """
    Process Whisper JSON output and create formatted transcript.

    Args:
        input_path: Path to Whisper JSON output
        output_text_path: Path to save formatted plain text
        output_json_path: Optional path to save formatted JSON with timestamps
    """
    input_path = Path(input_path)
    output_text_path = Path(output_text_path)

    with open(input_path, 'r') as f:
        whisper_data = json.load(f)

    # Get the full transcript text
    raw_text = whisper_data.get('text', '')

    # Format the full transcript
    formatted_text = format_transcript(raw_text)

    # Save plain text version
    with open(output_text_path, 'w') as f:
        f.write(formatted_text)

    print(f"Formatted transcript saved to: {output_text_path}")

    # If JSON output requested and we have segments with word timestamps
    if output_json_path and 'segments' in whisper_data:
        output_json_path = Path(output_json_path)
        formatted_segments = []

        for segment in whisper_data['segments']:
            formatted_segment = {
                'id': segment.get('id'),
                'start': segment.get('start'),
                'end': segment.get('end'),
                'text': format_transcript(segment.get('text', '')),
                'original_text': segment.get('text', '')
            }

            # Include word-level timestamps if available
            if 'words' in segment:
                formatted_segment['words'] = []
                for word in segment['words']:
                    formatted_segment['words'].append({
                        'word': format_transcript(word.get('word', '')),
                        'original_word': word.get('word', ''),
                        'start': word.get('start'),
                        'end': word.get('end')
                    })

            formatted_segments.append(formatted_segment)

        formatted_data = {
            'text': formatted_text,
            'original_text': raw_text,
            'segments': formatted_segments,
            'language': whisper_data.get('language', 'en')
        }

        with open(output_json_path, 'w') as f:
            json.dump(formatted_data, f, indent=2)

        print(f"Formatted JSON with timestamps saved to: {output_json_path}")

    return formatted_text


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Format Whisper transcription for TTS fine-tuning')
    parser.add_argument('input', help='Path to Whisper JSON output')
    parser.add_argument('--output-text', '-t', default=None, help='Output plain text path')
    parser.add_argument('--output-json', '-j', default=None, help='Output JSON path with timestamps')

    args = parser.parse_args()

    input_path = Path(args.input)
    output_text = args.output_text or input_path.with_suffix('.formatted.txt')
    output_json = args.output_json

    process_whisper_output(input_path, output_text, output_json)


if __name__ == '__main__':
    main()
