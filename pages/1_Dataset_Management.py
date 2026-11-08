"""
InvoiceIQ Module 1: Dataset Management
Loads Kaggle dataset, supports CSV/Excel uploads, inspects file metadata and previews.
"""

import os
import streamlit as st
import pandas as pd
from modules.ui_theme import render_header, format_number, COLOR_DARK_SAGE, COLOR_PRIMARY_SAGE, COLOR_SOFT_GREEN
from modules.data_loader import (
    get_available_raw_datasets, count_file_lines, load_dataset_sample,
    init_session_dataset, RAW_DATA_DIR
)

def render_dataset_management():
    init_session_dataset()
    render_header(title="Dataset Management", subtitle="Invoice Payment Data Ingestion, Inspection & File Management")

    st.markdown("### 🗄️ Available Raw Datasets")
    available_files = get_available_raw_datasets()
    
    if not available_files:
        st.error(f"No raw datasets found in {RAW_DATA_DIR}. Please place datasets in data/raw/")
        return

    # Dataset Selection Card
    col_sel1, col_sel2, col_sel3 = st.columns([2, 1, 1])
    with col_sel1:
        current_name = st.session_state.get("dataset_name", available_files[0]["filename"])
        file_options = [f["filename"] for f in available_files]
        default_idx = file_options.index(current_name) if current_name in file_options else 0
        
        selected_filename = st.selectbox(
            "Select Active Dataset",
            file_options,
            index=default_idx
        )
    with col_sel2:
        sample_options = [25000, 50000, 100000, 250000, "Full Dataset"]
        selected_sample = st.selectbox(
            "Working Sample Size",
            sample_options,
            index=1,
            help="Configurable row limit ensures fast interactive processing while retaining full scope accuracy."
        )
    with col_sel3:
        st.write("") # Spacer
        st.write("")
        reload_btn = st.button("🔄 Load Dataset", use_container_width=True)

    selected_file_meta = next(f for f in available_files if f["filename"] == selected_filename)
    
    if reload_btn or st.session_state.get("dataset_name") != selected_filename:
        with st.spinner(f"Loading {selected_filename}..."):
            filepath = selected_file_meta["filepath"]
            total_rows = count_file_lines(filepath)
            
            sample_val = None if selected_sample == "Full Dataset" else int(selected_sample)
            loaded_df = load_dataset_sample(filepath, nrows=sample_val)
            
            st.session_state["dataset_name"] = selected_filename
            st.session_state["dataset_path"] = filepath
            st.session_state["dataset_size_mb"] = selected_file_meta["size_mb"]
            st.session_state["total_dataset_rows"] = total_rows
            st.session_state["dataset_rows"] = f"{total_rows:,}"
            st.session_state["loaded_sample_size"] = len(loaded_df)
            st.session_state["raw_df"] = loaded_df.copy()
            st.session_state["working_df"] = loaded_df.copy()
            st.session_state["cleaning_status"] = "Raw Data Loaded"
            st.success(f"Successfully loaded {len(loaded_df):,} rows from {selected_filename}!")
            st.rerun()

    # Dataset Metadata Display
    raw_df = st.session_state.get("raw_df", pd.DataFrame())
    total_file_rows = st.session_state.get("total_dataset_rows", len(raw_df))
    
    m1, m2, m3, m4, m5 = st.columns(5)
    with m1:
        st.metric("Source File", selected_file_meta["filename"])
    with m2:
        st.metric("File Size", f"{selected_file_meta['size_mb']} MB")
    with m3:
        st.metric("Total Records", f"{total_file_rows:,}")
    with m4:
        st.metric("Loaded Records", f"{len(raw_df):,}")
    with m5:
        st.metric("Total Columns", f"{len(raw_df.columns)}")

    st.markdown("<hr/>", unsafe_allow_html=True)

    # Previews
    tab1, tab2, tab3 = st.tabs(["📄 First 10 Records (Head)", "📑 Last 10 Records (Tail)", "📤 Upload Alternative Dataset"])
    
    with tab1:
        st.markdown("**Head Inspection (First 10 Records):**")
        st.dataframe(raw_df.head(10), use_container_width=True)

    with tab2:
        st.markdown("**Tail Inspection (Last 10 Records):**")
        st.dataframe(raw_df.tail(10), use_container_width=True)

    with tab3:
        st.markdown("#### Upload Custom Dataset (CSV or Excel)")
        st.info("Uploaded files are stored locally in `data/raw/` and will never overwrite existing datasets.")
        
        uploaded_file = st.file_uploader(
            "Choose a CSV or Excel file",
            type=["csv", "xlsx", "xls"],
            help="Upload an invoice ledger or payment transactions file."
        )
        
        if uploaded_file is not None:
            save_path = os.path.join(RAW_DATA_DIR, uploaded_file.name)
            with open(save_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
                
            st.success(f"Saved {uploaded_file.name} to {RAW_DATA_DIR}!")
            
            if uploaded_file.name.endswith(('.xlsx', '.xls')):
                xl = pd.ExcelFile(save_path)
                selected_sheet = st.selectbox("Select Excel Worksheet", xl.sheet_names)
                load_custom = st.button("Load Selected Excel Sheet")
                if load_custom:
                    custom_df = pd.read_excel(save_path, sheet_name=selected_sheet)
                    st.session_state["dataset_name"] = f"{uploaded_file.name} [{selected_sheet}]"
                    st.session_state["dataset_path"] = save_path
                    st.session_state["dataset_size_mb"] = round(os.path.getsize(save_path) / (1024*1024), 2)
                    st.session_state["total_dataset_rows"] = len(custom_df)
                    st.session_state["dataset_rows"] = f"{len(custom_df):,}"
                    st.session_state["raw_df"] = custom_df.copy()
                    st.session_state["working_df"] = custom_df.copy()
                    st.session_state["cleaning_status"] = "Custom Upload Loaded"
                    st.rerun()
            else:
                load_custom_csv = st.button("Load Uploaded CSV")
                if load_custom_csv:
                    custom_df = pd.read_csv(save_path, low_memory=False)
                    st.session_state["dataset_name"] = uploaded_file.name
                    st.session_state["dataset_path"] = save_path
                    st.session_state["dataset_size_mb"] = round(os.path.getsize(save_path) / (1024*1024), 2)
                    st.session_state["total_dataset_rows"] = len(custom_df)
                    st.session_state["dataset_rows"] = f"{len(custom_df):,}"
                    st.session_state["raw_df"] = custom_df.copy()
                    st.session_state["working_df"] = custom_df.copy()
                    st.session_state["cleaning_status"] = "Custom Upload Loaded"
                    st.rerun()

if __name__ == "__main__":
    st.set_page_config(page_title="InvoiceIQ | Dataset Management", layout="wide")
    render_dataset_management()

