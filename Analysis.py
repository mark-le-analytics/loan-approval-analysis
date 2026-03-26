"""
analysis.py
===========
Loan Approval Data Validation and Risk Analysis

Dataset: Realistic Loan Approval Dataset (US and Canada)
Source:  Kaggle - parthpatel2130

Sections:
    1. Load and Understand
    2. Clean
    3. Validate
    4. Flag and Enrich
    5. Export
"""

import pandas as pd
import numpy as np
from datetime import datetime


# ==============================================================================
# SECTION 1 - LOAD AND UNDERSTAND
# ==============================================================================

print("Section 1 - Loading data...")

df = pd.read_csv("loan_approval_data_2025.csv")

print(f"  Rows: {len(df)}")
print(f"  Columns: {len(df.columns)}")
print(f"  Columns: {list(df.columns)}")
print()
print("  Data types:")
print(df.dtypes.to_string())
print()
print("  First 3 rows:")
print(df.head(3).to_string())

"""
Field reference:
    customer_id              Unique identifier per applicant
    age                      Applicant age in years
    occupation_status        Employment type (employed, self-employed, unemployed, etc.)
    years_employed           How long the applicant has been in their current role
    annual_income            Gross annual income in dollars
    credit_score             Credit score (valid range: 300 - 850)
    credit_history_years     Length of credit history in years
    savings_assets           Total savings and assets held
    current_debt             Total existing debt obligations
    defaults_on_file         Number of previous loan defaults recorded
    delinquencies_last_2yrs  Number of late payments in the last 2 years
    derogatory_marks         Negative marks on credit file (collections, bankruptcies)
    product_type             Type of loan product (personal, mortgage, auto, etc.)
    loan_intent              Stated purpose of the loan
    loan_amount              Amount requested in dollars
    interest_rate            Annual interest rate offered (%)
    debt_to_income_ratio     Current debt divided by annual income
    loan_to_income_ratio     Loan amount divided by annual income
    payment_to_income_ratio  Estimated monthly payment divided by monthly income
    loan_status              Outcome - Approved or Rejected
"""


# ==============================================================================
# SECTION 2 - CLEAN
# ==============================================================================

print()
print("Section 2 - Cleaning data...")

raw = df.copy()
cleaning_log = []

# --- Remove exact duplicate rows ---
before = len(df)
df = df.drop_duplicates()
cleaning_log.append(f"Duplicate rows removed: {before - len(df)}")

# --- Standardise text columns to lowercase and strip whitespace ---
text_cols = ["occupation_status", "product_type", "loan_intent"]
for col in text_cols:
    if col in df.columns:
        df[col] = df[col].astype(str).str.strip().str.lower()

cleaning_log.append("Text columns standardised to lowercase")

# --- Convert numeric columns that may have loaded as strings ---
numeric_cols = [
    "age", "years_employed", "annual_income", "credit_score",
    "credit_history_years", "savings_assets", "current_debt",
    "defaults_on_file", "delinquencies_last_2yrs", "derogatory_marks",
    "loan_amount", "interest_rate", "debt_to_income_ratio",
    "loan_to_income_ratio", "payment_to_income_ratio"
]
for col in numeric_cols:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

# Standardise interest rate format
if "interest_rate" in df.columns:
    df["interest_rate"] = df["interest_rate"].apply(
        lambda x: x / 100 if pd.notna(x) and x > 1 else x
    )
    df["interest_rate"] = df["interest_rate"].round(4)


# --- Report missing values per column ---
missing = df.isnull().sum()
missing = missing[missing > 0]
if len(missing) > 0:
    cleaning_log.append("Missing values found:")
    for col, count in missing.items():
        cleaning_log.append(f"  {col}: {count} missing")
else:
    cleaning_log.append("No missing values found")

print(f"  Rows after cleaning: {len(df)}")
for line in cleaning_log:
    print(f"  {line}")


# ==============================================================================
# SECTION 3 - VALIDATE
# ==============================================================================

print()
print("Section 3 - Running validation checks...")

# We collect every flagged record here with a reason
flags = []


def flag(row_index, reason):
    flags.append({"index": row_index, "reason": reason})


# --- 3A. Completeness checks ---
# Flag records where critical fields are missing

critical_fields = {
    "annual_income":  "Missing income",
    "credit_score":   "Missing credit score",
    "loan_amount":    "Missing loan amount",
    "occupation_status": "Missing occupation status",
}

for col, reason in critical_fields.items():
    if col in df.columns:
        for idx in df[df[col].isnull()].index:
            flag(idx, reason)


# --- 3B. Range and validity checks ---

