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
    # Removes commas and brackets for negative values
    val = val.replace(",", "")
    if "(" in val and ")" in val:
        val = "-" + val.strip("()")
    return val

def extract_financial_rows(text):
    lines = text.split("\n")
    financial_rows = []
    pattern = re.compile(
        r"^(?P<item>[A-Za-z /()]+)\s+(?P<q1>[\d,()\.-]+)?\s+(?P<q2>[\d,()\.-]+)?\s+(?P<q3>[\d,()\.-]+)?\s+(?P<y1>[\d,()\.-]+)?\s+(?P<y2>[\d,()\.-]+)?\s+(?P<y3>[\d,()\.-]+)?$"
    )

    for line in lines:
        match = pattern.match(line.strip())
        if match:
            data = match.groupdict()
            item = data['item']
            q1 = clean_number(data['q1'] or "")
            q2 = clean_number(data['q2'] or "")
            q3 = clean_number(data['q3'] or "")
            y1 = clean_number(data['y1'] or "")
            y2 = clean_number(data['y2'] or "")
            y3 = clean_number(data['y3'] or "")
            financial_rows.append([item, q1, q2, q3, y1, y2, y3])
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
