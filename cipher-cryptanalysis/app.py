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
from cryptanalysis.substitution import hill_climb_solve, random_key, substitution_encrypt

# Classroom sample used by the brief: "HELLO WORLD" shifted by 3.
SAMPLE_CIPHERTEXT = "KHOOR ZRUOG"
SAMPLE_PLAINTEXT = "HELLO WORLD"
SAMPLE_SHIFT = 3

# A paragraph long enough for chi-squared to recover the shift in one click.
# The true shift is 11. The lecture buttons never ask you to type this in.
LECTURE_PARAGRAPH = (
    "The students gathered in the lab to see why a simple shift cipher fails. "
    "They typed a long English sentence, hid it with a secret shift, and then "
    "asked the program to try every possible key. The correct sentence was the "
    "one whose letters behaved like ordinary English."
)
LECTURE_SHIFT = 11
LECTURE_CAESAR = caesar_encrypt(LECTURE_PARAGRAPH, LECTURE_SHIFT)

# Fixed key (seed 4) so the substitution demo is the same every time you present.
LECTURE_SUBSTITUTION_PLAIN = (
    "In the history of secret writing a substitution cipher replaces every letter "
    "with another letter and then keeps that choice for the whole message. English "
    "still shows through because the letter e remains common and the pair th keeps "
    "returning in words such as the that and with. A student can count those letters "
    "line them up with the usual English order and then swap two guesses whenever "
    "the text begins to look like real words. With a few hundred letters the pattern "
    "is strong enough that the original message comes back almost intact which is "
    "why this classical cipher is no longer a serious way to protect information."
)
LECTURE_SUBSTITUTION = substitution_encrypt(LECTURE_SUBSTITUTION_PLAIN, random_key(4))

MODES: list[str] = [
    "Break Caesar Cipher",
    "Break Substitution Cipher",
    "Encrypt Demo",
    "Why Monoalphabetic Ciphers Fail",
]

