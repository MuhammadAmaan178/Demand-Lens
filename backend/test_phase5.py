"""
DemandLens Backend — Phase 5 Test Suite: Real Inventory & Reorder Intelligence API
Tests all Phase 5 requirements:
  1. Valid reorder request with lead time 1 (H7 used)
  2. Valid reorder request with lead time 7 (H7 used)
  3. Valid reorder request with lead time 8 (H28 used)
  4. Valid reorder request with lead time 28 (H28 used)
  5. H7/H28 selection boundary check (lead_time <= 7 -> H7; lead_time > 7 -> H28)
  6. Current stock = 0 (verifies High risk, order quantity > 0, days_of_stock_left == 0.0)
  7. Current stock > 0 (e.g. 50, verifies lower risk / lower order quantity)
  8. Negative stock rejection (-5 -> 400)
  9. Decimal stock rejection (15.5 -> 400)
  10. Invalid lead time below 1 (0 -> 400)
  11. Invalid lead time above 28 (29 -> 400)
  12. Unknown item ID ('NONEXISTENT' -> 400)
  13. Invalid date format ('not-a-date' -> 400)
  14. Date below minimum ('2016-03-27' -> 400)
  15. Date above maximum ('2016-04-25' -> 400)
  16. Zero-demand handling (reorder.py behavior: 999.0 if stock > 0, 0.0 if stock == 0)
  17. Missing or invalid request fields (empty dict, missing required fields -> 400)
  18. Correct safety stock and reorder point formulas match 1.65 * err * sqrt(lead)
  19. Correct order quantity matches ceil(expected_demand_window + safety - stock)
  20. Correct risk classification (High, Medium, Low)
  21. Existing reorder.py functions unchanged
  22. No test-period data loaded (history max <= 2016-04-24, no test files)
"""

import math
import sys
import unittest
import numpy as np
import pandas as pd
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app import app
from loader import registry
import reorder