for idx, row in df.iterrows():

    # Credit score must be between 300 and 850
    if pd.notna(row.get("credit_score")):
        if row["credit_score"] < 300 or row["credit_score"] > 850:
            flag(idx, f"Credit score out of valid range ({row['credit_score']})")

    # Income cannot be zero or negative
    if pd.notna(row.get("annual_income")):
        if row["annual_income"] <= 0:
            flag(idx, f"Invalid income ({row['annual_income']})")

    # Loan amount cannot be zero or negative
    if pd.notna(row.get("loan_amount")):
        if row["loan_amount"] <= 0:
            flag(idx, f"Invalid loan amount ({row['loan_amount']})")

    # Age should be between 18 and 100
    if pd.notna(row.get("age")):
        if row["age"] < 18 or row["age"] > 100:
            flag(idx, f"Invalid age ({row['age']})")

    # Interest rate should be between 0 and 100
    if pd.notna(row.get("interest_rate")):
        if row["interest_rate"] < 0 or row["interest_rate"] > 1:
            flag(idx, f"Invalid interest rate ({row['interest_rate']})")

    # Years employed cannot be negative
    if pd.notna(row.get("years_employed")):
        if row["years_employed"] < 0:
            flag(idx, f"Negative years employed ({row['years_employed']})")

    # Current debt cannot be negative
    if pd.notna(row.get("current_debt")):
        if row["current_debt"] < 0:
            flag(idx, f"Negative current debt ({row['current_debt']})")


# --- 3C. Business rule validation ---
# These checks go beyond data quality into lending logic

for idx, row in df.iterrows():

    income = row.get("annual_income")
    loan   = row.get("loan_amount")
    score  = row.get("credit_score")
    status = row.get("loan_status")
    dti    = row.get("debt_to_income_ratio")

    # Loan amount more than 5x annual income is high risk
    if pd.notna(income) and pd.notna(loan) and income > 0:
        if loan / income > 5:
            flag(idx, f"Loan amount exceeds 5x annual income (ratio: {round(loan/income, 2)})")

    # Approved loan with very low credit score (below 500)
    if pd.notna(score) and pd.notna(status):
        if score < 500 and status == 1:
            flag(idx, f"Approved with low credit score ({score})")

    # Rejected loan with very high credit score (above 750)
    if pd.notna(score) and pd.notna(status):
        if score > 750 and status == 0:
            flag(idx, f"Rejected with high credit score ({score}) - possible policy inconsistency")

    # Debt-to-income ratio above 60% is high risk
    if pd.notna(dti):
        if dti > 0.60:
            flag(idx, f"High debt-to-income ratio ({round(dti * 100, 1)}%)")

    # Approved loan but applicant has defaults on file
    if pd.notna(row.get("defaults_on_file")) and pd.notna(status):
        if row["defaults_on_file"] > 0 and status == 1:
            flag(idx, f"Approved with {int(row['defaults_on_file'])} default(s) on file")


# --- 3D. Consistency checks ---

for idx, row in df.iterrows():

    income = row.get("annual_income")
    status = row.get("loan_status")
    occ    = row.get("occupation_status")
    years  = row.get("years_employed")

    # Loan approved but applicant has zero income
    if pd.notna(income) and pd.notna(status):
        if income == 0 and status == 1:
            flag(idx, "Approved with zero income")

    # Unemployed but years_employed > 0
    if pd.notna(occ) and pd.notna(years):
        if "unemployed" in str(occ) and years > 0:
            flag(idx, f"Unemployed but years_employed = {years}")

    # Validate pre-calculated loan_to_income_ratio
    if pd.notna(income) and pd.notna(row.get("loan_amount")) and pd.notna(row.get("loan_to_income_ratio")):
        if income > 0:
            expected = round(row["loan_amount"] / income, 4)
            actual   = round(row["loan_to_income_ratio"], 4)
            if abs(expected - actual) > 0.01:
                flag(idx, f"loan_to_income_ratio mismatch (stored: {actual}, calculated: {expected})")

    # Validate pre-calculated debt_to_income_ratio
    if pd.notna(income) and pd.notna(row.get("current_debt")) and pd.notna(row.get("debt_to_income_ratio")):
        if income > 0:
            expected = round(row["current_debt"] / income, 4)
            actual   = round(row["debt_to_income_ratio"], 4)
            if abs(expected - actual) > 0.01:
                flag(idx, f"debt_to_income_ratio mismatch (stored: {actual}, calculated: {expected})")

print(f"  Total flags raised: {len(flags)}")


# ==============================================================================
# SECTION 4 - FLAG AND ENRICH
# ==============================================================================

print()
print("Section 4 - Enriching dataset...")

# --- Build a reasons lookup: one row per customer_id with all reasons combined ---
flags_df = pd.DataFrame(flags)

