"""
InvoiceIQ Payment Analytics & Visualizations Module
Creates Plotly visualizations using the Warm Ivory + Sage Green palette,
computes executive KPIs, and handles multidimensional slice-and-dice filtering.
"""

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from modules.ui_theme import (
    COLOR_PRIMARY_SAGE, COLOR_DARK_SAGE, COLOR_TERRACOTTA, 
    COLOR_CHAMPAGNE, COLOR_SOFT_GREEN, COLOR_WARM_GREY, 
    COLOR_CARD, COLOR_TEXT_MAIN, COLOR_TEXT_MUTED,
    CHART_PALETTE, get_plotly_layout
)

def compute_executive_kpis(df):
    """
    Computes core financial KPIs from working DataFrame.
    """
    if df is None or df.empty:
        return {}
        
    total_invoices = len(df)
    
    # Total Amount
    amount_col = next((c for c in ['total_amount', 'amount', 'subtotal'] if c in df.columns), None)
    total_amount = df[amount_col].sum() if amount_col else None
    
    # Unique Customers
    cust_col = next((c for c in ['customer_name', 'customer_id', 'customer'] if c in df.columns), None)
    unique_customers = df[cust_col].nunique() if cust_col else None
    
    # Status metrics
    status_col = next((c for c in ['invoice_status', 'payment_status'] if c in df.columns), None)
    paid_count = 0
    open_count = 0
    if status_col:
        is_paid = df[status_col].astype(str).str.strip().str.lower() == 'paid'
        paid_count = int(is_paid.sum())
        open_count = total_invoices - paid_count
        
    # Late Paid Invoices
    late_count = None
    if 'paid_late_flag' in df.columns:
        late_count = int(df['paid_late_flag'].dropna().sum())
    elif 'is_overdue' in df.columns:
        late_count = int(df['is_overdue'].sum())
        
    # Payment Timing Averages (for paid invoices)
    avg_days_to_pay = df['days_to_pay'].dropna().mean() if 'days_to_pay' in df.columns else None
    avg_payment_delay = df['payment_delay'].dropna().mean() if 'payment_delay' in df.columns else None
    
    # Data Quality quick-stats
    missing_cells = int(df.isnull().sum().sum())
    duplicate_rows = int(df.duplicated().sum())

    return {
        "total_invoices": total_invoices,
        "total_amount": total_amount,
        "unique_customers": unique_customers,
        "paid_invoices": paid_count,
        "open_invoices": open_count,
        "late_invoices": late_count,
        "avg_days_to_pay": avg_days_to_pay,
        "avg_payment_delay": avg_payment_delay,
        "missing_cells": missing_cells,
        "duplicate_rows": duplicate_rows
    }

def filter_dataframe(df, customers=None, countries=None, currencies=None, statuses=None, date_range=None):
    """
    Applies multidimensional interactive filters.
    """
    if df is None or df.empty:
        return df
        
    filtered = df.copy()
    
    # Filter by Customer
    cust_col = next((c for c in ['customer_name', 'customer_id', 'customer'] if c in filtered.columns), None)
    if cust_col and customers:
        filtered = filtered[filtered[cust_col].isin(customers)]
        
    # Filter by Country
    country_col = next((c for c in ['customer_country', 'country'] if c in filtered.columns), None)
    if country_col and countries:
        filtered = filtered[filtered[country_col].isin(countries)]
        
    # Filter by Currency
    if 'currency' in filtered.columns and currencies:
        filtered = filtered[filtered['currency'].isin(currencies)]
        
    # Filter by Payment Status
    status_col = next((c for c in ['payment_status', 'invoice_status'] if c in filtered.columns), None)
    if status_col and statuses:
        filtered = filtered[filtered[status_col].isin(statuses)]
        
    # Filter by Date Range
    date_col = next((c for c in ['invoice_date', 'due_date'] if c in filtered.columns), None)
    if date_col and date_range and len(date_range) == 2:
        start_date, end_date = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
        parsed_dates = pd.to_datetime(filtered[date_col], errors='coerce')
        filtered = filtered[(parsed_dates >= start_date) & (parsed_dates <= end_date)]
        
    return filtered

# -------------------------------------------------------------
# Chart Generators
# -------------------------------------------------------------

def plot_invoice_status_donut(df):
    """Invoice / Payment Status Distribution Donut Chart."""
    status_col = next((c for c in ['payment_status', 'invoice_status'] if c in df.columns), None)
    if not status_col:
        return None
        
    counts = df[status_col].value_counts().reset_index()
    counts.columns = ['Status', 'Count']
    
    fig = px.pie(
        counts, 
        values='Count', 
        names='Status', 
        hole=0.6,
        color='Status',
        color_discrete_sequence=CHART_PALETTE
    )
    fig.update_layout(get_plotly_layout("Invoice Status Distribution"))
    fig.update_traces(textposition='inside', textinfo='percent+label', marker=dict(line=dict(color='#FFFFFF', width=2)))
    return fig

