"""
InvoiceIQ Module 3: Column Mapping
Maps dataset columns to required project fields, supports manual overrides, and documents unmapped attributes.
"""

import streamlit as st
import pandas as pd
from modules.ui_theme import render_header, COLOR_DARK_SAGE, COLOR_PRIMARY_SAGE, COLOR_TERRACOTTA, COLOR_SOFT_GREEN
from modules.data_loader import init_session_dataset
from modules.column_mapper import (
    CORE_PROJECT_FIELDS, suggest_mapping, generate_mapping_dataframe
)

def render_column_mapping():
    init_session_dataset()
    render_header(title="Column Mapping", subtitle="Semantic Field Alignment & Project Schema Mapping")

    df = st.session_state.get("working_df")
    if df is None or df.empty:
        st.warning("No active dataset loaded. Please navigate to Dataset Management.")
        return

    columns = df.columns.tolist()
    
    # Initialize mapping in session state if not set
    if "column_mapping" not in st.session_state:
        st.session_state["column_mapping"] = suggest_mapping(columns)
        
    current_mapping = st.session_state["column_mapping"]

    # Mapping status metrics
    mapped_count = sum(1 for f in CORE_PROJECT_FIELDS if current_mapping.get(f) is not None)
    total_core = len(CORE_PROJECT_FIELDS)
    
    col_k1, col_k2, col_k3 = st.columns(3)
    with col_k1:
        st.metric("Required Fields Mapped", f"{mapped_count} / {total_core}")
    with col_k2:
        mapped_actuals = set(v for v in current_mapping.values() if v is not None)
        unmapped_cnt = len(columns) - len(mapped_actuals)
        st.metric("Unmapped Raw Columns", f"{unmapped_cnt} of {len(columns)}")
    with col_k3:
        status_label = "Complete ✅" if mapped_count == total_core else "Partial Mapping ⚠️"
        st.metric("Mapping Status", status_label)

    st.markdown("<hr/>", unsafe_allow_html=True)

    # Manual Dropdown Form
    st.markdown("### 🎯 Configure Column Mappings")
    st.caption("Automatic suggestions are pre-filled based on header matching. Adjust dropdown selections if necessary.")

    with st.form("column_mapping_form"):
        col_left, col_right = st.columns(2)
        
        updated_mapping = {}
        dropdown_options = ["None (Unavailable)"] + columns

        # Split core fields across two columns
        half = (len(CORE_PROJECT_FIELDS) + 1) // 2
        with col_left:
            for field in CORE_PROJECT_FIELDS[:half]:
                curr_val = current_mapping.get(field)
                default_idx = dropdown_options.index(curr_val) if curr_val in dropdown_options else 0
                selected = st.selectbox(
                    f"📌 {field}",
                    dropdown_options,
                    index=default_idx,
                    key=f"map_{field}"
                )
                updated_mapping[field] = None if selected == "None (Unavailable)" else selected

        with col_right:
            for field in CORE_PROJECT_FIELDS[half:]:
                curr_val = current_mapping.get(field)
                default_idx = dropdown_options.index(curr_val) if curr_val in dropdown_options else 0
                selected = st.selectbox(
                    f"📌 {field}",
                    dropdown_options,
                    index=default_idx,
                    key=f"map_{field}"
                )
                updated_mapping[field] = None if selected == "None (Unavailable)" else selected

        submitted = st.form_submit_button("💾 Save & Apply Column Mapping", use_container_width=True)
        if submitted:
            st.session_state["column_mapping"] = updated_mapping
            st.success("Column mapping configuration saved!")
            st.rerun()

    # Generate Mapping Table
    map_df, unmapped_cols = generate_mapping_dataframe(st.session_state["column_mapping"], columns)
    st.session_state["column_mapping_df"] = map_df

    st.markdown("### 📋 Active Schema Mapping Table")
    
    col_dl, col_space = st.columns([1, 2])
    with col_dl:
        csv_bytes = map_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download column_mapping.csv",
            data=csv_bytes,
            file_name="column_mapping.csv",
            mime="text/csv",
            key="dl_col_map_btn"
        )

    st.dataframe(map_df, use_container_width=True)

    if unmapped_cols:
        st.markdown("**ℹ️ Unmapped Dataset Columns:**")
        st.write(", ".join([f"`{c}`" for c in unmapped_cols]))

if __name__ == "__main__":
    st.set_page_config(page_title="InvoiceIQ | Column Mapping", layout="wide")
    render_column_mapping()

