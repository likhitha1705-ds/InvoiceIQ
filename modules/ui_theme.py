"""
InvoiceIQ UI Theme & Styling Module
Design System: Warm Ivory + Sage Green + Muted Terracotta + Champagne Gold
Enterprise-grade Financial Data Cleaning & Intelligence Platform Theme
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Color Palette Constants
COLOR_BG = "#F7F6F0"            # Main warm ivory background
COLOR_CARD = "#FFFFFF"          # Crisp white card background
COLOR_PRIMARY_SAGE = "#829783"  # Primary sage green
COLOR_DARK_SAGE = "#465B4B"     # Dark sage for headers / high contrast
COLOR_SOFT_GREEN = "#E3EADF"    # Light pastel sage accent
COLOR_TERRACOTTA = "#C58C76"    # Muted terracotta for warnings / flags
COLOR_CHAMPAGNE = "#D8C59B"     # Champagne gold for highlights
COLOR_WARM_GREY = "#E9E7DF"     # Warm grey for borders
COLOR_TEXT_MAIN = "#41443F"     # Deep slate/charcoal text
COLOR_TEXT_MUTED = "#85867F"    # Secondary text

# Plotly Color Sequence
CHART_PALETTE = [
    "#829783",  # Primary Sage
    "#D8C59B",  # Champagne Gold
    "#C58C76",  # Muted Terracotta
    "#465B4B",  # Dark Sage
    "#A3B899",  # Minty Sage
    "#B89B72",  # Muted Amber
    "#8E9E82",  # Olive Sage
    "#D1A390",  # Rose Terracotta
]

def apply_custom_theme():
    """Inject custom CSS to establish the Warm Ivory + Sage Green enterprise theme."""
    custom_css = f"""
    <style>
    /* Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');

    html, body, [class*="css"] {{
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
        color: {COLOR_TEXT_MAIN};
    }}

    /* Main App Background */
    .stApp {{
        background-color: {COLOR_BG};
    }}

    /* Sidebar Background and Borders */
    section[data-testid="stSidebar"] {{
        background-color: #F1F0E8 !important;
        border-right: 1px solid {COLOR_WARM_GREY};
    }}

    section[data-testid="stSidebar"] .stMarkdown, 
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] span {{
        color: {COLOR_TEXT_MAIN} !important;
    }}

    /* Headers */
    h1, h2, h3, h4, h5, h6 {{
        font-family: 'Space Grotesk', sans-serif !important;
        color: {COLOR_DARK_SAGE} !important;
        font-weight: 600 !important;
        letter-spacing: -0.02em;
    }}

    /* Primary and Secondary Buttons */
    .stButton > button {{
        background-color: {COLOR_PRIMARY_SAGE} !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 0.5rem 1.25rem !important;
        font-weight: 500 !important;
        font-size: 0.9rem !important;
        transition: all 0.2s ease-in-out !important;
        box-shadow: 0 2px 6px rgba(70, 91, 75, 0.12) !important;
    }}

    .stButton > button:hover {{
        background-color: {COLOR_DARK_SAGE} !important;
        color: #FFFFFF !important;
        box-shadow: 0 4px 12px rgba(70, 91, 75, 0.2) !important;
        transform: translateY(-1px);
    }}

    /* Download Buttons */
    .stDownloadButton > button {{
        background-color: #FFFFFF !important;
        color: {COLOR_DARK_SAGE} !important;
        border: 1.5px solid {COLOR_PRIMARY_SAGE} !important;
        border-radius: 8px !important;
        padding: 0.5rem 1.25rem !important;
        font-weight: 600 !important;
        font-size: 0.9rem !important;
        transition: all 0.2s ease-in-out !important;
    }}

    .stDownloadButton > button:hover {{
        background-color: {COLOR_SOFT_GREEN} !important;
        border-color: {COLOR_DARK_SAGE} !important;
        color: {COLOR_DARK_SAGE} !important;
    }}

    /* Metric Cards */
    div[data-testid="stMetricValue"] {{
        font-family: 'Space Grotesk', sans-serif !important;
        font-size: 1.85rem !important;
        font-weight: 700 !important;
        color: {COLOR_DARK_SAGE} !important;
    }}

    div[data-testid="stMetricLabel"] {{
        font-size: 0.85rem !important;
        font-weight: 500 !important;
        color: {COLOR_TEXT_MUTED} !important;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }}

    /* Card Containers */
    .metric-card {{
        background-color: {COLOR_CARD};
        border: 1px solid {COLOR_WARM_GREY};
        border-radius: 12px;
        padding: 1.2rem 1.4rem;
        box-shadow: 0 4px 14px rgba(70, 91, 75, 0.04);
        margin-bottom: 1rem;
        transition: transform 0.15s ease, box-shadow 0.15s ease;
    }}

    .metric-card:hover {{
        transform: translateY(-2px);
        box-shadow: 0 6px 18px rgba(70, 91, 75, 0.08);
    }}

    /* Dataframe Tables */
    div[data-testid="stDataFrame"] {{
        background-color: {COLOR_CARD};
        border-radius: 10px;
        border: 1px solid {COLOR_WARM_GREY};
        overflow: hidden;
    }}

    /* Tabs Styling */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 8px;
        background-color: transparent;
        border-bottom: 2px solid {COLOR_WARM_GREY};
    }}

    .stTabs [data-baseweb="tab"] {{
        background-color: transparent !important;
        border-radius: 6px 6px 0 0 !important;
        color: {COLOR_TEXT_MUTED} !important;
        font-weight: 500 !important;
        padding: 0.5rem 1.2rem !important;
        border: none !important;
    }}

    .stTabs [aria-selected="true"] {{
        color: {COLOR_DARK_SAGE} !important;
        font-weight: 700 !important;
        border-bottom: 3px solid {COLOR_PRIMARY_SAGE} !important;
    }}

    /* Clean Dividers */
    hr {{
        border: none;
        border-top: 1px solid {COLOR_WARM_GREY};
        margin: 1.5rem 0;
    }}
    </style>
    """
    st.markdown(custom_css, unsafe_allow_html=True)

def render_header(title="Dataset Management", subtitle="Invoice Payment Data Cleaning & Intelligence Platform"):
    """Render consistent product header across all pages."""
    apply_custom_theme()
    
    current_dataset = st.session_state.get("dataset_name", "train_invoices.csv")
    row_count = st.session_state.get("dataset_rows", "2,500,000")
    status = st.session_state.get("cleaning_status", "Raw Data Loaded")
    
    header_html = f"""
    <div style="background: linear-gradient(135deg, #FFFFFF 0%, #F9F8F3 100%); 
                border: 1px solid {COLOR_WARM_GREY}; 
                border-radius: 14px; 
                padding: 1.4rem 1.8rem; 
                margin-bottom: 1.5rem;
                box-shadow: 0 4px 16px rgba(70,91,75,0.04);">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 1rem;">
            <div>
                <div style="display: flex; align-items: center; gap: 0.6rem; margin-bottom: 0.25rem;">
                    <span style="font-family: 'Space Grotesk', sans-serif; font-size: 1.5rem; font-weight: 700; color: {COLOR_DARK_SAGE};">
                        INVOICE<span style="color: {COLOR_TERRACOTTA};">IQ</span>
                    </span>
                    <span style="background-color: {COLOR_SOFT_GREEN}; color: {COLOR_DARK_SAGE}; font-size: 0.72rem; font-weight: 700; padding: 0.2rem 0.55rem; border-radius: 6px; letter-spacing: 0.05em;">
                        FINANCIAL INTELLIGENCE
                    </span>
                </div>
                <h2 style="font-size: 1.35rem; margin: 0 0 0.2rem 0; color: {COLOR_DARK_SAGE};">{title}</h2>
                <p style="font-size: 0.85rem; color: {COLOR_TEXT_MUTED}; margin: 0;">{subtitle}</p>
            </div>
            <div style="display: flex; gap: 0.8rem; align-items: center; flex-wrap: wrap;">
                <div style="background-color: #FFFFFF; border: 1px solid {COLOR_WARM_GREY}; border-radius: 8px; padding: 0.45rem 0.85rem; text-align: right;">
                    <div style="font-size: 0.68rem; color: {COLOR_TEXT_MUTED}; font-weight: 600; text-transform: uppercase;">Active Dataset</div>
                    <div style="font-size: 0.82rem; font-weight: 700; color: {COLOR_DARK_SAGE};">{current_dataset}</div>
                </div>
                <div style="background-color: #FFFFFF; border: 1px solid {COLOR_WARM_GREY}; border-radius: 8px; padding: 0.45rem 0.85rem; text-align: right;">
                    <div style="font-size: 0.68rem; color: {COLOR_TEXT_MUTED}; font-weight: 600; text-transform: uppercase;">Scope</div>
                    <div style="font-size: 0.82rem; font-weight: 700; color: {COLOR_PRIMARY_SAGE};">{row_count} rows</div>
                </div>
                <div style="background-color: #FFFFFF; border: 1px solid {COLOR_WARM_GREY}; border-radius: 8px; padding: 0.45rem 0.85rem; text-align: right;">
                    <div style="font-size: 0.68rem; color: {COLOR_TEXT_MUTED}; font-weight: 600; text-transform: uppercase;">Status</div>
                    <div style="font-size: 0.82rem; font-weight: 700; color: {COLOR_TERRACOTTA};">{status}</div>
                </div>
            </div>
        </div>
    </div>
    """
    st.markdown(header_html, unsafe_allow_html=True)

def format_currency(val, currency="USD"):
    """Format numeric values as currency."""
    if val is None or pd.isna(val):
        return "-"
    if abs(val) >= 1_000_000:
        return f"{currency} {val/1_000_000:.2f}M"
    elif abs(val) >= 1_000:
        return f"{currency} {val/1_000:.1f}K"
    else:
        return f"{currency} {val:,.2f}"

def format_number(val):
    """Format large numbers with readable commas."""
    if val is None or pd.isna(val):
        return "-"
    return f"{int(val):,}"

def get_plotly_layout(title=""):
    """Standardized Plotly chart layout matching Warm Ivory theme."""
    return dict(
        title=dict(
            text=f"<b>{title}</b>",
            font=dict(family="Space Grotesk, sans-serif", size=14, color=COLOR_DARK_SAGE),
            x=0.02,
            y=0.96
        ),
        paper_bgcolor=COLOR_CARD,
        plot_bgcolor=COLOR_CARD,
        font=dict(family="Plus Jakarta Sans, sans-serif", size=11, color=COLOR_TEXT_MAIN),
        margin=dict(l=40, r=30, t=50, b=40),
        xaxis=dict(
            showgrid=True,
            gridcolor=COLOR_WARM_GREY,
            zeroline=False,
            showline=True,
            linecolor=COLOR_WARM_GREY,
            tickfont=dict(size=10, color=COLOR_TEXT_MUTED)
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor=COLOR_WARM_GREY,
            zeroline=False,
            showline=True,
            linecolor=COLOR_WARM_GREY,
            tickfont=dict(size=10, color=COLOR_TEXT_MUTED)
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(size=10, color=COLOR_TEXT_MUTED)
        )
    )
