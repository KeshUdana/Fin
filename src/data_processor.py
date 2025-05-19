import os
import re
import pdfplumber
import pandas as pd

input_folder = "./data/raw/REXP/"
output_folder = "./data/processed/REXP/"
output_file = os.path.join(output_folder, "consolidated_income_all.csv")

os.makedirs(output_folder, exist_ok=True)

target_keywords = ["Consolidated Income Statements"]

def page_contains_keyword(text, keywords):
    return any(keyword.lower() in text.lower() for keyword in keywords)

def clean_number(val):
    if not val:
        return ""
    val = val.replace(",", "").replace("−", "-").strip()
    if "(" in val and ")" in val:
        val = "-" + val.strip("()")
    return val

def extract_financial_rows(text):
    lines = text.split("\n")
    financial_rows = []
    # Allow for flexible spacing and optional missing columns
    pattern = re.compile(
        r"^(?P<item>[A-Za-z /&.,\-()]+?)\s+"
        r"(?P<q1>[\d,().\-]+)?\s*"
        r"(?P<q2>[\d,().\-]+)?\s*"
        r"(?P<q3>[\d,().\-]+)?\s*"
        r"(?P<y1>[\d,().\-]+)?\s*"
        r"(?P<y2>[\d,().\-]+)?\s*"
        r"(?P<y3>[\d,().\-]+)?$"
    )

    for line in lines:
        match = pattern.match(line.strip())
        if match:
            data = match.groupdict()
            financial_rows.append([
                data['item'].strip(),
                clean_number(data.get('q1')),
                clean_number(data.get('q2')),
                clean_number(data.get('q3')),
                clean_number(data.get('y1')),
                clean_number(data.get('y2')),
                clean_number(data.get('y3'))
            ])
    return financial_rows

all_data = []

for filename in os.listdir(input_folder):
    if filename.lower().endswith(".pdf"):
        pdf_path = os.path.join(input_folder, filename)
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text() or ""
                if page_contains_keyword(text, target_keywords):
                    rows = extract_financial_rows(text)
                    if rows:
                        all_data.extend(rows)
                    break  # stop after finding the first matching page

# Save to CSV
if all_data:
    columns = [
        "Item", 
        "Q1_This_Year", "Q1_Last_Year", "Q1_Change(%)", 
        "Y1_This_Year", "Y1_Last_Year", "Y1_Change(%)"
    ]
    df = pd.DataFrame(all_data, columns=columns)
    df.to_csv(output_file, index=False)
    print(f"[✓] Text-parsed financials saved to: {output_file}")
else:
    print("[!] No matching financial rows found in any PDFs.")
