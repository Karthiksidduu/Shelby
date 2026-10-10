"""Tests for frequency scoring and Caesar key ranking."""

import random

from cryptanalysis.caesar import caesar_encrypt
from cryptanalysis.frequency import chi_squared, is_text_too_short, rank_caesar_keys

# More than 100 letters, written for this project (not copied from a book).
ENGLISH_PARAGRAPH = (
    "The students gathered in the lab to see why a simple shift cipher fails. "
    "They typed a long English sentence, hid it with a secret shift, and then "
    "asked the program to try every possible key. The correct sentence was the "
    "one whose letters behaved like ordinary English."
)


def test_best_ranked_key_matches_the_shift_on_a_long_paragraph() -> None:
    """A paragraph of 100 or more letters is ranked back to the true key."""
    letter_count = sum(1 for character in ENGLISH_PARAGRAPH if character.isalpha())
    assert letter_count >= 100

    shift = 11
    ciphertext = caesar_encrypt(ENGLISH_PARAGRAPH, shift)
    ranked = rank_caesar_keys(ciphertext)
    assert ranked[0]["rank"] == 1
    assert ranked[0]["key"] == shift
    assert ranked[0]["plaintext"] == ENGLISH_PARAGRAPH


def test_short_text_triggers_the_length_warning() -> None:
    """Fewer than 25 letters is too short. 25 letters is just long enough."""
    assert is_text_too_short("KHOOR ZRUOG")
    assert is_text_too_short("abc", minimum=25)
    assert not is_text_too_short("a" * 25)
    assert not is_text_too_short(ENGLISH_PARAGRAPH)


def test_chi_squared_is_lower_for_english_than_for_random_letters() -> None:
    """Real English sits closer to the frequency table than a random string."""
    english = ENGLISH_PARAGRAPH
    generator = random.Random(7)
    random_letters = "".join(
        generator.choice("abcdefghijklmnopqrstuvwxyz")
        for _ in range(sum(1 for character in english if character.isalpha()))
    )
    assert chi_squared(english) < chi_squared(random_letters)
