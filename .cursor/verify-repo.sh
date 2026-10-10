#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

EXPECTED=(
  "DAE 1,2 PROGRAM.doc"
  "DAE PROGRAM-3.docx"
  "DAE LAB 4T PROGRAM.docx"
  "DAE Program 5 n 6.docx"
  "dae continue 6 prog n 7 prog.docx"
  "DAE LAB 8 N 12 PROG.docx"
  "DAE LAB PROGRAM 9.docx"
  "DAE LAB Program 10 n 11.docx"
  "exp1.txt"
  "filee1.txt"
)

missing=0
for f in "${EXPECTED[@]}"; do
  if [[ ! -e "$f" ]]; then
    echo "MISSING: $f"
    missing=$((missing + 1))
  fi
done

if [[ "$missing" -gt 0 ]]; then
  echo "Verification failed: $missing file(s) missing"
  exit 1
fi

echo "All ${#EXPECTED[@]} tracked assets present."

sample="DAE LAB 4T PROGRAM.docx"
if command -v pandoc >/dev/null 2>&1; then
  words=$(pandoc "$sample" -t plain 2>/dev/null | wc -w)
  echo "Pandoc extracted ~${words} words from ${sample}."
  if [[ "$words" -lt 5 ]]; then
    echo "Warning: sample document looks empty after conversion."
    exit 1
  fi
else
  chars=$(unzip -p "$sample" word/document.xml 2>/dev/null | tr -d '\n' | wc -c)
  echo "Fallback XML check: ${chars} bytes in ${sample} document body."
  if [[ "$chars" -lt 100 ]]; then
    echo "Verification failed: document body too small."
    exit 1
  fi
fi

echo "Repository verification passed."
