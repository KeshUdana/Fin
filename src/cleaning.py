import pandas as pd
import re
import spacy
import os
import random

# Load spaCy model
nlp = spacy.load("en_core_web_sm")

# --- Config ---
input_paths = [
    "./data/processed_nlp/REXP_income_nlp.csv",
    "./data/processed_nlp/DIPD_income_nlp.csv"
]
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

# === Period Extraction ===
def extract_period(text, default_year=None):
    if default_year is None:
        default_year = random.randint(2005, 2023)
    patterns = [
        r'FY\s?(\d{2,4})',
        r'(Q[1-4])\s?[/-]?\s?(20\d{2}|\d{2})',
        r'(H[1-2])\s?[/-]?\s?(20\d{2}|\d{2})',
        r'(20\d{2})[-/](\d{2})',
        r'(20\d{4})',
        r'(\d{2})[-/](\d{2})'
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            groups = match.groups()
            if 'FY' in pattern:
                year = int(groups[0])
                return f"FY{2000 + year if year < 100 else year}"
            elif 'Q' in pattern:
                quarter, year = groups
                return f"{quarter.upper()} {2000 + int(year) if int(year) < 100 else int(year)}"
            elif 'H' in pattern:
                half, year = groups
                return f"{half.upper()} {2000 + int(year) if int(year) < 100 else int(year)}"
            elif len(groups) == 2 and re.match(r'\d{4}', groups[0]):
                return f"FY{int(groups[0])}"
            elif len(groups) == 1:
                return f"FY{int(groups[0])}"
    return f"FY{default_year}"

def extract_numbers(text):
    raw_numbers = re.findall(r'-?\(?\d[\d,]*\)?', text)
    cleaned = []
    for num in raw_numbers:
        num = num.replace(",", "")
        if num.startswith("(") and num.endswith(")"):
            num = "-" + num.strip("()")
        try:
            cleaned.append(int(num))
        except:
            continue
    return cleaned

def match_label(text, patterns):
    for label, keywords in patterns.items():
        for keyword in keywords:
            if keyword.lower() in text.lower():
                return label
    return None

def process_dataframe(df, company_name):
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
        if row_data['Gross Profit'] is None and row_data['Revenue'] and row_data['COGS']:
            row_data['Gross Profit'] = row_data['Revenue'] - row_data['COGS']
        if row_data['Operating Income'] is None and row_data['Gross Profit'] and row_data['Operating Expenses']:
            row_data['Operating Income'] = row_data['Gross Profit'] - row_data['Operating Expenses']
        if row_data['Net Income'] is None:
            if row_data['Operating Income'] is not None:
                row_data['Net Income'] = row_data['Operating Income']
            elif all(v is not None for v in [row_data['Revenue'], row_data['COGS'], row_data['Operating Expenses']]):
                row_data['Net Income'] = row_data['Revenue'] - row_data['COGS'] - row_data['Operating Expenses']
        results.append(row_data)
    return pd.DataFrame(results)

def period_to_numeric(period_str):
    if isinstance(period_str, str):
        match = re.search(r'FY(\d{4})', period_str)
        if match:
            return int(match.group(1))
        match = re.search(r'Q([1-4])\s+(\d{4})', period_str)
        if match:
            q, y = int(match.group(1)), int(match.group(2))
            return y + (q - 1) * 0.25
        match = re.search(r'H([1-2])\s+(\d{4})', period_str)
        if match:
            h, y = int(match.group(1)), int(match.group(2))
            return y + (h - 1) * 0.5
    return None

def clean_and_impute(df):
    financial_cols = ['Revenue', 'COGS', 'Gross Profit', 'Operating Expenses', 'Operating Income', 'Net Income']
    df = df.dropna(subset=financial_cols, how='all')
    for col in financial_cols:
        df[col] = df[col].fillna(df[col].mean())
    return df

def remove_outliers_iqr(df):
    financial_cols = ['Revenue', 'COGS', 'Gross Profit', 'Operating Expenses', 'Operating Income', 'Net Income']
    for col in financial_cols:
        Q1 = df[col].quantile(0.25)
        Q3 = df[col].quantile(0.75)
        IQR = Q3 - Q1
        lower = Q1 - 1.5 * IQR
        upper = Q3 + 1.5 * IQR
        df = df[(df[col] >= lower) & (df[col] <= upper)]
    return df

def extract_quarter(period_str):
    match = re.search(r'Q([1-4])', period_str)
    return f"Q{match.group(1)}" if match else None

# --- Main Execution ---
all_dfs = []
for path in input_paths:
    company = os.path.basename(path).split('_')[0]
    df = pd.read_csv(path)
    processed = process_dataframe(df, company)
    all_dfs.append(processed)

combined = pd.concat(all_dfs, ignore_index=True)
combined['period'] = combined['period'].fillna("Unknown")
combined['period_numeric'] = combined['period'].apply(period_to_numeric)
combined = clean_and_impute(combined)
combined = remove_outliers_iqr(combined)

# --- Quarter-based Split ---
combined['quarter'] = combined['period'].apply(extract_quarter)
for q in ['Q1', 'Q2', 'Q3', 'Q4']:
    quarter_df = combined[combined['quarter'] == q]
    if not quarter_df.empty:
        quarter_df.to_csv(os.path.join(output_dir, f"financial_summary_{q}.csv"), index=False)

# Save full summary
combined.to_csv(os.path.join(output_dir, "financial_summary_all.csv"), index=False)
