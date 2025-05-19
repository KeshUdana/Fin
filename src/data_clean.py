import pandas as pd

# === STEP 1: Load raw stacked data ===
document_path = "data\\processed\\REXP\\consolidated_income_all.csv"
df = pd.read_csv(document_path)

# === STEP 2: Clean column names ===
df.columns = df.columns.str.strip()
df["Item"] = df["Item"].astype(str).str.strip()

# === STEP 3: Identify start of each block (i.e., every time "Revenue" appears) ===
revenue_indices = df[df["Item"] == "Revenue"].index.tolist()

# === STEP 4: Helper function to extract one block ===
def extract_cleaned_block(start_idx):
    block = df.iloc[start_idx:start_idx + 18]  # relevant block ~18 rows
    block = block.reset_index(drop=True)
    
    def get_val(item, col):
        match = block[block["Item"].str.strip() == item]
        if match.empty:
            return 0.0
        val_str = str(match[col].values[0]).strip()

        if val_str in ["-", "", "–"]:
            return 0.0

        # Convert (12345) to -12345
        if "(" in val_str and ")" in val_str:
            val_str = val_str.replace("(", "-").replace(")", "")

        # Remove commas and spaces
        val_str = val_str.replace(",", "").replace(" ", "")

        # Fix negative numbers with leading zeros, e.g. '-0375238'
        if val_str.startswith("-"):
            # remove leading zeros after minus sign
            val_str = "-" + val_str[1:].lstrip("0")
            if val_str == "-":
                val_str = "0"
        else:
            # remove leading zeros for positive numbers
            val_str = val_str.lstrip("0")
            if val_str == "":
                val_str = "0"

        try:
            return float(val_str)
        except ValueError:
            return 0.0  # fallback if conversion fails

    def operating_expenses(col):
        return (
            get_val("Distribution Costs", col) +
            get_val("Administrative Expenses", col) +
            get_val("Other Operating Expenses", col)
        )
    
    return {
        "Period": "Q1_Current",
        "Revenue": get_val("Revenue", "Q1_This_Year"),
        "COGS": get_val("Cost of Sales", "Q1_This_Year"),
        "Gross Profit": get_val("Gross Profit", "Q1_This_Year"),
        "Operating Expenses": operating_expenses("Q1_This_Year"),
        "Operating Income": get_val("Profit / (Loss) from Operations", "Q1_This_Year"),
        "Net Income": get_val("Profit / (Loss) for the period", "Q1_This_Year")
    }

# === STEP 5: Loop through all blocks and extract cleaned data ===
all_cleaned = []
for idx in revenue_indices:
    try:
        cleaned_row = extract_cleaned_block(idx)
        all_cleaned.append(cleaned_row)
    except Exception as e:
        print(f"⚠️ Skipped block at index {idx} due to error: {e}")

# === STEP 6: Save the cleaned output ===
cleaned_df = pd.DataFrame(all_cleaned)
cleaned_df.to_csv("cleaned_financials.csv", index=False)

print("✅ Cleaned CSV saved as 'cleaned_financials.csv'")

