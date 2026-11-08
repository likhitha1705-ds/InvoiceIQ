"""
InvoiceIQ Data Profiler Module
Performs comprehensive structural profiling, metadata generation,
data dictionary compilation, and data_dictionary.csv export.
"""

import pandas as pd
import numpy as np
from modules.column_mapper import suggest_mapping

# Inferred meanings for known financial columns
COLUMN_MEANINGS = {
    "invoice_id": "Unique primary key integer identifying each invoice record in the system",
    "invoice_number": "Business invoice reference code with prefix INV-",
    "invoice_date": "Date on which the invoice was generated and issued to customer",
    "due_date": "Contractual payment deadline agreed in invoice terms",
    "customer_id": "Unique business customer / account identifier",
    "customer_name": "Full legal or commercial name of the purchasing company/customer",
    "customer_email": "Official corporate email contact for billing correspondence",
    "customer_city": "City where the customer or delivery location is situated",
    "customer_state": "State/Province of the customer location",
    "customer_country": "Country of the billing entity",
    "vendor_id": "Unique identifier for the issuing vendor/supplier",
    "vendor_name": "Commercial name of the seller / supplier entity",
    "product_id": "Stock Keeping Unit (SKU) or product code",
    "product_category": "Industry classification of goods or services billed",
    "product_name": "Commercial title or description of item purchased",
    "quantity": "Total number of units billed in transaction",
    "unit_price": "Base unit price per single item in specified currency",
    "discount_percent": "Contractual percentage discount applied to subtotal",
    "tax_percent": "Applicable statutory VAT / GST / sales tax rate",
    "subtotal": "Gross amount before discount, tax, and freight (quantity * unit_price)",
    "discount_amount": "Total monetary discount deducted from subtotal",
    "tax_amount": "Total statutory tax calculated on post-discount amount",
    "shipping_cost": "Freight, logistics, or dispatch charge billed to customer",
    "total_amount": "Final invoice total payable (subtotal - discount + tax + shipping)",
    "currency": "Standard ISO three-letter currency code (USD, INR, EUR, etc.)",
    "payment_method": "Payment instrument used or instructed (Bank Transfer, UPI, Credit Card, etc.)",
    "payment_status": "Current invoice settlement lifecycle state (Paid, Pending, Overdue, Cancelled)",
    "payment_date": "Recorded timestamp of payment settlement (or placeholder in raw data)",
    "order_channel": "Origination channel of the commercial order (Online Portal, Sales Rep, Marketplace)",
    "sales_rep": "Assigned internal commercial representative managing the client account",
    "is_overdue": "Binary flag indicating whether invoice has breached agreed payment terms (1=Yes, 0=No)"
}

def profile_dataset(df):
    """
    Computes complete dataset metadata, type splits, and memory consumption.
    """
    if df is None or df.empty:
        return {
            "total_rows": 0,
            "total_cols": 0,
            "memory_usage_mb": 0.0,
            "num_cols": [],
            "cat_cols": [],
            "date_cols": [],
            "missing_total": 0,
            "duplicate_rows": 0
        }
        
    total_rows = len(df)
    total_cols = len(df.columns)
    memory_mb = df.memory_usage(deep=True).sum() / (1024 * 1024)
    
    # Identify column types
    num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    cat_cols = df.select_dtypes(include=['object', 'category', 'string']).columns.tolist()
    
    # Identify potential date columns (either datetime dtype or containing 'date' in name)
    date_cols = [c for c in df.columns if 'date' in c.lower() or pd.api.types.is_datetime64_any_dtype(df[c])]
    # Remove date cols from cat/num lists for clarity
    cat_cols = [c for c in cat_cols if c not in date_cols]
    num_cols = [c for c in num_cols if c not in date_cols]
    
    missing_total = int(df.isnull().sum().sum())
    duplicate_rows = int(df.duplicated().sum())
    
    return {
        "total_rows": total_rows,
        "total_cols": total_cols,
        "memory_usage_mb": round(memory_mb, 2),
        "num_cols": num_cols,
        "cat_cols": cat_cols,
        "date_cols": date_cols,
        "missing_total": missing_total,
        "duplicate_rows": duplicate_rows
    }

def build_data_dictionary(df, mapping=None):
    """
    Constructs a structured data dictionary DataFrame.
    """
    if df is None or df.empty:
        return pd.DataFrame()
        
    if mapping is None:
        mapping = suggest_mapping(df.columns.tolist())
        
    # Reverse mapping for quick lookup: {col: project_field}
    rev_mapping = {v: k for k, v in mapping.items() if v is not None}
    
    records = []
    total_rows = len(df)
    
    for col in df.columns:
        dtype = str(df[col].dtype)
        unique_count = int(df[col].nunique(dropna=False))
        missing_count = int(df[col].isnull().sum())
        missing_pct = round((missing_count / total_rows) * 100, 2) if total_rows > 0 else 0.0
        
        # Inferred meaning
        clean_name = col.strip().lower()
        meaning = COLUMN_MEANINGS.get(clean_name, f"Attribute recording '{col}' values in the invoice stream")
        mapped_field = rev_mapping.get(col, "Unmapped / Extended")
        
        # Sample value
        sample_val = str(df[col].dropna().iloc[0]) if not df[col].dropna().empty else "None"
        if len(sample_val) > 40:
            sample_val = sample_val[:37] + "..."
            
        records.append({
            "Column Name": col,
            "Detected Data Type": dtype,
            "Unique Values": unique_count,
            "Missing Count": missing_count,
            "Missing %": f"{missing_pct:.2f}%",
            "Sample Value": sample_val,
            "Mapped Project Field": mapped_field,
            "Inferred Meaning": meaning
        })
        
    return pd.DataFrame(records)

