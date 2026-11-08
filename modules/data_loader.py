"""
InvoiceIQ Data Loader Module
Handles Kaggle dataset detection, file previewing, line counting,
manual CSV/Excel uploads, encoding error resilience, and session caching.
"""

import os
import pandas as pd
import streamlit as st

RAW_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "raw")
PROCESSED_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "processed")

def get_available_raw_datasets():
    """List all CSV/Excel files available in data/raw/."""
    os.makedirs(RAW_DATA_DIR, exist_ok=True)
    files = []
    for f in os.listdir(RAW_DATA_DIR):
        if f.endswith(('.csv', '.xlsx', '.xls', '.parquet')):
            path = os.path.join(RAW_DATA_DIR, f)
            size_mb = os.path.getsize(path) / (1024 * 1024)
            files.append({
                "filename": f,
                "filepath": path,
                "size_mb": round(size_mb, 2),
                "extension": os.path.splitext(f)[1].lower()
            })
    return files

def count_file_lines(filepath):
    """Accurately count rows in large CSV without memory overflow."""
    if not os.path.exists(filepath):
        return 0
    try:
        count = 0
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(1024 * 1024 * 8), b''):
                count += chunk.count(b'\n')
        # Subtract header row
        return max(0, count - 1)
    except Exception:
        return 0

@st.cache_data(show_spinner=False)
def load_dataset_sample(filepath, nrows=50000, encoding='utf-8'):
    """
    Load a representative sample or full dataset with encoding fallbacks.
    nrows=None loads the entire dataset.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Dataset not found at {filepath}")
    
    ext = os.path.splitext(filepath)[1].lower()
    
    if ext == '.csv':
        encodings_to_try = [encoding, 'utf-8', 'latin-1', 'cp1252']
        for enc in encodings_to_try:
            try:
                if nrows:
                    df = pd.read_csv(filepath, nrows=nrows, encoding=enc, low_memory=False)
                else:
                    df = pd.read_csv(filepath, encoding=enc, low_memory=False)
                return df
            except UnicodeDecodeError:
                continue
        raise ValueError(f"Unable to decode {filepath} with standard encodings.")
        
    elif ext in ('.xlsx', '.xls'):
        df = pd.read_excel(filepath, nrows=nrows)
        return df
        
    elif ext == '.parquet':
        df = pd.read_parquet(filepath)
        if nrows and len(df) > nrows:
            return df.head(nrows)
        return df
    else:
        raise ValueError(f"Unsupported file format: {ext}")

def load_file_preview(filepath, n=10):
    """Load first n and last n records safely."""
    ext = os.path.splitext(filepath)[1].lower()
    if ext == '.csv':
        try:
            head_df = pd.read_csv(filepath, nrows=n, low_memory=False)
            # For tail, read a small chunk from the end or sample
            return head_df
        except Exception as e:
            return pd.DataFrame({"Error": [str(e)]})
    return pd.DataFrame()

def init_session_dataset():
    """Ensure dataset state is initialized in Streamlit session state."""
    if "raw_df" not in st.session_state:
        available = get_available_raw_datasets()
        if available:
            # Default to train_invoices.csv if present
            default_file = next((f for f in available if "train" in f["filename"].lower()), available[0])
            filepath = default_file["filepath"]
            total_rows = count_file_lines(filepath)
            
            # Load default 50,000 rows for high-performance interactive exploration
            sample_size = 50000
            df = load_dataset_sample(filepath, nrows=sample_size)
            
            st.session_state["dataset_name"] = default_file["filename"]
            st.session_state["dataset_path"] = filepath
            st.session_state["dataset_size_mb"] = default_file["size_mb"]
            st.session_state["total_dataset_rows"] = total_rows
            st.session_state["dataset_rows"] = f"{total_rows:,}"
            st.session_state["loaded_sample_size"] = len(df)
            st.session_state["raw_df"] = df.copy()
            st.session_state["working_df"] = df.copy()
            st.session_state["cleaning_status"] = "Raw Data Loaded"
        else:
            st.session_state["dataset_name"] = "No dataset found"
            st.session_state["dataset_path"] = None
            st.session_state["dataset_rows"] = "0"
            st.session_state["total_dataset_rows"] = 0
            st.session_state["raw_df"] = pd.DataFrame()
            st.session_state["working_df"] = pd.DataFrame()
            st.session_state["cleaning_status"] = "No Dataset"

