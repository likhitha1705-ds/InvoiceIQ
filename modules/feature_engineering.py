"""
InvoiceIQ Payment Feature Engineering Module
Derives payment delay metrics, settlement durations, late-payment indicators,
and aging buckets strictly observing financial audit integrity.
"""

import pandas as pd
import numpy as np

def engineer_payment_features(df, reference_date=None):
    """
    Computes derived payment fields:
    - days_to_pay: payment_date - invoice_date (Paid only)
    - payment_delay: payment_date - due_date (Paid only)
    - paid_late_flag: 1 if payment_delay > 0 else 0 (Paid only)
    - invoice_status: 'Paid' vs 'Open'
    - days_past_due: reference_date - due_date (Open invoices only)
    - payment_aging_bucket: Discrete classification for cash-flow risk
    """
    df_feat = df.copy()
    
    # Ensure datetime format
    for col in ['invoice_date', 'due_date', 'payment_date']:
        if col in df_feat.columns and not pd.api.types.is_datetime64_any_dtype(df_feat[col]):
            df_feat[col] = pd.to_datetime(df_feat[col], errors='coerce')
            
    # Determine Reference Date for Open Invoices
    if reference_date is None:
        if 'due_date' in df_feat.columns and df_feat['due_date'].notnull().any():
            reference_date = df_feat['due_date'].max()
        elif 'invoice_date' in df_feat.columns and df_feat['invoice_date'].notnull().any():
            reference_date = df_feat['invoice_date'].max()
        else:
            reference_date = pd.Timestamp.today()
    else:
        reference_date = pd.to_datetime(reference_date)
        
    df_feat.attrs['reference_date'] = str(reference_date)

    # 1. Invoice Status (Paid vs Open)
    if 'payment_status' in df_feat.columns:
        status_clean = df_feat['payment_status'].astype(str).str.strip().str.lower()
        is_paid = status_clean == 'paid'
        df_feat['invoice_status'] = np.where(is_paid, 'Paid', 'Open')
    else:
        is_paid = pd.Series(False, index=df_feat.index)
        df_feat['invoice_status'] = 'Unknown'

    # Initialize engineered fields
    df_feat['days_to_pay'] = np.nan
    df_feat['payment_delay'] = np.nan
    df_feat['paid_late_flag'] = np.nan
    df_feat['days_past_due'] = np.nan
    df_feat['payment_aging_bucket'] = 'Unclassified'

    # 2. Days to Pay & Payment Delay (FOR PAID INVOICES ONLY)
    if 'invoice_date' in df_feat.columns and 'payment_date' in df_feat.columns:
        paid_and_valid = is_paid & df_feat['payment_date'].notnull() & df_feat['invoice_date'].notnull()
        df_feat.loc[paid_and_valid, 'days_to_pay'] = (
            df_feat.loc[paid_and_valid, 'payment_date'] - df_feat.loc[paid_and_valid, 'invoice_date']
        ).dt.days

    if 'due_date' in df_feat.columns and 'payment_date' in df_feat.columns:
        paid_and_valid_due = is_paid & df_feat['payment_date'].notnull() & df_feat['due_date'].notnull()
        df_feat.loc[paid_and_valid_due, 'payment_delay'] = (
            df_feat.loc[paid_and_valid_due, 'payment_date'] - df_feat.loc[paid_and_valid_due, 'due_date']
        ).dt.days
        
        # 3. Paid Late Flag (1 if payment_delay > 0, 0 otherwise)
        df_feat.loc[paid_and_valid_due, 'paid_late_flag'] = (
            df_feat.loc[paid_and_valid_due, 'payment_delay'] > 0
        ).astype(int)

    # 4. Days Past Due (FOR OPEN / UNSETTLED INVOICES ONLY)
    if 'due_date' in df_feat.columns:
        open_and_valid = (~is_paid) & df_feat['due_date'].notnull()
        df_feat.loc[open_and_valid, 'days_past_due'] = (
            reference_date - df_feat.loc[open_and_valid, 'due_date']
        ).dt.days

    # 5. Aging and Settlement Classification Buckets
    def assign_bucket(row):
        if row['invoice_status'] == 'Paid':
            delay = row['payment_delay']
            if pd.isna(delay):
                return 'Paid (Date Missing)'
            elif delay < -7:
                return 'Early (>7d early)'
            elif delay < 0:
                return 'Early (1-7d early)'
            elif delay == 0:
                return 'On-Time (Settled on Due Date)'
            elif delay <= 15:
                return 'Late (1-15d delay)'
            elif delay <= 30:
                return 'Late (16-30d delay)'
            else:
                return 'Severe Late (>30d delay)'
        elif row['invoice_status'] == 'Open':
            dpd = row['days_past_due']
            if pd.isna(dpd):
                return 'Open (Undated)'
            elif dpd <= 0:
                return 'Open (Current / Not Due)'
            elif dpd <= 30:
                return 'Open (1-30d Past Due)'
            elif dpd <= 60:
                return 'Open (31-60d Past Due)'
            elif dpd <= 90:
                return 'Open (61-90d Past Due)'
            else:
                return 'Open (>90d Past Due)'
        return 'Unclassified'

    df_feat['payment_aging_bucket'] = df_feat.apply(assign_bucket, axis=1)
    return df_feat
