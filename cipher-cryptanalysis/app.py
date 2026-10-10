"""Streamlit demo: break a Caesar cipher, break a substitution cipher, and explain why.

Launch from the project directory:

    streamlit run app.py

The sidebar chooses the mode. Each mode uses tabs for its sections.
"""

from __future__ import annotations

import html
import math

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

from cryptanalysis.caesar import caesar_encrypt
from cryptanalysis.english_stats import ENGLISH_FREQ
from cryptanalysis.frequency import (
    ALPHABET,
    confidence,
    is_text_too_short,
    letter_percentages,
    rank_caesar_keys,
)
from cryptanalysis.substitution import hill_climb_solve

# Classroom sample used by the brief: "HELLO WORLD" shifted by 3.
SAMPLE_CIPHERTEXT = "KHOOR ZRUOG"
SAMPLE_PLAINTEXT = "HELLO WORLD"
SAMPLE_SHIFT = 3

# Warm paper, ink, and jewel tones. Chosen so a lecture-hall projector
# still shows strong contrast.
INK = "#1c1915"
GOLD = "#9a6b2f"
TEAL = "#1f6f6a"
CORAL = "#9a3b2f"
CREAM = "#fffaf3"
PAPER = "#f4efe4"


def _inject_styles() -> None:
    """Apply the page theme. Streamlit has no built-in 'exhibition' layout."""
    st.markdown(
        """
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,560;9..144,680&family=Source+Sans+3:wght@400;600;700&display=swap');

            .stApp {
                background:
                    radial-gradient(1200px 500px at 10% -10%, rgba(154, 107, 47, 0.16), transparent 55%),
                    radial-gradient(900px 420px at 100% 0%, rgba(31, 111, 106, 0.12), transparent 50%),
                    linear-gradient(180deg, #fbf7f0 0%, #f3eadc 100%);
                color: #1c1915;
                font-family: "Source Sans 3", "Segoe UI", sans-serif;
            }
            header[data-testid="stHeader"] {
                background: transparent;
            }
            section[data-testid="stSidebar"] {
                background: linear-gradient(180deg, #2a241e 0%, #1a1613 100%);
                border-right: 1px solid rgba(226, 196, 140, 0.25);
                min-width: 22rem !important;
                width: 22rem !important;
            }
            [data-testid="stToolbar"] {
                display: none;
            }
            section[data-testid="stSidebar"] h1,
            section[data-testid="stSidebar"] h2,
            section[data-testid="stSidebar"] h3,
            section[data-testid="stSidebar"] p,
            section[data-testid="stSidebar"] label,
            section[data-testid="stSidebar"] span {
                color: #f6f0e6 !important;
            }
            section[data-testid="stSidebar"] .stRadio label {
                background: rgba(255, 250, 243, 0.06);
                border: 1px solid rgba(226, 196, 140, 0.18);
                border-radius: 12px;
                padding: 0.55rem 0.75rem;
                margin-bottom: 0.4rem;
                line-height: 1.25;
            }
            .hero {
                padding: 0.2rem 0 1rem 0;
            }
            .eyebrow {
                letter-spacing: 0.18em;
                text-transform: uppercase;
                color: #9a6b2f;
                font-weight: 700;
                font-size: 0.78rem;
                margin-bottom: 0.35rem;
            }
            .hero h1 {
                font-family: Fraunces, Georgia, serif;
                font-size: 2.6rem;
                line-height: 1.05;
                color: #1c1915;
                margin: 0;
            }
            .lede {
                font-size: 1.12rem;
                color: #3d3832;
                max-width: 46rem;
                margin-top: 0.6rem;
            }
            .telegram {
                background: #fffaf3;
                border: 1px solid rgba(28, 25, 21, 0.12);
                border-left: 6px solid #1f6f6a;
                border-radius: 16px;
                padding: 1.1rem 1.25rem 0.4rem 1.25rem;
                box-shadow: 0 14px 40px rgba(60, 40, 15, 0.08);
            }
            .telegram h3 {
                font-family: Fraunces, Georgia, serif;
                margin-top: 0;
            }
            .plain-out {
                font-family: Fraunces, Georgia, serif;
                font-size: 1.8rem;
                line-height: 1.25;
                color: #1f6f6a;
                margin: 0.2rem 0 0.8rem 0;
                overflow-wrap: anywhere;
            }
            .note-card, .explain-card {
                background: rgba(255, 250, 243, 0.78);
                border: 1px solid rgba(28, 25, 21, 0.08);
                border-radius: 16px;
                padding: 0.9rem 1rem;
                margin-bottom: 0.8rem;
            }
            .explain-card h3 {
                font-family: Fraunces, Georgia, serif;
                margin-top: 0.2rem;
            }
            .key-chip {
                display: inline-block;
                background: #1c1915;
                color: #f6f0e6;
                border-radius: 999px;
                padding: 0.15rem 0.7rem;
                font-weight: 700;
                letter-spacing: 0.04em;
            }
            .map-row {
                font-family: "Source Sans 3", sans-serif;
                letter-spacing: 0.04em;
                font-size: 1rem;
                background: #fffaf3;
                border-radius: 12px;
                padding: 0.7rem 0.8rem;
                border: 1px solid rgba(28, 25, 21, 0.08);
                margin-bottom: 0.4rem;
            }
            div[data-testid="stMetric"] {
                background: #fffaf3;
                border: 1px solid rgba(28, 25, 21, 0.08);
                border-radius: 16px;
                padding: 0.7rem 0.9rem;
                box-shadow: 0 10px 24px rgba(60, 40, 15, 0.05);
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _hero() -> None:
    """Draw the title block shared by every mode."""
    st.markdown(
        """
        <div class="hero">
            <div class="eyebrow">Frequency analysis · classical ciphers</div>
            <h1>Automated Cryptanalysis of Classical Ciphers</h1>
            <p class="lede">
                Recover the plaintext without the key. A Caesar cipher has only 25
                useful shifts, and a full substitution cipher still leaks the
                letter-frequency fingerprint of English.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _style_charts() -> None:
    """Match matplotlib charts to the page colours."""
    plt.rcParams.update(
        {
            "axes.facecolor": CREAM,
            "figure.facecolor": CREAM,
            "axes.edgecolor": INK,
            "axes.labelcolor": INK,
            "xtick.color": INK,
            "ytick.color": INK,
            "text.color": INK,
            "font.size": 11,
        }
    )


def _english_sample() -> str:
    """Build a synthetic letter string with the standard English percentages.

    Repeating each letter in proportion to its published frequency gives
    the explanation tab a fingerprint chart without pretending it is a
    ciphertext.
    """
    pieces: list[str] = []
    for letter in ALPHABET:
        pieces.append(letter * int(round(ENGLISH_FREQ[letter] * 10)))
    return "".join(pieces)


def _frequency_chart(text: str, title: str) -> plt.Figure:
    """Grouped bar chart of letter percentages in ``text`` against English."""
    _style_charts()
    observed = letter_percentages(text)
    positions = list(range(26))
    observed_heights = [observed[letter] for letter in ALPHABET]
    english_heights = [ENGLISH_FREQ[letter] for letter in ALPHABET]

    figure, axis = plt.subplots(figsize=(11, 4.2))
    axis.bar(
        [position - 0.18 for position in positions],
        observed_heights,
        width=0.36,
        label="This text",
        color=TEAL,
    )
    axis.bar(
        [position + 0.18 for position in positions],
        english_heights,
        width=0.36,
        label="English",
        color=GOLD,
    )
    axis.set_xticks(positions)
    axis.set_xticklabels(list(ALPHABET))
    axis.set_ylabel("Percent of letters")
    axis.set_title(title)
    axis.legend(frameon=False)
    axis.spines["top"].set_visible(False)
    axis.spines["right"].set_visible(False)
    figure.tight_layout()
    return figure


def _show_chart(text: str, title: str) -> None:
    """Render one frequency chart and close the figure so memory stays flat."""
    figure = _frequency_chart(text, title)
    st.pyplot(figure, width="stretch")
    plt.close(figure)


def _render_caesar() -> None:
    """Break a Caesar cipher: metrics, ranked table, and two frequency charts."""
    st.subheader("Break Caesar Cipher")
    st.write(
        "Paste ciphertext. Key k means the letters were shifted forward by k, "
        "so the attack shifts them back by k and keeps the most English-like result."
    )

    if st.button("Load sample: KHOOR ZRUOG"):
        st.session_state["caesar_ciphertext"] = SAMPLE_CIPHERTEXT

    ciphertext = st.text_area(
        "Ciphertext",
        height=140,
        key="caesar_ciphertext",
        placeholder="Paste ciphertext here, or load the sample.",
    )

    if st.button("Analyze", type="primary"):
        # Store the text that was analyzed. Tab clicks rerun the script,
        # and the button itself is True only on the click that produced it.
        st.session_state["caesar_analyzed"] = ciphertext

    verdict_tab, table_tab, chart_tab = st.tabs(
        ["Verdict", "All 25 keys", "Frequency charts"]
    )

    analyzed = st.session_state.get("caesar_analyzed")
    if analyzed is None:
        with verdict_tab:
            st.markdown(
                '<div class="note-card">Press <b>Analyze</b> to rank every Caesar key.</div>',
                unsafe_allow_html=True,
            )
        return

    ranked = rank_caesar_keys(analyzed)
    best = ranked[0]
    score = confidence(ranked)

    with verdict_tab:
        if is_text_too_short(analyzed):
            st.warning(
                "This ciphertext has fewer than 25 letters. Frequency counts are "
                "noisy, so the top key may be wrong."
            )
        chi_value = best["chi_squared"]
        chi_label = "n/a" if math.isinf(chi_value) else f"{chi_value:.2f}"
        left, middle, right = st.columns(3)
        left.metric("Best key", str(best["key"]))
        middle.metric("Confidence", f"{score:.1f}%")
        right.metric("Chi-squared", chi_label)
        safe_plaintext = html.escape(best["plaintext"]) if best["plaintext"] else "—"
        st.markdown(
            f"""
            <div class="telegram">
                <h3>Likely plaintext</h3>
                <p class="plain-out">{safe_plaintext}</p>
                <p><span class="key-chip">Key {best["key"]}</span></p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with table_tab:
        frame = pd.DataFrame(ranked)
        frame = frame.rename(
            columns={
                "rank": "Rank",
                "key": "Key",
                "plaintext": "Plaintext",
                "chi_squared": "Chi-squared",
                "word_score": "Word score",
            }
        )
        frame["Chi-squared"] = frame["Chi-squared"].map(lambda value: round(float(value), 3))
        frame["Word score"] = frame["Word score"].map(lambda value: round(float(value), 3))
        st.dataframe(frame, width="stretch", hide_index=True)
        st.caption("Rank 1 is the lowest chi-squared score. The word score breaks ties.")

    with chart_tab:
        st.write("The English fingerprint is the gold bars. A good decryption should follow them.")
        left, right = st.columns(2)
        with left:
            _show_chart(analyzed, "Ciphertext vs English")
        with right:
            _show_chart(best["plaintext"], "Best decryption vs English")


def _render_substitution() -> None:
    """Break a general substitution cipher with the hill-climbing solver."""
    st.subheader("Break Substitution Cipher")
    st.write(
        "A full substitution key is a permutation of A–Z. Brute force cannot "
        "search 26! keys, so the solver starts from letter frequencies and "
        "swaps letters whenever the English bigram score improves."
    )
    ciphertext = st.text_area(
        "Substitution ciphertext",
        height=160,
        key="substitution_ciphertext",
        placeholder="Paste a longer English ciphertext (a few hundred letters works best).",
    )
    if st.button("Solve", type="primary"):
        with st.spinner("Climbing the key space..."):
            key, plaintext, score = hill_climb_solve(ciphertext)
        st.session_state["substitution_solution"] = {
            "ciphertext": ciphertext,
            "key": key,
            "plaintext": plaintext,
            "score": score,
        }

    text_tab, map_tab = st.tabs(["Recovered text", "Key mapping"])
    solution = st.session_state.get("substitution_solution")
    if solution is None:
        with text_tab:
            st.markdown(
                '<div class="note-card">Press <b>Solve</b>. A few thousand swaps usually take a few seconds.</div>',
                unsafe_allow_html=True,
            )
        return

    ciphertext = solution["ciphertext"]
    key = solution["key"]
    plaintext = solution["plaintext"]
    score = solution["score"]

    with text_tab:
        if is_text_too_short(ciphertext):
            st.warning(
                "This ciphertext has fewer than 25 letters. A substitution solver "
                "needs a much longer sample before the bigram score is trustworthy."
            )
        st.metric("Bigram log-score", f"{score:.1f}")
        safe_plaintext = html.escape(plaintext) if plaintext else "—"
        st.markdown(
            f"""
            <div class="telegram">
                <h3>Recovered plaintext</h3>
                <p class="plain-out">{safe_plaintext}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.caption("Higher bigram log-score means more English-like letter pairs. The score is negative because it is a sum of logarithms.")

    with map_tab:
        st.write("Read each pair as plaintext letter → ciphertext letter.")
        pairs = [
            f"<b>{ALPHABET[index]}</b>→{key[index]}" for index in range(26)
        ]
        st.markdown(
            f'<div class="map-row">{"&nbsp;&nbsp;".join(pairs[:13])}</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            f'<div class="map-row">{"&nbsp;&nbsp;".join(pairs[13:])}</div>',
            unsafe_allow_html=True,
        )
        st.code(key, language=None)
        st.caption("The key string is 26 letters: position 1 (A) through position 26 (Z).")


def _render_encrypt() -> None:
    """Encrypt a live plaintext, with a button that loads the classroom sample."""
    st.subheader("Encrypt Demo")
    st.write("Shift a sentence forward, then paste the ciphertext into Break Caesar Cipher.")

    demo_tab, how_tab = st.tabs(["Live encrypt", "How the shift works"])

    with demo_tab:
        if "demo_plaintext" not in st.session_state:
            st.session_state["demo_plaintext"] = ""
        if "demo_shift" not in st.session_state:
            st.session_state["demo_shift"] = SAMPLE_SHIFT

        if st.button("Load sample (fills KHOOR ZRUOG)"):
            st.session_state["demo_plaintext"] = SAMPLE_PLAINTEXT
            st.session_state["demo_shift"] = SAMPLE_SHIFT
            st.session_state["demo_ready"] = True

        plaintext = st.text_area(
            "Plaintext",
            height=140,
            key="demo_plaintext",
            placeholder="Type a sentence to encrypt.",
        )
        shift = st.number_input(
            "Shift (key)",
            min_value=1,
            max_value=25,
            step=1,
            key="demo_shift",
        )
        if st.button("Encrypt", type="primary"):
            st.session_state["demo_ready"] = True

        if st.session_state.get("demo_ready") and plaintext:
            produced = caesar_encrypt(plaintext, int(shift))
            safe_ciphertext = html.escape(produced)
            st.markdown(
                f"""
                <div class="telegram">
                    <h3>Ciphertext</h3>
                    <p class="plain-out">{safe_ciphertext}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.caption("Key k shifts each letter forward by k. Paste this into Break Caesar Cipher.")
        elif st.session_state.get("demo_ready"):
            st.info("Enter a plaintext sentence, or load the sample that produces KHOOR ZRUOG.")

    with how_tab:
        st.markdown(
            """
            <div class="explain-card">
                <h3>One rule, 25 keys</h3>
                <p>Key k moves every letter forward k places in the alphabet and wraps from Z back to A.
                "HELLO" with key 3 becomes "KHOOR" because H→K, E→H, L→O, L→O, O→R.
                Spaces and punctuation stay put, which is why the word breaks still show.</p>
                <p>Decryption uses the same rule in reverse. The attack does not need the key:
                it tries all 25 reverse shifts and measures which result looks like English.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )


def _render_explanation() -> None:
    """Static lecture notes: key space, the frequency fingerprint, and limits."""
    st.subheader("Why Monoalphabetic Ciphers Fail")
    space_tab, print_tab, limit_tab = st.tabs(
        ["Key space", "Frequency fingerprint", "Limitations"]
    )

    with space_tab:
        caesar_col, full_col = st.columns(2)
        caesar_col.metric("Caesar keys", "25")
        full_col.metric("Substitution keys", "26!")
        st.markdown(
            """
            <div class="explain-card">
                <h3>25 versus 26 factorial</h3>
                <p>A Caesar key is only a shift, so keys 1 through 25 can be tried by hand
                or in one short loop. A general monoalphabetic key can send A to any of
                26 letters, B to any of the remaining 25, and so on:</p>
                <p><b>26! = 403,291,461,126,605,635,584,000,000</b> (about 4.03 × 10<sup>26</sup>).</p>
                <p>That space is far too large to brute force. Frequency analysis does not
                visit every key. It proposes one good guess, then hill climbing swaps
                letters only when the text becomes more English-like.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with print_tab:
        st.markdown(
            """
            <div class="explain-card">
                <h3>The fingerprint survives</h3>
                <p>In a monoalphabetic cipher each plaintext letter always becomes the
                same ciphertext letter. The names change; the crowd does not.
                E is still the tallest bar, and Z is still rare. Caesar only rotates
                that bar chart. A full substitution rearranges the bars, but the
                heights are the same multiset.</p>
                <p><b>Chi-squared</b> compares a candidate's letter counts with the
                English percentages. For each letter it adds
                (observed − expected)<sup>2</sup> / expected. The candidate with the
                smallest total is the most English-like. Common words are used only
                to break an exact tie.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        # A static picture of the English fingerprint, with no ciphertext required.
        _show_chart(
            _english_sample(),
            "The English letter fingerprint these attacks look for",
        )

    with limit_tab:
        st.markdown(
            """
            <div class="explain-card">
                <h3>Where the demo stops being reliable</h3>
                <p><b>Short ciphertext.</b> Under 25 letters, chi-squared is mostly noise.
                The app shows a warning instead of pretending the top key is certain.
                The accuracy experiment in <code>experiments/accuracy.py</code> prints
                how often Caesar recovery succeeds at lengths 10, 20, 50, 100, and 200.</p>
                <p><b>English only.</b> The frequency table, the word list, and the
                bigram table are English. A French or Hindi message needs its own tables.</p>
                <p><b>Classical ciphers only.</b> AES and other modern ciphers are not
                a single letter-for-letter map. They mix the message so thoroughly that
                ciphertext letter frequencies look flat, and knowing one letter tells
                you nothing about the next. A 128-bit key is also far beyond 26!.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )


def main() -> None:
    """Build the wide Streamlit page and dispatch the selected mode."""
    st.set_page_config(
        page_title="Automated Cryptanalysis of Classical Ciphers",
        page_icon="⌕",
        layout="wide",
    )
    _inject_styles()
    _hero()

    st.sidebar.markdown("## Mode")
    mode = st.sidebar.radio(
        "Mode",
        [
            "Break Caesar Cipher",
            "Break Substitution Cipher",
            "Encrypt Demo",
            "Why Monoalphabetic Ciphers Fail",
        ],
        label_visibility="collapsed",
    )
    st.sidebar.markdown("---")
    st.sidebar.write(
        "Key k means the ciphertext was shifted forward by k. "
        "Decryption shifts back by k."
    )
    st.sidebar.caption("College project · Caesar cipher and frequency analysis")

    if mode == "Break Caesar Cipher":
        _render_caesar()
    elif mode == "Break Substitution Cipher":
        _render_substitution()
    elif mode == "Encrypt Demo":
        _render_encrypt()
    else:
        _render_explanation()


if __name__ == "__main__":
    main()
