"""Hill-climbing solver for a general monoalphabetic substitution cipher.

Algorithm
---------
A substitution cipher replaces each plaintext letter with one fixed
ciphertext letter. The key is a permutation of the 26 letters: position
0 says what plaintext A becomes, position 1 says what B becomes, and so
on. There are 26! such keys (about 4 x 10^26), so trying every key is
impossible. This module searches instead:

1. ``initial_guess`` lines the ciphertext letters up by frequency with
   the English letters E, T, A, O, I, N, ... The most common ciphertext
   letter is guessed to be E, the next to be T, and so on.
2. ``hill_climb_solve`` turns that guess into a key, then repeatedly
   swaps two letters in the key. A swap is kept only when the bigram
   log-probability of the decrypted text goes up.
3. Several restarts begin from a slightly shaken copy of the frequency
   guess, so one unlucky local peak does not end the search.
4. A final pass tries every pair of letters and keeps any swap that
   still improves the score. That locks in gains the random swaps missed.

The score is the sum of log probabilities of consecutive letter pairs.
Common English pairs such as TH and HE raise the score. Pairs that
almost never occur pull it down. Spaces and punctuation are ignored
when pairs are counted, so "THE CAT" contributes TH, HE, EC, CA, AT.
"""

from __future__ import annotations

import math
import random

from cryptanalysis.english_stats import ENGLISH_FREQ
from cryptanalysis.frequency import ALPHABET, letter_counts

# Approximate percent frequencies of the most common English letter pairs.
# The exact values are rounded textbook figures. Only the ranking among
# pairs matters to the hill climber, not the third decimal place.
BIGRAM_FREQ: dict[str, float] = {
    "TH": 3.56, "HE": 3.07, "IN": 2.43, "ER": 2.05, "AN": 1.99,
    "RE": 1.85, "ON": 1.76, "AT": 1.49, "EN": 1.45, "ND": 1.35,
    "TI": 1.34, "ES": 1.34, "OR": 1.28, "TE": 1.20, "OF": 1.17,
    "ED": 1.17, "IS": 1.13, "IT": 1.12, "AL": 1.09, "AR": 1.07,
    "ST": 1.05, "TO": 1.04, "NT": 1.04, "NG": 0.95, "SE": 0.93,
    "HA": 0.93, "AS": 0.87, "OU": 0.87, "IO": 0.83, "LE": 0.83,
    "VE": 0.83, "CO": 0.79, "ME": 0.79, "DE": 0.76, "HI": 0.76,
    "RI": 0.73, "RO": 0.73, "IC": 0.70, "NE": 0.69, "EA": 0.69,
    "RA": 0.69, "CE": 0.65, "LI": 0.62, "CH": 0.60, "LL": 0.58,
    "BE": 0.58, "MA": 0.57, "SI": 0.55, "OM": 0.55, "UR": 0.54,
    "CA": 0.53, "EL": 0.52, "TA": 0.51, "LA": 0.50, "NS": 0.49,
    "DI": 0.49, "FO": 0.48, "HO": 0.47, "PE": 0.46, "EC": 0.46,
    "PR": 0.45, "NO": 0.44, "CT": 0.44, "US": 0.43, "AC": 0.43,
    "OT": 0.43, "IL": 0.42, "TR": 0.42, "LY": 0.42, "NC": 0.41,
    "ET": 0.40, "UT": 0.40, "SS": 0.40, "SO": 0.39, "RS": 0.39,
    "UN": 0.38, "LO": 0.38, "WA": 0.37, "GE": 0.37, "IE": 0.36,
    "WH": 0.36, "EE": 0.35, "WI": 0.35, "EM": 0.34, "AD": 0.34,
    "OL": 0.33, "RT": 0.33, "PO": 0.32, "WE": 0.32, "AV": 0.31,
    "AG": 0.31, "VI": 0.30, "OS": 0.30, "CI": 0.29, "DA": 0.28,
}

# Unseen pairs are rare, not impossible. A small floor stops log(0)
# and still punishes pairs that are missing from the table above.
_UNSEEN_BIGRAM_FLOOR: float = 0.01


