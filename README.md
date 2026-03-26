# Loan Approval Data Validation and Risk Analysis

A Python-based data validation and risk analysis pipeline applied to a loan approval dataset of 50,000 records across the US and Canadian lending market.

---

## Project Overview

This project simulates the work of a data analyst inside a lending or credit risk team — validating raw loan application data, applying business rules, flagging anomalies, and producing a structured output ready for review.

It is the second of two projects covering the full lending lifecycle:

| Project | Stage | Focus |
|---|---|---|
| Loan Portfolio ETL Pipeline | Repayment stage | Reconciliation, reporting automation |
| Loan Approval Analysis (this project) | Approval stage | Validation, risk logic, anomaly detection |

---

## Dataset

Source: Kaggle - Realistic Loan Approval Dataset (US and Canada)
Records: 50,000 loan applications
File: loan_approval_data_2025.csv

Key fields:

| Field | Description |
|---|---|
| customer_id | Unique applicant identifier |
| age | Applicant age in years |
| occupation_status | Employment type |
| annual_income | Gross annual income ($) |
| credit_score | Credit score (valid range: 300-850) |
| loan_amount | Amount requested ($) |
| debt_to_income_ratio | Current debt divided by annual income |
| loan_to_income_ratio | Loan amount divided by annual income |
| loan_status | Outcome - 1 = Approved, 0 = Rejected |

---

## What the Script Does

### Section 1 - Load and Understand
Loads the dataset and prints shape, data types, and a field reference for all 20 columns.

### Section 2 - Clean
- Removes exact duplicate rows
- Standardises text columns to lowercase
- Converts numeric columns that may have loaded as strings
- Reports missing values per column

### Section 3 - Validate
Runs four layers of validation checks:

**A. Completeness checks**
Flags records where critical fields are missing - income, credit score, loan amount, occupation status.

**B. Range and validity checks**
- Credit score outside 300-850
- Zero or negative income
- Zero or negative loan amount
- Age outside 18-100
- Invalid interest rate
- Negative years employed or current debt

**C. Business rule validation**
- Loan amount exceeds 5x annual income
- Approved loan with credit score below 500
- Rejected loan with credit score above 750 - possible policy inconsistency
- Debt-to-income ratio above 60%
- Approved loan with defaults on file

**D. Consistency checks**
- Approved loan with zero income
- Unemployed applicant with years_employed > 0
- Recalculates loan_to_income_ratio and debt_to_income_ratio from raw fields and flags mismatches against stored values

### Section 4 - Flag and Enrich
- Merges all validation flags back onto the main dataset as a validation_flags column
- Multiple flags per record are separated by |
- Assigns a risk_category (low / medium / high) based on credit score and loan-to-income ratio

### Section 5 - Export
Produces loan_approval_analysis.xlsx with three sheets and a plain text validation log.

---

## Output

```
loan_approval_analysis.xlsx
    Full Dataset       All 50,000 records with validation_flags and risk_category columns added
    Flagged Records    Only records that failed one or more validation checks
    Summary            Headline metrics across the full dataset

validation_log.txt
    Run date, record counts, flag breakdown, business interpretation notes
```

### Sample Summary Output
```
Total records:               50,000
Total flagged records:        2,059
Flagged rate (%):              4.12
High risk records:            8,038
Medium risk records:         32,267
Low risk records:             9,695
Avg credit score:              643.6
Avg loan amount ($):        33,041.87
Avg annual income ($):      50,062.89
Avg debt-to-income ratio:      0.2857
```

---

## Business Interpretation

- High loan-to-income ratios may indicate higher default risk
- Approvals with low credit scores suggest potential policy inconsistencies worth reviewing
- Approved loans with defaults on file warrant manual underwriting review
- DTI above 60% indicates the applicant is already heavily leveraged before taking on new debt
- Unemployed applicants with employment years recorded are likely data entry errors

---

## How to Run

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Place the dataset in the project folder
```
loan_approval_project/
    analysis.py
    loan_approval_data_2025.csv
```

### 3. Run the script
```bash
python analysis.py
```

---

## Requirements

- Python 3.10+
- pandas
- numpy
- openpyxl

---

## Skills Demonstrated

- Python data validation pipeline design
- Business rule logic applied to financial data
- Anomaly and inconsistency detection
- Risk categorisation
- Multi-layered validation with structured reason flagging
- Automated Excel reporting with openpyxl
