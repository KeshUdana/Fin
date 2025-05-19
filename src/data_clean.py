import pandas as pd
import re

def extract_financial_metrics(data):
    # Initialize dictionary to store metrics
    metrics = {
        'Period': [],
        'Revenue': [],
        'COGS': [],
        'Gross Profit': [],
        'Operating Expenses': [],
        'Operating Income': [],
        'Net Income': []
    }
    
    # Regular expressions to identify each metric
    patterns = {
        'Revenue': r'Revenue\s+([\d,]+)\s+([\d,]+)',
        'COGS': r'Cost of Sales\s+\(?([\d,]+)\)?\s+\(?([\d,]+)\)?',
        'Gross Profit': r'Gross Profit\s+([\d,]+)\s+([\d,]+)',
        'Operating Income': r'Profit / \(Loss\) from Operations\s+([\d,]+)\s+([\d,]+)',
        'Net Income': r'Profit / \(Loss\) for the period\s+([\d,]+)\s+([\d,]+)'
    }
    
    # Split data into lines
    lines = data.split('\n')
    
    current_period = ""
    period_pattern = r'(\d+ (months|years?) ended (\d+ \w+|\d+\w+ \w+))'
    
    for line in lines:
        # Check for period
        period_match = re.search(period_pattern, line)
        if period_match:
            current_period = period_match.group(1)
            metrics['Period'].append(current_period)
        
        # Extract metrics
        for metric, pattern in patterns.items():
            if metric in line:
                match = re.search(pattern, line)
                if match:
                    value = match.group(1).replace(',', '')
                    if '(' in value:
                        value = '-' + value.replace('(', '').replace(')', '')
                    
                    # Handle different metrics
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
    
    # Calculate Operating Expenses (COGS + Operating Expenses = Revenue - Operating Income)
    for i in range(len(metrics['Revenue'])):
        if i < len(metrics['COGS']) and i < len(metrics['Operating Income']):
            op_expenses = metrics['Revenue'][i] + metrics['COGS'][i] - metrics['Operating Income'][i]
            metrics['Operating Expenses'].append(op_expenses)
        else:
            metrics['Operating Expenses'].append(None)
    
    # Create DataFrame
    df = pd.DataFrame(metrics)
    
    # Clean period format
    df['Period'] = df['Period'].str.replace('months? ended', 'M')
    df['Period'] = df['Period'].str.replace('years? ended', '12M')
    df['Period'] = df['Period'].str.replace(' ', '')
    
    return df

# Example usage with your data
with open('financial_data.txt', 'r') as file:
    raw_data = file.read()

# Extract metrics
financial_metrics = extract_financial_metrics(raw_data)

# Save to CSV
financial_metrics.to_csv('financial_metrics.csv', index=False)

print("Financial metrics extracted and saved to financial_metrics.csv")
print(financial_metrics.head())