def plot_invoice_amount_histogram(df):
    """Distribution of Invoice Monetary Amounts."""
    amount_col = next((c for c in ['total_amount', 'amount', 'subtotal'] if c in df.columns), None)
    if not amount_col:
        return None
        
    fig = px.histogram(
        df, 
        x=amount_col, 
        nbins=40,
        marginal="box",
        color_discrete_sequence=[COLOR_PRIMARY_SAGE]
    )
    fig.update_layout(get_plotly_layout("Invoice Amount Distribution"))
    fig.update_layout(xaxis_title="Monetary Value", yaxis_title="Invoice Count")
    return fig

def plot_monthly_trend(df):
    """Monthly Invoice Issuance and Volume Trend."""
    date_col = next((c for c in ['invoice_date', 'due_date'] if c in df.columns), None)
    amount_col = next((c for c in ['total_amount', 'amount'] if c in df.columns), None)
    if not date_col:
        return None
        
    temp_df = df.copy()
    temp_df['dt'] = pd.to_datetime(temp_df[date_col], errors='coerce')
    temp_df = temp_df.dropna(subset=['dt'])
    temp_df['year_month'] = temp_df['dt'].dt.to_period('M').astype(str)
    
    if amount_col:
        monthly = temp_df.groupby('year_month').agg(
            Invoice_Count=('dt', 'count'),
            Total_Volume=(amount_col, 'sum')
        ).reset_index()
    else:
        monthly = temp_df.groupby('year_month').size().reset_index(name='Invoice_Count')
        
    monthly = monthly.sort_values('year_month')
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=monthly['year_month'],
        y=monthly['Invoice_Count'],
        name='Invoice Count',
        marker_color=COLOR_SOFT_GREEN,
        marker_line_color=COLOR_PRIMARY_SAGE,
        marker_line_width=1.5
    ))
    
    fig.update_layout(get_plotly_layout("Monthly Invoice Volume Trend"))
    fig.update_layout(xaxis_title="Billing Month", yaxis_title="Number of Invoices")
    return fig

def plot_customer_ranking(df, top_n=10):
    """Customer-wise Total Invoiced Amount (Top N)."""
    cust_col = next((c for c in ['customer_name', 'customer_id', 'customer'] if c in df.columns), None)
    amount_col = next((c for c in ['total_amount', 'amount', 'subtotal'] if c in df.columns), None)
    if not cust_col or not amount_col:
        return None
        
    top_cust = df.groupby(cust_col)[amount_col].sum().reset_index()
    top_cust = top_cust.sort_values(by=amount_col, ascending=False).head(top_n)
    
    fig = px.bar(
        top_cust,
        x=amount_col,
        y=cust_col,
        orientation='h',
        color=amount_col,
        color_continuous_scale=[[0, COLOR_SOFT_GREEN], [1, COLOR_DARK_SAGE]]
    )
    fig.update_layout(get_plotly_layout(f"Top {top_n} Customers by Total Invoiced Value"))
    fig.update_layout(yaxis=dict(autorange="reversed"), xaxis_title="Total Invoiced Value", yaxis_title="Customer")
    return fig

def plot_payment_delay_distribution(df):
    """Payment Delay (Days) Histogram for Settled Invoices."""
    if 'payment_delay' not in df.columns:
        return None
        
    delays = df['payment_delay'].dropna()
    if delays.empty:
        return None
        
    fig = px.histogram(
        delays,
        nbins=35,
        color_discrete_sequence=[COLOR_TERRACOTTA]
    )
    fig.add_vline(x=0, line_dash="dash", line_color=COLOR_DARK_SAGE, annotation_text="Due Date (0 Days Delay)")
    fig.update_layout(get_plotly_layout("Settlement Delay Distribution (Paid Invoices)"))
    fig.update_layout(xaxis_title="Days Delayed Relative to Due Date (Negative = Early)", yaxis_title="Count")
    return fig

def plot_payment_aging_breakdown(df):
    """Distribution of Aging & Settlement Buckets."""
    if 'payment_aging_bucket' not in df.columns:
        return None
        
    bucket_counts = df['payment_aging_bucket'].value_counts().reset_index()
    bucket_counts.columns = ['Aging Bucket', 'Count']
    
    fig = px.bar(
        bucket_counts,
        x='Aging Bucket',
        y='Count',
        color='Aging Bucket',
        color_discrete_sequence=CHART_PALETTE
    )
    fig.update_layout(get_plotly_layout("Payment Aging & Settlement Risk Taxonomy"))
    fig.update_layout(xaxis_tickangle=-30, yaxis_title="Invoices")
    return fig

def plot_missing_values_bar(df):
    """Missing Values Count by Column."""
    missing = df.isnull().sum()
    missing_cols = missing[missing > 0].reset_index()
    if missing_cols.empty:
        return None
    missing_cols.columns = ['Column', 'Missing Count']
    
    fig = px.bar(
        missing_cols,
        x='Column',
        y='Missing Count',
        color_discrete_sequence=[COLOR_TERRACOTTA]
    )
    fig.update_layout(get_plotly_layout("Missing Values by Column"))
    return fig

