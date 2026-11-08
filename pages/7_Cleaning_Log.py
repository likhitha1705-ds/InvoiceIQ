"""
InvoiceIQ Module 7: Cleaning Log
Full audit trail of all data hygiene transformations, reason codes, affected counts, and CSV export.
"""

import streamlit as st
import pandas as pd
from modules.ui_theme import render_header, COLOR_DARK_SAGE, COLOR_PRIMARY_SAGE, COLOR_TERRACOTTA
from modules.data_loader import init_session_dataset

def render_cleaning_log():
    init_session_dataset()
    render_header(title="Cleaning Log", subtitle="Comprehensive Transformation Register, Audit Reasons & Affected Row Counts")

    cleaning_log_df = st.session_state.get("cleaning_log_df")
    
    if cleaning_log_df is None or cleaning_log_df.empty:
        st.info("No cleaning operations have been recorded yet. Navigate to 'Data Cleaning' to run the preprocessing pipeline.")
        return

    # Metrics
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Total Cleaning Actions", len(cleaning_log_df))
    with c2:
        tot_affected = cleaning_log_df['Rows Affected'].sum() if 'Rows Affected' in cleaning_log_df.columns else 0
        st.metric("Total Rows Processed", f"{tot_affected:,}")
    with c3:
        success_cnt = (cleaning_log_df['Status'] == 'Success').sum() if 'Status' in cleaning_log_df.columns else len(cleaning_log_df)
        st.metric("Successful Actions", success_cnt)
    with c4:
        st.write("")
        csv_bytes = cleaning_log_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download cleaning_log.csv",
            data=csv_bytes,
            file_name="cleaning_log.csv",
            mime="text/csv",
            key="dl_clean_log_btn",
            use_container_width=True
        )

    st.markdown("<hr/>", unsafe_allow_html=True)
    st.markdown("### 📋 Audit Transformation Log")
    
    # Filter by Column or Status
    col_filters, stat_filters = st.columns(2)
    with col_filters:
        cols_present = ["All"] + sorted(cleaning_log_df['Column Name'].unique().tolist())
        sel_c = st.selectbox("Filter by Column", cols_present)
    with stat_filters:
        stats_present = ["All"] + sorted(cleaning_log_df['Status'].unique().tolist())
        sel_s = st.selectbox("Filter by Status", stats_present)

    filtered_log = cleaning_log_df.copy()
    if sel_c != "All":
        filtered_log = filtered_log[filtered_log['Column Name'] == sel_c]
    if sel_s != "All":
        filtered_log = filtered_log[filtered_log['Status'] == sel_s]

    st.dataframe(filtered_log, use_container_width=True, height=450)

if __name__ == "__main__":
    st.set_page_config(page_title="InvoiceIQ | Cleaning Log", layout="wide")
    render_cleaning_log()