# Spoken cues for the five sidebar buttons, in presentation order.
LECTURE_CUES: dict[int, str] = {
    1: "Say: every letter moved forward 3 places, so HELLO became KHOOR. Next I will hide a whole paragraph and not tell the program the key.",
    2: "Say: this paragraph was shifted by a secret amount. The true shift is 11. If the best key is 11, the attack worked.",
    3: "Say: the same attack on only ten letters is a guess. The true text is HELLO WORLD, key 3. The warning is the point of this slide.",
    4: "Say: a full substitution cipher has 26 factorial keys, so we cannot try them all. Frequency analysis plus hill climbing still reads the message. A few letters may stay swapped.",
    5: "Say: Caesar has 25 keys and still leaks English letter frequencies. AES does not leave this fingerprint.",
}
LECTURE_STEP_MODE: dict[int, str] = {
    1: "Encrypt Demo",
    2: "Break Caesar Cipher",
    3: "Break Caesar Cipher",
    4: "Break Substitution Cipher",
    5: "Why Monoalphabetic Ciphers Fail",
}

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
            section[data-testid="stSidebar"] .stButton button {
                width: 100%;
                border: none;
                border-radius: 12px;
                background: #e4c48c;
                font-weight: 700;
            }
            section[data-testid="stSidebar"] .stButton button p {
                color: #1c1915 !important;
                font-weight: 700;
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
                margin-top: 0.4rem;
            }
            .stat-row {
                display: flex;
                gap: 1.5rem;
                margin-bottom: 0.4rem;
            }
            .stat-label {
                letter-spacing: 0.08em;
                text-transform: uppercase;
                font-size: 0.75rem;
                color: #6b6256;
                font-weight: 700;
            }
            .stat-value {
                font-family: Fraunces, Georgia, serif;
                font-size: 1.8rem;
                color: #1c1915;
                line-height: 1.1;
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


def _hero(compact: bool = False) -> None:
    """Draw the title block. A lecture step uses a shorter title so the answer fits."""
    if compact:
        st.markdown(
            """
            <div class="hero">
                <div class="eyebrow">Frequency analysis · classical ciphers</div>
                <h1 style="font-size:1.7rem;">Automated Cryptanalysis of Classical Ciphers</h1>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return
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


def _show_caesar_verdict(analyzed: str) -> tuple[list, dict]:
    """Show the best key and plaintext, and return the ranking for the table."""
    ranked = rank_caesar_keys(analyzed)
    best = ranked[0]
    score = confidence(ranked)
    if is_text_too_short(analyzed):
        st.warning(
            "This ciphertext has fewer than 25 letters. Frequency counts are "
            "noisy, so the top key may be wrong."
        )
    chi_value = best["chi_squared"]
    chi_label = "n/a" if math.isinf(chi_value) else f"{chi_value:.2f}"
    safe_plaintext = html.escape(best["plaintext"]) if best["plaintext"] else "—"
    # Plain HTML, not st.metric: metrics drawn into an earlier container stay blank.
    st.markdown(
        f"""
        <div class="telegram">
            <div class="stat-row">
                <div><div class="stat-label">Best key</div><div class="stat-value">{best["key"]}</div></div>
                <div><div class="stat-label">Confidence</div><div class="stat-value">{score:.1f}%</div></div>
                <div><div class="stat-label">Chi-squared</div><div class="stat-value">{chi_label}</div></div>
            </div>
            <h3>Likely plaintext</h3>
            <p class="plain-out">{safe_plaintext}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    return ranked, best


def _render_caesar() -> None:
    """Break a Caesar cipher: metrics, ranked table, and two frequency charts."""
    st.subheader("Break Caesar Cipher")
    sample_column, paragraph_column = st.columns(2)
    if sample_column.button("Short sample: KHOOR ZRUOG"):
        # One click fills the box and ranks the keys, so you are not hunting for Analyze.
        st.session_state["caesar_ciphertext"] = SAMPLE_CIPHERTEXT
        st.session_state["caesar_analyzed"] = SAMPLE_CIPHERTEXT
        st.session_state["lecture_step"] = 3
        st.rerun()
    if paragraph_column.button("Full paragraph"):
        st.session_state["caesar_ciphertext"] = LECTURE_CAESAR
        st.session_state["caesar_analyzed"] = LECTURE_CAESAR
        st.session_state["lecture_step"] = 2
        st.rerun()

    analyzed = st.session_state.get("caesar_analyzed")
    if analyzed:
        ranked, best = _show_caesar_verdict(analyzed)
    else:
        ranked, best = None, None
        st.markdown(
            '<div class="note-card">Press <b>Analyze</b>, or use a gold button in the sidebar.</div>',
            unsafe_allow_html=True,
        )

    ciphertext = st.text_area(
        "Ciphertext",
        height=110,
        key="caesar_ciphertext",
        placeholder="Paste ciphertext here, or load the sample.",
    )

    if st.button("Analyze", type="primary"):
        # Store the text that was analyzed. Tab clicks rerun the script,
        # and the button itself is True only on the click that produced it.
        st.session_state["caesar_analyzed"] = ciphertext
        st.rerun()

    table_tab, chart_tab = st.tabs(["All 25 keys", "Frequency charts"])

    if not analyzed or ranked is None or best is None:
        return

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


def _show_substitution_answer(solution: dict[str, object]) -> None:
    """Draw the recovered substitution plaintext above the ciphertext box."""
    ciphertext = str(solution["ciphertext"])
    plaintext = str(solution["plaintext"])
    score = float(solution["score"])  # type: ignore[arg-type]
    if is_text_too_short(ciphertext):
        st.warning(
            "This ciphertext has fewer than 25 letters. A substitution solver "
            "needs a much longer sample before the bigram score is trustworthy."
        )
    safe_plaintext = html.escape(plaintext) if plaintext else "—"
    st.markdown(
        f"""
        <div class="telegram">
            <div class="stat-label">Bigram log-score</div>
            <div class="stat-value">{score:.1f}</div>
            <h3>Recovered plaintext</h3>
            <p class="plain-out">{safe_plaintext}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.caption(
        "Higher bigram log-score means more English-like letter pairs. "
        "The score is negative because it is a sum of logarithms."
    )


def _render_substitution() -> None:
    """Break a general substitution cipher with the hill-climbing solver."""
    st.subheader("Break Substitution Cipher")
    st.write(
        "A full substitution key is a permutation of A–Z. Brute force cannot "
        "search 26! keys, so the solver starts from letter frequencies and "
        "swaps letters whenever the English bigram score improves."
    )
    if st.button("Load lecture sample and solve"):
        st.session_state["substitution_ciphertext"] = LECTURE_SUBSTITUTION
        st.session_state["lecture_step"] = 4
        with st.spinner("Climbing the key space..."):
            key, plaintext, score = hill_climb_solve(LECTURE_SUBSTITUTION, seed=4)
        st.session_state["substitution_solution"] = {
            "ciphertext": LECTURE_SUBSTITUTION,
            "key": key,
            "plaintext": plaintext,
            "score": score,
        }
        st.rerun()

    solution = st.session_state.get("substitution_solution")
    if solution is None:
        st.markdown(
            '<div class="note-card">Press <b>Solve</b>, or use sidebar button 4. A few thousand swaps usually take a few seconds.</div>',
            unsafe_allow_html=True,
        )
    else:
        _show_substitution_answer(solution)

    ciphertext = st.text_area(
        "Substitution ciphertext",
        height=160,
        key="substitution_ciphertext",
        placeholder="Paste a longer English ciphertext, or load the lecture sample.",
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
        st.rerun()

    if solution is None:
        return

    key = solution["key"]
    map_tab = st.tabs(["Key mapping"])[0]
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
        # The ciphertext card is filled after the inputs, but drawn above them.
        result_slot = st.container()
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
            with result_slot:
                st.markdown(
                    f"""
                    <div class="telegram">
                        <h3>Ciphertext</h3>
                        <p class="plain-out">{safe_ciphertext}</p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                st.caption("Key k shifts each letter forward by k.")
        elif st.session_state.get("demo_ready"):
            with result_slot:
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


def _start_encrypt_demo() -> None:
    """Open the encrypt page on HELLO WORLD with shift 3 already applied."""
    st.session_state["mode"] = "Encrypt Demo"
    st.session_state["demo_plaintext"] = SAMPLE_PLAINTEXT
    st.session_state["demo_shift"] = SAMPLE_SHIFT
    st.session_state["demo_ready"] = True
    st.session_state["lecture_step"] = 1


def _start_long_caesar() -> None:
    """Open Caesar analysis on the prepared paragraph and show the ranking."""
    st.session_state["mode"] = "Break Caesar Cipher"
    st.session_state["caesar_ciphertext"] = LECTURE_CAESAR
    st.session_state["caesar_analyzed"] = LECTURE_CAESAR
    st.session_state["lecture_step"] = 2


def _start_short_caesar() -> None:
    """Open Caesar analysis on KHOOR ZRUOG so the short-text warning appears."""
    st.session_state["mode"] = "Break Caesar Cipher"
    st.session_state["caesar_ciphertext"] = SAMPLE_CIPHERTEXT
    st.session_state["caesar_analyzed"] = SAMPLE_CIPHERTEXT
    st.session_state["lecture_step"] = 3


def _start_substitution() -> None:
    """Solve the prepared substitution ciphertext with the fixed lecture seed."""
    st.session_state["mode"] = "Break Substitution Cipher"
    st.session_state["substitution_ciphertext"] = LECTURE_SUBSTITUTION
    st.session_state["lecture_step"] = 4
    with st.spinner("Climbing the key space..."):
        key, plaintext, score = hill_climb_solve(LECTURE_SUBSTITUTION, seed=4)
    st.session_state["substitution_solution"] = {
        "ciphertext": LECTURE_SUBSTITUTION,
        "key": key,
        "plaintext": plaintext,
        "score": score,
    }


def _start_explanation() -> None:
    """Open the explanation page used for the closing minute."""
    st.session_state["mode"] = "Why Monoalphabetic Ciphers Fail"
    st.session_state["lecture_step"] = 5


def _lecture_sidebar() -> None:
    """Five buttons, in the order to click them during the presentation."""
    st.sidebar.markdown("## Present this")
    st.sidebar.caption("Click in order. Nothing to type or paste.")
    if st.sidebar.button("1. Show the shift"):
        _start_encrypt_demo()
    if st.sidebar.button("2. Break a paragraph"):
        _start_long_caesar()
    if st.sidebar.button("3. Short text fails"):
        _start_short_caesar()
    if st.sidebar.button("4. Crack substitution"):
        _start_substitution()
    if st.sidebar.button("5. Why it fails"):
        _start_explanation()


def _lecture_banner(mode: str) -> None:
    """Show the line to say for the lecture step that opened this page."""
    step = st.session_state.get("lecture_step")
    if not isinstance(step, int):
        return
    if LECTURE_STEP_MODE.get(step) != mode:
        return
    st.info(LECTURE_CUES[step])


def main() -> None:
    """Build the wide Streamlit page and dispatch the selected mode."""
    st.set_page_config(
        page_title="Automated Cryptanalysis of Classical Ciphers",
        page_icon="⌕",
        layout="wide",
    )
    _inject_styles()
    if "mode" not in st.session_state:
        st.session_state["mode"] = MODES[0]

    # Lecture buttons update the mode before the radio button is created,
    # and before the title, so a lecture step can use the shorter header.
    _lecture_sidebar()
    _hero(compact=bool(st.session_state.get("lecture_step")))
    st.sidebar.markdown("## Or pick a page")
    mode = st.sidebar.radio(
        "Mode",
        MODES,
        label_visibility="collapsed",
        key="mode",
    )
    st.sidebar.markdown("---")
    st.sidebar.write(
        "Key k means the ciphertext was shifted forward by k. "
        "Decryption shifts back by k."
    )
    st.sidebar.caption("College project · Caesar cipher and frequency analysis")

    _lecture_banner(mode)
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
