import pandas as pd
import pdfplumber
import re
from deep_translator import GoogleTranslator

CSV_FILE = "vocab.csv"
PDF_FILE = "Goethe-Zertifikat_A2_Wortliste.pdf"

# --------------------------
# Extract vocabulary entries from PDF
# --------------------------

def extract_examples(pdf_path):
    examples = {}

    with pdfplumber.open(pdf_path) as pdf:
        full_text = ""

        for page in pdf.pages:
            text = page.extract_text()
            if text:
                full_text += "\n" + text

    lines = full_text.split("\n")

    current_word = None

    for line in lines:

        # Detect vocabulary entries
        match = re.match(
            r"^([A-Za-zÄÖÜäöüß][A-Za-zÄÖÜäöüß\-/() ]{1,40})[, ]",
            line
        )

        if match:
            current_word = match.group(1).strip()
            continue

        if current_word:
            sentence = line.strip()

            if len(sentence) > 15:
                if current_word not in examples:
                    examples[current_word.lower()] = sentence

    return examples


# --------------------------
# Load PDF examples
# --------------------------

pdf_examples = extract_examples(PDF_FILE)

# --------------------------
# Load CSV
# --------------------------

df = pd.read_csv(CSV_FILE)

for index, row in df.iterrows():

    german = str(row["German Word"]).strip()

    if not german:
        continue

    # ----------------------
    # Fill English meaning
    # ----------------------

    if pd.isna(row["English"]) or row["English"] == "":

        try:
            english = GoogleTranslator(
                source="de",
                target="en"
            ).translate(german)

            df.at[index, "English"] = english

        except Exception:
            pass

    # ----------------------
    # Fill example sentence
    # ----------------------

    if pd.isna(row["Example"]) or row["Example"] == "":

        word_key = german.lower()

        if word_key in pdf_examples:
            df.at[index, "Example"] = pdf_examples[word_key]

# --------------------------
# Save
# --------------------------

df.to_csv(
    "vocab_completed.csv",
    index=False,
    encoding="utf-8-sig"
)

print("Finished.")