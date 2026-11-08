"""
INVOICEIQ
Invoice Payment Data Cleaning & Intelligence Platform
Main Application Entry Point
"""

import importlib
import streamlit as st
import pandas as pd
from modules.ui_theme import apply_custom_theme, COLOR_DARK_SAGE, COLOR_PRIMARY_SAGE, COLOR_TERRACOTTA, COLOR_WARM_GREY
from modules.data_loader import init_session_dataset

# 1. Page Configuration
st.set_page_config(
    page_title="InvoiceIQ | Invoice Payment Data Cleaning Platform",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Inject Custom Theme (Warm Ivory + Sage Green + Terracotta)
apply_custom_theme()

# 3. Initialize Shared Session State & Load Dataset
init_session_dataset()

# 4. Branded Executive Sidebar
with st.sidebar:
    st.markdown(f"""
    <div style="padding: 0.6rem 0.2rem; text-align: center; border-bottom: 1.5px solid {COLOR_WARM_GREY}; margin-bottom: 1.2rem;">
        <div style="font-family: 'Space Grotesk', sans-serif; font-size: 1.6rem; font-weight: 700; color: {COLOR_DARK_SAGE}; letter-spacing: -0.02em;">
            INVOICE<span style="color: {COLOR_TERRACOTTA};">IQ</span>
        </div>
        <div style="font-size: 0.72rem; color: #85867F; font-weight: 600; letter-spacing: 0.08em; text-transform: uppercase; margin-top: 2px;">
            Payment Data Cleaning & Intelligence
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Clean 8-Module Navigation Menu
    pages = {
        "1. Dataset Management": ("1_Dataset_Management", "render_dataset_management"),
        "2. Data Profiling": ("2_Data_Profiling", "render_profiling"),
        "3. Column Mapping": ("3_Column_Mapping", "render_column_mapping"),
        "4. Data Quality Audit": ("4_Data_Quality_Audit", "render_quality_audit"),
        "5. Data Cleaning": ("5_Data_Cleaning", "render_data_cleaning"),
        "6. Payment Feature Engineering": ("6_Payment_Feature_Engineering", "render_feature_engineering"),
        "7. Cleaning Log": ("7_Cleaning_Log", "render_cleaning_log"),
        "8. Export Deliverables": ("8_Export_Deliverables", "render_export_deliverables")
    }

    selected_page_label = st.radio(
        "Navigation",
        list(pages.keys()),
        index=0,
        label_visibility="collapsed"
    )

    st.markdown(f"""
    <div style="margin-top: 2rem; padding: 0.8rem; background-color: #FFFFFF; border: 1px solid {COLOR_WARM_GREY}; border-radius: 10px;">
        <div style="font-size: 0.7rem; color: #85867F; font-weight: 600; text-transform: uppercase;">Active Scope</div>
        <div style="font-size: 0.82rem; font-weight: 700; color: {COLOR_DARK_SAGE}; margin-top: 2px;">
            {st.session_state.get('dataset_name', 'Loading...')}
        </div>
        <div style="font-size: 0.72rem; color: {COLOR_PRIMARY_SAGE}; font-weight: 600; margin-top: 4px;">
            {st.session_state.get('loaded_sample_size', 0):,} loaded / {st.session_state.get('dataset_rows', '0')} total
        </div>
        <div style="margin-top: 6px; font-size: 0.7rem; color: {COLOR_TERRACOTTA}; font-weight: 700;">
            Status: {st.session_state.get('cleaning_status', 'Initialized')}
        </div>
    </div>
    """, unsafe_allow_html=True)

# 5. Page Routing Controller
module_name, func_name = pages[selected_page_label]
mod = importlib.import_module(f"pages.{module_name}")
render_func = getattr(mod, func_name)
render_func()
