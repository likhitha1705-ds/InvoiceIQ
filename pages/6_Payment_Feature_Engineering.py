"""
InvoiceIQ Module 6: Payment Feature Engineering
Derives payment delay, settlement timeline, paid late flag, and open/paid exposure metrics.
Strictly observes financial data integrity without data leakage or invented dates.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from modules.ui_theme import (
    render_header, format_number, COLOR_DARK_SAGE, COLOR_PRIMARY_SAGE,
    COLOR_TERRACOTTA, COLOR_CHAMPAGNE, COLOR_SOFT_GREEN, CHART_PALETTE, get_plotly_layout
)
from modules.data_loader import init_session_dataset
from modules.feature_engineering import engineer_payment_features

def render_feature_engineering():
    init_session_dataset()
    render_header(title="Payment Feature Engineering", subtitle="Derivation of Settlement Delays, Realized Timelines & Payment Status Flags")

    df = st.session_state.get("working_df")
    if df is None or df.empty:
        st.warning("No dataset loaded. Please go to Dataset Management.")
        return

    st.markdown("### 🛠️ Payment Derived Columns Specification")
    st.markdown("""
    The following derived features are computed strictly from available ground-truth dates:
    1. **Days to Pay (`days_to_pay`):** Calendar days between invoice issuance and settlement (`payment_date - invoice_date`). *Computed exclusively for Paid invoices.*
    2. **Payment Delay (`payment_delay`):** Calendar days relative to contractual deadline (`payment_date - due_date`). *Negative = Early, Zero = On-Time, Positive = Late.*
    3. **Paid Late Flag (`paid_late_flag`):** Binary indicator where `1` = Paid after due date, and `0` = Paid on or before due date.
    4. **Open/Paid Flag (`invoice_status`):** Categorical settlement classification (`Paid` vs `Open`).
    """)

    # Calculation Execution Button
    col_btn, col_ref = st.columns([1, 1])
    with col_ref:
        ref_date = st.date_input(
            "Reference Date for Open Invoices",
            value=pd.to_datetime("2023-12-31"),
            help="Used to compute aging (days_past_due) exclusively for open/unsettled invoices."
        )
    with col_btn:
        st.write("")
        st.write("")
        run_feat_btn = st.button("⚡ Calculate Payment Features", use_container_width=True)

    if run_feat_btn or 'payment_delay' not in df.columns:
        with st.spinner("Engineering payment features..."):
            featured_df = engineer_payment_features(df, reference_date=ref_date)
            st.session_state["working_df"] = featured_df
            st.session_state["featured_df"] = featured_df
            df = featured_df
            st.success("Payment features successfully calculated!")

    st.markdown("<hr/>", unsafe_allow_html=True)

    # Summary KPI Cards
    total_inv = len(df)
    paid_mask = df['invoice_status'] == 'Paid' if 'invoice_status' in df.columns else pd.Series(False, index=df.index)
    paid_count = int(paid_mask.sum())
    open_count = total_inv - paid_count
    
    avg_days_to_pay = df.loc[paid_mask, 'days_to_pay'].dropna().mean() if 'days_to_pay' in df.columns else None
    avg_delay = df.loc[paid_mask, 'payment_delay'].dropna().mean() if 'payment_delay' in df.columns else None
    late_count = int(df.loc[paid_mask, 'paid_late_flag'].dropna().sum()) if 'paid_late_flag' in df.columns else 0

    k1, k2, k3, k4, k5 = st.columns(5)
    with k1:
        st.metric("Total Invoices", f"{total_inv:,}")
    with k2:
        st.metric("Paid Invoices", f"{paid_count:,} ({(paid_count/total_inv)*100:.1f}%)" if total_inv > 0 else "0")
    with k3:
        st.metric("Open Invoices", f"{open_count:,} ({(open_count/total_inv)*100:.1f}%)" if total_inv > 0 else "0")
    with k4:
        d_val = f"{avg_days_to_pay:.1f} days" if avg_days_to_pay is not None else "-"
        st.metric("Avg Days to Pay", d_val)
    with k5:
        del_val = f"{avg_delay:.1f} days" if avg_delay is not None else "-"
        color = COLOR_PRIMARY_SAGE if avg_delay and avg_delay <= 0 else COLOR_TERRACOTTA
        st.metric("Avg Payment Delay", del_val)

    st.markdown("<br/>", unsafe_allow_html=True)

    # Visualizations
    v1, v2 = st.columns(2)
    with v1:
        if 'payment_delay' in df.columns:
            delays = df.loc[paid_mask, 'payment_delay'].dropna()
            if not delays.empty:
                fig_delay = px.histogram(
                    delays,
                    nbins=35,
                    color_discrete_sequence=[COLOR_PRIMARY_SAGE]
                )
                fig_delay.add_vline(x=0, line_dash="dash", line_color=COLOR_DARK_SAGE, annotation_text="Due Date (0 Days)")
                fig_delay.update_layout(get_plotly_layout("Realized Payment Delay Distribution (Paid Invoices)"))
                fig_delay.update_layout(xaxis_title="Delay in Days Relative to Due Date (Negative = Early)", yaxis_title="Invoice Count")
                st.plotly_chart(fig_delay, use_container_width=True)
    with v2:
        if 'payment_aging_bucket' in df.columns:
            aging_counts = df['payment_aging_bucket'].value_counts().reset_index()
            aging_counts.columns = ['Cohort', 'Count']
            fig_aging = px.bar(
                aging_counts,
                x='Cohort',
                y='Count',
                color='Cohort',
                color_discrete_sequence=CHART_PALETTE
            )
            fig_aging.update_layout(get_plotly_layout("Settlement & Aging Risk Taxonomy"))
            fig_aging.update_layout(xaxis_tickangle=-30)
            st.plotly_chart(fig_aging, use_container_width=True)

    # Preview Table of Engineered Fields
    st.markdown("### 📋 Engineered Attributes Preview")
    display_cols = [c for c in ['invoice_number', 'customer_name', 'invoice_date', 'due_date', 'payment_date', 'invoice_status', 'days_to_pay', 'payment_delay', 'paid_late_flag', 'days_past_due'] if c in df.columns]
    st.dataframe(df[display_cols].head(15), use_container_width=True)

if __name__ == "__main__":
    st.set_page_config(page_title="InvoiceIQ | Feature Engineering", layout="wide")
    render_feature_engineering()

