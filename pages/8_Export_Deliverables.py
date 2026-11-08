"""
InvoiceIQ Module 8: Export Deliverables
Consolidated export station for deliverables: cleaned datasets, data dictionary,
column mapping, cleaning log, quality report, and reproducible cleaning script.
"""

import os
import streamlit as st
import pandas as pd
from modules.ui_theme import render_header, COLOR_DARK_SAGE, COLOR_PRIMARY_SAGE, COLOR_TERRACOTTA, COLOR_SOFT_GREEN
from modules.data_loader import init_session_dataset
from modules.export_manager import (
    generate_all_deliverables, get_file_bytes, EXPORTS_DIR
)
from modules.column_mapper import suggest_mapping, generate_mapping_dataframe
from modules.data_profiler import build_data_dictionary
from modules.data_quality import run_quality_audit

def render_export_deliverables():
    init_session_dataset()
    render_header(title="Export Deliverables", subtitle="Export Station for Cleaned Datasets, Schema Catalogs & Reusable Scripts")

    working_df = st.session_state.get("working_df")
    if working_df is None or working_df.empty:
        st.warning("No dataset loaded. Please go to Dataset Management.")
        return

    # Check or auto-build supporting DataFrames if not already in session state
    if "column_mapping_df" not in st.session_state:
        mapping = suggest_mapping(working_df.columns.tolist())
        map_df, _ = generate_mapping_dataframe(mapping, working_df.columns.tolist())
        st.session_state["column_mapping_df"] = map_df
        
    if "data_dictionary_df" not in st.session_state:
        mapping = st.session_state.get("column_mapping", suggest_mapping(working_df.columns.tolist()))
        st.session_state["data_dictionary_df"] = build_data_dictionary(working_df, mapping)
        
    if "data_quality_report_df" not in st.session_state:
        q_df, _ = run_quality_audit(working_df)
        st.session_state["data_quality_report_df"] = q_df
        
    if "cleaning_log_df" not in st.session_state:
        st.session_state["cleaning_log_df"] = pd.DataFrame([
            {"Issue": "Initialization", "Column Name": "Dataset", "Action Taken": "Loaded baseline dataset", "Reason": "Session startup", "Rows Affected": len(working_df), "Timestamp": "Initial", "Status": "Success"}
        ])

    st.markdown("### 📦 Generate & Bundle Deliverables")
    st.caption("Click below to compile all output files to disk and generate the unified ZIP package.")

    gen_col, zip_col = st.columns([1, 1])
    with gen_col:
        gen_btn = st.button("⚡ Generate Deliverables on Disk", use_container_width=True)

    manifest = generate_all_deliverables(
        cleaned_df=working_df,
        data_dict_df=st.session_state["data_dictionary_df"],
        col_mapping_df=st.session_state["column_mapping_df"],
        cleaning_log_df=st.session_state["cleaning_log_df"],
        quality_report_df=st.session_state["data_quality_report_df"]
    )

    with zip_col:
        zip_bytes = get_file_bytes(manifest.get("InvoiceIQ_Deliverables.zip"))
        if zip_bytes:
            st.download_button(
                label="🎁 Download Complete ZIP Archive (All Deliverables)",
                data=zip_bytes,
                file_name="InvoiceIQ_Deliverables.zip",
                mime="application/zip",
                key="dl_master_zip",
                use_container_width=True
            )

    if gen_btn:
        st.success("All deliverables successfully compiled and packaged into data/exports/!")

    st.markdown("<hr/>", unsafe_allow_html=True)
    st.markdown("### 📄 Individual File Downloads")

    deliverables_info = [
        ("1. cleaned_invoices.csv", "Cleaned invoice dataset with engineered payment features", manifest.get("cleaned_invoices.csv"), "text/csv"),
        ("2. data_dictionary.csv", "Data dictionary detailing data types, null ratios, and column definitions", manifest.get("data_dictionary.csv"), "text/csv"),
        ("3. column_mapping.csv", "Schema mapping between raw column headers and project fields", manifest.get("column_mapping.csv"), "text/csv"),
        ("4. cleaning_log.csv", "Chronological audit trail of all transformations, reasons, and affected rows", manifest.get("cleaning_log.csv"), "text/csv"),
        ("5. cleaning_script.py", "Standalone, reproducible Python CLI script for independent execution", manifest.get("cleaning_script.py"), "text/x-python"),
        ("6. data_quality_report.csv", "Supporting audit report detailing anomalies, severities, and corrective actions", manifest.get("data_quality_report.csv"), "text/csv"),
        ("7. cleaned_invoices.parquet", "Supporting columnar format for compressed high-speed analytics", manifest.get("cleaned_invoices.parquet"), "application/octet-stream")
    ]

    for i in range(0, len(deliverables_info), 2):
        col_a, col_b = st.columns(2)
        
        name_a, desc_a, path_a, mime_a = deliverables_info[i]
        with col_a:
            st.markdown(f"**{name_a}**")
            st.caption(desc_a)
            file_bytes_a = get_file_bytes(path_a)
            if file_bytes_a:
                st.download_button(
                    label=f"📥 Download {name_a.split('. ')[1]}",
                    data=file_bytes_a,
                    file_name=name_a.split('. ')[1],
                    mime=mime_a,
                    key=f"dl_deliv_{i}"
                )
            else:
                st.info("File ready to generate")
                
        if i + 1 < len(deliverables_info):
            name_b, desc_b, path_b, mime_b = deliverables_info[i+1]
            with col_b:
                st.markdown(f"**{name_b}**")
                st.caption(desc_b)
                file_bytes_b = get_file_bytes(path_b)
                if file_bytes_b:
                    st.download_button(
                        label=f"📥 Download {name_b.split('. ')[1]}",
                        data=file_bytes_b,
                        file_name=name_b.split('. ')[1],
                        mime=mime_b,
                        key=f"dl_deliv_{i+1}"
                    )
                else:
                    st.info("File ready to generate")

        st.markdown("<br/>", unsafe_allow_html=True)

if __name__ == "__main__":
    st.set_page_config(page_title="InvoiceIQ | Exports", layout="wide")
    render_export_deliverables()

