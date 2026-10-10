"""Frequency analysis and scoring for Caesar cipher candidates.

A Caesar cipher only rotates the alphabet, so the letter-frequency
fingerprint of English survives. These functions measure that
fingerprint and rank the 25 possible keys.
"""

from __future__ import annotations

import math
import re
from typing import TypedDict

from cryptanalysis.caesar import brute_force
from cryptanalysis.english_stats import COMMON_WORDS, ENGLISH_FREQ

# Lookup set so dictionary checks are a single hash lookup per word.
_COMMON_WORD_SET: set[str] = set(COMMON_WORDS)

# The 26 letters, in alphabet order. Charts and counts always use this order.
ALPHABET: str = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"


class CaesarCandidate(TypedDict):
    """One decrypted Caesar candidate, plus the scores used to rank it."""

    rank: int
    key: int
    plaintext: str
    chi_squared: float
    word_score: float


def letter_counts(text: str) -> dict[str, int]:
    """Count A-Z letters in ``text``, ignoring case and non-letters.

    Every letter from A to Z is present in the result, even when its
    count is zero. That keeps later percentage and chi-squared code
    from having to handle missing keys.
    """
    counts: dict[str, int] = {letter: 0 for letter in ALPHABET}
    for character in text.upper():
        if character in counts:
            counts[character] += 1
    return counts


def letter_percentages(text: str) -> dict[str, float]:
    """Return A-Z letter frequencies in ``text`` as percentages.

    The scale matches ``ENGLISH_FREQ``: 12.7 means "12.7 percent of
    the letters", not a fraction between 0 and 1. An empty text
    returns 0 for every letter.
    """
    counts = letter_counts(text)
    total = sum(counts.values())
    if total == 0:
        return {letter: 0.0 for letter in ALPHABET}
    return {letter: (counts[letter] / total) * 100.0 for letter in ALPHABET}


def chi_squared(text: str) -> float:
    """Chi-squared distance between ``text`` and standard English.

    For each letter the formula is ``(observed - expected) ** 2 / expected``.
    ``observed`` is the raw count. ``expected`` is the English percentage
    scaled to the same number of letters. A lower total means the text
    looks more like English. Text with no letters returns infinity so
    it sorts to the bottom of a ranking.
    """
    counts = letter_counts(text)
    total = sum(counts.values())
    if total == 0:
        return math.inf

    # Normalise in case the published percentages are a hair off 100.
    frequency_total = sum(ENGLISH_FREQ.values())
    statistic = 0.0
    for letter in ALPHABET:
        observed = counts[letter]
        expected = (ENGLISH_FREQ[letter] / frequency_total) * total
        statistic += (observed - expected) ** 2 / expected
    return statistic


def dictionary_score(text: str) -> float:
    """Fraction of words in ``text`` that are in the common-word list.

    Words are runs of letters. Case and surrounding punctuation are
    ignored. The result is between 0 and 1. Text with no words scores 0.
    """
    words = re.findall(r"[A-Za-z]+", text.lower())
    if not words:
        return 0.0
    hits = sum(1 for word in words if word in _COMMON_WORD_SET)
    return hits / len(words)


def rank_caesar_keys(ciphertext: str) -> list[CaesarCandidate]:
    """Rank all 25 Caesar keys. The best candidate has rank 1.

    Each candidate is decrypted, then scored with chi-squared (lower
    is better) and with the common-word fraction (higher is better).
    Sort order is chi-squared first. The word score only breaks ties,
    which matters for very short samples such as "HELLO WORLD".
    """
    candidates: list[CaesarCandidate] = []
    for key, plaintext in brute_force(ciphertext):
        candidates.append(
            {
                "rank": 0,
                "key": key,
                "plaintext": plaintext,
                "chi_squared": chi_squared(plaintext),
                "word_score": dictionary_score(plaintext),
            }
        )

    candidates.sort(key=lambda row: (row["chi_squared"], -row["word_score"], row["key"]))
    for index, row in enumerate(candidates, start=1):
        row["rank"] = index
    return candidates


def confidence(ranked: list[CaesarCandidate]) -> float:
    """Score from 0 to 100 for how clearly the best key beats the runner-up.

    The gap is ``(second - best) / second``. A big gap means the best
    chi-squared value is much smaller than the next one, so the result
    is trustworthy. Equal scores, missing rows, or infinite scores
    (no letters) produce 0.
    """
    if len(ranked) < 2:
        return 0.0

    best = float(ranked[0]["chi_squared"])
    second = float(ranked[1]["chi_squared"])
    if math.isinf(best) or math.isinf(second) or second == 0:
        return 0.0

    gap = (second - best) / second * 100.0
    return max(0.0, min(100.0, gap))


def is_text_too_short(text: str, minimum: int = 25) -> bool:
    """Return True when ``text`` has fewer than ``minimum`` letters.

    Frequency counts from a handful of letters are mostly noise, so
    callers show a warning instead of trusting the top key blindly.
    """
    letter_total = sum(letter_counts(text).values())
    return letter_total < minimum
