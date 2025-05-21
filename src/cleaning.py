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

# Financial keywords
financial_keywords = {
    'Revenue': ['Revenue', 'Turnover'],
    'COGS': ['Cost of Sales', 'Cost of Goods Sold'],
    'Gross Profit': ['Gross Profit'],
    'Operating Expenses': ['Distribution Costs', 'Administrative expenses'],
    'Operating Income': ['Profit / (loss) from Operations'],
    'Net Income': [
        'Profit / (loss) for the period',
        'Profit / (loss) Attributable to Ordinary Shareholders'
    ]
}

# Regex for period
period_pattern = re.compile(r'\b(Q[1-4]|H[1-2]|FY\s?\d{2,4}|\d{4})\b', re.IGNORECASE)

def extract_period(text, default_year=2023):
    matches = period_pattern.findall(text)
    if not matches:
        return default_year  # Fallback if no match

    period_raw = matches[0].upper().replace(" ", "")

    if period_raw.startswith("FY"):
        year_part = period_raw[2:]
        if len(year_part) == 2:
            return int("20" + year_part)
        elif len(year_part) == 4:
            return int(year_part)

    elif period_raw.startswith("Q"):
        try:
            quarter = int(period_raw[1])
            return default_year + (quarter - 1) * 0.25  # e.g., Q1 = 2023.0, Q2 = 2023.25
        except ValueError:
            return default_year

    elif period_raw.startswith("H"):
        try:
            half = int(period_raw[1])
            return default_year + (half - 1) * 0.5  # e.g., H1 = 2023.0, H2 = 2023.5
        except ValueError:
            return default_year

    elif period_raw.isdigit():
        return int(period_raw)

    return default_year  # If all parsing fails, fallback


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

def match_label(text, patterns):
    for label, keywords in patterns.items():
        for keyword in keywords:
            if keyword.lower() in text.lower():
                return label
    return None

def process_dataframe(df, company_name, use_flexible_matching=False):
    df.rename(columns={"Source File": "filename", "Page": "page", "Line": "text"}, inplace=True)
    results = []

    for (filename, page), group in df.groupby(["filename", "page"]):
        row_data = {
            'company': company_name,
            'filename': filename,
            'page': page,
            'period': None,
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

            if row_data['period'] is None:
                period = extract_period(text)
                if period:
                    row_data['period'] = period

            label = match_label(text, financial_keywords)

            if label:
                numbers = extract_numbers(text)
                if numbers:
                    row_data[label] = numbers[0]

        if row_data['COGS'] is not None:
            row_data['COGS'] = abs(row_data['COGS'])

        if row_data['Gross Profit'] is None:
            if row_data['Revenue'] is not None and row_data['COGS'] is not None:
                row_data['Gross Profit'] = row_data['Revenue'] - row_data['COGS']

        if row_data['Operating Income'] is None:
            if row_data['Gross Profit'] is not None and row_data['Operating Expenses'] is not None:
                row_data['Operating Income'] = row_data['Gross Profit'] - row_data['Operating Expenses']

        if row_data['Net Income'] is None:
            if (row_data['Revenue'] is not None and
                row_data['COGS'] is not None and
                row_data['Operating Expenses'] is not None):
                row_data['Net Income'] = (
                    row_data['Revenue'] - row_data['COGS'] - row_data['Operating Expenses']
                )
            elif row_data['Operating Income'] is not None:
                row_data['Net Income'] = row_data['Operating Income']

        results.append(row_data)

    return pd.DataFrame(results)

def clean_and_impute(df):
    # Drop rows where all financial metrics are null
    financial_cols = [
        'Revenue', 'COGS', 'Gross Profit',
        'Operating Expenses', 'Operating Income', 'Net Income'
    ]
    df = df.dropna(subset=financial_cols, how='all')

    # Impute individual missing values with column average
    for col in financial_cols:
        if df[col].isnull().any():
            mean_val = df[col].mean()
            df[col].fillna(mean_val, inplace=True)

    return df

# --- Main Processing ---
summary_dfs = []

for company, path in input_files.items():
    df = pd.read_csv(path)

    summary = process_dataframe(df, company_name=company, use_flexible_matching=(company != "REXP"))

    summary = clean_and_impute(summary)

    summary.to_csv(os.path.join(output_dir, f"{company}_financial_summary.csv"), index=False)
    summary_dfs.append(summary)

# Combine and clean all summaries
combined = pd.concat(summary_dfs, ignore_index=True)
combined = clean_and_impute(combined)
combined.to_csv(os.path.join(output_dir, "combined_financial_summary.csv"), index=False)

print("✅ Processed REXP, DIPD, and combined financial summaries saved with imputed values.")
