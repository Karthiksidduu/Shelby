"""Plain-text report for a Caesar ciphertext.

Run from the project directory:

    python -m cryptanalysis.report "KHOOR ZRUOG"
"""

from __future__ import annotations

import sys

from cryptanalysis.frequency import confidence, is_text_too_short, rank_caesar_keys


def format_report(ciphertext: str) -> str:
    """Return a multi-line Caesar analysis report for ``ciphertext``.

    The three strongest keys are listed so the best one appears last
    and is marked with a check. A confidence percentage is always
    included. A warning line is added when the ciphertext has fewer
    than 25 letters.
    """
    ranked = rank_caesar_keys(ciphertext)
    top_three = ranked[:3]
    # Reverse the top three so the best key is printed last.
    display_order = list(reversed(top_three))

    lines: list[str] = [
        f"Ciphertext: {ciphertext}",
        "",
        "Cipher Type: Caesar Cipher",
        "Possible Keys:",
    ]

    best_key = ranked[0]["key"] if ranked else None
    for row in display_order:
        marker = " ✓" if row["key"] == best_key else ""
        lines.append(f"Key {row['key']} -> {row['plaintext']}{marker}")

    likely_plaintext = ranked[0]["plaintext"] if ranked else ""
    lines.append("")
    lines.append(f"Likely Plaintext: {likely_plaintext}")
    lines.append(f"Confidence: {confidence(ranked):.1f}%")
    if is_text_too_short(ciphertext):
        lines.append(
            "Warning: Ciphertext is too short for a reliable result (fewer than 25 letters)."
        )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> None:
    """Print a report for the ciphertext given on the command line."""
    arguments = list(sys.argv[1:] if argv is None else argv)
    if not arguments:
        print('Usage: python -m cryptanalysis.report "KHOOR ZRUOG"')
        return
    # Join so a quoted sentence with spaces arrives as one ciphertext.
    ciphertext = " ".join(arguments)
    print(format_report(ciphertext))


if __name__ == "__main__":
    main()
