"""
InvoiceIQ Data Quality Audit Engine
Inspects datasets for missing values, exact and key duplicates,
chronological inconsistencies, numerical anomalies, extreme IQR outliers,
and categorical defects. Exports data_quality_report.csv.
"""

import pandas as pd
import numpy as np

def run_quality_audit(df, mapping=None):
    """
    Executes a comprehensive data quality audit across 5 dimensions:
    1. Missing Values
    2. Duplicate Records
    3. Date & Chronological Validation
    4. Numerical & Outlier Checks
    5. Categorical & Text Standardization
    """
    if df is None or df.empty:
        return pd.DataFrame(), {}

    issues = []
    total_rows = len(df)
    
    # -------------------------------------------------------------
    # 1. Missing Values Audit
    # -------------------------------------------------------------
    critical_cols = [c for c in ['invoice_id', 'invoice_number', 'total_amount', 'invoice_date', 'due_date'] if c in df.columns]
    
    null_counts = df.isnull().sum()
    for col in df.columns:
        cnt = int(null_counts[col])
        if cnt > 0:
            pct = (cnt / total_rows) * 100
            sev = "Critical" if col in critical_cols else ("High" if pct > 10 else "Medium")
            rec = "Investigate source or impute via business rule" if col not in critical_cols else "Flag or reject record without primary key/amount"
            issues.append({
                "Category": "Missing Values",
                "Issue": f"Missing values in {col}",
                "Affected Column": col,
                "Affected Rows": cnt,
                "Percentage": f"{pct:.2f}%",
                "Severity": sev,
                "Recommended Action": rec
            })
            
    # -------------------------------------------------------------
    # 2. Duplicate Records Audit
    # -------------------------------------------------------------
    exact_dups = int(df.duplicated().sum())
    if exact_dups > 0:
        pct = (exact_dups / total_rows) * 100
        issues.append({
            "Category": "Duplicate Records",
            "Issue": "Exact duplicate rows detected",
            "Affected Column": "All Columns",
            "Affected Rows": exact_dups,
            "Percentage": f"{pct:.2f}%",
            "Severity": "High",
            "Recommended Action": "Deduplicate dataset preserving primary occurrence"
        })
        
    id_col = 'invoice_number' if 'invoice_number' in df.columns else ('invoice_id' if 'invoice_id' in df.columns else None)
    if id_col:
        id_dups = int(df.duplicated(subset=[id_col]).sum()) - exact_dups
        if id_dups > 0:
            pct = (id_dups / total_rows) * 100
            issues.append({
                "Category": "Duplicate Records",
                "Issue": f"Duplicate primary key ({id_col}) with differing attributes",
                "Affected Column": id_col,
                "Affected Rows": id_dups,
                "Percentage": f"{pct:.2f}%",
                "Severity": "Critical",
                "Recommended Action": "Investigate transaction collision or append revision suffix"
            })

    # -------------------------------------------------------------
    # 3. Date & Chronological Validation
    # -------------------------------------------------------------
    date_cols = [c for c in df.columns if 'date' in c.lower()]
    for dcol in date_cols:
        parsed = pd.to_datetime(df[dcol], errors='coerce')
        unparseable = int(parsed.isnull().sum() - df[dcol].isnull().sum())
        if unparseable > 0:
            pct = (unparseable / total_rows) * 100
            issues.append({
                "Category": "Date Validation",
                "Issue": f"Unparseable date formats in {dcol}",
                "Affected Column": dcol,
                "Affected Rows": unparseable,
                "Percentage": f"{pct:.2f}%",
                "Severity": "Critical",
                "Recommended Action": "Standardize to ISO-8601 (YYYY-MM-DD)"
            })
            
    # Chronological checks
    if 'invoice_date' in df.columns and 'due_date' in df.columns:
        inv_d = pd.to_datetime(df['invoice_date'], errors='coerce')
        due_d = pd.to_datetime(df['due_date'], errors='coerce')
        due_before_inv = int((due_d < inv_d).sum())
        if due_before_inv > 0:
            pct = (due_before_inv / total_rows) * 100
            issues.append({
                "Category": "Date Validation",
                "Issue": "Due date precedes invoice issue date",
                "Affected Column": "due_date",
                "Affected Rows": due_before_inv,
                "Percentage": f"{pct:.2f}%",
                "Severity": "Critical",
                "Recommended Action": "Flag as chronological defect; verify payment terms"
            })
            
    # Check for placeholder payment dates on unpaid invoices
    if 'payment_status' in df.columns and 'payment_date' in df.columns and 'due_date' in df.columns:
        unpaid_mask = df['payment_status'].str.strip().str.lower().isin(['pending', 'overdue', 'cancelled'])
        if unpaid_mask.any():
            same_date_cnt = int((df.loc[unpaid_mask, 'payment_date'] == df.loc[unpaid_mask, 'due_date']).sum())
            if same_date_cnt > 0:
                pct = (same_date_cnt / total_rows) * 100
                issues.append({
                    "Category": "Date Validation",
                    "Issue": "Synthetic placeholder: payment_date matches due_date on unpaid invoices",
                    "Affected Column": "payment_date",
                    "Affected Rows": same_date_cnt,
                    "Percentage": f"{pct:.2f}%",
                    "Severity": "High",
                    "Recommended Action": "Set payment_date to NaT for unpaid invoices to prevent false 0-day delays"
                })

    # Paid invoices where payment date is before invoice date
    if 'payment_status' in df.columns and 'payment_date' in df.columns and 'invoice_date' in df.columns:
        paid_mask = df['payment_status'].str.strip().str.lower() == 'paid'
        if paid_mask.any():
            inv_d = pd.to_datetime(df.loc[paid_mask, 'invoice_date'], errors='coerce')
            pay_d = pd.to_datetime(df.loc[paid_mask, 'payment_date'], errors='coerce')
            pay_before_inv = int((pay_d < inv_d).sum())
            if pay_before_inv > 0:
                pct = (pay_before_inv / total_rows) * 100
                issues.append({
                    "Category": "Date Validation",
                    "Issue": "Payment date precedes invoice issuance date",
                    "Affected Column": "payment_date",
                    "Affected Rows": pay_before_inv,
                    "Percentage": f"{pct:.2f}%",
                    "Severity": "Critical",
                    "Recommended Action": "Investigate advance settlement or billing timestamp mismatch"
                })

    # -------------------------------------------------------------
    # 4. Numerical Validation & IQR Outliers
    # -------------------------------------------------------------
    amount_col = 'total_amount' if 'total_amount' in df.columns else ('amount' if 'amount' in df.columns else None)
    if amount_col:
        neg_amounts = int((df[amount_col] < 0).sum())
        if neg_amounts > 0:
            pct = (neg_amounts / total_rows) * 100
            issues.append({
                "Category": "Numerical Validation",
                "Issue": f"Negative monetary amount in {amount_col}",
                "Affected Column": amount_col,
                "Affected Rows": neg_amounts,
                "Percentage": f"{pct:.2f}%",
                "Severity": "Critical",
                "Recommended Action": "Investigate credit note / reversal or adjust polarity"
            })
            
        zero_amounts = int((df[amount_col] == 0).sum())
        if zero_amounts > 0:
            pct = (zero_amounts / total_rows) * 100
            issues.append({
                "Category": "Numerical Validation",
                "Issue": f"Zero monetary value in {amount_col}",
                "Affected Column": amount_col,
                "Affected Rows": zero_amounts,
                "Percentage": f"{pct:.2f}%",
                "Severity": "Medium",
                "Recommended Action": "Verify complimentary / warranty dispatch or data omission"
            })
            
        # IQR Outlier Detection
        valid_vals = df[amount_col].dropna()
        if len(valid_vals) > 10:
            q25 = valid_vals.quantile(0.25)
            q75 = valid_vals.quantile(0.75)
            iqr = q75 - q25
            upper_bound = q75 + 3.0 * iqr  # Extreme outlier cutoff
            outlier_cnt = int((valid_vals > upper_bound).sum())
            if outlier_cnt > 0:
                pct = (outlier_cnt / total_rows) * 100
                issues.append({
                    "Category": "Numerical Validation",
                    "Issue": f"Statistical extreme amounts (> Q3 + 3*IQR: {upper_bound:,.2f})",
                    "Affected Column": amount_col,
                    "Affected Rows": outlier_cnt,
                    "Percentage": f"{pct:.2f}%",
                    "Severity": "Low",
                    "Recommended Action": "Flag as statistical outlier for audit; do not delete valid enterprise invoices"
                })

    # -------------------------------------------------------------
    # 5. Categorical & Text Validation
    # -------------------------------------------------------------
    str_cols = df.select_dtypes(include=['object', 'string']).columns.tolist()
    for scol in str_cols:
        # Check whitespace
        has_spaces = df[scol].dropna().astype(str).str.contains(r'^\s+|\s+$', regex=True)
        ws_count = int(has_spaces.sum())
        if ws_count > 0:
            pct = (ws_count / total_rows) * 100
            issues.append({
                "Category": "Categorical Validation",
                "Issue": f"Leading or trailing whitespace in {scol}",
                "Affected Column": scol,
                "Affected Rows": ws_count,
                "Percentage": f"{pct:.2f}%",
                "Severity": "Medium",
                "Recommended Action": "Strip whitespace safely across string columns"
            })

    # Currency consistency check
    if 'currency' in df.columns:
        non_standard_curr = df['currency'].dropna().str.strip().str.upper()
        invalid_currs = int((~non_standard_curr.isin(['USD', 'EUR', 'INR', 'GBP', 'AUD', 'CAD', 'SGD', 'JPY', 'AED'])).sum())
        if invalid_currs > 0:
            pct = (invalid_currs / total_rows) * 100
            issues.append({
                "Category": "Categorical Validation",
                "Issue": "Non-standard or unrecognized currency codes",
                "Affected Column": "currency",
                "Affected Rows": invalid_currs,
                "Percentage": f"{pct:.2f}%",
                "Severity": "Medium",
                "Recommended Action": "Map or harmonize to ISO 4217 currency specifications"
            })

    # Summary dictionary
    summary_stats = {
        "Total Issues Found": len(issues),
        "Critical": sum(1 for i in issues if i["Severity"] == "Critical"),
        "High": sum(1 for i in issues if i["Severity"] == "High"),
        "Medium": sum(1 for i in issues if i["Severity"] == "Medium"),
        "Low": sum(1 for i in issues if i["Severity"] == "Low")
    }

    # If no issues found, provide clean bill of health
    if not issues:
        issues.append({
            "Category": "Quality Health",
            "Issue": "No critical defects detected",
            "Affected Column": "All Columns",
            "Affected Rows": 0,
            "Percentage": "0.00%",
            "Severity": "Low",
            "Recommended Action": "Proceed to preprocessing and feature engineering"
        })

    report_df = pd.DataFrame(issues)
    return report_df, summary_stats

