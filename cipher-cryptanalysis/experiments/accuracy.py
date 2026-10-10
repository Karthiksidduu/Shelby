"""Print Caesar recovery success rates for several ciphertext lengths.

Run from the project directory:

    python experiments/accuracy.py

Each trial encrypts an English window with a random shift, then asks the
ranker for its best key. Short windows fail more often because a handful
of letter counts does not look like the English frequency table yet.
"""

from __future__ import annotations

import random
import sys
from pathlib import Path

# Allow `python experiments/accuracy.py` to import the package, which lives
# in the project root rather than in this folder.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from cryptanalysis.caesar import caesar_encrypt
from cryptanalysis.frequency import rank_caesar_keys

# One long English passage. Windows are cut from it so every length is
# real prose rather than a repeated single word.
PASSAGE = (
    "During the afternoon lab the class compared ciphers that hide a message "
    "one letter at a time. A Caesar cipher only slides the alphabet, so twenty "
    "five guesses are enough to read it once the text is long. The students "
    "wrote notes about ships, weather, markets, and the walk back across campus. "
    "They observed that very short notes still looked strange after every shift, "
    "while a full paragraph settled quickly onto the sentence they had typed. "
    "That is the practical limit of frequency analysis: the English pattern has "
    "to be given enough letters to show itself. Modern ciphers avoid the problem "
    "by mixing each letter with many others, so counting letters no longer helps."
)

LENGTHS: tuple[int, ...] = (10, 20, 50, 100, 200)
TRIALS: int = 30


def window_with_letter_count(text: str, start: int, letter_count: int) -> str:
    """Return a slice of ``text`` that contains exactly ``letter_count`` letters.

    The slice keeps the spaces and punctuation that sit among those letters,
    because that is what a real ciphertext looks like.
    """
    seen = 0
    for end in range(start, len(text)):
        if text[end].isalpha():
            seen += 1
            if seen == letter_count:
                return text[start : end + 1]
    raise ValueError(f"Not enough letters after index {start} to take {letter_count}.")


def success_rate(length: int, trials: int, generator: random.Random) -> float:
    """Fraction of random windows of ``length`` letters whose best key is correct."""
    # Last index where a window of this many letters can still start.
    letter_positions = [index for index, character in enumerate(PASSAGE) if character.isalpha()]
    if len(letter_positions) < length:
        raise ValueError(f"Passage is shorter than {length} letters.")
    last_start = letter_positions[-length]

    successes = 0
    for _ in range(trials):
        start = generator.randint(0, last_start)
        sample = window_with_letter_count(PASSAGE, start, length)
        shift = generator.randint(1, 25)
        ciphertext = caesar_encrypt(sample, shift)
        best_key = rank_caesar_keys(ciphertext)[0]["key"]
        if best_key == shift:
            successes += 1
    return successes / trials


def main() -> None:
    """Print one success rate for each requested ciphertext length."""
    generator = random.Random(4)
    print("Caesar cipher recovery by ciphertext length")
    print(f"{TRIALS} random windows and shifts at each length")
    print()
    for length in LENGTHS:
        rate = success_rate(length, TRIALS, generator)
        print(f"Length {length:3d} letters: {rate:6.1%} success")


if __name__ == "__main__":
    main()