def _build_log_table() -> dict[str, float]:
    """Pre-compute log probability for every possible letter pair.

    Listed bigrams use their table value. Every other pair uses the
    floor. Dividing by the grand total turns those weights into
    probabilities before the logarithm.
    """
    listed_total = sum(BIGRAM_FREQ.values())
    unseen_pairs = (26 * 26) - len(BIGRAM_FREQ)
    grand_total = listed_total + (_UNSEEN_BIGRAM_FLOOR * unseen_pairs)

    log_table: dict[str, float] = {}
    for first in ALPHABET:
        for second in ALPHABET:
            pair = first + second
            weight = BIGRAM_FREQ.get(pair, _UNSEEN_BIGRAM_FLOOR)
            log_table[pair] = math.log(weight / grand_total)
    return log_table


_LOG_PROB: dict[str, float] = _build_log_table()


def _letters_only(text: str) -> str:
    """Return the uppercase letters of ``text`` with everything else removed."""
    return "".join(character.upper() for character in text if character.isalpha())


def _validate_key(key: str) -> str:
    """Return ``key`` in uppercase, or raise ValueError if it is not a permutation."""
    normalised = key.upper()
    if len(normalised) != 26 or sorted(normalised) != list(ALPHABET):
        raise ValueError("key must be a 26-letter permutation of A-Z")
    return normalised


def substitution_encrypt(text: str, key: str) -> str:
    """Encrypt ``text`` with a 26-letter substitution ``key``.

    ``key[0]`` is the ciphertext letter for plaintext A, ``key[1]`` is
    the ciphertext letter for B, and so on. Case is preserved.
    Non-letters are copied through unchanged.
    """
    normalised = _validate_key(key)
    mapping = {ALPHABET[index]: normalised[index] for index in range(26)}
    output: list[str] = []
    for character in text:
        if character.isalpha():
            replacement = mapping[character.upper()]
            output.append(replacement if character.isupper() else replacement.lower())
        else:
            output.append(character)
    return "".join(output)


def substitution_decrypt(text: str, key: str) -> str:
    """Decrypt ``text`` that was encrypted with substitution ``key``.

    The encryption key maps plaintext letters to ciphertext letters.
    Inverting that map, then encrypting with the inverse, recovers
    the plaintext.
    """
    normalised = _validate_key(key)
    inverse = ["?"] * 26
    for plain_index, cipher_letter in enumerate(normalised):
        inverse[ord(cipher_letter) - ord("A")] = ALPHABET[plain_index]
    return substitution_encrypt(text, "".join(inverse))


def random_key(seed: int | None = None) -> str:
    """Return a random 26-letter permutation key.

    Pass ``seed`` when a test or a demo must produce the same key again.
    """
    generator = random.Random(seed)
    letters = list(ALPHABET)
    generator.shuffle(letters)
    return "".join(letters)


def bigram_score(text: str) -> float:
    """Sum of log probabilities of consecutive letter pairs in ``text``.

    Higher (closer to zero, since logs of probabilities are negative)
    means the letter pairs look more like English. Non-letters are
    skipped before pairs are formed.
    """
    letters = _letters_only(text)
    if len(letters) < 2:
        return 0.0
    total = 0.0
    for index in range(len(letters) - 1):
        total += _LOG_PROB[letters[index] + letters[index + 1]]
    return total


def _cipher_bigram_counts(ciphertext: str) -> dict[str, int]:
    """Count consecutive ciphertext letter pairs once, for fast rescoring."""
    letters = _letters_only(ciphertext)
    counts: dict[str, int] = {}
    for index in range(len(letters) - 1):
        pair = letters[index] + letters[index + 1]
        counts[pair] = counts.get(pair, 0) + 1
    return counts


def _score_key(key: str, cipher_bigrams: dict[str, int]) -> float:
    """Score an encryption ``key`` using pre-counted ciphertext bigrams.

    Each ciphertext pair is translated with the inverse of ``key``, then
    looked up in the English log-probability table. Doing this from the
    counts, rather than rebuilding the plaintext string, keeps the
    thousands of trial swaps cheap.
    """
    plain_for_cipher = ["?"] * 26
    for plain_index, cipher_letter in enumerate(key):
        plain_for_cipher[ord(cipher_letter) - ord("A")] = ALPHABET[plain_index]

    total = 0.0
    for pair, count in cipher_bigrams.items():
        plain_pair = (
            plain_for_cipher[ord(pair[0]) - ord("A")]
            + plain_for_cipher[ord(pair[1]) - ord("A")]
        )
        total += count * _LOG_PROB[plain_pair]
    return total


