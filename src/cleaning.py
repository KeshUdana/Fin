import pandas as pd
import re
import spacy
import os

# Load spaCy model
nlp = spacy.load("en_core_web_sm")

# --- Config ---
input_files = {
    "REXP": "./data/processed_nlp/REXP_income_nlp.csv",
    "DIPD": "./data/processed_nlp/DIPD_income_nlp.csv"
}
output_dir = "./data/financial_summaries"
os.makedirs(output_dir, exist_ok=True)

# Financial keywords (for flexible matching)
financial_keywords = {
    'Revenue': ['Revenue', 'Turnover'],
    'COGS': ['Cost of Sales', 'Cost of Goods Sold'],
    'Gross Profit': ['Gross Profit'],
    'Operating Expenses': ['Distribution Costs', 'Administrative expenses'],
    'Operating Income': ['Profit / (loss) from Operations'],
    'Net Income': ['Profit / (loss) for the period', 'Profit / (loss) Attributable to Ordinary Shareholders']
}

# Regex patterns for strict matching (optional, not used for DIPD here)
regex_patterns = {
    'Revenue': re.compile(r'^Revenue', re.IGNORECASE),
    'COGS': re.compile(r'^(Cost of Sales|Cost of Goods Sold)', re.IGNORECASE),
    'Operating Expenses': re.compile(r'^Distribution Costs', re.IGNORECASE),
    'Operating Income': re.compile(r'^Profit / \(loss\) from Operations', re.IGNORECASE),
    'Net Income': re.compile(r'^(Profit / \(loss\) (for the period|Attributable to Ordinary Shareholders))', re.IGNORECASE),
}

def extract_numbers(text):
    raw_numbers = re.findall(r'-?\(?\d[\d,]*\)?', text)
    cleaned = []
    for num in raw_numbers:
        num = num.replace(",", "").strip()
        if num.startswith("(") and num.endswith(")"):
            num = "-" + num.strip("()")
        try:
            cleaned.append(int(num))
        except ValueError:
            continue
    return cleaned

def match_label_flexible(text, patterns):
    # Flexible keyword-based matching (used for DIPD)
    for label, keywords in patterns.items():
        for keyword in keywords:
            if keyword.lower() in text.lower():
                return label
    return None

def match_label_spacy(text, patterns):
    # spaCy-based or exact matching (used for REXP)
    for label, keywords in patterns.items():
        for keyword in keywords:
            if keyword.lower() in text.lower():
                return label
    return None

def process_dataframe(df, use_flexible_matching=False):
    df.rename(columns={"Source File": "filename", "Page": "page", "Line": "text"}, inplace=True)
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
            text = str(row['text'])
            if not text.strip():
                continue

            if use_flexible_matching:
                label = match_label_flexible(text, financial_keywords)
            else:
                label = match_label_spacy(text, financial_keywords)

            if label:
                numbers = extract_numbers(text)
                if numbers:
                    row_data[label] = numbers[0]

        # Post-processing fixes and calculations

        # Make sure COGS is positive
        if row_data['COGS'] is not None:
            row_data['COGS'] = abs(row_data['COGS'])

        # Calculate Gross Profit if missing but possible
        if row_data['Gross Profit'] is None:
            if row_data['Revenue'] is not None and row_data['COGS'] is not None:
                row_data['Gross Profit'] = row_data['Revenue'] - row_data['COGS']

        # Calculate Operating Income if missing but possible
        if row_data['Operating Income'] is None:
            if row_data['Gross Profit'] is not None and row_data['Operating Expenses'] is not None:
                row_data['Operating Income'] = row_data['Gross Profit'] - row_data['Operating Expenses']

        # Estimate Net Income if missing
        if row_data['Net Income'] is None:
            if (row_data['Revenue'] is not None and
                row_data['COGS'] is not None and
                row_data['Operating Expenses'] is not None):
                row_data['Net Income'] = row_data['Revenue'] - row_data['COGS'] - row_data['Operating Expenses']
            elif row_data['Operating Income'] is not None:
                row_data['Net Income'] = row_data['Operating Income']

        results.append(row_data)

    return pd.DataFrame(results)


# --- Main processing ---

summary_dfs = []

for company, path in input_files.items():
    df = pd.read_csv(path)

    if company == "REXP":
        # Use spaCy / exact keyword matching (works better for REXP)
        summary = process_dataframe(df, use_flexible_matching=False)
    else:
        # Use flexible matching for DIPD (your original DIPD approach)
        summary = process_dataframe(df, use_flexible_matching=True)

    summary.to_csv(os.path.join(output_dir, f"{company}_financial_summary.csv"), index=False)
    summary_dfs.append(summary)

# Combine both company summaries into one file
combined = pd.concat(summary_dfs, ignore_index=True)
combined.to_csv(os.path.join(output_dir, "combined_financial_summary.csv"), index=False)

print("✅ Processed REXP, DIPD, and combined financial summaries saved.")
