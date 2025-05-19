import os
import pdfplumber
import pandas as pd

input_folder = "./data/raw/REXP/"
output_folder = "./data/processed/REXP/"
output_file = os.path.join(output_folder, "consolidated_income_all.csv")

os.makedirs(output_folder, exist_ok=True)

target_keywords = ["Consolidated Income Statements"]

def page_contains_keyword(text, keywords):
    return any(keyword.lower() in text.lower() for keyword in keywords)

all_data = []

for filename in os.listdir(input_folder):
    if filename.lower().endswith(".pdf"):
        pdf_path = os.path.join(input_folder, filename)
        with pdfplumber.open(pdf_path) as pdf:
            for i, page in enumerate(pdf.pages):
                text = page.extract_text() or ""
                if page_contains_keyword(text, target_keywords):
                    tables = page.extract_tables()
                    if tables:
                        for t_idx, table in enumerate(tables):
                            df = pd.DataFrame(table)
                            df['Source File'] = filename
                            df['Page Number'] = i + 1
                            df['Table Number'] = t_idx + 1
                            all_data.append(df)
                    break  # stop after finding the first matching page

# Combine all tables into one DataFrame
if all_data:
    combined_df = pd.concat(all_data, ignore_index=True)
    combined_df.to_csv(output_file, index=False)
    print(f"[✓] Combined CSV saved to: {output_file}")
else:
    print("[!] No tables found in any PDFs.")
