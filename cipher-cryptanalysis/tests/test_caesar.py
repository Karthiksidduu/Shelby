"""Tests for Caesar encryption, decryption, and brute force."""

from cryptanalysis.caesar import brute_force, caesar_decrypt, caesar_encrypt


def test_encrypt_decrypt_round_trip() -> None:
    """Encrypting and then decrypting with the same key returns the original text."""
    original = "Attack at dawn."
    for shift in range(26):
        encrypted = caesar_encrypt(original, shift)
        assert caesar_decrypt(encrypted, shift) == original


def test_case_and_punctuation_are_preserved() -> None:
    """Letters keep their case, and spaces, digits, and punctuation stay put."""
    original = "Hello, World! 123"
    encrypted = caesar_encrypt(original, 3)
    assert encrypted == "Khoor, Zruog! 123"
    assert caesar_decrypt(encrypted, 3) == original


def test_khoor_zruog_key_three_is_hello_world() -> None:
    """The classroom example decrypts with key 3."""
    assert caesar_decrypt("KHOOR ZRUOG", 3) == "HELLO WORLD"


def test_brute_force_returns_25_results() -> None:
    """Keys 1 through 25 are the only candidates, in that order."""
    results = brute_force("KHOOR ZRUOG")
    assert len(results) == 25
    assert [key for key, _plaintext in results] == list(range(1, 26))
    assert results[2] == (3, "HELLO WORLD")
