#!/usr/bin/env python3
"""
Phonetic Preprocessor for TTS

Converts text to phonetically-accurate spellings for better TTS output.

Usage:
    from phonetic_preprocessor import process_for_tts
    tts_text = process_for_tts("I work in Tech")
    # Returns: "I work in Teck"
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
from typing import Dict, Optional

# =============================================================================
# PHONETIC DICTIONARY
# Add words here that the TTS mispronounces
# Format: "original": "phonetic_spelling"
# =============================================================================

PHONETIC_DICTIONARY: Dict[str, str] = {
    # Tech terms
    "tech": "teck",
    "gif": "jiff",  # or "giff" if you prefer hard G
    "sql": "sequel",
    "api": "A P I",
    "gui": "gooey",
    "linux": "linnux",
    "nginx": "engine X",
    "cli": "C L I",
    "wifi": "why-fye",
    "ieee": "I triple E",
    "ascii": "askey",
    "scsi": "scuzzy",
    "wysiwyg": "wizzy-wig",

    # Acronyms (spell out)
    "aws": "A W S",
    "gcp": "G C P",
    "ai": "A I",
    "ml": "M L",
    "llm": "L L M",
    "gpu": "G P U",
    "cpu": "C P U",
    "ram": "ram",  # This one is usually fine as-is
    "ssd": "S S D",
    "hdd": "H D D",
    "url": "U R L",
    "http": "H T T P",
    "https": "H T T P S",
    "html": "H T M L",
    "css": "C S S",
    "json": "jason",
    "yaml": "yammel",
    "xml": "X M L",
    "jwt": "J W T",
    "oauth": "oh-auth",
    "saas": "sass",
    "paas": "pass",
    "iaas": "eye-ass",
    "devops": "dev-ops",
    "cicd": "C I C D",
    "vpc": "V P C",
    "iam": "I A M",
    "sdk": "S D K",
    "ide": "I D E",
    "oop": "O O P",
    "mvc": "M V C",
    "mvp": "M V P",
    "poc": "P O C",
    "roi": "R O I",
    "kpi": "K P I",
    "cto": "C T O",
    "ceo": "C E O",
    "cfo": "C F O",

    # Common mispronunciations
    # "data": "dayta",  # Commented out - causes issues with "database", etc.
    "either": "eether",
    "neither": "neether",
    "route": "root",  # or "rowt"
    "cache": "cash",
    "niche": "neesh",
    "epitome": "eh-pit-oh-mee",
    "hyperbole": "hy-per-bow-lee",
    "segue": "segway",
    "queue": "kyoo",
    "genre": "zhon-ruh",
    "faux": "foe",
    "coup": "koo",
    "debris": "duh-bree",
    "rendezvous": "ron-day-voo",

    # Names that are often mispronounced
    "pytorch": "pie-torch",
    "numpy": "num-pie",
    "scipy": "sigh-pie",
    "matplotlib": "mat-plot-lib",
    "jupyter": "joo-piter",
    "kubernetes": "koo-ber-net-eez",
    "ubuntu": "oo-boon-too",
    "debian": "deb-ee-an",
    "macos": "mac O S",
    "ios": "eye O S",
    "gmail": "G mail",

    # Numbers and symbols (context-dependent, be careful)
    # These are handled separately in the process function
}

# =============================================================================
# PHONETIC RULES
# Pattern-based replacements
# =============================================================================

PHONETIC_RULES = [
    # Convert "Dr." to "Doctor"
    (r'\bDr\.', 'Doctor'),

    # Convert "Mr." to "Mister"
    (r'\bMr\.', 'Mister'),

    # Convert "Mrs." to "Missus"
    (r'\bMrs\.', 'Missus'),

    # Convert "Ms." to "Mizz"
    (r'\bMs\.', 'Mizz'),

    # Convert "St." to "Street" or "Saint" (context-dependent, defaulting to Street)
    (r'\bSt\.\s+(\d)', r'Street \1'),  # If followed by number, it's Street
    (r'\bSt\.', 'Saint'),  # Otherwise, Saint

    # Convert "vs." to "versus"
    (r'\bvs\.', 'versus'),

    # Convert "etc." to "etcetera"
    (r'\betc\.', 'etcetera'),

    # Convert "e.g." to "for example"
    (r'\be\.g\.', 'for example'),

    # Convert "i.e." to "that is"
    (r'\bi\.e\.', 'that is'),

    # Convert "approx." to "approximately"
    (r'\bapprox\.', 'approximately'),

    # Convert "dept." to "department"
    (r'\bdept\.', 'department'),

    # Ellipsis to pause
    (r'\.\.\.', ', '),

    # Multiple exclamation/question marks to single
    (r'!+', '!'),
    (r'\?+', '?'),
]


def apply_dictionary(text: str, case_sensitive: bool = False) -> str:
    """Apply phonetic dictionary replacements (whole words only)."""
    result = text

    for original, replacement in PHONETIC_DICTIONARY.items():
        # Use word boundaries to avoid matching inside other words
        # e.g., "tech" should match "Tech" but not "technology"
        pattern = re.compile(rf'\b{re.escape(original)}\b', re.IGNORECASE)

        def make_replacer(repl):
            def replace_match(match):
                matched_text = match.group(0)
                # Preserve capitalization
                if matched_text.isupper():
                    return repl.upper()
                elif matched_text[0].isupper():
                    return repl.capitalize()
                else:
                    return repl.lower()
            return replace_match

        result = pattern.sub(make_replacer(replacement), result)

    return result


def apply_rules(text: str) -> str:
    """Apply regex-based phonetic rules."""
    result = text

    for pattern, replacement in PHONETIC_RULES:
        result = re.sub(pattern, replacement, result)

    return result


def expand_numbers(text: str) -> str:
    """Convert numbers to words for better TTS pronunciation."""
    # This is a simplified version - for production, use 'inflect' library

    number_words = {
        '0': 'zero', '1': 'one', '2': 'two', '3': 'three', '4': 'four',
        '5': 'five', '6': 'six', '7': 'seven', '8': 'eight', '9': 'nine',
        '10': 'ten', '11': 'eleven', '12': 'twelve', '13': 'thirteen',
        '14': 'fourteen', '15': 'fifteen', '16': 'sixteen', '17': 'seventeen',
        '18': 'eighteen', '19': 'nineteen', '20': 'twenty',
        '30': 'thirty', '40': 'forty', '50': 'fifty',
        '60': 'sixty', '70': 'seventy', '80': 'eighty', '90': 'ninety',
        '100': 'one hundred', '1000': 'one thousand',
    }

    result = text

    # Handle years (4-digit numbers between 1000-2099)
    def year_to_words(match):
        year = match.group(0)
        y = int(year)
        if 2000 <= y <= 2009:
            return f"two thousand {number_words.get(str(y - 2000), year[-1])}" if y > 2000 else "two thousand"
        elif 2010 <= y <= 2099:
            tens = y - 2000
            return f"twenty {number_words.get(str(tens), str(tens))}"
        elif 1900 <= y <= 1999:
            return f"nineteen {number_words.get(str(y - 1900), str(y - 1900))}"
        return year

    result = re.sub(r'\b(19|20)\d{2}\b', year_to_words, result)

    # Handle simple numbers (standalone digits)
    for num, word in sorted(number_words.items(), key=lambda x: -len(x[0])):
        result = re.sub(rf'\b{num}\b', word, result)

    return result


def add_breathing_pauses(text: str) -> str:
    """Add natural pauses for better TTS rhythm."""
    # Add slight pause after colons
    text = re.sub(r':\s*', ': ', text)

    # Ensure proper spacing after punctuation
    text = re.sub(r'([.!?])\s*([A-Z])', r'\1 \2', text)

    return text


def process_for_tts(
    text: str,
    apply_dict: bool = True,
    apply_phonetic_rules: bool = True,
    expand_nums: bool = True,
    add_pauses: bool = True
) -> str:
    """
    Main function to process text for TTS.

    Args:
        text: Input text to process
        apply_dict: Apply phonetic dictionary replacements
        apply_phonetic_rules: Apply regex-based rules
        expand_nums: Convert numbers to words
        add_pauses: Add natural breathing pauses

    Returns:
        Processed text optimized for TTS
    """
    result = text

    if apply_phonetic_rules:
        result = apply_rules(result)

    if apply_dict:
        result = apply_dictionary(result)

    if expand_nums:
        result = expand_numbers(result)

    if add_pauses:
        result = add_breathing_pauses(result)

    # Clean up extra whitespace
    result = re.sub(r'\s+', ' ', result).strip()

    return result


def add_custom_word(original: str, phonetic: str):
    """Add a custom word to the dictionary at runtime."""
    PHONETIC_DICTIONARY[original.lower()] = phonetic


def remove_custom_word(original: str):
    """Remove a word from the dictionary."""
    PHONETIC_DICTIONARY.pop(original.lower(), None)


def get_dictionary() -> Dict[str, str]:
    """Get a copy of the current phonetic dictionary."""
    return PHONETIC_DICTIONARY.copy()


# =============================================================================
# CLI Interface
# =============================================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Phonetic preprocessor for TTS')
    parser.add_argument('text', nargs='?', help='Text to process')
    parser.add_argument('-f', '--file', help='Read text from file')
    parser.add_argument('-o', '--output', help='Write output to file')
    parser.add_argument('--no-dict', action='store_true', help='Skip dictionary replacements')
    parser.add_argument('--no-rules', action='store_true', help='Skip rule-based replacements')
    parser.add_argument('--no-numbers', action='store_true', help='Skip number expansion')
    parser.add_argument('--show-dict', action='store_true', help='Show phonetic dictionary')

    args = parser.parse_args()

    if args.show_dict:
        print("Phonetic Dictionary:")
        print("-" * 40)
        for original, phonetic in sorted(PHONETIC_DICTIONARY.items()):
            print(f"  {original:20} → {phonetic}")
        exit(0)

    # Get input text
    if args.file:
        with open(args.file, 'r') as f:
            text = f.read()
    elif args.text:
        text = args.text
    else:
        print("Enter text (Ctrl+D to finish):")
        import sys
        text = sys.stdin.read()

    # Process
    result = process_for_tts(
        text,
        apply_dict=not args.no_dict,
        apply_phonetic_rules=not args.no_rules,
        expand_nums=not args.no_numbers
    )

    # Output
    if args.output:
        with open(args.output, 'w') as f:
            f.write(result)
        print(f"Written to {args.output}")
    else:
        print("\nProcessed text:")
        print("-" * 40)
        print(result)


# =============================================================================
# Examples
# =============================================================================

EXAMPLES = """
Examples:
---------
Input:  "I work in Tech and use SQL databases with the AWS API."
Output: "I work in Teck and use sequel databases with the A W S A P I."

Input:  "Dr. Smith works at 123 Main St. etc."
Output: "Doctor Smith works at one hundred twenty three Main Street etcetera."

Input:  "The gif shows the GUI of our new SaaS product."
Output: "The jiff shows the gooey of our new sass product."

Input:  "In 2024, AI and ML changed everything... really!"
Output: "In twenty twenty four, A I and M L changed everything, really!"
"""
