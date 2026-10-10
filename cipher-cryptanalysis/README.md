# Automated Cryptanalysis of Classical Substitution Ciphers (Caesar Cipher) Using Frequency Analysis

A Python program that receives ciphertext and recovers the plaintext **without the key**. It shows why a monoalphabetic cipher is weak: it hides the names of the letters, but not how often they appear.

## Objective

Classical substitution ciphers replace each letter with another letter and then keep that choice for the whole message. English does not use letters equally. `E` is common and `Z` is rare, and pairs such as `TH` and `HE` keep coming back. This project measures that leftover pattern and turns it into a key.

## How it works

### Frequency analysis

`letter_counts` and `letter_percentages` tally A–Z, ignoring case and non-letters. The percentages are drawn next to the standard English percentages (E = 12.70, T = 9.06, and so on). If the two bar charts have the same shape, the text is probably English.

### Chi-squared

For every letter the program computes

```text
(observed count − expected count)² / expected count
```

The expected count is the English percentage scaled to the number of letters in the candidate. The 25 Caesar candidates are sorted by this total. **Lower is better.** The best candidate is rank 1. If two chi-squared scores tie, the fraction of common English words breaks the tie.

### Brute force (Caesar)

A Caesar key is only a shift. Key `k` means the plaintext was shifted **forward** by `k`, so decryption shifts **backward** by `k`. There are 25 useful keys. Example:

```text
Ciphertext: KHOOR ZRUOG
Key 3 -> HELLO WORLD
```

### Hill climbing (general substitution)

A full substitution key is a permutation of the alphabet: 26! possibilities, about 4.03 × 10²⁶. Brute force is not realistic. The solver:

1. Maps ciphertext letters, most frequent first, onto English letters in the order E, T, A, O, I, N, …
2. Repeatedly swaps two letters in the key.
3. Keeps the swap only when the bigram log-probability improves.
4. Restarts from new random permutations so one poor peak is not the end of the search, then checks every remaining pair. Pairs are counted inside words, because a space is still visible in the ciphertext.

Unseen letter pairs get a small floor probability so the logarithm is always defined.

### Confidence and short text

Confidence is a 0–100 score for the gap between the best chi-squared value and the second best. If the ciphertext has fewer than 25 letters, the report and the app warn that the ranking may be wrong.

## Features

- Caesar encrypt, decrypt, and a 25-key ranking with chi-squared and a common-word score
- Frequency charts of ciphertext and of the best decryption against English
- A hill-climbing solver for a general monoalphabetic substitution cipher
- A command-line report and a Streamlit demonstration app
- Pytest coverage and a length-versus-accuracy experiment

## Screenshots

Placeholder for lecture slides. Capture these from `streamlit run app.py`:

1. **Break Caesar Cipher** after analyzing a paragraph of 100 or more letters: verdict, ranked keys, and both frequency charts.
2. **Short ciphertext warning** on a sample shorter than 25 letters, such as `KHOOR ZRUOG`.
3. **Break Substitution Cipher** showing the recovered plaintext and the A–Z key mapping.
4. **Encrypt Demo** showing `HELLO WORLD` with shift 3 producing `KHOOR ZRUOG`.
5. **Why Monoalphabetic Ciphers Fail**, including the English fingerprint chart.

## Installation

Python 3.10 or newer is required. From the `cipher-cryptanalysis` directory, create a virtual environment so the project packages stay separate from the rest of the machine:

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Allowed libraries are listed in `requirements.txt`: Streamlit, Matplotlib, pandas, and pytest. Everything else is the Python standard library.

## Run it in the lecture

From the `cipher-cryptanalysis` folder, one command installs anything missing and opens the app:

```bash
python run_demo.py
```

macOS or Linux: `./run_demo.sh`  
Windows: double-click `run_demo.bat`

Leave that window open. In the browser, click the gold sidebar buttons **in order**. You do not type or paste.

