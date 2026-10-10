"""Tests for the monoalphabetic substitution solver."""

from cryptanalysis.substitution import hill_climb_solve, substitution_encrypt, random_key

# About 300 letters of ordinary English, written for this test.
ENGLISH_PASSAGE = (
    "In the history of secret writing a substitution cipher replaces every letter "
    "with another letter and then keeps that choice for the whole message. English "
    "still shows through because the letter e remains common and the pair th keeps "
    "returning in words such as the that and with. A student can count those letters "
    "line them up with the usual English order and then swap two guesses whenever "
    "the text begins to look like real words. With a few hundred letters the pattern "
    "is strong enough that the original message comes back almost intact which is "
    "why this classical cipher is no longer a serious way to protect information."
)


def _letter_accuracy(original: str, recovered: str) -> float:
    """Fraction of alphabetic characters that match, ignoring case."""
    pairs = [
        (left.upper(), right.upper())
        for left, right in zip(original, recovered)
        if left.isalpha()
    ]
    correct = sum(left == right for left, right in pairs)
    return correct / len(pairs)


def test_solver_recovers_at_least_ninety_percent_of_letters() -> None:
    """A few hundred English letters are enough for the hill climber."""
    letter_count = sum(1 for character in ENGLISH_PASSAGE if character.isalpha())
    assert letter_count >= 300

    key = random_key(seed=21)
    ciphertext = substitution_encrypt(ENGLISH_PASSAGE, key)
    _found_key, plaintext, _score = hill_climb_solve(
        ciphertext,
        iterations=5000,
        restarts=5,
        seed=21,
    )
    assert _letter_accuracy(ENGLISH_PASSAGE, plaintext) >= 0.90
