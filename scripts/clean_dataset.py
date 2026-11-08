"""
InvoiceIQ Reusable Data Cleaning & Feature Engineering CLI Script
Independent of Streamlit — executes end-to-end preprocessing from the command line.

Usage:
    python scripts/clean_dataset.py --input data/raw/train_invoices.csv --output data/processed/cleaned_invoices.csv --sample 100000
    python scripts/clean_dataset.py (uses defaults)
"""

import os
import sys
import argparse
import pandas as pd
from datetime import datetime

# Add project root to path for module imports
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from modules.data_cleaner import DataCleaner
from modules.feature_engineering import engineer_payment_features
from modules.data_quality import run_quality_audit
from modules.column_mapper import suggest_mapping, generate_mapping_dataframe
from modules.data_profiler import build_data_dictionary

def run_pipeline(input_path, output_path, sample_size=None, num_strategy="preserve", cat_strategy="preserve"):
    print("=" * 65)
    print("INVOICEIQ — INVOICE PAYMENT DATA CLEANING & PREPROCESSING ENGINE")
    print("=" * 65)
    print(f"Timestamp:   {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Input File:  {input_path}")
    print(f"Output File: {output_path}")
    print(f"Sample Rows: {'Full Dataset' if sample_size is None else f'{sample_size:,}'}")
    print("-" * 65)

    if not os.path.exists(input_path):
        print(f"ERROR: Target dataset does not exist at {input_path}")
        sys.exit(1)

    # 1. Load Data
    print("[1/6] Loading source dataset...")
    if sample_size:
        df = pd.read_csv(input_path, nrows=sample_size, low_memory=False)
    else:
        df = pd.read_csv(input_path, low_memory=False)
    print(f"      Loaded {len(df):,} records with {len(df.columns)} columns.")

    # 2. Quality Audit Prior to Cleaning
    print("[2/6] Executing pre-cleaning data quality audit...")
    audit_report, audit_stats = run_quality_audit(df)
    print(f"      Identified {len(audit_report)} distinct quality observations:")
    for k, v in audit_stats.items():
        print(f"      - {k}: {v}")

    # 3. Clean Data
    print("[3/6] Applying cleaning rules (dedup, formatting, sanitization, IQR)...")
    cleaner = DataCleaner(df)
    cleaned_df, cleaning_log, comp_df = cleaner.execute_all(num_strategy=num_strategy, cat_strategy=cat_strategy)
    print(f"      Executed {len(cleaning_log)} cleaning actions.")

    # 4. Feature Engineering
    print("[4/6] Engineering payment delay & cash-flow indicators...")
    featured_df = engineer_payment_features(cleaned_df)
    print("      Engineered fields:")
    print("      - days_to_pay (Paid invoices only)")
    print("      - payment_delay (Relative to due date)")
    print("      - paid_late_flag (Binary: 1=Late, 0=On-Time/Early)")
    print("      - invoice_status (Paid vs Open)")
    print("      - days_past_due (Open invoices aging from reference date)")
    print("      - payment_aging_bucket (Risk taxonomy)")

    # 5. Export Processed Data & Parquet
    print("[5/6] Exporting cleaned deliverables...")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    featured_df.to_csv(output_path, index=False)
    print(f"      Saved: {output_path} ({len(featured_df):,} rows)")

    parquet_path = output_path.replace(".csv", ".parquet")
    try:
        featured_df.to_parquet(parquet_path, index=False, engine="pyarrow")
        print(f"      Saved: {parquet_path}")
    except Exception as e:
        print(f"      Warning: Could not save Parquet: {e}")

    # 6. Export Supporting Tables
    exports_dir = os.path.join(ROOT_DIR, "data", "exports")
    os.makedirs(exports_dir, exist_ok=True)
    
    mapping = suggest_mapping(df.columns.tolist())
    map_df, _ = generate_mapping_dataframe(mapping, df.columns.tolist())
    map_df.to_csv(os.path.join(exports_dir, "column_mapping.csv"), index=False)

    data_dict = build_data_dictionary(featured_df, mapping)
    data_dict.to_csv(os.path.join(exports_dir, "data_dictionary.csv"), index=False)

    cleaning_log.to_csv(os.path.join(exports_dir, "cleaning_log.csv"), index=False)
    audit_report.to_csv(os.path.join(exports_dir, "data_quality_report.csv"), index=False)
    print(f"      Exported column_mapping, data_dictionary, cleaning_log, and data_quality_report.")

    print("-" * 65)
    print("CLEANING & PREPROCESSING COMPLETED SUCCESSFULLY")
    print("=" * 65)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="InvoiceIQ Preprocessing Pipeline CLI")
    parser.add_argument("--input", default="data/raw/train_invoices.csv", help="Path to input CSV dataset")
    parser.add_argument("--output", default="data/processed/cleaned_invoices.csv", help="Path to output CSV destination")
    parser.add_argument("--sample", type=int, default=50000, help="Row sample limit (omit or 0 for full file)")
    parser.add_argument("--num_strategy", default="preserve", choices=["preserve", "mean", "median"], help="Numerical missing strategy")
    parser.add_argument("--cat_strategy", default="preserve", choices=["preserve", "mode"], help="Categorical missing strategy")
    
    args = parser.parse_args()
    sample_val = None if args.sample == 0 else args.sample
    
    run_pipeline(
        input_path=args.input,
        output_path=args.output,
        sample_size=sample_val,
        num_strategy=args.num_strategy,
        cat_strategy=args.cat_strategy
    )