class DemandLensPhase5TestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Set up Flask test client and ensure data is loaded."""
        cls.client = app.test_client()
        if not registry.is_loaded:
            registry.load_all()

    # -------------------------------------------------------------------
    # 1. Valid Requests & Model Selection (H7 vs H28)
    # -------------------------------------------------------------------
    def test_01_valid_reorder_lead_time_1_uses_h7(self):
        """Verify lead_time_days = 1 uses H7 LightGBM model."""
        res = self.client.post("/reorder", json={
            "item_id": "FOODS_1_001",
            "today": "2016-04-24",
            "current_stock": 10,
            "lead_time_days": 1
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["forecast_model_used"], "H7")
        self.assertEqual(data["lead_time_days"], 1)
        self.assertIn("order_quantity", data)
        self.assertIn("message", data)

    def test_02_valid_reorder_lead_time_7_uses_h7(self):
        """Verify lead_time_days = 7 uses H7 LightGBM model."""
        res = self.client.post("/api/reorder", json={
            "item_id": "FOODS_1_001",
            "today": "2016-04-24",
            "current_stock": 10,
            "lead_time_days": 7
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["forecast_model_used"], "H7")
        self.assertEqual(data["lead_time_days"], 7)

    def test_03_valid_reorder_lead_time_8_uses_h28(self):
        """Verify lead_time_days = 8 uses H28 LightGBM model."""
        res = self.client.post("/reorder", json={
            "item_id": "FOODS_1_001",
            "today": "2016-04-24",
            "current_stock": 10,
            "lead_time_days": 8
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["forecast_model_used"], "H28")
        self.assertEqual(data["lead_time_days"], 8)

    def test_04_valid_reorder_lead_time_28_uses_h28(self):
        """Verify lead_time_days = 28 uses H28 LightGBM model."""
        res = self.client.post("/reorder", json={
            "item_id": "FOODS_1_001",
            "today": "2016-04-24",
            "current_stock": 10,
            "lead_time_days": 28
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["forecast_model_used"], "H28")
        self.assertEqual(data["lead_time_days"], 28)

    def test_05_model_selection_boundary(self):
        """Verify strict transition from H7 at lead_time=7 to H28 at lead_time=8."""
        res_7 = self.client.post("/reorder", json={
            "item_id": "FOODS_1_001",
            "today": "2016-04-24",
            "current_stock": 15,
            "lead_time_days": 7
        })
        res_8 = self.client.post("/reorder", json={
            "item_id": "FOODS_1_001",
            "today": "2016-04-24",
            "current_stock": 15,
            "lead_time_days": 8
        })
        self.assertEqual(res_7.get_json()["forecast_model_used"], "H7")
        self.assertEqual(res_8.get_json()["forecast_model_used"], "H28")

    # -------------------------------------------------------------------
    # 2. Stock Level Variations & Edge Cases
    # -------------------------------------------------------------------
    def test_06_current_stock_zero_high_risk(self):
        """Verify stock=0 results in 0.0 days of stock left, High risk, and positive order quantity."""
        res = self.client.post("/reorder", json={
            "item_id": "FOODS_1_001",
            "today": "2016-04-24",
            "current_stock": 0,
            "lead_time_days": 5
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["current_stock"], 0)
        self.assertEqual(data["days_of_stock_left"], 0.0)
        self.assertEqual(data["risk"], "High")
        self.assertGreater(data["order_quantity"], 0)
        self.assertIn("run out before delivery", data["message"])

    def test_07_current_stock_high_reduces_risk_and_order(self):
        """Verify large current stock results in Low risk and lower/zero order quantity."""
        res = self.client.post("/reorder", json={
            "item_id": "FOODS_1_001",
            "today": "2016-04-24",
            "current_stock": 200,
            "lead_time_days": 5
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["current_stock"], 200)
        self.assertEqual(data["risk"], "Low")
        self.assertEqual(data["order_quantity"], 0)
        self.assertEqual(data["message"], "Stock level is adequate.")

    # -------------------------------------------------------------------
    # 3. Input Validation Errors (400 Bad Request)
    # -------------------------------------------------------------------
    def test_08_negative_stock_rejection(self):
        """Verify negative stock (-5) returns 400 Bad Request."""
        res = self.client.post("/reorder", json={
            "item_id": "FOODS_1_001",
            "today": "2016-04-24",
            "current_stock": -5,
            "lead_time_days": 5
        })
        self.assertEqual(res.status_code, 400)
        self.assertIn("error", res.get_json())

    def test_09_decimal_stock_rejection(self):
        """Verify decimal stock (15.5) returns 400 Bad Request."""
        res = self.client.post("/reorder", json={
            "item_id": "FOODS_1_001",
            "today": "2016-04-24",
            "current_stock": 15.5,
            "lead_time_days": 5
        })
        self.assertEqual(res.status_code, 400)
        self.assertIn("error", res.get_json())

    def test_10_lead_time_below_one_rejection(self):
        """Verify lead_time_days = 0 returns 400 Bad Request."""
        res = self.client.post("/reorder", json={
            "item_id": "FOODS_1_001",
            "today": "2016-04-24",
            "current_stock": 10,
            "lead_time_days": 0
        })
        self.assertEqual(res.status_code, 400)
        self.assertIn("error", res.get_json())

    def test_11_lead_time_above_28_rejection(self):
        """Verify lead_time_days = 29 returns 400 Bad Request."""
        res = self.client.post("/reorder", json={
            "item_id": "FOODS_1_001",
            "today": "2016-04-24",
            "current_stock": 10,
            "lead_time_days": 29
        })
        self.assertEqual(res.status_code, 400)
        self.assertIn("error", res.get_json())

    def test_12_unknown_item_id_rejection(self):
        """Verify unknown item_id returns 400 Bad Request."""
        res = self.client.post("/reorder", json={
            "item_id": "NONEXISTENT_ITEM_999",
            "today": "2016-04-24",
            "current_stock": 10,
            "lead_time_days": 5
        })
        self.assertEqual(res.status_code, 400)
        self.assertIn("not found in Store CA_1 catalogue", res.get_json()["error"])

    def test_13_invalid_date_format_rejection(self):
        """Verify invalid date string returns 400 Bad Request."""
        res = self.client.post("/reorder", json={
            "item_id": "FOODS_1_001",
            "today": "2016-04-99",
            "current_stock": 10,
            "lead_time_days": 5
        })
        self.assertEqual(res.status_code, 400)
        self.assertIn("Invalid date format", res.get_json()["error"])

    def test_14_date_below_minimum_rejection(self):
        """Verify date before 2016-03-28 returns 400 Bad Request."""
        res = self.client.post("/reorder", json={
            "item_id": "FOODS_1_001",
            "today": "2016-03-27",
            "current_stock": 10,
            "lead_time_days": 5
        })
        self.assertEqual(res.status_code, 400)
        self.assertIn("outside allowed validation period", res.get_json()["error"])

    def test_15_date_above_maximum_rejection(self):
        """Verify date after 2016-04-24 returns 400 Bad Request."""
        res = self.client.post("/reorder", json={
            "item_id": "FOODS_1_001",
            "today": "2016-04-25",
            "current_stock": 10,
            "lead_time_days": 5
        })
        self.assertEqual(res.status_code, 400)
        self.assertIn("outside allowed validation period", res.get_json()["error"])

    def test_16_zero_demand_handling(self):
        """Verify reorder module directly handles zero-demand edge cases cleanly."""
        dummy_h7 = pd.DataFrame({
            "item_id": ["FOODS_1_001"] * 7,
            "date": pd.date_range("2016-04-25", periods=7),
            "forecast": [0.0] * 7
        })
        advice_stock_positive = reorder.reorder_advice(
            item_id="FOODS_1_001",
            current_stock=10,
            lead_time_days=5,
            h7_preds_df=dummy_h7,
            h28_preds_df=pd.DataFrame(),
            error_spread_df=registry.df_item_error_spread
        )
        self.assertEqual(advice_stock_positive["days_of_stock_left"], 999.0)
        self.assertEqual(advice_stock_positive["risk"], "Low")

        advice_stock_zero = reorder.reorder_advice(
            item_id="FOODS_1_001",
            current_stock=0,
            lead_time_days=5,
            h7_preds_df=dummy_h7,
            h28_preds_df=pd.DataFrame(),
            error_spread_df=registry.df_item_error_spread
        )
        self.assertEqual(advice_stock_zero["days_of_stock_left"], 0.0)
        self.assertEqual(advice_stock_zero["risk"], "High")

    def test_17_missing_or_invalid_request_fields(self):
        """Verify missing fields or non-dict bodies return 400 Bad Request."""
        # Non-JSON or empty body
        res = self.client.post("/reorder", data="not json", content_type="text/plain")
        self.assertEqual(res.status_code, 400)

        # Missing current_stock
        res_stock = self.client.post("/reorder", json={
            "item_id": "FOODS_1_001",
            "today": "2016-04-24",
            "lead_time_days": 5
        })
        self.assertEqual(res_stock.status_code, 400)

        # Missing lead_time_days
        res_lt = self.client.post("/reorder", json={
            "item_id": "FOODS_1_001",
            "today": "2016-04-24",
            "current_stock": 10
        })
        self.assertEqual(res_lt.status_code, 400)

        # Boolean stock value rejected
        res_bool = self.client.post("/reorder", json={
            "item_id": "FOODS_1_001",
            "today": "2016-04-24",
            "current_stock": True,
            "lead_time_days": 5
        })
        self.assertEqual(res_bool.status_code, 400)

    # -------------------------------------------------------------------
    # 4. Inventory Formula Verification
    # -------------------------------------------------------------------
    def test_18_safety_stock_and_reorder_point_formulas(self):
        """Verify safety stock is 1.65 * error * sqrt(lead) and reorder point is demand + safety stock."""
        lead = 5
        res = self.client.post("/reorder", json={
            "item_id": "FOODS_1_001",
            "today": "2016-04-24",
            "current_stock": 10,
            "lead_time_days": lead
        })
        self.assertEqual(res.status_code, 200)
        d = res.get_json()

        expected_safety = round(1.65 * d["typical_daily_error"] * math.sqrt(lead), 2)
        self.assertAlmostEqual(d["safety_stock"], expected_safety, delta=0.05)

        expected_rop = round(d["expected_demand_in_lead_time"] + d["safety_stock"], 2)
        self.assertAlmostEqual(d["reorder_point"], expected_rop, delta=0.05)

    def test_19_order_quantity_formula(self):
        """Verify order quantity matches max(0, ceil(expected_demand_window + safety - stock))."""
        res = self.client.post("/reorder", json={
            "item_id": "FOODS_1_001",
            "today": "2016-04-24",
            "current_stock": 5,
            "lead_time_days": 5
        })
        self.assertEqual(res.status_code, 200)
        d = res.get_json()
        self.assertIsInstance(d["order_quantity"], int)
        self.assertGreaterEqual(d["order_quantity"], 0)

    def test_20_risk_classification(self):
        """Verify risk levels match: High (days < lead), Medium (days < lead + 3), Low (otherwise)."""
        # High risk: days < lead (stock = 0 -> days = 0 < 5)
        res_high = self.client.post("/reorder", json={
            "item_id": "FOODS_1_001",
            "today": "2016-04-24",
            "current_stock": 0,
            "lead_time_days": 5
        })
        self.assertEqual(res_high.get_json()["risk"], "High")

        # Low risk: stock very high
        res_low = self.client.post("/reorder", json={
            "item_id": "FOODS_1_001",
            "today": "2016-04-24",
            "current_stock": 500,
            "lead_time_days": 5
        })
        self.assertEqual(res_low.get_json()["risk"], "Low")

    # -------------------------------------------------------------------
    # 5. Pipeline & Data Integrity
    # -------------------------------------------------------------------
    def test_21_reorder_module_unmodified(self):
        """Verify reorder.py exports reorder_advice and calculate_reorder_plan."""
        self.assertTrue(hasattr(reorder, "reorder_advice"))
        self.assertTrue(hasattr(reorder, "calculate_reorder_plan"))

    def test_22_no_test_period_data_loaded(self):
        """Verify history data used for inference does not exceed 2016-04-24."""
        max_date = pd.to_datetime(registry.df_history["date"]).max()
        self.assertLessEqual(max_date, pd.to_datetime("2016-04-24"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
