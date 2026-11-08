"""
InvoiceIQ Module 5: Data Cleaning
Executes data cleaning rules: deduplication, text normalization, category standardization,
unpaid date sanitization, numerical conversion, missing values, and IQR outlier detection.
"""

import streamlit as st
import pandas as pd
from modules.ui_theme import render_header, COLOR_DARK_SAGE, COLOR_PRIMARY_SAGE, COLOR_TERRACOTTA, COLOR_SOFT_GREEN
from modules.data_loader import init_session_dataset
from modules.data_cleaner import DataCleaner

def render_data_cleaning():
    init_session_dataset()
    render_header(title="Data Cleaning", subtitle="Automated Data Hygiene, Categorical Harmonization & Outlier Detection")

    raw_df = st.session_state.get("raw_df")
    if raw_df is None or raw_df.empty:
        st.warning("No dataset loaded. Please go to Dataset Management.")
        return

    st.markdown("### ⚙️ Cleaning Operations & Configuration")
    st.caption("Select the cleaning transformations to execute. All operations are documented with reasons and affected row counts.")

    col_conf1, col_conf2 = st.columns(2)
    with col_conf1:
        st.markdown("**Structural & Text Operations:**")
        chk_dedup = st.checkbox("Remove Exact Duplicate Rows", value=True)
        chk_names = st.checkbox("Standardize Column Names (lowercase snake_case)", value=True)
        chk_trim = st.checkbox("Strip Leading/Trailing Whitespace from Text", value=True)
        chk_cat = st.checkbox("Standardize Categorical Labels (Payment Status & Currencies)", value=True)
        chk_unpaid = st.checkbox("Sanitize Unpaid Dates (Set placeholder payment_date to NaT)", value=True,
                                help="Financial rule: Unsettled accounts must not have payment dates to avoid artificial zero delay.")

    with col_conf2:
        st.markdown("**Numerical & Missing Value Strategy:**")
        chk_num = st.checkbox("Convert Numerical Fields to Numeric Data Types", value=True)
        chk_iqr = st.checkbox("Detect & Flag Extreme Outliers (IQR Method)", value=True,
                              help="Flags records with is_amount_outlier=1 without deleting valid enterprise transactions.")
        chk_susp = st.checkbox("Flag Suspicious Chronological / Polarity Inconsistencies", value=True)

        num_strategy = st.selectbox(
            "Numerical Missing Values",
            ["preserve", "mean", "median"],
            format_func=lambda x: "Preserve Existing Values (Recommended)" if x == "preserve" else f"Impute with Column {x.capitalize()}"
        )
        cat_strategy = st.selectbox(
            "Categorical Missing Values",
            ["preserve", "mode"],
            format_func=lambda x: "Preserve Existing Values (Recommended)" if x == "preserve" else "Impute with Most Frequent (Mode)"
        )

    st.markdown("<br/>", unsafe_allow_html=True)
    run_btn = st.button("🚀 Run Data Cleaning Engine", use_container_width=True)

    if run_btn:
        with st.spinner("Processing dataset through cleaning engine..."):
            cleaner = DataCleaner(raw_df)
            
            if chk_dedup:
                cleaner.remove_duplicates()
            if chk_names:
                cleaner.standardize_column_names()
            if chk_trim:
                cleaner.strip_and_normalize_text()
            if chk_cat:
                cleaner.standardize_categorical_labels()
            if chk_unpaid:
                cleaner.sanitize_unpaid_payment_dates()
            
            cleaner.parse_and_validate_dates()
            
            if chk_num:
                cleaner.convert_numerical_columns()
                
            cleaner.handle_missing_values(num_strategy=num_strategy, cat_strategy=cat_strategy)
            
            if chk_iqr or chk_susp:
                cleaner.flag_iqr_outliers_and_suspicious()

            cleaned_df = cleaner.df
            
            st.session_state["working_df"] = cleaned_df
            st.session_state["cleaned_df"] = cleaned_df
            st.session_state["cleaning_log_df"] = pd.DataFrame(cleaner.cleaning_log)
            st.session_state["comparison_df"] = cleaner.get_comparison_summary()
            st.session_state["cleaning_status"] = "Cleaned"
            
            st.success("✅ Data cleaning executed successfully! Proceed to Payment Feature Engineering to calculate derived metrics.")

    # Display Before-and-After Metrics
    if "comparison_df" in st.session_state:
        st.markdown("<hr/>", unsafe_allow_html=True)
        st.markdown("### 📊 Before vs. After Cleaning Comparison")
        st.dataframe(st.session_state["comparison_df"], use_container_width=True)

        st.markdown("### 🔍 Cleaned Dataset Preview")
        df_show = st.session_state["working_df"]
        st.dataframe(df_show.head(10), use_container_width=True)

if __name__ == "__main__":
    st.set_page_config(page_title="InvoiceIQ | Data Cleaning", layout="wide")
    render_data_cleaning()