if len(flags_df) > 0:
    flags_df["customer_id"] = df.loc[flags_df["index"]]["customer_id"].values
    reason_lookup = (
        flags_df
        .groupby("customer_id")["reason"]
        .apply(lambda x: " | ".join(sorted(set(x))))
        .reset_index()
        .rename(columns={"reason": "validation_flags"})
    )
else:
    reason_lookup = pd.DataFrame(columns=["customer_id", "validation_flags"])

# --- Merge flags back onto main dataset ---
df = df.merge(reason_lookup, on="customer_id", how="left")
df["is_flagged"] = df["validation_flags"].notna()

# --- Assign risk category based on credit score and loan-to-income ratio ---
def assign_risk(row):
    score = row.get("credit_score")
    lti   = row.get("loan_to_income_ratio")

    if pd.isna(score) or pd.isna(lti):
        return "unknown"

    if score >= 700 and lti <= 2.5:
        return "low"
    elif score >= 580 and lti <= 4.0:
        return "medium"
    else:
        return "high"

df["risk_category"] = df.apply(assign_risk, axis=1)

print(f"  Flagged records: {df['is_flagged'].sum()}")
print(f"  Risk breakdown:")
print(df["risk_category"].value_counts().to_string())


# ==============================================================================
# SECTION 5 - EXPORT
# ==============================================================================

print()
print("Section 5 - Exporting results...")

today_str = datetime.today().strftime("%Y-%m-%d")

# --- Clean dataset: all records with enriched columns ---
clean_export = df.copy()

# --- Flagged records only ---
flagged_export = df[df["is_flagged"]].copy()

# --- Summary ---
total            = len(df)
total_flagged    = int(df["is_flagged"].sum())
total_approved   = int((df["loan_status"] == 1).sum())
total_rejected   = int((df["loan_status"] == 0).sum())
high_risk        = int((df["risk_category"] == "high").sum())
medium_risk      = int((df["risk_category"] == "medium").sum())
low_risk         = int((df["risk_category"] == "low").sum())

# Flag type breakdown
if len(flags_df) > 0:
    flag_counts = flags_df["reason"].str.split(" - ").str[0].value_counts()
else:
    flag_counts = pd.Series(dtype=int)

summary = pd.DataFrame([
    {"Metric": "Total records",                "Value": total},
    {"Metric": "Total flagged records",        "Value": total_flagged},
    {"Metric": "Flagged rate (%)",             "Value": round(total_flagged / total * 100, 2)},
    {"Metric": "Total approved loans",         "Value": total_approved},
    {"Metric": "Total rejected loans",         "Value": total_rejected},
    {"Metric": "Approval rate (%)",            "Value": round(total_approved / total * 100, 2)},
    {"Metric": "High risk records",            "Value": high_risk},
    {"Metric": "Medium risk records",          "Value": medium_risk},
    {"Metric": "Low risk records",             "Value": low_risk},
    {"Metric": "Avg credit score",             "Value": round(df["credit_score"].mean(), 1)},
    {"Metric": "Avg loan amount ($)",          "Value": round(df["loan_amount"].mean(), 2)},
    {"Metric": "Avg annual income ($)",        "Value": round(df["annual_income"].mean(), 2)},
    {"Metric": "Avg debt-to-income ratio",     "Value": round(df["debt_to_income_ratio"].mean(), 4)},
])

# --- Write to Excel ---
output_file = "loan_approval_analysis.xlsx"

with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
    clean_export.to_excel(writer,   sheet_name="Full Dataset",      index=False)
    flagged_export.to_excel(writer, sheet_name="Flagged Records",   index=False)
    summary.to_excel(writer,        sheet_name="Summary",           index=False)

# --- Write validation log to text file ---
with open("validation_log.txt", "w") as f:
    f.write(f"Loan Approval Validation Report\n")
    f.write(f"Run date: {today_str}\n")
    f.write(f"{'='*50}\n\n")
    f.write(f"Total records:     {total}\n")
    f.write(f"Total flagged:     {total_flagged}\n")
    f.write(f"Flagged rate:      {round(total_flagged / total * 100, 2)}%\n\n")
    f.write("Flag breakdown:\n")
    for line in cleaning_log:
        f.write(f"  {line}\n")
    f.write("\nBusiness interpretation:\n")
    f.write("  High loan-to-income ratios may indicate higher default risk.\n")
    f.write("  Approvals with low credit scores suggest potential policy inconsistencies.\n")
    f.write("  Approved loans with defaults on file warrant manual review.\n")
    f.write("  DTI above 60% indicates the applicant is already heavily leveraged.\n")
    f.write("  Unemployed applicants with employment years recorded may be data entry errors.\n")

print(f"  Output saved: {output_file}")
print(f"  Validation log saved: validation_log.txt")
print()
print("Done.")
print()
print(summary.to_string(index=False))