def _swap_key(key: str, first: int, second: int) -> str:
    """Return ``key`` with the letters at two indexes exchanged."""
    characters = list(key)
    characters[first], characters[second] = characters[second], characters[first]
    return "".join(characters)


def initial_guess(ciphertext: str) -> str:
    """Build a frequency-based encryption key for ``ciphertext``.

    Ciphertext letters are sorted from most common to least common.
    English letters are sorted the same way (E, then T, then A, ...).
    The most common ciphertext letter is assumed to decrypt to E, the
    next to T, and so on. Ties are broken alphabetically so the guess
    is stable. The returned string is an encryption key: index 0 is
    the ciphertext image of plaintext A.
    """
    counts = letter_counts(ciphertext)
    cipher_order = sorted(ALPHABET, key=lambda letter: (-counts[letter], letter))
    english_order = sorted(
        ALPHABET,
        key=lambda letter: (-ENGLISH_FREQ[letter], letter),
    )

    # decrypt_map[cipher_letter] = guessed plaintext letter.
    decrypt_map = {
        cipher_letter: english_letter
        for cipher_letter, english_letter in zip(cipher_order, english_order)
    }
    encrypt_key = ["?"] * 26
    for cipher_letter, plain_letter in decrypt_map.items():
        encrypt_key[ord(plain_letter) - ord("A")] = cipher_letter
    return "".join(encrypt_key)


def _polish(key: str, cipher_bigrams: dict[str, int], max_passes: int = 40) -> tuple[str, float]:
    """Try every pair swap until none of them improves the score.

    This is the same "keep the swap only if the score rises" rule as
    the random search, but it checks all 325 pairs so a near-finished
    key is not left one swap short of the best neighbour.
    """
    current = key
    current_score = _score_key(current, cipher_bigrams)
    for _ in range(max_passes):
        improved = False
        for first in range(26):
            for second in range(first + 1, 26):
                trial = _swap_key(current, first, second)
                trial_score = _score_key(trial, cipher_bigrams)
                if trial_score > current_score:
                    current = trial
                    current_score = trial_score
                    improved = True
        if not improved:
            break
    return current, current_score


def hill_climb_solve(
    ciphertext: str,
    iterations: int = 5000,
    restarts: int = 5,
    seed: int | None = None,
) -> tuple[str, str, float]:
    """Search for the substitution key and return ``(key, plaintext, score)``.

    The first restart starts from ``initial_guess``. Each later restart
    applies a few extra random swaps to that guess, then climbs again.
    Inside a restart the function proposes ``iterations`` random swaps
    and keeps a swap only when ``bigram_score`` improves. The best key
    across restarts is polished and returned.

    ``score`` is the bigram log-probability of the recovered plaintext
    (higher is better). ``seed`` makes the random swaps repeatable.
    """
    if restarts < 1:
        raise ValueError("restarts must be at least 1")
    if iterations < 0:
        raise ValueError("iterations cannot be negative")

    generator = random.Random(seed)
    starting_key = initial_guess(ciphertext)
    cipher_bigrams = _cipher_bigram_counts(ciphertext)

    best_key = starting_key
    best_score = _score_key(best_key, cipher_bigrams)

    for restart in range(restarts):
        current = starting_key
        # Shake later restarts a little so they can leave a bad peak.
        for _ in range(restart * 2):
            left, right = generator.sample(range(26), 2)
            current = _swap_key(current, left, right)
        current_score = _score_key(current, cipher_bigrams)

        for _ in range(iterations):
            left, right = generator.sample(range(26), 2)
            trial = _swap_key(current, left, right)
            trial_score = _score_key(trial, cipher_bigrams)
            if trial_score > current_score:
                current = trial
                current_score = trial_score

        if current_score > best_score:
            best_key = current
            best_score = current_score

    best_key, best_score = _polish(best_key, cipher_bigrams)
    plaintext = substitution_decrypt(ciphertext, best_key)
    # Report the public scoring function so the number matches bigram_score.
    return best_key, plaintext, bigram_score(plaintext)
