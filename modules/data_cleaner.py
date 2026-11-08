"""
InvoiceIQ Data Cleaning Engine
Implements actual data cleaning operations, categorical standardization,
date coercion, IQR outlier flagging, synthetic placeholder sanitization,
missing value imputation, before/after metrics, and cleaning log generation.
"""

import pandas as pd
import numpy as np
from datetime import datetime

class DataCleaner:
    def __init__(self, df):
        self.raw_df = df.copy()
        self.df = df.copy()
        self.cleaning_log = []
        self.before_stats = self._capture_stats(self.raw_df)
        self.after_stats = None

    def _capture_stats(self, df):
        """Captures snapshot of row count, missing values, duplicates, and memory."""
        return {
            "row_count": len(df),
            "col_count": len(df.columns),
            "missing_count": int(df.isnull().sum().sum()),
            "duplicate_count": int(df.duplicated().sum()),
            "outliers_flagged": int(df['is_amount_outlier'].sum()) if 'is_amount_outlier' in df.columns else 0,
            "suspicious_flagged": int(df['is_suspicious_record'].sum()) if 'is_suspicious_record' in df.columns else 0
        }

    def _log_action(self, issue, column, action, reason, affected_rows, status="Success"):
        """Records a timestamped entry in the audit cleaning log."""
        self.cleaning_log.append({
            "Issue": issue,
            "Column Name": column,
            "Action Taken": action,
            "Reason": reason,
            "Rows Affected": int(affected_rows),
            "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Status": status
        })

    def remove_duplicates(self):
        """Removes exact duplicate rows while strictly preserving distinct transactions."""
        initial_count = len(self.df)
        dup_mask = self.df.duplicated()
        dup_count = int(dup_mask.sum())
        
        if dup_count > 0:
            self.df = self.df.drop_duplicates().reset_index(drop=True)
            self._log_action(
                issue="Exact Duplicate Records",
                column="All Columns",
                action="Removed duplicate rows via drop_duplicates()",
                reason="Eliminate redundant record transmission and prevent double-counting of receivables",
                affected_rows=dup_count
            )
        else:
            self._log_action(
                issue="Exact Duplicate Records",
                column="All Columns",
                action="Verified uniqueness",
                reason="Dataset confirmed free of exact duplicated entries",
                affected_rows=0
            )
        return self

    def standardize_column_names(self):
        """Standardizes column names to clean lowercase snake_case."""
        old_cols = self.df.columns.tolist()
        new_cols = [c.strip().lower().replace(" ", "_").replace("-", "_").replace(".", "_") for c in old_cols]
        changed = sum(1 for o, n in zip(old_cols, new_cols) if o != n)
        
        self.df.columns = new_cols
        self._log_action(
            issue="Column Naming Consistency",
            column="Header Schema",
            action="Standardized to lowercase snake_case",
            reason="Ensure programmatic reliability and prevent case-sensitive key lookup failures",
            affected_rows=changed
        )
        return self

    def strip_and_normalize_text(self):
        """Strips leading/trailing whitespace and normalizes string case safely."""
        str_cols = self.df.select_dtypes(include=['object', 'string']).columns.tolist()
        total_affected = 0
        
        for col in str_cols:
            if col in ['invoice_date', 'due_date', 'payment_date']:
                continue
            # Trim whitespace
            trimmed = self.df[col].astype(str).str.strip()
            # Count changes
            diff = (self.df[col].astype(str) != trimmed).sum()
            if diff > 0:
                total_affected += diff
            self.df[col] = trimmed
            
        self._log_action(
            issue="Leading/Trailing Whitespace",
            column="Categorical Columns",
            action="Applied string .strip() across text fields",
            reason="Prevent hidden whitespace from causing foreign key join and filtering misses",
            affected_rows=total_affected
        )
        return self

    def standardize_categorical_labels(self):
        """Normalizes categorical values: payment_status, currency, customer_country."""
        # 1. Payment status
        if 'payment_status' in self.df.columns:
            status_map = {
                'paid': 'Paid',
                'pending': 'Pending',
                'overdue': 'Overdue',
                'cancelled': 'Cancelled',
                'canceled': 'Cancelled',
                'unpaid': 'Pending'
            }
            cleaned_status = self.df['payment_status'].str.strip().str.lower().map(status_map).fillna(self.df['payment_status'])
            diff_cnt = (self.df['payment_status'] != cleaned_status).sum()
            self.df['payment_status'] = cleaned_status
            self._log_action(
                issue="Payment Status Normalization",
                column="payment_status",
                action="Standardized status taxonomy (Paid, Pending, Overdue, Cancelled)",
                reason="Harmonize disparate lifecycle representations into unified financial states",
                affected_rows=diff_cnt
            )

        # 2. Currency
        if 'currency' in self.df.columns:
            curr_cleaned = self.df['currency'].str.strip().str.upper()
            diff_cnt = (self.df['currency'] != curr_cleaned).sum()
            self.df['currency'] = curr_cleaned
            self._log_action(
                issue="Currency Standardization",
                column="currency",
                action="Enforced uppercase ISO 4217 standard codes",
                reason="Ensure standard 3-character ISO currency representations",
                affected_rows=diff_cnt
            )
        return self

    def sanitize_unpaid_payment_dates(self):
        """
        CRITICAL FINANCIAL RULE:
        In the raw dataset, Pending/Overdue/Cancelled invoices have payment_date set equal to due_date.
        Because settlement has not occurred, setting payment_date = NaT prevents fraudulent 0-day delay calculations!
        """
        if 'payment_status' in self.df.columns and 'payment_date' in self.df.columns:
            # Identify non-paid rows
            unpaid_mask = self.df['payment_status'].str.strip().str.lower().isin(['pending', 'overdue', 'cancelled'])
            
            # Count rows where payment_date is currently populated
            populated_unpaid = unpaid_mask & self.df['payment_date'].notnull()
            affected = int(populated_unpaid.sum())
            
            if affected > 0:
                # Store original raw payment date for auditing before sanitizing
                self.df['raw_payment_date_audit'] = self.df['payment_date'].copy()
                self.df.loc[unpaid_mask, 'payment_date'] = np.nan
                
                self._log_action(
                    issue="Synthetic Placeholder on Unsettled Invoices",
                    column="payment_date",
                    action="Set payment_date to NaT for Pending, Overdue, and Cancelled invoices",
                    reason="Prevent artificial zero-day payment delay calculation on unsettled accounts",
                    affected_rows=affected
                )
        return self

    def parse_and_validate_dates(self):
        """Parses date fields into ISO datetime objects, tracking unparseable dates."""
        date_cols = [c for c in ['invoice_date', 'due_date', 'payment_date'] if c in self.df.columns]
        
        for col in date_cols:
            raw_series = self.df[col].copy()
            parsed = pd.to_datetime(self.df[col], errors='coerce')
            unparseable_cnt = int(parsed.isnull().sum() - raw_series.isnull().sum())
            
            self.df[col] = parsed
            self._log_action(
                issue="Date Format Standardization",
                column=col,
                action="Parsed to pd.to_datetime (ISO-8601 YYYY-MM-DD)",
                reason="Enable calendar arithmetic, delay calculation, and temporal grouping",
                affected_rows=len(self.df) - int(self.df[col].isnull().sum())
            )
            
            if unparseable_cnt > 0:
                self._log_action(
                    issue="Unparseable Dates Coerced to NaT",
                    column=col,
                    action="Coerced malformed dates to NaT",
                    reason="Prevent corrupt calendar dates from distorting chronology",
                    affected_rows=unparseable_cnt,
                    status="Warning"
                )
        return self

    def convert_numerical_columns(self):
        """Ensures monetary, quantity, and tax attributes are clean float/int types."""
        num_candidates = [
            'total_amount', 'subtotal', 'unit_price', 'quantity', 
            'discount_percent', 'tax_percent', 'discount_amount', 
            'tax_amount', 'shipping_cost'
        ]
        
        for col in num_candidates:
            if col in self.df.columns:
                self.df[col] = pd.to_numeric(self.df[col], errors='coerce')
                
        self._log_action(
            issue="Numerical Type Casting",
            column="Financial Columns",
            action="Converted monetary and quantity fields via pd.to_numeric()",
            reason="Enable accurate aggregation, KPI computation, and statistical profiling",
            affected_rows=len(self.df)
        )
        return self

    def handle_missing_values(self, num_strategy="preserve", cat_strategy="preserve"):
        """
        Handles missing values based on user strategy:
        - Numerical: 'mean', 'median', or 'preserve'
        - Categorical: 'mode' or 'preserve'
        NOTE: Never blindly imputes primary keys or dates!
        """
        num_cols = self.df.select_dtypes(include=[np.number]).columns.tolist()
        # Exclude IDs, flags, and engineered columns
        excluded_num = ['invoice_id', 'is_overdue', 'paid_late_flag']
        num_cols = [c for c in num_cols if c not in excluded_num]
        
        if num_strategy in ["mean", "median"]:
            for col in num_cols:
                null_cnt = int(self.df[col].isnull().sum())
                if null_cnt > 0:
                    val = self.df[col].mean() if num_strategy == "mean" else self.df[col].median()
                    self.df[col] = self.df[col].fillna(val)
                    self._log_action(
                        issue=f"Missing Values in {col}",
                        column=col,
                        action=f"Imputed missing entries with column {num_strategy} ({val:,.2f})",
                        reason="Ensure numerical continuity for aggregation",
                        affected_rows=null_cnt
                    )

        cat_cols = self.df.select_dtypes(include=['object', 'string']).columns.tolist()
        # Exclude primary keys or date audit
        excluded_cat = ['invoice_number', 'raw_payment_date_audit']
        cat_cols = [c for c in cat_cols if c not in excluded_cat]
        
        if cat_strategy == "mode":
            for col in cat_cols:
                null_cnt = int(self.df[col].isnull().sum())
                if null_cnt > 0:
                    mode_val = self.df[col].mode()[0] if not self.df[col].mode().empty else "Unknown"
                    self.df[col] = self.df[col].fillna(mode_val)
                    self._log_action(
                        issue=f"Missing Values in {col}",
                        column=col,
                        action=f"Imputed missing entries with column mode ('{mode_val}')",
                        reason="Standardize categorical groupings",
                        affected_rows=null_cnt
                    )
                    
        if num_strategy == "preserve" and cat_strategy == "preserve":
            self._log_action(
                issue="Missing Value Retention Strategy",
                column="All Applicable Columns",
                action="Preserved existing nulls with audit visibility",
                reason="Maintain ground-truth integrity without fabricating unverified financial data",
                affected_rows=0
            )
        return self

    def flag_iqr_outliers_and_suspicious(self):
        """
        Identifies extreme statistical outliers using IQR on total_amount,
        and flags suspicious records (e.g. negative values, due_date < invoice_date).
        DOES NOT DELETE: Only flags for transparent audit review.
        """
        # 1. IQR on total_amount
        self.df['is_amount_outlier'] = 0
        if 'total_amount' in self.df.columns:
            valid = self.df['total_amount'].dropna()
            if len(valid) > 10:
                q25 = valid.quantile(0.25)
                q75 = valid.quantile(0.75)
                iqr = q75 - q25
                upper_bound = q75 + 3.0 * iqr
                lower_bound = max(0, q25 - 3.0 * iqr)
                
                outlier_mask = (self.df['total_amount'] > upper_bound) | (self.df['total_amount'] < lower_bound)
                outlier_count = int(outlier_mask.sum())
                self.df.loc[outlier_mask, 'is_amount_outlier'] = 1
                
                self._log_action(
                    issue="Extreme Amount Outliers (IQR Method)",
                    column="total_amount",
                    action=f"Flagged records with is_amount_outlier=1 (Threshold: >{upper_bound:,.2f})",
                    reason="Highlight anomalous high-exposure receivables without deleting valid transactions",
                    affected_rows=outlier_count
                )

        # 2. Suspicious Record Flagging
        self.df['is_suspicious_record'] = 0
        suspicious_mask = pd.Series(False, index=self.df.index)
        
        # Check negative amounts
        if 'total_amount' in self.df.columns:
            suspicious_mask |= (self.df['total_amount'] < 0)
            
        # Check chronological error: due_date < invoice_date
        if 'invoice_date' in self.df.columns and 'due_date' in self.df.columns:
            inv_d = self.df['invoice_date']
            due_d = self.df['due_date']
            chrono_error = (due_d.notnull()) & (inv_d.notnull()) & (due_d < inv_d)
            suspicious_mask |= chrono_error
            
        suspicious_cnt = int(suspicious_mask.sum())
        self.df.loc[suspicious_mask, 'is_suspicious_record'] = 1
        
        self._log_action(
            issue="Suspicious Record Flagging",
            column="Data Integrity",
            action="Tagged anomalies with is_suspicious_record=1",
            reason="Segregate corrupted rows for human supervisor inspection",
            affected_rows=suspicious_cnt
        )
        return self

    def execute_all(self, num_strategy="preserve", cat_strategy="preserve"):
        """Executes the complete standard cleaning pipeline."""
        (
            self.remove_duplicates()
            .standardize_column_names()
            .strip_and_normalize_text()
            .standardize_categorical_labels()
            .sanitize_unpaid_payment_dates()
            .parse_and_validate_dates()
            .convert_numerical_columns()
            .handle_missing_values(num_strategy, cat_strategy)
            .flag_iqr_outliers_and_suspicious()
        )
        self.after_stats = self._capture_stats(self.df)
        return self.df, pd.DataFrame(self.cleaning_log), self.get_comparison_summary()

    def get_comparison_summary(self):
        """Returns structured before-and-after comparison metrics."""
        after = self.after_stats or self._capture_stats(self.df)
        before = self.before_stats
        
        return pd.DataFrame([
            {"Metric": "Total Invoices (Row Count)", "Before Cleaning": f"{before['row_count']:,}", "After Cleaning": f"{after['row_count']:,}", "Delta": f"{after['row_count'] - before['row_count']:,}"},
            {"Metric": "Total Attributes (Columns)", "Before Cleaning": before['col_count'], "After Cleaning": after['col_count'], "Delta": f"{after['col_count'] - before['col_count']:+d}"},
            {"Metric": "Missing Value Cells", "Before Cleaning": f"{before['missing_count']:,}", "After Cleaning": f"{after['missing_count']:,}", "Delta": f"{after['missing_count'] - before['missing_count']:+d}"},
            {"Metric": "Exact Duplicate Rows", "Before Cleaning": f"{before['duplicate_count']:,}", "After Cleaning": f"{after['duplicate_count']:,}", "Delta": f"{after['duplicate_count'] - before['duplicate_count']:+d}"},
            {"Metric": "IQR Extreme Outliers Flagged", "Before Cleaning": "0", "After Cleaning": f"{after['outliers_flagged']:,}", "Delta": f"+{after['outliers_flagged']:,}"},
            {"Metric": "Suspicious Records Flagged", "Before Cleaning": "0", "After Cleaning": f"{after['suspicious_flagged']:,}", "Delta": f"+{after['suspicious_flagged']:,}"}
        ])

