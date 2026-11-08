# INVOICEIQ — INVOICE PAYMENT DATA CLEANING & INTELLIGENCE PLATFORM
### Financial Data Cleaning, Quality Auditing & Preprocessing Engine

---

## 1. Project Overview
**InvoiceIQ** is an independent, enterprise-grade financial data processing software platform designed to ingest, profile, audit, clean, and engineer payment features from commercial B2B invoice ledgers.

The application provides an interactive web dashboard and a standalone reproducible command-line preprocessing engine built entirely with free and open-source Python technologies.

---

## 2. Core Functional Modules
The software consists of 8 core functional modules:

1. **Dataset Management:**
   - Ingests raw CSV and Excel (`.xlsx`, `.xls`) invoice ledgers.
   - Inspects file size, line counts, record volume, and schema dimensions.
   - Provides head (first 10) and tail (last 10) data inspection tables.
   - Preserves original raw datasets strictly without in-place modification.

2. **Data Profiling:**
   - Evaluates dataset dimensions, column types, and memory usage.
   - Analyzes unique value counts, missing counts, and missing percentages.
   - Automatically generates a comprehensive Data Dictionary detailing business meanings.

3. **Column Mapping:**
   - Maps raw source headers to standard financial fields:
     - `Invoice ID`
     - `Customer`
     - `Invoice Date`
     - `Due Date`
     - `Payment Date`
     - `Payment Status`
     - `Amount`
     - `Currency`
     - `Country`
   - Supports automated matching suggestions and manual user overrides.
   - Identifies unmapped attributes and exports `column_mapping.csv`.

4. **Data Quality Audit:**
   - 5-factor quality audit engine detecting:
     - Missing values across critical financial fields.
     - Exact record duplicates and duplicate invoice identifiers.
     - Date anomalies (due dates preceding invoice dates, malformed formats).
     - Synthetic placeholders (e.g. placeholder payment dates on unsettled invoices).
     - Numerical inconsistencies (negative amounts, zero amounts, extreme IQR outliers).
     - Categorical inconsistencies (leading/trailing whitespace, mixed casing).
   - Generates defect severity ratings and exports `data_quality_report.csv`.

5. **Data Cleaning:**
   - Automated and configurable data hygiene operations:
     - Exact duplicate removal.
     - Header normalization to lowercase `snake_case`.
     - Whitespace trimming across string fields.
     - Categorical harmonization (standardizing payment status and ISO currency codes).
     - Sanitization of placeholder payment dates on unsettled invoices (`NaT`).
     - ISO-8601 date parsing.
     - Numerical type coercion.
     - Missing value handling (mean, median, mode, or preservation).
     - IQR outlier detection and record flagging (`is_amount_outlier`).
   - Generates before-and-after audit comparison metrics.

6. **Payment Feature Engineering:**
   - Derives essential payment settlement metrics:
     - **Days to Pay (`days_to_pay`):** Calendar days between invoice date and payment date (Paid invoices only).
     - **Payment Delay (`payment_delay`):** Calendar days relative to contractual due date (Paid invoices only).
     - **Paid Late Flag (`paid_late_flag`):** Binary target indicator (`1` = Late, `0` = On-Time / Early).
     - **Open/Paid Flag (`invoice_status`):** Settlement classification (`Paid` vs `Open`).
     - **Days Past Due (`days_past_due`):** Aging metric for open invoices against reference date.
     - **Payment Aging Bucket:** Discrete risk cohorts.

7. **Cleaning Log:**
   - Displays a complete chronological audit trail:
     - Issue identified.
     - Action taken.
     - Business and operational reason.
     - Number of records affected.
     - Timestamp and execution status.
   - Exports `cleaning_log.csv`.

8. **Export Deliverables:**
   - Generates and exports:
     - `cleaned_invoices.csv`
     - `data_dictionary.csv`
     - `column_mapping.csv`
     - `cleaning_log.csv`
     - `cleaning_script.py`
     - `data_quality_report.csv`
     - `cleaned_invoices.parquet`
     - `InvoiceIQ_Deliverables.zip` (consolidated master ZIP archive).

---

## 3. Visual Design System
The user interface follows a professional financial SaaS aesthetic:
* **Background:** Warm Ivory (`#F7F6F0`)
* **Cards:** Pure White (`#FFFFFF`) with subtle drop-shadows and 12px rounded borders
* **Primary Accents:** Sage Green (`#829783`) and Dark Sage (`#465B4B`)
* **Secondary Accents:** Soft Green (`#E3EADF`), Muted Terracotta (`#C58C76`), Champagne Gold (`#D8C59B`), Warm Grey (`#E9E7DF`)
* **Charts:** Coordinated Plotly pastel sequences
* **Avoided:** Dark navy sidebars, black backgrounds, neon colors, and excessive gradients.

---

## 4. Project Directory Structure
```
InvoiceIQ/
│
├── app.py                      # Streamlit application entry point
├── requirements.txt            # Python dependencies
├── README.md                   # Technical documentation
├── streamlit.bat               # Windows batch launcher
│
├── data/
│   ├── raw/                    # Raw original datasets (train_invoices.csv, etc.)
│   ├── processed/              # Cleaned datasets
│   └── exports/                # Exported deliverables (CSVs, Parquet, ZIP)
│
├── modules/
│   ├── ui_theme.py             # Warm Ivory theme & Plotly styles
│   ├── data_loader.py          # Data ingestion & encoding resilience
│   ├── data_profiler.py        # Structural profiling & data dictionary
│   ├── column_mapper.py        # Schema mapping & suggestions
│   ├── data_quality.py         # 5-factor quality audit engine
│   ├── data_cleaner.py         # Standardized cleaning engine & IQR flags
│   ├── feature_engineering.py  # Days to pay, delay & aging metrics
│   └── export_manager.py       # Exporter & ZIP archive bundler
│
├── pages/
│   ├── 1_Dataset_Management.py
│   ├── 2_Data_Profiling.py
│   ├── 3_Column_Mapping.py
│   ├── 4_Data_Quality_Audit.py
│   ├── 5_Data_Cleaning.py
│   ├── 6_Payment_Feature_Engineering.py
│   ├── 7_Cleaning_Log.py
│   └── 8_Export_Deliverables.py
│
├── scripts/
│   └── clean_dataset.py        # Standalone reproducible CLI cleaning script
│
└── tests/
    └── test_pipeline.py        # Automated test suite
```

---

## 5. Installation & Execution

### Prerequisites
Python 3.10+ on Windows, Linux, or macOS.

### Step 1: Install Dependencies
```powershell
pip install -r requirements.txt
```

### Step 2: Launch the Web Dashboard
```powershell
streamlit run app.py
```
*(Or via python module: `python -m streamlit run app.py`)*

### Step 3: Run the Standalone CLI Cleaning Engine
```powershell
# Run with sample (e.g. 50,000 rows):
python scripts/clean_dataset.py --sample 50000

# Run on full dataset:
python scripts/clean_dataset.py --sample 0
```

### Step 4: Run the Test Suite
```powershell
python -m unittest tests/test_pipeline.py
```
