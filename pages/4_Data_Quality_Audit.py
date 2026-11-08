"""
InvoiceIQ Module 4: Data Quality Audit
Detects missing values, duplicates, chronological anomalies, negative amounts, and synthetic placeholders.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from modules.ui_theme import (
    render_header, format_number, COLOR_DARK_SAGE, COLOR_PRIMARY_SAGE,
    COLOR_TERRACOTTA, COLOR_CHAMPAGNE, COLOR_SOFT_GREEN, CHART_PALETTE, get_plotly_layout
)
from modules.data_loader import init_session_dataset
from modules.data_quality import run_quality_audit

def render_quality_audit():
    init_session_dataset()
    render_header(title="Data Quality Audit", subtitle="Automated Defect Detection, Chronological Integrity & Anomaly Scoring")

    df = st.session_state.get("working_df")
    if df is None or df.empty:
        st.warning("No active dataset loaded. Please navigate to Dataset Management.")
        return

    # Run Audit
    report_df, stats = run_quality_audit(df)
    st.session_state["data_quality_report_df"] = report_df

    # Severity Summary Metrics
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        st.metric("Total Quality Issues", stats.get("Total Issues Found", len(report_df)))
    with c2:
        st.metric("Critical Defects", stats.get("Critical", 0))
    with c3:
        st.metric("High Priority Issues", stats.get("High", 0))
    with c4:
        st.metric("Medium Issues", stats.get("Medium", 0))
    with c5:
        st.metric("Low / Statistical Flags", stats.get("Low", 0))

    st.markdown("<hr/>", unsafe_allow_html=True)

    # Visualizations
    col_v1, col_v2 = st.columns(2)
    with col_v1:
        if "Severity" in report_df.columns and not report_df.empty:
            sev_counts = report_df['Severity'].value_counts().reset_index()
            sev_counts.columns = ['Severity', 'Count']
            color_map = {
                "Critical": "#B0413E",
                "High": COLOR_TERRACOTTA,
                "Medium": COLOR_CHAMPAGNE,
                "Low": COLOR_PRIMARY_SAGE
            }
            fig_sev = px.pie(
                sev_counts,
                values='Count',
                names='Severity',
                hole=0.55,
                color='Severity',
                color_discrete_map=color_map
            )
            fig_sev.update_layout(get_plotly_layout("Audit Issues by Severity Level"))
            st.plotly_chart(fig_sev, use_container_width=True)

    with col_v2:
        if "Category" in report_df.columns and not report_df.empty:
            cat_counts = report_df['Category'].value_counts().reset_index()
            cat_counts.columns = ['Category', 'Issues']
            fig_cat = px.bar(
                cat_counts,
                x='Category',
                y='Issues',
                color='Category',
                color_discrete_sequence=CHART_PALETTE
            )
            fig_cat.update_layout(get_plotly_layout("Defects by Category"))
            fig_cat.update_layout(xaxis_tickangle=-25)
            st.plotly_chart(fig_cat, use_container_width=True)

    st.markdown("### 📋 Data Quality Audit Report")
    st.caption("Detailed inventory of identified anomalies, affected rows, severities, and corrective actions.")

    # Filter Controls
    f1, f2, f3 = st.columns([1, 1, 1])
    with f1:
        sev_filter = st.multiselect("Filter Severity", ["All", "Critical", "High", "Medium", "Low"], default=["All"])
    with f2:
        cat_filter = st.multiselect("Filter Category", ["All"] + report_df['Category'].unique().tolist(), default=["All"])
    with f3:
        st.write("")
        csv_bytes = report_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download data_quality_report.csv",
            data=csv_bytes,
            file_name="data_quality_report.csv",
            mime="text/csv",
            key="dl_qual_rep_btn",
            use_container_width=True
        )

    # Filter logic
    filtered_report = report_df.copy()
    if "All" not in sev_filter and sev_filter:
        filtered_report = filtered_report[filtered_report['Severity'].isin(sev_filter)]
    if "All" not in cat_filter and cat_filter:
        filtered_report = filtered_report[filtered_report['Category'].isin(cat_filter)]

    st.dataframe(filtered_report, use_container_width=True, height=400)

    # Key Data Quality Observation
    st.info("""
    💡 **Key Quality Finding:** Unpaid invoices (`Pending`, `Overdue`, `Cancelled`) in the raw dataset contain synthetic placeholder payment dates identical to their due dates. 
    The **Data Cleaning Engine** automatically sanitizes these dates to `NaT` to ensure data validity.
    """)

if __name__ == "__main__":
    st.set_page_config(page_title="InvoiceIQ | Quality Audit", layout="wide")
    render_quality_audit()

