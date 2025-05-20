import os
import pdfplumber
import spacy
import pandas as pd
import re

# Load spaCy English model
nlp = spacy.load("en_core_web_sm")

input_folder = "./data/raw/"
output_folder = "./data/processed_nlp/"
os.makedirs(output_folder, exist_ok=True)

# Target file sets
companies = ["REXP", "DIPD"]

# Keywords to check if the page is related to income statements
income_keywords = ["INCOME STATEMENTS", "STATEMENT OF PROFIT OR LOSS", "Comprehensive Income","Consolidated Income Statements"]

def contains_income_keyword(text):
    return any(kw.lower() in text.lower() for kw in income_keywords)

def count_numeric_values(line):
    # Accepts digits with commas, periods, parentheses (accounting), minus signs
    return len(re.findall(r"[-(]?\d[\d,.\-()]*", line))

def clean_line(line):
    return re.sub(r"\s+", " ", line).strip()

def is_probable_financial_row(line):
    # Run NLP on the line
    doc = nlp(line)
    has_financial_noun = any(token.pos_ == "NOUN" for token in doc)
    has_multiple_numbers = count_numeric_values(line) >= 2
    return has_financial_noun and has_multiple_numbers

for company in companies:
    input_path = os.path.join(input_folder, company)
    output_file = os.path.join(output_folder, f"{company}_income_nlp.csv")
    extracted_rows = []

    for file in os.listdir(input_path):
        if not file.lower().endswith(".pdf"):
            continue
        pdf_path = os.path.join(input_path, file)
        print(f"[~] Processing {pdf_path}")
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if not text:
                    continue
                if not contains_income_keyword(text):
                    continue
                lines = text.split("\n")
                for line in lines:
                    line = clean_line(line)
                    if is_probable_financial_row(line):
                        extracted_rows.append([file, page.page_number, line])

    if extracted_rows:
        df = pd.DataFrame(extracted_rows, columns=["Source File", "Page", "Line"])
        df.to_csv(output_file, index=False)
        print(f"[✓] Extracted data saved to: {output_file}")
    else:
        print(f"[!] No valid rows found for {company}")
