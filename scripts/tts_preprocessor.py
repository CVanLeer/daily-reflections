#!/usr/bin/env python3
"""
Minimal TTS Preprocessor

Based on actual TTS documentation and best practices:
- Only fix things that are actually broken
- Use punctuation for pacing, not phonetic respellings
- Let the model do its job

Sources:
- https://help.7taps.com/en/articles/8223744-text-to-speech-pronunciation-tips
- https://knowledge.resemble.ai/what-are-best-practices-for-text-to-speech
- https://cloud.google.com/text-to-speech/docs/ssml
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


import re
from typing import Dict

# =============================================================================
# ONLY truly problematic words that TTS consistently gets wrong
# Keep this minimal - add only when you hear actual mispronunciations
# =============================================================================

WORD_FIXES: Dict[str, str] = {
    # Acronyms that should be spelled out (add hyphens for natural pacing)
    # Only add if the TTS actually mispronounces them

    # Example: "SQL" often becomes "squeal" - fix:
    # "sql": "S-Q-L",  # Uncomment if needed

    # Example: "GIF" pronunciation debate - uncomment your preference:
    # "gif": "jif",
}

# Acronyms that should be spoken as letters with hyphens for pacing
# Format: lowercase acronym -> hyphenated version
ACRONYM_LETTERIZE: Dict[str, str] = {
    # Only add acronyms the TTS mispronounces as words
    # "aws": "A-W-S",  # Uncomment if TTS says "awss"
    # "api": "A-P-I",  # Uncomment if TTS says "appee"
}

# Acronyms that should be pronounced as words (leave alone or respell)
ACRONYM_AS_WORD: Dict[str, str] = {
    # "nasa": "nasa",     # Already works
    # "scuba": "scuba",   # Already works
    # "gif": "jif",       # If you want hard pronunciation
}

# =============================================================================
# ABBREVIATION EXPANSIONS
# These are generally safe and improve clarity
# =============================================================================

ABBREVIATIONS: Dict[str, str] = {
    r'\bDr\.': 'Doctor',
    r'\bMr\.': 'Mister',
    r'\bMrs\.': 'Missus',
    r'\bMs\.': 'Ms',  # Usually fine as-is
    r'\bvs\.': 'versus',
    r'\betc\.': 'etcetera',
    r'\be\.g\.': 'for example,',
    r'\bi\.e\.': 'that is,',
    r'\bSt\.(?=\s+\d)': 'Street',  # "St. 5" -> "Street 5"
}


def process_for_tts(text: str) -> str:
    """
    Minimal preprocessing for TTS.

    Philosophy: Only fix what's actually broken.
    The model is usually smarter than we give it credit for.
    """
    result = text

    # 1. Expand abbreviations (these are generally safe)
    for pattern, replacement in ABBREVIATIONS.items():
        result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)

    # 2. Fix specific problem words (keep this list small!)
    for word, fix in WORD_FIXES.items():
        result = re.sub(rf'\b{word}\b', fix, result, flags=re.IGNORECASE)

    # 3. Letterize specific acronyms that get mispronounced
    for acronym, hyphenated in ACRONYM_LETTERIZE.items():
        result = re.sub(rf'\b{acronym}\b', hyphenated, result, flags=re.IGNORECASE)

    # 4. Clean up multiple spaces/weird punctuation
    result = re.sub(r'\s+', ' ', result)
    result = re.sub(r'\.{4,}', '...', result)  # Normalize ellipsis

    return result.strip()


def test_with_model(text: str, processed: str):
    """
    Helper to compare original vs processed.
    Run the TTS on both and listen for differences.
    """
    print("=" * 50)
    print("ORIGINAL:")
    print(f"  {text}")
    print("\nPROCESSED:")
    print(f"  {processed}")
    print("=" * 50)


# =============================================================================
# USAGE GUIDE
# =============================================================================
"""
HOW TO USE THIS:

1. Start with the preprocessor doing almost nothing
2. Generate TTS audio
3. Listen for mispronunciations
4. Add ONLY those specific words to the dictionaries above
5. Test again

Example workflow:

    from tts_preprocessor import process_for_tts

    text = "The AWS API uses SQL databases"
    processed = process_for_tts(text)

    # Generate TTS with processed text
    tts.tts_to_file(processed, ...)

    # Listen to output
    # If "AWS" sounds like "awss", add to ACRONYM_LETTERIZE:
    #   "aws": "A-W-S",
    #
    # If "SQL" sounds like "squeal", add to WORD_FIXES:
    #   "sql": "sequel",  # or "S-Q-L" for letters


PUNCTUATION TIPS (use in your source text):

    Short pause:    comma (,) or hyphen (-)
    Medium pause:   semicolon (;)
    Long pause:     period (.)
    Dramatic:       ellipsis (...)

    Example:
    "Welcome... to your daily reflection."
    "Today - take a moment - to breathe."
"""

if __name__ == "__main__":
    # Demo
    test_cases = [
        "Dr. Smith uses the AWS API with SQL databases.",
        "The GIF shows our GUI, etc.",
        "I work in Tech... it's challenging, but rewarding.",
        "NASA launched in 1958, i.e., during the Space Race.",
    ]

    print("TTS Preprocessor Demo")
    print("=" * 50)
    print("Note: This preprocessor is intentionally minimal.")
    print("Add words to the dictionaries only when TTS mispronounces them.")
    print("=" * 50)

    for text in test_cases:
        processed = process_for_tts(text)
        print(f"\nIN:  {text}")
        print(f"OUT: {processed}")
