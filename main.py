import re
import csv
import time
from pathlib import Path
from typing import Dict, List, Optional
import pdfplumber
from deep_translator import GoogleTranslator


class GoetheA2ExampleExtractor:
    def __init__(self, pdf_path: str, vocab_csv_path: str, output_csv_path: str):
        self.pdf_path = pdf_path
        self.vocab_csv_path = vocab_csv_path
        self.output_csv_path = output_csv_path
        self.translator = GoogleTranslator(source='de', target='en')

    def load_vocab_list(self) -> List[str]:
        vocab_words = []
        try:
            with open(self.vocab_csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if 'German Word' in row and row['German Word'].strip():
                        vocab_words.append(row['German Word'].strip())
        except FileNotFoundError:
            print(f"Error: {self.vocab_csv_path} not found")
            raise

        print(f"Loaded {len(vocab_words)} German words from CSV")
        return vocab_words

    def translate_german_word(self, german_word: str, retry_count: int = 2) -> str:
        for attempt in range(retry_count + 1):
            try:
                
                if attempt > 0:
                    time.sleep(1)

                translation = self.translator.translate(german_word)

                
                if translation and translation.lower() != german_word.lower():
                    return translation
                else:
                    
                    common_words = {
                    }

                    if german_word.lower() in common_words:
                        return common_words[german_word.lower()]

                    return f"Translation unavailable"

            except Exception as e:
                print(f"  Translation attempt {attempt + 1} failed for '{german_word}': {e}")
                if attempt == retry_count:
                    return "Translation unavailable"

        return "Translation unavailable"

    def extract_sentence_after_word(self, text: str, target_word: str, start_pos: int) -> Optional[str]:        
        remaining_text = text[start_pos:]

        
        sentence_match = re.search(r'([A-ZÖÄÜ][^.!?]*[.!?])', remaining_text)

        if sentence_match:
            sentence = sentence_match.group(1).strip()
            
            sentence = re.sub(r'\s+', ' ', sentence)
            
            sentence = re.sub(r'[|•-]', '', sentence)
            return sentence

        return None

    def find_example_for_word(self, page_text: str, target_word: str) -> Optional[str]:
        if not page_text:
            return None

        
        word_pattern = r'\b' + re.escape(target_word) + r'\b'
        match = re.search(word_pattern, page_text, re.IGNORECASE)

        if match:
            
            sentence = self.extract_sentence_after_word(page_text, target_word, match.end())

            
            if sentence and re.search(word_pattern, sentence, re.IGNORECASE):
                
                sentence = sentence.strip()
                return sentence

        return None

    def process_pdf(self, vocab_words: List[str]) -> Dict[str, str]:
        examples = {}
        remaining_words = set(vocab_words)

        print(f"\nOpening PDF: {self.pdf_path}")
        with pdfplumber.open(self.pdf_path) as pdf:
            total_pages = len(pdf.pages)
            print(f"Total pages: {total_pages}")

            
            start_page = 7  
            if start_page >= total_pages:
                print(f"Error: PDF has only {total_pages} pages, cannot start from page 8")
                return examples

            print(f"Processing from page {start_page + 1} to {total_pages}")

            for page_num in range(start_page, total_pages):
                if not remaining_words:
                    print("\n✓ All words found! Stopping early.")
                    break

                print(f"\nPage {page_num + 1}/{total_pages} - {len(remaining_words)} words remaining...")
                page = pdf.pages[page_num]
                page_text = page.extract_text()

                if not page_text:
                    print("  No text extracted from this page")
                    continue

                
                found_count = 0
                for word in list(remaining_words):
                    sentence = self.find_example_for_word(page_text, word)
                    if sentence:
                        examples[word] = sentence
                        remaining_words.remove(word)
                        found_count += 1
                        print(f"  ✓ Found '{word}': {sentence[:80]}...")

                if found_count == 0:
                    print("  No new words found on this page")

        
        for word in vocab_words:
            if word not in examples:
                examples[word] = ""
                print(f"  ✗ No example found for '{word}'")

        return examples

    def save_results(self, examples: Dict[str, str], vocab_words: List[str]):
        print("\n" + "=" * 60)
        print("Translating German words to English...")
        print("=" * 60)

        results = []

        for i, word in enumerate(vocab_words, 1):
            print(f"  [{i}/{len(vocab_words)}] Translating '{word}'...", end=" ")

            
            english_word = self.translate_german_word(word)
            print(f"→ {english_word}")

            
            example = examples.get(word, "")

            results.append({
                'German Word': word,
                'English': english_word,
                'Example': example
            })

            
            if i % 10 == 0:
                time.sleep(0.5)

        
        with open(self.output_csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['German Word', 'English', 'Example'])
            writer.writeheader()
            writer.writerows(results)

        print("\n" + "=" * 60)
        found_count = len([e for e in examples.values() if e])
        print(f"✅ Results saved to: {self.output_csv_path}")
        print(f"   Found examples for {found_count}/{len(vocab_words)} words")
        print(f"   Translated ALL {len(vocab_words)} German words")
        print("=" * 60)

        
        missing_examples = [word for word, example in examples.items() if not example]
        if missing_examples:
            print(f"\n⚠️  No examples found for {len(missing_examples)} words:")
            for word in missing_examples[:10]:
                print(f"  - {word}")
            if len(missing_examples) > 10:
                print(f"  ... and {len(missing_examples) - 10} more")

    def run(self):
        print("=" * 60)
        print("Goethe A2 Vocabulary Example Extractor")
        print("=" * 60)

        
        vocab_words = self.load_vocab_list()

        
        examples = self.process_pdf(vocab_words)

        
        self.save_results(examples, vocab_words)

        print("\n✨ Extraction complete!")


def create_sample_vocab_csv():
    sample_words = [
      "Hallo Welt"
    ]

    with open('vocab.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['German Word'])
        for word in sample_words:
            writer.writerow([word])

    print("✓ Created sample vocab.csv with 16 words")


if __name__ == "__main__":
    PDF_PATH = "Goethe-Zertifikat_A2_Wortliste.pdf"  
    VOCAB_CSV = "vocab.csv"
    OUTPUT_CSV = "vocab.csv"

    if not Path(PDF_PATH).exists():
        print(f"❌ Error: PDF file not found at '{PDF_PATH}'")
        print("\nPlease update the PDF_PATH variable with the correct path")
        exit(1)

    if not Path(VOCAB_CSV).exists():
        print(f"⚠️  Warning: '{VOCAB_CSV}' not found.")
        create_sample_vocab_csv()
        print(f"\n📝 Please edit '{VOCAB_CSV}' with your actual German words and run again.")
        exit(0)

    try:
        extractor = GoetheA2ExampleExtractor(PDF_PATH, VOCAB_CSV, OUTPUT_CSV)
        extractor.run()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()