1. **Show the shift** — `HELLO WORLD` with key 3 becomes `KHOOR ZRUOG`.
2. **Break a paragraph** — a long ciphertext. The best key should be **11**, and the sentence about the lab should come back.
3. **Short text fails** — the same `KHOOR ZRUOG` sample. A warning appears, and key 3 is usually not rank 1. Say that this is the limitation.
4. **Crack substitution** — wait a few seconds. The paragraph about secret writing comes back. A few letters such as `v` and `k` may stay swapped.
5. **Why it fails** — 25 keys versus 26!, then the fingerprint chart and the limitations tab.

Each button also writes the sentence to say in a blue box at the top of the page.

## Usage

### Command line

From the `cipher-cryptanalysis` directory:

```bash
python -m cryptanalysis.report "KHOOR ZRUOG"
```

### Streamlit

```bash
python run_demo.py
```

`streamlit run app.py` still works if the packages are already installed.

Use the sidebar to switch mode:

| Mode | What to do |
| --- | --- |
| Break Caesar Cipher | Paste ciphertext and press **Analyze**. |
| Break Substitution Cipher | Paste a few hundred letters and press **Solve**. |
| Encrypt Demo | Enter plaintext and a shift, or load the sample that fills `KHOOR ZRUOG`. |
| Why Monoalphabetic Ciphers Fail | Read the key-space, fingerprint, and limitation notes. |

### Accuracy experiment

```bash
python experiments/accuracy.py
```

The script encrypts English windows of length 10, 20, 50, 100, and 200 and prints the Caesar success rate at each length.

## Project structure

```text
cipher-cryptanalysis/
├── app.py
├── run_demo.py
├── run_demo.sh
├── run_demo.bat
├── cryptanalysis/
│   ├── __init__.py
│   ├── english_stats.py
│   ├── caesar.py
│   ├── frequency.py
│   ├── substitution.py
│   └── report.py
├── tests/
│   ├── test_caesar.py
│   ├── test_frequency.py
│   └── test_substitution.py
├── experiments/
│   └── accuracy.py
├── requirements.txt
└── README.md
```

## Sample output

`python -m cryptanalysis.report "KHOOR ZRUOG"` prints the top three keys with the best one last. Ten letters are not enough for chi-squared to prefer the true shift (key 3, `HELLO WORLD`), which is the short-ciphertext limitation:

```text
Ciphertext: KHOOR ZRUOG

Cipher Type: Caesar Cipher
Possible Keys:
Key 3 -> HELLO WORLD
Key 14 -> WTAAD LDGAS
Key 6 -> EBIIL TLOIA ✓

Likely Plaintext: EBIIL TLOIA
Confidence: 3.2%
Warning: Ciphertext is too short for a reliable result (fewer than 25 letters).
```

A paragraph of 100 or more letters usually places the true shift at rank 1. One run of `experiments/accuracy.py` (30 windows at each length) produced:

```text
Length  10 letters:  73.3% success
Length  20 letters:  96.7% success
Length  50 letters: 100.0% success
Length 100 letters: 100.0% success
Length 200 letters: 100.0% success
```

## Limitations

- **English only.** The letter table, the word list, and the bigram table describe English. Another language needs its own tables.
- **Short ciphertext.** Below 25 letters, Caesar ranking is unreliable. A general substitution cipher needs still more text, on the order of a few hundred letters, before hill climbing is stable.
- **Classical ciphers only.** The program attacks letter-for-letter substitution. It does not attack modern ciphers.

## Conclusion

A monoalphabetic cipher fails because it is a fixed relabeling of the alphabet. The statistical fingerprint of the language is still in the ciphertext, and for Caesar the key space is small enough to search completely.

Modern ciphers such as AES are built to avoid both weaknesses. A 128-bit key cannot be tried one by one, and each output bit depends on many input bits (diffusion) mixed by a key-dependent nonlinear step (confusion). Letter counts in AES ciphertext are essentially flat, so a frequency chart no longer points at the plaintext.

## Tests

```bash
pytest
```
