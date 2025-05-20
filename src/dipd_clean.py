import pandas as pd
import re
import spacy

# Load spaCy NLP model
nlp = spacy.load("en_core_web_sm")

# Load CSV
csv_path = "data\processed_nlp\DIPD_income_nlp.csv"
df = pd.read_csv(csv_path)
df.rename(columns={"Source File": "filename", "Page": "page", "Line": "text"}, inplace=True)

# Define financial keywords for flexible matching
financial_keywords = {
    'Revenue': ['Revenue', 'Turnover'],
    'COGS': ['Cost of Sales', 'Cost of Goods Sold'],
    'Gross Profit': ['Gross Profit'],
    'Operating Expenses': ['Distribution Costs', 'Administrative expenses'],
    'Operating Income': ['Profit / (loss) from Operations'],
    'Net Income': ['Profit / (loss) for the period', 'Profit / (loss) Attributable to Ordinary Shareholders']
}

def match_label(text, patterns):
    for label, keywords in patterns.items():
        for keyword in keywords:
            if keyword.lower() in text.lower():
                return label
    return None

def extract_numbers(text):
    # Match integers with optional commas and negative/parentheses
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

# Process by (filename, page)
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

        label = match_label(text, financial_keywords)
        if label:
            numbers = extract_numbers(text)
            if numbers:
                row_data[label] = numbers[0]

    # Ensure COGS is positive
    if row_data['COGS'] is not None:
        row_data['COGS'] = abs(row_data['COGS'])

    # Calculate Gross Profit
    if row_data['Revenue'] is not None and row_data['COGS'] is not None:
        row_data['Gross Profit'] = row_data['Revenue'] - row_data['COGS']

    # Calculate Operating Income
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

# Save to CSV
final_df = pd.DataFrame(results)
print(final_df)
final_df.to_csv("DIPD_financial_summary.csv", index=False)
