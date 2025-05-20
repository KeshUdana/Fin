import os
import pdfplumber
import spacy
import pandas as pd
import re

# --- Load spaCy English model ---
nlp = spacy.load("en_core_web_sm")

# --- Configs ---
input_folder = "./data/raw/"
output_folder = "./data/processed_nlp/"
summary_output_folder = "./data/financial_summaries/"
os.makedirs(output_folder, exist_ok=True)
os.makedirs(summary_output_folder, exist_ok=True)

companies = ["REXP", "DIPD"]

income_keywords = [
    "INCOME STATEMENTS", 
    "STATEMENT OF PROFIT OR LOSS", 
    "Comprehensive Income", 
    "Consolidated Income Statements"
]

# Regex to detect period on the page
period_patterns = [
    r"(?:Year|12 months|Twelve months)\s+(?:ended|to)\s+(?:31st\s+)?(?:March|December|June|September)[ ,\d]+",
    r"03\s*months\s+(?:ended|to)\s+(?:31st\s+)?(?:March|December|June|September)[ ,\d]+",
    r"\d{2}\.\d{2}\.\d{4}"  # For formats like 31.03.2013
]

def contains_income_keyword(text):
    return any(kw.lower() in text.lower() for kw in income_keywords)

def extract_period(text):
    for pattern in period_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(0)
    return "Unknown Period"

def count_numeric_values(line):
    return len(re.findall(r"[-(]?\d[\d,.\-()]*", line))

def clean_line(line):
    return re.sub(r"\s+", " ", line).strip()

def is_probable_financial_row(line):
    doc = nlp(line)
    has_financial_noun = any(token.pos_ == "NOUN" for token in doc)
    has_multiple_numbers = count_numeric_values(line) >= 2
    return has_financial_noun and has_multiple_numbers

# --- PHASE 1: Extract Financial Lines from PDFs ---
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
                if not text or not contains_income_keyword(text):
                    continue

                period = extract_period(text)
                lines = text.split("\n")

                for line in lines:
                    line = clean_line(line)
                    if is_probable_financial_row(line):
                        extracted_rows.append([file, page.page_number, period, line])

    if extracted_rows:
        df = pd.DataFrame(extracted_rows, columns=["Source File", "Page", "Period", "Line"])
        df.to_csv(output_file, index=False)
        print(f"[✓] Extracted data saved to: {output_file}")
    else:
        print(f"[!] No valid rows found for {company}")