"""Caesar cipher encryption, decryption, and brute-force search.

Convention used everywhere in this project
------------------------------------------
"Key k" means each plaintext letter was shifted *forward* by k positions
to produce the ciphertext. Decryption therefore shifts *backward* by k.

Example: "HELLO WORLD" encrypted with key 3 becomes "KHOOR ZRUOG".
Decrypting "KHOOR ZRUOG" with key 3 returns "HELLO WORLD".
Key 1 returns "JGNNQ YQTNF", and key 2 returns "IFMMP XPSME".
"""

from __future__ import annotations


def _shift_letter(character: str, shift: int) -> str:
    """Shift one character by ``shift`` places, preserving non-letters.

    Uppercase and lowercase are shifted inside their own alphabet so
    "Hello" stays "Hello" in shape. Digits, spaces, and punctuation
    are returned unchanged. The shift is wrapped with modulo 26, so
    a shift of 27 is the same as a shift of 1.
    """
    if character.isupper():
        alphabet_start = ord("A")
        offset = ord(character) - alphabet_start
        return chr(alphabet_start + (offset + shift) % 26)
    if character.islower():
        alphabet_start = ord("a")
        offset = ord(character) - alphabet_start
        return chr(alphabet_start + (offset + shift) % 26)
    return character


def caesar_encrypt(text: str, shift: int) -> str:
    """Encrypt ``text`` by shifting every letter forward by ``shift``.

    Only the letters A-Z and a-z move. Case, spaces, digits, and
    punctuation are preserved.
    """
    return "".join(_shift_letter(character, shift) for character in text)


def caesar_decrypt(text: str, shift: int) -> str:
    """Decrypt ``text`` that was encrypted with Caesar key ``shift``.

    This is encryption with the opposite shift. Key 3 decrypts by
    shifting each letter back three places.
    """
    return caesar_encrypt(text, -shift)


def brute_force(ciphertext: str) -> list[tuple[int, str]]:
    """Try every useful Caesar key and return ``(key, plaintext)`` pairs.

    Key 0 is skipped because it leaves the ciphertext unchanged, so
    there are exactly 25 candidates (keys 1 through 25).
    """
    return [(key, caesar_decrypt(ciphertext, key)) for key in range(1, 26)]
