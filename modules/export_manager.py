"""
InvoiceIQ Export & Deliverables Manager
Generates, packages, and exports deliverables:
- cleaned_invoices.csv
- data_dictionary.csv
- column_mapping.csv
- cleaning_log.csv
- cleaning_script.py
- data_quality_report.csv
- cleaned_invoices.parquet
- Master ZIP package (InvoiceIQ_Deliverables.zip)
"""

import os
import io
import zipfile
import pandas as pd
import streamlit as st

EXPORTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "exports")
SCRIPTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "scripts")
ROOT_DIR = os.path.dirname(os.path.dirname(__file__))

def ensure_export_dirs():
    os.makedirs(EXPORTS_DIR, exist_ok=True)
    os.makedirs(SCRIPTS_DIR, exist_ok=True)

def generate_all_deliverables(cleaned_df, data_dict_df, col_mapping_df, cleaning_log_df, quality_report_df):
    """
    Saves deliverables to disk and compiles them into a ZIP archive.
    """
    ensure_export_dirs()
    manifest = {}

    # 1. cleaned_invoices.csv
    csv_path = os.path.join(EXPORTS_DIR, "cleaned_invoices.csv")
    cleaned_df.to_csv(csv_path, index=False)
    manifest["cleaned_invoices.csv"] = csv_path

    # 2. data_dictionary.csv
    dict_path = os.path.join(EXPORTS_DIR, "data_dictionary.csv")
    data_dict_df.to_csv(dict_path, index=False)
    manifest["data_dictionary.csv"] = dict_path

    # 3. column_mapping.csv
    map_path = os.path.join(EXPORTS_DIR, "column_mapping.csv")
    col_mapping_df.to_csv(map_path, index=False)
    manifest["column_mapping.csv"] = map_path

    # 4. cleaning_log.csv
    log_path = os.path.join(EXPORTS_DIR, "cleaning_log.csv")
    cleaning_log_df.to_csv(log_path, index=False)
    manifest["cleaning_log.csv"] = log_path

    # 5. cleaning_script.py (standalone CLI engine)
    script_src = os.path.join(SCRIPTS_DIR, "clean_dataset.py")
    script_export = os.path.join(EXPORTS_DIR, "cleaning_script.py")
    if os.path.exists(script_src):
        with open(script_src, 'r', encoding='utf-8') as src, open(script_export, 'w', encoding='utf-8') as dst:
            dst.write(src.read())
        manifest["cleaning_script.py"] = script_export

    # 6. data_quality_report.csv
    qual_path = os.path.join(EXPORTS_DIR, "data_quality_report.csv")
    quality_report_df.to_csv(qual_path, index=False)
    manifest["data_quality_report.csv"] = qual_path

    # 7. cleaned_invoices.parquet (high performance binary)
    parquet_path = os.path.join(EXPORTS_DIR, "cleaned_invoices.parquet")
    try:
        cleaned_df.to_parquet(parquet_path, index=False, engine="pyarrow")
        manifest["cleaned_invoices.parquet"] = parquet_path
    except Exception:
        manifest["cleaned_invoices.parquet"] = None

    # 8. Create ZIP bundle
    zip_path = os.path.join(EXPORTS_DIR, "InvoiceIQ_Deliverables.zip")
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for fname, fpath in manifest.items():
            if fpath and os.path.exists(fpath):
                zipf.write(fpath, arcname=fname)
    manifest["InvoiceIQ_Deliverables.zip"] = zip_path

    return manifest

def get_file_bytes(filepath):
    """Safely reads binary file bytes for Streamlit download button."""
    if filepath and os.path.exists(filepath):
        with open(filepath, 'rb') as f:
            return f.read()
    return None
