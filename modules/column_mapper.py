"""
InvoiceIQ Column Mapping Module
Provides automatic field detection, manual dropdown overrides,
validation, and export to column_mapping.csv.
"""

import re
import pandas as pd
import streamlit as st

# Required Project Fields defined in Section 9
CORE_PROJECT_FIELDS = [
    "Invoice ID",
    "Customer",
    "Invoice Date",
    "Due Date",
    "Payment Date",
    "Payment Status",
    "Amount",
    "Currency",
    "Country"
]

EXTENDED_PROJECT_FIELDS = [
    "Invoice Number",
    "Customer ID",
    "Customer Email",
    "Vendor",
    "Product Category",
    "Product Name",
    "Quantity",
    "Unit Price",
    "Discount Amount",
    "Tax Amount",
    "Shipping Cost",
    "Subtotal",
    "Payment Method",
    "Is Overdue"
]

# Detection heuristic patterns
PATTERNS = {
    "Invoice ID": [r"^invoice_?id$", r"^inv_?id$", r"^id$", r"^bill_?id$"],
    "Invoice Number": [r"^invoice_?num(ber)?$", r"^inv_?num(ber)?$", r"^bill_?no$"],
    "Customer": [r"^customer_?name$", r"^client_?name$", r"^customer$", r"^client$", r"^buyer$"],
    "Customer ID": [r"^customer_?id$", r"^client_?id$", r"^cust_?id$"],
    "Customer Email": [r"^customer_?email$", r"^client_?email$", r"^email$"],
    "Invoice Date": [r"^invoice_?date$", r"^inv_?date$", r"^bill_?date$", r"^issue_?date$"],
    "Due Date": [r"^due_?date$", r"^payment_?due_?date$", r"^deadline$"],
    "Payment Date": [r"^payment_?date$", r"^paid_?date$", r"^settlement_?date$", r"^pay_?date$"],
    "Payment Status": [r"^payment_?status$", r"^status$", r"^invoice_?status$", r"^paid_?status$"],
    "Amount": [r"^total_?amount$", r"^amount$", r"^invoice_?amount$", r"^net_?amount$", r"^grand_?total$"],
    "Currency": [r"^currency$", r"^curr$", r"^currency_?code$"],
    "Country": [r"^customer_?country$", r"^country$", r"^billing_?country$", r"^client_?country$"],
    "Vendor": [r"^vendor_?name$", r"^vendor$", r"^supplier_?name$", r"^supplier$"],
    "Product Category": [r"^product_?category$", r"^category$"],
    "Product Name": [r"^product_?name$", r"^item_?name$", r"^description$"],
    "Quantity": [r"^quantity$", r"^qty$"],
    "Unit Price": [r"^unit_?price$", r"^price$"],
    "Discount Amount": [r"^discount_?amount$", r"^discount$"],
    "Tax Amount": [r"^tax_?amount$", r"^tax$"],
    "Shipping Cost": [r"^shipping_?cost$", r"^freight$", r"^shipping$"],
    "Subtotal": [r"^subtotal$", r"^base_?amount$"],
    "Payment Method": [r"^payment_?method$", r"^pay_?method$", r"^payment_?type$"],
    "Is Overdue": [r"^is_?overdue$", r"^overdue_?flag$"]
}

def suggest_mapping(columns):
    """
    Automatically suggest mapping from actual columns to project fields.
    Returns dict: {project_field: mapped_actual_column or None}
    """
    mapping = {}
    used_columns = set()
    all_fields = CORE_PROJECT_FIELDS + EXTENDED_PROJECT_FIELDS
    
    # 1. Exact match / regex matching
    for field in all_fields:
        patterns = PATTERNS.get(field, [])
        match_found = None
        for col in columns:
            clean_col = col.strip().lower()
            if col in used_columns:
                continue
            for pat in patterns:
                if re.match(pat, clean_col):
                    match_found = col
                    break
            if match_found:
                break
        if match_found:
            mapping[field] = match_found
            used_columns.add(match_found)
        else:
            mapping[field] = None

    # Fallback heuristics
    if not mapping.get("Invoice ID") and mapping.get("Invoice Number"):
        mapping["Invoice ID"] = mapping["Invoice Number"]
        
    return mapping

def generate_mapping_dataframe(mapping, columns):
    """Create a structured DataFrame for display and export."""
    records = []
    mapped_actuals = set(v for v in mapping.values() if v is not None)
    
    for field in CORE_PROJECT_FIELDS:
        actual = mapping.get(field)
        status = "Mapped" if actual else "Missing / Not Found"
        records.append({
            "Project Field": field,
            "Mapped Column": actual if actual else "None",
            "Field Type": "Core Requirement",
            "Status": status
        })
        
    for field in EXTENDED_PROJECT_FIELDS:
        actual = mapping.get(field)
        if actual:
            records.append({
                "Project Field": field,
                "Mapped Column": actual,
                "Field Type": "Extended Attribute",
                "Status": "Mapped"
            })
            
    # Also list unmapped actual columns
    unmapped = [c for c in columns if c not in mapped_actuals]
    
    df_map = pd.DataFrame(records)
    return df_map, unmapped

def get_mapped_series(df, mapping, project_field):
    """Safely retrieve series by mapped project field."""
    col = mapping.get(project_field)
    if col and col in df.columns:
        return df[col]
    return None

