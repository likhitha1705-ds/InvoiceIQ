"""
InvoiceIQ Automated Test Suite
Verifies all 8 core application modules, data cleaning, quality auditing,
feature engineering, deliverables generation, and module imports.
"""

import os
import sys
import unittest
import importlib
import pandas as pd
import numpy as np

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from modules.data_loader import get_available_raw_datasets, load_dataset_sample, count_file_lines
from modules.data_profiler import profile_dataset, build_data_dictionary
from modules.column_mapper import suggest_mapping, generate_mapping_dataframe, CORE_PROJECT_FIELDS
from modules.data_quality import run_quality_audit
from modules.data_cleaner import DataCleaner
from modules.feature_engineering import engineer_payment_features
from modules.export_manager import generate_all_deliverables, EXPORTS_DIR

class TestInvoiceIQPipeline(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        cls.raw_files = get_available_raw_datasets()
        cls.sample_df = pd.read_csv("data/raw/train_invoices.csv", nrows=1000, low_memory=False)

    def test_01_dependencies_installed(self):
        """1. Verify required libraries are importable."""
        for mod in ['streamlit', 'pandas', 'numpy', 'plotly', 'openpyxl', 'pyarrow']:
            __import__(mod)

    def test_02_kaggle_dataset_exists(self):
        """2. Verify actual Kaggle dataset files exist in data/raw/."""
        filenames = [f["filename"] for f in self.raw_files]
        self.assertIn("train_invoices.csv", filenames)
        self.assertIn("test_invoices.csv", filenames)

    def test_03_dataset_dimensions(self):
        """3. Verify real dataset scale."""
        train_rows = count_file_lines("data/raw/train_invoices.csv")
        self.assertEqual(train_rows, 2500000)
        self.assertEqual(len(self.sample_df.columns), 31)

    def test_04_data_profiler(self):
        """4. Test data profiling engine."""
        profile = profile_dataset(self.sample_df)
        self.assertEqual(profile["total_rows"], 1000)
        self.assertEqual(profile["total_cols"], 31)
        self.assertGreater(profile["memory_usage_mb"], 0)

    def test_05_column_mapping(self):
        """5. Test automatic column mapping against core fields."""
        mapping = suggest_mapping(self.sample_df.columns.tolist())
        for field in CORE_PROJECT_FIELDS:
            self.assertIsNotNone(mapping.get(field), f"Field '{field}' failed to map")

    def test_06_data_quality_audit(self):
        """6. Test quality audit engine for anomalies."""
        audit_report, stats = run_quality_audit(self.sample_df)
        self.assertIsInstance(audit_report, pd.DataFrame)
        self.assertIn("Total Issues Found", stats)
        # Verify detection of placeholder dates on unpaid records
        has_placeholder = any("placeholder" in str(x).lower() for x in audit_report["Issue"])
        self.assertTrue(has_placeholder)

    def test_07_data_cleaner(self):
        """7. Test data cleaner operations and before/after stats."""
        cleaner = DataCleaner(self.sample_df)
        clean_df, log_df, comp_df = cleaner.execute_all()
        self.assertEqual(len(clean_df), len(self.sample_df))
        self.assertGreater(len(log_df), 5)
        # Unpaid payment dates must be sanitized to NaT
        unpaid = clean_df['payment_status'].str.lower().isin(['pending', 'overdue', 'cancelled'])
        self.assertTrue(clean_df.loc[unpaid, 'payment_date'].isna().all())

    def test_08_feature_engineering(self):
        """8. Test payment delay feature derivations."""
        cleaner = DataCleaner(self.sample_df)
        clean_df, _, _ = cleaner.execute_all()
        feat_df = engineer_payment_features(clean_df)
        
        for col in ['days_to_pay', 'payment_delay', 'paid_late_flag', 'invoice_status', 'days_past_due', 'payment_aging_bucket']:
            self.assertIn(col, feat_df.columns)
            
        # Check rule: Days to pay only for paid invoices
        open_mask = feat_df['invoice_status'] == 'Open'
        self.assertTrue(feat_df.loc[open_mask, 'days_to_pay'].isna().all())
        self.assertTrue(feat_df.loc[open_mask, 'payment_delay'].isna().all())

    def test_09_deliverables_generation(self):
        """9. Test deliverables generation (CSV, Parquet, ZIP)."""
        cleaner = DataCleaner(self.sample_df)
        clean_df, log_df, _ = cleaner.execute_all()
        feat_df = engineer_payment_features(clean_df)
        mapping = suggest_mapping(self.sample_df.columns.tolist())
        map_df, _ = generate_mapping_dataframe(mapping, self.sample_df.columns.tolist())
        dict_df = build_data_dictionary(feat_df, mapping)
        qual_df, _ = run_quality_audit(self.sample_df)

        manifest = generate_all_deliverables(feat_df, dict_df, map_df, log_df, qual_df)
        for key in [
            'cleaned_invoices.csv', 'data_dictionary.csv', 'column_mapping.csv',
            'cleaning_log.csv', 'cleaning_script.py', 'data_quality_report.csv',
            'InvoiceIQ_Deliverables.zip'
        ]:
            self.assertIn(key, manifest)
            self.assertTrue(os.path.exists(manifest[key]), f"Missing deliverable: {key}")

    def test_10_all_8_modules_loadable(self):
        """10. Verify all 8 core application modules can be loaded."""
        pages = {
            "1_Dataset_Management": "render_dataset_management",
            "2_Data_Profiling": "render_profiling",
            "3_Column_Mapping": "render_column_mapping",
            "4_Data_Quality_Audit": "render_quality_audit",
            "5_Data_Cleaning": "render_data_cleaning",
            "6_Payment_Feature_Engineering": "render_feature_engineering",
            "7_Cleaning_Log": "render_cleaning_log",
            "8_Export_Deliverables": "render_export_deliverables"
        }
        for mod_name, func_name in pages.items():
            mod = importlib.import_module(f'pages.{mod_name}')
            self.assertTrue(hasattr(mod, func_name), f"Missing {func_name} in pages.{mod_name}")

if __name__ == '__main__':
    unittest.main()
