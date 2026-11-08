"""
InvoiceIQ Module 2: Data Profiling
Inspects dataset dimensions, data types, column meanings, unique counts, missing ratios, and data dictionary.
"""

import streamlit as st
import pandas as pd
from modules.ui_theme import render_header, format_number, COLOR_DARK_SAGE, COLOR_PRIMARY_SAGE, COLOR_TERRACOTTA
from modules.data_loader import init_session_dataset
from modules.data_profiler import profile_dataset, build_data_dictionary
from modules.column_mapper import suggest_mapping

def render_profiling():
    init_session_dataset()
    render_header(title="Data Profiling", subtitle="Structural Profiling, Column Meanings & Data Dictionary Catalog")

    df = st.session_state.get("working_df")
    if df is None or df.empty:
        st.warning("No active dataset loaded. Please navigate to Dataset Management.")
        return

    # Compute profiling metrics
    profile = profile_dataset(df)
    
    # Overview Cards
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        st.metric("Total Records", format_number(profile['total_rows']))
    with c2:
        st.metric("Total Columns", profile['total_cols'])
    with c3:
        st.metric("Memory Usage", f"{profile['memory_usage_mb']} MB")
    with c4:
        st.metric("Numerical Columns", len(profile['num_cols']))
    with c5:
        st.metric("Categorical / Dates", len(profile['cat_cols']) + len(profile['date_cols']))

    st.markdown("<hr/>", unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs([
        "📖 Data Dictionary & Inferred Meanings",
        "📊 Column Specifications & Null Ratios",
        "📈 Numerical Summary Statistics"
    ])

    mapping = st.session_state.get("column_mapping", suggest_mapping(df.columns.tolist()))
    data_dict = build_data_dictionary(df, mapping)
    st.session_state["data_dictionary_df"] = data_dict

    with tab1:
        st.markdown("#### 📚 Data Dictionary & Column Meanings")
        st.caption("Detailed specification of every column: storage type, unique count, missing ratio, and business meaning.")
        
        csv_bytes = data_dict.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download data_dictionary.csv",
            data=csv_bytes,
            file_name="data_dictionary.csv",
            mime="text/csv",
            key="dl_dict_btn"
        )
        st.dataframe(data_dict, use_container_width=True, height=450)

    with tab2:
        st.markdown("#### 🔬 Column Specifications, Data Types & Missing Percentages")
        schema_records = []
        for col in df.columns:
            null_cnt = int(df[col].isnull().sum())
            null_pct = (null_cnt / len(df)) * 100 if len(df) > 0 else 0.0
            schema_records.append({
                "Column Name": col,
                "Data Type": str(df[col].dtype),
                "Unique Values": int(df[col].nunique(dropna=False)),
                "Non-Null Count": int(df[col].notnull().sum()),
                "Missing Count": null_cnt,
                "Missing %": f"{null_pct:.2f}%"
            })
        st.dataframe(pd.DataFrame(schema_records), use_container_width=True)

    with tab3:
        st.markdown("#### 📈 Numerical Summary Statistics")
        num_cols = profile['num_cols']
        if num_cols:
            stats_df = df[num_cols].describe().T
            stats_df['skewness'] = df[num_cols].skew()
            stats_df = stats_df.round(2)
            st.dataframe(stats_df, use_container_width=True)
        else:
            st.info("No numerical columns detected.")

if __name__ == "__main__":
    st.set_page_config(page_title="InvoiceIQ | Profiling", layout="wide")
    render_profiling()

