import pandas as pd
import re
import os

# Load correct CSV
csv_path = "./data/processed_nlp/REXP_income_nlp.csv"
df = pd.read_csv(csv_path)
df.rename(columns={"Source File": "filename", "Page": "page", "Line": "text"}, inplace=True)

# Define regex patterns for financial terms
patterns = {
    'Revenue': re.compile(r'^Revenue', re.IGNORECASE),
    'COGS': re.compile(r'^(Cost of Sales|Cost of Goods Sold)', re.IGNORECASE),
    'Operating Expenses': re.compile(r'^Distribution Costs', re.IGNORECASE),
    'Operating Income': re.compile(r'^Profit / \(Loss\) from Operations', re.IGNORECASE),
    'Net Income': re.compile(r'^(Profit / \(Loss\) (for the period|Attributable to Ordinary Shareholders))', re.IGNORECASE),
}

def extract_numbers(text):
    # Match integers with optional commas, optional parentheses or minus signs
    raw_numbers = re.findall(r'-?\(?\d[\d,]*\)?', text)
    cleaned = []
    for num in raw_numbers:
        num = num.replace(",", "").strip()

        # Convert (1234) to -1234
        if num.startswith("(") and num.endswith(")"):
            num = "-" + num.strip("()")

        # Ensure only valid numbers are passed
        try:
            cleaned.append(int(num))
        except ValueError:
            continue  # Skip any malformed number like "3)" or empty string
    return cleaned 

# Iterate and extract per (filename, page)
results = []

for (filename, page), group in df.groupby(["filename", "page"]):
    row_data = {
        'filename': filename,
        'page': page,
        'Revenue': None,
        'COGS': None,
        'Gross Profit': None,
        'Operating Expenses': None,
        'Operating Income': None,
        'Net Income': None
    }

    for _, row in group.iterrows():
        text = row["text"]

        for key, pattern in patterns.items():
            if pattern.match(text):
                nums = extract_numbers(text)
                if nums:
                    row_data[key] = nums[0]  # Adjust here if you want full-year or 3-month value
                break  # Prevent matching same row with multiple keys

    # Compute Gross Profit
    if row_data['Revenue'] is not None and row_data['COGS'] is not None:
        row_data['Gross Profit'] = row_data['Revenue'] - row_data['COGS']

    results.append(row_data)

# Save to new CSV
final_df = pd.DataFrame(results)
print(final_df)
final_df.to_csv("REXP_financial_summary.csv", index=False)
