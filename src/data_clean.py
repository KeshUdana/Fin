import pandas as pd
import re

# Load the CSV
file_path = 'data/processed/REXP/consolidated_income_all.csv'
df = pd.read_csv(file_path, header=None)

# Convert all rows to a single long string for easier regex parsing
raw_text = ' '.join(df.astype(str).values.flatten())
