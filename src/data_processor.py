import os
import re
import pdfplumber
import pandas as pd

input_folder = "./data/raw/REXP/"
output_folder = "./data/processed/REXP/"
output_file = os.path.join(output_folder, "consolidated_income_all.csv")
metrics_file = os.path.join(output_folder, "financial_metrics.csv")

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

def extract_financial_metrics(text):
    metrics = {
        'Period': [],
        'Revenue': [],
        'COGS': [],
        'Gross Profit': [],
        'Operating Expenses': [],
        'Operating Income': [],
        'Net Income': []
    }
    
    patterns = {
        'Revenue': r'Revenue\s+([\d,]+)\s+([\d,]+)',
        'COGS': r'Cost of Sales\s+\(?([\d,]+)\)?\s+\(?([\d,]+)\)?',
        'Gross Profit': r'Gross Profit\s+([\d,]+)\s+([\d,]+)',
        'Operating Income': r'Profit / \(Loss\) from Operations\s+([\d,]+)\s+([\d,]+)',
        'Net Income': r'Profit / \(Loss\) for the period\s+([\d,]+)\s+([\d,]+)'
    }
    
    lines = text.split('\n')
    current_period = ""
    period_pattern = r'(\d+ (months|years?) ended (\d+ \w+|\d+\w+ \w+))'
    
    for line in lines:
        period_match = re.search(period_pattern, line)
        if period_match:
            current_period = period_match.group(1)
            metrics['Period'].append(current_period)
        
        for metric, pattern in patterns.items():
            if metric in line:
                match = re.search(pattern, line)
                if match:
                    value = match.group(1).replace(',', '')
                    if '(' in value:
                        value = '-' + value.replace('(', '').replace(')', '')
                    
                    if metric == 'Revenue':
                        metrics['Revenue'].append(float(value))
                    elif metric == 'COGS':
                        metrics['COGS'].append(float(value))
                    elif metric == 'Gross Profit':
                        metrics['Gross Profit'].append(float(value))
                    elif metric == 'Operating Income':
                        metrics['Operating Income'].append(float(value))
                    elif metric == 'Net Income':
                        metrics['Net Income'].append(float(value))
    
    for i in range(len(metrics['Revenue'])):
        if i < len(metrics['COGS']) and i < len(metrics['Operating Income']):
            op_expenses = metrics['Revenue'][i] + metrics['COGS'][i] - metrics['Operating Income'][i]
            metrics['Operating Expenses'].append(op_expenses)
        else:
            metrics['Operating Expenses'].append(None)
    
    df = pd.DataFrame(metrics)
    df['Period'] = df['Period'].str.replace('months? ended', 'M')
    df['Period'] = df['Period'].str.replace('years? ended', '12M')
    df['Period'] = df['Period'].str.replace(' ', '')
    
    return df

all_data = []
all_metrics = []

for filename in os.listdir(input_folder):
    if filename.lower().endswith(".pdf"):
        pdf_path = os.path.join(input_folder, filename)
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text() or ""
                if page_contains_keyword(text, target_keywords):
                    # Extract detailed rows
                    rows = extract_financial_rows(text)
                    if rows:
                        all_data.extend(rows)
                    
                    # Extract key metrics
                    metrics_df = extract_financial_metrics(text)
                    if not metrics_df.empty:
                        all_metrics.append(metrics_df)
                    
                    break  # stop after finding the first matching page

# Save detailed data to CSV
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

# Save metrics data to CSV
if all_metrics:
    metrics_df = pd.concat(all_metrics, ignore_index=True)
    metrics_df.to_csv(metrics_file, index=False)
    print(f"[✓] Key financial metrics saved to: {metrics_file}")
else:
    print("[!] No financial metrics extracted from PDFs.")